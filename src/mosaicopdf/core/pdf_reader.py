import fitz


class PDFReader:
    """
    Clase encargada de abrir e inspeccionar documentos PDF.
    """

    def __init__(self, filename: str):
        """
        Abre el documento PDF.
        """
        self.filename = filename
        self.document = fitz.open(filename)

    @property
    def page_count(self) -> int:
        """
        Devuelve el número de páginas del documento.
        """
        return self.document.page_count

    def page_size(self, page_number: int = 0) -> tuple[float, float]:
        """
        Devuelve el tamaño de una página en puntos PDF.

        Parameters
        ----------
        page_number : int
            Número de página (por defecto la primera).

        Returns
        -------
        tuple[float, float]
            (ancho, alto)
        """
        page = self.document.load_page(page_number)
        rect = page.rect
        return rect.width, rect.height

    def first_page_size(self) -> tuple[float, float]:
        """
        Devuelve el tamaño de la primera página.
        """
        return self.page_size(0)

    def page_orientation(self, page_number: int = 0) -> str:
        """
        Devuelve la orientación de una página.
        """
        width, height = self.page_size(page_number)

        if width >= height:
            return "Horizontal"

        return "Vertical"

    def info(self) -> None:
        """
        Imprime un resumen del documento.
        """
        print(f"Archivo : {self.filename}")
        print(f"Páginas : {self.page_count}")

        for page_number in range(self.page_count):

            width, height = self.page_size(page_number)

            orientation = self.page_orientation(page_number)

            print(
                f"Página {page_number + 1}: "
                f"{width:.2f} × {height:.2f} pt "
                f"({orientation})"
            )

    def close(self) -> None:
        """
        Cierra el documento PDF.
        """
        self.document.close()