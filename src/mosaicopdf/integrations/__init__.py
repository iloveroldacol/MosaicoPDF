"""Integraciones externas de MosaicoPDF (Inkscape y menús contextuales Linux)."""

from mosaicopdf.integrations.installer import (
    InstallReport,
    detect_inkscape_extensions_dirs,
    install_inkscape_extension,
    install_linux_rightclick,
)

__all__ = [
    "InstallReport",
    "detect_inkscape_extensions_dirs",
    "install_inkscape_extension",
    "install_linux_rightclick",
]
