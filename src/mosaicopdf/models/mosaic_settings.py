from dataclasses import dataclass

from mosaicopdf.models.printer_profile import PrinterProfile


@dataclass(frozen=True, slots=True)
class MosaicSettings:
    """
    Configuración utilizada para generar un mosaico.
    """

    printer_profile: PrinterProfile

    overlap_x: float = 0.0
    overlap_y: float = 0.0