"""
Formatos de papel estándar y de gran formato soportados por MosaicoPDF.

Las dimensiones físicas se almacenan en puntos PDF (1 pulgada = 72 pt).
"""

from __future__ import annotations

from mosaicopdf.models.paper import Paper
from mosaicopdf.utils.units import mm_to_pt, parse_dimensions

OFFICE_PAPERS: dict[str, Paper] = {
    "carta": Paper(name="Carta", width=612.0, height=792.0),
    "oficio": Paper(name="Oficio", width=612.0, height=936.0),
    "legal": Paper(name="Legal", width=612.0, height=1008.0),
    "a4": Paper(name="A4", width=mm_to_pt(210.0), height=mm_to_pt(297.0)),
    "a3": Paper(name="A3", width=mm_to_pt(297.0), height=mm_to_pt(420.0)),
    "tabloide": Paper(name="Tabloide", width=792.0, height=1224.0),
}

LARGE_FORMAT_PAPERS: dict[str, Paper] = {
    "a2": Paper(name="A2", width=mm_to_pt(420.0), height=mm_to_pt(594.0)),
    "a1": Paper(name="A1", width=mm_to_pt(594.0), height=mm_to_pt(841.0)),
    "a0": Paper(name="A0", width=mm_to_pt(841.0), height=mm_to_pt(1189.0)),
    "arch_c": Paper(name="ARCH C", width=1296.0, height=1728.0),
    "arch_d": Paper(name="ARCH D", width=1728.0, height=2592.0),
    "arch_e": Paper(name="ARCH E", width=2592.0, height=3456.0),
}

PAPERS: dict[str, Paper] = {**OFFICE_PAPERS, **LARGE_FORMAT_PAPERS}


def get_paper(name: str) -> Paper:
    """Devuelve un formato de papel predefinido por nombre."""
    key = name.strip().lower()
    if key not in PAPERS:
        available = ", ".join(PAPERS.keys())
        raise ValueError(
            f"Formato de papel no válido: '{name}'. "
            f"Opciones disponibles: {available}."
        )
    return PAPERS[key]


def parse_paper(spec: str) -> Paper:
    """
    Interpreta un formato predefinido (ej. ``carta``, ``a4``) o una medida
    personalizada ``ANCHOxALTO`` (ej. ``215x280mm`` o ``22x33cm``).
    """
    key = spec.strip().lower()
    if key in PAPERS:
        return PAPERS[key]

    try:
        width, height = parse_dimensions(spec, default_unit="mm")
    except ValueError as exc:
        available = ", ".join(PAPERS.keys())
        raise ValueError(
            f"Formato de papel no válido: '{spec}'. "
            f"Usa un nombre ({available}) o medidas ANCHOxALTO (ej. 215x280mm)."
        ) from exc

    return Paper(name=f"Personalizado ({spec.strip()})", width=width, height=height)
