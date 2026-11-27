import runpy
import argparse


def main():
    parser = argparse.ArgumentParser(description='Sistema de gestion comercial Tiendas Mi Cholo')
    parser.add_argument('--consola', action='store_true', help='Iniciar en modo consola')
    argumentos = parser.parse_args()
    runpy.run_module('consola' if argumentos.consola else 'interfaz', run_name='__main__')


if __name__ == '__main__':
    main()
