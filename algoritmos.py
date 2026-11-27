
from productos import listar_productos
from base_datos import inicializar_base_datos
from validaciones import formatear_dinero


def busqueda_secuencial(productos, termino):
    """Busca productos por codigo, nombre o categoria."""

    termino = str(termino).strip().casefold()

    if not termino:
        raise ValueError("Ingrese un termino de busqueda.")

    if len(termino) > 60:
        raise ValueError("El termino de busqueda es demasiado largo.")

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


def ordenamiento_burbuja(
    productos,
    campo="nombre",
    descendente=False
):
    """Ordena productos mediante el algoritmo burbuja."""

    campos_permitidos = [
        "codigo",
        "nombre",
        "categoria",
        "precio_centavos",
        "stock"
    ]

    if campo not in campos_permitidos:
        raise ValueError("Campo de ordenamiento no permitido.")

    lista = productos.copy()
    n = len(lista)

    for i in range(n - 1):

        intercambio = False

        for j in range(n - 1 - i):

            actual = lista[j][campo]
            siguiente = lista[j + 1][campo]

            if isinstance(actual, str):
                actual = actual.casefold()
                siguiente = siguiente.casefold()

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


def mostrar_resultados(productos):
    """Muestra los resultados obtenidos."""

    if not productos:
        print("No se encontraron productos.")
        return

    print("-" * 95)

    print(
        f"{'CODIGO':<22}"
        f"{'PRODUCTO':<25}"
        f"{'CATEGORIA':<20}"
        f"{'PRECIO':<18}"
        f"{'STOCK'}"
    )

    print("-" * 95)

    for producto in productos:

        precio = formatear_dinero(
            producto["precio_centavos"]
        )

        print(
            f"{producto['codigo']:<22}"
            f"{producto['nombre'][:24]:<25}"
            f"{producto['categoria'][:19]:<20}"
            f"{precio:<18}"
            f"{producto['stock']}"
        )

    print("-" * 95)
    print(f"Productos encontrados: {len(productos)}")


def menu_algoritmos():
    """Menu de prueba de busqueda y ordenamiento."""

    while True:

        print("\n===== BUSQUEDA Y ORDENAMIENTO =====")
        print("1. Buscar producto")
        print("2. Ordenar por nombre")
        print("3. Ordenar por precio: menor a mayor")
        print("4. Ordenar por precio: mayor a menor")
        print("5. Ordenar por stock: menor a mayor")
        print("6. Ordenar por codigo")
        print("7. Ordenar por categoria")
        print("0. Salir")

        try:

            opcion = input(
                "Seleccione una opcion: "
            ).strip()

            if opcion == "0":
                print("Modulo finalizado.")
                break

            productos = listar_productos()

            if opcion == "1":

                termino = input(
                    "Ingrese codigo, nombre o categoria: "
                )

                resultados = busqueda_secuencial(
                    productos, termino
                )

            elif opcion == "2":

                resultados = ordenamiento_burbuja(
                    productos, "nombre"
                )

            elif opcion == "3":

                resultados = ordenamiento_burbuja(
                    productos, "precio_centavos"
                )

            elif opcion == "4":

                resultados = ordenamiento_burbuja(
                    productos, "precio_centavos", True
                )

            elif opcion == "5":

                resultados = ordenamiento_burbuja(
                    productos, "stock"
                )

            elif opcion == "6":

                resultados = ordenamiento_burbuja(
                    productos, "codigo"
                )

            elif opcion == "7":

                resultados = ordenamiento_burbuja(
                    productos, "categoria"
                )

            else:

                print("Opcion invalida.")
                continue

            mostrar_resultados(resultados)

        except ValueError as error:

            print(f"AVISO: {error}")

        except (KeyboardInterrupt, EOFError):

            print("\nModulo finalizado.")
            break


if __name__ == "__main__":

    import sqlite3

    try:

        inicializar_base_datos()
        menu_algoritmos()

    except (sqlite3.Error, OSError) as error:

        print(f"Error de almacenamiento: {error}")
