
import sqlite3
from datetime import datetime
from contextlib import closing

from base_datos import conectar, inicializar_base_datos
from productos import obtener_producto

from validaciones import (
    validar_codigo,
    validar_cantidad,
    validar_metodo_pago,
    validar_entero,
    formatear_dinero
)


def agregar_al_carrito(carrito, codigo, cantidad):
    """Agrega un producto al carrito de compras."""

    codigo = validar_codigo(codigo)
    cantidad = validar_cantidad(cantidad)

    producto = obtener_producto(codigo)

    if not producto["activo"]:
        raise ValueError("El producto esta inactivo.")

    cantidad_anterior = 0

    if codigo in carrito:
        cantidad_anterior = carrito[codigo]["cantidad"]

    cantidad_total = cantidad_anterior + cantidad

    if cantidad_total > producto["stock"]:
        raise ValueError(
            f"Stock insuficiente. Disponible: {producto['stock']}"
        )

    carrito[codigo] = {
        "codigo": codigo,
        "nombre": producto["nombre"],
        "cantidad": cantidad_total,
        "precio_centavos": producto["precio_centavos"],
        "subtotal_centavos": (
            cantidad_total * producto["precio_centavos"]
        )
    }

    return carrito


def quitar_del_carrito(carrito, codigo):
    """Retira un producto del carrito."""

    codigo = validar_codigo(codigo)

    if codigo not in carrito:
        raise ValueError("El producto no esta en el carrito.")

    del carrito[codigo]


def calcular_total(carrito):
    """Calcula el importe total de la compra."""

    total = 0

    for producto in carrito.values():

        total += producto["subtotal_centavos"]

    return total


def mostrar_carrito(carrito):
    """Muestra los productos seleccionados."""

    if not carrito:
        print("El carrito esta vacio.")
        return

    print("\n" + "-" * 90)

    print(
        f"{'CODIGO':<22}"
        f"{'PRODUCTO':<25}"
        f"{'CANT.':<10}"
        f"{'PRECIO':<16}"
        f"{'SUBTOTAL'}"
    )

    print("-" * 90)

    for producto in carrito.values():

        precio = formatear_dinero(
            producto["precio_centavos"]
        )

        subtotal = formatear_dinero(
            producto["subtotal_centavos"]
        )

        print(
            f"{producto['codigo']:<22}"
            f"{producto['nombre'][:24]:<25}"
            f"{producto['cantidad']:<10}"
            f"{precio:<16}"
            f"{subtotal}"
        )

    print("-" * 90)

    print(
        "TOTAL:",
        formatear_dinero(calcular_total(carrito))
    )


def registrar_venta(carrito, metodo_pago):
    """Registra una venta y actualiza el inventario."""

    if not carrito:
        raise ValueError("No se puede registrar una venta vacia.")

    metodo_pago = validar_metodo_pago(metodo_pago)

    fecha = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    with closing(conectar()) as conexion:

        with conexion:

            conexion.execute("BEGIN IMMEDIATE")

            detalles = []
            total = 0

            for codigo, item in carrito.items():

                codigo = validar_codigo(codigo)

                cantidad = validar_cantidad(
                    item["cantidad"]
                )

                producto = conexion.execute("""
                    SELECT * FROM productos
                    WHERE codigo = ?
                    AND activo = 1
                """, (codigo,)).fetchone()

                if producto is None:
                    raise ValueError(
                        f"Producto no disponible: {codigo}"
                    )

                if cantidad > producto["stock"]:
                    raise ValueError(
                        f"Stock insuficiente para {codigo}."
                    )

                precio = producto["precio_centavos"]

                if precio != item["precio_centavos"]:
                    raise ValueError(
                        f"El precio de {codigo} cambio. "
                        "Retirelo y agreguelo nuevamente."
                    )

                subtotal = cantidad * precio

                total += subtotal

                detalles.append((
                    producto["id_producto"],
                    cantidad,
                    precio,
                    subtotal
                ))

            cursor = conexion.execute("""
                INSERT INTO ventas (
                    fecha,
                    total_centavos,
                    metodo_pago
                )
                VALUES (?, ?, ?)
            """, (
                fecha,
                total,
                metodo_pago
            ))

            id_venta = cursor.lastrowid

            for detalle in detalles:

                id_producto, cantidad, precio, subtotal = detalle

                conexion.execute("""
                    INSERT INTO detalle_venta (
                        id_venta,
                        id_producto,
                        cantidad,
                        precio_centavos,
                        subtotal_centavos
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    id_venta,
                    id_producto,
                    cantidad,
                    precio,
                    subtotal
                ))

                cursor_stock = conexion.execute("""
                    UPDATE productos
                    SET stock = stock - ?
                    WHERE id_producto = ?
                    AND stock >= ?
                    AND activo = 1
                """, (
                    cantidad,
                    id_producto,
                    cantidad
                ))

                if cursor_stock.rowcount != 1:
                    raise ValueError(
                        "No se pudo actualizar el inventario."
                    )

    carrito.clear()

    return id_venta


def listar_ventas():
    """Retorna el historial de ventas registradas."""

    with closing(conectar()) as conexion:

        registros = conexion.execute("""
            SELECT *
            FROM ventas
            ORDER BY id_venta DESC
        """).fetchall()

        return [dict(registro) for registro in registros]


def obtener_detalle_venta(id_venta):
    """Consulta los productos de una venta."""

    id_venta = validar_entero(
        id_venta,
        "ID de venta",
        1,
        9223372036854775807
    )

    with closing(conectar()) as conexion:

        venta = conexion.execute("""
            SELECT *
            FROM ventas
            WHERE id_venta = ?
        """, (id_venta,)).fetchone()

        if venta is None:
            raise ValueError("La venta no existe.")

        detalles = conexion.execute("""
            SELECT
                p.codigo,
                p.nombre,
                d.cantidad,
                d.precio_centavos,
                d.subtotal_centavos
            FROM detalle_venta AS d
            INNER JOIN productos AS p
                ON d.id_producto = p.id_producto
            WHERE d.id_venta = ?
            ORDER BY d.id_detalle
        """, (id_venta,)).fetchall()

        return {
            "venta": dict(venta),
            "detalles": [
                dict(detalle) for detalle in detalles
            ]
        }


def mostrar_historial():
    """Muestra todas las ventas almacenadas."""

    ventas = listar_ventas()

    if not ventas:
        print("No hay ventas registradas.")
        return

    print("\n" + "-" * 75)

    print(
        f"{'ID':<8}"
        f"{'FECHA Y HORA':<25}"
        f"{'METODO DE PAGO':<20}"
        f"{'TOTAL'}"
    )

    print("-" * 75)

    total_ingresos = 0

    for venta in ventas:

        total_ingresos += venta["total_centavos"]

        total = formatear_dinero(
            venta["total_centavos"]
        )

        print(
            f"{venta['id_venta']:<8}"
            f"{venta['fecha']:<25}"
            f"{venta['metodo_pago']:<20}"
            f"{total}"
        )

    print("-" * 75)

    print("Ventas realizadas:", len(ventas))

    print(
        "Ingresos totales:",
        formatear_dinero(total_ingresos)
    )


def mostrar_detalle_venta(id_venta):
    """Muestra el comprobante interno de una venta."""

    resultado = obtener_detalle_venta(id_venta)

    venta = resultado["venta"]

    print("\n===== TIENDAS MI CHOLO =====")

    print("Venta Nro:", venta["id_venta"])
    print("Fecha:", venta["fecha"])
    print("Pago:", venta["metodo_pago"])

    print("-" * 50)

    for producto in resultado["detalles"]:

        subtotal = formatear_dinero(
            producto["subtotal_centavos"]
        )

        print(
            f"{producto['nombre']} | "
            f"Cantidad: {producto['cantidad']} | "
            f"{subtotal}"
        )

    print("-" * 50)

    print(
        "TOTAL:",
        formatear_dinero(venta["total_centavos"])
    )

    print("============================")


def menu_ventas():
    """Menu de prueba del modulo de ventas."""

    carrito = {}

    while True:

        print("\n===== GESTION DE VENTAS =====")
        print("1. Agregar producto al carrito")
        print("2. Quitar producto del carrito")
        print("3. Mostrar carrito")
        print("4. Confirmar venta")
        print("5. Historial de ventas")
        print("6. Consultar detalle de venta")
        print("7. Vaciar carrito")
        print("0. Salir")

        try:

            opcion = input(
                "Seleccione una opcion: "
            ).strip()

            if opcion == "1":

                codigo = input("Codigo del producto: ")
                cantidad = input("Cantidad: ")

                agregar_al_carrito(
                    carrito, codigo, cantidad
                )

                print("Producto agregado correctamente.")

            elif opcion == "2":

                codigo = input("Codigo del producto: ")

                quitar_del_carrito(carrito, codigo)

                print("Producto retirado del carrito.")

            elif opcion == "3":

                mostrar_carrito(carrito)

            elif opcion == "4":

                if not carrito:
                    raise ValueError("El carrito esta vacio.")

                mostrar_carrito(carrito)

                print("\nMetodos de pago:")
                print("1. Efectivo")
                print("2. Yape")
                print("3. Plin")
                print("4. Tarjeta")

                metodos = {
                    "1": "Efectivo",
                    "2": "Yape",
                    "3": "Plin",
                    "4": "Tarjeta"
                }

                seleccion = input(
                    "Seleccione metodo de pago: "
                ).strip()

                if seleccion not in metodos:
                    raise ValueError(
                        "Metodo de pago incorrecto."
                    )

                confirmar = input(
                    "Confirmar venta (S/N): "
                ).strip().upper()

                if confirmar == "S":

                    id_venta = registrar_venta(
                        carrito,
                        metodos[seleccion]
                    )

                    print("Venta registrada correctamente.")

                    mostrar_detalle_venta(id_venta)

                else:

                    print("Venta cancelada.")

            elif opcion == "5":

                mostrar_historial()

            elif opcion == "6":

                id_venta = input("ID de la venta: ")

                mostrar_detalle_venta(id_venta)

            elif opcion == "7":

                carrito.clear()

                print("Carrito vaciado.")

            elif opcion == "0":

                print("Modulo de ventas finalizado.")
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
        menu_ventas()

    except (sqlite3.Error, OSError) as error:

        print(f"No se pudo iniciar el modulo: {error}")
