#!/usr/bin/env bash
#
# Genera la carpeta deploy/ a partir de backend/static/
#
# Netlify ejecuta este script automáticamente en cada push.
# También puedes correrlo a mano:  bash scripts/build-deploy.sh
#
# ⚠️  Nunca edites archivos dentro de deploy/ — este script los sobrescribe.
#     El original está siempre en backend/static/

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/backend/static"
OUT="$ROOT/deploy"

echo "Generando deploy/ desde backend/static/ …"

rm -rf "$OUT"
mkdir -p "$OUT/app"

# La landing es la página de entrada del sitio
cp "$SRC/landing.html" "$OUT/index.html"

# Las páginas van bajo /app/ para conservar los enlaces internos existentes
cp "$SRC/index.html"       "$OUT/app/index.html"
cp "$SRC/landing.html"     "$OUT/app/landing.html"
cp "$SRC/empathy-map.html" "$OUT/app/empathy-map.html"
cp "$SRC/journey-map.html" "$OUT/app/journey-map.html"

# vendor va en la raíz porque los <script> lo piden como /vendor/…
cp -R "$SRC/vendor" "$OUT/vendor"

echo "✅ deploy/ generado — $(find "$OUT" -type f | wc -l | tr -d ' ') archivos"
