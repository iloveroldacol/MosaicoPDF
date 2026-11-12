#!/usr/bin/env bash
# Lanzador de clic derecho para MosaicoPDF 2.0 en escritorios Linux.
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Uso: $0 <archivo.pdf>" >&2
    exit 1
fi

PDF_FILE="$1"
MOSAIC_BIN="${MOSAICOPDF_BIN:-mosaicopdf}"
PYTHON_BIN="${MOSAICOPDF_PYTHON:-python3}"

if command -v "$MOSAIC_BIN" >/dev/null 2>&1; then
    CMD_PREFIX="\"$MOSAIC_BIN\""
else
    CMD_PREFIX="\"$PYTHON_BIN\" -m mosaicopdf"
fi

RUN_CMD="$CMD_PREFIX \"$PDF_FILE\" --interactivo; echo; read -r -p 'Presiona Enter para cerrar...' _"

if command -v gnome-terminal >/dev/null 2>&1; then
    exec gnome-terminal -- bash -lc "$RUN_CMD"
elif command -v konsole >/dev/null 2>&1; then
    exec konsole -e bash -lc "$RUN_CMD"
elif command -v xfce4-terminal >/dev/null 2>&1; then
    exec xfce4-terminal -x bash -lc "$RUN_CMD"
elif command -v mate-terminal >/dev/null 2>&1; then
    exec mate-terminal -e "bash -lc '$RUN_CMD'"
elif command -v tilix >/dev/null 2>&1; then
    exec tilix -e "bash -lc '$RUN_CMD'"
elif command -v kitty >/dev/null 2>&1; then
    exec kitty bash -lc "$RUN_CMD"
elif command -v alacritty >/dev/null 2>&1; then
    exec alacritty -e bash -lc "$RUN_CMD"
elif command -v x-terminal-emulator >/dev/null 2>&1; then
    exec x-terminal-emulator -e bash -lc "$RUN_CMD"
else
    exec xterm -e bash -lc "$RUN_CMD"
fi
