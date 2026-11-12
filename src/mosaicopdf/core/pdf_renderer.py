"""
Renderizador vectorial de fragmentos PDF con soporte de escala, márgenes y guías.
"""

from __future__ import annotations

from typing import Any

from mosaicopdf.core.guide_drawer import GuideDrawer
from mosaicopdf.core.pdf_reader import _require_fitz
from mosaicopdf.models.mosaic import Mosaic
from mosaicopdf.models.tile import Tile


class PDFRenderer:
    """
    Renderiza cada ``Tile`` en una página destino conservando contenido vectorial.

    Al mantener exactamente la proporción ``destino = clip * scale_factor``,
    PyMuPDF embebe el fragmento como XObject vectorial sin rasterizar ni deformar.
    """

    def __init__(
        self,
        source_document: Any,
        guide_drawer: GuideDrawer | None = None,
    ):
        self.source_document = source_document
        self.guide_drawer = guide_drawer or GuideDrawer()

    def compute_rects(
        self,
        tile: Tile,
        mosaic: Mosaic,
        source_origin: tuple[float, float] = (0.0, 0.0),
    ) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
        """
        Calcula las coordenadas exactas ``(src_clip, dest_rect)`` en puntos PDF.

        Se separa este cálculo puro para permitir auditoría matemática y pruebas
        unitarias exactas independientemente de PyMuPDF.
        """
        scale = mosaic.scale_result.scale_factor
        ox, oy = source_origin

        src_x0 = ox + (tile.x / scale)
        src_y0 = oy + (tile.y / scale)
        src_x1 = ox + ((tile.x + tile.width) / scale)
        src_y1 = oy + ((tile.y + tile.height) / scale)

        profile = mosaic.settings.printer_profile
        dest_x0 = profile.margin_left + tile.dest_offset_x
        dest_y0 = profile.margin_top + tile.dest_offset_y
        dest_x1 = dest_x0 + tile.width
        dest_y1 = dest_y0 + tile.height

        return (src_x0, src_y0, src_x1, src_y1), (dest_x0, dest_y0, dest_x1, dest_y1)

    def render(
        self,
        page: Any,
        tile: Tile,
        mosaic: Mosaic,
        page_number: int = 0,
        page_index: int = 0,
        source_origin: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        """Dibuja un tile vectorial en ``page`` junto con sus marcas/guías."""
        fitz = _require_fitz()
        src_coords, dest_coords = self.compute_rects(
            tile=tile,
            mosaic=mosaic,
            source_origin=source_origin,
        )
        clip = fitz.Rect(*src_coords)
        dest_rect = fitz.Rect(*dest_coords)

        if tile.width > 0 and tile.height > 0:
            page.show_pdf_page(
                dest_rect,
                self.source_document,
                page_number,
                clip=clip,
                keep_proportion=True,
            )

        self.guide_drawer.draw_tile_guides(
            fitz_mod=fitz,
            page=page,
            tile=tile,
            mosaic=mosaic,
            dest_rect=dest_rect,
            page_index=page_index,
        )
