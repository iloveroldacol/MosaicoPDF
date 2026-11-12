# Manual de Usuario — MosaicoPDF 2.0

MosaicoPDF es una herramienta libre y de código abierto escrita en Python para **dividir y escalar documentos PDF manteniendo el 100% de su calidad vectorial** (sin convertir planos ni dibujos en imágenes rasterizadas).

Está pensada especialmente para **arquitectura, diseño técnico, cartografía, pósteres y muralismo**.

---

## 1. ¿Qué puedes hacer con la versión 2.0?

- **Dividir planos grandes (1:1):** toma un PDF de gran formato (A0, A1, planos CAD, etc.) y repártelo en hojas estándar (Carta, Oficio, A4, A3, Tabloide o medidas personalizadas) a escala exacta.
- **Efecto inverso (pequeño → gran formato / mural):** toma un diseño en Carta, A4 o menor y amplíalo vectorialmente a un formato grande (ej. `A0`, `150x100cm`) o a una cuadrícula exacta de hojas (ej. `4x3` hojas) para armarlo como mural.
- **Perfiles de impresora y márgenes en mm:** define márgenes iguales o distintos por cada lado (`arriba, derecha, abajo, izquierda`) y guárdalos como perfiles reutilizables.
- **Solapas con guías de armado:** añade franjas de pegado indicando explícitamente **con qué pieza contigua se une** (`SOLAPA 12.0mm -> UNIR CON A2`), marcas de corte en esquinas, brújula de vecinos y una **página inicial de mapa visual**.
- **Organización flexible:** orientación automática (para gastar menos hojas), centrado simétrico para murales y orden por filas, columnas o serpentina (zig-zag).
- **Integración con Inkscape y clic derecho en Linux.**

---

## 2. Instalación sin complicaciones (Windows, macOS y Linux)

No necesitas saber usar entornos virtuales (`venv`) ni instalar librerías manualmente: MosaicoPDF 2.0 gestiona su propio entorno aislado interno.

### Opción A: Instaladores automáticos de 1 paso (recomendado)

- **En Windows:**
  1. Descarga o clona el proyecto.
  2. Haz **doble clic** en `installers\instalar_windows.bat`.
  3. El instalador verifica Python 3.10+ (si falta intenta instalarlo con `winget`), configura `PyMuPDF` automáticamente, crea un acceso directo **`MosaicoPDF 2.0`** en el Escritorio, agrega menú clic derecho en PDFs y registra la extensión en Inkscape.

- **En Linux y macOS:**
  ```bash
  git clone https://github.com/iloveroldacol/MosaicoPDF.git
  cd MosaicoPDF
  ./installers/instalar_linux_mac.sh
  ```
  Esto crea el entorno interno aislado (sin afectar el Python del sistema), instala `mosaicopdf` + `PyMuPDF`, deja listo el comando `mosaicopdf`, configura Inkscape y (en Linux) registra el clic derecho o (en macOS) crea un acceso directo ejecutable en el Escritorio.

### Opción B: Auto-instalación de PyMuPDF desde la app
Si ya ejecutaste MosaicoPDF pero falta `PyMuPDF`, al iniciar el asistente o ejecutar un comando te preguntará si deseas instalarlo automáticamente, o puedes correr:
```bash
mosaicopdf doctor --instalar
```

### Opción C: Ejecutable autocontenido (sin Python)
Para distribuir binarios independientes (`mosaicopdf.exe`, `mosaicopdf-macos`, `mosaicopdf-linux`) donde el usuario final ni siquiera necesite tener Python instalado:
```bash
pip install pyinstaller
python3 installers/build_executable.py
```
El repositorio incluye además un flujo automático en `.github/workflows/build-and-release.yml` para generar los ejecutables en los 3 sistemas operativos al crear un tag `v*` en GitHub.

### Opción D: Instalación manual para desarrolladores
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Verifica en cualquier caso:
```bash
mosaicopdf doctor
```

---

## 3. Modo Asistente ASCII Interactivo (recomendado para empezar)

Si ejecutas `mosaicopdf` sin parámetros (o pasando un archivo con `-i`):

```bash
mosaicopdf
```

o directamente sobre un archivo:

```bash
mosaicopdf mi_plano.pdf --interactivo
```

Se abrirá un menú ASCII paso a paso donde podrás:
1. Elegir el PDF y las páginas a procesar.
2. Seleccionar el modo de escala (`1:1`, porcentaje, gran formato o cuadrícula mural).
3. Elegir papel, orientación, alineación y orden de impresión.
4. Elegir o personalizar los márgenes de tu impresora en `mm`.
5. Configurar solapas, marcas de corte, guías de armado y mapa inicial.
6. **Ver la vista previa ASCII en terminal** con medidas reales y total de hojas antes de exportar.

---

## 4. Uso directo por línea de comandos (CLI)

### Sintaxis compatible con v1.0
```bash
mosaicopdf plano.pdf carta
```

### Ejemplos prácticos de arquitectura (escala 1:1)

Dividir un plano en **Carta** con margen de **8 mm**, solapa de **12 mm**, marcas de corte y página mapa inicial:
```bash
mosaicopdf plano.pdf --papel carta --margen 8mm --solapa 12mm --mapa
```

Usar orientación horizontal forzada, márgenes distintos (`sup,der,inf,izq`) y exportar también JSON de ensamblaje:
```bash
mosaicopdf plano.pdf --papel a4 --orientacion horizontal --margen 5,5,12,5mm --solapa 15mm --json
```

Simular sin crear archivo (solo ver el mapa ASCII y cálculo de hojas):
```bash
mosaicopdf plano.pdf --papel oficio --solapa 10mm --simular
```

---

## 5. Efecto inverso: escalar de tamaño pequeño a gran formato o mural

Cuando partes de un boceto en `A4` o `Carta` y quieres imprimirlo en tamaño mural manteniendo líneas y textos 100% vectoriales:

### Opción A: Escalar a un formato grande estándar (`A0`, `A1`, `A2`, `ARCH D`, etc.)
```bash
mosaicopdf boceto_a4.pdf --escalar-a a0 --papel carta --solapa 15mm --centrar --mapa
```

### Opción B: Escalar a medidas personalizadas exactas
```bash
mosaicopdf ilustracion.pdf --escalar-a 180x120cm --papel a4 --solapa 15mm --alineacion centrado --mapa
```
*(También puedes indicar solo ancho `--ancho-objetivo 1500mm` o solo alto `--alto-objetivo 1000mm`, manteniendo siempre la proporción).*

### Opción C: Escalar por porcentaje
```bash
mosaicopdf lamina.pdf --escala 300% --papel carta --solapa 12mm --mapa
```

### Opción D: Ajustar a una cuadrícula exacta de hojas (`--cuadricula COLxFIL`)
Si ya sabes exactamente cuántas hojas de ancho y alto caben en tu pared (por ejemplo **4 columnas × 3 filas** en papel Carta):
```bash
mosaicopdf mural.pdf --cuadricula 4x3 --papel carta --solapa 15mm --alineacion centrado --orden serpentina --mapa
```

---

## 6. Perfiles de impresora (márgenes persistentes)

Puedes ver los perfiles incluidos y los tuyos con:
```bash
mosaicopdf perfiles listar
```

Perfiles integrados:
- `estandar`: 5 mm en los 4 lados.
- `segura`: 10 mm en los 4 lados.
- `amplia`: 12.7 mm en los 4 lados.
- `sin-bordes`: 0 mm.

Crear y guardar un perfil para tu impresora real (por ejemplo con margen inferior de 14 mm por el rodillo):
```bash
mosaicopdf perfiles crear mi-epson --margen 5,5,14,5mm --descripcion "Epson L3250 taller"
```

Usarlo al generar un mosaico:
```bash
mosaicopdf plano.pdf --perfil mi-epson --papel carta --solapa 12mm
```

Eliminar un perfil personalizado:
```bash
mosaicopdf perfiles eliminar mi-epson
```

Los perfiles se guardan en `~/.config/mosaicopdf/printers.json`.

---

## 7. Cómo leer las solapas y guías de armado al imprimir

Cuando activas solapas (`--solapa 12mm`) y guías (activas por defecto):

1. **Página 1 (si usas `--mapa`):** muestra el plano completo en miniatura con las divisiones `A1`, `A2`, `B1`, `B2` y el número de hoja impresa (`#1`, `#2`, ...).
2. **Encabezado de cada hoja:** indica el código de pieza, su posición fila-columna y sus vecinas directas:
   `[A1] Hoja 1/6 | F1-C1 | Der:A2 Inf:B1 | Escala 100%`
3. **Franja azul suave de solapa:** aparece en el borde derecho (si existe hoja a la derecha) y en el borde inferior (si existe hoja abajo) con:
   - Una línea discontinua de referencia y triángulo de alineación (`▶` / `▼`).
   - El texto explícito de unión: **`SOLAPA 12.0mm -> UNIR CON A2`** o **`SOLAPA 12.0mm v UNIR CON B1`**.
4. **Consejo de montaje mural:** recorta siguiendo las marcas de esquina de la pieza que va *encima* (`A2`) y apóyala sobre la franja sombreada de `A1` haciendo coincidir las líneas del dibujo y el triángulo de registro.

---

## 8. Integración con Inkscape

MosaicoPDF 2.0 incluye una extensión oficial para Inkscape. Para instalarla automáticamente:

```bash
mosaicopdf integrar --inkscape
```

Luego:
1. Reinicia **Inkscape**.
2. Abre o diseña tu plano o mural en SVG.
3. Ve al menú: **`Extensiones -> Exportar -> MosaicoPDF 2.0 (Dividir y Escalar)`**.
4. Configura papel, escala (incluyendo efecto inverso a `A0` o cuadrícula `3x2`), márgenes, solapa y carpeta de salida.
5. Haz clic en **Aplicar**: Inkscape exportará internamente a PDF vectorial y MosaicoPDF creará el archivo `*_mosaico.pdf` sin perder calidad.

---

## 9. Integración con clic derecho en Linux

Para abrir cualquier PDF directamente desde tu explorador de archivos con clic derecho:

```bash
mosaicopdf integrar --linux
```

Esto instala:
- **`~/.local/bin/mosaicopdf-rightclick`**: abre tu terminal directamente en el asistente ASCII con el PDF seleccionado.
- **Entrada "Abrir con -> MosaicoPDF 2.0"** (`~/.local/share/applications/mosaicopdf.desktop`) compatible con GNOME Files/Nautilus, Nemo, Caja, KDE, XFCE y otros escritorios.
- **Scripts contextuales** en Nautilus / Nemo / Caja (`Clic derecho -> Scripts -> MosaicoPDF 2.0`) y ServiceMenu para KDE Dolphin.
- Para **XFCE Thunar**, puedes copiar la acción XML ubicada en `src/mosaicopdf/integrations/linux/mosaicopdf-thunar-uca.xml` dentro de `~/.config/Thunar/uca.xml`.

*(Para instalar Inkscape y Linux a la vez, ejecuta simplemente `mosaicopdf integrar --todo`)*.

---

## 10. Referencia rápida de opciones CLI

| Opción | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `-i, --interactivo` | Inicia el asistente ASCII | `mosaicopdf plano.pdf -i` |
| `-p, --papel` | Papel destino o `ANCHOxALTOmm` | `--papel carta` / `--papel 215x280mm` |
| `--perfil` | Perfil de impresora guardado | `--perfil mi-epson` |
| `--margen` | Márgenes en `mm` (1, 2 o 4 valores) | `--margen 8mm` / `--margen 5,5,12,5mm` |
| `--solapa` | Solapa uniforme X e Y (mm por defecto) | `--solapa 15mm` |
| `--solapa-x` / `--solapa-y` | Solapa independiente por eje | `--solapa-x 15mm --solapa-y 10mm` |
| `--orientacion` | `auto`, `vertical`, `horizontal` | `--orientacion auto` |
| `--alineacion` | `top-left` o `centrado` | `--alineacion centrado` |
| `--orden` | `filas`, `columnas` o `serpentina` | `--orden serpentina` |
| `--escala` | Factor o porcentaje | `--escala 250%` |
| `--escalar-a` | Gran formato o medida mural | `--escalar-a a0` / `--escalar-a 180x120cm` |
| `--cuadricula` | Ajustar proporcionalmente a `COLxFIL` | `--cuadricula 4x3` |
| `--paginas` | Selección de páginas | `--paginas 1,3-5` / `--paginas all` |
| `--sin-marcas` | Oculta marcas de corte | `--sin-marcas` |
| `--sin-guias` | Oculta rótulos y textos de solapa | `--sin-guias` |
| `--mapa` | Añade página 1 con mapa visual | `--mapa` |
| `--json` | Guarda mapa en `.json` | `--json` |
| `--simular` | Vista previa ASCII sin escribir PDF | `--simular` |

---

## 11. Solución de problemas

- **`PyMuPDF (fitz) no está instalado`**: asegúrate de instalar las dependencias dentro de tu entorno (`pip install PyMuPDF` o `pip install -e .`).
- **La extensión no aparece en Inkscape**: reinicia Inkscape por completo y verifica que existen `mosaicopdf.inx` y `mosaicopdf_inkscape.py` en `~/.config/inkscape/extensions/` (o en la ruta Snap/Flatpak si usas Inkscape empaquetado).
- **La impresora recorta el borde de la página**: aumenta el margen en `--margen` o crea un perfil con `--margen 10mm` o márgenes asimétricos para esa impresora.
