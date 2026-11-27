
import repositorios as repo
import sqlite3
from usuarios import _autorizar
from auditoria import registrar_auditoria
from contextlib import closing

from base_datos import conectar, inicializar_base_datos
from repositorios import (consultar_productos, consultar_producto, insertar_producto,
                          actualizar_producto, actualizar_estado_producto)

from validaciones import (
    validar_codigo,
    validar_nombre,
    validar_categoria,
    validar_precio,
    validar_stock,
    formatear_dinero
)


def listar_productos(incluir_inactivos=False):
    """Retorna una lista de productos registrados."""

    with closing(conectar()) as conexion:

        registros = consultar_productos(conexion, incluir_inactivos)

        return [dict(registro) for registro in registros]


def obtener_producto(codigo):
    """Busca un producto mediante su codigo."""

    codigo = validar_codigo(codigo)

    with closing(conectar()) as conexion:

        producto = consultar_producto(conexion, codigo)

        if producto is None:
            raise ValueError("El producto no existe.")

        return dict(producto)


def crear_producto(codigo, nombre, categoria, precio, stock, id_usuario=None):
    """Registra un nuevo producto en la base de datos."""

    codigo = validar_codigo(codigo)
    nombre = validar_nombre(nombre)
    categoria = validar_categoria(categoria)
    precio = validar_precio(precio)
    stock = validar_stock(stock)

    try:

        with closing(conectar()) as conexion:
            with conexion:

                repo.iniciar_transaccion(conexion)
                _autorizar(conexion, id_usuario, ('Administrador',))
                previo = consultar_producto(conexion, codigo)
                cursor = insertar_producto(conexion, codigo, nombre, categoria, precio, stock)

                posterior = consultar_producto(conexion, codigo)
                registrar_auditoria(conexion, id_usuario, "INSERTAR", "Productos", f"Producto {codigo}", anteriores=dict(previo) if previo else None, nuevos=dict(posterior))
                return cursor.lastrowid

    except sqlite3.IntegrityError as error:

        raise ValueError(
            "Codigo duplicado o datos no permitidos."
        ) from error


def modificar_producto(
    codigo_actual,
    codigo_nuevo,
    nombre,
    categoria,
    precio,
    stock,
    id_usuario=None
):
    """Actualiza los datos de un producto activo."""

    codigo_actual = validar_codigo(codigo_actual)
    codigo_nuevo = validar_codigo(codigo_nuevo)
    nombre = validar_nombre(nombre)
    categoria = validar_categoria(categoria)
    precio = validar_precio(precio)
    stock = validar_stock(stock)

    try:

        with closing(conectar()) as conexion:
            with conexion:

                repo.iniciar_transaccion(conexion)
                _autorizar(conexion, id_usuario, ('Administrador',))
                previo = consultar_producto(conexion, codigo_actual)
                cursor = actualizar_producto(conexion, codigo_actual, codigo_nuevo, nombre, categoria, precio, stock)

                if cursor.rowcount == 0:
                    raise ValueError(
                        "El producto no existe o esta inactivo."
                    )

                posterior = consultar_producto(conexion, codigo_nuevo)
                registrar_auditoria(conexion, id_usuario, "MODIFICAR", "Productos", f"Producto {codigo_nuevo}", anteriores=dict(previo) if previo else None, nuevos=dict(posterior))
                return True

    except sqlite3.IntegrityError as error:

        raise ValueError(
            "El nuevo codigo ya existe o los datos son invalidos."
        ) from error


def eliminar_producto(codigo, id_usuario=None):
    """Desactiva un producto sin borrar su historial."""

    codigo = validar_codigo(codigo)

    with closing(conectar()) as conexion:
        with conexion:

            repo.iniciar_transaccion(conexion)
            _autorizar(conexion, id_usuario, ('Administrador',))
            previo = consultar_producto(conexion, codigo)
            cursor = actualizar_estado_producto(conexion, codigo, 0)

            if cursor.rowcount == 0:
                raise ValueError(
                    "El producto no existe o ya esta eliminado."
                )

            posterior = consultar_producto(conexion, codigo)
            registrar_auditoria(conexion, id_usuario, "ELIMINAR", "Productos", f"Producto {codigo}", anteriores=dict(previo) if previo else None, nuevos=dict(posterior))
            return True


def restaurar_producto(codigo, id_usuario=None):
    """Recupera un producto previamente desactivado."""

    codigo = validar_codigo(codigo)

    with closing(conectar()) as conexion:
        with conexion:

            repo.iniciar_transaccion(conexion)
            _autorizar(conexion, id_usuario, ('Administrador',))
            previo = consultar_producto(conexion, codigo)
            cursor = actualizar_estado_producto(conexion, codigo, 1)

            if cursor.rowcount == 0:
                raise ValueError(
                    "El producto no existe o ya esta activo."
                )

            posterior = consultar_producto(conexion, codigo)
            registrar_auditoria(conexion, id_usuario, "RESTAURAR", "Productos", f"Producto {codigo}", anteriores=dict(previo) if previo else None, nuevos=dict(posterior))
            return True


def mostrar_productos(incluir_inactivos=False):
    """Muestra los productos registrados en consola."""

    productos = listar_productos(incluir_inactivos)

    if not productos:
        print("No hay productos registrados.")
        return

    print("-" * 85)

    print(
        f"{'CODIGO':<12}"
        f"{'PRODUCTO':<25}"
        f"{'PRECIO':<18}"
        f"{'STOCK':<12}"
        f"{'ESTADO'}"
    )

    print("-" * 85)

    for producto in productos:

        estado = (
            "Activo" if producto["activo"]
            else "Inactivo"
        )

        precio = formatear_dinero(
            producto["precio_centavos"]
        )

        print(
            f"{producto['codigo']:<12}"
            f"{producto['nombre'][:24]:<25}"
            f"{precio:<18}"
            f"{producto['stock']:<12}"
            f"{estado}"
        )

    print("-" * 85)


def menu_productos():
    """Menu de prueba del CRUD de productos."""

    while True:

        print("\n===== GESTION DE PRODUCTOS =====")
        print("1. Listar productos")
        print("2. Crear producto")
        print("3. Modificar producto")
        print("4. Eliminar producto")
        print("5. Restaurar producto")
        print("6. Listar todos los productos")
        print("0. Salir")

        try:

            opcion = input(
                "Seleccione una opcion: "
            ).strip()

            if opcion == "1":

                mostrar_productos()

            elif opcion == "2":

                codigo = input("Codigo: ")
                nombre = input("Nombre: ")
                categoria = input("Categoria: ")
                precio = input("Precio S/: ")
                stock = input("Stock: ")

                crear_producto(
                    codigo,
                    nombre,
                    categoria,
                    precio,
                    stock
                )

                print("Producto registrado correctamente.")

            elif opcion == "3":

                codigo_actual = input("Codigo actual: ")

                producto = obtener_producto(codigo_actual)

                if not producto["activo"]:
                    raise ValueError("El producto esta inactivo.")

                print("Producto:", producto["nombre"])

                codigo_nuevo = input("Nuevo codigo: ")
                nombre = input("Nuevo nombre: ")
                categoria = input("Nueva categoria: ")
                precio = input("Nuevo precio S/: ")
                stock = input("Nuevo stock: ")

                modificar_producto(
                    codigo_actual,
                    codigo_nuevo,
                    nombre,
                    categoria,
                    precio,
                    stock
                )

                print("Producto modificado correctamente.")

            elif opcion == "4":

                codigo = input("Codigo del producto: ")

                producto = obtener_producto(codigo)

                print("Producto:", producto["nombre"])

                confirmar = input(
                    "Confirmar eliminacion (S/N): "
                ).strip().upper()

                if confirmar == "S":

                    eliminar_producto(codigo)

                    print("Producto eliminado correctamente.")

                else:

                    print("Operacion cancelada.")

            elif opcion == "5":

                codigo = input("Codigo del producto: ")

                restaurar_producto(codigo)

                print("Producto restaurado correctamente.")

            elif opcion == "6":

                mostrar_productos(True)

            elif opcion == "0":

                print("Saliendo del modulo de productos.")
                break

            else:

                print("Opcion invalida.")

        except ValueError as error:

            print(f"AVISO: {error}")

        except (sqlite3.Error, OSError) as error:

            print(f"ERROR DE ALMACENAMIENTO: {error}")

        except (KeyboardInterrupt, EOFError):

            print("\nModulo finalizado.")
            break


if __name__ == "__main__":

    try:

        inicializar_base_datos()
        menu_productos()

    except (sqlite3.Error, OSError) as error:

        print(f"No se pudo iniciar el modulo: {error}")
