#!/usr/bin/env bash
# build.sh
#
# Reempaqueta `casiopea-wiki/` como `casiopea-wiki.plugin` (un zip listo para
# instalar en Claude Cowork con doble clic o arrastre al chat).
#
# Uso:
#   ./build.sh
#
# El .plugin generado esta en .gitignore: es un artefacto de build, no fuente.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/casiopea-wiki"
OUT="$ROOT/casiopea-wiki.plugin"

if [ ! -d "$SRC" ]; then
  echo "ERROR: no existe $SRC" >&2
  exit 1
fi

rm -f "$OUT"

cd "$SRC"
zip -r "$OUT" . \
  -x "*.DS_Store" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  > /dev/null

echo "OK: $OUT ($(du -h "$OUT" | cut -f1))"
