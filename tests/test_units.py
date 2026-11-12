import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.utils.units import (
    PT_PER_MM,
    format_dimensions_mm,
    mm_to_pt,
    parse_dimensions,
    parse_length,
    parse_margins,
    parse_scale_factor,
    pt_to_mm,
)


class TestUnits(unittest.TestCase):
    def test_mm_and_pt_roundtrip(self) -> None:
        pts = mm_to_pt(25.4)
        self.assertAlmostEqual(pts, 72.0, places=5)
        self.assertAlmostEqual(pt_to_mm(pts), 25.4, places=5)

    def test_parse_length_defaults_to_mm(self) -> None:
        self.assertAlmostEqual(parse_length("10"), 10.0 * PT_PER_MM, places=5)
        self.assertAlmostEqual(parse_length("10mm"), 10.0 * PT_PER_MM, places=5)
        self.assertAlmostEqual(parse_length("1.5cm"), 15.0 * PT_PER_MM, places=5)
        self.assertAlmostEqual(parse_length("1,5cm"), 15.0 * PT_PER_MM, places=5)
        self.assertAlmostEqual(parse_length("1in"), 72.0, places=5)
        self.assertAlmostEqual(parse_length("42pt"), 42.0, places=5)

    def test_parse_dimensions_propagates_trailing_unit(self) -> None:
        w, h = parse_dimensions("120x90cm")
        self.assertAlmostEqual(pt_to_mm(w), 1200.0, places=4)
        self.assertAlmostEqual(pt_to_mm(h), 900.0, places=4)

        w2, h2 = parse_dimensions("1000 x 800")
        self.assertAlmostEqual(pt_to_mm(w2), 1000.0, places=4)
        self.assertAlmostEqual(pt_to_mm(h2), 800.0, places=4)

    def test_parse_margins_forms(self) -> None:
        self.assertEqual(
            [round(pt_to_mm(x), 2) for x in parse_margins("8mm")],
            [8.0, 8.0, 8.0, 8.0],
        )
        self.assertEqual(
            [round(pt_to_mm(x), 2) for x in parse_margins("10,5mm")],
            [10.0, 5.0, 10.0, 5.0],
        )
        self.assertEqual(
            [round(pt_to_mm(x), 2) for x in parse_margins("4,6,8,10")],
            [4.0, 6.0, 8.0, 10.0],
        )

    def test_parse_scale_factor(self) -> None:
        self.assertAlmostEqual(parse_scale_factor("250%"), 2.5)
        self.assertAlmostEqual(parse_scale_factor("0.75"), 0.75)
        with self.assertRaises(ValueError):
            parse_scale_factor("0%")

    def test_format_dimensions_mm(self) -> None:
        text = format_dimensions_mm(mm_to_pt(1000), mm_to_pt(500))
        self.assertIn("1000.0 × 500.0 mm", text)
        self.assertIn("100.0 × 50.0 cm", text)


if __name__ == "__main__":
    unittest.main()
