import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.config.papers import get_paper
from mosaicopdf.core.scaler import ScaleCalculator
from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.models.scale_spec import ScaleSpec
from mosaicopdf.utils.units import mm_to_pt, pt_to_mm


class TestScaler(unittest.TestCase):
    def test_original_and_factor_scale(self) -> None:
        a4 = get_paper("a4")
        res_orig = ScaleCalculator.calculate(a4.width, a4.height, ScaleSpec())
        self.assertEqual(res_orig.scale_factor, 1.0)
        self.assertEqual(res_orig.virtual_width, a4.width)

        res_250 = ScaleCalculator.calculate(
            a4.width, a4.height, ScaleSpec(mode="factor", factor=2.5)
        )
        self.assertAlmostEqual(res_250.virtual_width, a4.width * 2.5)
        self.assertAlmostEqual(res_250.virtual_height, a4.height * 2.5)
        self.assertAlmostEqual(res_250.percentage, 250.0)

    def test_reverse_effect_a4_to_a0_preserves_aspect(self) -> None:
        a4 = get_paper("a4")
        a0 = get_paper("a0")
        res = ScaleCalculator.calculate(
            a4.width,
            a4.height,
            ScaleSpec(
                mode="target_size",
                target_width=a0.width,
                target_height=a0.height,
                fit_mode="contain",
            ),
        )
        # A4 -> A0 es exactamente ~4.0x lineal (400%)
        self.assertAlmostEqual(res.scale_factor, 4.0, places=2)
        self.assertAlmostEqual(
            res.virtual_width / res.virtual_height,
            a4.width / a4.height,
            places=5,
        )

    def test_target_size_auto_rotates_box(self) -> None:
        # Diseño horizontal (300 x 150 mm) escalado a caja vertical (600 x 1200 mm)
        res = ScaleCalculator.calculate(
            mm_to_pt(300),
            mm_to_pt(150),
            ScaleSpec(
                mode="target_size",
                target_width=mm_to_pt(600),
                target_height=mm_to_pt(1200),
                auto_rotate_target=True,
            ),
        )
        self.assertAlmostEqual(res.scale_factor, 4.0, places=4)
        self.assertAlmostEqual(pt_to_mm(res.virtual_width), 1200.0, places=3)
        self.assertAlmostEqual(pt_to_mm(res.virtual_height), 600.0, places=3)

    def test_grid_mural_scaling(self) -> None:
        paper = get_paper("carta")
        profile = PrinterProfile(
            name="test",
            margin_top=mm_to_pt(10),
            margin_right=mm_to_pt(10),
            margin_bottom=mm_to_pt(10),
            margin_left=mm_to_pt(10),
        )
        settings = MosaicSettings(
            printer_profile=profile,
            overlap_x=mm_to_pt(10),
            overlap_y=mm_to_pt(10),
            orientation="portrait",
        )
        res = ScaleCalculator.calculate(
            mm_to_pt(200),
            mm_to_pt(200),
            ScaleSpec(mode="grid", grid_columns=3, grid_rows=2),
            paper=paper,
            settings=settings,
        )
        pw = profile.printable_width(paper)
        ph = profile.printable_height(paper)
        expected_w = pw + 2 * (pw - mm_to_pt(10))
        expected_h = ph + 1 * (ph - mm_to_pt(10))
        expected_factor = min(expected_w / mm_to_pt(200), expected_h / mm_to_pt(200))
        self.assertAlmostEqual(res.scale_factor, expected_factor, places=5)


if __name__ == "__main__":
    unittest.main()
