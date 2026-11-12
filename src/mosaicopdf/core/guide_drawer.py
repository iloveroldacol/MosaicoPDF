"""
Dibujo vectorial de marcas de corte, solapas con referencia a piezas vecinas
y página mapa de ensamblaje para arquitectura y muralismo.
"""

from __future__ import annotations

from typing import Any

from mosaicopdf.models.mosaic import Mosaic
from mosaicopdf.models.tile import Tile
from mosaicopdf.utils.units import format_dimensions_mm, mm_to_pt, pt_to_mm


class GuideDrawer:
    """Dibuja elementos vectoriales de corte y montaje sobre páginas PyMuPDF."""

    _CROP_COLOR = (0.25, 0.25, 0.25)
    _BORDER_COLOR = (0.55, 0.55, 0.55)
    _OVERLAP_COLOR = (0.12, 0.42, 0.72)
    _TEXT_COLOR = (0.15, 0.15, 0.15)
    _MUTED_TEXT_COLOR = (0.35, 0.35, 0.35)

    def draw_tile_guides(
        self,
        fitz_mod: Any,
        page: Any,
        tile: Tile,
        mosaic: Mosaic,
        dest_rect: Any,
        page_index: int,
    ) -> None:
        """Dibuja marcas de corte y guías de armado configuradas en el mosaico."""
        if tile.width <= 0 or tile.height <= 0:
            return

        if mosaic.settings.cut_marks:
            self._draw_cut_marks(fitz_mod, page, tile, dest_rect)

        if mosaic.settings.assembly_guides:
            self._draw_overlap_guides(fitz_mod, page, tile, dest_rect)
            self._draw_piece_header(fitz_mod, page, tile, mosaic, dest_rect, page_index)

    def _draw_cut_marks(
        self,
        fitz_mod: Any,
        page: Any,
        tile: Tile,
        dest_rect: Any,
    ) -> None:
        """Dibuja líneas de corte en las esquinas y contorno discontinuo del recorte."""
        shape = page.new_shape()
        tick = mm_to_pt(4.0)
        x0, y0, x1, y1 = dest_rect.x0, dest_rect.y0, dest_rect.x1, dest_rect.y1

        # Contorno discontinuo exterior del recorte útil + solapa
        shape.draw_rect(dest_rect)
        shape.finish(
            color=self._BORDER_COLOR,
            width=0.35,
            dashes="[2 2]",
        )

        # Marcas de esquina en L fuera o sobre el borde del rectángulo
        corners = [
            ((x0 - tick, y0), (x0, y0), (x0, y0 - tick)),
            ((x1 + tick, y0), (x1, y0), (x1, y0 - tick)),
            ((x0 - tick, y1), (x0, y1), (x0, y1 + tick)),
            ((x1 + tick, y1), (x1, y1), (x1, y1 + tick)),
        ]
        for p1, corner, p2 in corners:
            shape.draw_line(
                fitz_mod.Point(*self._clamp_point(p1, page.rect)),
                fitz_mod.Point(*self._clamp_point(corner, page.rect)),
            )
            shape.draw_line(
                fitz_mod.Point(*self._clamp_point(corner, page.rect)),
                fitz_mod.Point(*self._clamp_point(p2, page.rect)),
            )

        shape.finish(color=self._CROP_COLOR, width=0.55)
        shape.commit()

    def _draw_overlap_guides(
        self,
        fitz_mod: Any,
        page: Any,
        tile: Tile,
        dest_rect: Any,
    ) -> None:
        """Dibuja franjas de solapa identificando explícitamente la pieza contigua."""
        x0, y0, x1, y1 = dest_rect.x0, dest_rect.y0, dest_rect.x1, dest_rect.y1

        if tile.overlap_right > 0.5 and tile.neighbor_right:
            cut_x = x1 - tile.overlap_right
            flap_rect = fitz_mod.Rect(cut_x, y0, x1, y1)
            shape = page.new_shape()
            shape.draw_rect(flap_rect)
            shape.finish(
                color=None,
                fill=self._OVERLAP_COLOR,
                fill_opacity=0.07,
            )
            shape.draw_line(
                fitz_mod.Point(cut_x, y0),
                fitz_mod.Point(cut_x, y1),
            )
            shape.finish(
                color=self._OVERLAP_COLOR,
                width=0.65,
                dashes="[4 2]",
            )
            # Triángulo de registro en punto medio vertical
            mid_y = (y0 + y1) / 2.0
            tri = mm_to_pt(1.8)
            shape.draw_polyline(
                [
                    fitz_mod.Point(cut_x, mid_y - tri),
                    fitz_mod.Point(cut_x + tri, mid_y),
                    fitz_mod.Point(cut_x, mid_y + tri),
                ]
            )
            shape.finish(color=self._OVERLAP_COLOR, fill=self._OVERLAP_COLOR, closePath=True)
            shape.commit()

            overlap_mm = pt_to_mm(tile.overlap_right)
            label = (
                f"SOLAPA {overlap_mm:.1f}mm -> UNIR CON {tile.neighbor_right} "
                f"({tile.code} | {tile.neighbor_right})"
            )
            text_x = min(x1 - mm_to_pt(2.0), cut_x + tile.overlap_right * 0.65)
            text_y = max(y0 + mm_to_pt(8.0), min(y1 - mm_to_pt(8.0), mid_y + mm_to_pt(35.0)))
            if y1 - y0 >= mm_to_pt(45.0):
                page.insert_text(
                    fitz_mod.Point(text_x, text_y),
                    label,
                    fontsize=6.5,
                    fontname="helv",
                    color=self._OVERLAP_COLOR,
                    rotate=90,
                )

        if tile.overlap_bottom > 0.5 and tile.neighbor_bottom:
            cut_y = y1 - tile.overlap_bottom
            flap_rect = fitz_mod.Rect(x0, cut_y, x1, y1)
            shape = page.new_shape()
            shape.draw_rect(flap_rect)
            shape.finish(
                color=None,
                fill=self._OVERLAP_COLOR,
                fill_opacity=0.07,
            )
            shape.draw_line(
                fitz_mod.Point(x0, cut_y),
                fitz_mod.Point(x1, cut_y),
            )
            shape.finish(
                color=self._OVERLAP_COLOR,
                width=0.65,
                dashes="[4 2]",
            )
            mid_x = (x0 + x1) / 2.0
            tri = mm_to_pt(1.8)
            shape.draw_polyline(
                [
                    fitz_mod.Point(mid_x - tri, cut_y),
                    fitz_mod.Point(mid_x + tri, cut_y),
                    fitz_mod.Point(mid_x, cut_y + tri),
                ]
            )
            shape.finish(color=self._OVERLAP_COLOR, fill=self._OVERLAP_COLOR, closePath=True)
            shape.commit()

            overlap_mm = pt_to_mm(tile.overlap_bottom)
            label = (
                f"SOLAPA {overlap_mm:.1f}mm v UNIR CON {tile.neighbor_bottom} "
                f"({tile.code} / {tile.neighbor_bottom})"
            )
            text_x = max(x0 + mm_to_pt(5.0), mid_x - mm_to_pt(35.0))
            text_y = min(y1 - mm_to_pt(2.0), cut_y + tile.overlap_bottom * 0.65)
            if x1 - x0 >= mm_to_pt(45.0):
                page.insert_text(
                    fitz_mod.Point(text_x, text_y),
                    label,
                    fontsize=6.5,
                    fontname="helv",
                    color=self._OVERLAP_COLOR,
                    rotate=0,
                )

    def _draw_piece_header(
        self,
        fitz_mod: Any,
        page: Any,
        tile: Tile,
        mosaic: Mosaic,
        dest_rect: Any,
        page_index: int,
    ) -> None:
        """Rotula el código de pieza, número de hoja y sus piezas vecinas."""
        neighbors: list[str] = []
        if tile.neighbor_top:
            neighbors.append(f"Sup:{tile.neighbor_top}")
        if tile.neighbor_left:
            neighbors.append(f"Izq:{tile.neighbor_left}")
        if tile.neighbor_right:
            neighbors.append(f"Der:{tile.neighbor_right}")
        if tile.neighbor_bottom:
            neighbors.append(f"Inf:{tile.neighbor_bottom}")

        neighbor_str = " ".join(neighbors) if neighbors else "Hoja unica"
        header_text = (
            f"[{tile.code}] Hoja {page_index + 1}/{len(mosaic)} | "
            f"F{tile.row + 1}-C{tile.column + 1} | {neighbor_str} | "
            f"Escala {mosaic.scale_result.percentage:.0f}%"
        )

        margin_top = mosaic.settings.printer_profile.margin_top
        if margin_top >= mm_to_pt(4.5):
            text_y = max(mm_to_pt(3.5), dest_rect.y0 - mm_to_pt(1.6))
        else:
            text_y = min(page.rect.height - mm_to_pt(2.0), dest_rect.y0 + mm_to_pt(3.5))

        text_x = max(mm_to_pt(3.0), dest_rect.x0)
        page.insert_text(
            fitz_mod.Point(text_x, text_y),
            header_text,
            fontsize=6.5,
            fontname="helv",
            color=self._TEXT_COLOR,
        )

    def draw_cover_map_page(
        self,
        fitz_mod: Any,
        page: Any,
        mosaic: Mosaic,
        source_document: Any,
        source_page_number: int,
        source_filename: str,
    ) -> None:
        """
        Genera la página inicial de mapa visual para armar murales o planos grandes.
        """
        margin = mm_to_pt(14.0)
        page_w = page.rect.width
        page_h = page.rect.height

        # Encabezado
        page.insert_text(
            fitz_mod.Point(margin, margin + mm_to_pt(4.0)),
            f"MosaicoPDF 2.0 - Mapa de Ensamblaje ({mosaic.rows}x{mosaic.columns} = {len(mosaic)} hojas)",
            fontsize=13,
            fontname="helv",
            color=self._TEXT_COLOR,
        )

        meta_lines = [
            f"Origen: {source_filename} (pág. {source_page_number + 1})  |  "
            f"Tamaño original: {format_dimensions_mm(mosaic.scale_result.source_width, mosaic.scale_result.source_height)}",
            f"Tamaño final: {format_dimensions_mm(mosaic.scale_result.virtual_width, mosaic.scale_result.virtual_height)}  |  "
            f"Escala: {mosaic.scale_result.percentage:.1f}%",
            f"Papel: {mosaic.paper.name} ({'Horizontal' if mosaic.paper.is_landscape else 'Vertical'})  |  "
            f"Solapa: {pt_to_mm(mosaic.settings.overlap_x):.1f} x {pt_to_mm(mosaic.settings.overlap_y):.1f} mm  |  "
            f"Orden: {mosaic.settings.traversal_order}",
        ]
        y_cursor = margin + mm_to_pt(11.0)
        for line in meta_lines:
            page.insert_text(
                fitz_mod.Point(margin, y_cursor),
                line,
                fontsize=8.0,
                fontname="helv",
                color=self._MUTED_TEXT_COLOR,
            )
            y_cursor += mm_to_pt(4.5)

        # Área reservada para el diagrama vectorial
        map_top = y_cursor + mm_to_pt(4.0)
        map_bottom = page_h - margin - mm_to_pt(10.0)
        avail_w = max(mm_to_pt(40.0), page_w - 2 * margin)
        avail_h = max(mm_to_pt(40.0), map_bottom - map_top)

        vw = mosaic.scale_result.virtual_width
        vh = mosaic.scale_result.virtual_height
        preview_scale = min(avail_w / vw, avail_h / vh)
        draw_w = vw * preview_scale
        draw_h = vh * preview_scale
        ox = margin + (avail_w - draw_w) / 2.0
        oy = map_top + (avail_h - draw_h) / 2.0

        preview_rect = fitz_mod.Rect(ox, oy, ox + draw_w, oy + draw_h)
        page.show_pdf_page(preview_rect, source_document, source_page_number)

        # Superponer cuadrícula del mosaico sobre la miniatura
        ordered = mosaic.ordered_tiles()
        order_lookup = {t.code: idx + 1 for idx, t in enumerate(ordered)}

        shape = page.new_shape()
        for row in range(mosaic.rows):
            for col in range(mosaic.columns):
                tile = mosaic.get_tile(row, col)
                tx0 = ox + tile.x * preview_scale
                ty0 = oy + tile.y * preview_scale
                tx1 = ox + (tile.x + tile.width) * preview_scale
                ty1 = oy + (tile.y + tile.height) * preview_scale
                t_rect = fitz_mod.Rect(tx0, ty0, tx1, ty1)
                shape.draw_rect(t_rect)
                shape.finish(color=self._OVERLAP_COLOR, width=0.8)

                cx = (tx0 + tx1) / 2.0
                cy = (ty0 + ty1) / 2.0
                num = order_lookup[tile.code]
                page.insert_text(
                    fitz_mod.Point(max(tx0 + 2, cx - mm_to_pt(5.0)), cy + mm_to_pt(1.5)),
                    f"{tile.code} (#{num})",
                    fontsize=8.0,
                    fontname="helv",
                    color=self._OVERLAP_COLOR,
                )
        shape.commit()

        page.insert_text(
            fitz_mod.Point(margin, page_h - margin),
            "Instrucciones: recorte por las líneas discontinuas y alinee cada hoja sobre la solapa azul de la pieza contigua.",
            fontsize=8.0,
            fontname="helv",
            color=self._TEXT_COLOR,
        )

    @staticmethod
    def _clamp_point(point: tuple[float, float], rect: Any) -> tuple[float, float]:
        x = max(0.0, min(rect.width, point[0]))
        y = max(0.0, min(rect.height, point[1]))
        return x, y
