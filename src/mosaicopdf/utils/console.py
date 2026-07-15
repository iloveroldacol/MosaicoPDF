"""
Funciones para mostrar mensajes en la terminal.

Toda la interacción con la consola se centraliza aquí.
De esta manera el resto del programa no utiliza print()
directamente.
"""

APP_NAME = "MosaicoPDF"
APP_VERSION = "1.0"


def header() -> None:
    """Muestra el encabezado de la aplicación."""

    print("=" * 60)
    print(f"{APP_NAME} {APP_VERSION}")
    print("=" * 60)
    print()


def blank() -> None:
    """Imprime una línea en blanco."""

    print()


def info(message: str) -> None:
    """Mensaje informativo."""

    print(f"[INFO] {message}")


def ok(message: str) -> None:
    """Mensaje de operación exitosa."""

    print(f"[ OK ] {message}")


def warning(message: str) -> None:
    """Mensaje de advertencia."""

    print(f"[WARN] {message}")


def error(message: str) -> None:
    """Mensaje de error."""

    print(f"[ERROR] {message}")


def print_summary(
    input_file: str,
    output_file: str,
    paper_name: str,
    rows: int,
    columns: int,
) -> None:
    """
    Muestra un resumen del mosaico generado.
    """

    blank()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)

    print(f"Archivo origen : {input_file}")
    print(f"Archivo salida : {output_file}")
    print(f"Papel          : {paper_name}")
    print(f"Filas          : {rows}")
    print(f"Columnas       : {columns}")
    print(f"Total hojas    : {rows * columns}")

    blank()


def print_ascii_mosaic(rows: int, columns: int) -> None:
    """
    Dibuja el mosaico utilizando caracteres ASCII.
    """

    blank()
    print("Mosaico generado:")
    blank()

    cell_width = 8

    horizontal = "+" + ("-" * cell_width + "+") * columns

    for row in range(rows):

        print(horizontal)

        line = "|"

        for column in range(columns):
            text = f"{row},{column}"
            line += text.center(cell_width) + "|"

        print(line)

    print(horizontal)

    blank()