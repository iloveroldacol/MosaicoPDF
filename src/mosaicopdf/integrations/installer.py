"""
Instalador de integraciones de escritorio para Inkscape y menús contextuales Linux.
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

_INTEGRATIONS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class InstallReport:
    """Resumen de rutas instaladas durante la integración."""

    installed: tuple[Path, ...]
    notes: tuple[str, ...]


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def detect_inkscape_extensions_dirs(home: Path | None = None) -> list[Path]:
    """Detecta carpetas de extensiones de Inkscape en Windows, macOS y Linux."""
    user_home = home or Path.home()
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else (user_home / "AppData" / "Roaming")
        return [base / "inkscape" / "extensions"]

    if sys.platform == "darwin":
        candidates = [
            user_home
            / "Library"
            / "Application Support"
            / "org.inkscape.Inkscape"
            / "config"
            / "inkscape"
            / "extensions",
            user_home / ".config" / "inkscape" / "extensions",
        ]
        existing = [p for p in candidates if p.parent.exists()]
        return existing if existing else [candidates[0]]

    candidates = [
        user_home / ".config" / "inkscape" / "extensions",
        user_home / "snap" / "inkscape" / "current" / ".config" / "inkscape" / "extensions",
        user_home / ".var" / "app" / "org.inkscape.Inkscape" / "config" / "inkscape" / "extensions",
    ]
    existing = [p for p in candidates if p.parent.exists()]
    return existing if existing else [candidates[0]]


def install_inkscape_extension(
    target_dirs: list[Path] | None = None,
    home: Path | None = None,
) -> InstallReport:
    """Instala ``mosaicopdf.inx`` y ``mosaicopdf_inkscape.py`` en Inkscape."""
    src_dir = _INTEGRATIONS_DIR / "inkscape"
    inx_src = src_dir / "mosaicopdf.inx"
    py_src = src_dir / "mosaicopdf_inkscape.py"

    # Ruta del paquete mosaicopdf para inyectarla en el adaptador de Inkscape
    pkg_src_root = Path(__file__).resolve().parents[2]
    py_content = py_src.read_text(encoding="utf-8").replace(
        'os.environ.get("MOSAICOPDF_SRC_DIR")',
        f'os.environ.get("MOSAICOPDF_SRC_DIR", {str(pkg_src_root)!r})',
    )

    dirs = target_dirs or detect_inkscape_extensions_dirs(home=home)
    installed: list[Path] = []

    for ext_dir in dirs:
        ext_dir.mkdir(parents=True, exist_ok=True)
        inx_dst = ext_dir / "mosaicopdf.inx"
        py_dst = ext_dir / "mosaicopdf_inkscape.py"

        shutil.copy2(inx_src, inx_dst)
        py_dst.write_text(py_content, encoding="utf-8")
        _make_executable(py_dst)
        installed.extend([inx_dst, py_dst])

    notes = (
        "Reinicia Inkscape y abre: Extensiones -> Exportar -> MosaicoPDF 2.0",
    )
    return InstallReport(installed=tuple(installed), notes=notes)


def install_linux_rightclick(home: Path | None = None) -> InstallReport:
    """
    Instala el lanzador de clic derecho para Nautilus, Nemo, Caja, Dolphin
    y entrada estándar 'Abrir con' (.desktop) en Linux.
    """
    user_home = home or Path.home()
    linux_src = _INTEGRATIONS_DIR / "linux"
    local_bin = user_home / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)

    mosaic_bin = shutil.which("mosaicopdf") or "mosaicopdf"
    rightclick_dst = local_bin / "mosaicopdf-rightclick"

    sh_template = (linux_src / "mosaicopdf-rightclick.sh").read_text(encoding="utf-8")
    sh_rendered = (
        sh_template.replace(
            'MOSAIC_BIN="${MOSAICOPDF_BIN:-mosaicopdf}"',
            f'MOSAIC_BIN="${{MOSAICOPDF_BIN:-{mosaic_bin}}}"',
        )
        .replace(
            'PYTHON_BIN="${MOSAICOPDF_PYTHON:-python3}"',
            f'PYTHON_BIN="${{MOSAICOPDF_PYTHON:-{sys.executable}}}"',
        )
    )
    rightclick_dst.write_text(sh_rendered, encoding="utf-8")
    _make_executable(rightclick_dst)

    installed: list[Path] = [rightclick_dst]
    notes: list[str] = []

    # 1. Entrada genérica 'Abrir con -> MosaicoPDF 2.0'
    apps_dir = user_home / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    app_desktop = apps_dir / "mosaicopdf.desktop"
    app_desktop.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=MosaicoPDF 2.0\n"
        "Comment=Dividir y escalar PDFs vectoriales en mosaico\n"
        f"Exec={rightclick_dst} %f\n"
        "Icon=document-print\n"
        "Terminal=false\n"
        "Categories=Graphics;Utility;\n"
        "MimeType=application/pdf;\n",
        encoding="utf-8",
    )
    installed.append(app_desktop)

    # 2. Scripts de clic derecho para Nautilus / Nemo / Caja
    for fm in ("nautilus", "nemo", "caja"):
        fm_base = user_home / ".local" / "share" / fm
        if fm == "nautilus" or fm_base.exists():
            scripts_dir = fm_base / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            script_path = scripts_dir / "MosaicoPDF 2.0"
            script_path.write_text(
                "#!/usr/bin/env bash\n"
                f'exec "{rightclick_dst}" "$1"\n',
                encoding="utf-8",
            )
            _make_executable(script_path)
            installed.append(script_path)

    # 3. Menú de servicio KDE Dolphin
    kio_dir = user_home / ".local" / "share" / "kio" / "servicemenus"
    if (user_home / ".local" / "share" / "kio").exists() or os.environ.get("XDG_CURRENT_DESKTOP", "").upper() == "KDE":
        kio_dir.mkdir(parents=True, exist_ok=True)
        dolphin_dst = kio_dir / "mosaicopdf.desktop"
        dolphin_tpl = (linux_src / "mosaicopdf-dolphin.desktop").read_text(encoding="utf-8")
        dolphin_rendered = dolphin_tpl.replace(
            "__RIGHTCLICK_BIN__", str(rightclick_dst)
        ).replace("__MOSAICOPDF_BIN__", mosaic_bin)
        dolphin_dst.write_text(dolphin_rendered, encoding="utf-8")
        _make_executable(dolphin_dst)
        installed.append(dolphin_dst)

    notes.append(
        "En GNOME/Nautilus usa clic derecho sobre un PDF -> 'Scripts' -> 'MosaicoPDF 2.0' "
        "o 'Abrir con -> MosaicoPDF 2.0'."
    )
    notes.append(
        f"Para XFCE Thunar, agrega la acción de: {linux_src / 'mosaicopdf-thunar-uca.xml'}"
    )
    return InstallReport(installed=tuple(installed), notes=tuple(notes))
