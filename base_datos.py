
import sys
import sqlite3
from pathlib import Path
from contextlib import closing


# ==========================================
# UBICACION DE LAS CARPETAS
# ==========================================

if getattr(sys, "frozen", False):
    RUTA_BASE = Path(sys.executable).resolve().parent
else:
    RUTA_BASE = Path(__file__).resolve().parent

CARPETA_DATOS = RUTA_BASE / "datos"
CARPETA_BACKUPS = RUTA_BASE / "backups"
CARPETA_REPORTES = RUTA_BASE / "reportes"

RUTA_DB = CARPETA_DATOS / "tienda_mi_cholo.db"


# ==========================================
# CREACION DE CARPETAS
# ==========================================

def crear_carpetas():
    """Crea las carpetas necesarias del sistema."""

    for carpeta in (
        CARPETA_DATOS,
        CARPETA_BACKUPS,
        CARPETA_REPORTES
    ):
        carpeta.mkdir(
            parents=True,
            exist_ok=True
        )


# ==========================================
# CONEXION A SQLITE
# ==========================================

def conectar():
    """Establece una conexion con SQLite."""

    crear_carpetas()

    conexion = sqlite3.connect(
        RUTA_DB,
        timeout=10
    )

    conexion.row_factory = sqlite3.Row

    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA synchronous = FULL")

    return conexion


# ==========================================
# INICIALIZACION DE LA BASE DE DATOS
# ==========================================

def inicializar_base_datos():
    """Crea las tablas necesarias del sistema."""

    with closing(conectar()) as conexion:

        with conexion:

            # TABLA DE PRODUCTOS

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

            # TABLA DE VENTAS

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,

                    fecha TEXT NOT NULL,

                    total_centavos INTEGER NOT NULL
                        CHECK(total_centavos > 0),

                    metodo_pago TEXT NOT NULL
                        CHECK(metodo_pago IN (
                            'Efectivo',
                            'Yape',
                            'Plin',
                            'Tarjeta'
                        ))
                )
            """)

            # TABLA DE DETALLE DE VENTAS

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

            # NUEVA TABLA DE USUARIOS

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,

                    usuario TEXT NOT NULL COLLATE NOCASE UNIQUE
                        CHECK(length(usuario) BETWEEN 4 AND 30),

                    nombre_completo TEXT NOT NULL
                        CHECK(length(nombre_completo) BETWEEN 2 AND 100),

                    password_hash TEXT NOT NULL
                        CHECK(length(password_hash) = 64),

                    salt TEXT NOT NULL
                        CHECK(length(salt) = 64),

                    iteraciones INTEGER NOT NULL DEFAULT 600000
                        CHECK(iteraciones >= 600000),

                    rol TEXT NOT NULL
                        CHECK(rol IN (
                            'Administrador',
                            'Vendedor'
                        )),

                    activo INTEGER NOT NULL DEFAULT 1
                        CHECK(activo IN (0, 1)),

                    fecha_creacion TEXT NOT NULL,

                    ultimo_acceso TEXT
                )
            """)

            # NUEVA TABLA DE AUDITORIA

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS auditoria (
                    id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,

                    id_usuario INTEGER,

                    usuario TEXT NOT NULL
                        CHECK(length(usuario) BETWEEN 1 AND 30),

                    accion TEXT NOT NULL
                        CHECK(length(accion) BETWEEN 1 AND 50),

                    modulo TEXT NOT NULL
                        CHECK(length(modulo) BETWEEN 1 AND 50),

                    descripcion TEXT NOT NULL
                        CHECK(length(descripcion) BETWEEN 1 AND 1000),

                    datos_anteriores TEXT,

                    datos_nuevos TEXT,

                    fecha TEXT NOT NULL,

                    resultado TEXT NOT NULL DEFAULT 'EXITOSO'
                        CHECK(resultado IN (
                            'EXITOSO',
                            'FALLIDO'
                        )),

                    FOREIGN KEY (id_usuario)
                        REFERENCES usuarios(id_usuario)
                        ON DELETE RESTRICT
                )
            """)

            # ==========================================
            # INDICES PARA OPTIMIZAR LAS CONSULTAS
            # ==========================================

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_productos_nombre
                ON productos(nombre)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_productos_categoria
                ON productos(categoria)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_productos_activo
                ON productos(activo)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_ventas_fecha
                ON ventas(fecha)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_detalle_venta
                ON detalle_venta(id_venta)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_detalle_producto
                ON detalle_venta(id_producto)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_auditoria_fecha
                ON auditoria(fecha)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_auditoria_usuario
                ON auditoria(id_usuario)
            """)

            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_auditoria_accion
                ON auditoria(accion)
            """)


# ==========================================
# VERIFICACION DE TABLAS
# ==========================================

def obtener_tablas():
    """Devuelve las tablas existentes."""

    with closing(conectar()) as conexion:

        registros = conexion.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        return [
            registro["name"]
            for registro in registros
        ]


def verificar_tablas():
    """Comprueba las tablas requeridas."""

    tablas_requeridas = [
        "productos",
        "ventas",
        "detalle_venta",
        "usuarios",
        "auditoria"
    ]

    tablas_existentes = obtener_tablas()

    for tabla in tablas_requeridas:

        if tabla in tablas_existentes:

            print(f"Tabla {tabla}: OK")

        else:

            print(f"Tabla {tabla}: FALTANTE")

    return all(
        tabla in tablas_existentes
        for tabla in tablas_requeridas
    )


# ==========================================
# EJECUCION DIRECTA
# ==========================================

if __name__ == "__main__":

    try:

        inicializar_base_datos()

        print("=" * 45)
        print(" TIENDAS MI CHOLO - BASE DE DATOS")
        print("=" * 45)

        if verificar_tablas():

            print("\nBase de datos actualizada correctamente.")

        else:

            print("\nExisten tablas pendientes.")

        print(f"\nUbicacion: {RUTA_DB}")

    except (sqlite3.Error, OSError) as error:

        print(f"Error en la base de datos: {error}")
