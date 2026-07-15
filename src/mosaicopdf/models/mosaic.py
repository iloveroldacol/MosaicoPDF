from dataclasses import dataclass
from collections.abc import Iterator

from mosaicopdf.models.paper import Paper
from mosaicopdf.models.tile import Tile


@dataclass(frozen=True, slots=True)
class Mosaic:
    """
    Representa la división completa de una página en un conjunto organizado
    de tiles.

    Un Mosaic es el resultado del algoritmo de cálculo y contiene toda la
    información necesaria para recorrer y exportar el mosaico.
    """

    paper: Paper
    rows: int
    columns: int
    _tile_grid: list[list[Tile]]

    def get_tile(self, row: int, column: int) -> Tile:
        """
        Devuelve el tile ubicado en la fila y columna indicadas.
        """
        return self._tile_grid[row][column]

    def __iter__(self) -> Iterator[Tile]:
        """
        Recorre todos los tiles del mosaico por filas.
        """
        for row in self._tile_grid:
            yield from row

    def __len__(self) -> int:
        """
        Devuelve el número total de hojas del mosaico.
        """
        return self.rows * self.columns