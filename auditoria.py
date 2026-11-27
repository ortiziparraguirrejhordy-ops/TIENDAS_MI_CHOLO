"""Registro y consulta de operaciones del sistema."""
import repositorios as repo
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from base_datos import conectar, inicializar_base_datos
from usuarios import autenticar, verificar_permiso
from getpass import getpass


def serializar(datos):
    """Solo admite campos comerciales expresamente autorizados."""
    if datos is None:
        return None
    permitidos = {'codigo', 'nombre', 'categoria', 'precio_centavos',
                  'stock', 'activo', 'id_producto', 'id_venta',
                  'cantidad', 'total_centavos', 'metodo_pago', 'rol'}
    if not isinstance(datos, dict):
        raise ValueError('Los datos deben ser un diccionario.')
    seguros = {k: v for k, v in datos.items() if k in permitidos
               and isinstance(v, (str, int, float, bool, type(None)))}
    return json.dumps(seguros, ensure_ascii=False)


def registrar_auditoria(conexion, id_usuario, accion, modulo, descripcion,
                        anteriores=None, nuevos=None, resultado='EXITOSO'):
    """Registra dentro de la transaccion del llamador, sin hacer commit."""
    for valor, limite in ((accion, 50), (modulo, 50), (descripcion, 1000)):
        if not isinstance(valor, str) or not 1 <= len(valor.strip()) <= limite:
            raise ValueError('Datos de auditoria invalidos.')
    if resultado not in ('EXITOSO', 'FALLIDO'):
        raise ValueError('Resultado invalido.')
    usuario = 'Sistema'
    if id_usuario is not None:
        fila = repo.consultar_nombre_usuario(conexion, (id_usuario,)).fetchone()
        if fila is None:
            raise ValueError('Usuario inexistente.')
        usuario = fila['usuario']
    cursor = repo.insertar_auditoria(conexion, (id_usuario, usuario, accion.strip(), modulo.strip(), descripcion.strip(), serializar(anteriores), serializar(nuevos), datetime.now().isoformat(sep=' ', timespec='seconds'), resultado))
    return cursor.lastrowid


def registrar_evento(id_usuario, accion, modulo, descripcion,
                     anteriores=None, nuevos=None, resultado='EXITOSO'):
    """Registra eventos independientes, por ejemplo una busqueda."""
    with closing(conectar()) as conexion, conexion:
        return registrar_auditoria(conexion, id_usuario, accion, modulo,
                                   descripcion, anteriores, nuevos, resultado)


def listar_auditoria(id_admin, limite=100):
    verificar_permiso(id_admin, ('Administrador',))
    if type(limite) is not int or not 1 <= limite <= 1000:
        raise ValueError('Limite invalido.')
    with closing(conectar()) as conexion:
        filas = repo.consultar_auditoria(conexion, (limite,)).fetchall()
        return [dict(fila) for fila in filas]


def menu_auditoria():
    inicializar_base_datos()
    sesion = autenticar(input('Usuario administrador: '), getpass('Contrasena: '))
    if not sesion:
        raise ValueError('Credenciales invalidas.')
    id_admin = sesion['id_usuario']
    verificar_permiso(id_admin, ('Administrador',))
    while True:
        print('\n1. Registrar evento de prueba\n2. Listar auditoria\n0. Salir')
        opcion = input('Opcion: ').strip()
        if opcion == '0':
            return
        if opcion == '1':
            registrar_evento(id_admin, 'PRUEBA', 'Auditoria', 'Verificacion manual del modulo')
            print('[OK] Evento de prueba registrado.')
        elif opcion == '2':
            for fila in listar_auditoria(id_admin):
                print(f"{fila['id_auditoria']} | {fila['fecha']} | {fila['usuario']} | {fila['accion']} | {fila['modulo']} | {fila['resultado']} | {fila['descripcion']}")
        else:
            print('Opcion invalida.')


if __name__ == '__main__':
    try:
        menu_auditoria()
    except (ValueError, PermissionError, sqlite3.Error, OSError) as error:
        print(f'Error: {error}')
    except (KeyboardInterrupt, EOFError):
        print('\nPrograma finalizado.')
