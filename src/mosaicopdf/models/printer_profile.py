"""
Modelo de perfil de impresora con márgenes físicos configurables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mosaicopdf.models.paper import Paper
from mosaicopdf.utils.units import mm_to_pt, pt_to_mm


@dataclass(frozen=True, slots=True)
class PrinterProfile:
    """
    Describe los márgenes físicos no imprimibles de una impresora (en puntos PDF).
    """

    name: str
    margin_top: float = 0.0
    margin_right: float = 0.0
    margin_bottom: float = 0.0
    margin_left: float = 0.0
    description: str = ""

    def __post_init__(self) -> None:
        margins = (
            self.margin_top,
            self.margin_right,
            self.margin_bottom,
            self.margin_left,
        )
        if any(m < 0 for m in margins):
            raise ValueError("Los márgenes de impresora no pueden ser negativos.")

    def printable_width(self, paper: Paper) -> float:
        """Ancho útil imprimible al aplicar este perfil sobre un papel."""
        width = paper.width - self.margin_left - self.margin_right
        if width <= 0:
            raise ValueError(
                f"Los márgenes horizontales superan el ancho del papel '{paper.name}'."
            )
        return width

    def printable_height(self, paper: Paper) -> float:
        """Alto útil imprimible al aplicar este perfil sobre un papel."""
        height = paper.height - self.margin_top - self.margin_bottom
        if height <= 0:
            raise ValueError(
                f"Los márgenes verticales superan el alto del papel '{paper.name}'."
            )
        return height

    def with_margins(
        self,
        top: float,
        right: float,
        bottom: float,
        left: float,
        name: str | None = None,
    ) -> PrinterProfile:
        """Devuelve una copia del perfil con nuevos márgenes en puntos PDF."""
        return PrinterProfile(
            name=name or self.name,
            margin_top=top,
            margin_right=right,
            margin_bottom=bottom,
            margin_left=left,
            description=self.description,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializa el perfil guardando sus márgenes en milímetros."""
        return {
            "name": self.name,
            "description": self.description,
            "margins_mm": {
                "top": round(pt_to_mm(self.margin_top), 3),
                "right": round(pt_to_mm(self.margin_right), 3),
                "bottom": round(pt_to_mm(self.margin_bottom), 3),
                "left": round(pt_to_mm(self.margin_left), 3),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PrinterProfile:
        """Reconstruye un perfil desde un diccionario JSON (márgenes en mm)."""
        margins = data.get("margins_mm", {})
        return cls(
            name=str(data["name"]),
            description=str(data.get("description", "")),
            margin_top=mm_to_pt(float(margins.get("top", 0.0))),
            margin_right=mm_to_pt(float(margins.get("right", 0.0))),
            margin_bottom=mm_to_pt(float(margins.get("bottom", 0.0))),
            margin_left=mm_to_pt(float(margins.get("left", 0.0))),
        )
