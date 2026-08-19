#!/usr/bin/env bash

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== TwinLight ==="

# ── Liberar puertos si quedaron ocupados ─────────────────────────────────────
echo "[0/3] Liberando puertos 8000 y 5173 si están en uso..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1

# ── Backend ──────────────────────────────────────────────────────────────────
echo "[1/3] Instalando dependencias del backend..."
cd "$ROOT/backend"
python3 -m pip install -r requirements.txt -q

echo "[2/3] Iniciando backend en http://localhost:8000 ..."
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────────────────────────────────────
echo "[3/3] Iniciando frontend React..."
cd "$ROOT/frontend"

if ! command -v npm &>/dev/null; then
  echo ""
  echo "  ERROR: npm no encontrado. Instala Node.js primero:"
  echo "  brew install node"
  echo ""
  kill $BACKEND_PID 2>/dev/null
  exit 1
fi

npm install -q
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  ✅ Backend:  http://localhost:8000"
echo "  ✅ Frontend: http://localhost:5173"
echo "  ✅ API docs: http://localhost:8000/docs"
echo ""
echo "  Abre en el navegador: http://localhost:5173"
echo ""
echo "  Presiona Ctrl+C para detener ambos servidores."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
