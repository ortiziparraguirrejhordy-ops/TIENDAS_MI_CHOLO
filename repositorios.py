"""Capa de acceso a datos: consultas SQL del sistema."""


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


CAMPOS_PUBLICOS = "id_usuario, usuario, nombre_completo, rol, activo, fecha_creacion, ultimo_acceso"


def iniciar_transaccion(conexion):
    return conexion.execute('BEGIN IMMEDIATE')


def consultar_producto_activo(conexion, parametros):
    return conexion.execute('\n                    SELECT * FROM productos\n                    WHERE codigo = ?\n                    AND activo = 1\n                ', parametros)


def insertar_venta(conexion, parametros):
    return conexion.execute('\n                INSERT INTO ventas (\n                    fecha,\n                    total_centavos,\n                    metodo_pago\n                )\n                VALUES (?, ?, ?)\n            ', parametros)


def insertar_detalle_venta(conexion, parametros):
    return conexion.execute('\n                    INSERT INTO detalle_venta (\n                        id_venta,\n                        id_producto,\n                        cantidad,\n                        precio_centavos,\n                        subtotal_centavos\n                    )\n                    VALUES (?, ?, ?, ?, ?)\n                ', parametros)


def descontar_stock(conexion, parametros):
    return conexion.execute('\n                    UPDATE productos\n                    SET stock = stock - ?\n                    WHERE id_producto = ?\n                    AND stock >= ?\n                    AND activo = 1\n                ', parametros)


def consultar_ventas(conexion):
    return conexion.execute('\n            SELECT *\n            FROM ventas\n            ORDER BY id_venta DESC\n        ')


def consultar_venta(conexion, parametros):
    return conexion.execute('\n            SELECT *\n            FROM ventas\n            WHERE id_venta = ?\n        ', parametros)


def consultar_detalles_venta(conexion, parametros):
    return conexion.execute('\n            SELECT\n                p.codigo,\n                p.nombre,\n                d.cantidad,\n                d.precio_centavos,\n                d.subtotal_centavos\n            FROM detalle_venta AS d\n            INNER JOIN productos AS p\n                ON d.id_producto = p.id_producto\n            WHERE d.id_venta = ?\n            ORDER BY d.id_detalle\n        ', parametros)


def consultar_ingresos(conexion, parametros):
    return conexion.execute('\n            SELECT\n                COUNT(*) AS total_ventas,\n\n                COALESCE(\n                    SUM(total_centavos), 0\n                ) AS ingresos_totales,\n\n                COALESCE(\n                    SUM(\n                        CASE\n                            WHEN substr(fecha, 1, 10) = ?\n                            THEN total_centavos\n                            ELSE 0\n                        END\n                    ), 0\n                ) AS ingresos_hoy,\n\n                COALESCE(\n                    SUM(\n                        CASE\n                            WHEN substr(fecha, 1, 7) = ?\n                            THEN total_centavos\n                            ELSE 0\n                        END\n                    ), 0\n                ) AS ingresos_mes\n\n            FROM ventas\n        ', parametros)


def consultar_ingresos_pago(conexion):
    return conexion.execute('\n            SELECT\n                metodo_pago,\n                COUNT(*) AS cantidad_ventas,\n                SUM(total_centavos) AS ingresos\n\n            FROM ventas\n\n            GROUP BY metodo_pago\n\n            ORDER BY ingresos DESC\n        ')


def consultar_mas_vendidos(conexion, parametros):
    return conexion.execute('\n            SELECT\n                p.codigo,\n                p.nombre,\n\n                SUM(d.cantidad) AS unidades_vendidas,\n\n                SUM(d.subtotal_centavos) AS ingresos\n\n            FROM detalle_venta AS d\n\n            INNER JOIN productos AS p\n                ON d.id_producto = p.id_producto\n\n            GROUP BY p.id_producto, p.codigo, p.nombre\n\n            ORDER BY unidades_vendidas DESC,\n                     p.id_producto ASC\n\n            LIMIT ?\n        ', parametros)


def insertar_usuario(conexion, parametros):
    return conexion.execute('INSERT INTO usuarios\n            (usuario, nombre_completo, password_hash, salt, iteraciones, rol, fecha_creacion)\n            VALUES (?, ?, ?, ?, ?, ?, ?)', parametros)


def contar_usuarios(conexion):
    return conexion.execute('SELECT COUNT(*) FROM usuarios')


def consultar_credenciales(conexion, parametros):
    return conexion.execute('SELECT * FROM usuarios WHERE usuario = ?', parametros)


def actualizar_acceso(conexion, parametros):
    return conexion.execute('UPDATE usuarios SET ultimo_acceso = ? WHERE id_usuario = ? AND activo = 1 AND password_hash = ?', parametros)


def consultar_usuario_publico(conexion, parametros):
    return conexion.execute(f'SELECT {CAMPOS_PUBLICOS} FROM usuarios WHERE id_usuario = ?', parametros)


def consultar_usuario_activo(conexion, parametros):
    return conexion.execute(f'SELECT {CAMPOS_PUBLICOS} FROM usuarios WHERE id_usuario = ? AND activo = 1', parametros)


def consultar_usuarios_publicos(conexion):
    return conexion.execute(f'SELECT {CAMPOS_PUBLICOS} FROM usuarios ORDER BY usuario')


def actualizar_estado_usuario(conexion, parametros):
    return conexion.execute('UPDATE usuarios SET activo = ? WHERE id_usuario = ?', parametros)


def consultar_usuario_id(conexion, parametros):
    return conexion.execute('SELECT * FROM usuarios WHERE id_usuario = ?', parametros)


def actualizar_password(conexion, parametros):
    return conexion.execute('UPDATE usuarios SET password_hash = ?, salt = ?, iteraciones = ? WHERE id_usuario = ?', parametros)


def consultar_nombre_usuario(conexion, parametros):
    return conexion.execute('SELECT usuario FROM usuarios WHERE id_usuario = ?', parametros)


def insertar_auditoria(conexion, parametros):
    return conexion.execute('INSERT INTO auditoria\n        (id_usuario, usuario, accion, modulo, descripcion, datos_anteriores,\n         datos_nuevos, fecha, resultado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', parametros)


def consultar_auditoria(conexion, parametros):
    return conexion.execute('SELECT * FROM auditoria ORDER BY id_auditoria DESC LIMIT ?', parametros)


def consultar_detalles_exportacion(conexion):
    return conexion.execute('\n            SELECT\n                v.id_venta,\n                v.fecha,\n                p.codigo,\n                p.nombre,\n                d.cantidad,\n                d.precio_centavos,\n                d.subtotal_centavos\n            FROM detalle_venta AS d\n            INNER JOIN ventas AS v\n                ON d.id_venta = v.id_venta\n            INNER JOIN productos AS p\n                ON d.id_producto = p.id_producto\n            ORDER BY v.id_venta DESC, d.id_detalle\n        ')


def consultar_integridad(conexion):
    return conexion.execute('PRAGMA integrity_check')


def consultar_claves_foraneas(conexion):
    return conexion.execute('PRAGMA foreign_key_check')


def consultar_tablas(conexion):
    return conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")
