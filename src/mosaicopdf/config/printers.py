"""
Perfiles de impresora integrados y almacenamiento persistente de perfiles de usuario.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.utils.units import mm_to_pt

BUILTIN_PRINTERS: dict[str, PrinterProfile] = {
    "estandar": PrinterProfile(
        name="estandar",
        margin_top=mm_to_pt(5.0),
        margin_right=mm_to_pt(5.0),
        margin_bottom=mm_to_pt(5.0),
        margin_left=mm_to_pt(5.0),
        description="Impresora doméstica/oficina estándar (5 mm por lado)",
    ),
    "segura": PrinterProfile(
        name="segura",
        margin_top=mm_to_pt(10.0),
        margin_right=mm_to_pt(10.0),
        margin_bottom=mm_to_pt(10.0),
        margin_left=mm_to_pt(10.0),
        description="Margen conservador para alimentación segura (10 mm por lado)",
    ),
    "amplia": PrinterProfile(
        name="amplia",
        margin_top=mm_to_pt(12.7),
        margin_right=mm_to_pt(12.7),
        margin_bottom=mm_to_pt(12.7),
        margin_left=mm_to_pt(12.7),
        description="Margen amplio con espacio extra para rotulación (12.7 mm)",
    ),
    "sin-bordes": PrinterProfile(
        name="sin-bordes",
        margin_top=0.0,
        margin_right=0.0,
        margin_bottom=0.0,
        margin_left=0.0,
        description="Impresión sin márgenes (0 mm)",
    ),
}


def default_config_path() -> Path:
    """Devuelve la ruta estándar del archivo JSON de perfiles de impresora."""
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(xdg_home) if xdg_home else (Path.home() / ".config")
    return base_dir / "mosaicopdf" / "printers.json"


class PrinterStore:
    """
    Gestiona perfiles de impresora combinando los integrados con los guardados
    por el usuario en disco.
    """

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or default_config_path()

    def load_custom(self) -> dict[str, PrinterProfile]:
        """Carga los perfiles personalizados del usuario desde JSON."""
        if not self.config_path.exists():
            return {}
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"No se pudo leer el archivo de perfiles '{self.config_path}': {exc}"
            ) from exc

        profiles: dict[str, PrinterProfile] = {}
        for item in raw.get("profiles", []):
            profile = PrinterProfile.from_dict(item)
            profiles[profile.name.lower()] = profile
        return profiles

    def list_all(self) -> dict[str, PrinterProfile]:
        """Devuelve todos los perfiles disponibles (los personalizados sobrescriben)."""
        combined = dict(BUILTIN_PRINTERS)
        combined.update(self.load_custom())
        return combined

    def get(self, name: str) -> PrinterProfile:
        """Obtiene un perfil por nombre (insensible a mayúsculas)."""
        key = name.strip().lower()
        all_profiles = self.list_all()
        if key not in all_profiles:
            available = ", ".join(all_profiles.keys())
            raise ValueError(
                f"Perfil de impresora no encontrado: '{name}'. "
                f"Disponibles: {available}."
            )
        return all_profiles[key]

    def save_profile(self, profile: PrinterProfile) -> None:
        """Guarda o actualiza un perfil personalizado en disco."""
        custom = self.load_custom()
        custom[profile.name.strip().lower()] = profile

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "profiles": [p.to_dict() for p in custom.values()],
        }
        self.config_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def delete_profile(self, name: str) -> bool:
        """Elimina un perfil personalizado. Devuelve False si no existía."""
        key = name.strip().lower()
        custom = self.load_custom()
        if key not in custom:
            return False

        del custom[key]
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "profiles": [p.to_dict() for p in custom.values()],
        }
        self.config_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return True
