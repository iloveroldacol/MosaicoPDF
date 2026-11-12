"""
Lector e inspector de documentos PDF usando PyMuPDF.
"""

from __future__ import annotations

from typing import Any

from mosaicopdf.models.document import DocumentInfo, PageInfo
from mosaicopdf.runtime import import_fitz


def _require_fitz() -> Any:
    """Importa PyMuPDF bajo demanda (incluyendo el entorno gestionado interno)."""
    return import_fitz()


class PDFReader:
    """Abre e inspecciona las dimensiones y páginas de un documento PDF."""

    def __init__(self, filename: str):
        fitz = _require_fitz()
        self.filename = filename
        self.document = fitz.open(filename)

    @property
    def page_count(self) -> int:
        return int(self.document.page_count)

    def page_info(self, page_number: int = 0) -> PageInfo:
        """Devuelve la geometría de la página indicada (base 0)."""
        if page_number < 0 or page_number >= self.page_count:
            raise IndexError(
                f"Página {page_number + 1} fuera de rango (total: {self.page_count})."
            )
        page = self.document.load_page(page_number)
        rect = page.rect
        return PageInfo(
            page_number=page_number,
            width=float(rect.width),
            height=float(rect.height),
            origin_x=float(rect.x0),
            origin_y=float(rect.y0),
        )

    def page_size(self, page_number: int = 0) -> tuple[float, float]:
        """Devuelve ``(ancho, alto)`` en puntos PDF."""
        info = self.page_info(page_number)
        return info.width, info.height

    def first_page_size(self) -> tuple[float, float]:
        return self.page_size(0)

    def document_info(self) -> DocumentInfo:
        """Devuelve un ``DocumentInfo`` completo con todas las páginas."""
        pages = tuple(self.page_info(i) for i in range(self.page_count))
        return DocumentInfo(filename=self.filename, pages=pages)

    def close(self) -> None:
        self.document.close()

    def __enter__(self) -> PDFReader:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
