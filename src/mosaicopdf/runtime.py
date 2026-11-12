"""
Gestión automática del entorno de ejecución y de la dependencia PyMuPDF.

Permite que usuarios sin experiencia en Python puedan instalar y usar
MosaicoPDF sin crear entornos virtuales ni ejecutar comandos de pip manualmente.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import venv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """Estado de diagnóstico del entorno de MosaicoPDF."""

    platform: str
    python_executable: str
    python_version: str
    fitz_available: bool
    fitz_version: str | None
    managed_venv: Path
    managed_python: Path
    managed_venv_exists: bool
    inkscape_executable: str | None


def managed_app_dir(home: Path | None = None) -> Path:
    """Devuelve la carpeta estándar de datos de usuario según Windows/macOS/Linux."""
    user_home = home or Path.home()
    if os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA")
        base = Path(local_app) if local_app else (user_home / "AppData" / "Local")
        return base / "MosaicoPDF"
    if sys.platform == "darwin":
        return user_home / "Library" / "Application Support" / "MosaicoPDF"
    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data) if xdg_data else (user_home / ".local" / "share")
    return base / "mosaicopdf"


def managed_venv_dir(home: Path | None = None) -> Path:
    """Ruta del entorno aislado interno gestionado por MosaicoPDF."""
    return managed_app_dir(home=home) / "venv"


def managed_python_path(venv_dir: Path | None = None) -> Path:
    """Ruta del intérprete Python dentro del entorno gestionado."""
    root = venv_dir or managed_venv_dir()
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    py3 = root / "bin" / "python3"
    return py3 if py3.exists() else (root / "bin" / "python")


def find_managed_site_packages(venv_dir: Path | None = None) -> list[Path]:
    """Localiza carpetas ``site-packages`` dentro del entorno gestionado."""
    root = venv_dir or managed_venv_dir()
    if not root.exists():
        return []
    candidates: list[Path] = []
    win_sp = root / "Lib" / "site-packages"
    if win_sp.is_dir():
        candidates.append(win_sp)
    lib_dir = root / "lib"
    if lib_dir.is_dir():
        for sp in sorted(lib_dir.glob("python*/site-packages")):
            if sp.is_dir():
                candidates.append(sp)
    return candidates


def _matching_managed_site_packages(venv_dir: Path | None = None) -> list[Path]:
    """Devuelve ``site-packages`` compatibles con la versión actual de Python."""
    py_tag = f"python{sys.version_info.major}.{sys.version_info.minor}"
    matches: list[Path] = []
    for sp in find_managed_site_packages(venv_dir):
        if os.name == "nt" or py_tag in sp.parts:
            matches.append(sp)
    return matches


def attach_managed_venv(venv_dir: Path | None = None) -> bool:
    """Agrega el entorno gestionado compatible a ``sys.path`` si existe."""
    added = False
    for sp in _matching_managed_site_packages(venv_dir):
        sp_str = str(sp)
        if sp_str not in sys.path:
            sys.path.insert(0, sp_str)
            added = True
    return added


def is_fitz_available() -> bool:
    """Indica si PyMuPDF (``fitz``) puede importarse en el proceso actual."""
    try:
        importlib.import_module("fitz")
        return True
    except ImportError:
        attach_managed_venv()
        try:
            importlib.import_module("fitz")
            return True
        except ImportError:
            return False


def get_fitz_version() -> str | None:
    """Devuelve la versión de PyMuPDF disponible o ``None`` si falta."""
    if not is_fitz_available():
        return None
    fitz_mod = importlib.import_module("fitz")
    return str(getattr(fitz_mod, "__version__", "desconocida"))


def import_fitz():
    """Importa ``fitz`` buscando también en el entorno gestionado interno."""
    attach_managed_venv()
    try:
        return importlib.import_module("fitz")
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF (fitz) no está instalado en este equipo. "
            "Ejecuta 'mosaicopdf doctor --instalar' para instalarlo automáticamente."
        ) from exc


def install_pymupdf_managed(
    venv_dir: Path | None = None,
    install_self_from: Path | None = None,
) -> Path:
    """
    Crea (si no existe) el entorno aislado interno de MosaicoPDF e instala PyMuPDF.
    No modifica el Python del sistema (compatible con PEP 668 / Windows / macOS).
    """
    target_venv = venv_dir or managed_venv_dir()
    target_venv.parent.mkdir(parents=True, exist_ok=True)

    py_bin = managed_python_path(target_venv)
    if not py_bin.exists():
        builder = venv.EnvBuilder(with_pip=True, clear=False)
        builder.create(str(target_venv))
        py_bin = managed_python_path(target_venv)

    cmd = [
        str(py_bin),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--upgrade",
        "PyMuPDF>=1.24",
    ]
    if install_self_from is not None and (install_self_from / "pyproject.toml").exists():
        cmd.append(str(install_self_from))

    proc = subprocess.run(cmd, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "No se pudo instalar PyMuPDF automáticamente. "
            "Verifica tu conexión a internet e intenta de nuevo."
        )

    attach_managed_venv(target_venv)
    return py_bin


def diagnose_runtime(home: Path | None = None) -> RuntimeStatus:
    """Recopila un diagnóstico completo del entorno para ``mosaicopdf doctor``."""
    venv_dir = managed_venv_dir(home=home)
    py_path = managed_python_path(venv_dir)
    fitz_ver = get_fitz_version()
    return RuntimeStatus(
        platform=sys.platform,
        python_executable=sys.executable,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        fitz_available=fitz_ver is not None,
        fitz_version=fitz_ver,
        managed_venv=venv_dir,
        managed_python=py_path,
        managed_venv_exists=venv_dir.exists(),
        inkscape_executable=shutil.which("inkscape"),
    )
