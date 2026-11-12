"""
Despachador principal de la CLI de MosaicoPDF 2.0.
"""

from __future__ import annotations

import sys

from pathlib import Path

from mosaicopdf.cli.parser import (
    SUBCOMMANDS,
    build_main_parser,
    build_subcommand_parser,
    resolve_direct_args,
)
from mosaicopdf.cli.wizard import run_wizard
from mosaicopdf.config.papers import LARGE_FORMAT_PAPERS, OFFICE_PAPERS
from mosaicopdf.config.printers import PrinterStore
from mosaicopdf.core.pdf_reader import PDFReader
from mosaicopdf.core.pipeline import parse_page_selection, plan_page_mosaic, run_mosaic_job
from mosaicopdf.integrations.installer import (
    install_inkscape_extension,
    install_linux_rightclick,
)
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.runtime import (
    diagnose_runtime,
    install_pymupdf_managed,
    is_fitz_available,
)
from mosaicopdf.utils.console import (
    banner,
    error,
    info,
    ok,
    print_ascii_mosaic,
    print_mosaic_summary,
    print_printer_profiles,
    section,
)
from mosaicopdf.utils.units import format_dimensions_mm, parse_margins


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la interfaz de línea de comandos."""
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        return run_wizard(initial_file=None)

    if args[0] in SUBCOMMANDS:
        return _run_subcommand(args)

    parser = build_main_parser()
    ns = parser.parse_args(args)

    try:
        parsed = resolve_direct_args(ns)
    except Exception as exc:
        banner()
        error(str(exc))
        return 1

    if parsed.interactive or not parsed.input_file:
        return run_wizard(initial_file=parsed.input_file)

    banner()
    if not _ensure_fitz_ready():
        return 1

    if parsed.dry_run:
        return _run_dry_run(parsed)

    info(f"Procesando '{parsed.input_file}'...")
    try:
        result = run_mosaic_job(
            input_file=parsed.input_file,
            paper=parsed.paper,
            settings=parsed.settings,
            scale_spec=parsed.scale_spec,
            output_file=parsed.output_file,
            page_selection=parsed.page_selection,
            export_json=parsed.export_json,
        )
    except Exception as exc:
        error(str(exc))
        return 1

    for page_idx, mosaic in result.mosaics:
        print_ascii_mosaic(mosaic)
        print_mosaic_summary(
            mosaic=mosaic,
            input_file=str(result.input_file),
            output_file=str(result.output_file),
            page_number=page_idx + 1,
        )

    ok(f"Proceso terminado correctamente. Paginas exportadas: {result.total_output_pages}")
    if result.json_file:
        ok(f"Mapa de ensamblaje JSON: {result.json_file}")
    return 0


def _run_dry_run(parsed) -> int:
    try:
        with PDFReader(parsed.input_file) as reader:
            indices = parse_page_selection(parsed.page_selection, reader.page_count)
            for idx in indices:
                pinfo = reader.page_info(idx)
                mosaic = plan_page_mosaic(
                    page_info=pinfo,
                    paper=parsed.paper,
                    settings=parsed.settings,
                    scale_spec=parsed.scale_spec,
                )
                print_ascii_mosaic(mosaic)
                print_mosaic_summary(
                    mosaic=mosaic,
                    input_file=parsed.input_file,
                    output_file=None,
                    page_number=idx + 1,
                )
    except Exception as exc:
        error(str(exc))
        return 1

    ok("Simulacion completada (no se escribieron archivos).")
    return 0


def _run_subcommand(args: list[str]) -> int:
    parser = build_subcommand_parser()
    ns = parser.parse_args(args)
    banner()

    if ns.subcommand == "papeles":
        section("FORMATOS DE PAPEL DE OFICINA")
        for key, paper in OFFICE_PAPERS.items():
            print(f"  {key:<10} -> {paper.name:<10} {format_dimensions_mm(paper.width, paper.height)}")
        section("FORMATOS DE GRAN FORMATO")
        for key, paper in LARGE_FORMAT_PAPERS.items():
            print(f"  {key:<10} -> {paper.name:<10} {format_dimensions_mm(paper.width, paper.height)}")
        print()
        return 0

    if ns.subcommand == "perfiles":
        store = PrinterStore()
        if ns.action == "listar":
            print_printer_profiles(store.list_all())
            return 0
        if ns.action == "crear":
            try:
                t, r, b, l = parse_margins(ns.margen, default_unit="mm")
                store.save_profile(
                    PrinterProfile(
                        name=ns.name,
                        margin_top=t,
                        margin_right=r,
                        margin_bottom=b,
                        margin_left=l,
                        description=ns.descripcion,
                    )
                )
            except Exception as exc:
                error(str(exc))
                return 1
            ok(f"Perfil '{ns.name}' guardado en {store.config_path}")
            return 0
        if ns.action == "eliminar":
            if store.delete_profile(ns.name):
                ok(f"Perfil '{ns.name}' eliminado.")
                return 0
            error(f"No existe un perfil personalizado llamado '{ns.name}'.")
            return 1

    if ns.subcommand == "integrar":
        do_all = ns.todo or (not ns.inkscape and not ns.linux)
        if do_all or ns.inkscape:
            rep = install_inkscape_extension()
            for p in rep.installed:
                ok(f"Inkscape: {p}")
            for note in rep.notes:
                info(note)
        if do_all or ns.linux:
            rep = install_linux_rightclick()
            for p in rep.installed:
                ok(f"Linux: {p}")
            for note in rep.notes:
                info(note)
        return 0

    if ns.subcommand == "doctor":
        return _run_doctor(auto_install=bool(ns.instalar))

    return 1


def _ensure_fitz_ready() -> bool:
    """Verifica PyMuPDF y ofrece instalación automática en entorno interno si falta."""
    if is_fitz_available():
        return True

    info("No se detectó la librería gráfica PyMuPDF en el Python actual.")
    if sys.stdin.isatty():
        answer = input("  ¿Deseas instalar PyMuPDF automáticamente ahora? [S/n]: ").strip().lower()
        if answer in ("", "s", "si", "sí", "y", "yes"):
            try:
                repo_root = Path(__file__).resolve().parents[3]
                py_bin = install_pymupdf_managed(install_self_from=repo_root)
                ok(f"PyMuPDF instalado en entorno interno: {py_bin}")
                return True
            except Exception as exc:
                error(str(exc))
                return False

    error("Falta PyMuPDF. Ejecuta: mosaicopdf doctor --instalar")
    return False


def _run_doctor(auto_install: bool) -> int:
    status = diagnose_runtime()
    section("DIAGNOSTICO DEL SISTEMA")
    print(f"  Sistema operativo  : {status.platform}")
    print(f"  Python actual      : {status.python_version} ({status.python_executable})")
    print(f"  Entorno MosaicoPDF : {status.managed_venv} ({'existe' if status.managed_venv_exists else 'no creado'})")
    print(
        f"  PyMuPDF (fitz)     : "
        f"{'OK v' + status.fitz_version if status.fitz_available and status.fitz_version else 'NO INSTALADO'}"
    )
    print(f"  Inkscape           : {status.inkscape_executable or 'No detectado en PATH'}")
    print()

    if status.fitz_available:
        ok("Todo listo para procesar PDFs vectoriales.")
        return 0

    if not auto_install:
        info("Para instalar PyMuPDF automáticamente sin tocar tu sistema, ejecuta:")
        print("    mosaicopdf doctor --instalar")
        return 1

    info("Instalando PyMuPDF en el entorno interno de MosaicoPDF...")
    try:
        repo_root = Path(__file__).resolve().parents[3]
        py_bin = install_pymupdf_managed(install_self_from=repo_root)
    except Exception as exc:
        error(str(exc))
        return 1

    ok(f"PyMuPDF instalado correctamente en: {py_bin}")
    return 0
