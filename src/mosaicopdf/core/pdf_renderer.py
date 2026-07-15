import fitz

from mosaicopdf.models.paper import Paper
from mosaicopdf.models.tile import Tile


class PDFRenderer:
    def __init__(self, source_document: fitz.Document):
        self.source_document = source_document

    def render(
        self,
        page: fitz.Page,
        tile: Tile,
        paper: Paper,
        page_number: int = 0,
    ) -> None:
        """
        Renderiza un fragmento del PDF original manteniendo la escala 1:1.
        """
        clip = fitz.Rect(
            tile.x,
            tile.y,
            tile.x + tile.width,
            tile.y + tile.height,
        )

        destino = fitz.Rect(
            0,
            0,
            tile.width,
            tile.height,
        )

        page.show_pdf_page(
            destino,
            self.source_document,
            page_number,
            clip=clip,
        )
