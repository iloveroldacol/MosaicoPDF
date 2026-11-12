"""
Definición de argumentos CLI para MosaicoPDF 2.0 (modo directo y subcomandos).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from mosaicopdf.config.papers import parse_paper
from mosaicopdf.config.printers import PrinterStore
from mosaicopdf.models.mosaic_settings import (
    AlignmentMode,
    MosaicSettings,
    OrientationMode,
    TraversalOrder,
)
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.models.scale_spec import FitMode, ScaleSpec
from mosaicopdf.utils.units import (
    parse_dimensions,
    parse_length,
    parse_margins,
    parse_scale_factor,
)

SUBCOMMANDS = {"perfiles", "papeles", "integrar", "doctor"}

_ORIENTATION_ALIASES: dict[str, OrientationMode] = {
    "auto": "auto",
    "vertical": "portrait",
    "portrait": "portrait",
    "horizontal": "landscape",
    "landscape": "landscape",
}

_ALIGNMENT_ALIASES: dict[str, AlignmentMode] = {
    "top-left": "top-left",
    "izquierda": "top-left",
    "arriba-izquierda": "top-left",
    "center": "center",
    "centrado": "center",
    "centro": "center",
}

_ORDER_ALIASES: dict[str, TraversalOrder] = {
    "row-major": "row-major",
    "filas": "row-major",
    "col-major": "col-major",
    "columnas": "col-major",
    "snake": "snake",
    "serpentina": "snake",
    "zigzag": "snake",
}

_FIT_ALIASES: dict[str, FitMode] = {
    "contain": "contain",
    "contener": "contain",
    "cover": "cover",
    "cubrir": "cover",
}


@dataclass(frozen=True, slots=True)
class ParsedDirectArgs:
    """Parámetros ya validados y convertidos listos para el motor del mosaico."""

    input_file: str | None
    interactive: bool
    paper: Paper
    settings: MosaicSettings
    scale_spec: ScaleSpec
    output_file: str | None
    page_selection: str
    export_json: bool
    dry_run: bool


def build_main_parser() -> argparse.ArgumentParser:
    """Construye el parser principal para procesar un PDF en mosaico."""
    parser = argparse.ArgumentParser(
        prog="mosaicopdf",
        description=(
            "MosaicoPDF 2.0 - Divide y escala documentos PDF vectoriales en hojas "
            "imprimibles con márgenes, solapas y guías de armado.\n\n"
            "Subcomandos disponibles:\n"
            "  mosaicopdf papeles              Lista formatos estándar y gran formato\n"
            "  mosaicopdf perfiles ...         Gestiona perfiles de impresora\n"
            "  mosaicopdf integrar ...         Instala extensión Inkscape y clic derecho\n"
            "  mosaicopdf doctor [--instalar]  Verifica o instala PyMuPDF automáticamente"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        help="Ruta del archivo PDF de entrada. Si se omite, abre el asistente ASCII.",
    )
    parser.add_argument(
        "paper_pos",
        nargs="?",
        help="Formato de papel posicional opcional (compatibilidad v1, ej. carta).",
    )
    parser.add_argument(
        "-i",
        "--interactivo",
        action="store_true",
        help="Inicia el asistente interactivo ASCII en terminal.",
    )
    parser.add_argument(
        "-p",
        "--papel",
        dest="paper_opt",
        help="Papel destino: carta, oficio, legal, a4, a3, tabloide o ANCHOxALTOmm.",
    )
    parser.add_argument(
        "--perfil",
        default="estandar",
        help="Perfil de impresora a usar (defecto: estandar).",
    )
    parser.add_argument(
        "--margen",
        "--margenes",
        dest="margins",
        help="Márgenes personalizados en mm (1, 2 o 4 valores: '8mm' o '10,8,10,8mm').",
    )
    parser.add_argument(
        "--solapa",
        help="Solapa uniforme X e Y en mm por defecto (ej. '12mm' o '1.5cm').",
    )
    parser.add_argument(
        "--solapa-x",
        help="Solapa horizontal entre columnas (ej. '15mm').",
    )
    parser.add_argument(
        "--solapa-y",
        help="Solapa vertical entre filas (ej. '15mm').",
    )
    parser.add_argument(
        "--orientacion",
        default="auto",
        choices=tuple(_ORIENTATION_ALIASES.keys()),
        help="Orientación del papel: auto (menos hojas), vertical u horizontal.",
    )
    parser.add_argument(
        "--alineacion",
        default="top-left",
        choices=tuple(_ALIGNMENT_ALIASES.keys()),
        help="Alineación del diseño en el mosaico: top-left o centrado.",
    )
    parser.add_argument(
        "--centrar",
        action="store_true",
        help="Atajo equivalente a --alineacion centrado.",
    )
    parser.add_argument(
        "--orden",
        default="row-major",
        choices=tuple(_ORDER_ALIASES.keys()),
        help="Orden de hojas: filas, columnas o serpentina.",
    )
    parser.add_argument(
        "--escala",
        help="Factor o porcentaje de escala (ej. '200%%', '50%%', '2.5').",
    )
    parser.add_argument(
        "--escalar-a",
        dest="scale_to",
        help="Efecto inverso: escalar a gran formato (ej. 'a0', 'a1', '1500x1000mm').",
    )
    parser.add_argument(
        "--ancho-objetivo",
        help="Escalar proporcionalmente al ancho indicado (ej. '1200mm').",
    )
    parser.add_argument(
        "--alto-objetivo",
        help="Escalar proporcionalmente al alto indicado (ej. '900mm').",
    )
    parser.add_argument(
        "--cuadricula",
        help="Escalar proporcionalmente para llenar COLxFIL hojas (ej. '3x2').",
    )
    parser.add_argument(
        "--ajuste",
        default="contain",
        choices=tuple(_FIT_ALIASES.keys()),
        help="Modo de ajuste con --escalar-a: contener (sin recorte) o cubrir.",
    )
    parser.add_argument(
        "--no-rotar-objetivo",
        action="store_true",
        help="No rotar el formato objetivo al usar --escalar-a.",
    )
    parser.add_argument(
        "--paginas",
        default="1",
        help="Páginas del PDF a procesar (ej. '1', '1,3-5', 'all').",
    )
    parser.add_argument(
        "--sin-marcas",
        action="store_true",
        help="Ocultar marcas de corte en esquinas y contorno.",
    )
    parser.add_argument(
        "--sin-guias",
        action="store_true",
        help="Ocultar rótulos de pieza y guías de solapa con pieza vecina.",
    )
    parser.add_argument(
        "--mapa",
        action="store_true",
        help="Añadir página inicial con el mapa visual de ensamblaje.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Generar archivo .json con coordenadas y vecinos de ensamblaje.",
    )
    parser.add_argument(
        "-o",
        "--salida",
        help="Ruta del archivo PDF de salida.",
    )
    parser.add_argument(
        "--simular",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Calcula y muestra el resumen ASCII sin escribir el PDF.",
    )
    return parser


def build_subcommand_parser() -> argparse.ArgumentParser:
    """Construye el parser para subcomandos de administración."""
    parser = argparse.ArgumentParser(prog="mosaicopdf")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # papeles
    sub.add_parser("papeles", help="Lista formatos de papel estándar y gran formato.")

    # perfiles
    p_prof = sub.add_parser("perfiles", help="Gestiona perfiles de impresora.")
    p_sub = p_prof.add_subparsers(dest="action", required=True)
    p_sub.add_parser("listar", help="Muestra los perfiles disponibles.")

    p_create = p_sub.add_parser("crear", help="Crea o actualiza un perfil.")
    p_create.add_argument("name", help="Nombre corto del perfil (ej. mi-epson).")
    p_create.add_argument(
        "--margen",
        required=True,
        help="Márgenes en mm: '8mm' o '10,8,10,8mm'.",
    )
    p_create.add_argument("--descripcion", default="", help="Descripción opcional.")

    p_del = p_sub.add_parser("eliminar", help="Elimina un perfil personalizado.")
    p_del.add_argument("name", help="Nombre del perfil a eliminar.")

    # integrar
    p_int = sub.add_parser(
        "integrar",
        help="Instala extensión de Inkscape y/o menú contextual de Linux.",
    )
    p_int.add_argument("--inkscape", action="store_true", help="Instalar en Inkscape.")
    p_int.add_argument("--linux", action="store_true", help="Instalar clic derecho Linux.")
    p_int.add_argument("--todo", action="store_true", help="Instalar todas las integraciones.")

    # doctor
    p_doc = sub.add_parser(
        "doctor",
        help="Diagnostica Python, PyMuPDF e Inkscape, e instala dependencias faltantes.",
    )
    p_doc.add_argument(
        "--instalar",
        action="store_true",
        help="Instala PyMuPDF automáticamente en el entorno interno de MosaicoPDF.",
    )

    return parser


def resolve_direct_args(
    ns: argparse.Namespace,
    store: PrinterStore | None = None,
) -> ParsedDirectArgs:
    """Convierte los argumentos crudos de CLI en modelos de dominio validados."""
    printer_store = store or PrinterStore()
    paper_raw = ns.paper_opt or ns.paper_pos or "carta"
    paper = parse_paper(paper_raw)

    profile: PrinterProfile = printer_store.get(ns.perfil)
    if ns.margins:
        top, right, bottom, left = parse_margins(ns.margins, default_unit="mm")
        profile = profile.with_margins(
            top=top,
            right=right,
            bottom=bottom,
            left=left,
            name=f"{profile.name} (personalizado)",
        )

    base_overlap = parse_length(ns.solapa, default_unit="mm") if ns.solapa else 0.0
    overlap_x = (
        parse_length(ns.solapa_x, default_unit="mm")
        if ns.solapa_x is not None
        else base_overlap
    )
    overlap_y = (
        parse_length(ns.solapa_y, default_unit="mm")
        if ns.solapa_y is not None
        else base_overlap
    )

    scale_spec = _resolve_scale_spec(ns)
    alignment = "center" if ns.centrar else _ALIGNMENT_ALIASES[ns.alineacion]
    settings = MosaicSettings(
        printer_profile=profile,
        overlap_x=overlap_x,
        overlap_y=overlap_y,
        orientation=_ORIENTATION_ALIASES[ns.orientacion],
        alignment=alignment,
        traversal_order=_ORDER_ALIASES[ns.orden],
        cut_marks=not ns.sin_marcas,
        assembly_guides=not ns.sin_guias,
        cover_map=bool(ns.mapa),
    )

    return ParsedDirectArgs(
        input_file=ns.input_file,
        interactive=bool(ns.interactivo),
        paper=paper,
        settings=settings,
        scale_spec=scale_spec,
        output_file=ns.salida,
        page_selection=ns.paginas,
        export_json=bool(ns.json),
        dry_run=bool(ns.dry_run),
    )


def _resolve_scale_spec(ns: argparse.Namespace) -> ScaleSpec:
    """Valida que no haya banderas de escala contradictorias y crea ``ScaleSpec``."""
    chosen = [
        flag
        for flag, val in (
            ("--escala", ns.escala),
            ("--escalar-a", ns.scale_to),
            ("--ancho-objetivo", ns.ancho_objetivo),
            ("--alto-objetivo", ns.alto_objetivo),
            ("--cuadricula", ns.cuadricula),
        )
        if val is not None
    ]
    if len(chosen) > 1:
        raise ValueError(
            f"Elige solo una opción de escala a la vez (usaste: {', '.join(chosen)})."
        )

    if ns.escala is not None:
        return ScaleSpec(mode="factor", factor=parse_scale_factor(ns.escala))

    if ns.scale_to is not None:
        try:
            target_paper = parse_paper(ns.scale_to)
            tw, th = target_paper.width, target_paper.height
        except ValueError:
            tw, th = parse_dimensions(ns.scale_to, default_unit="mm")
        return ScaleSpec(
            mode="target_size",
            target_width=tw,
            target_height=th,
            fit_mode=_FIT_ALIASES[ns.ajuste],
            auto_rotate_target=not ns.no_rotar_objetivo,
        )

    if ns.ancho_objetivo is not None:
        return ScaleSpec(
            mode="target_width",
            target_width=parse_length(ns.ancho_objetivo, default_unit="mm"),
        )

    if ns.alto_objetivo is not None:
        return ScaleSpec(
            mode="target_height",
            target_height=parse_length(ns.alto_objetivo, default_unit="mm"),
        )

    if ns.cuadricula is not None:
        parts = ns.cuadricula.lower().replace("×", "x").split("x", 1)
        if len(parts) != 2:
            raise ValueError("La cuadrícula debe tener formato COLxFIL (ej. 3x2).")
        return ScaleSpec(
            mode="grid",
            grid_columns=int(parts[0].strip()),
            grid_rows=int(parts[1].strip()),
        )

    return ScaleSpec(mode="original")
