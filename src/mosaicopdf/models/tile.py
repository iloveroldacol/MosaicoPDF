from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tile:
    """
    Representa una hoja del mosaico.
    """

    row: int
    column: int

    x: float
    y: float

    width: float
    height: float