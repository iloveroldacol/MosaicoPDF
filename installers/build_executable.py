#!/usr/bin/env python3
"""
Genera un ejecutable autocontenido de MosaicoPDF 2.0 (Windows/macOS/Linux)
usando PyInstaller para distribución sin requerir Python en el equipo final.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    entrypoint = repo_root / "src" / "mosaicopdf" / "__main__.py"
    integrations_dir = repo_root / "src" / "mosaicopdf" / "integrations"

    if shutil.which("pyinstaller") is None:
        print("[INFO] PyInstaller no encontrado. Instalalo con: pip install pyinstaller")
        return 1

    sep = ";" if sys.platform.startswith("win") else ":"
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "mosaicopdf",
        "--paths",
        str(repo_root / "src"),
        "--add-data",
        f"{integrations_dir / 'inkscape'}{sep}mosaicopdf/integrations/inkscape",
        "--add-data",
        f"{integrations_dir / 'linux'}{sep}mosaicopdf/integrations/linux",
        str(entrypoint),
    ]
    print("[INFO] Ejecutando:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(repo_root))


if __name__ == "__main__":
    raise SystemExit(main())
