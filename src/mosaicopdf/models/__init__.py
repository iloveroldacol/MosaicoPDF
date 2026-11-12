"""Modelos de dominio de MosaicoPDF."""

from mosaicopdf.models.document import DocumentInfo, PageInfo
from mosaicopdf.models.mosaic import Mosaic, row_label, tile_code
from mosaicopdf.models.mosaic_settings import (
    AlignmentMode,
    MosaicSettings,
    OrientationMode,
    TraversalOrder,
)
from mosaicopdf.models.paper import Paper, PaperOrientation
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.models.scale_spec import FitMode, ScaleMode, ScaleResult, ScaleSpec
from mosaicopdf.models.tile import Tile

__all__ = [
    "AlignmentMode",
    "DocumentInfo",
    "FitMode",
    "Mosaic",
    "MosaicSettings",
    "OrientationMode",
    "PageInfo",
    "Paper",
    "PaperOrientation",
    "PrinterProfile",
    "ScaleMode",
    "ScaleResult",
    "ScaleSpec",
    "Tile",
    "TraversalOrder",
    "row_label",
    "tile_code",
]
