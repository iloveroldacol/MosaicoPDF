███╗   ███╗ ██████╗ ███████╗ █████╗ ██╗ ██████╗ ██████╗ ██████╗ ██████╗ ███████╗
████╗ ████║██╔═══██╗██╔════╝██╔══██╗██║██╔════╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝
██╔████╔██║██║   ██║███████╗███████║██║██║     ██║   ██║██████╔╝██║  ██║█████╗  
██║╚██╔╝██║██║   ██║╚════██║██╔══██║██║██║     ██║   ██║██╔═══╝ ██║  ██║██╔══╝  
██║ ╚═╝ ██║╚██████╔╝███████║██║  ██║██║╚██████╗╚██████╔╝██║     ██████╔╝██║     
╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═════╝ ╚═╝

+---------------------------------------------+
|                                             |
|            M O S A I C O P D F              |
|                                             |
+---------------------------------------------+
| Versión: 1.0 (Estable)                      |
| Autor: Fabian Andreison España Vélez        |
| Año: 2026                                   |
+---------------------------------------------+
|                                             |
|   +-----------+-----------+-----------+     |
|   |   A1      |   A2      |   A3      |     |
|   +-----------+-----------+-----------+     |
|   |   B1      |   B2      |   B3      |     |
|   +-----------+-----------+-----------+     |
|   |   C1      |   C2      |   C3      |     |
|   +-----------+-----------+-----------+     |
|                                             |
+---------------------------------------------+
|                                             |
|       Hecho con orgullo en Colombia         |
|                                             |
+---------------------------------------------+

# MosaicoPDF

MosaicoPDF es una herramienta CLI (línea de comandos) libre y de código abierto escrita en Python para dividir documentos PDF vectoriales de gran formato en múltiples hojas imprimibles estándar (Carta, Oficio, A4, etc.), conservando la escala 1:1 y la calidad vectorial original del documento sin rasterizar el contenido.

Está orientada a la impresión de planos técnicos, dibujos CAD, mapas, pósteres y material didáctico universitario que exceda el tamaño del papel disponible en impresoras convencionales.

## ✨ Características de la Versión 1.0

- 📐 **Conservación Vectorial Absoluta:** No transforma el PDF en imágenes; el documento resultante mantiene la nitidez vectorial original de sus trazos y textos.
- 📏 **Matriz Dinámica Anti-Estiramiento:** El motor matemático calcula de forma exacta los remanentes del plano en las últimas filas y columnas, evitando deformaciones de escala.
- 🗺️ **Diagrama de Ensamblaje Visual:** Genera un croquis ASCII detallado en la terminal para comprender la disposición de las hojas impresas.
- 🚀 **Instalación Moderna:** Arquitectura limpia basada en la distribución estándar de Python (`pyproject.toml`).

## 🛠️ Requisitos previos

- **Python 3.10** o superior.
- Librería **PyMuPDF (fitz)** para la manipulación y renderizado eficiente del PDF.

## 📦 Instalación (Modo Desarrollo)

Para clonar este repositorio de forma local y comenzar a trabajar en él o integrarlo en tus herramientas:

1. Clona el repositorio:
   ```bash
   git clone [https://github.com/TU_USUARIO/MosaicoPDF.git](https://github.com/TU_USUARIO/MosaicoPDF.git)
   cd MosaicoPDF