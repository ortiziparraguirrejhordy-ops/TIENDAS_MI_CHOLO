
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import subprocess

from datetime import date
from decimal import Decimal

from base_datos import inicializar_base_datos, CARPETA_REPORTES

from productos import (
    listar_productos,
    obtener_producto,
    crear_producto,
    modificar_producto,
    eliminar_producto,
    restaurar_producto
)

from algoritmos import (
    busqueda_secuencial,
    ordenamiento_adaptativo
)

from ventas import (
    agregar_al_carrito,
    quitar_del_carrito,
    calcular_total,
    registrar_venta,
    listar_ventas,
    obtener_detalle_venta
)

from inventario import (
    obtener_resumen_inventario,
    obtener_ingresos,
    obtener_ingresos_por_pago,
    obtener_productos_mas_vendidos,
    STOCK_MINIMO
)

from usuarios import (autenticar, verificar_permiso, necesita_administrador,
                      crear_primer_administrador, crear_usuario, listar_usuarios,
                      cambiar_estado, cambiar_password)
from auditoria import registrar_evento, listar_auditoria
from validaciones import formatear_dinero
from reportes import (
    exportar_productos, exportar_ventas, exportar_detalle_ventas,
    exportar_inventario, exportar_ingresos, exportar_todo
)


# ==========================================
# CONFIGURACION VISUAL
# ==========================================

FONDO = "#F1F5F9"
LATERAL = "#14283F"
AZUL = "#2563EB"
BLANCO = "#FFFFFF"
TEXTO = "#14283F"
GRIS = "#64748B"
VERDE = "#15803D"
ROJO = "#DC2626"
NARANJA = "#D97706"

ERRORES = (ValueError, sqlite3.Error, OSError)


# ==========================================
# CLASE PRINCIPAL
# ==========================================

class Aplicacion(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("TIENDAS MI CHOLO | Sistema de ventas")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(bg=FONDO)

        self.carrito = {}
        self.botones_menu = {}
        self.busqueda_pendiente = None

        self.configurar_estilos()
        self.sesion = None
        self.mostrar_login()

        self.protocol("WM_DELETE_WINDOW", self.salir)


    # ======================================
    # ESTILOS
    # ======================================

    def mostrar_login(self):
        self.geometry("1000x650")
        self.login = tk.Frame(self, bg=LATERAL)
        self.login.pack(fill="both", expand=True)
        panel = tk.Frame(self.login, bg=BLANCO, padx=48, pady=30)
        panel.place(relx=.5, rely=.5, anchor="center")
        inicial = necesita_administrador()
        tk.Label(panel, text="TIENDAS MI CHOLO", bg=BLANCO, fg=TEXTO,
                 font=("Segoe UI", 25, "bold")).pack(pady=(0, 10))
        tk.Label(panel, text="Crear primer administrador" if inicial else "Iniciar sesion",
                 bg=BLANCO, fg=GRIS, font=("Segoe UI", 13)).pack(pady=(0, 15))
        campos = {}
        nombres = ["Usuario", "Nombre completo", "Contrasena", "Repetir contrasena"] if inicial else ["Usuario", "Contrasena"]
        for nombre in nombres:
            tk.Label(panel, text=nombre, bg=BLANCO, fg=TEXTO).pack(anchor="w")
            entrada = ttk.Entry(panel, width=36, show="*" if "contrasena" in nombre.lower() else "")
            entrada.pack(fill="x", pady=(2, 9))
            campos[nombre] = entrada
        visible = tk.BooleanVar(value=False)
        def mostrar_password():
            for nombre, entrada in campos.items():
                if "contrasena" in nombre.lower():
                    entrada.configure(show="" if visible.get() else "*")
        ttk.Checkbutton(panel, text="Mostrar contrasena", variable=visible,
                        command=mostrar_password).pack(anchor="w")
        def ingresar(event=None):
            try:
                usuario = campos["Usuario"].get()
                password = campos["Contrasena"].get()
                if inicial:
                    if password != campos["Repetir contrasena"].get():
                        raise ValueError("Las contrasenas no coinciden.")
                    crear_primer_administrador(usuario, campos["Nombre completo"].get(), password)
                sesion = autenticar(usuario, password)
                registrar_evento(sesion["id_usuario"], "LOGIN", "Usuarios", "Inicio de sesion grafico")
                self.sesion = sesion
            except ERRORES as error:
                messagebox.showerror("Acceso", str(error), parent=self)
                return
            self.login.destroy()
            self.geometry("1200x750")
            self.crear_estructura()
            self.navegar("Inicio", self.mostrar_inicio)
        self.boton(panel, "Crear administrador" if inicial else "Ingresar", ingresar).pack(fill="x", pady=(15, 0))
        if not inicial:
            self.boton(panel, "Crear cuenta", lambda: self.formulario_cuenta(True), LATERAL).pack(fill="x", pady=(8, 0))
        for entrada in campos.values():
            entrada.bind("<Return>", ingresar)
        campos["Usuario"].focus_set()

    def dialogo_cuenta(self, titulo, campos, guardar, rol=False):
        ventana = tk.Toplevel(self)
        ventana.title(titulo)
        ventana.transient(self)
        ventana.configure(bg=BLANCO)
        panel = tk.Frame(ventana, bg=BLANCO, padx=24, pady=18)
        panel.pack(fill="both", expand=True)
        entradas = {}
        for nombre, secreto in campos:
            tk.Label(panel, text=nombre, bg=BLANCO, fg=TEXTO).pack(anchor="w")
            entrada = ttk.Entry(panel, width=38, show="*" if secreto else "")
            entrada.pack(fill="x", pady=(2, 7))
            entradas[nombre] = entrada
        if rol:
            tk.Label(panel, text="Rol", bg=BLANCO).pack(anchor="w")
            selector = ttk.Combobox(panel, values=("Vendedor", "Administrador"), state="readonly")
            selector.set("Vendedor")
            selector.pack(fill="x", pady=5)
            entradas["Rol"] = selector
        def aceptar():
            try:
                guardar({k: v.get() for k, v in entradas.items()})
            except ERRORES as error:
                messagebox.showerror("Usuarios", str(error), parent=ventana)
                return
            ventana.destroy()
        self.boton(panel, "Guardar", aceptar).pack(fill="x", pady=(10, 4))
        self.boton(panel, "Cancelar", ventana.destroy, GRIS).pack(fill="x")
        ventana.grab_set()
        next(iter(entradas.values())).focus_set()

    def auditar_cuenta(self, actor, accion, descripcion, nuevos=None):
        try:
            registrar_evento(actor, accion, "Usuarios", descripcion, nuevos=nuevos)
        except ERRORES as error:
            messagebox.showwarning("Auditoria", "Cambio guardado, pero fallo la auditoria: " + str(error), parent=self)

    def formulario_cuenta(self, desde_login=False):
        if not desde_login and not self.permiso(True):
            return
        campos = [("Usuario administrador", False), ("Contrasena administrador", True)] if desde_login else []
        campos += [("Usuario nuevo", False), ("Nombre completo", False), ("Contrasena nueva", True), ("Repetir contrasena", True)]
        def guardar(datos):
            if datos["Contrasena nueva"] != datos["Repetir contrasena"]:
                raise ValueError("Las contrasenas no coinciden.")
            actor = autenticar(datos["Usuario administrador"], datos["Contrasena administrador"]) if desde_login else self.sesion
            verificar_permiso(actor["id_usuario"], ("Administrador",))
            nuevo = crear_usuario(actor["id_usuario"], datos["Usuario nuevo"], datos["Nombre completo"], datos["Contrasena nueva"], datos["Rol"])
            self.auditar_cuenta(actor["id_usuario"], "INSERTAR", "Cuenta creada", {"id_usuario": nuevo, "rol": datos["Rol"]})
            messagebox.showinfo("Usuarios", "Cuenta creada correctamente.", parent=self)
            if not desde_login:
                self.mostrar_usuarios()
        self.dialogo_cuenta("Crear cuenta", campos, guardar, rol=True)

    def mostrar_usuarios(self):
        if not self.permiso(True):
            return
        self.limpiar_contenido()
        self.encabezado("Usuarios", "Administracion de cuentas y permisos")
        barra = tk.Frame(self.contenido, bg=FONDO)
        barra.pack(fill="x", pady=8)
        self.boton(barra, "Crear cuenta", self.formulario_cuenta).pack(side="left", padx=4)
        tabla = self.crear_tabla(("id", "usuario", "nombre", "rol", "estado"), ("ID", "Usuario", "Nombre", "Rol", "Estado"), (50, 120, 220, 120, 90))
        for i, fila in enumerate(listar_usuarios(self.sesion["id_usuario"])):
            self.insertar_fila(tabla, (fila["id_usuario"], fila["usuario"], fila["nombre_completo"], fila["rol"], "Activo" if fila["activo"] else "Inactivo"), i)
        def estado(activo):
            if not self.permiso(True):
                return
            valores = self.seleccionado(tabla)
            if not valores:
                return
            if not messagebox.askyesno("Usuarios", "Cambiar estado de la cuenta seleccionada?", parent=self):
                return
            try:
                objetivo = int(valores[0])
                cambiar_estado(self.sesion["id_usuario"], objetivo, activo)
                self.auditar_cuenta(self.sesion["id_usuario"], "MODIFICAR", "Estado de cuenta actualizado", {"id_usuario": objetivo, "activo": activo})
                self.mostrar_usuarios()
            except ERRORES as error:
                messagebox.showerror("Usuarios", str(error), parent=self)
        self.boton(barra, "Activar", lambda: estado(1), VERDE).pack(side="left", padx=4)
        self.boton(barra, "Desactivar", lambda: estado(0), ROJO).pack(side="left", padx=4)

    def formulario_password(self):
        if not self.permiso():
            return
        def guardar(datos):
            if datos["Contrasena nueva"] != datos["Repetir contrasena"]:
                raise ValueError("Las contrasenas no coinciden.")
            actor = self.sesion["id_usuario"]
            cambiar_password(actor, datos["Contrasena actual"], datos["Contrasena nueva"])
            self.auditar_cuenta(actor, "MODIFICAR", "Cambio de contrasena")
            messagebox.showinfo("Usuarios", "Contrasena actualizada.", parent=self)
        self.dialogo_cuenta("Cambiar contrasena", [("Contrasena actual", True), ("Contrasena nueva", True), ("Repetir contrasena", True)], guardar)

    def es_admin(self):
        return self.sesion is not None and self.sesion["rol"] == "Administrador"

    def permiso(self, admin=False):
        try:
            if self.sesion is None:
                raise ValueError("Inicie sesion.")
            roles = ("Administrador",) if admin else ("Administrador", "Vendedor")
            verificar_permiso(self.sesion["id_usuario"], roles)
            return True
        except ERRORES as error:
            messagebox.showerror("Acceso", str(error), parent=self)
            return False

    def cerrar_sesion(self):
        if not messagebox.askyesno("Cerrar sesion", "Cerrar sesion? El carrito pendiente se perdera.", parent=self):
            return
        try:
            registrar_evento(self.sesion["id_usuario"], "LOGOUT", "Usuarios", "Cierre de sesion grafico")
        except ERRORES as error:
            messagebox.showwarning("Auditoria", str(error), parent=self)
        self.cancelar_busqueda_pendiente()
        self.carrito.clear()
        self.botones_menu.clear()
        self.lateral.destroy()
        self.principal.destroy()
        self.sesion = None
        self.mostrar_login()

    def mostrar_auditoria(self):
        if not self.permiso(True):
            return
        self.limpiar_contenido()
        self.encabezado("Auditoria", "Ultimos 100 eventos registrados")
        tabla = self.crear_tabla(("fecha", "usuario", "accion", "modulo", "resultado", "descripcion"),
            ("Fecha", "Usuario", "Accion", "Modulo", "Resultado", "Descripcion"),
            (150, 90, 90, 90, 90, 240))
        for i, fila in enumerate(listar_auditoria(self.sesion["id_usuario"])):
            self.insertar_fila(tabla, tuple(fila[k] for k in ("fecha", "usuario", "accion", "modulo", "resultado", "descripcion")), i)

    def configurar_estilos(self):

        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        estilo.configure(
            "Treeview",
            background=BLANCO,
            foreground=TEXTO,
            fieldbackground=BLANCO,
            rowheight=32,
            font=("Segoe UI", 10)
        )

        estilo.configure(
            "Treeview.Heading",
            background=LATERAL,
            foreground=BLANCO,
            font=("Segoe UI", 10, "bold"),
            padding=8
        )

        estilo.map(
            "Treeview",
            background=[("selected", AZUL)],
            foreground=[("selected", BLANCO)]
        )

        estilo.configure(
            "TEntry",
            padding=6
        )

        estilo.configure(
            "TCombobox",
            padding=6
        )


    # ======================================
    # ESTRUCTURA PRINCIPAL
    # ======================================

    def crear_estructura(self):

        self.lateral = tk.Frame(
            self,
            bg=LATERAL,
            width=220
        )

        self.lateral.pack(side="left", fill="y")
        self.lateral.pack_propagate(False)

        tk.Label(
            self.lateral,
            text="MI CHOLO",
            font=("Segoe UI", 24, "bold"),
            bg=LATERAL,
            fg=BLANCO
        ).pack(pady=(28, 4))

        tk.Label(
            self.lateral,
            text="SISTEMA DE VENTAS",
            font=("Segoe UI", 9),
            bg=LATERAL,
            fg="#94A3B8"
        ).pack(pady=(0, 25))

        opciones = [
            ("Inicio", self.mostrar_inicio),
            ("Productos", self.mostrar_productos),
            ("Nueva venta", self.mostrar_nueva_venta),
            ("Historial de ventas", self.mostrar_historial),
            ("Inventario", self.mostrar_inventario),
            ("Reportes", self.mostrar_reportes),
            ("Seguridad", self.mostrar_seguridad)
        ]

        if self.es_admin():
            opciones.append(("Auditoria", self.mostrar_auditoria))
            opciones.append(("Usuarios", self.mostrar_usuarios))
        else:
            opciones = [(n, f) for n, f in opciones if n not in ("Reportes", "Seguridad")]

        opciones.append(("Mi contrasena", self.formulario_password))
        for nombre, funcion in opciones:

            boton = tk.Button(
                self.lateral,
                text=nombre,
                command=lambda n=nombre, f=funcion:
                    self.navegar(n, f),
                bg=LATERAL,
                fg=BLANCO,
                activebackground=AZUL,
                activeforeground=BLANCO,
                font=("Segoe UI", 11),
                anchor="w",
                padx=20,
                pady=7,
                relief="flat",
                cursor="hand2"
            )

            boton.pack(fill="x", padx=8, pady=2)

            self.botones_menu[nombre] = boton

        tk.Button(
            self.lateral,
            text="Cerrar sesion",
            command=self.cerrar_sesion,
            bg=ROJO,
            fg=BLANCO,
            activebackground="#991B1B",
            activeforeground=BLANCO,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            pady=10
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
            text=f"SQLite | {self.sesion['usuario']} | {self.sesion['rol']}",
            bg=BLANCO,
            fg=GRIS,
            anchor="w",
            padx=15,
            pady=8,
            font=("Segoe UI", 9)
        )

        self.estado.pack(side="bottom", fill="x")

        self.contenido = tk.Frame(
            self.principal,
            bg=FONDO
        )

        self.contenido.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=18
        )


    def navegar(self, nombre, funcion):
        if not self.permiso(nombre in ("Reportes", "Seguridad", "Auditoria", "Usuarios")):
            return

        for boton in self.botones_menu.values():
            boton.configure(bg=LATERAL)

        self.botones_menu[nombre].configure(bg=AZUL)

        try:
            funcion()

        except ERRORES as error:
            messagebox.showerror(
                "Error del sistema",
                str(error),
                parent=self
            )


    def limpiar_contenido(self):

        self.cancelar_busqueda_pendiente()

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
        ).pack(anchor="w", pady=(3, 15))


    def boton(self, padre, texto, funcion, color=AZUL):

        return tk.Button(
            padre,
            text=texto,
            command=funcion,
            bg=color,
            fg=BLANCO,
            activebackground=color,
            activeforeground=BLANCO,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=9
        )


    def tarjeta(self, padre, titulo, valor, color=AZUL):

        marco = tk.Frame(
            padre,
            bg=BLANCO,
            padx=16,
            pady=15
        )

        marco.pack(
            side="left",
            fill="both",
            expand=True,
            padx=4
        )

        tk.Label(
            marco,
            text=titulo,
            bg=BLANCO,
            fg=GRIS,
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        tk.Label(
            marco,
            text=valor,
            bg=BLANCO,
            fg=color,
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", pady=(6, 0))


    def crear_tabla(
        self,
        columnas,
        titulos,
        anchos,
        padre=None,
        altura=10
    ):

        if padre is None:
            padre = self.contenido

        marco = tk.Frame(padre, bg=BLANCO)

        marco.pack(
            fill="both",
            expand=True,
            pady=6
        )

        tabla = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings",
            selectmode="browse",
            height=altura
        )

        for columna, titulo, ancho in zip(
            columnas, titulos, anchos
        ):

            tabla.heading(columna, text=titulo)

            tabla.column(
                columna,
                width=ancho,
                minwidth=50,
                anchor="center"
            )

        vertical = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=tabla.yview
        )

        horizontal = ttk.Scrollbar(
            marco,
            orient="horizontal",
            command=tabla.xview
        )

        tabla.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set
        )

        vertical.pack(side="right", fill="y")
        horizontal.pack(side="bottom", fill="x")

        tabla.pack(fill="both", expand=True)

        tabla.tag_configure(
            "par",
            background="#F8FAFC"
        )

        tabla.tag_configure(
            "impar",
            background=BLANCO
        )

        tabla.tag_configure(
            "agotado",
            foreground=ROJO
        )

        tabla.tag_configure(
            "bajo",
            foreground=NARANJA
        )

        tabla.tag_configure(
            "inactivo",
            foreground=GRIS
        )

        return tabla


    def vaciar_tabla(self, tabla):

        for fila in tabla.get_children():
            tabla.delete(fila)


    def seleccionado(self, tabla):

        seleccion = tabla.selection()

        if not seleccion:

            messagebox.showwarning(
                "Aviso",
                "Seleccione un registro de la tabla.",
                parent=self
            )

            return None

        return tabla.item(
            seleccion[0],
            "values"
        )


    def insertar_fila(self, tabla, valores, indice):

        etiqueta = "par" if indice % 2 == 0 else "impar"

        tabla.insert(
            "",
            "end",
            values=valores,
            tags=(etiqueta,)
        )


    # ======================================
    # PANEL PRINCIPAL
    # ======================================

    def mostrar_inicio(self):

        self.limpiar_contenido()

        self.encabezado(
            "Panel general",
            "Resumen de operaciones comerciales"
        )

        resumen = obtener_resumen_inventario()
        ingresos = obtener_ingresos()

        fila1 = tk.Frame(self.contenido, bg=FONDO)
        fila1.pack(fill="x", pady=5)

        self.tarjeta(
            fila1,
            "Ingresos de hoy",
            formatear_dinero(ingresos["ingresos_hoy"]),
            VERDE
        )

        self.tarjeta(
            fila1,
            "Ingresos del mes",
            formatear_dinero(ingresos["ingresos_mes"]),
            VERDE
        )

        self.tarjeta(
            fila1,
            "Ventas realizadas",
            str(ingresos["total_ventas"])
        )

        fila2 = tk.Frame(self.contenido, bg=FONDO)
        fila2.pack(fill="x", pady=5)

        self.tarjeta(
            fila2,
            "Productos activos",
            str(resumen["total_productos"])
        )

        self.tarjeta(
            fila2,
            "Unidades disponibles",
            str(resumen["total_unidades"])
        )

        self.tarjeta(
            fila2,
            "Alertas de inventario",
            str(
                resumen["stock_bajo"]
                + resumen["agotados"]
            ),
            NARANJA
        )

        tk.Label(
            self.contenido,
            text="Ultimas ventas",
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(15, 4))

        tabla = self.crear_tabla(
            ("id", "fecha", "pago", "total"),
            ("Venta", "Fecha y hora", "Pago", "Total"),
            (110, 210, 130, 120)
        )

        for i, venta in enumerate(listar_ventas()[:10]):

            self.insertar_fila(
                tabla,
                (
                    f"V-{venta['id_venta']:06d}",
                    venta["fecha"],
                    venta["metodo_pago"],
                    formatear_dinero(
                        venta["total_centavos"]
                    )
                ),
                i
            )


    # ======================================
    # GESTION DE PRODUCTOS
    # ======================================

    def mostrar_productos(self):

        self.limpiar_contenido()

        self.encabezado(
            "Gestion de productos",
            "Registro y administracion del catalogo"
        )

        herramientas = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        herramientas.pack(fill="x", pady=5)

        opciones = [
            ("Nuevo producto", self.formulario_producto, VERDE),
            ("Modificar", self.editar_producto, AZUL),
            ("Eliminar", self.desactivar_producto, ROJO),
            ("Restaurar", self.reactivar_producto, NARANJA)
        ]

        for texto, funcion, color in (opciones if self.es_admin() else []):

            self.boton(
                herramientas,
                texto,
                funcion,
                color
            ).pack(side="left", padx=(0, 6))

        filtros = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        filtros.pack(fill="x", pady=10)

        tk.Label(
            filtros,
            text="Buscar:",
            bg=FONDO,
            fg=TEXTO
        ).pack(side="left")

        self.busqueda_producto = tk.StringVar()

        entrada = ttk.Entry(
            filtros,
            textvariable=self.busqueda_producto,
            width=22
        )

        entrada.pack(side="left", padx=6)

        self.orden_producto = tk.StringVar(
            value="Sin ordenar"
        )

        selector = ttk.Combobox(
            filtros,
            textvariable=self.orden_producto,
            state="readonly",
            width=19,
            values=[
                "Sin ordenar",
                "Nombre",
                "Codigo",
                "Categoria",
                "Precio ascendente",
                "Precio descendente",
                "Stock"
            ]
        )

        selector.pack(side="left", padx=5)

        self.ver_inactivos = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            filtros,
            text="Mostrar inactivos",
            variable=self.ver_inactivos,
            command=self.actualizar_tabla_productos
        ).pack(side="left", padx=5)

        self.contador_productos = tk.Label(
            self.contenido,
            bg=FONDO,
            fg=GRIS
        )

        self.contador_productos.pack(anchor="w")

        self.tabla_productos = self.crear_tabla(
            (
                "codigo",
                "nombre",
                "categoria",
                "precio",
                "stock",
                "estado"
            ),
            (
                "Codigo",
                "Producto",
                "Categoria",
                "Precio",
                "Stock",
                "Estado"
            ),
            (90, 180, 130, 90, 65, 90)
        )

        self.pagina_productos = 0
        self.productos_filtrados = []
        self.metricas_productos = "Sin ordenar"
        pie = tk.Frame(self.contenido, bg=FONDO)
        pie.pack(fill="x", pady=4)
        self.anterior_productos = self.boton(
            pie, "Anterior", lambda: self.cambiar_pagina_productos(-1))
        self.anterior_productos.pack(side="left")
        self.siguiente_productos = self.boton(
            pie, "Siguiente", lambda: self.cambiar_pagina_productos(1))
        self.siguiente_productos.pack(side="right")
        self.etiqueta_pagina = tk.Label(pie, bg=FONDO, fg=TEXTO)
        self.etiqueta_pagina.pack(side="left", expand=True)
        self.busqueda_producto.trace_add("write", self.programar_busqueda_productos)
        selector.bind("<<ComboboxSelected>>", lambda evento: self.actualizar_tabla_productos())
        self.tabla_productos.bind("<Double-1>", lambda evento: self.editar_producto())
        self.actualizar_tabla_productos()

    def cancelar_busqueda_pendiente(self):
        if self.busqueda_pendiente is not None:
            self.after_cancel(self.busqueda_pendiente)
            self.busqueda_pendiente = None

    def programar_busqueda_productos(self, *_):
        self.cancelar_busqueda_pendiente()
        self.busqueda_pendiente = self.after(300, self.actualizar_tabla_productos)

    def actualizar_tabla_productos(self):
        self.cancelar_busqueda_pendiente()
        self.pagina_productos = 0
        try:
            productos = listar_productos(self.ver_inactivos.get())
            termino = self.busqueda_producto.get().strip()
            if termino:
                productos = busqueda_secuencial(productos, termino)
            opciones = {
                "Nombre": ("nombre", False),
                "Codigo": ("codigo", False),
                "Categoria": ("categoria", False),
                "Precio ascendente": ("precio_centavos", False),
                "Precio descendente": ("precio_centavos", True),
                "Stock": ("stock", False)
            }
            orden = self.orden_producto.get()
            self.metricas_productos = "Sin ordenar"
            if orden in opciones:
                campo, descendente = opciones[orden]
                resultado = ordenamiento_adaptativo(productos, campo, descendente)
                productos = resultado["productos"]
                self.metricas_productos = (
                    f"{resultado['algoritmo']} | {resultado['tiempo']:.6f} s"
                )
            self.productos_filtrados = productos
            self.mostrar_pagina_productos()
        except ERRORES as error:
            self.productos_filtrados = []
            self.metricas_productos = "Sin ordenar"
            self.mostrar_pagina_productos()
            self.contador_productos.configure(text=f"Aviso: {error}")

    def cambiar_pagina_productos(self, paso):
        total = max(1, (len(self.productos_filtrados) + 49) // 50)
        self.pagina_productos = max(0, min(total - 1, self.pagina_productos + paso))
        self.mostrar_pagina_productos()

    def mostrar_pagina_productos(self):
        productos = self.productos_filtrados
        total = max(1, (len(productos) + 49) // 50)
        inicio = self.pagina_productos * 50
        self.vaciar_tabla(self.tabla_productos)
        for i, producto in enumerate(productos[inicio:inicio + 50]):
            estado = (
                "Activo"
                if producto["activo"]
                else "Inactivo"
            )

            etiqueta = "par" if i % 2 == 0 else "impar"

            if not producto["activo"]:
                etiqueta = "inactivo"

            elif producto["stock"] == 0:
                etiqueta = "agotado"

            elif producto["stock"] <= STOCK_MINIMO:
                etiqueta = "bajo"

            self.tabla_productos.insert(
                "",
                "end",
                values=(
                    producto["codigo"],
                    producto["nombre"],
                    producto["categoria"],
                    formatear_dinero(
                        producto["precio_centavos"]
                    ),
                    producto["stock"],
                    estado
                ),
                tags=(etiqueta,)
            )

        self.contador_productos.configure(
            text=f"Productos encontrados: {len(productos)} | {self.metricas_productos}")
        self.etiqueta_pagina.configure(text=f"Pagina {self.pagina_productos + 1} de {total}")
        self.anterior_productos.configure(state="normal" if self.pagina_productos > 0 else "disabled")
        self.siguiente_productos.configure(state="normal" if self.pagina_productos + 1 < total else "disabled")


    def formulario_producto(self, producto=None):
        if not self.permiso(True):
            return

        ventana = tk.Toplevel(self)

        ventana.title(
            "Modificar producto"
            if producto
            else "Registrar producto"
        )

        ventana.geometry("460x550")
        ventana.resizable(False, False)
        ventana.configure(bg=FONDO)
        ventana.transient(self)
        ventana.grab_set()

        tk.Label(
            ventana,
            text=(
                "Modificar producto"
                if producto
                else "Nuevo producto"
            ),
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 21, "bold")
        ).pack(pady=15)

        formulario = tk.Frame(
            ventana,
            bg=FONDO
        )

        formulario.pack(
            fill="both",
            expand=True,
            padx=25
        )

        campos = [
            ("Codigo", "codigo"),
            ("Nombre", "nombre"),
            ("Categoria", "categoria"),
            ("Precio unitario (S/)", "precio"),
            ("Stock disponible", "stock")
        ]

        variables = {}

        for fila, (titulo, clave) in enumerate(campos):

            tk.Label(
                formulario,
                text=titulo,
                bg=FONDO,
                fg=TEXTO,
                font=("Segoe UI", 10)
            ).grid(
                row=fila * 2,
                column=0,
                sticky="w",
                pady=(5, 2)
            )

            variable = tk.StringVar()
            variables[clave] = variable

            if clave == "categoria":

                entrada = ttk.Combobox(
                    formulario,
                    textvariable=variable,
                    values=[
                        "Abarrotes",
                        "Bebidas",
                        "Lacteos",
                        "Limpieza",
                        "Higiene personal",
                        "Golosinas",
                        "Frutas y verduras",
                        "Otros"
                    ]
                )

            else:

                entrada = ttk.Entry(
                    formulario,
                    textvariable=variable,
                    font=("Segoe UI", 11)
                )

            entrada.grid(
                row=fila * 2 + 1,
                column=0,
                sticky="ew",
                pady=(0, 3)
            )

        formulario.columnconfigure(0, weight=1)

        if producto:

            for clave in (
                "codigo", "nombre", "categoria", "stock"
            ):

                variables[clave].set(
                    str(producto[clave])
                )

            variables["precio"].set(
                f"{Decimal(producto['precio_centavos']) / 100:.2f}"
            )

        else:

            variables["stock"].set("0")
            variables["categoria"].set("Abarrotes")

        def guardar():

            try:

                datos = {
                    clave: variable.get()
                    for clave, variable in variables.items()
                }

                if producto:

                    modificar_producto(
                        producto["codigo"],
                        datos["codigo"],
                        datos["nombre"],
                        datos["categoria"],
                        datos["precio"],
                        datos["stock"]
                    )

                else:

                    crear_producto(
                        datos["codigo"],
                        datos["nombre"],
                        datos["categoria"],
                        datos["precio"],
                        datos["stock"]
                    )

                messagebox.showinfo(
                    "Operacion exitosa",
                    "Producto guardado correctamente.",
                    parent=ventana
                )

                ventana.destroy()

                self.actualizar_tabla_productos()

            except ERRORES as error:

                messagebox.showerror(
                    "Datos incorrectos",
                    str(error),
                    parent=ventana
                )

        self.boton(
            ventana,
            "Guardar producto",
            guardar,
            VERDE
        ).pack(fill="x", padx=25, pady=5)

        self.boton(
            ventana,
            "Cancelar",
            ventana.destroy,
            GRIS
        ).pack(fill="x", padx=25, pady=(0, 15))


    def editar_producto(self):
        if not self.permiso(True):
            return

        valores = self.seleccionado(
            self.tabla_productos
        )

        if valores is None:
            return

        try:

            producto = obtener_producto(valores[0])

            if not producto["activo"]:

                raise ValueError(
                    "Primero debe restaurar el producto."
                )

            self.formulario_producto(producto)

        except ERRORES as error:

            messagebox.showerror("Error", str(error))


    def desactivar_producto(self):
        if not self.permiso(True):
            return

        valores = self.seleccionado(
            self.tabla_productos
        )

        if valores is None:
            return

        codigo = valores[0]

        if not messagebox.askyesno(
            "Confirmar eliminacion",
            f"Desea desactivar el producto {codigo}?"
        ):
            return

        try:

            eliminar_producto(codigo)

            self.actualizar_tabla_productos()

            messagebox.showinfo(
                "Operacion exitosa",
                "Producto desactivado correctamente."
            )

        except ERRORES as error:

            messagebox.showerror("Error", str(error))


    def reactivar_producto(self):
        if not self.permiso(True):
            return

        valores = self.seleccionado(
            self.tabla_productos
        )

        if valores is None:
            return

        try:

            restaurar_producto(valores[0])

            self.actualizar_tabla_productos()

            messagebox.showinfo(
                "Operacion exitosa",
                "Producto restaurado correctamente."
            )

        except ERRORES as error:

            messagebox.showerror("Error", str(error))


    # ======================================
    # NUEVA VENTA
    # ======================================

    def mostrar_nueva_venta(self):

        self.limpiar_contenido()

        self.encabezado(
            "Nueva venta",
            "Seleccione productos y registre una compra"
        )

        filtros = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        filtros.pack(fill="x", pady=4)

        tk.Label(
            filtros,
            text="Buscar producto:",
            bg=FONDO,
            fg=TEXTO
        ).pack(side="left")

        self.busqueda_venta = tk.StringVar()

        entrada = ttk.Entry(
            filtros,
            textvariable=self.busqueda_venta,
            width=25
        )

        entrada.pack(side="left", padx=6)

        self.tabla_catalogo = self.crear_tabla(
            ("codigo", "nombre", "precio", "stock"),
            ("Codigo", "Producto", "Precio", "Stock"),
            (100, 230, 100, 80),
            altura=4
        )

        entrada.bind(
            "<KeyRelease>",
            lambda evento: self.actualizar_catalogo()
        )

        controles = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        controles.pack(fill="x", pady=5)

        tk.Label(
            controles,
            text="Cantidad:",
            bg=FONDO,
            fg=TEXTO
        ).pack(side="left")

        self.cantidad_venta = tk.StringVar(value="1")

        ttk.Entry(
            controles,
            textvariable=self.cantidad_venta,
            width=8
        ).pack(side="left", padx=6)

        self.boton(
            controles,
            "Agregar al carrito",
            self.agregar_producto_venta,
            VERDE
        ).pack(side="left", padx=5)

        self.boton(
            controles,
            "Quitar producto",
            self.quitar_producto_venta,
            ROJO
        ).pack(side="left", padx=5)

        self.boton(
            controles,
            "Vaciar carrito",
            self.vaciar_carrito,
            GRIS
        ).pack(side="left", padx=5)

        tk.Label(
            self.contenido,
            text="Carrito de compras",
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(6, 2))

        self.tabla_carrito = self.crear_tabla(
            ("codigo", "nombre", "cantidad", "precio", "subtotal"),
            ("Codigo", "Producto", "Cantidad", "Precio", "Subtotal"),
            (90, 190, 75, 100, 110),
            altura=4
        )

        pie = tk.Frame(
            self.contenido,
            bg=BLANCO,
            padx=12,
            pady=12
        )

        pie.pack(fill="x", pady=5)

        tk.Label(
            pie,
            text="Metodo de pago:",
            bg=BLANCO,
            fg=TEXTO
        ).pack(side="left")

        self.metodo_pago = tk.StringVar(
            value="Efectivo"
        )

        ttk.Combobox(
            pie,
            textvariable=self.metodo_pago,
            values=[
                "Efectivo",
                "Yape",
                "Plin",
                "Tarjeta"
            ],
            state="readonly",
            width=10
        ).pack(side="left", padx=6)

        self.boton(
            pie,
            "Confirmar venta",
            self.confirmar_venta,
            VERDE
        ).pack(side="right", padx=5)

        self.total_venta = tk.Label(
            pie,
            text="S/ 0.00",
            bg=BLANCO,
            fg=VERDE,
            font=("Segoe UI", 20, "bold")
        )

        self.total_venta.pack(side="right", padx=10)

        self.tabla_catalogo.bind(
            "<Double-1>",
            lambda evento: self.agregar_producto_venta()
        )

        self.actualizar_catalogo()
        self.actualizar_carrito()


    def actualizar_catalogo(self):

        try:

            productos = listar_productos()

            termino = self.busqueda_venta.get().strip()

            if termino:

                productos = busqueda_secuencial(
                    productos,
                    termino
                )

            self.vaciar_tabla(self.tabla_catalogo)

            for i, producto in enumerate(productos):

                self.insertar_fila(
                    self.tabla_catalogo,
                    (
                        producto["codigo"],
                        producto["nombre"],
                        formatear_dinero(
                            producto["precio_centavos"]
                        ),
                        producto["stock"]
                    ),
                    i
                )

        except ERRORES as error:

            self.vaciar_tabla(self.tabla_catalogo)

            self.estado.configure(
                text=f"Aviso: {error}"
            )


    def agregar_producto_venta(self):

        valores = self.seleccionado(
            self.tabla_catalogo
        )

        if valores is None:
            return

        try:

            agregar_al_carrito(
                self.carrito,
                valores[0],
                self.cantidad_venta.get()
            )

            self.actualizar_carrito()

            self.cantidad_venta.set("1")

        except ERRORES as error:

            messagebox.showerror(
                "No se pudo agregar",
                str(error)
            )


    def quitar_producto_venta(self):

        valores = self.seleccionado(
            self.tabla_carrito
        )

        if valores is None:
            return

        try:

            quitar_del_carrito(
                self.carrito,
                valores[0]
            )

            self.actualizar_carrito()

        except ERRORES as error:

            messagebox.showerror("Error", str(error))


    def vaciar_carrito(self):

        if not self.carrito:
            return

        if messagebox.askyesno(
            "Vaciar carrito",
            "Desea retirar todos los productos?"
        ):

            self.carrito.clear()

            self.actualizar_carrito()


    def actualizar_carrito(self):

        self.vaciar_tabla(self.tabla_carrito)

        for i, producto in enumerate(
            self.carrito.values()
        ):

            self.insertar_fila(
                self.tabla_carrito,
                (
                    producto["codigo"],
                    producto["nombre"],
                    producto["cantidad"],
                    formatear_dinero(
                        producto["precio_centavos"]
                    ),
                    formatear_dinero(
                        producto["subtotal_centavos"]
                    )
                ),
                i
            )

        self.total_venta.configure(
            text=formatear_dinero(
                calcular_total(self.carrito)
            )
        )


    def confirmar_venta(self):
        if not self.permiso():
            return

        if not self.carrito:

            messagebox.showwarning(
                "Aviso",
                "El carrito esta vacio."
            )

            return

        total = formatear_dinero(
            calcular_total(self.carrito)
        )

        pago = self.metodo_pago.get()

        confirmar = messagebox.askyesno(
            "Confirmar venta",
            f"Total: {total}\n"
            f"Metodo de pago: {pago}\n\n"
            "Desea registrar la venta?"
        )

        if not confirmar:
            return

        try:

            id_venta = registrar_venta(
                self.carrito,
                pago
            )

        except ERRORES as error:

            messagebox.showerror(
                "No se pudo registrar la venta",
                str(error)
            )

            return

        self.actualizar_carrito()
        self.actualizar_catalogo()

        messagebox.showinfo(
            "Venta registrada",
            f"Venta V-{id_venta:06d} registrada correctamente."
        )

        try:

            self.ventana_detalle_venta(id_venta)

        except ERRORES as error:

            messagebox.showwarning(
                "Venta guardada",
                f"La venta fue registrada, pero no se pudo "
                f"mostrar su detalle: {error}"
            )


    # ======================================
    # HISTORIAL DE VENTAS
    # ======================================

    def mostrar_historial(self):

        self.limpiar_contenido()

        self.encabezado(
            "Historial de ventas",
            "Consulta y detalle de operaciones registradas"
        )

        filtros = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        filtros.pack(fill="x", pady=5)

        tk.Label(
            filtros,
            text="Fecha (AAAA-MM-DD):",
            bg=FONDO,
            fg=TEXTO
        ).pack(side="left")

        self.fecha_historial = tk.StringVar()

        ttk.Entry(
            filtros,
            textvariable=self.fecha_historial,
            width=13
        ).pack(side="left", padx=5)

        self.pago_historial = tk.StringVar(
            value="Todos"
        )

        ttk.Combobox(
            filtros,
            textvariable=self.pago_historial,
            values=[
                "Todos",
                "Efectivo",
                "Yape",
                "Plin",
                "Tarjeta"
            ],
            state="readonly",
            width=10
        ).pack(side="left", padx=5)

        self.boton(
            filtros,
            "Filtrar",
            self.actualizar_historial
        ).pack(side="left", padx=5)

        self.boton(
            filtros,
            "Limpiar",
            self.limpiar_filtros_historial,
            GRIS
        ).pack(side="left", padx=5)

        herramientas = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        herramientas.pack(fill="x", pady=5)

        self.boton(
            herramientas,
            "Ver detalle de venta",
            self.ver_detalle_seleccionado,
            VERDE
        ).pack(side="left")

        self.resumen_historial = tk.Label(
            self.contenido,
            bg=FONDO,
            fg=GRIS,
            font=("Segoe UI", 11)
        )

        self.resumen_historial.pack(anchor="w", pady=5)

        self.tabla_historial = self.crear_tabla(
            ("id", "fecha", "pago", "total"),
            ("Venta", "Fecha y hora", "Metodo de pago", "Total"),
            (120, 230, 150, 120)
        )

        self.tabla_historial.bind(
            "<Double-1>",
            lambda evento: self.ver_detalle_seleccionado()
        )

        self.actualizar_historial()


    def actualizar_historial(self):

        try:

            ventas = listar_ventas()

            fecha = self.fecha_historial.get().strip()

            pago = self.pago_historial.get()

            if fecha:

                fecha = date.fromisoformat(fecha).isoformat()

                ventas = [
                    venta for venta in ventas
                    if venta["fecha"][:10] == fecha
                ]

            if pago != "Todos":

                ventas = [
                    venta for venta in ventas
                    if venta["metodo_pago"] == pago
                ]

            self.vaciar_tabla(self.tabla_historial)

            total = 0

            for i, venta in enumerate(ventas):

                total += venta["total_centavos"]

                self.insertar_fila(
                    self.tabla_historial,
                    (
                        f"V-{venta['id_venta']:06d}",
                        venta["fecha"],
                        venta["metodo_pago"],
                        formatear_dinero(
                            venta["total_centavos"]
                        )
                    ),
                    i
                )

            self.resumen_historial.configure(
                text=(
                    f"Ventas encontradas: {len(ventas)}"
                    f"  |  Total: {formatear_dinero(total)}"
                )
            )

        except ValueError:

            messagebox.showerror(
                "Fecha incorrecta",
                "Ingrese una fecha valida. Ejemplo: 2026-11-26"
            )

        except (sqlite3.Error, OSError) as error:

            messagebox.showerror("Error", str(error))


    def limpiar_filtros_historial(self):

        self.fecha_historial.set("")
        self.pago_historial.set("Todos")

        self.actualizar_historial()


    def ver_detalle_seleccionado(self):

        valores = self.seleccionado(
            self.tabla_historial
        )

        if valores is None:
            return

        try:

            id_venta = int(
                str(valores[0]).replace("V-", "", 1)
            )

            self.ventana_detalle_venta(id_venta)

        except ERRORES as error:

            messagebox.showerror("Error", str(error))


    def ventana_detalle_venta(self, id_venta):

        resultado = obtener_detalle_venta(id_venta)

        venta = resultado["venta"]

        ventana = tk.Toplevel(self)

        ventana.title(
            f"Detalle de venta V-{id_venta:06d}"
        )

        ventana.geometry("780x480")
        ventana.minsize(650, 400)
        ventana.configure(bg=FONDO)
        ventana.transient(self)

        tk.Label(
            ventana,
            text="TIENDAS MI CHOLO",
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 22, "bold")
        ).pack(pady=(15, 5))

        tk.Label(
            ventana,
            text=f"Comprobante interno V-{id_venta:06d}",
            bg=FONDO,
            fg=GRIS,
            font=("Segoe UI", 12)
        ).pack()

        tk.Label(
            ventana,
            text=(
                f"Fecha: {venta['fecha']}"
                f"  |  Pago: {venta['metodo_pago']}"
            ),
            bg=FONDO,
            fg=TEXTO
        ).pack(pady=10)

        marco = tk.Frame(ventana, bg=FONDO)

        marco.pack(
            fill="both",
            expand=True,
            padx=15
        )

        tabla = self.crear_tabla(
            ("codigo", "nombre", "cantidad", "precio", "subtotal"),
            ("Codigo", "Producto", "Cantidad", "Precio", "Subtotal"),
            (90, 190, 80, 100, 100),
            padre=marco
        )

        for i, producto in enumerate(resultado["detalles"]):

            self.insertar_fila(
                tabla,
                (
                    producto["codigo"],
                    producto["nombre"],
                    producto["cantidad"],
                    formatear_dinero(
                        producto["precio_centavos"]
                    ),
                    formatear_dinero(
                        producto["subtotal_centavos"]
                    )
                ),
                i
            )

        tk.Label(
            ventana,
            text=(
                "TOTAL: "
                + formatear_dinero(venta["total_centavos"])
            ),
            bg=FONDO,
            fg=VERDE,
            font=("Segoe UI", 22, "bold")
        ).pack(pady=10)

        self.boton(
            ventana,
            "Cerrar detalle",
            ventana.destroy
        ).pack(pady=(0, 15))


    # ======================================
    # INVENTARIO
    # ======================================

    def mostrar_inventario(self):

        self.limpiar_contenido()

        self.encabezado(
            "Inventario",
            "Control de existencias y alertas de stock"
        )

        resumen = obtener_resumen_inventario()

        fila = tk.Frame(self.contenido, bg=FONDO)

        fila.pack(fill="x", pady=5)

        self.tarjeta(
            fila,
            "Unidades disponibles",
            str(resumen["total_unidades"])
        )

        self.tarjeta(
            fila,
            "Valor del inventario",
            formatear_dinero(resumen["valor_inventario"]),
            VERDE
        )

        self.tarjeta(
            fila,
            "Productos agotados",
            str(resumen["agotados"]),
            ROJO
        )

        filtros = tk.Frame(
            self.contenido,
            bg=FONDO
        )

        filtros.pack(fill="x", pady=8)

        self.filtro_inventario = tk.StringVar(
            value="Todos"
        )

        selector = ttk.Combobox(
            filtros,
            textvariable=self.filtro_inventario,
            values=[
                "Todos",
                "Stock bajo",
                "Agotados",
                "Disponibles"
            ],
            state="readonly",
            width=20
        )

        selector.pack(side="left")

        selector.bind(
            "<<ComboboxSelected>>",
            lambda evento: self.actualizar_inventario()
        )

        self.tabla_inventario = self.crear_tabla(
            ("codigo", "nombre", "categoria", "stock", "estado"),
            ("Codigo", "Producto", "Categoria", "Stock", "Estado"),
            (100, 200, 140, 80, 130)
        )

        self.actualizar_inventario()


    def actualizar_inventario(self):

        try:

            productos = listar_productos()

            filtro = self.filtro_inventario.get()

            self.vaciar_tabla(self.tabla_inventario)

            for producto in productos:

                stock = producto["stock"]

                if stock == 0:

                    estado = "Agotado"
                    etiqueta = "agotado"

                elif stock <= STOCK_MINIMO:

                    estado = "Stock bajo"
                    etiqueta = "bajo"

                else:

                    estado = "Disponible"
                    etiqueta = "par"

                if filtro == "Stock bajo" and estado != "Stock bajo":
                    continue

                if filtro == "Agotados" and estado != "Agotado":
                    continue

                if filtro == "Disponibles" and estado != "Disponible":
                    continue

                self.tabla_inventario.insert(
                    "",
                    "end",
                    values=(
                        producto["codigo"],
                        producto["nombre"],
                        producto["categoria"],
                        stock,
                        estado
                    ),
                    tags=(etiqueta,)
                )

        except ERRORES as error:

            messagebox.showerror("Error", str(error))


    # ======================================
    # REPORTES Y ESTADISTICAS
    # ======================================

    def mostrar_reportes(self):
        if not self.permiso(True):
            return

        self.limpiar_contenido()

        self.encabezado(
            "Reportes",
            "Resumen de ingresos y rendimiento comercial"
        )

        exportaciones = tk.Frame(self.contenido, bg=FONDO)
        exportaciones.pack(fill="x", pady=4)
        opciones = [
            ("Productos", exportar_productos),
            ("Ventas", exportar_ventas),
            ("Detalle de ventas", exportar_detalle_ventas),
            ("Inventario", exportar_inventario),
            ("Ingresos", exportar_ingresos),
            ("Exportar todo", exportar_todo)
        ]
        for i, (nombre, funcion) in enumerate(opciones):
            self.boton(
                exportaciones, nombre,
                lambda f=funcion: self.generar_reporte_csv(f),
                VERDE if nombre == "Exportar todo" else AZUL
            ).grid(row=i // 3, column=i % 3, sticky="ew", padx=3, pady=3)
        for columna in range(3):
            exportaciones.columnconfigure(columna, weight=1)
        self.boton(self.contenido, "Abrir carpeta de reportes",
                   self.abrir_carpeta_reportes, GRIS).pack(anchor="w", pady=3)

        ingresos = obtener_ingresos()

        fila = tk.Frame(self.contenido, bg=FONDO)

        fila.pack(fill="x", pady=5)

        self.tarjeta(
            fila,
            "Ingresos diarios",
            formatear_dinero(ingresos["ingresos_hoy"]),
            VERDE
        )

        self.tarjeta(
            fila,
            "Ingresos mensuales",
            formatear_dinero(ingresos["ingresos_mes"]),
            VERDE
        )

        self.tarjeta(
            fila,
            "Ingresos totales",
            formatear_dinero(ingresos["ingresos_totales"]),
            VERDE
        )

        tk.Label(
            self.contenido,
            text="Ingresos por metodo de pago",
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(10, 2))

        tabla_pago = self.crear_tabla(
            ("pago", "ventas", "ingresos"),
            ("Metodo de pago", "Ventas", "Ingresos"),
            (180, 100, 150),
            altura=4
        )

        for i, registro in enumerate(
            obtener_ingresos_por_pago()
        ):

            self.insertar_fila(
                tabla_pago,
                (
                    registro["metodo_pago"],
                    registro["cantidad_ventas"],
                    formatear_dinero(
                        registro["ingresos"]
                    )
                ),
                i
            )

        tk.Label(
            self.contenido,
            text="Productos mas vendidos",
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(10, 2))

        tabla_productos = self.crear_tabla(
            ("codigo", "nombre", "unidades", "ingresos"),
            ("Codigo", "Producto", "Unidades vendidas", "Ingresos"),
            (90, 180, 140, 130),
            altura=5
        )

        for i, producto in enumerate(
            obtener_productos_mas_vendidos()
        ):

            self.insertar_fila(
                tabla_productos,
                (
                    producto["codigo"],
                    producto["nombre"],
                    producto["unidades_vendidas"],
                    formatear_dinero(
                        producto["ingresos"]
                    )
                ),
                i
            )


    def generar_reporte_csv(self, funcion):
        if not self.permiso(True):
            return
        try:
            resultado = funcion()
            archivos = resultado if isinstance(resultado, list) else [resultado]
            mensaje = "\n".join(archivo.name for archivo in archivos)
            messagebox.showinfo("Reportes generados", mensaje, parent=self)
        except ERRORES as error:
            messagebox.showerror("Error de exportacion", str(error), parent=self)

    def abrir_carpeta_reportes(self):
        if not self.permiso(True):
            return
        try:
            CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(CARPETA_REPORTES))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(CARPETA_REPORTES)])
            else:
                subprocess.Popen(["xdg-open", str(CARPETA_REPORTES)])
        except OSError as error:
            messagebox.showerror("No se pudo abrir la carpeta", str(error), parent=self)


    # ======================================
    # SEGURIDAD
    # ======================================

    def mostrar_seguridad(self):
        if not self.permiso(True):
            return

        self.limpiar_contenido()

        self.encabezado(
            "Seguridad del sistema",
            "Proteccion de datos e integridad de operaciones"
        )

        protecciones = [
            (
                "Validacion de entradas",
                "Control de codigos, nombres, precios y cantidades."
            ),
            (
                "Base de datos SQLite",
                "Almacenamiento permanente de informacion."
            ),
            (
                "Consultas parametrizadas",
                "Separacion de instrucciones SQL y valores ingresados."
            ),
            (
                "Transacciones",
                "Registro de ventas y actualizacion de stock."
            ),
            (
                "Eliminacion logica",
                "Conservacion de productos y relaciones historicas."
            ),
            (
                "Control de errores",
                "Manejo de excepciones y mensajes informativos."
            )
        ]

        for titulo, descripcion in protecciones:

            marco = tk.Frame(
                self.contenido,
                bg=BLANCO,
                padx=15,
                pady=10
            )

            marco.pack(fill="x", pady=3)

            tk.Label(
                marco,
                text=titulo,
                bg=BLANCO,
                fg=VERDE,
                font=("Segoe UI", 12, "bold")
            ).pack(anchor="w")

            tk.Label(
                marco,
                text=descripcion,
                bg=BLANCO,
                fg=GRIS,
                font=("Segoe UI", 10),
                wraplength=650,
                justify="left"
            ).pack(anchor="w")

        tk.Label(
            self.contenido,
            text="Copias de seguridad: modulo pendiente de integracion.",
            bg=FONDO,
            fg=NARANJA,
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=10)


    # ======================================
    # CIERRE DEL SISTEMA
    # ======================================

    def salir(self):

        mensaje = "Desea cerrar el sistema?"

        if self.carrito:

            mensaje = (
                "Existe una venta sin confirmar.\n"
                "El carrito se perdera al cerrar.\n\n"
                "Desea salir?"
            )

        if messagebox.askyesno(
            "Salir del sistema",
            mensaje,
            parent=self
        ):

            self.destroy()


# ==========================================
# INICIO DE LA APLICACION
# ==========================================

def iniciar_interfaz():

    inicializar_base_datos()

    aplicacion = Aplicacion()

    aplicacion.mainloop()


if __name__ == "__main__":

    try:

        iniciar_interfaz()

    except (sqlite3.Error, OSError, tk.TclError) as error:

        print(f"Error al iniciar el sistema: {error}")
