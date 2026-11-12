"""
Modelos que describen un documento PDF de entrada y sus páginas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageInfo:
    """Metadatos geométricos de una página individual del PDF."""

    page_number: int
    width: float
    height: float
    origin_x: float = 0.0
    origin_y: float = 0.0

    @property
    def orientation(self) -> str:
        """Orientación natural de la página."""
        return "Horizontal" if self.width >= self.height else "Vertical"


@dataclass(frozen=True, slots=True)
class DocumentInfo:
    """Resumen estructural de un documento PDF leído."""

    filename: str
    pages: tuple[PageInfo, ...]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def get_page(self, page_number: int = 0) -> PageInfo:
        if page_number < 0 or page_number >= len(self.pages):
            raise IndexError(
                f"Número de página fuera de rango: {page_number + 1} "
                f"(el documento tiene {len(self.pages)} páginas)."
            )
        return self.pages[page_number]
