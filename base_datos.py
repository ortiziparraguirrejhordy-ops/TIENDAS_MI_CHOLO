
import sqlite3
from pathlib import Path
from contextlib import closing


# Ubicación de las carpetas del proyecto
RUTA_BASE = Path(__file__).resolve().parent
CARPETA_DATOS = RUTA_BASE / "datos"
CARPETA_BACKUPS = RUTA_BASE / "backups"
CARPETA_REPORTES = RUTA_BASE / "reportes"

RUTA_DB = CARPETA_DATOS / "tienda_mi_cholo.db"


def crear_carpetas():
    """Crea las carpetas necesarias del sistema."""

    for carpeta in (
        CARPETA_DATOS,
        CARPETA_BACKUPS,
        CARPETA_REPORTES
    ):
        carpeta.mkdir(parents=True, exist_ok=True)


def conectar():
    """Establece una conexión con SQLite."""

    crear_carpetas()

    conexion = sqlite3.connect(
        RUTA_DB,
        timeout=10
    )

    conexion.row_factory = sqlite3.Row

    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA synchronous = FULL")

    return conexion


def inicializar_base_datos():
    """Crea las tablas necesarias del sistema."""

    with closing(conectar()) as conexion:
        with conexion:

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE
                        CHECK(length(codigo) BETWEEN 1 AND 20),
                    nombre TEXT NOT NULL
                        CHECK(length(nombre) BETWEEN 2 AND 60),
                    categoria TEXT NOT NULL
                        CHECK(length(categoria) BETWEEN 2 AND 40),
                    precio_centavos INTEGER NOT NULL
                        CHECK(precio_centavos BETWEEN 1 AND 1000000),
                    stock INTEGER NOT NULL DEFAULT 0
                        CHECK(stock BETWEEN 0 AND 100000),
                    activo INTEGER NOT NULL DEFAULT 1
                        CHECK(activo IN (0, 1))
                )
            """)

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    total_centavos INTEGER NOT NULL
                        CHECK(total_centavos > 0),
                    metodo_pago TEXT NOT NULL
                        CHECK(metodo_pago IN (
                            'Efectivo', 'Yape', 'Plin', 'Tarjeta'
                        ))
                )
            """)

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS detalle_venta (
                    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER NOT NULL,
                    id_producto INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL
                        CHECK(cantidad BETWEEN 1 AND 100000),
                    precio_centavos INTEGER NOT NULL
                        CHECK(precio_centavos BETWEEN 1 AND 1000000),
                    subtotal_centavos INTEGER NOT NULL
                        CHECK(subtotal_centavos =
                              cantidad * precio_centavos),

                    FOREIGN KEY (id_venta)
                        REFERENCES ventas(id_venta),

                    FOREIGN KEY (id_producto)
                        REFERENCES productos(id_producto)
                )
            """)


if __name__ == "__main__":
    try:
        inicializar_base_datos()

        print("====================================")
        print(" TIENDAS MI CHOLO - BASE DE DATOS")
        print("====================================")
        print("Base de datos creada correctamente.")
        print("Tabla productos: OK")
        print("Tabla ventas: OK")
        print("Tabla detalle_venta: OK")
        print(f"Ubicacion: {RUTA_DB}")

    except (sqlite3.Error, OSError) as error:
        print(f"Error en la base de datos: {error}")
