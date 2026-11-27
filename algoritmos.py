
from time import perf_counter
from random import Random

from productos import listar_productos
from base_datos import inicializar_base_datos
from validaciones import formatear_dinero


# ==========================================
# CONFIGURACION
# ==========================================

LIMITE_BURBUJA = 500

CAMPOS_VALIDOS = (
    "codigo",
    "nombre",
    "categoria",
    "precio_centavos",
    "stock"
)


# ==========================================
# BUSQUEDA SECUENCIAL
# ==========================================

def busqueda_secuencial(productos, termino):

    termino = str(termino).strip().casefold()

    if not termino:
        raise ValueError("Ingrese un termino de busqueda.")

    if len(termino) > 60:
        raise ValueError(
            "La busqueda no puede superar 60 caracteres."
        )

    resultados = []

    for producto in productos:

        codigo = producto["codigo"].casefold()
        nombre = producto["nombre"].casefold()
        categoria = producto["categoria"].casefold()

        if (
            termino in codigo
            or termino in nombre
            or termino in categoria
        ):

            resultados.append(producto)

    return resultados


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def validar_campo(campo):

    if campo not in CAMPOS_VALIDOS:

        raise ValueError(
            "Campo de ordenamiento no permitido."
        )


def obtener_clave(producto, campo):

    valor = producto[campo]

    if isinstance(valor, str):

        return valor.casefold()

    return valor


# ==========================================
# ORDENAMIENTO BURBUJA
# ==========================================

def ordenamiento_burbuja(
    productos,
    campo="nombre",
    descendente=False
):

    validar_campo(campo)

    lista = productos.copy()

    n = len(lista)

    for i in range(n - 1):

        intercambio = False

        for j in range(n - 1 - i):

            actual = obtener_clave(lista[j], campo)

            siguiente = obtener_clave(
                lista[j + 1],
                campo
            )

            if descendente:

                cambiar = actual < siguiente

            else:

                cambiar = actual > siguiente

            if cambiar:

                lista[j], lista[j + 1] = (
                    lista[j + 1],
                    lista[j]
                )

                intercambio = True

        if not intercambio:

            break

    return lista


# ==========================================
# MERGE SORT - ORDENAMIENTO POR MEZCLA
# ==========================================

def mezclar(
    izquierda,
    derecha,
    campo,
    descendente
):

    resultado = []

    i = 0
    j = 0

    while i < len(izquierda) and j < len(derecha):

        valor_izquierdo = obtener_clave(
            izquierda[i],
            campo
        )

        valor_derecho = obtener_clave(
            derecha[j],
            campo
        )

        if descendente:

            elegir_izquierda = (
                valor_izquierdo >= valor_derecho
            )

        else:

            elegir_izquierda = (
                valor_izquierdo <= valor_derecho
            )

        if elegir_izquierda:

            resultado.append(izquierda[i])

            i += 1

        else:

            resultado.append(derecha[j])

            j += 1

    resultado.extend(izquierda[i:])

    resultado.extend(derecha[j:])

    return resultado


def merge_sort_recursivo(
    productos,
    campo,
    descendente
):

    # Caso base

    if len(productos) <= 1:

        return productos.copy()

    # Division de la lista

    mitad = len(productos) // 2

    # Casos recursivos

    izquierda = merge_sort_recursivo(
        productos[:mitad],
        campo,
        descendente
    )

    derecha = merge_sort_recursivo(
        productos[mitad:],
        campo,
        descendente
    )

    # Combinacion de resultados

    return mezclar(
        izquierda,
        derecha,
        campo,
        descendente
    )


def ordenamiento_merge_sort(
    productos,
    campo="nombre",
    descendente=False
):

    validar_campo(campo)

    return merge_sort_recursivo(
        productos,
        campo,
        descendente
    )


# ==========================================
# ORDENAMIENTO ADAPTATIVO
# ==========================================

def ordenamiento_adaptativo(
    productos,
    campo="nombre",
    descendente=False
):

    validar_campo(campo)

    cantidad = len(productos)

    inicio = perf_counter()

    if cantidad <= LIMITE_BURBUJA:

        resultado = ordenamiento_burbuja(
            productos,
            campo,
            descendente
        )

        algoritmo = "Bubble Sort"

        complejidad = "O(n^2)"

    else:

        resultado = ordenamiento_merge_sort(
            productos,
            campo,
            descendente
        )

        algoritmo = "Merge Sort"

        complejidad = "O(n log n)"

    tiempo = perf_counter() - inicio

    return {
        "productos": resultado,
        "algoritmo": algoritmo,
        "cantidad": cantidad,
        "tiempo": tiempo,
        "complejidad": complejidad
    }


# ==========================================
# MOSTRAR RESULTADOS
# ==========================================

def mostrar_resultados(productos):

    if not productos:

        print("\nNo se encontraron productos.")

        return

    print("\n" + "=" * 80)

    print("RESULTADOS DEL CATALOGO")

    print("=" * 80)

    for producto in productos:

        print(
            f"{producto['codigo']} | "
            f"{producto['nombre']} | "
            f"{producto['categoria']} | "
            f"{formatear_dinero(producto['precio_centavos'])} | "
            f"Stock: {producto['stock']}"
        )

    print("=" * 80)

    print(f"Total de productos: {len(productos)}")


def mostrar_rendimiento(resultado):

    print("\nRENDIMIENTO DEL ORDENAMIENTO")

    print("-" * 45)

    print(
        f"Algoritmo: {resultado['algoritmo']}"
    )

    print(
        f"Productos: {resultado['cantidad']}"
    )

    print(
        f"Tiempo: {resultado['tiempo']:.8f} segundos"
    )

    print(
        f"Complejidad: {resultado['complejidad']}"
    )

    print("-" * 45)


# ==========================================
# GENERACION DE DATOS DE PRUEBA
# ==========================================

def generar_productos_prueba(cantidad):

    if not isinstance(cantidad, int):

        raise ValueError("La cantidad debe ser entera.")

    if not 1 <= cantidad <= 100000:

        raise ValueError(
            "La prueba permite entre 1 y 100000 productos."
        )

    generador = Random(42)

    productos = []

    for i in range(cantidad):

        producto = {
            "codigo": f"P{i + 1:06d}",
            "nombre": f"Producto {i + 1}",
            "categoria": "Prueba",
            "precio_centavos": generador.randint(
                1, 1000000
            ),
            "stock": generador.randint(0, 100000),
            "activo": 1
        }

        productos.append(producto)

    return productos


# ==========================================
# COMPARACION DE ALGORITMOS
# ==========================================

def comparar_algoritmos():

    cantidades = [
        100,
        500,
        1000,
        10000,
        100000
    ]

    print("\n" + "=" * 70)

    print("PRUEBA DE RENDIMIENTO DE ALGORITMOS")

    print("=" * 70)

    for cantidad in cantidades:

        productos = generar_productos_prueba(
            cantidad
        )

        print(f"\nProductos generados: {cantidad}")

        print("-" * 45)

        esperado = sorted(
            productos,
            key=lambda producto:
                producto["precio_centavos"]
        )

        if cantidad <= 1000:

            inicio = perf_counter()

            resultado_burbuja = ordenamiento_burbuja(
                productos,
                "precio_centavos"
            )

            tiempo_burbuja = perf_counter() - inicio

            print(
                f"Bubble Sort: "
                f"{tiempo_burbuja:.8f} segundos"
            )

            print(
                "Resultado correcto:",
                resultado_burbuja == esperado
            )

        else:

            print(
                "Bubble Sort: omitido para evitar "
                "procesamiento excesivo."
            )

        inicio = perf_counter()

        resultado_merge = ordenamiento_merge_sort(
            productos,
            "precio_centavos"
        )

        tiempo_merge = perf_counter() - inicio

        print(
            f"Merge Sort: "
            f"{tiempo_merge:.8f} segundos"
        )

        print(
            "Resultado correcto:",
            resultado_merge == esperado
        )

        resultado = ordenamiento_adaptativo(
            productos,
            "precio_centavos"
        )

        print(
            f"Modo adaptativo: {resultado['algoritmo']}"
        )

        print(
            "Resultado adaptativo correcto:",
            resultado["productos"] == esperado
        )

    print("\nPruebas finalizadas.")


# ==========================================
# MENU DE CONSOLA
# ==========================================

def menu_algoritmos():

    while True:

        print("\n" + "=" * 45)

        print("TIENDAS MI CHOLO - ALGORITMOS")

        print("=" * 45)

        print("1. Buscar producto")
        print("2. Ordenar por nombre")
        print("3. Ordenar por precio ascendente")
        print("4. Ordenar por precio descendente")
        print("5. Ordenar por stock")
        print("6. Ordenar por codigo")
        print("7. Ordenar por categoria")
        print("8. Comparar algoritmos")
        print("0. Regresar")

        try:

            opcion = input(
                "\nSeleccione una opcion: "
            ).strip()

            if opcion == "0":

                break

            elif opcion == "8":

                comparar_algoritmos()

            elif opcion == "1":

                productos = listar_productos()

                termino = input(
                    "Ingrese codigo, nombre o categoria: "
                )

                resultado = busqueda_secuencial(
                    productos,
                    termino
                )

                mostrar_resultados(resultado)

            elif opcion in (
                "2", "3", "4", "5", "6", "7"
            ):

                productos = listar_productos()

                opciones = {
                    "2": ("nombre", False),
                    "3": ("precio_centavos", False),
                    "4": ("precio_centavos", True),
                    "5": ("stock", False),
                    "6": ("codigo", False),
                    "7": ("categoria", False)
                }

                campo, descendente = opciones[opcion]

                resultado = ordenamiento_adaptativo(
                    productos,
                    campo,
                    descendente
                )

                mostrar_resultados(
                    resultado["productos"]
                )

                mostrar_rendimiento(resultado)

            else:

                print("Opcion incorrecta.")

        except ValueError as error:

            print(f"Error: {error}")

        except (KeyboardInterrupt, EOFError):

            print("\nRegresando al menu principal.")

            break


# ==========================================
# EJECUCION DIRECTA
# ==========================================

if __name__ == "__main__":

    inicializar_base_datos()

    menu_algoritmos()
