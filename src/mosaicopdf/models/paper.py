from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Paper:
    """
    Representa un formato de papel.

    Todas las dimensiones se almacenan en puntos PDF (1 pt = 1/72").
    El área imprimible corresponde al espacio útil que utilizará el
    algoritmo del mosaico.
    """

    name: str

    # Tamaño físico del papel
    width: float
    height: float

    # Área imprimible
    printable_width: float
    printable_height: float