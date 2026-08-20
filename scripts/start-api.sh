#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example - edit HP URLs before use."
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

API_DIR="$ROOT/services/api"
cd "$API_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -e .

cd "$ROOT"
export CONFIG_DIR="$ROOT/config"
mkdir -p "$ROOT/data"

# Optional: ./scripts/start-api.sh --build  or  BUILD_DASHBOARD=1 ./scripts/start-api.sh
if [ "${1:-}" = "--build" ] || [ "${BUILD_DASHBOARD:-0}" = "1" ]; then
  "$ROOT/scripts/build-dashboard.sh"
fi

if [ -f "$ROOT/dashboard/dist/index.html" ]; then
  echo "Dashboard: http://0.0.0.0:8000  (served from dashboard/dist)"
else
  echo "Dashboard: not built yet - run ./scripts/build-dashboard.sh for phone/LAN single-port UI"
  echo "           or use: cd dashboard && npm run dev  (http://localhost:5173)"
fi

echo "API docs: http://0.0.0.0:8000/docs"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir "$API_DIR"
