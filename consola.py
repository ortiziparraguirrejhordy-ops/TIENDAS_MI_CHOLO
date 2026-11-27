"""Modo consola privado de Tiendas Mi Cholo."""
import sqlite3
from getpass import getpass
from base_datos import inicializar_base_datos
from usuarios import autenticar, verificar_permiso, necesita_administrador
from auditoria import registrar_evento, listar_auditoria
from productos import listar_productos, crear_producto, modificar_producto, eliminar_producto, restaurar_producto
from algoritmos import busqueda_secuencial
from ventas import agregar_al_carrito, quitar_del_carrito, mostrar_carrito, registrar_venta
from inventario import mostrar_resumen_inventario, mostrar_ingresos
from validaciones import formatear_dinero


def mostrar_productos(productos):
    for p in productos:
        print(p['codigo'], p['nombre'], formatear_dinero(p['precio_centavos']), 'Stock:', p['stock'])
    print('Total:', len(productos))


def datos_producto():
    return (input('Codigo: '), input('Nombre: '), input('Categoria: '),
            input('Precio: '), input('Stock: '))


def vender(id_usuario):
    carrito = {}
    while True:
        verificar_permiso(id_usuario)
        print('\n1. Agregar  2. Quitar  3. Ver carrito  4. Confirmar  0. Cancelar')
        opcion = input('Opcion: ')
        try:
            if opcion == '1':
                agregar_al_carrito(carrito, input('Codigo: '), input('Cantidad: '))
            elif opcion == '2':
                quitar_del_carrito(carrito, input('Codigo: '))
            elif opcion == '3':
                mostrar_carrito(carrito)
            elif opcion == '4':
                mostrar_carrito(carrito)
                pago = input('Pago (Efectivo/Yape/Plin/Tarjeta): ')
                if input('Confirmar venta (s/n): ').lower() == 's':
                    print('Venta registrada:', registrar_venta(carrito, pago, id_usuario=id_usuario))
                    return
            elif opcion == '0':
                return
            else:
                print('Opcion invalida.')
        except (ValueError, sqlite3.Error, OSError) as error:
            print('Aviso:', error)


def iniciar_consola():
    inicializar_base_datos()
    if necesita_administrador():
        print('Configure el primer administrador desde la interfaz grafica.')
        return
    print('TIENDAS MI CHOLO | Consola privada')
    try:
        sesion = autenticar(input('Usuario: '), getpass('Contrasena: '))
    except ValueError as error:
        print(error)
        return
    id_usuario = sesion['id_usuario']
    registrar_evento(id_usuario, 'LOGIN', 'Usuarios', 'Inicio de sesion consola')
    try:
        while True:
            sesion = verificar_permiso(id_usuario)
            admin = sesion['rol'] == 'Administrador'
            print('\nUsuario:', sesion['usuario'], '|', sesion['rol'])
            print('1. Productos  2. Buscar  3. Nueva venta  4. Inventario  0. Salir')
            if admin:
                print('5. Crear  6. Modificar  7. Eliminar  8. Restaurar  9. Ingresos  10. Auditoria')
            opcion = input('Opcion: ')
            try:
                if opcion == '0':
                    break
                if opcion == '1':
                    mostrar_productos(listar_productos())
                elif opcion == '2':
                    termino = input('Buscar: ')
                    resultados = busqueda_secuencial(listar_productos(), termino)
                    registrar_evento(id_usuario, 'BUSCAR', 'Productos', 'Busqueda: ' + termino)
                    mostrar_productos(resultados)
                elif opcion == '3':
                    vender(id_usuario)
                elif opcion == '4':
                    mostrar_resumen_inventario()
                elif admin and opcion in ('5', '6', '7', '8', '9', '10'):
                    verificar_permiso(id_usuario, ('Administrador',))
                    if opcion == '5':
                        crear_producto(*datos_producto(), id_usuario=id_usuario)
                    elif opcion == '6':
                        codigo = input('Codigo actual: ')
                        modificar_producto(codigo, *datos_producto(), id_usuario=id_usuario)
                    elif opcion == '7':
                        codigo = input('Codigo: ')
                        if input('Desactivar (s/n): ').lower() == 's':
                            eliminar_producto(codigo, id_usuario=id_usuario)
                    elif opcion == '8':
                        restaurar_producto(input('Codigo: '), id_usuario=id_usuario)
                    elif opcion == '9':
                        mostrar_ingresos()
                    else:
                        for evento in listar_auditoria(id_usuario):
                            print(evento['fecha'], evento['usuario'], evento['accion'], evento['descripcion'])
                else:
                    print('Opcion invalida o no autorizada.')
            except (ValueError, sqlite3.Error, OSError) as error:
                print('Aviso:', error)
    finally:
        registrar_evento(id_usuario, 'LOGOUT', 'Usuarios', 'Cierre de sesion consola')


if __name__ == '__main__':
    try:
        iniciar_consola()
    except (KeyboardInterrupt, EOFError):
        print('\nSesion finalizada.')
    except (ValueError, sqlite3.Error, OSError) as error:
        print('Error:', error)
