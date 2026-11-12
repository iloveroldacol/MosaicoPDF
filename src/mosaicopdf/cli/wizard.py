"""
Asistente interactivo ASCII para configurar mosaicos, perfiles e integraciones.
"""

from __future__ import annotations

from pathlib import Path

from mosaicopdf.config.papers import LARGE_FORMAT_PAPERS, OFFICE_PAPERS, parse_paper
from mosaicopdf.config.printers import PrinterStore
from mosaicopdf.core.pdf_reader import PDFReader
from mosaicopdf.core.pipeline import plan_page_mosaic, run_mosaic_job
from mosaicopdf.integrations.installer import (
    install_inkscape_extension,
    install_linux_rightclick,
)
from mosaicopdf.models.mosaic_settings import (
    AlignmentMode,
    MosaicSettings,
    OrientationMode,
    TraversalOrder,
)
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.models.scale_spec import ScaleSpec
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
from mosaicopdf.utils.units import (
    format_dimensions_mm,
    parse_dimensions,
    parse_length,
    parse_margins,
    parse_scale_factor,
)


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    try:
        raw = input(f"  {label}{suffix}: ").strip()
    except EOFError:
        return default or ""
    return raw if raw else (default or "")


def _prompt_yes_no(label: str, default: bool = True) -> bool:
    hint = "S/n" if default else "s/N"
    raw = _prompt(label, hint).lower()
    if raw in ("s/n", "s", "si", "sí", "y", "yes"):
        return True if raw != "s/n" else default
    if raw in ("n", "no"):
        return False
    return default


def run_wizard(initial_file: str | None = None) -> int:
    """Ejecuta el menú ASCII principal o salta directo al asistente si hay archivo."""
    banner()

    if initial_file:
        return _wizard_process_pdf(initial_file)

    while True:
        section("MENU PRINCIPAL")
        print("  [1] Procesar PDF (dividir plano o escalar a gran formato/mural)")
        print("  [2] Gestionar perfiles de impresora (margenes en mm)")
        print("  [3] Instalar integraciones (Inkscape y clic derecho Linux)")
        print("  [4] Ver formatos de papel disponibles")
        print("  [5] Verificar / instalar PyMuPDF automaticamente (doctor)")
        print("  [0] Salir")
        print()

        choice = _prompt("Elige una opcion", "1")
        if choice == "1":
            _wizard_process_pdf(None)
        elif choice == "2":
            _wizard_printers_menu()
        elif choice == "3":
            _wizard_integrations_menu()
        elif choice == "4":
            _show_papers_table()
        elif choice == "5":
            _wizard_doctor_menu()
        elif choice == "0":
            info("Hasta pronto.")
            return 0
        else:
            error("Opcion no valida.")


def _wizard_process_pdf(initial_file: str | None) -> int:
    if not is_fitz_available():
        info("PyMuPDF (motor PDF) aún no está instalado en este equipo.")
        if _prompt_yes_no("¿Instalarlo automáticamente en el entorno interno ahora?", True):
            try:
                repo_root = Path(__file__).resolve().parents[3]
                py_bin = install_pymupdf_managed(install_self_from=repo_root)
                ok(f"PyMuPDF instalado correctamente en: {py_bin}")
            except Exception as exc:
                error(str(exc))
                return 1
        else:
            error("Se requiere PyMuPDF para procesar archivos PDF.")
            return 1

    section("1. ARCHIVO PDF DE ENTRADA")
    raw_path = initial_file or _prompt("Ruta del PDF (puedes arrastrar el archivo aqui)")
    pdf_path = Path(raw_path.strip().strip("'\"")).expanduser()

    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        error(f"Archivo PDF no encontrado o invalido: {pdf_path}")
        return 1

    try:
        with PDFReader(str(pdf_path)) as reader:
            doc_info = reader.document_info()
    except Exception as exc:
        error(str(exc))
        return 1

    info(f"Paginas detectadas: {doc_info.page_count}")
    for p in doc_info.pages[:5]:
        print(
            f"    - Pagina {p.page_number + 1}: "
            f"{format_dimensions_mm(p.width, p.height)} ({p.orientation})"
        )

    page_sel = "1"
    if doc_info.page_count > 1:
        page_sel = _prompt("Paginas a procesar (ej. 1, 1-3, all)", "1")

    # Paso 2: Escala / Efecto inverso
    section("2. ESCALA / EFECTO INVERSO")
    print("  [1] Tamano original 1:1 (planos a escala real)")
    print("  [2] Escalar por porcentaje (ej. 250% para ampliar o 50% para reducir)")
    print("  [3] Escalar a gran formato o medida mural (ej. A0, A1, 1500x1000mm)")
    print("  [4] Ajustar a cuadricula de hojas (ej. 3x2 hojas para mural)")
    scale_choice = _prompt("Modo de escala", "1")
    scale_spec = _ask_scale_spec(scale_choice)

    # Paso 3: Papel y organizacion
    section("3. PAPEL DE IMPRESION Y ORGANIZACION")
    paper = _ask_paper()
    orient = _ask_orientation()
    alignment = _ask_alignment()
    order = _ask_traversal_order()

    # Paso 4: Perfil de impresora y margenes
    section("4. IMPRESORA Y MARGENES (mm)")
    profile = _ask_printer_profile()

    # Paso 5: Solapas y guias de armado
    section("5. SOLAPAS DE PEGADO Y GUIAS DE ARMADO")
    overlap_raw = _prompt("Solapa entre hojas en mm (0 = sin solapa)", "12")
    overlap_pt = parse_length(overlap_raw, default_unit="mm")
    cut_marks = _prompt_yes_no("Dibujar marcas de corte en esquinas?", True)
    assembly_guides = _prompt_yes_no(
        "Dibujar guias de solapa indicando la pieza vecina?", True
    )
    cover_map = _prompt_yes_no(
        "Incluir pagina inicial con mapa visual de ensamblaje?", True
    )
    export_json = _prompt_yes_no("Exportar tambien archivo .json de ensamblaje?", False)

    settings = MosaicSettings(
        printer_profile=profile,
        overlap_x=overlap_pt,
        overlap_y=overlap_pt,
        orientation=orient,
        alignment=alignment,
        traversal_order=order,
        cut_marks=cut_marks,
        assembly_guides=assembly_guides,
        cover_map=cover_map,
    )

    # Vista previa ASCII sobre la primera pagina seleccionada
    first_page = doc_info.get_page(0)
    try:
        preview = plan_page_mosaic(
            page_info=first_page,
            paper=paper,
            settings=settings,
            scale_spec=scale_spec,
        )
    except Exception as exc:
        error(str(exc))
        return 1

    print_ascii_mosaic(preview)
    print_mosaic_summary(preview, input_file=str(pdf_path), page_number=1)

    if not _prompt_yes_no("Confirmas generar el PDF en mosaico con esta configuracion?", True):
        info("Operacion cancelada por el usuario.")
        return 0

    try:
        result = run_mosaic_job(
            input_file=pdf_path,
            paper=paper,
            settings=settings,
            scale_spec=scale_spec,
            page_selection=page_sel,
            export_json=export_json,
        )
    except Exception as exc:
        error(f"Error al exportar: {exc}")
        return 1

    ok(f"PDF vectorial generado en: {result.output_file}")
    if result.json_file:
        ok(f"JSON de ensamblaje guardado en: {result.json_file}")
    info(f"Total de paginas en el PDF generado: {result.total_output_pages}")
    return 0


def _ask_scale_spec(choice: str) -> ScaleSpec:
    if choice == "2":
        raw = _prompt("Porcentaje o factor (ej. 200% o 2.5)", "200%")
        return ScaleSpec(mode="factor", factor=parse_scale_factor(raw))
    if choice == "3":
        raw = _prompt("Formato destino (a2, a1, a0, arch_d o ANCHOxALTOmm)", "a0")
        try:
            p = parse_paper(raw)
            tw, th = p.width, p.height
        except ValueError:
            tw, th = parse_dimensions(raw, default_unit="mm")
        return ScaleSpec(mode="target_size", target_width=tw, target_height=th)
    if choice == "4":
        cols = int(_prompt("Numero de columnas (hojas de ancho)", "3"))
        rows = int(_prompt("Numero de filas (hojas de alto)", "2"))
        return ScaleSpec(mode="grid", grid_columns=cols, grid_rows=rows)
    return ScaleSpec(mode="original")


def _ask_paper() -> Paper:
    print("  Opciones rapidas: carta, oficio, legal, a4, a3, tabloide, o '215x280mm'")
    while True:
        raw = _prompt("Papel de impresion", "carta")
        try:
            return parse_paper(raw)
        except ValueError as exc:
            error(str(exc))


def _ask_orientation() -> OrientationMode:
    print("  [1] Automatica (minimiza hojas)  [2] Vertical  [3] Horizontal")
    c = _prompt("Orientacion del papel", "1")
    return {"2": "portrait", "3": "landscape"}.get(c, "auto")  # type: ignore[return-value]


def _ask_alignment() -> AlignmentMode:
    print("  [1] Esquina superior izquierda (planos)  [2] Centrado (murales)")
    c = _prompt("Alineacion", "1")
    return "center" if c == "2" else "top-left"


def _ask_traversal_order() -> TraversalOrder:
    print("  [1] Por filas (A1, A2...)  [2] Por columnas (A1, B1...)  [3] Serpentina")
    c = _prompt("Orden de hojas", "1")
    return {"2": "col-major", "3": "snake"}.get(c, "row-major")  # type: ignore[return-value]


def _ask_printer_profile() -> PrinterProfile:
    store = PrinterStore()
    profiles = store.list_all()
    print_printer_profiles(profiles)
    raw = _prompt("Nombre del perfil (o escribe 'custom' para margenes propios)", "estandar")
    if raw.strip().lower() == "custom":
        margins_raw = _prompt("Margenes en mm (1 valor o sup,der,inf,izq)", "8")
        top, right, bottom, left = parse_margins(margins_raw, default_unit="mm")
        return PrinterProfile(
            name="personalizado",
            margin_top=top,
            margin_right=right,
            margin_bottom=bottom,
            margin_left=left,
        )
    try:
        return store.get(raw)
    except ValueError:
        info("Perfil no reconocido; usando 'estandar' (5 mm).")
        return store.get("estandar")


def _wizard_printers_menu() -> None:
    store = PrinterStore()
    while True:
        profiles = store.list_all()
        print_printer_profiles(profiles)
        print("  [1] Crear o actualizar perfil personalizado")
        print("  [2] Eliminar perfil personalizado")
        print("  [0] Volver")
        opt = _prompt("Elige una opcion", "0")
        if opt == "1":
            name = _prompt("Nombre del perfil (ej. mi-epson)")
            margins_raw = _prompt("Margenes en mm (ej. '6' o '5,5,12,5')", "6")
            desc = _prompt("Descripcion", "Perfil personalizado")
            try:
                t, r, b, l = parse_margins(margins_raw, default_unit="mm")
                store.save_profile(
                    PrinterProfile(
                        name=name,
                        margin_top=t,
                        margin_right=r,
                        margin_bottom=b,
                        margin_left=l,
                        description=desc,
                    )
                )
                ok(f"Perfil '{name}' guardado en {store.config_path}")
            except Exception as exc:
                error(str(exc))
        elif opt == "2":
            name = _prompt("Nombre del perfil a eliminar")
            if store.delete_profile(name):
                ok(f"Perfil '{name}' eliminado.")
            else:
                error(f"No existe un perfil personalizado llamado '{name}'.")
        else:
            return


def _wizard_integrations_menu() -> None:
    section("INTEGRACIONES DISPONIBLES")
    print("  [1] Instalar extension en Inkscape")
    print("  [2] Instalar menu clic derecho en Linux (Nautilus/Nemo/Dolphin/Abrir con)")
    print("  [3] Instalar ambas integraciones")
    print("  [0] Volver")
    opt = _prompt("Elige una opcion", "3")
    if opt in ("1", "3"):
        rep = install_inkscape_extension()
        for p in rep.installed:
            ok(f"Instalado: {p}")
        for note in rep.notes:
            info(note)
    if opt in ("2", "3"):
        rep = install_linux_rightclick()
        for p in rep.installed:
            ok(f"Instalado: {p}")
        for note in rep.notes:
            info(note)


def _show_papers_table() -> None:
    section("FORMATOS DE PAPEL DE OFICINA")
    for key, paper in OFFICE_PAPERS.items():
        print(f"  {key:<10} -> {paper.name:<10} {format_dimensions_mm(paper.width, paper.height)}")
    section("FORMATOS DE GRAN FORMATO (PARA ESCALADO INVERSO)")
    for key, paper in LARGE_FORMAT_PAPERS.items():
        print(f"  {key:<10} -> {paper.name:<10} {format_dimensions_mm(paper.width, paper.height)}")
    print()


def _wizard_doctor_menu() -> None:
    status = diagnose_runtime()
    section("DIAGNOSTICO DEL ENTORNO")
    print(f"  Sistema operativo  : {status.platform}")
    print(f"  Python             : {status.python_version}")
    print(f"  Entorno MosaicoPDF : {status.managed_venv}")
    print(
        f"  PyMuPDF (fitz)     : "
        f"{'OK v' + status.fitz_version if status.fitz_available and status.fitz_version else 'NO INSTALADO'}"
    )
    print(f"  Inkscape           : {status.inkscape_executable or 'No detectado en PATH'}")
    print()
    if not status.fitz_available:
        if _prompt_yes_no("¿Instalar PyMuPDF automáticamente ahora?", True):
            try:
                repo_root = Path(__file__).resolve().parents[3]
                py_bin = install_pymupdf_managed(install_self_from=repo_root)
                ok(f"PyMuPDF instalado en: {py_bin}")
            except Exception as exc:
                error(str(exc))
