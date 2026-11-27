"""Autenticacion y administracion de cuentas de Tiendas Mi Cholo."""
import repositorios as repo
import hashlib
import secrets
import hmac
import re
import sqlite3
from datetime import datetime
from contextlib import closing
from getpass import getpass
from base_datos import conectar, inicializar_base_datos

ITERACIONES = 600000
ROLES = ('Administrador', 'Vendedor')
CAMPOS_PUBLICOS = 'id_usuario, usuario, nombre_completo, rol, activo, fecha_creacion, ultimo_acceso'


def fecha_actual():
    return datetime.now().isoformat(sep=' ', timespec='seconds')


def validar_usuario(usuario):
    usuario = str(usuario).strip().lower()
    if not re.fullmatch(r'[a-z0-9_.-]{4,30}', usuario):
        raise ValueError('Usuario: entre 4 y 30 letras ASCII, numeros, puntos, guiones o guion bajo.')
    return usuario


def validar_password(password):
    if not isinstance(password, str) or not 6 <= len(password) <= 128:
        raise ValueError('La contrasena debe tener entre 6 y 128 caracteres.')
    if not password.strip():
        raise ValueError('La contrasena no puede estar vacia.')
    return password


def generar_hash(password, salt, iteraciones=ITERACIONES):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), iteraciones).hex()


def preparar_password(password):
    validar_password(password)
    salt = secrets.token_hex(32)
    return generar_hash(password, salt), salt


def _insertar(conexion, usuario, nombre, password, rol):
    usuario = validar_usuario(usuario)
    nombre = str(nombre).strip()
    if not 2 <= len(nombre) <= 100 or not any(c.isalpha() for c in nombre):
        raise ValueError('Nombre completo invalido.')
    if rol not in ROLES:
        raise ValueError('Rol invalido.')
    hash_password, salt = preparar_password(password)
    try:
        cursor = repo.insertar_usuario(conexion, (usuario, nombre, hash_password, salt, ITERACIONES, rol, fecha_actual()))
    except sqlite3.IntegrityError as error:
        raise ValueError('Usuario duplicado o datos invalidos.') from error
    return cursor.lastrowid


def necesita_administrador():
    with closing(conectar()) as conexion:
        return repo.contar_usuarios(conexion).fetchone()[0] == 0


def crear_primer_administrador(usuario, nombre, password):
    with closing(conectar()) as conexion, conexion:
        repo.iniciar_transaccion(conexion)
        if repo.contar_usuarios(conexion).fetchone()[0]:
            raise ValueError('La configuracion inicial ya fue realizada.')
        return _insertar(conexion, usuario, nombre, password, 'Administrador')


def autenticar(usuario, password):
    try:
        usuario = validar_usuario(usuario)
        validar_password(password)
    except ValueError:
        raise ValueError('Credenciales incorrectas.') from None
    with closing(conectar()) as conexion, conexion:
        fila = repo.consultar_credenciales(conexion, (usuario,)).fetchone()
        salt = fila['salt'] if fila else '00' * 32
        calculado = generar_hash(password, salt, fila['iteraciones'] if fila else ITERACIONES)
        esperado = fila['password_hash'] if fila else '00' * 32
        if not hmac.compare_digest(calculado, esperado) or not fila or not fila['activo']:
            raise ValueError('Credenciales incorrectas o cuenta inactiva.')
        cursor = repo.actualizar_acceso(conexion, (fecha_actual(), fila['id_usuario'], esperado))
        if cursor.rowcount != 1:
            raise ValueError('La cuenta cambio. Inicie sesion nuevamente.')
        return dict(repo.consultar_usuario_publico(conexion, (fila['id_usuario'],)).fetchone())


def _autorizar(conexion, id_usuario, roles=ROLES):
    fila = repo.consultar_usuario_activo(conexion, (id_usuario,)).fetchone()
    if not fila or fila['rol'] not in roles:
        raise ValueError('Acceso no autorizado.')
    return dict(fila)


def verificar_permiso(id_usuario, roles=ROLES):
    with closing(conectar()) as conexion:
        return _autorizar(conexion, id_usuario, roles)


def crear_usuario(id_admin, usuario, nombre, password, rol):
    with closing(conectar()) as conexion, conexion:
        repo.iniciar_transaccion(conexion)
        _autorizar(conexion, id_admin, ('Administrador',))
        return _insertar(conexion, usuario, nombre, password, rol)


def listar_usuarios(id_admin):
    with closing(conectar()) as conexion:
        _autorizar(conexion, id_admin, ('Administrador',))
        return [dict(f) for f in repo.consultar_usuarios_publicos(conexion)]


def cambiar_estado(id_admin, id_objetivo, activo):
    if activo not in (0, 1):
        raise ValueError('Estado invalido.')
    with closing(conectar()) as conexion, conexion:
        repo.iniciar_transaccion(conexion)
        _autorizar(conexion, id_admin, ('Administrador',))
        if id_admin == id_objetivo and not activo:
            raise ValueError('No puede desactivar su propia cuenta.')
        cursor = repo.actualizar_estado_usuario(conexion, (activo, id_objetivo))
        if cursor.rowcount != 1:
            raise ValueError('Usuario inexistente.')


def cambiar_password(id_usuario, actual, nueva):
    nuevo_hash, salt = preparar_password(nueva)
    validar_password(actual)
    with closing(conectar()) as conexion, conexion:
        repo.iniciar_transaccion(conexion)
        _autorizar(conexion, id_usuario)
        fila = repo.consultar_usuario_id(conexion, (id_usuario,)).fetchone()
        calculado = generar_hash(actual, fila['salt'], fila['iteraciones'])
        if not hmac.compare_digest(calculado, fila['password_hash']):
            raise ValueError('Contrasena actual incorrecta.')
        repo.actualizar_password(conexion, (nuevo_hash, salt, ITERACIONES, id_usuario))


def pedir_password():
    password = getpass('Contrasena nueva (minimo 6 caracteres): ')
    if password != getpass('Repita la contrasena: '):
        raise ValueError('Las contrasenas no coinciden.')
    return validar_password(password)


def menu_usuarios():
    if necesita_administrador():
        print('CONFIGURACION INICIAL: CREAR ADMINISTRADOR')
        usuario = input('Usuario: ')
        nombre = input('Nombre completo: ')
        crear_primer_administrador(usuario, nombre, pedir_password())
        print('[OK] Administrador creado.')
    sesion = None
    while True:
        try:
            if sesion is None:
                print('\n1. Iniciar sesion\n0. Salir')
                opcion = input('Opcion: ').strip()
                if opcion == '0': return
                if opcion != '1': continue
                sesion = autenticar(input('Usuario: '), getpass('Contrasena: '))
                print('[OK] Bienvenido:', sesion['nombre_completo'], '|', sesion['rol'])
                continue
            identificador = sesion['id_usuario']
            sesion = verificar_permiso(identificador)
            print('\n1. Cambiar contrasena\n0. Cerrar sesion')
            if sesion['rol'] == 'Administrador':
                print('2. Crear usuario\n3. Listar usuarios\n4. Cambiar estado')
            opcion = input('Opcion: ').strip()
            if opcion == '0': sesion = None
            elif opcion == '1':
                cambiar_password(identificador, getpass('Contrasena actual: '), pedir_password())
                print('[OK] Contrasena actualizada.')
                sesion = None
            elif opcion == '2' and sesion['rol'] == 'Administrador':
                usuario = input('Usuario nuevo: ')
                nombre = input('Nombre completo: ')
                rol = input('Rol (1 Administrador, 2 Vendedor): ').strip()
                if rol not in ('1', '2'): raise ValueError('Rol invalido.')
                crear_usuario(identificador, usuario, nombre, pedir_password(), ROLES[int(rol)-1])
                print('[OK] Usuario creado.')
            elif opcion == '3' and sesion['rol'] == 'Administrador':
                for fila in listar_usuarios(identificador):
                    print(fila['id_usuario'], fila['usuario'], fila['rol'], 'Activo' if fila['activo'] else 'Inactivo')
            elif opcion == '4' and sesion['rol'] == 'Administrador':
                cambiar_estado(identificador, int(input('ID: ')), int(input('Estado (1 activo, 0 inactivo): ')))
                print('[OK] Estado actualizado.')
            else: print('Opcion incorrecta o no autorizada.')
        except (ValueError, sqlite3.Error, OSError) as error:
            print('Error:', error)
        except (KeyboardInterrupt, EOFError):
            print('\nSaliendo.')
            return


if __name__ == '__main__':
    try:
        inicializar_base_datos()
        menu_usuarios()
    except (ValueError, sqlite3.Error, OSError, KeyboardInterrupt, EOFError) as error:
        print('No se pudo continuar:', error)
