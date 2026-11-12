"""
Motor matemático de cálculo de mosaico con soporte de márgenes, solapas,
orientación automática, alineación y referencias entre piezas vecinas.
"""

from __future__ import annotations

import math

from mosaicopdf.models.mosaic import Mosaic, tile_code
from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.paper import Paper, PaperOrientation
from mosaicopdf.models.scale_spec import ScaleResult
from mosaicopdf.models.tile import Tile

# Tolerancia para evitar columnas o filas fantasma por redondeo mm <-> pt
_EPS = 1e-4


class MosaicBuilder:
    """
    Construye un ``Mosaic`` exacto a partir de las dimensiones virtuales (ya escaladas),
    el papel físico y la configuración de impresora/solapas.
    """

    def __init__(
        self,
        page_width: float,
        page_height: float,
        paper: Paper,
        settings: MosaicSettings,
        scale_result: ScaleResult | None = None,
    ):
        if page_width <= 0 or page_height <= 0:
            raise ValueError("Las dimensiones del plano deben ser mayores que cero.")

        self.page_width = page_width
        self.page_height = page_height
        self.paper = paper
        self.settings = settings
        self.scale_result = scale_result or ScaleResult(
            source_width=page_width,
            source_height=page_height,
            virtual_width=page_width,
            virtual_height=page_height,
            scale_factor=1.0,
            description="Escala original 1:1 (100%)",
        )

    def build(self) -> Mosaic:
        """
        Calcula el mosaico eligiendo la orientación óptima si se configuró ``auto``.
        """
        if self.settings.orientation == "auto":
            portrait = self._build_for_orientation("portrait")
            landscape = self._build_for_orientation("landscape")
            return self._choose_better_mosaic(portrait, landscape)

        return self._build_for_orientation(self.settings.orientation)

    def _choose_better_mosaic(self, first: Mosaic, second: Mosaic) -> Mosaic:
        """Elige el mosaico con menor cantidad de hojas (y menor área desperdiciada)."""
        if len(first) != len(second):
            return first if len(first) < len(second) else second

        waste_first = (
            len(first) * first.printable_width * first.printable_height
            - self.page_width * self.page_height
        )
        waste_second = (
            len(second) * second.printable_width * second.printable_height
            - self.page_width * self.page_height
        )
        return first if waste_first <= waste_second else second

    def _build_for_orientation(self, orientation: PaperOrientation) -> Mosaic:
        oriented_paper = self.paper.oriented(orientation)
        printable_w = self.settings.printer_profile.printable_width(oriented_paper)
        printable_h = self.settings.printer_profile.printable_height(oriented_paper)

        overlap_x = self.settings.overlap_x
        overlap_y = self.settings.overlap_y

        step_x = printable_w - overlap_x
        step_y = printable_h - overlap_y

        if step_x <= _EPS or step_y <= _EPS:
            raise ValueError(
                "La solapa no puede ser mayor o igual al área imprimible útil del papel."
            )

        columns = (
            1
            if self.page_width <= printable_w + _EPS
            else 1 + math.ceil((self.page_width - printable_w - _EPS) / step_x)
        )
        rows = (
            1
            if self.page_height <= printable_h + _EPS
            else 1 + math.ceil((self.page_height - printable_h - _EPS) / step_y)
        )

        total_grid_w = printable_w + (columns - 1) * step_x
        total_grid_h = printable_h + (rows - 1) * step_y

        if self.settings.alignment == "center":
            art_x0 = max(0.0, (total_grid_w - self.page_width) / 2.0)
            art_y0 = max(0.0, (total_grid_h - self.page_height) / 2.0)
        else:
            art_x0 = 0.0
            art_y0 = 0.0

        art_x1 = art_x0 + self.page_width
        art_y1 = art_y0 + self.page_height

        tile_grid: list[tuple[Tile, ...]] = []

        for row in range(rows):
            win_y0 = row * step_y
            win_y1 = win_y0 + printable_h
            clip_y0 = max(art_y0, win_y0)
            clip_y1 = min(art_y1, win_y1)
            src_y = clip_y0 - art_y0
            tile_h = max(0.0, clip_y1 - clip_y0)
            dest_offset_y = clip_y0 - win_y0

            next_win_y0 = (row + 1) * step_y
            bottom_overlap = (
                max(0.0, clip_y1 - next_win_y0) if row < rows - 1 else 0.0
            )

            row_tiles: list[Tile] = []
            for column in range(columns):
                win_x0 = column * step_x
                win_x1 = win_x0 + printable_w
                clip_x0 = max(art_x0, win_x0)
                clip_x1 = min(art_x1, win_x1)
                src_x = clip_x0 - art_x0
                tile_w = max(0.0, clip_x1 - clip_x0)
                dest_offset_x = clip_x0 - win_x0

                next_win_x0 = (column + 1) * step_x
                right_overlap = (
                    max(0.0, clip_x1 - next_win_x0) if column < columns - 1 else 0.0
                )

                code = tile_code(row, column)
                tile = Tile(
                    row=row,
                    column=column,
                    code=code,
                    x=src_x,
                    y=src_y,
                    width=tile_w,
                    height=tile_h,
                    dest_offset_x=dest_offset_x,
                    dest_offset_y=dest_offset_y,
                    overlap_right=right_overlap,
                    overlap_bottom=bottom_overlap,
                    neighbor_right=(
                        tile_code(row, column + 1) if column < columns - 1 else None
                    ),
                    neighbor_bottom=(
                        tile_code(row + 1, column) if row < rows - 1 else None
                    ),
                    neighbor_left=tile_code(row, column - 1) if column > 0 else None,
                    neighbor_top=tile_code(row - 1, column) if row > 0 else None,
                )
                row_tiles.append(tile)

            tile_grid.append(tuple(row_tiles))

        return Mosaic(
            paper=oriented_paper,
            rows=rows,
            columns=columns,
            _tile_grid=tuple(tile_grid),
            settings=self.settings,
            scale_result=self.scale_result,
            printable_width=printable_w,
            printable_height=printable_h,
        )
