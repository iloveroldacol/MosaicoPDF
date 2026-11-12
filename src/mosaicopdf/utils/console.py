"""
Interfaz de consola ASCII y utilidades visuales de terminal para MosaicoPDF 2.0.

Usa caracteres ASCII puros para garantizar legibilidad en cualquier terminal,
con soporte opcional de color ANSI cuando la salida es interactiva.
"""

from __future__ import annotations

import os
import sys

from mosaicopdf.models.mosaic import Mosaic
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.utils.units import format_dimensions_mm, format_mm, pt_to_mm

APP_NAME = "MosaicoPDF"
APP_VERSION = "2.0.0"

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _style(text: str, code: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def banner() -> None:
    """Muestra el encabezado ASCII principal de la aplicación."""
    border = "+" + "-" * 62 + "+"
    print(border)
    print(f"|{f'  {APP_NAME} v{APP_VERSION}  -  Motor Vectorial de Mosaicos PDF':<62}|")
    print(f"|{'  Arquitectura | Muralismo | Impresion en Gran Formato':<62}|")
    print(border)
    print()


def section(title: str) -> None:
    """Imprime un separador de sección legible."""
    print()
    print(f"=== {title} " + "=" * max(4, 58 - len(title)))


def blank() -> None:
    print()


def info(message: str) -> None:
    print(f"{_style('[INFO]', '36')} {message}")


def ok(message: str) -> None:
    print(f"{_style('[ OK ]', '32')} {message}")


def warning(message: str) -> None:
    print(f"{_style('[WARN]', '33')} {message}")


def error(message: str) -> None:
    print(f"{_style('[ERR ]', '31')} {message}")


def render_ascii_mosaic(mosaic: Mosaic) -> str:
    """
    Construye un diagrama ASCII detallado del mosaico con códigos de pieza,
    orden de impresión e indicadores de solapa entre hojas vecinas.
    """
    ordered = mosaic.ordered_tiles()
    order_map = {tile.code: idx + 1 for idx, tile in enumerate(ordered)}

    has_ox = mosaic.settings.overlap_x > 0.5
    has_oy = mosaic.settings.overlap_y > 0.5

    cell_w = 13
    lines: list[str] = []

    top_border = "+" + ("-" * cell_w + "+") * mosaic.columns
    lines.append(top_border)

    for r in range(mosaic.rows):
        row_top = "|"
        row_mid = "|"
        for c in range(mosaic.columns):
            tile = mosaic.get_tile(r, c)
            num = order_map[tile.code]
            label = f"{tile.code} (#{num})"
            dim = f"{pt_to_mm(tile.width):.0f}x{pt_to_mm(tile.height):.0f}"
            right_tag = ":" if (has_ox and tile.overlap_right > 0.5) else "|"
            row_top += label.center(cell_w) + right_tag
            row_mid += dim.center(cell_w) + right_tag

        lines.append(row_top)
        lines.append(row_mid)

        if r < mosaic.rows - 1 and has_oy:
            sep = "+" + ("~" * cell_w + "+") * mosaic.columns
            lines.append(sep)
        else:
            lines.append(top_border)

    legend_parts = ["[#n] Orden de impresion", "mm x mm por hoja"]
    if has_ox or has_oy:
        legend_parts.append("':' / '~' = Solapa de pegado")
    lines.append("Leyenda: " + " | ".join(legend_parts))
    return "\n".join(lines)


def print_ascii_mosaic(mosaic: Mosaic) -> None:
    """Imprime el diagrama ASCII del mosaico en consola."""
    section("MAPA DEL MOSAICO (ASCII)")
    print(render_ascii_mosaic(mosaic))


def print_mosaic_summary(
    mosaic: Mosaic,
    input_file: str,
    output_file: str | None = None,
    page_number: int = 1,
) -> None:
    """Muestra una ficha técnica completa del mosaico calculado."""
    section(f"RESUMEN TECNICO (Pagina origen #{page_number})")
    orient_label = "Horizontal" if mosaic.paper.is_landscape else "Vertical"
    profile = mosaic.settings.printer_profile
    margins_mm = (
        f"Sup {pt_to_mm(profile.margin_top):.1f} / "
        f"Der {pt_to_mm(profile.margin_right):.1f} / "
        f"Inf {pt_to_mm(profile.margin_bottom):.1f} / "
        f"Izq {pt_to_mm(profile.margin_left):.1f} mm"
    )

    rows_data = [
        ("Archivo origen", input_file),
        ("Archivo salida", output_file or "(simulacion sin exportar)"),
        ("Tamano original", format_dimensions_mm(mosaic.scale_result.source_width, mosaic.scale_result.source_height)),
        ("Escala aplicada", f"{mosaic.scale_result.percentage:.1f}% ({mosaic.scale_result.description})"),
        ("Tamano final", format_dimensions_mm(mosaic.scale_result.virtual_width, mosaic.scale_result.virtual_height)),
        ("Papel / Orient.", f"{mosaic.paper.name} ({orient_label}) [{format_dimensions_mm(mosaic.paper.width, mosaic.paper.height)}]"),
        ("Perfil impresora", f"{profile.name} ({margins_mm})"),
        ("Area util hoja", format_dimensions_mm(mosaic.printable_width, mosaic.printable_height)),
        ("Solapas", f"X={format_mm(mosaic.settings.overlap_x)} | Y={format_mm(mosaic.settings.overlap_y)}"),
        ("Organizacion", f"Alineacion={mosaic.settings.alignment} | Orden={mosaic.settings.traversal_order}"),
        ("Marcas / Guias", f"Corte={'Si' if mosaic.settings.cut_marks else 'No'} | Armado={'Si' if mosaic.settings.assembly_guides else 'No'} | Mapa={'Si' if mosaic.settings.cover_map else 'No'}"),
        ("Cuadricula", f"{mosaic.rows} filas x {mosaic.columns} columnas = {len(mosaic)} hojas"),
    ]
    for key, val in rows_data:
        print(f"  {key:<18}: {val}")
    blank()


def print_printer_profiles(profiles: dict[str, PrinterProfile]) -> None:
    """Imprime una tabla ASCII con los perfiles de impresora disponibles."""
    section("PERFILES DE IMPRESORA")
    header_line = f"  {'NOMBRE':<16} {'SUP':>6} {'DER':>6} {'INF':>6} {'IZQ':>6}  DESCRIPCION"
    print(header_line)
    print("  " + "-" * 72)
    for prof in profiles.values():
        print(
            f"  {prof.name:<16} "
            f"{pt_to_mm(prof.margin_top):>5.1f}  "
            f"{pt_to_mm(prof.margin_right):>5.1f}  "
            f"{pt_to_mm(prof.margin_bottom):>5.1f}  "
            f"{pt_to_mm(prof.margin_left):>5.1f}  "
            f"{prof.description}"
        )
    blank()
