"""Configuración predefinida y persistente de papeles e impresoras."""

from mosaicopdf.config.papers import LARGE_FORMAT_PAPERS, OFFICE_PAPERS, PAPERS, get_paper, parse_paper
from mosaicopdf.config.printers import BUILTIN_PRINTERS, PrinterStore, default_config_path

__all__ = [
    "BUILTIN_PRINTERS",
    "LARGE_FORMAT_PAPERS",
    "OFFICE_PAPERS",
    "PAPERS",
    "PrinterStore",
    "default_config_path",
    "get_paper",
    "parse_paper",
]
