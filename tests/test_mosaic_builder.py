import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.core.mosaic_builder import MosaicBuilder
from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.utils.units import mm_to_pt, pt_to_mm


class TestMosaicBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.paper = Paper("Test200x300", width=mm_to_pt(220), height=mm_to_pt(320))
        self.profile = PrinterProfile(
            name="m10",
            margin_top=mm_to_pt(10),
            margin_right=mm_to_pt(10),
            margin_bottom=mm_to_pt(10),
            margin_left=mm_to_pt(10),
        )  # Área útil: 200 x 300 mm

    def test_exact_fit_produces_single_sheet_without_phantom_tile(self) -> None:
        settings = MosaicSettings(printer_profile=self.profile, orientation="portrait")
        mosaic = MosaicBuilder(
            page_width=mm_to_pt(200.0),
            page_height=mm_to_pt(300.0),
            paper=self.paper,
            settings=settings,
        ).build()
        self.assertEqual(mosaic.rows, 1)
        self.assertEqual(mosaic.columns, 1)
        self.assertEqual(len(mosaic), 1)
        t = mosaic.get_tile(0, 0)
        self.assertEqual(t.code, "A1")
        self.assertIsNone(t.neighbor_right)

    def test_overlaps_and_neighbor_labels(self) -> None:
        # Área útil 200 x 300 mm, solapa 15 mm -> paso X=185, paso Y=285
        # Plano 386 x 590 mm -> Cols: [0..200], [185..385], [370..386] => 3 cols
        # Rows: [0..300], [285..585], [570..590] => 3 rows
        settings = MosaicSettings(
            printer_profile=self.profile,
            overlap_x=mm_to_pt(15),
            overlap_y=mm_to_pt(15),
            orientation="portrait",
        )
        mosaic = MosaicBuilder(
            page_width=mm_to_pt(386),
            page_height=mm_to_pt(590),
            paper=self.paper,
            settings=settings,
        ).build()

        self.assertEqual(mosaic.columns, 3)
        self.assertEqual(mosaic.rows, 3)

        a1 = mosaic.get_tile(0, 0)
        self.assertEqual(a1.code, "A1")
        self.assertEqual(a1.neighbor_right, "A2")
        self.assertEqual(a1.neighbor_bottom, "B1")
        self.assertIsNone(a1.neighbor_left)
        self.assertAlmostEqual(pt_to_mm(a1.overlap_right), 15.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a1.overlap_bottom), 15.0, places=4)

        a2 = mosaic.get_tile(0, 1)
        self.assertAlmostEqual(pt_to_mm(a2.x), 185.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a2.width), 200.0, places=4)
        self.assertEqual(a2.neighbor_left, "A1")
        self.assertEqual(a2.neighbor_right, "A3")

        a3 = mosaic.get_tile(0, 2)
        self.assertAlmostEqual(pt_to_mm(a3.x), 370.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a3.width), 16.0, places=4)
        self.assertEqual(a3.overlap_right, 0.0)
        self.assertIsNone(a3.neighbor_right)

    def test_auto_orientation_chooses_fewer_sheets(self) -> None:
        # Plano horizontal 290 x 190 mm:
        # En portrait (200x300 útil) necesita 2 hojas; en landscape (300x200 útil) cabe en 1 hoja!
        settings = MosaicSettings(printer_profile=self.profile, orientation="auto")
        mosaic = MosaicBuilder(
            page_width=mm_to_pt(290),
            page_height=mm_to_pt(190),
            paper=self.paper,
            settings=settings,
        ).build()
        self.assertEqual(len(mosaic), 1)
        self.assertTrue(mosaic.paper.is_landscape)

    def test_center_alignment_splits_artwork_evenly(self) -> None:
        settings = MosaicSettings(
            printer_profile=self.profile,
            overlap_x=mm_to_pt(20),
            overlap_y=0.0,
            orientation="portrait",
            alignment="center",
        )
        # Área útil 200mm, paso 180mm. 2 columnas cubren 380mm.
        # Diseño de 300mm centrado: art_x0 = (380 - 300)/2 = 40mm
        mosaic = MosaicBuilder(
            page_width=mm_to_pt(300),
            page_height=mm_to_pt(250),
            paper=self.paper,
            settings=settings,
        ).build()
        self.assertEqual(mosaic.columns, 2)
        a1 = mosaic.get_tile(0, 0)
        a2 = mosaic.get_tile(0, 1)
        self.assertAlmostEqual(pt_to_mm(a1.dest_offset_x), 40.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a1.width), 160.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a1.overlap_right), 20.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a2.x), 140.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a2.width), 160.0, places=4)
        self.assertAlmostEqual(pt_to_mm(a2.dest_offset_x), 0.0, places=4)

    def test_traversal_orders_and_json_export(self) -> None:
        settings = MosaicSettings(
            printer_profile=self.profile,
            orientation="portrait",
            traversal_order="snake",
        )
        mosaic = MosaicBuilder(
            page_width=mm_to_pt(350),
            page_height=mm_to_pt(500),
            paper=self.paper,
            settings=settings,
        ).build()
        self.assertEqual([t.code for t in mosaic.ordered_tiles("row-major")], ["A1", "A2", "B1", "B2"])
        self.assertEqual([t.code for t in mosaic.ordered_tiles("col-major")], ["A1", "B1", "A2", "B2"])
        self.assertEqual([t.code for t in mosaic.ordered_tiles("snake")], ["A1", "A2", "B2", "B1"])

        data = mosaic.to_dict()
        self.assertEqual(data["grid"]["total_sheets"], 4)
        self.assertEqual(len(data["tiles"]), 4)
        self.assertEqual(data["tiles"][2]["code"], "B2")


if __name__ == "__main__":
    unittest.main()
