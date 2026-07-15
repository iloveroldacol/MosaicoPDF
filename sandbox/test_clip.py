import fitz

# Abrir el PDF original
src = fitz.open("examples/plano.pdf")

# Crear un PDF nuevo
dst = fitz.open()

# Tomar la primera página
page = src[0]

# Crear una página Carta
new_page = dst.new_page(width=612, height=792)

# Definir la región que queremos copiar
clip = fitz.Rect(
    0,
    0,
    612,
    792,
)

# Copiar esa región a la nueva página
new_page.show_pdf_page(
    new_page.rect,
    src,
    0,
    clip=clip,
)

# Guardar resultado
dst.save("output/A1.pdf")

dst.close()
src.close()

print("A1.pdf generado correctamente.")