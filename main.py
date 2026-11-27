
import runpy
import argparse


def main():
    """Punto de entrada principal de Tiendas Mi Cholo."""

    parser = argparse.ArgumentParser(
        description="Sistema de gestion comercial Tiendas Mi Cholo"
    )

    parser.add_argument(
        "--consola",
        action="store_true",
        help="Iniciar el sistema en modo consola"
    )

    argumentos = parser.parse_args()

    if argumentos.consola:
        print("Modo consola pendiente de integracion.")
    else:
        runpy.run_module("interfaz", run_name="__main__")


if __name__ == "__main__":
    main()
