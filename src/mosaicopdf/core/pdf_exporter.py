import fitz

from mosaicopdf.core.pdf_renderer import PDFRenderer
from mosaicopdf.models.mosaic import Mosaic


class PdfExporter:
    """
    Exporta un Mosaic a un documento PDF.
    """

    def __init__(self, source_document: fitz.Document):
        self.source_document = source_document
        self.renderer = PDFRenderer(source_document)

    def export(
        self,
        mosaic: Mosaic,
        output_filename: str,
        page_number: int = 0,
    ) -> None:

        dst = fitz.open()

        for tile in mosaic:
            page = dst.new_page(
                width=mosaic.paper.width,
                height=mosaic.paper.height,
            )

            self.renderer.render(
                page=page,
                tile=tile,
                paper=mosaic.paper,
                page_number=page_number,
            )

        dst.save(output_filename)
        dst.close()
