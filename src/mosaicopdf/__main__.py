import sys
from pathlib import Path

from mosaicopdf.config.papers import get_paper
from mosaicopdf.core.mosaic_builder import MosaicBuilder
from mosaicopdf.core.pdf_exporter import PdfExporter
from mosaicopdf.core.pdf_reader import PDFReader

from mosaicopdf.utils.console import (
    header,
    info,
    ok,
    error,
    print_ascii_mosaic,
    print_summary,
)

from mosaicopdf.utils.output_filename import build_output_filename


def main() -> int:
    """
    Punto de entrada de MosaicoPDF.
    """

    header()

    # ---------------------------------------------------------
    # Validar argumentos
    # ---------------------------------------------------------

    if len(sys.argv) != 3:
        error("Uso:")
        print("    mosaicopdf <archivo.pdf> <carta|oficio|a4>")
        return 1

    input_file = sys.argv[1]
    paper_name = sys.argv[2]

    # ---------------------------------------------------------
    # Validar archivo
    # ---------------------------------------------------------

    input_path = Path(input_file)

    if not input_path.exists():
        error(f"No existe el archivo:\n{input_path}")
        return 1

    if input_path.suffix.lower() != ".pdf":
        error("El archivo debe tener extensión .pdf")
        return 1

    # ---------------------------------------------------------
    # Papel
    # ---------------------------------------------------------

    try:
        paper = get_paper(paper_name)
    except ValueError as exc:
        error(str(exc))
        return 1

    output_file = build_output_filename(input_file)

    # ---------------------------------------------------------
    # Leer PDF
    # ---------------------------------------------------------

    info("Leyendo PDF...")

    reader = PDFReader(str(input_path))

    page_width, page_height = reader.first_page_size()

    # ---------------------------------------------------------
    # Construir mosaico
    # ---------------------------------------------------------

    info("Calculando mosaico...")

    builder = MosaicBuilder(
        page_width,
        page_height,
        paper,
    )

    mosaic = builder.build()

    # ---------------------------------------------------------
    # Exportar
    # ---------------------------------------------------------

    info("Exportando PDF...")

    exporter = PdfExporter(reader.document)

    exporter.export(
        mosaic,
        str(output_file),
    )

    reader.close()

    # ---------------------------------------------------------
    # Resumen
    # ---------------------------------------------------------

    print_ascii_mosaic(
        mosaic.rows,
        mosaic.columns,
    )

    print_summary(
        input_file=str(input_path),
        output_file=str(output_file),
        paper_name=paper.name,
        rows=mosaic.rows,
        columns=mosaic.columns,
    )

    ok("Proceso terminado correctamente.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())