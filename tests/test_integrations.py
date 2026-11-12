import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.integrations.installer import (
    install_inkscape_extension,
    install_linux_rightclick,
)


class TestIntegrations(unittest.TestCase):
    def test_inkscape_inx_is_valid_xml(self) -> None:
        inx_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "mosaicopdf"
            / "integrations"
            / "inkscape"
            / "mosaicopdf.inx"
        )
        tree = ET.parse(inx_path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("inkscape-extension"))

    def test_install_inkscape_and_linux_rightclick_into_temp_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            ink_report = install_inkscape_extension(home=fake_home)
            self.assertEqual(len(ink_report.installed), 2)
            for path in ink_report.installed:
                self.assertTrue(path.exists())

            py_ext = fake_home / ".config" / "inkscape" / "extensions" / "mosaicopdf_inkscape.py"
            self.assertTrue(os.access(py_ext, os.X_OK))

            linux_report = install_linux_rightclick(home=fake_home)
            rightclick_bin = fake_home / ".local" / "bin" / "mosaicopdf-rightclick"
            nautilus_script = fake_home / ".local" / "share" / "nautilus" / "scripts" / "MosaicoPDF 2.0"
            desktop_entry = fake_home / ".local" / "share" / "applications" / "mosaicopdf.desktop"

            self.assertIn(rightclick_bin, linux_report.installed)
            self.assertIn(nautilus_script, linux_report.installed)
            self.assertIn(desktop_entry, linux_report.installed)
            self.assertTrue(os.access(rightclick_bin, os.X_OK))
            self.assertTrue(os.access(nautilus_script, os.X_OK))
            self.assertIn("MimeType=application/pdf;", desktop_entry.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
