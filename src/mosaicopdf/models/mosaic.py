"""
Modelo completo del mosaico calculado para una página PDF.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from mosaicopdf.models.mosaic_settings import MosaicSettings, TraversalOrder
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.scale_spec import ScaleResult
from mosaicopdf.models.tile import Tile
from mosaicopdf.utils.units import pt_to_mm


def row_label(row_index: int) -> str:
    """Convierte índice de fila (0, 1, 2...) a etiqueta tipo hoja de cálculo (A, B, ..., AA)."""
    index = row_index
    chars: list[str] = []
    while True:
        index, rem = divmod(index, 26)
        chars.append(chr(ord("A") + rem))
        if index == 0:
            break
        index -= 1
    return "".join(reversed(chars))


def tile_code(row_index: int, col_index: int) -> str:
    """Genera el código legible de montaje para un tile (ej. ``A1``, ``B3``)."""
    return f"{row_label(row_index)}{col_index + 1}"


@dataclass(frozen=True, slots=True)
class Mosaic:
    """
    Representa la división completa de una página escalada en hojas organizadas.
    """

    paper: Paper
    rows: int
    columns: int
    _tile_grid: tuple[tuple[Tile, ...], ...]
    settings: MosaicSettings
    scale_result: ScaleResult
    printable_width: float
    printable_height: float

    def get_tile(self, row: int, column: int) -> Tile:
        """Devuelve el tile ubicado en la fila y columna indicadas."""
        return self._tile_grid[row][column]

    def ordered_tiles(self, order: TraversalOrder | None = None) -> list[Tile]:
        """Devuelve los tiles en el orden de impresión configurado."""
        effective_order = order or self.settings.traversal_order

        if effective_order == "row-major":
            return [tile for row in self._tile_grid for tile in row]

        if effective_order == "col-major":
            return [
                self._tile_grid[r][c]
                for c in range(self.columns)
                for r in range(self.rows)
            ]

        if effective_order == "snake":
            result: list[Tile] = []
            for r, row in enumerate(self._tile_grid):
                result.extend(row if r % 2 == 0 else reversed(row))
            return result

        raise ValueError(f"Orden de recorrido no válido: '{effective_order}'.")

    def __iter__(self) -> Iterator[Tile]:
        """Recorre los tiles según el orden de impresión configurado."""
        return iter(self.ordered_tiles())

    def __len__(self) -> int:
        """Devuelve el número total de hojas del mosaico."""
        return self.rows * self.columns

    def to_dict(self) -> dict[str, Any]:
        """Serializa el mapa completo de ensamblaje a formato JSON-friendly (en mm)."""
        ordered = self.ordered_tiles()
        return {
            "paper": {
                "name": self.paper.name,
                "width_mm": round(pt_to_mm(self.paper.width), 2),
                "height_mm": round(pt_to_mm(self.paper.height), 2),
                "orientation": "landscape" if self.paper.is_landscape else "portrait",
            },
            "printer_profile": self.settings.printer_profile.to_dict(),
            "scale": {
                "factor": round(self.scale_result.scale_factor, 6),
                "percentage": round(self.scale_result.percentage, 2),
                "source_mm": [
                    round(pt_to_mm(self.scale_result.source_width), 2),
                    round(pt_to_mm(self.scale_result.source_height), 2),
                ],
                "virtual_mm": [
                    round(pt_to_mm(self.scale_result.virtual_width), 2),
                    round(pt_to_mm(self.scale_result.virtual_height), 2),
                ],
                "description": self.scale_result.description,
            },
            "grid": {
                "rows": self.rows,
                "columns": self.columns,
                "total_sheets": len(self),
                "overlap_x_mm": round(pt_to_mm(self.settings.overlap_x), 2),
                "overlap_y_mm": round(pt_to_mm(self.settings.overlap_y), 2),
                "alignment": self.settings.alignment,
                "traversal_order": self.settings.traversal_order,
            },
            "tiles": [
                {
                    "page_in_output": idx + 1,
                    "code": tile.code,
                    "row": tile.row + 1,
                    "column": tile.column + 1,
                    "x_mm": round(pt_to_mm(tile.x), 2),
                    "y_mm": round(pt_to_mm(tile.y), 2),
                    "width_mm": round(pt_to_mm(tile.width), 2),
                    "height_mm": round(pt_to_mm(tile.height), 2),
                    "overlap_right_mm": round(pt_to_mm(tile.overlap_right), 2),
                    "overlap_bottom_mm": round(pt_to_mm(tile.overlap_bottom), 2),
                    "neighbors": {
                        "right": tile.neighbor_right,
                        "bottom": tile.neighbor_bottom,
                        "left": tile.neighbor_left,
                        "top": tile.neighbor_top,
                    },
                }
                for idx, tile in enumerate(ordered)
            ],
        }
