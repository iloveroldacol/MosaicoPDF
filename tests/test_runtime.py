import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.runtime import (
    attach_managed_venv,
    diagnose_runtime,
    find_managed_site_packages,
    managed_app_dir,
    managed_venv_dir,
)


class TestRuntime(unittest.TestCase):
    def test_managed_paths_respect_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            app_dir = managed_app_dir(home=fake_home)
            venv_dir = managed_venv_dir(home=fake_home)
            self.assertEqual(venv_dir.parent, app_dir)
            self.assertTrue(str(app_dir).startswith(str(fake_home)) or "AppData" in str(app_dir))

    def test_attach_managed_venv_finds_matching_python_site_packages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_venv = Path(tmpdir) / "venv"
            py_tag = f"python{sys.version_info.major}.{sys.version_info.minor}"
            sp = fake_venv / "lib" / py_tag / "site-packages"
            sp.mkdir(parents=True)

            found = find_managed_site_packages(fake_venv)
            self.assertIn(sp, found)

            added = attach_managed_venv(fake_venv)
            self.assertTrue(added)
            self.assertIn(str(sp), sys.path)
            # Limpiar sys.path
            sys.path.remove(str(sp))

    def test_diagnose_runtime_returns_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status = diagnose_runtime(home=Path(tmpdir))
            self.assertFalse(status.managed_venv_exists)
            self.assertTrue(status.python_version.startswith("3."))


if __name__ == "__main__":
    unittest.main()
