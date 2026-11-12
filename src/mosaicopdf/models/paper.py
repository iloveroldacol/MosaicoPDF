"""
Modelo de formato de papel físico en puntos PDF.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PaperOrientation = Literal["portrait", "landscape"]


@dataclass(frozen=True, slots=True)
class Paper:
    """
    Representa un formato físico de papel en puntos PDF (1 pt = 1/72").
    """

    name: str
    width: float
    height: float
    printable_width: float | None = None
    printable_height: float | None = None

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Las dimensiones del papel deben ser mayores que cero.")
        if self.printable_width is None:
            object.__setattr__(self, "printable_width", self.width)
        if self.printable_height is None:
            object.__setattr__(self, "printable_height", self.height)

    @property
    def is_landscape(self) -> bool:
        return self.width > self.height

    def oriented(self, orientation: PaperOrientation) -> Paper:
        """Devuelve el papel orientado en vertical (portrait) u horizontal (landscape)."""
        if orientation == "portrait":
            if self.width <= self.height:
                return self
            return Paper(
                name=self.name,
                width=self.height,
                height=self.width,
                printable_width=self.printable_height,
                printable_height=self.printable_width,
            )
        if orientation == "landscape":
            if self.width >= self.height:
                return self
            return Paper(
                name=self.name,
                width=self.height,
                height=self.width,
                printable_width=self.printable_height,
                printable_height=self.printable_width,
            )
        raise ValueError(f"Orientación de papel no válida: '{orientation}'.")
