
import sqlite3
from datetime import datetime
from contextlib import closing

from base_datos import conectar, inicializar_base_datos
from productos import listar_productos
from validaciones import formatear_dinero, validar_stock


STOCK_MINIMO = 10


def obtener_resumen_inventario():
    """Calcula las estadisticas generales del inventario."""

    productos = listar_productos()

    total_productos = len(productos)
    total_unidades = 0
    valor_inventario = 0
    stock_bajo = 0
    agotados = 0

    for producto in productos:

        stock = producto["stock"]
        precio = producto["precio_centavos"]

        total_unidades += stock
        valor_inventario += stock * precio

        if stock == 0:
            agotados += 1

        elif stock <= STOCK_MINIMO:
            stock_bajo += 1

    return {
        "total_productos": total_productos,
        "total_unidades": total_unidades,
        "valor_inventario": valor_inventario,
        "stock_bajo": stock_bajo,
        "agotados": agotados
    }


def obtener_stock_bajo(limite=STOCK_MINIMO):
    """Retorna productos con pocas unidades."""

    limite = validar_stock(limite)

    productos = listar_productos()
    resultados = []

    for producto in productos:

        if 0 < producto["stock"] <= limite:

            resultados.append(producto)

    return resultados


def obtener_productos_agotados():
    """Retorna productos sin existencias."""

    productos = listar_productos()
    resultados = []

    for producto in productos:

        if producto["stock"] == 0:

            resultados.append(producto)

    return resultados


def obtener_ingresos():
    """Calcula ingresos diarios, mensuales y totales."""

    hoy = datetime.now().strftime("%Y-%m-%d")
    mes = datetime.now().strftime("%Y-%m")

    with closing(conectar()) as conexion:

        resultado = conexion.execute("""
            SELECT
                COUNT(*) AS total_ventas,

                COALESCE(
                    SUM(total_centavos), 0
                ) AS ingresos_totales,

                COALESCE(
                    SUM(
                        CASE
                            WHEN substr(fecha, 1, 10) = ?
                            THEN total_centavos
                            ELSE 0
                        END
                    ), 0
                ) AS ingresos_hoy,

                COALESCE(
                    SUM(
                        CASE
                            WHEN substr(fecha, 1, 7) = ?
                            THEN total_centavos
                            ELSE 0
                        END
                    ), 0
                ) AS ingresos_mes

            FROM ventas
        """, (hoy, mes)).fetchone()

        return dict(resultado)


def obtener_ingresos_por_pago():
    """Agrupa los ingresos por metodo de pago."""

    with closing(conectar()) as conexion:

        registros = conexion.execute("""
            SELECT
                metodo_pago,
                COUNT(*) AS cantidad_ventas,
                SUM(total_centavos) AS ingresos

            FROM ventas

            GROUP BY metodo_pago

            ORDER BY ingresos DESC
        """).fetchall()

        return [dict(registro) for registro in registros]


def obtener_productos_mas_vendidos(limite=5):
    """Retorna los productos con mayores ventas."""

    with closing(conectar()) as conexion:

        registros = conexion.execute("""
            SELECT
                p.codigo,
                p.nombre,

                SUM(d.cantidad) AS unidades_vendidas,

                SUM(d.subtotal_centavos) AS ingresos

            FROM detalle_venta AS d

            INNER JOIN productos AS p
                ON d.id_producto = p.id_producto

            GROUP BY p.id_producto, p.codigo, p.nombre

            ORDER BY unidades_vendidas DESC,
                     p.id_producto ASC

            LIMIT ?
        """, (limite,)).fetchall()

        return [dict(registro) for registro in registros]


def mostrar_resumen_inventario():
    """Muestra las estadisticas del inventario."""

    resumen = obtener_resumen_inventario()

    print("\n===== RESUMEN DEL INVENTARIO =====")

    print(
        "Productos activos:",
        resumen["total_productos"]
    )

    print(
        "Unidades disponibles:",
        resumen["total_unidades"]
    )

    print(
        "Valor del inventario:",
        formatear_dinero(
            resumen["valor_inventario"]
        )
    )

    print(
        "Productos con stock bajo:",
        resumen["stock_bajo"]
    )

    print(
        "Productos agotados:",
        resumen["agotados"]
    )


def mostrar_ingresos():
    """Muestra los ingresos registrados."""

    ingresos = obtener_ingresos()

    print("\n===== RESUMEN DE INGRESOS =====")

    print(
        "Ventas realizadas:",
        ingresos["total_ventas"]
    )

    print(
        "Ingresos de hoy:",
        formatear_dinero(
            ingresos["ingresos_hoy"]
        )
    )

    print(
        "Ingresos del mes:",
        formatear_dinero(
            ingresos["ingresos_mes"]
        )
    )

    print(
        "Ingresos totales:",
        formatear_dinero(
            ingresos["ingresos_totales"]
        )
    )


def mostrar_alertas():
    """Muestra productos con stock bajo o agotado."""

    stock_bajo = obtener_stock_bajo()
    agotados = obtener_productos_agotados()

    print("\n===== ALERTAS DE INVENTARIO =====")

    if not stock_bajo and not agotados:

        print("No existen alertas de inventario.")
        return

    for producto in stock_bajo:

        print(
            f"STOCK BAJO | {producto['codigo']} | "
            f"{producto['nombre']} | "
            f"Unidades: {producto['stock']}"
        )

    for producto in agotados:

        print(
            f"AGOTADO | {producto['codigo']} | "
            f"{producto['nombre']}"
        )


def mostrar_ingresos_por_pago():
    """Muestra los ingresos segun el metodo de pago."""

    registros = obtener_ingresos_por_pago()

    print("\n===== INGRESOS POR METODO DE PAGO =====")

    if not registros:

        print("No existen ventas registradas.")
        return

    for registro in registros:

        print(
            f"{registro['metodo_pago']} | "
            f"Ventas: {registro['cantidad_ventas']} | "
            f"{formatear_dinero(registro['ingresos'])}"
        )


def mostrar_productos_mas_vendidos():
    """Muestra los cinco productos mas vendidos."""

    productos = obtener_productos_mas_vendidos()

    print("\n===== PRODUCTOS MAS VENDIDOS =====")

    if not productos:

        print("No existen ventas registradas.")
        return

    for posicion, producto in enumerate(productos, 1):

        print(
            f"{posicion}. {producto['nombre']} | "
            f"Unidades vendidas: "
            f"{producto['unidades_vendidas']} | "
            f"{formatear_dinero(producto['ingresos'])}"
        )


def menu_inventario():
    """Menu de inventario y estadisticas."""

    while True:

        print("\n===== INVENTARIO Y ESTADISTICAS =====")
        print("1. Resumen del inventario")
        print("2. Resumen de ingresos")
        print("3. Alertas de stock")
        print("4. Ingresos por metodo de pago")
        print("5. Productos mas vendidos")
        print("6. Resumen general")
        print("0. Salir")

        try:

            opcion = input(
                "Seleccione una opcion: "
            ).strip()

            if opcion == "1":

                mostrar_resumen_inventario()

            elif opcion == "2":

                mostrar_ingresos()

            elif opcion == "3":

                mostrar_alertas()

            elif opcion == "4":

                mostrar_ingresos_por_pago()

            elif opcion == "5":

                mostrar_productos_mas_vendidos()

            elif opcion == "6":

                mostrar_resumen_inventario()
                mostrar_ingresos()
                mostrar_alertas()
                mostrar_ingresos_por_pago()
                mostrar_productos_mas_vendidos()

            elif opcion == "0":

                print("Modulo finalizado.")
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
        menu_inventario()

    except (sqlite3.Error, OSError) as error:

        print(f"No se pudo iniciar el modulo: {error}")
