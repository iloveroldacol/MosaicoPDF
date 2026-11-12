"""
Configuración completa para calcular, organizar y renderizar un mosaico.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mosaicopdf.models.printer_profile import PrinterProfile

OrientationMode = Literal["auto", "portrait", "landscape"]
AlignmentMode = Literal["top-left", "center"]
TraversalOrder = Literal["row-major", "col-major", "snake"]


@dataclass(frozen=True, slots=True)
class MosaicSettings:
    """
    Parámetros de diseño del mosaico, solapas, márgenes y guías de armado.
    """

    printer_profile: PrinterProfile
    overlap_x: float = 0.0
    overlap_y: float = 0.0
    orientation: OrientationMode = "auto"
    alignment: AlignmentMode = "top-left"
    traversal_order: TraversalOrder = "row-major"
    cut_marks: bool = True
    assembly_guides: bool = True
    cover_map: bool = False

    def __post_init__(self) -> None:
        if self.overlap_x < 0 or self.overlap_y < 0:
            raise ValueError("Las solapas (overlap) no pueden ser negativas.")
