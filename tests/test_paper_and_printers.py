import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.config.papers import get_paper, parse_paper
from mosaicopdf.config.printers import PrinterStore
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.utils.units import mm_to_pt, pt_to_mm


class TestPaperAndPrinters(unittest.TestCase):
    def test_paper_orientation(self) -> None:
        carta = get_paper("carta")
        self.assertEqual(carta.width, 612.0)
        self.assertEqual(carta.height, 792.0)
        self.assertFalse(carta.is_landscape)

        land = carta.oriented("landscape")
        self.assertEqual(land.width, 792.0)
        self.assertEqual(land.height, 612.0)
        self.assertTrue(land.is_landscape)

        port = land.oriented("portrait")
        self.assertEqual(port.width, 612.0)
        self.assertEqual(port.height, 792.0)

    def test_parse_custom_paper(self) -> None:
        custom = parse_paper("215x280mm")
        self.assertAlmostEqual(pt_to_mm(custom.width), 215.0, places=3)
        self.assertAlmostEqual(pt_to_mm(custom.height), 280.0, places=3)

        simple = Paper(name="Test", width=500, height=700)
        self.assertEqual(simple.printable_width, 500)
        self.assertEqual(simple.printable_height, 700)

    def test_printer_profile_printable_area(self) -> None:
        paper = Paper("Test", width=mm_to_pt(200), height=mm_to_pt(300))
        prof = PrinterProfile(
            name="custom",
            margin_top=mm_to_pt(10),
            margin_right=mm_to_pt(5),
            margin_bottom=mm_to_pt(15),
            margin_left=mm_to_pt(5),
        )
        self.assertAlmostEqual(pt_to_mm(prof.printable_width(paper)), 190.0, places=4)
        self.assertAlmostEqual(pt_to_mm(prof.printable_height(paper)), 275.0, places=4)

    def test_printer_store_crud(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PrinterStore(config_path=Path(tmpdir) / "printers.json")
            self.assertIn("estandar", store.list_all())

            custom = PrinterProfile(
                name="mi-plotter",
                margin_top=mm_to_pt(8),
                margin_right=mm_to_pt(8),
                margin_bottom=mm_to_pt(12),
                margin_left=mm_to_pt(8),
                description="Impresora de taller",
            )
            store.save_profile(custom)

            loaded = store.get("mi-plotter")
            self.assertAlmostEqual(pt_to_mm(loaded.margin_bottom), 12.0, places=2)
            self.assertEqual(loaded.description, "Impresora de taller")

            self.assertTrue(store.delete_profile("mi-epson") is False)
            self.assertTrue(store.delete_profile("mi-plotter") is True)
            with self.assertRaises(ValueError):
                store.get("mi-plotter")


if __name__ == "__main__":
    unittest.main()
