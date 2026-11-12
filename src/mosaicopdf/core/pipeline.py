"""
Orquestador de alto nivel del flujo Leer -> Escalar -> Calcular -> Exportar.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mosaicopdf.core.mosaic_builder import MosaicBuilder
from mosaicopdf.core.pdf_exporter import PdfExporter
from mosaicopdf.core.pdf_reader import PDFReader
from mosaicopdf.core.scaler import ScaleCalculator
from mosaicopdf.models.document import PageInfo
from mosaicopdf.models.mosaic import Mosaic
from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.scale_spec import ScaleSpec
from mosaicopdf.utils.output_filename import build_output_filename


@dataclass(frozen=True, slots=True)
class JobResult:
    """Resultado completo de procesar un documento PDF en MosaicoPDF."""

    input_file: Path
    output_file: Path
    json_file: Path | None
    mosaics: tuple[tuple[int, Mosaic], ...]

    @property
    def total_output_pages(self) -> int:
        total = 0
        for _, mosaic in self.mosaics:
            total += len(mosaic) + (1 if mosaic.settings.cover_map else 0)
        return total


def parse_page_selection(spec: str, page_count: int) -> list[int]:
    """
    Convierte una selección de páginas tipo ``"1"``, ``"1,3-5"`` o ``"all"``
    a índices base 0 ordenados y sin duplicados.
    """
    cleaned = spec.strip().lower()
    if cleaned in ("all", "todas", "*"):
        return list(range(page_count))

    selected: list[int] = []
    seen: set[int] = set()
    for part in cleaned.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            bounds = token.split("-", 1)
            start = int(bounds[0].strip())
            end = int(bounds[1].strip())
            if start < 1 or end > page_count or start > end:
                raise ValueError(
                    f"Rango de páginas inválido '{token}' (el PDF tiene {page_count} páginas)."
                )
            for p in range(start - 1, end):
                if p not in seen:
                    seen.add(p)
                    selected.append(p)
        else:
            num = int(token)
            if num < 1 or num > page_count:
                raise ValueError(
                    f"Página {num} fuera de rango (el PDF tiene {page_count} páginas)."
                )
            idx = num - 1
            if idx not in seen:
                seen.add(idx)
                selected.append(idx)

    if not selected:
        raise ValueError("Debes seleccionar al menos una página.")
    return selected


def plan_page_mosaic(
    page_info: PageInfo,
    paper: Paper,
    settings: MosaicSettings,
    scale_spec: ScaleSpec,
) -> Mosaic:
    """Calcula el ``Mosaic`` para una página sin necesidad de escribir en disco."""
    scale_result = ScaleCalculator.calculate(
        source_width=page_info.width,
        source_height=page_info.height,
        spec=scale_spec,
        paper=paper,
        settings=settings,
    )
    builder = MosaicBuilder(
        page_width=scale_result.virtual_width,
        page_height=scale_result.virtual_height,
        paper=paper,
        settings=settings,
        scale_result=scale_result,
    )
    return builder.build()


def run_mosaic_job(
    input_file: str | Path,
    paper: Paper,
    settings: MosaicSettings,
    scale_spec: ScaleSpec | None = None,
    output_file: str | Path | None = None,
    page_selection: str = "1",
    export_json: bool = False,
) -> JobResult:
    """
    Ejecuta el flujo completo de MosaicoPDF sobre un archivo en disco.
    """
    in_path = Path(input_file)
    if not in_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {in_path}")
    if in_path.suffix.lower() != ".pdf":
        raise ValueError("El archivo de entrada debe tener extensión .pdf")

    out_path = (
        Path(output_file)
        if output_file is not None
        else build_output_filename(in_path)
    )
    effective_scale = scale_spec or ScaleSpec()

    with PDFReader(str(in_path)) as reader:
        indices = parse_page_selection(page_selection, reader.page_count)
        items: list[tuple[int, Mosaic, tuple[float, float]]] = []

        for idx in indices:
            info = reader.page_info(idx)
            mosaic = plan_page_mosaic(
                page_info=info,
                paper=paper,
                settings=settings,
                scale_spec=effective_scale,
            )
            items.append((idx, mosaic, (info.origin_x, info.origin_y)))

        exporter = PdfExporter(reader.document)
        exporter.export_many(
            items=items,
            output_filename=out_path,
            source_filename=in_path.name,
        )

    mosaics_summary = tuple((idx, mosaic) for idx, mosaic, _ in items)
    json_path: Path | None = None
    if export_json:
        json_path = out_path.with_suffix(".json")
        PdfExporter.export_assembly_json(
            items=list(mosaics_summary),
            json_filename=json_path,
            source_filename=str(in_path),
            output_pdf=str(out_path),
        )

    return JobResult(
        input_file=in_path,
        output_file=out_path,
        json_file=json_path,
        mosaics=mosaics_summary,
    )
