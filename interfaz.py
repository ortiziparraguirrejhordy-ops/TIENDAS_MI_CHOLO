
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from base_datos import inicializar_base_datos
from inventario import (
    obtener_resumen_inventario,
    obtener_ingresos
)
from productos import listar_productos
from ventas import listar_ventas
from validaciones import formatear_dinero


# Colores principales del sistema
FONDO = "#F1F5F9"
LATERAL = "#14283F"
AZUL = "#2563EB"
BLANCO = "#FFFFFF"
TEXTO = "#14283F"
GRIS = "#64748B"
VERDE = "#15803D"


class Aplicacion(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("TIENDAS MI CHOLO | Sistema de ventas")
        self.geometry("1200x750")
        self.minsize(900, 600)
        self.configure(bg=FONDO)

        self.configurar_estilos()
        self.crear_estructura()
        self.mostrar_inicio()

        self.protocol(
            "WM_DELETE_WINDOW",
            self.salir
        )

    def configurar_estilos(self):

        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        estilo.configure(
            "Treeview",
            background=BLANCO,
            foreground=TEXTO,
            rowheight=32,
            font=("Segoe UI", 10),
            fieldbackground=BLANCO
        )

        estilo.configure(
            "Treeview.Heading",
            background=LATERAL,
            foreground=BLANCO,
            font=("Segoe UI", 10, "bold")
        )

        estilo.map(
            "Treeview",
            background=[("selected", AZUL)],
            foreground=[("selected", BLANCO)]
        )

    def crear_estructura(self):

        self.lateral = tk.Frame(
            self,
            bg=LATERAL,
            width=220
        )

        self.lateral.pack(
            side="left",
            fill="y"
        )

        self.lateral.pack_propagate(False)

        tk.Label(
            self.lateral,
            text="MI CHOLO",
            font=("Segoe UI", 23, "bold"),
            bg=LATERAL,
            fg=BLANCO
        ).pack(pady=(30, 5))

        tk.Label(
            self.lateral,
            text="SISTEMA DE VENTAS",
            font=("Segoe UI", 9),
            bg=LATERAL,
            fg="#94A3B8"
        ).pack(pady=(0, 30))

        opciones = [
            ("Inicio", self.mostrar_inicio),
            ("Productos", self.mostrar_productos),
            ("Nueva venta", self.mostrar_pendiente),
            ("Historial de ventas", self.mostrar_historial),
            ("Inventario", self.mostrar_inventario),
            ("Reportes", self.mostrar_pendiente),
            ("Seguridad", self.mostrar_pendiente)
        ]

        for nombre, funcion in opciones:

            tk.Button(
                self.lateral,
                text=nombre,
                command=funcion,
                bg=LATERAL,
                fg=BLANCO,
                activebackground=AZUL,
                activeforeground=BLANCO,
                font=("Segoe UI", 11),
                anchor="w",
                padx=22,
                pady=13,
                relief="flat",
                cursor="hand2"
            ).pack(fill="x", padx=8)

        tk.Button(
            self.lateral,
            text="Salir del sistema",
            command=self.salir,
            bg="#991B1B",
            fg=BLANCO,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            pady=12
        ).pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=20
        )

        self.principal = tk.Frame(
            self,
            bg=FONDO
        )

        self.principal.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.estado = tk.Label(
            self.principal,
            text="SQLite conectado | Modo local | Version 1.0",
            bg=BLANCO,
            fg=GRIS,
            anchor="w",
            padx=15,
            pady=8,
            font=("Segoe UI", 9)
        )

        self.estado.pack(
            side="bottom",
            fill="x"
        )

        self.contenido = tk.Frame(
            self.principal,
            bg=FONDO
        )

        self.contenido.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

    def limpiar_contenido(self):

        for elemento in self.contenido.winfo_children():
            elemento.destroy()

    def encabezado(self, titulo, descripcion):

        tk.Label(
            self.contenido,
            text=titulo,
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 25, "bold")
        ).pack(anchor="w")

        tk.Label(
            self.contenido,
            text=descripcion,
            bg=FONDO,
            fg=GRIS,
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(3, 20))

    def tarjeta(self, padre, titulo, valor, color):

        tarjeta = tk.Frame(
            padre,
            bg=BLANCO,
            padx=18,
            pady=18
        )

        tarjeta.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5
        )

        tk.Label(
            tarjeta,
            text=titulo,
            bg=BLANCO,
            fg=GRIS,
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        tk.Label(
            tarjeta,
            text=valor,
            bg=BLANCO,
            fg=color,
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", pady=(8, 0))

    def crear_tabla(self, columnas, titulos, anchos):

        marco = tk.Frame(
            self.contenido,
            bg=BLANCO
        )

        marco.pack(
            fill="both",
            expand=True,
            pady=10
        )

        tabla = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings"
        )

        for columna, titulo, ancho in zip(
            columnas, titulos, anchos
        ):

            tabla.heading(
                columna,
                text=titulo
            )

            tabla.column(
                columna,
                width=ancho,
                minwidth=60,
                anchor="center"
            )

        barra = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=tabla.yview
        )

        tabla.configure(
            yscrollcommand=barra.set
        )

        barra.pack(
            side="right",
            fill="y"
        )

        tabla.pack(
            fill="both",
            expand=True
        )

        return tabla

    def mostrar_inicio(self):

        self.limpiar_contenido()

        self.encabezado(
            "Panel general",
            "Resumen de las operaciones de Tiendas Mi Cholo"
        )

        resumen = obtener_resumen_inventario()
        ingresos = obtener_ingresos()

        fila = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        fila.pack(fill="x", pady=5)

        self.tarjeta(
            fila,
            "Ingresos de hoy",
            formatear_dinero(ingresos["ingresos_hoy"]),
            VERDE
        )

        self.tarjeta(
            fila,
            "Ventas realizadas",
            str(ingresos["total_ventas"]),
            AZUL
        )

        fila2 = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        fila2.pack(fill="x", pady=10)

        self.tarjeta(
            fila2,
            "Productos activos",
            str(resumen["total_productos"]),
            AZUL
        )

        self.tarjeta(
            fila2,
            "Unidades disponibles",
            str(resumen["total_unidades"]),
            AZUL
        )

        tk.Label(
            self.contenido,
            text="Ultimas ventas",
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(20, 5))

        tabla = self.crear_tabla(
            ("id", "fecha", "pago", "total"),
            ("ID", "Fecha y hora", "Pago", "Total"),
            (60, 210, 120, 120)
        )

        for venta in listar_ventas()[:10]:

            tabla.insert(
                "",
                "end",
                values=(
                    venta["id_venta"],
                    venta["fecha"],
                    venta["metodo_pago"],
                    formatear_dinero(
                        venta["total_centavos"]
                    )
                )
            )

    def mostrar_productos(self):

        self.limpiar_contenido()

        self.encabezado(
            "Gestion de productos",
            "Consulta de productos registrados"
        )

        tabla = self.crear_tabla(
            ("codigo", "nombre", "categoria", "precio", "stock"),
            ("Codigo", "Producto", "Categoria", "Precio", "Stock"),
            (100, 200, 140, 100, 70)
        )

        for producto in listar_productos():

            tabla.insert(
                "",
                "end",
                values=(
                    producto["codigo"],
                    producto["nombre"],
                    producto["categoria"],
                    formatear_dinero(
                        producto["precio_centavos"]
                    ),
                    producto["stock"]
                )
            )

    def mostrar_historial(self):

        self.limpiar_contenido()

        self.encabezado(
            "Historial de ventas",
            "Consulta de todas las ventas registradas"
        )

        tabla = self.crear_tabla(
            ("id", "fecha", "pago", "total"),
            ("ID", "Fecha y hora", "Metodo de pago", "Total"),
            (80, 230, 150, 130)
        )

        for venta in listar_ventas():

            tabla.insert(
                "",
                "end",
                values=(
                    venta["id_venta"],
                    venta["fecha"],
                    venta["metodo_pago"],
                    formatear_dinero(
                        venta["total_centavos"]
                    )
                )
            )

    def mostrar_inventario(self):

        self.limpiar_contenido()

        self.encabezado(
            "Inventario",
            "Control de existencias y alertas de stock"
        )

        tabla = self.crear_tabla(
            ("codigo", "nombre", "stock", "estado"),
            ("Codigo", "Producto", "Stock", "Estado"),
            (100, 240, 100, 140)
        )

        tabla.tag_configure(
            "agotado",
            foreground="#DC2626"
        )

        tabla.tag_configure(
            "bajo",
            foreground="#D97706"
        )

        tabla.tag_configure(
            "disponible",
            foreground=VERDE
        )

        for producto in listar_productos():

            stock = producto["stock"]

            if stock == 0:
                estado = "Agotado"
                etiqueta = "agotado"

            elif stock <= 10:
                estado = "Stock bajo"
                etiqueta = "bajo"

            else:
                estado = "Disponible"
                etiqueta = "disponible"

            tabla.insert(
                "",
                "end",
                values=(
                    producto["codigo"],
                    producto["nombre"],
                    stock,
                    estado
                ),
                tags=(etiqueta,)
            )

    def mostrar_pendiente(self):

        messagebox.showinfo(
            "Modulo en desarrollo",
            "Esta funcion se integrara en la siguiente etapa."
        )

    def salir(self):

        confirmar = messagebox.askyesno(
            "Salir",
            "Desea cerrar el sistema?"
        )

        if confirmar:
            self.destroy()


def iniciar_interfaz():

    inicializar_base_datos()

    aplicacion = Aplicacion()
    aplicacion.mainloop()


if __name__ == "__main__":

    try:

        iniciar_interfaz()

    except (sqlite3.Error, OSError, tk.TclError) as error:

        print(f"Error al iniciar el sistema: {error}")
