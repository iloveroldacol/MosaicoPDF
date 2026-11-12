# ADR-0002: Motor Vectorial Proporcional, Escalado Inverso y Geometría de Solapas (v2.0)

**Estado:** Aceptado  
**Fecha:** Noviembre de 2026  

---

## 1. Contexto

En la versión 1.0 (ver [ADR.txt](ADR.txt), nota `ADR-001`), se observó durante pruebas tempranas en `sandbox/test_clip.py` que `fitz.Page.show_pdf_page()` reescalaba el contenido del `clip` cuando el rectángulo destino tenía el tamaño completo de la página física mientras el `clip` de la última columna era más angosto.

Además, la versión 2.0 introduce dos requisitos fundamentales:

1. **Efecto inverso (escalado a gran formato):** partir de un PDF pequeño (Carta, Oficio, A4 o menor), escalarlo a gran formato personalizado o a una cuadrícula mural, y dividirlo conservando la nitidez vectorial.
2. **Márgenes personalizados, solapas y centrado:** posicionar cada fragmento dentro del área imprimible real de la impresora sin deformar la escala.

---

## 2. Decisiones técnicas

### 2.1 Renderizado vectorial exacto con `show_pdf_page`

El problema observado en la Beta se debía a que `destino` medía toda la hoja mientras `clip` medía solo el remanente de la última fila o columna. En MosaicoPDF 2.0 se formaliza en `PDFRenderer.compute_rects()` la invariante matemática:

```
clip_origen = origen_pagina + (tile_virtual / scale_factor)
rect_destino = (margen_izq + offset_x, margen_sup + offset_y) + tamaño(tile_virtual)
```

Dado que `rect_destino.width / clip_origen.width == scale_factor` y `rect_destino.height / clip_origen.height == scale_factor` en ambos ejes (con `keep_proportion=True`), PyMuPDF incrusta el fragmento como un **XObject PDF vectorial** con escala uniforme exacta, sin rasterizar y sin estirar filas o columnas periféricas. Adicionalmente, sumar `origen_pagina` (`page.rect.x0, page.rect.y0`) garantiza compatibilidad con PDFs generados por CAD cuyo origen no está en `(0, 0)`.

### 2.2 Desacoplamiento del escalado previo (`ScaleCalculator`)

En lugar de mezclar factores de escala dentro de `MosaicBuilder`, el flujo sigue el modelo:

```
PDF origen (w0, h0)
  └─> ScaleCalculator ─> Plano virtual escalado (w0 * s, h0 * s)
        └─> MosaicBuilder ─> Cuadrícula de Tiles con solapas y alineación
              └─> PDFRenderer ─> Recorte (tile / s) -> Destino (tile)
```

Esto permite soportar de manera uniforme cinco modos de escala (`original`, `factor/%`, `target_size`, `target_width`, `target_height` y `grid` mural `COLxFIL`).

### 2.3 Geometría unificada de solapas (`overlap`) y centrado

Con área imprimible `(printable_w, printable_h)` y solapas `(overlap_x, overlap_y)`, el paso efectivo entre hojas es:

```
step_x = printable_w - overlap_x
step_y = printable_h - overlap_y
```

El número de columnas se calcula como `1` si `page_width <= printable_w + EPS`, y `1 + ceil((page_width - printable_w - EPS) / step_x)` en caso contrario (análogo para filas). La tolerancia `EPS = 1e-4 pt` evita hojas fantasma por redondeo entre milímetros y puntos PDF.

Cada `Tile` se calcula mediante intersección entre la ventana de la hoja `[c * step_x, c * step_x + printable_w]` y la caja del diseño `[art_x0, art_x0 + page_width]`, permitiendo tanto alineación `top-left` (planos técnicos) como `center` (murales simétricos) con la misma fórmula exacta.

---

## 3. Consecuencias

- Se conserva el **100% de la geometría vectorial** tanto al dividir planos grandes (1:1 o reducidos) como al ampliar diseños pequeños a escala mural.
- La geometría de recorte y destino queda aislada en funciones puras fácilmente auditables y verificables con pruebas unitarias sin depender de la interfaz gráfica.
