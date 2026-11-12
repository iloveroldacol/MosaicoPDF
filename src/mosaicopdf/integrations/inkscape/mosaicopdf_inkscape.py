#!/usr/bin/env python3
"""
Extensión de Inkscape para MosaicoPDF 2.0 (Windows, macOS y Linux).

Exporta el SVG activo a PDF vectorial mediante Inkscape CLI y ejecuta
MosaicoPDF conservando el 100% de los vectores. Si el Python interno de
Inkscape no tiene PyMuPDF, delega automáticamente al entorno gestionado
de MosaicoPDF.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_EXTRA_SRC = os.environ.get("MOSAICOPDF_SRC_DIR")
if _EXTRA_SRC and _EXTRA_SRC not in sys.path:
    sys.path.insert(0, _EXTRA_SRC)

try:
    import inkex  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover - ejecutado dentro de Inkscape
    raise SystemExit(
        "Este script debe ejecutarse desde Inkscape (falta el módulo inkex)."
    ) from exc


def _find_inkscape_binary() -> str:
    found = shutil.which("inkscape")
    if found:
        return found
    if os.name == "nt":
        for cand in (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inkscape" / "bin" / "inkscape.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Inkscape" / "bin" / "inkscape.exe",
        ):
            if cand.exists():
                return str(cand)
    elif sys.platform == "darwin":
        mac_bin = Path("/Applications/Inkscape.app/Contents/MacOS/inkscape")
        if mac_bin.exists():
            return str(mac_bin)
    return "inkscape"


def _find_managed_command(src_dir: str | None) -> list[str] | None:
    """Localiza el ejecutable o entorno gestionado de MosaicoPDF si falta fitz en Inkscape."""
    from mosaicopdf.runtime import managed_python_path

    managed_py = managed_python_path()
    if managed_py.exists():
        return [str(managed_py), "-m", "mosaicopdf"]

    cli_bin = shutil.which("mosaicopdf")
    if cli_bin:
        return [cli_bin]

    if src_dir:
        return [sys.executable, "-m", "mosaicopdf"]
    return None


class MosaicoPDFExtension(inkex.EffectExtension):
    """Efecto de Inkscape que genera un mosaico PDF vectorial del dibujo actual."""

    def add_arguments(self, pars) -> None:
        pars.add_argument("--tab", default="layout")
        pars.add_argument("--paper", default="carta")
        pars.add_argument("--orientation", default="auto")
        pars.add_argument("--scale_mode", default="original")
        pars.add_argument("--scale_value", default="100%")
        pars.add_argument("--alignment", default="top-left")
        pars.add_argument("--margin_mm", type=float, default=5.0)
        pars.add_argument("--overlap_mm", type=float, default=12.0)
        pars.add_argument("--traversal", default="row-major")
        pars.add_argument("--cut_marks", type=inkex.Boolean, default=True)
        pars.add_argument("--assembly_guides", type=inkex.Boolean, default=True)
        pars.add_argument("--cover_map", type=inkex.Boolean, default=True)
        pars.add_argument("--output_dir", default="")
        pars.add_argument("--export_json", type=inkex.Boolean, default=False)

    def effect(self) -> None:
        try:
            from mosaicopdf.runtime import is_fitz_available
            from mosaicopdf.utils.output_filename import build_output_filename
        except ImportError as exc:
            inkex.errormsg(
                "No se encontró el paquete 'mosaicopdf'. "
                "Ejecuta el instalador de MosaicoPDF 2.0 primero.\n"
                f"Detalle: {exc}"
            )
            return

        doc_path_str = self.document_path()
        base_name = Path(doc_path_str).stem if doc_path_str else "dibujo_inkscape"
        out_dir_opt = str(self.options.output_dir or "").strip()

        if out_dir_opt:
            target_dir = Path(out_dir_opt).expanduser()
        elif doc_path_str:
            target_dir = Path(doc_path_str).parent
        else:
            desktop = Path.home() / "Desktop"
            target_dir = desktop if desktop.exists() else Path.home()

        target_dir.mkdir(parents=True, exist_ok=True)
        output_pdf = build_output_filename(
            target_dir / f"{base_name}.pdf",
            output_dir=target_dir,
        )

        with tempfile.TemporaryDirectory(prefix="mosaicopdf_ink_") as tmpdir:
            tmp_svg = Path(tmpdir) / f"{base_name}.svg"
            tmp_pdf = Path(tmpdir) / f"{base_name}.pdf"
            self.svg.getroottree().write(str(tmp_svg), encoding="utf-8", xml_declaration=True)

            ink_cmd = [
                _find_inkscape_binary(),
                str(tmp_svg),
                "--export-type=pdf",
                f"--export-filename={tmp_pdf}",
            ]
            proc = subprocess.run(ink_cmd, capture_output=True, text=True)
            if proc.returncode != 0 or not tmp_pdf.exists():
                inkex.errormsg(
                    "Inkscape no pudo exportar el SVG a PDF vectorial:\n"
                    f"{proc.stderr or proc.stdout}"
                )
                return

            if is_fitz_available():
                self._run_direct(tmp_pdf, output_pdf)
            else:
                self._run_via_subprocess(tmp_pdf, output_pdf)

    def _run_direct(self, tmp_pdf: Path, output_pdf: Path) -> None:
        from mosaicopdf.config.papers import parse_paper
        from mosaicopdf.core.pipeline import run_mosaic_job
        from mosaicopdf.models.mosaic_settings import MosaicSettings
        from mosaicopdf.models.printer_profile import PrinterProfile
        from mosaicopdf.models.scale_spec import ScaleSpec
        from mosaicopdf.utils.units import mm_to_pt, parse_dimensions, parse_scale_factor

        scale_spec = self._build_scale_spec(
            parse_paper, parse_dimensions, parse_scale_factor, ScaleSpec
        )
        if scale_spec is None:
            return

        margin_pt = mm_to_pt(max(0.0, float(self.options.margin_mm)))
        overlap_pt = mm_to_pt(max(0.0, float(self.options.overlap_mm)))
        paper = parse_paper(self.options.paper)
        profile = PrinterProfile(
            name="inkscape",
            margin_top=margin_pt,
            margin_right=margin_pt,
            margin_bottom=margin_pt,
            margin_left=margin_pt,
        )
        settings = MosaicSettings(
            printer_profile=profile,
            overlap_x=overlap_pt,
            overlap_y=overlap_pt,
            orientation=self.options.orientation,
            alignment=self.options.alignment,
            traversal_order=self.options.traversal,
            cut_marks=bool(self.options.cut_marks),
            assembly_guides=bool(self.options.assembly_guides),
            cover_map=bool(self.options.cover_map),
        )

        try:
            result = run_mosaic_job(
                input_file=tmp_pdf,
                paper=paper,
                settings=settings,
                scale_spec=scale_spec,
                output_file=output_pdf,
                page_selection="1",
                export_json=bool(self.options.export_json),
            )
        except Exception as exc:
            inkex.errormsg(f"Error al generar el mosaico: {exc}")
            return

        _, mosaic = result.mosaics[0]
        inkex.errormsg(
            f"MosaicoPDF 2.0 completado:\n"
            f"- Archivo: {result.output_file}\n"
            f"- Cuadricula: {mosaic.rows} filas x {mosaic.columns} columnas ({len(mosaic)} hojas)\n"
            f"- Escala aplicada: {mosaic.scale_result.percentage:.1f}%"
        )

    def _run_via_subprocess(self, tmp_pdf: Path, output_pdf: Path) -> None:
        """Usa el Python gestionado de MosaicoPDF cuando Inkscape usa un Python aislado."""
        cmd_prefix = _find_managed_command(_EXTRA_SRC)
        if not cmd_prefix:
            inkex.errormsg(
                "PyMuPDF no está disponible en el Python interno de Inkscape. "
                "Ejecuta 'mosaicopdf doctor --instalar' o el instalador del sistema."
            )
            return

        cli_args = [
            *cmd_prefix,
            str(tmp_pdf),
            "--papel",
            str(self.options.paper),
            "--orientacion",
            str(self.options.orientation),
            "--alineacion",
            str(self.options.alignment),
            "--orden",
            str(self.options.traversal),
            "--margen",
            f"{float(self.options.margin_mm)}mm",
            "--solapa",
            f"{float(self.options.overlap_mm)}mm",
            "--salida",
            str(output_pdf),
        ]
        mode = self.options.scale_mode
        val = str(self.options.scale_value or "").strip()
        if mode == "factor" and val:
            cli_args.extend(["--escala", val])
        elif mode == "target_size" and val:
            cli_args.extend(["--escalar-a", val])
        elif mode == "grid" and val:
            cli_args.extend(["--cuadricula", val])

        if not bool(self.options.cut_marks):
            cli_args.append("--sin-marcas")
        if not bool(self.options.assembly_guides):
            cli_args.append("--sin-guias")
        if bool(self.options.cover_map):
            cli_args.append("--mapa")
        if bool(self.options.export_json):
            cli_args.append("--json")

        env = dict(os.environ)
        if _EXTRA_SRC:
            env["PYTHONPATH"] = _EXTRA_SRC

        proc = subprocess.run(cli_args, capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            inkex.errormsg(
                "Error al ejecutar MosaicoPDF:\n"
                f"{proc.stderr or proc.stdout}"
            )
            return

        inkex.errormsg(f"MosaicoPDF 2.0 completado:\n- Archivo: {output_pdf}")

    def _build_scale_spec(
        self,
        parse_paper,
        parse_dimensions,
        parse_scale_factor,
        ScaleSpec,
    ):
        mode = self.options.scale_mode
        val = str(self.options.scale_value or "").strip()

        try:
            if mode == "original":
                return ScaleSpec(mode="original")
            if mode == "factor":
                return ScaleSpec(mode="factor", factor=parse_scale_factor(val or "100%"))
            if mode == "target_size":
                try:
                    target_paper = parse_paper(val)
                    w, h = target_paper.width, target_paper.height
                except ValueError:
                    w, h = parse_dimensions(val, default_unit="mm")
                return ScaleSpec(mode="target_size", target_width=w, target_height=h)
            if mode == "grid":
                cols_str, rows_str = val.lower().replace("×", "x").split("x", 1)
                return ScaleSpec(
                    mode="grid",
                    grid_columns=int(cols_str.strip()),
                    grid_rows=int(rows_str.strip()),
                )
        except Exception as exc:
            inkex.errormsg(f"Valor de escala invalido ('{val}'): {exc}")
            return None

        return ScaleSpec(mode="original")


if __name__ == "__main__":  # pragma: no cover
    MosaicoPDFExtension().run()
