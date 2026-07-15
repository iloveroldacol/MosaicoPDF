from dataclasses import dataclass

from mosaicopdf.models.paper import Paper


@dataclass(frozen=True, slots=True)
class PrinterProfile:
    """
    Describe las capacidades de impresión de una impresora para un formato
    de papel determinado.
    """

    name: str
    paper: Paper

    margin_left: float
    margin_right: float
    margin_top: float
    margin_bottom: float

    @property
    def printable_width(self) -> float:
        return self.paper.width - self.margin_left - self.margin_right

    @property
    def printable_height(self) -> float:
        return self.paper.height - self.margin_top - self.margin_bottom