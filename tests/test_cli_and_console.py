import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.cli.parser import build_main_parser, resolve_direct_args
from mosaicopdf.config.papers import get_paper
from mosaicopdf.config.printers import PrinterStore
from mosaicopdf.core.mosaic_builder import MosaicBuilder
from mosaicopdf.core.pipeline import parse_page_selection
from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.utils.console import render_ascii_mosaic
from mosaicopdf.utils.units import mm_to_pt, pt_to_mm


class TestCliAndConsole(unittest.TestCase):
    def test_v1_positional_backward_compat(self) -> None:
        parser = build_main_parser()
        ns = parser.parse_args(["plano.pdf", "oficio"])
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PrinterStore(Path(tmpdir) / "printers.json")
            parsed = resolve_direct_args(ns, store=store)
        self.assertEqual(parsed.input_file, "plano.pdf")
        self.assertEqual(parsed.paper.name, "Oficio")

    def test_v2_flags_reverse_scaling_and_guides(self) -> None:
        parser = build_main_parser()
        ns = parser.parse_args(
            [
                "boceto_a4.pdf",
                "--papel",
                "carta",
                "--margen",
                "8mm",
                "--solapa",
                "15mm",
                "--escalar-a",
                "a0",
                "--orientacion",
                "horizontal",
                "--centrar",
                "--orden",
                "serpentina",
                "--mapa",
                "--json",
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PrinterStore(Path(tmpdir) / "printers.json")
            parsed = resolve_direct_args(ns, store=store)

        self.assertEqual(parsed.paper.name, "Carta")
        self.assertAlmostEqual(pt_to_mm(parsed.settings.overlap_x), 15.0, places=3)
        self.assertAlmostEqual(pt_to_mm(parsed.settings.printer_profile.margin_left), 8.0, places=3)
        self.assertEqual(parsed.settings.orientation, "landscape")
        self.assertEqual(parsed.settings.alignment, "center")
        self.assertEqual(parsed.settings.traversal_order, "snake")
        self.assertTrue(parsed.settings.cover_map)
        self.assertTrue(parsed.export_json)
        self.assertEqual(parsed.scale_spec.mode, "target_size")

    def test_parse_page_selection(self) -> None:
        self.assertEqual(parse_page_selection("1", 5), [0])
        self.assertEqual(parse_page_selection("1,3-5", 5), [0, 2, 3, 4])
        self.assertEqual(parse_page_selection("all", 3), [0, 1, 2])
        with self.assertRaises(ValueError):
            parse_page_selection("6", 5)

    def test_render_ascii_mosaic_shows_codes_and_overlap_marker(self) -> None:
        paper = get_paper("carta")
        profile = PrinterProfile("m5", mm_to_pt(5), mm_to_pt(5), mm_to_pt(5), mm_to_pt(5))
        settings = MosaicSettings(
            printer_profile=profile,
            overlap_x=mm_to_pt(12),
            overlap_y=mm_to_pt(12),
            orientation="portrait",
        )
        mosaic = MosaicBuilder(mm_to_pt(350), mm_to_pt(400), paper, settings).build()
        diagram = render_ascii_mosaic(mosaic)
        self.assertIn("A1 (#1)", diagram)
        self.assertIn("A2 (#2)", diagram)
        self.assertIn(":", diagram)
        self.assertIn("~", diagram)


if __name__ == "__main__":
    unittest.main()
