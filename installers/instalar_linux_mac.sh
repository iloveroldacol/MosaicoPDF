#!/usr/bin/env bash
# Instalador guiado sin dependencias previas de entorno virtual para Linux y macOS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OS_NAME="$(uname -s)"

echo "============================================================"
echo "  Instalador MosaicoPDF 2.0 ($OS_NAME)"
echo "============================================================"
echo

PYTHON_BIN=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PYTHON_BIN="$(command -v "$cand")"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "[ERR] Se requiere Python 3.10 o superior."
    if [ "$OS_NAME" = "Darwin" ]; then
        echo "      Instalalo desde https://www.python.org/downloads/macos/ o con: brew install python"
    else
        echo "      Instalalo con: sudo apt install python3 python3-venv python3-pip"
    fi
    exit 1
fi

if [ "$OS_NAME" = "Darwin" ]; then
    APP_DIR="$HOME/Library/Application Support/MosaicoPDF"
else
    APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mosaicopdf"
fi

VENV_DIR="$APP_DIR/venv"
BIN_DIR="$HOME/.local/bin"

echo "[INFO] Python detectado : $PYTHON_BIN"
echo "[INFO] Entorno interno  : $VENV_DIR"

mkdir -p "$APP_DIR" "$BIN_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "[INFO] Instalando MosaicoPDF 2.0 y PyMuPDF (sin tocar el Python del sistema)..."
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --upgrade pip >/dev/null
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --upgrade "$REPO_ROOT"

cat > "$BIN_DIR/mosaicopdf" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/mosaicopdf" "\$@"
EOF
chmod +x "$BIN_DIR/mosaicopdf"

echo "[ OK ] Comando instalado en: $BIN_DIR/mosaicopdf"

# Instalar extension de Inkscape (y clic derecho en Linux)
"$VENV_DIR/bin/mosaicopdf" integrar --inkscape || true
if [ "$OS_NAME" = "Linux" ]; then
    "$VENV_DIR/bin/mosaicopdf" integrar --linux || true
elif [ "$OS_NAME" = "Darwin" ] && [ -d "$HOME/Desktop" ]; then
    MAC_CMD="$HOME/Desktop/MosaicoPDF 2.0.command"
    cat > "$MAC_CMD" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/mosaicopdf" --interactivo
EOF
    chmod +x "$MAC_CMD"
    echo "[ OK ] Acceso directo en Escritorio: $MAC_CMD"
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo
    echo "[WARN] '$BIN_DIR' no esta en tu PATH actual."
    echo "       Agrega esta linea a tu ~/.bashrc o ~/.zshrc:"
    echo "       export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo
echo "[ OK ] Instalacion completada. Ejecuta: mosaicopdf"
