#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit HP URLs before use."
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

echo "Starting Home Lab API on http://0.0.0.0:8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir "$API_DIR"
