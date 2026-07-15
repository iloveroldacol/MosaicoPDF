import math

from mosaicopdf.models.mosaic import Mosaic
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.tile import Tile


class MosaicBuilder:
    """
    Construye un objeto Mosaic a partir del tamaño de una página PDF
    y del formato de papel seleccionado.
    """

    def __init__(
        self,
        page_width: float,
        page_height: float,
        paper: Paper,
    ):
        self.page_width = page_width
        self.page_height = page_height
        self.paper = paper

    def build(self) -> Mosaic:
        """
        Calcula el mosaico necesario para cubrir completamente
        la página PDF, ajustando dinámicamente el tamaño de los tiles periféricos.
        """

        usable_width = self.paper.printable_width
        usable_height = self.paper.printable_height

        columns = math.ceil(self.page_width / usable_width)
        rows = math.ceil(self.page_height / usable_height)

        tile_grid: list[list[Tile]] = []

        for row in range(rows):
            tile_row: list[Tile] = []

            for column in range(columns):
                # Calcular la posición de inicio del tile
                tile_x = column * usable_width
                tile_y = row * usable_height

                # CORRECCIÓN: El ancho y alto no pueden ser fijos.
                # Si es la última columna o fila, deben medir únicamente el remanente real del plano.
                tile_width = min(usable_width, self.page_width - tile_x)
                tile_height = min(usable_height, self.page_height - tile_y)

                tile = Tile(
                    row=row,
                    column=column,
                    x=tile_x,
                    y=tile_y,
                    width=tile_width,
                    height=tile_height,
                )

                tile_row.append(tile)

            tile_grid.append(tile_row)

        return Mosaic(
            paper=self.paper,
            rows=rows,
            columns=columns,
            _tile_grid=tile_grid,
        )
