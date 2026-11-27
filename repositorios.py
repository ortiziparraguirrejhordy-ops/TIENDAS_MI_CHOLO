"""Capa de acceso a datos: consultas de productos."""


def consultar_productos(conexion, incluir_inactivos=False):
    consulta = 'SELECT * FROM productos'
    if not incluir_inactivos:
        consulta += ' WHERE activo = 1'
    consulta += ' ORDER BY id_producto'
    return conexion.execute(consulta).fetchall()


def consultar_producto(conexion, codigo):
    return conexion.execute('SELECT * FROM productos WHERE codigo = ?', (codigo,)).fetchone()


def insertar_producto(conexion, codigo, nombre, categoria, precio, stock):
    return conexion.execute('''INSERT INTO productos
        (codigo, nombre, categoria, precio_centavos, stock)
        VALUES (?, ?, ?, ?, ?)''', (codigo, nombre, categoria, precio, stock))


def actualizar_producto(conexion, codigo_actual, codigo_nuevo, nombre, categoria, precio, stock):
    return conexion.execute('''UPDATE productos SET codigo = ?, nombre = ?,
        categoria = ?, precio_centavos = ?, stock = ?
        WHERE codigo = ? AND activo = 1''',
        (codigo_nuevo, nombre, categoria, precio, stock, codigo_actual))


def actualizar_estado_producto(conexion, codigo, activo):
    return conexion.execute('UPDATE productos SET activo = ? WHERE codigo = ? AND activo = ?',
                            (activo, codigo, 1 - activo))
