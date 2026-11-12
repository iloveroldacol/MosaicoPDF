"""
Modelos para la especificación y resultado del escalado vectorial previo al mosaico.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScaleMode = Literal[
    "original",
    "factor",
    "target_size",
    "target_width",
    "target_height",
    "grid",
]
FitMode = Literal["contain", "cover"]


@dataclass(frozen=True, slots=True)
class ScaleSpec:
    """
    Define cómo debe transformarse el tamaño del PDF original antes de dividirlo.

    Permite tanto reducir planos grandes como el efecto inverso: ampliar un
    diseño pequeño (Carta/Oficio/A4) a un gran formato o cuadrícula mural.
    """

    mode: ScaleMode = "original"
    factor: float = 1.0
    target_width: float | None = None
    target_height: float | None = None
    fit_mode: FitMode = "contain"
    auto_rotate_target: bool = True
    grid_columns: int | None = None
    grid_rows: int | None = None


@dataclass(frozen=True, slots=True)
class ScaleResult:
    """Resultado numérico del cálculo de escala sobre una página concreta."""

    source_width: float
    source_height: float
    virtual_width: float
    virtual_height: float
    scale_factor: float
    description: str

    @property
    def percentage(self) -> float:
        return self.scale_factor * 100.0
