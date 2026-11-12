"""
Modelo de una hoja individual (tile) dentro de la cuadrícula del mosaico.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tile:
    """
    Representa una hoja del mosaico en coordenadas virtuales escaladas (puntos PDF).

    Attributes
    ----------
    row, column : int
        Índices base 0 dentro de la matriz del mosaico.
    code : str
        Identificador legible de montaje (ej. ``"A1"``, ``"B2"``).
    x, y : float
        Origen del recorte dentro del plano virtual escalado.
    width, height : float
        Ancho y alto del recorte capturado en esta hoja (incluye solapas si aplica).
    dest_offset_x, dest_offset_y : float
        Desplazamiento dentro del área imprimible (usado al centrar murales).
    overlap_right, overlap_bottom : float
        Ancho de la franja de solapa derecha o inferior compartida con la hoja vecina.
    neighbor_right, neighbor_bottom, neighbor_left, neighbor_top : str | None
        Códigos de las hojas vecinas para rotular las guías de armado.
    """

    row: int
    column: int
    code: str

    x: float
    y: float
    width: float
    height: float

    dest_offset_x: float = 0.0
    dest_offset_y: float = 0.0

    overlap_right: float = 0.0
    overlap_bottom: float = 0.0

    neighbor_right: str | None = None
    neighbor_bottom: str | None = None
    neighbor_left: str | None = None
    neighbor_top: str | None = None

    @property
    def net_width(self) -> float:
        """Ancho útil sin contar la solapa derecha."""
        return max(0.0, self.width - self.overlap_right)

    @property
    def net_height(self) -> float:
        """Alto útil sin contar la solapa inferior."""
        return max(0.0, self.height - self.overlap_bottom)
