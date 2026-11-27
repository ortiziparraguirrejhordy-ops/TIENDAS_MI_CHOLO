
import re
from decimal import Decimal, InvalidOperation


# Limites establecidos para el sistema
MAX_CODIGO = 20
MAX_NOMBRE = 60
MAX_CATEGORIA = 40
MAX_PRECIO = Decimal("10000.00")
MAX_STOCK = 100000


def validar_codigo(codigo):
    """Valida el codigo de un producto."""

    codigo = str(codigo).strip().upper()

    if not 1 <= len(codigo) <= MAX_CODIGO:
        raise ValueError(
            "El codigo debe tener entre 1 y 20 caracteres."
        )

    if not re.fullmatch(r"[A-Z0-9-]+", codigo):
        raise ValueError(
            "El codigo solo admite letras, numeros y guiones."
        )

    return codigo


def validar_texto(texto, campo, limite):
    """Valida nombres y categorias."""

    texto = str(texto).strip()

    if not 2 <= len(texto) <= limite:
        raise ValueError(
            f"{campo} debe tener entre 2 y {limite} caracteres."
        )

    if not any(caracter.isalpha() for caracter in texto):
        raise ValueError(
            f"{campo} debe contener letras."
        )

    for caracter in texto:
        if not (
            caracter.isalnum()
            or caracter in " -.,()/&%"
        ):
            raise ValueError(
                f"{campo} contiene caracteres no permitidos."
            )

    return " ".join(texto.split())


def validar_nombre(nombre):
    """Valida el nombre del producto."""

    return validar_texto(
        nombre, "El nombre", MAX_NOMBRE
    )


def validar_categoria(categoria):
    """Valida la categoria del producto."""

    return validar_texto(
        categoria, "La categoria", MAX_CATEGORIA
    )


def validar_precio(precio):
    """Valida el precio y lo convierte a centimos."""

    precio = str(precio).strip().replace(",", ".")

    if len(precio) > 12:
        raise ValueError("El precio es demasiado largo.")

    if not re.fullmatch(r"[0-9]+(\.[0-9]{1,2})?", precio):
        raise ValueError(
            "Ingrese un precio valido con hasta dos decimales."
        )

    try:
        valor = Decimal(precio)

    except InvalidOperation:
        raise ValueError("El precio ingresado no es valido.")

    if not Decimal("0.01") <= valor <= MAX_PRECIO:
        raise ValueError(
            "El precio debe estar entre S/ 0.01 y S/ 10000."
        )

    return int(valor * 100)


def validar_entero(valor, campo, minimo, maximo):
    """Valida cantidades enteras dentro de un rango."""

    valor = str(valor).strip()

    if len(valor) > len(str(maximo)):
        raise ValueError(f"{campo}: cantidad demasiado grande.")

    if not re.fullmatch(r"[0-9]+", valor):
        raise ValueError(
            f"{campo} debe ser un numero entero positivo o cero."
        )

    numero = int(valor)

    if not minimo <= numero <= maximo:
        raise ValueError(
            f"{campo} debe estar entre {minimo} y {maximo}."
        )

    return numero


def validar_stock(stock):
    """Valida las existencias de un producto."""

    return validar_entero(
        stock, "El stock", 0, MAX_STOCK
    )


def validar_cantidad(cantidad):
    """Valida la cantidad de una venta."""

    return validar_entero(
        cantidad, "La cantidad", 1, MAX_STOCK
    )


def validar_metodo_pago(metodo):
    """Valida el metodo de pago seleccionado."""

    metodos = ["Efectivo", "Yape", "Plin", "Tarjeta"]

    metodo = str(metodo).strip().capitalize()

    if metodo not in metodos:
        raise ValueError("Metodo de pago no permitido.")

    return metodo


def formatear_dinero(centavos):
    """Convierte centimos a soles para mostrarlos."""

    return f"S/ {Decimal(centavos) / 100:,.2f}"


if __name__ == "__main__":

    casos = [
        (validar_codigo, "P001"),
        (validar_codigo, "1" * 1000),
        (validar_nombre, "Arroz 1 kg"),
        (validar_nombre, "111111111111"),
        (validar_precio, "4.50"),
        (validar_precio, "-50"),
        (validar_precio, "999999999999999999"),
        (validar_precio, "NaN"),
        (validar_stock, "50"),
        (validar_stock, "999999999999999999"),
        (validar_stock, "abc"),
        (validar_cantidad, "0"),
        (validar_cantidad, "5"),
        (validar_metodo_pago, "Yape")
    ]

    print("====================================")
    print(" PRUEBAS DE VALIDACION - MI CHOLO")
    print("====================================")

    for funcion, dato in casos:

        muestra = dato[:25]

        if len(dato) > 25:
            muestra += "..."

        try:
            resultado = funcion(dato)

            print(
                f"ACEPTADO | {muestra} | {resultado}"
            )

        except ValueError as error:

            print(
                f"RECHAZADO | {muestra} | {error}"
            )

    print("====================================")
    print("Pruebas finalizadas.")
    print("====================================")
