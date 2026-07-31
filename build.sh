#!/usr/bin/env bash
# build.sh
#
# Reempaqueta `casiopea-wiki/` como `casiopea-wiki.plugin`, un zip listo para
# instalar en Claude Cowork con doble clic o arrastrandolo al chat.
#
# Antes de empaquetar valida lo que suele romperse en silencio: que los
# manifiestos sean JSON valido y que los scripts compilen. Un plugin que
# instala pero no arranca cuesta mas de diagnosticar que uno que no instala.
#
# Uso:
#   ./build.sh
#
# El .plugin generado esta en .gitignore: es artefacto, no fuente.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/casiopea-wiki"
OUT="$ROOT/casiopea-wiki.plugin"

if [ ! -d "$SRC" ]; then
  echo "ERROR: no existe $SRC" >&2
  exit 1
fi

echo "validando manifiestos..."
for f in "$SRC/.claude-plugin/plugin.json" "$SRC/.mcp.json" \
         "$ROOT/.claude-plugin/marketplace.json"; do
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" \
    || { echo "ERROR: JSON invalido en $f" >&2; exit 1; }
  echo "  ok  ${f#$ROOT/}"
done

echo "validando scripts..."
for f in "$SRC"/skills/casiopea/scripts/*.py; do
  python3 -m py_compile "$f" \
    || { echo "ERROR: no compila $f" >&2; exit 1; }
  echo "  ok  ${f#$ROOT/}"
done
find "$SRC" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "comprobando que el .plugin no lleve secretos..."
if find "$SRC" -name "credentials" -not -name "*.example" | grep -q .; then
  echo "ERROR: hay un archivo 'credentials' dentro de casiopea-wiki/." >&2
  echo "       Las credenciales van FUERA del plugin. Sacalo antes de empaquetar." >&2
  exit 1
fi

rm -f "$OUT"
cd "$SRC"
zip -r "$OUT" . \
  -x "*.DS_Store" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.old" \
  > /dev/null

echo "OK: $OUT ($(du -h "$OUT" | cut -f1), $(unzip -l "$OUT" | tail -1 | awk '{print $2}') archivos)"
