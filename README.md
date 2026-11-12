```text
███╗   ███╗ ██████╗ ███████╗ █████╗ ██╗ ██████╗ ██████╗ ██████╗ ██████╗ ███████╗
████╗ ████║██╔═══██╗██╔════╝██╔══██╗██║██╔════╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝
██╔████╔██║██║   ██║███████╗███████║██║██║     ██║   ██║██████╔╝██║  ██║█████╗  
██║╚██╔╝██║██║   ██║╚════██║██╔══██║██║██║     ██║   ██║██╔═══╝ ██║  ██║██╔══╝  
██║ ╚═╝ ██║╚██████╔╝███████║██║  ██║██║╚██████╗╚██████╔╝██║     ██████╔╝██║     
╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═════╝ ╚═╝

+---------------------------------------------+
|            M O S A I C O P D F              |
+---------------------------------------------+
| Versión: 2.0.0                              |
| Autor: Fabian Andreison España Vélez        |
| Hecho con orgullo en Colombia               |
+---------------------------------------------+
```

# MosaicoPDF 2.0

**MosaicoPDF** es una herramienta libre y de código abierto escrita en Python para dividir y escalar documentos PDF **conservando el 100% de su calidad vectorial** (sin rasterizar líneas ni textos), lista para imprimir en hojas convencionales de oficina (Carta, Oficio, A4, A3, Tabloide o medidas personalizadas).

Está diseñada para **planos de arquitectura, dibujos CAD, cartografía, pósteres y proyectos de muralismo**.

---

## ✨ Novedades y características de la Versión 2.0

- **Conservación Vectorial Absoluta:** tanto al dividir un plano grande (1:1) como al ampliar un diseño pequeño, el PDF resultante mantiene sus trazos y tipografía vectoriales intactos.
- **Efecto Inverso (Pequeño → Gran Formato / Mural):** escala un PDF pequeño (Carta, Oficio, A4) a `A0`, `A1`, medidas personalizadas (`180x120cm`) o a una cuadrícula exacta de hojas (`4x3`) y genera el mosaico imprimible listo para armar.
- **Unidades en Milímetros (`mm`) y Perfiles de Impresora:** márgenes personalizables por lado (`sup,der,inf,izq`) y perfiles reutilizables guardados en `~/.config/mosaicopdf/printers.json`.
- **Solapas con Guías de Armado para Muralismo:** marcas de corte en esquinas, franjas de pegado con líneas de registro y rótulos explícitos indicando la pieza contigua (`SOLAPA 12.0mm -> UNIR CON A2`, `SOLAPA 12.0mm v UNIR CON B1`), más **página inicial de mapa visual** (`--mapa`) y JSON de ensamblaje (`--json`).
- **Organización Inteligente del Mosaico:** orientación `auto` (elige vertical u horizontal para gastar menos hojas), alineación `top-left` o `centrado`, orden `filas`, `columnas` o `serpentina`, y soporte multipágina.
- **CLI Dual con Entorno ASCII Amigable:** asistente interactivo ASCII en terminal (ejecutando `mosaicopdf` sin argumentos o con `-i`) y modo directo por comandos.
- **Integración Nativa con Inkscape y Clic Derecho en Linux:** extensión oficial en `Extensiones -> Exportar -> MosaicoPDF 2.0` y menú contextual para exploradores de archivos Linux.

---

## 🛠️ Instalación fácil (Windows, macOS y Linux)

Pensado para diseñadores, arquitectos y muralistas **sin necesidad de saber crear entornos virtuales ni instalar librerías manualmente**:

- **Windows:** descarga o clona el repositorio y haz **doble clic** en [instalar_windows.bat](installers/instalar_windows.bat) (instala Python si falta con `winget`, configura `PyMuPDF`, crea acceso directo en el Escritorio, registra clic derecho en PDFs e instala la extensión de Inkscape).
- **Linux y macOS:** ejecuta en una terminal:
  ```bash
  ./installers/instalar_linux_mac.sh
  ```
- **Auto-reparación desde la app:** si ejecutas `mosaicopdf` y falta `PyMuPDF`, la propia herramienta ofrece instalarlo en su entorno interno aislado (`mosaicopdf doctor --instalar`).
- **Ejecutable sin Python:** puedes compilar un binario autocontenido con `python3 installers/build_executable.py` (o publicarlo automáticamente por etiqueta `v*` en GitHub Releases).

---

## 🚀 Uso rápido

### 1. Asistente ASCII interactivo
```bash
mosaicopdf
```

### 2. Dividir un plano de arquitectura (escala 1:1) con solapas y guías
```bash
mosaicopdf plano.pdf --papel carta --margen 8mm --solapa 12mm --mapa
```

### 3. Efecto inverso: ampliar un diseño A4 a mural A0 (o 180x120cm)
```bash
mosaicopdf boceto_a4.pdf --escalar-a a0 --papel carta --solapa 15mm --centrar --mapa
mosaicopdf mural.pdf --cuadricula 4x3 --papel carta --solapa 15mm --orden serpentina --mapa
```

### 4. Gestionar perfiles de impresora e integraciones
```bash
mosaicopdf perfiles listar
mosaicopdf perfiles crear mi-epson --margen 5,5,14,5mm --descripcion "Epson taller"
mosaicopdf integrar --todo
```

---

## 📖 Documentación y Arquitectura

- **[Manual de Usuario Completo](docs/MANUAL_USUARIO.md)**: guía paso a paso de todas las funciones, ejemplos de muralismo, Inkscape y clic derecho en Linux.
- **[Decisiones de Arquitectura (ADR)](ADR/)**:
  - [ADR-0001 (v1.0)](ADR/ADR.txt)
  - [ADR-0002: Motor vectorial, escalado inverso y geometría de solapas](ADR/ADR-0002-motor-vectorial-y-escalado-v2.md)
  - [ADR-0003: Perfiles, guías de armado e integraciones](ADR/ADR-0003-perfiles-guias-ensamblaje-e-integraciones.md)

---

## 🧪 Pruebas

```bash
python3 -m unittest discover -s tests -v
```

---

## 📄 Licencia

Distribuido bajo licencia MIT. Consulta [LICENSE](LICENSE) para más detalles.
