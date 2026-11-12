"""
Generación segura de nombres de archivo de salida sin sobrescritura accidental.
"""

from __future__ import annotations

from pathlib import Path


def build_output_filename(
    input_file: str | Path,
    output_dir: str | Path | None = None,
    suffix_tag: str = "_mosaico",
    extension: str | None = None,
) -> Path:
    """
    Genera automáticamente un nombre de archivo de salida único.

    Si no se indica ``output_dir``, se guarda junto al PDF original.
    Nunca sobrescribe un archivo existente salvo que el usuario especifique
    una ruta explícita fuera de esta función.
    """
    input_path = Path(input_file)
    directory = Path(output_dir) if output_dir is not None else input_path.parent
    stem = input_path.stem
    ext = extension if extension is not None else (input_path.suffix or ".pdf")
    if not ext.startswith("."):
        ext = f".{ext}"

    candidate = directory / f"{stem}{suffix_tag}{ext}"
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = directory / f"{stem}{suffix_tag}_{counter}{ext}"
        if not candidate.exists():
            return candidate
        counter += 1
