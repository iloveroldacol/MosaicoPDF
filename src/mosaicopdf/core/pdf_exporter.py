"""
Exportador de mosaicos a PDF vectorial y metadatos JSON de ensamblaje.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mosaicopdf.core.pdf_reader import _require_fitz
from mosaicopdf.core.pdf_renderer import PDFRenderer
from mosaicopdf.models.mosaic import Mosaic


class PdfExporter:
    """Exporta uno o varios mosaicos a un documento PDF y opcionalmente a JSON."""

    def __init__(
        self,
        source_document: Any,
        renderer: PDFRenderer | None = None,
    ):
        self.source_document = source_document
        self.renderer = renderer or PDFRenderer(source_document)

    def export(
        self,
        mosaic: Mosaic,
        output_filename: str | Path,
        page_number: int = 0,
        source_origin: tuple[float, float] = (0.0, 0.0),
        source_filename: str = "",
    ) -> None:
        """Exporta un único mosaico a un PDF."""
        self.export_many(
            items=[(page_number, mosaic, source_origin)],
            output_filename=output_filename,
            source_filename=source_filename,
        )

    def export_many(
        self,
        items: list[tuple[int, Mosaic, tuple[float, float]]],
        output_filename: str | Path,
        source_filename: str = "",
    ) -> None:
        """Exporta una lista de ``(page_number, Mosaic, source_origin)`` a un único PDF."""
        fitz = _require_fitz()
        out_path = Path(output_filename)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        dst = fitz.open()
        try:
            for page_number, mosaic, source_origin in items:
                if mosaic.settings.cover_map:
                    cover_page = dst.new_page(
                        width=mosaic.paper.width,
                        height=mosaic.paper.height,
                    )
                    self.renderer.guide_drawer.draw_cover_map_page(
                        fitz_mod=fitz,
                        page=cover_page,
                        mosaic=mosaic,
                        source_document=self.source_document,
                        source_page_number=page_number,
                        source_filename=source_filename or str(out_path.name),
                    )

                for idx, tile in enumerate(mosaic):
                    page = dst.new_page(
                        width=mosaic.paper.width,
                        height=mosaic.paper.height,
                    )
                    self.renderer.render(
                        page=page,
                        tile=tile,
                        mosaic=mosaic,
                        page_number=page_number,
                        page_index=idx,
                        source_origin=source_origin,
                    )

            dst.save(str(out_path))
        finally:
            dst.close()

    @staticmethod
    def export_assembly_json(
        items: list[tuple[int, Mosaic]],
        json_filename: str | Path,
        source_filename: str,
        output_pdf: str,
    ) -> None:
        """Exporta el mapa completo de ensamblaje en formato JSON."""
        path = Path(json_filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "mosaicopdf_version": "2.0.0",
            "source_file": source_filename,
            "output_pdf": output_pdf,
            "pages": [
                {
                    "source_page": page_number + 1,
                    "mosaic": mosaic.to_dict(),
                }
                for page_number, mosaic in items
            ],
        }
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
