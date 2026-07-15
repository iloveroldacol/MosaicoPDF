"""
Definición de los formatos de papel soportados por MosaicoPDF.

Todas las dimensiones están expresadas en puntos PDF.
(1 pulgada = 72 puntos)
"""

from mosaicopdf.models.paper import Paper


# ----------------------------------------------------------------------
# Formatos de papel
# ----------------------------------------------------------------------

PAPERS = {
    "carta": Paper(
        name="Carta",
        width=612,
        height=792,
        printable_width=588,
        printable_height=768,
    ),
    "oficio": Paper(
        name="Oficio",
        width=612,
        height=936,
        printable_width=588,
        printable_height=912,
    ),
    "a4": Paper(
        name="A4",
        width=595,
        height=842,
        printable_width=571,
        printable_height=818,
    ),
}


def get_paper(name: str) -> Paper:
    """
    Devuelve el formato de papel solicitado.

    Parameters
    ----------
    name : str
        Nombre del formato (carta, oficio o a4).

    Returns
    -------
    Paper
        Objeto Paper correspondiente.

    Raises
    ------
    ValueError
        Si el formato solicitado no existe.
    """
    key = name.strip().lower()

    if key not in PAPERS:
        raise ValueError(
            f"Formato de papel no válido: '{name}'. "
            "Opciones disponibles: carta, oficio, a4."
        )

    return PAPERS[key]