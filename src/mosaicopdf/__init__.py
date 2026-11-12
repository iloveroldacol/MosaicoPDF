"""
MosaicoPDF 2.0 - Herramienta libre y vectorial para dividir y escalar PDFs en mosaico.
"""

from mosaicopdf.config.papers import get_paper, parse_paper
from mosaicopdf.config.printers import PrinterStore
from mosaicopdf.core.mosaic_builder import MosaicBuilder
from mosaicopdf.core.pipeline import JobResult, plan_page_mosaic, run_mosaic_job
from mosaicopdf.core.scaler import ScaleCalculator
from mosaicopdf.models.mosaic import Mosaic
from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.models.scale_spec import ScaleResult, ScaleSpec

__version__ = "2.0.0"

__all__ = [
    "JobResult",
    "Mosaic",
    "MosaicBuilder",
    "MosaicSettings",
    "Paper",
    "PrinterProfile",
    "PrinterStore",
    "ScaleCalculator",
    "ScaleResult",
    "ScaleSpec",
    "__version__",
    "get_paper",
    "parse_paper",
    "plan_page_mosaic",
    "run_mosaic_job",
]
