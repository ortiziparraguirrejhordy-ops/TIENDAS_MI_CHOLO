
import csv
import sqlite3

from datetime import datetime
from decimal import Decimal
from contextlib import closing

from base_datos import (
    conectar,
    inicializar_base_datos,
    CARPETA_REPORTES
)

from productos import listar_productos

from inventario import (
    obtener_ingresos,
    STOCK_MINIMO
)

from ventas import listar_ventas


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def convertir_dinero(centavos):

    return f"{Decimal(centavos) / 100:.2f}"


def proteger_celda(valor):

    # Evita la interpretacion de formulas
    # peligrosas al abrir el CSV en Excel.

    if isinstance(valor, str):

        if valor.lstrip().startswith(
            ("=", "+", "-", "@", "\t", "\r", "\n")
        ):

            return "'" + valor

    return valor


def guardar_archivo_csv(nombre, encabezados, filas):

    CARPETA_REPORTES.mkdir(
        parents=True,
        exist_ok=True
    )

    fecha = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    ruta = CARPETA_REPORTES / f"{nombre}_{fecha}.csv"

    with open(
        ruta,
        mode="x",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.writer(
            archivo,
            delimiter=";"
        )

        escritor.writerow(encabezados)

        for fila in filas:

            escritor.writerow([
                proteger_celda(valor)
                for valor in fila
            ])

    return ruta


# ==========================================
# EXPORTAR PRODUCTOS
# ==========================================

def exportar_productos():

    productos = listar_productos(
        incluir_inactivos=True
    )

    encabezados = [
        "Codigo",
        "Nombre",
        "Categoria",
        "Precio unitario (S/)",
        "Stock",
        "Estado"
    ]

    filas = []

    for producto in productos:

        estado = (
            "Activo"
            if producto["activo"]
            else "Inactivo"
        )

        filas.append([
            producto["codigo"],
            producto["nombre"],
            producto["categoria"],
            convertir_dinero(
                producto["precio_centavos"]
            ),
            producto["stock"],
            estado
        ])

    return guardar_archivo_csv(
        "productos",
        encabezados,
        filas
    )


# ==========================================
# EXPORTAR VENTAS
# ==========================================

def exportar_ventas():

    ventas = listar_ventas()

    encabezados = [
        "ID de venta",
        "Fecha y hora",
        "Metodo de pago",
        "Total (S/)"
    ]

    filas = []

    for venta in ventas:

        filas.append([
            f"V-{venta['id_venta']:06d}",
            venta["fecha"],
            venta["metodo_pago"],
            convertir_dinero(
                venta["total_centavos"]
            )
        ])

    return guardar_archivo_csv(
        "ventas",
        encabezados,
        filas
    )


# ==========================================
# EXPORTAR DETALLE DE VENTAS
# ==========================================

def exportar_detalle_ventas():

    with closing(conectar()) as conexion:

        registros = conexion.execute("""
            SELECT
                v.id_venta,
                v.fecha,
                p.codigo,
                p.nombre,
                d.cantidad,
                d.precio_centavos,
                d.subtotal_centavos
            FROM detalle_venta AS d
            INNER JOIN ventas AS v
                ON d.id_venta = v.id_venta
            INNER JOIN productos AS p
                ON d.id_producto = p.id_producto
            ORDER BY v.id_venta DESC, d.id_detalle
        """).fetchall()

    encabezados = [
        "ID de venta",
        "Fecha",
        "Codigo de producto",
        "Producto",
        "Cantidad",
        "Precio unitario (S/)",
        "Subtotal (S/)"
    ]

    filas = []

    for registro in registros:

        filas.append([
            f"V-{registro['id_venta']:06d}",
            registro["fecha"],
            registro["codigo"],
            registro["nombre"],
            registro["cantidad"],
            convertir_dinero(
                registro["precio_centavos"]
            ),
            convertir_dinero(
                registro["subtotal_centavos"]
            )
        ])

    return guardar_archivo_csv(
        "detalle_ventas",
        encabezados,
        filas
    )


# ==========================================
# EXPORTAR INVENTARIO
# ==========================================

def exportar_inventario():

    productos = listar_productos()

    encabezados = [
        "Codigo",
        "Producto",
        "Categoria",
        "Stock",
        "Precio unitario (S/)",
        "Valor de existencias (S/)",
        "Estado"
    ]

    filas = []

    for producto in productos:

        stock = producto["stock"]

        precio = producto["precio_centavos"]

        if stock == 0:

            estado = "Agotado"

        elif stock <= STOCK_MINIMO:

            estado = "Stock bajo"

        else:

            estado = "Disponible"

        filas.append([
            producto["codigo"],
            producto["nombre"],
            producto["categoria"],
            stock,
            convertir_dinero(precio),
            convertir_dinero(stock * precio),
            estado
        ])

    return guardar_archivo_csv(
        "inventario",
        encabezados,
        filas
    )


# ==========================================
# EXPORTAR INGRESOS
# ==========================================

def exportar_ingresos():

    ingresos = obtener_ingresos()

    encabezados = [
        "Indicador",
        "Valor",
        "Unidad"
    ]

    filas = [
        [
            "Fecha de generacion",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "Fecha"
        ],
        [
            "Total de ventas",
            ingresos["total_ventas"],
            "Operaciones"
        ],
        [
            "Ingresos diarios",
            convertir_dinero(
                ingresos["ingresos_hoy"]
            ),
            "Soles"
        ],
        [
            "Ingresos mensuales",
            convertir_dinero(
                ingresos["ingresos_mes"]
            ),
            "Soles"
        ],
        [
            "Ingresos totales",
            convertir_dinero(
                ingresos["ingresos_totales"]
            ),
            "Soles"
        ]
    ]

    return guardar_archivo_csv(
        "ingresos",
        encabezados,
        filas
    )


# ==========================================
# EXPORTACION GENERAL
# ==========================================

def exportar_todo():

    funciones = [
        exportar_productos,
        exportar_ventas,
        exportar_detalle_ventas,
        exportar_inventario,
        exportar_ingresos
    ]

    archivos = []

    for funcion in funciones:

        archivos.append(funcion())

    return archivos


# ==========================================
# MENU DE REPORTES
# ==========================================

def menu_reportes():

    opciones = {
        "1": exportar_productos,
        "2": exportar_ventas,
        "3": exportar_detalle_ventas,
        "4": exportar_inventario,
        "5": exportar_ingresos,
        "6": exportar_todo
    }

    while True:

        print("\n" + "=" * 50)
        print("TIENDAS MI CHOLO - REPORTES CSV")
        print("=" * 50)

        print("1. Exportar productos")
        print("2. Exportar ventas")
        print("3. Exportar detalle de ventas")
        print("4. Exportar inventario")
        print("5. Exportar ingresos")
        print("6. Exportar todos los reportes")
        print("0. Regresar")

        try:

            opcion = input(
                "\nSeleccione una opcion: "
            ).strip()

            if opcion == "0":

                break

            if opcion not in opciones:

                print("Opcion incorrecta.")

                continue

            resultado = opciones[opcion]()

            if isinstance(resultado, list):

                print("\nArchivos generados:")

                for archivo in resultado:

                    print(f"[OK] {archivo}")

            else:

                print("\nArchivo generado correctamente:")

                print(f"[OK] {resultado}")

        except (ValueError, sqlite3.Error, OSError) as error:

            print(f"Error: {error}")

        except (KeyboardInterrupt, EOFError):

            print("\nRegresando al menu principal.")

            break


# ==========================================
# EJECUCION DIRECTA
# ==========================================

if __name__ == "__main__":

    try:

        inicializar_base_datos()

        menu_reportes()

    except (sqlite3.Error, OSError) as error:

        print(f"Error al iniciar: {error}")
