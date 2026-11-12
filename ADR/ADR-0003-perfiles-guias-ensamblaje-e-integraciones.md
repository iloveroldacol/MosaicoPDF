# ADR-0003: Perfiles de Impresora, Guías de Armado para Muralismo e Integraciones (v2.0)

**Estado:** Aceptado  
**Fecha:** Noviembre de 2026  

---

## 1. Contexto

Al llevar MosaicoPDF de una prueba funcional a una herramienta de uso real en arquitectura y muralismo surgen cuatro necesidades operativas:

1. Trabajar en **milímetros (mm)** por defecto en lugar de puntos PDF.
2. Guardar márgenes reales por impresora para no reconfigurarlos en cada trabajo.
3. Identificar sin ambigüedad cómo se unen las hojas físicas al armar mosaicos grandes.
4. Invocar la herramienta desde **Inkscape** y desde el **menú contextual (clic derecho)** en Linux manteniendo una CLI amigable sin dependencias pesadas.

---

## 2. Decisiones

### 2.1 Unidades en milímetros con conversión transparente

`mosaicopdf.utils.units` adopta `mm` como unidad por defecto y acepta sufijos explícitos (`mm`, `cm`, `m`, `in`/`pulg`, `pt`). Todas las dimensiones internas siguen expresándose en puntos PDF (`1 in = 72 pt`) para operar nativamente sobre el sistema de coordenadas PDF.

### 2.2 Perfiles de impresora persistentes (`PrinterStore`)

Se incorporan perfiles integrados (`estandar` 5 mm, `segura` 10 mm, `amplia` 12.7 mm, `sin-bordes` 0 mm) y almacenamiento en JSON en `$XDG_CONFIG_HOME/mosaicopdf/printers.json` (por defecto `~/.config/mosaicopdf/printers.json`), con márgenes independientes por lado (`top`, `right`, `bottom`, `left`) serializados en milímetros para fácil lectura humana.

### 2.3 Guías vectoriales de corte y armado con referencia a pieza contigua

`GuideDrawer` dibuja elementos vectoriales opcionales sobre cada hoja:

- **Marcas de corte:** escuadras en las esquinas y recuadro discontinuo del recorte.
- **Franjas de solapa identificadas:** sombreado suave en la zona de traslape, línea discontinua de corte/alineación, triángulo de registro y texto explícito indicando la pieza vecina (`SOLAPA 12.0mm -> UNIR CON A2` y `SOLAPA 12.0mm v UNIR CON B1`).
- **Rótulo de pieza:** código de cuadrícula (`A1`, `B2`), número de hoja y brújula de vecinas (`Sup`, `Izq`, `Der`, `Inf`).
- **Página mapa opcional (`--mapa`):** primera hoja resumen con miniatura vectorial del diseño completo, cuadrícula numerada y dimensiones reales.
- **JSON de ensamblaje (`--json`):** exportación estructurada con coordenadas en milímetros y vecindad de cada hoja.

### 2.4 CLI dual (Directa + Asistente ASCII) e integraciones libres

- **Sin dependencias externas de UI:** se mantiene únicamente `PyMuPDF` como dependencia de ejecución. La interfaz terminal usa ASCII puro (`+---+`, `|`, `---`) con color ANSI opcional automático en TTY (`NO_COLOR` respetado).
- **Modo dual:** `mosaicopdf` sin argumentos o con `--interactivo` lanza un asistente ASCII paso a paso con previsualización del mosaico; con argumentos funciona de forma directa para scripts e integraciones.
- **Inkscape:** extensión nativa (`mosaicopdf.inx` + `mosaicopdf_inkscape.py`) que exporta el SVG activo a PDF vectorial mediante `inkscape --export-type=pdf` y lo procesa con `run_mosaic_job`. Si el Python embebido de Inkscape carece de `PyMuPDF` (común en Windows/macOS), la extensión delega automáticamente vía subproceso al entorno gestionado de MosaicoPDF.
- **Linux clic derecho:** lanzador `mosaicopdf-rightclick`, entrada estándar `.desktop` (`MimeType=application/pdf;`) y scripts para Nautilus/Nemo/Caja/Dolphin/Thunar instalados mediante `mosaicopdf integrar`.
- **Instalación sin fricción multiplataforma:** `mosaicopdf.runtime` gestiona automáticamente un entorno aislado de usuario (`%LOCALAPPDATA%\MosaicoPDF\venv` en Windows, `~/Library/Application Support/MosaicoPDF/venv` en macOS y `~/.local/share/mosaicopdf/venv` en Linux) junto con `mosaicopdf doctor --instalar`, instaladores de 1 paso (`installers/`) y empaquetado opcional en binario único con PyInstaller.

---

## 3. Consecuencias

- El código permanece modular, auditable y sin acoplamiento entre lógica matemática, renderizado PDF e interfaz de usuario.
- La extensión de Inkscape y el menú contextual de escritorio reutilizan exactamente el mismo motor que la CLI.
