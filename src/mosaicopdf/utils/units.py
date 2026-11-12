"""
Conversión y formato de unidades físicas y factores de escala.

Internamente, MosaicoPDF opera en puntos PDF (1 pulgada = 72 pt).
La unidad predeterminada para la interacción con el usuario es el milímetro (mm).
"""

from __future__ import annotations

import re

PT_PER_INCH: float = 72.0
MM_PER_INCH: float = 25.4
PT_PER_MM: float = PT_PER_INCH / MM_PER_INCH
PT_PER_CM: float = PT_PER_MM * 10.0

_UNIT_FACTORS: dict[str, float] = {
    "mm": PT_PER_MM,
    "cm": PT_PER_CM,
    "m": PT_PER_MM * 1000.0,
    "in": PT_PER_INCH,
    "pulg": PT_PER_INCH,
    "pt": 1.0,
}

_LENGTH_RE = re.compile(
    r"^\s*([+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+))\s*([a-zA-Z]*)\s*$"
)
_DIM_RE = re.compile(
    r"^\s*(.+?)\s*[xX×]\s*(.+?)\s*$"
)


def mm_to_pt(mm: float) -> float:
    """Convierte milímetros a puntos PDF."""
    return mm * PT_PER_MM


def pt_to_mm(pt: float) -> float:
    """Convierte puntos PDF a milímetros."""
    return pt / PT_PER_MM


def cm_to_pt(cm: float) -> float:
    """Convierte centímetros a puntos PDF."""
    return cm * PT_PER_CM


def pt_to_cm(pt: float) -> float:
    """Convierte puntos PDF a centímetros."""
    return pt / PT_PER_CM


def parse_length(value: str | float | int, default_unit: str = "mm") -> float:
    """
    Convierte una longitud textual o numérica a puntos PDF.

    Ejemplos válidos: ``"10"``, ``"10mm"``, ``"1.5cm"``, ``"0.5in"``, ``"28pt"``.
    Si ``value`` es numérico o no especifica unidad, se asume ``default_unit``.
    """
    if isinstance(value, (int, float)):
        unit = default_unit.strip().lower()
        if unit not in _UNIT_FACTORS:
            raise ValueError(f"Unidad no soportada: '{default_unit}'.")
        return float(value) * _UNIT_FACTORS[unit]

    text = str(value).strip()
    match = _LENGTH_RE.match(text)
    if not match:
        raise ValueError(
            f"Longitud inválida: '{value}'. Usa un número con unidad opcional "
            "(ej. 10mm, 1.5cm, 0.5in, 28pt)."
        )

    number_str, unit_str = match.groups()
    number = float(number_str.replace(",", "."))
    unit = (unit_str or default_unit).strip().lower()

    if unit not in _UNIT_FACTORS:
        supported = ", ".join(_UNIT_FACTORS.keys())
        raise ValueError(f"Unidad no soportada '{unit}'. Opciones: {supported}.")

    return number * _UNIT_FACTORS[unit]


def parse_dimensions(
    spec: str,
    default_unit: str = "mm",
) -> tuple[float, float]:
    """
    Interpreta una especificación ``ANCHO x ALTO`` en puntos PDF.

    Si solo el segundo valor trae unidad (ej. ``"120x90cm"``), esa unidad
    se aplica también al primer valor.
    """
    match = _DIM_RE.match(spec)
    if not match:
        raise ValueError(
            f"Dimensión inválida: '{spec}'. Usa el formato ANCHOxALTO "
            "(ej. 1200x900mm o 120x90cm)."
        )

    left_raw, right_raw = match.groups()

    right_match = _LENGTH_RE.match(right_raw)
    left_match = _LENGTH_RE.match(left_raw)
    if not left_match or not right_match:
        raise ValueError(f"Dimensión inválida: '{spec}'.")

    left_unit = left_match.group(2)
    right_unit = right_match.group(2)

    inferred_unit = right_unit if (not left_unit and right_unit) else default_unit

    width = parse_length(left_raw, default_unit=inferred_unit)
    height = parse_length(right_raw, default_unit=default_unit)

    if width <= 0 or height <= 0:
        raise ValueError("El ancho y el alto deben ser mayores que cero.")

    return width, height


def parse_margins(
    spec: str,
    default_unit: str = "mm",
) -> tuple[float, float, float, float]:
    """
    Interpreta 1, 2 o 4 márgenes en orden CSS:
    - 1 valor: todos iguales (``"8mm"``)
    - 2 valores: vertical, horizontal (``"10mm,5mm"``)
    - 4 valores: arriba, derecha, abajo, izquierda (``"10,8,10,8mm"``)
    """
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    if len(parts) not in (1, 2, 4):
        raise ValueError(
            f"Márgenes inválidos: '{spec}'. Indica 1 valor, 2 valores "
            "(vertical,horizontal) o 4 valores (arriba,derecha,abajo,izquierda)."
        )

    # Si el último trae unidad y los anteriores no, propagar esa unidad.
    last_match = _LENGTH_RE.match(parts[-1])
    trailing_unit = last_match.group(2) if last_match else ""
    unit = trailing_unit or default_unit

    values = [parse_length(p, default_unit=unit) for p in parts]
    if any(v < 0 for v in values):
        raise ValueError("Los márgenes no pueden ser negativos.")

    if len(values) == 1:
        v = values[0]
        return v, v, v, v
    if len(values) == 2:
        v_tb, v_lr = values
        return v_tb, v_lr, v_tb, v_lr
    return values[0], values[1], values[2], values[3]


def parse_scale_factor(spec: str) -> float:
    """
    Interpreta un factor o porcentaje de escala.

    Ejemplos: ``"200%"`` -> ``2.0``, ``"50%"`` -> ``0.5``, ``"2.5"`` -> ``2.5``.
    """
    text = spec.strip().replace(",", ".")
    if text.endswith("%"):
        factor = float(text[:-1].strip()) / 100.0
    else:
        factor = float(text)

    if factor <= 0:
        raise ValueError("El factor de escala debe ser mayor que cero.")
    return factor


def format_mm(points: float, decimals: int = 1) -> str:
    """Formatea una longitud en puntos PDF como milímetros legibles."""
    return f"{pt_to_mm(points):.{decimals}f} mm"


def format_dimensions_mm(width_pt: float, height_pt: float, decimals: int = 1) -> str:
    """Formatea ancho x alto en milímetros (y en cm entre paréntesis si supera 30 cm)."""
    w_mm = pt_to_mm(width_pt)
    h_mm = pt_to_mm(height_pt)
    base = f"{w_mm:.{decimals}f} × {h_mm:.{decimals}f} mm"
    if max(w_mm, h_mm) >= 300.0:
        return f"{base} ({w_mm / 10:.1f} × {h_mm / 10:.1f} cm)"
    return base
