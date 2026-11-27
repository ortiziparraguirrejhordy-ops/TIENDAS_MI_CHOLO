"""Pruebas automatizadas aisladas de la base de datos comercial."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from contextlib import ExitStack
import base_datos as bd
import productos as p
import ventas as v
import usuarios as u
import auditoria as a
import algoritmos as alg
import validaciones as val
import seguridad as seg


class PruebasSistema(unittest.TestCase):
    def setUp(self):
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        ruta = Path(temporal.name)
        pila = ExitStack()
        self.addCleanup(pila.close)
        for nombre, valor in {'RUTA_DB': ruta / 'prueba.db',
                              'CARPETA_DATOS': ruta / 'datos',
                              'CARPETA_BACKUPS': ruta / 'backups',
                              'CARPETA_REPORTES': ruta / 'reportes'}.items():
            pila.enter_context(patch.object(bd, nombre, valor))
        bd.inicializar_base_datos()
        self.admin = u.crear_primer_administrador('admin_test', 'Admin Prueba', 'ClavePrueba123!')
        self.vendedor = u.crear_usuario(self.admin, 'venta_test', 'Vendedor Prueba', 'ClavePrueba456!', 'Vendedor')

    def producto(self):
        p.crear_producto('P001', 'Arroz', 'Abarrotes', '4.50', '10', self.admin)

    def test_01_entradas_excesivas(self):
        for funcion in (val.validar_codigo, val.validar_nombre, val.validar_precio, val.validar_stock):
            with self.subTest(funcion=funcion.__name__), self.assertRaises(ValueError):
                funcion('9' * 10000)

    def test_02_precio_negativo(self):
        with self.assertRaises(ValueError):
            val.validar_precio('-10')

    def test_03_codigo_duplicado(self):
        self.producto()
        with self.assertRaises(ValueError):
            self.producto()
        self.assertEqual(len(p.listar_productos()), 1)

    def test_04_stock_insuficiente(self):
        self.producto()
        with self.assertRaises(ValueError):
            v.agregar_al_carrito({}, 'P001', '11')
        self.assertEqual(p.obtener_producto('P001')['stock'], 10)

    def test_05_venta_y_auditoria(self):
        self.producto()
        carrito = {}
        v.agregar_al_carrito(carrito, 'P001', '2')
        v.registrar_venta(carrito, 'Efectivo', self.vendedor)
        self.assertEqual(p.obtener_producto('P001')['stock'], 8)
        self.assertEqual(v.listar_ventas()[0]['total_centavos'], 900)
        self.assertTrue(any(x['accion'] == 'VENTA' for x in a.listar_auditoria(self.admin)))

    def test_06_ordenamiento(self):
        datos = alg.generar_productos_prueba(100)
        esperado = sorted(datos, key=lambda x: x['precio_centavos'])
        for ordenar in (alg.ordenamiento_burbuja, alg.ordenamiento_merge_sort):
            self.assertEqual(ordenar(datos, 'precio_centavos'), esperado)

    def test_07_autenticacion(self):
        self.assertEqual(u.autenticar('ADMIN_TEST', 'ClavePrueba123!')['rol'], 'Administrador')
        with self.assertRaises(ValueError):
            u.autenticar('admin_test', 'Incorrecta123!')

    def test_08_permisos(self):
        with self.assertRaises(ValueError):
            p.crear_producto('P002', 'Leche', 'Lacteos', '4', '10', self.vendedor)
        self.assertEqual(p.listar_productos(), [])

    def test_09_integridad(self):
        self.assertTrue(seg.verificar_integridad())

    def test_10_crud_auditoria(self):
        self.producto()
        p.modificar_producto('P001', 'P001', 'Arroz', 'Abarrotes', '5', '10', self.admin)
        p.eliminar_producto('P001', self.admin)
        self.assertEqual(p.listar_productos(), [])
        p.restaurar_producto('P001', self.admin)
        self.assertEqual(p.obtener_producto('P001')['precio_centavos'], 500)
        acciones = {x['accion'] for x in a.listar_auditoria(self.admin)}
        self.assertTrue({'INSERTAR', 'MODIFICAR', 'ELIMINAR', 'RESTAURAR'} <= acciones)


if __name__ == '__main__':
    unittest.main(verbosity=2)
