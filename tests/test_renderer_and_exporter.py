import json
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mosaicopdf.core.guide_drawer import GuideDrawer
from mosaicopdf.core.mosaic_builder import MosaicBuilder
from mosaicopdf.core.pdf_exporter import PdfExporter
from mosaicopdf.core.pdf_renderer import PDFRenderer
from mosaicopdf.core.scaler import ScaleCalculator
from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.printer_profile import PrinterProfile
from mosaicopdf.models.scale_spec import ScaleSpec
from mosaicopdf.utils.units import mm_to_pt, pt_to_mm


class _FakePoint:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class _FakeRect:
    def __init__(self, x0: float, y0: float, x1: float, y1: float):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.width = x1 - x0
        self.height = y1 - y0


class _FakeShape:
    def __init__(self) -> None:
        self.lines = 0
        self.rects = 0
        self.polylines = 0
        self.committed = False

    def draw_line(self, p1, p2) -> None:
        self.lines += 1

    def draw_rect(self, rect) -> None:
        self.rects += 1

    def draw_polyline(self, pts) -> None:
        self.polylines += 1

    def finish(self, **kwargs) -> None:
        pass

    def commit(self) -> None:
        self.committed = True


class _FakePage:
    def __init__(self, width: float, height: float):
        self.rect = _FakeRect(0.0, 0.0, width, height)
        self.texts: list[tuple[str, int]] = []
        self.shapes: list[_FakeShape] = []
        self.shown: list[tuple[object, object, int]] = []

    def new_shape(self) -> _FakeShape:
        s = _FakeShape()
        self.shapes.append(s)
        return s

    def insert_text(self, point, text: str, **kwargs) -> None:
        self.texts.append((text, int(kwargs.get("rotate", 0))))

    def show_pdf_page(self, rect, doc, pno, **kwargs) -> None:
        self.shown.append((rect, doc, pno))


class _FakeFitz:
    Point = _FakePoint
    Rect = _FakeRect


class TestRendererAndExporter(unittest.TestCase):
    def test_compute_rects_with_reverse_scale_and_origin(self) -> None:
        paper = Paper("Test", width=mm_to_pt(220), height=mm_to_pt(320))
        profile = PrinterProfile(
            name="m10",
            margin_top=mm_to_pt(10),
            margin_right=mm_to_pt(10),
            margin_bottom=mm_to_pt(10),
            margin_left=mm_to_pt(10),
        )
        settings = MosaicSettings(
            printer_profile=profile,
            overlap_x=mm_to_pt(15),
            overlap_y=mm_to_pt(15),
            orientation="portrait",
        )
        # Origen pequeño 100 x 150 mm escalado 4x -> virtual 400 x 600 mm
        scale_res = ScaleCalculator.calculate(
            mm_to_pt(100), mm_to_pt(150), ScaleSpec(mode="factor", factor=4.0)
        )
        mosaic = MosaicBuilder(
            scale_res.virtual_width,
            scale_res.virtual_height,
            paper=paper,
            settings=settings,
            scale_result=scale_res,
        ).build()

        renderer = PDFRenderer(source_document=object())
        tile_a2 = mosaic.get_tile(0, 1)
        src_coords, dest_coords = renderer.compute_rects(
            tile=tile_a2,
            mosaic=mosaic,
            source_origin=(mm_to_pt(5), mm_to_pt(7)),
        )

        # tile_a2.x = 185mm virtual / 4.0 = 46.25mm + 5mm origin = 51.25mm
        self.assertAlmostEqual(pt_to_mm(src_coords[0]), 51.25, places=4)
        self.assertAlmostEqual(pt_to_mm(src_coords[1]), 7.0, places=4)
        # Proporción destino / origen debe ser exactamente 4.0x
        dest_w = dest_coords[2] - dest_coords[0]
        src_w = src_coords[2] - src_coords[0]
        self.assertAlmostEqual(dest_w / src_w, 4.0, places=5)
        # Margen izquierdo aplicado en destino
        self.assertAlmostEqual(pt_to_mm(dest_coords[0]), 10.0, places=4)
        self.assertAlmostEqual(pt_to_mm(dest_coords[1]), 10.0, places=4)

    def test_guide_drawer_draws_neighbor_overlap_labels_and_cover_map(self) -> None:
        paper = Paper("Test", width=mm_to_pt(220), height=mm_to_pt(320))
        profile = PrinterProfile("m10", mm_to_pt(10), mm_to_pt(10), mm_to_pt(10), mm_to_pt(10))
        settings = MosaicSettings(
            printer_profile=profile,
            overlap_x=mm_to_pt(15),
            overlap_y=mm_to_pt(15),
            orientation="portrait",
            cut_marks=True,
            assembly_guides=True,
            cover_map=True,
        )
        mosaic = MosaicBuilder(mm_to_pt(350), mm_to_pt(500), paper, settings).build()
        drawer = GuideDrawer()
        fake_page = _FakePage(paper.width, paper.height)
        a1 = mosaic.get_tile(0, 0)
        dest_rect = _FakeRect(
            mm_to_pt(10),
            mm_to_pt(10),
            mm_to_pt(10) + a1.width,
            mm_to_pt(10) + a1.height,
        )
        drawer.draw_tile_guides(_FakeFitz, fake_page, a1, mosaic, dest_rect, page_index=0)

        rendered_texts = [t for t, _ in fake_page.texts]
        self.assertTrue(any("UNIR CON A2" in t for t in rendered_texts))
        self.assertTrue(any("UNIR CON B1" in t for t in rendered_texts))
        self.assertTrue(any("[A1] Hoja 1/4" in t for t in rendered_texts))
        self.assertTrue(any(s.committed for s in fake_page.shapes))

        map_page = _FakePage(paper.width, paper.height)
        drawer.draw_cover_map_page(_FakeFitz, map_page, mosaic, object(), 0, "mural.pdf")
        map_texts = [t for t, _ in map_page.texts]
        self.assertTrue(any("Mapa de Ensamblaje" in t for t in map_texts))
        self.assertTrue(any("A1 (#1)" in t for t in map_texts))
        self.assertEqual(len(map_page.shown), 1)

    def test_export_assembly_json(self) -> None:
        paper = Paper("Test", width=mm_to_pt(220), height=mm_to_pt(320))
        profile = PrinterProfile("m10", mm_to_pt(10), mm_to_pt(10), mm_to_pt(10), mm_to_pt(10))
        settings = MosaicSettings(printer_profile=profile, overlap_x=mm_to_pt(12))
        mosaic = MosaicBuilder(mm_to_pt(300), mm_to_pt(250), paper, settings).build()

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "salida.json"
            PdfExporter.export_assembly_json(
                items=[(0, mosaic)],
                json_filename=json_path,
                source_filename="plano.pdf",
                output_pdf="salida.pdf",
            )
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["mosaicopdf_version"], "2.0.0")
            self.assertEqual(payload["pages"][0]["source_page"], 1)
            self.assertEqual(payload["pages"][0]["mosaic"]["tiles"][0]["code"], "A1")


if __name__ == "__main__":
    unittest.main()
