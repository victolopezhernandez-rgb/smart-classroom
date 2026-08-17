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

# Las capturas del gemelo se piden con ruta relativa (img/…), y la landing
# queda publicada en dos sitios, así que la carpeta va en los dos.
cp -R "$SRC/img" "$OUT/img"
cp -R "$SRC/img" "$OUT/app/img"

# GitHub Pages publica el sitio bajo /smart-classroom/, no en la raíz del
# dominio, así que las rutas absolutas (/vendor/…, /app/…) darían 404. Con
# BASE_PATH se les antepone el prefijo — pero solo en la copia publicada,
# para que backend/static/ siga funcionando en la raíz cuando corres local.
#
#   BASE_PATH=/smart-classroom/ bash scripts/build-deploy.sh
#
# Las rutas /api/ no se tocan: el gemelo ya las manda al backend de Render.
BASE_PATH="${BASE_PATH:-/}"
if [ "$BASE_PATH" != "/" ]; then
  find "$OUT" -name '*.html' -print0 \
    | xargs -0 perl -pi -e "s{(\"|')/(vendor|app)/}{\$1${BASE_PATH}\$2/}g"
  echo "   rutas reescritas con prefijo $BASE_PATH"
fi

echo "✅ deploy/ generado — $(find "$OUT" -type f | wc -l | tr -d ' ') archivos"
