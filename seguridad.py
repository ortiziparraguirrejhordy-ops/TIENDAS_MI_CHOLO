import repositorios as repo
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from contextlib import closing
from base_datos import conectar, inicializar_base_datos, CARPETA_BACKUPS, RUTA_DB


def registrar_error(error):
    CARPETA_BACKUPS.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('mi_cholo.seguridad')
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(CARPETA_BACKUPS / 'errores.log', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        logger.addHandler(handler)
    logger.error('%s', error)


def verificar_conexion(conexion):
    resultados = repo.consultar_integridad(conexion).fetchall()
    if [fila[0] for fila in resultados] != ['ok']:
        raise ValueError('La base de datos presenta problemas de integridad.')
    if repo.consultar_claves_foraneas(conexion).fetchone() is not None:
        raise ValueError('Existen relaciones invalidas entre registros.')
    tablas = {'productos', 'ventas', 'detalle_venta', 'usuarios', 'auditoria'}
    existentes = {fila[0] for fila in repo.consultar_tablas(conexion)}
    if not tablas.issubset(existentes):
        raise ValueError('La copia no contiene las tablas requeridas.')
    return True


def verificar_integridad():
    with closing(conectar()) as conexion:
        return verificar_conexion(conexion)


def abrir_copia(ruta):
    return sqlite3.connect(Path(ruta).resolve().as_uri() + '?mode=ro', uri=True, timeout=10)


def crear_backup(tipo='manual'):
    if tipo not in ('manual', 'automatico', 'preventivo'):
        raise ValueError('Tipo de respaldo invalido.')
    CARPETA_BACKUPS.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    ruta = CARPETA_BACKUPS / f'{tipo}_{fecha}.db'
    temporal = ruta.with_suffix('.tmp')
    try:
        with closing(conectar()) as origen, closing(sqlite3.connect(temporal)) as destino:
            origen.backup(destino)
            verificar_conexion(destino)
        temporal.replace(ruta)
        return ruta
    except (ValueError, sqlite3.Error, OSError):
        temporal.unlink(missing_ok=True)
        raise


def listar_backups():
    CARPETA_BACKUPS.mkdir(parents=True, exist_ok=True)
    return sorted(CARPETA_BACKUPS.glob('*.db'), key=lambda ruta: ruta.stat().st_mtime, reverse=True)


def backup_automatico():
    hoy = datetime.now().strftime('%Y%m%d')
    for ruta in listar_backups():
        if ruta.name.startswith(f'automatico_{hoy}_'):
            try:
                with closing(abrir_copia(ruta)) as conexion:
                    verificar_conexion(conexion)
                return ruta
            except (ValueError, sqlite3.Error, OSError) as error:
                registrar_error(error)
    return crear_backup('automatico')


def restaurar_backup(ruta, confirmacion):
    if confirmacion != 'RESTAURAR':
        raise ValueError('Restauracion cancelada.')
    ruta = Path(ruta).resolve()
    if ruta.parent != CARPETA_BACKUPS.resolve() or ruta.suffix != '.db' or not ruta.is_file() or ruta == RUTA_DB.resolve():
        raise ValueError('Seleccione una copia valida de la carpeta backups.')
    # Ejecutar exclusivamente con las otras instancias del sistema cerradas.
    with closing(abrir_copia(ruta)) as origen:
        verificar_conexion(origen)
        preventivo = crear_backup('preventivo')
        with closing(conectar()) as destino:
            origen.backup(destino)
            verificar_conexion(destino)
    return preventivo


def menu_seguridad():
    while True:
        print('\n=== TIENDAS MI CHOLO - SEGURIDAD ===')
        print('1. Crear copia manual\n2. Listar copias\n3. Verificar integridad\n4. Crear copia diaria\n5. Restaurar copia\n0. Regresar')
        try:
            opcion = input('Seleccione una opcion: ').strip()
            if opcion == '0':
                break
            elif opcion == '1':
                print('[OK]', crear_backup())
            elif opcion == '2':
                for i, ruta in enumerate(listar_backups(), 1):
                    print(i, ruta.name)
            elif opcion == '3':
                verificar_integridad()
                print('[OK] Base de datos integra.')
            elif opcion == '4':
                print('[OK]', backup_automatico())
            elif opcion == '5':
                copias = listar_backups()
                if not copias:
                    print('No existen copias.')
                    continue
                for i, ruta in enumerate(copias, 1):
                    print(i, ruta.name)
                numero = input('Numero de copia: ').strip()
                if not numero.isascii() or not numero.isdigit() or len(numero) > 8 or not 1 <= int(numero) <= len(copias):
                    raise ValueError('Numero invalido.')
                print('ADVERTENCIA: cierre todas las otras instancias del sistema. Se reemplazaran los datos actuales.')
                confirmacion = input('Escriba RESTAURAR para confirmar: ')
                print('[OK] Respaldo previo:', restaurar_backup(copias[int(numero)-1], confirmacion))
            else:
                print('Opcion incorrecta.')
        except (KeyboardInterrupt, EOFError):
            break
        except (ValueError, sqlite3.Error, OSError) as error:
            print('Error:', error)
            try:
                registrar_error(error)
            except OSError:
                print('No se pudo escribir el registro de errores.')


if __name__ == '__main__':
    inicializar_base_datos()
    menu_seguridad()
