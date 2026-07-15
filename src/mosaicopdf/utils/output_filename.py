"""
Funciones para generar automáticamente el nombre del
archivo PDF de salida.

Ejemplo:

plano.pdf
↓
plano_mosaico.pdf

Si ya existe:

plano_mosaico_2.pdf
"""

from pathlib import Path


def build_output_filename(input_file: str) -> Path:
    """
    Genera automáticamente el nombre del PDF de salida.

    El archivo se guarda en la misma carpeta que el PDF
    original.

    Nunca sobrescribe un archivo existente.
    """

    input_path = Path(input_file)

    directory = input_path.parent
    stem = input_path.stem
    suffix = input_path.suffix

    output = directory / f"{stem}_mosaico{suffix}"

    if not output.exists():
        return output

    counter = 2

    while True:

        output = directory / f"{stem}_mosaico_{counter}{suffix}"

        if not output.exists():
            return output

        counter += 1