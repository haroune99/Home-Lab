#!/usr/bin/env bash
# Start Home Lab metrics agent on the MacBook Air (Intel / High Sierra).
# Run this ON the Air, with the Home-Lab repo available locally or via shared copy.
#
# Usage (from repo root on the Air):
#   ./scripts/start-agent-air.sh
#
# Requires: llama-server already running on :8080 for loaded-model reporting (optional).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_DIR="$ROOT/services/agent"
PORT="${AGENT_PORT:-8002}"
LLAMA_URL="${LLAMA_URL:-http://127.0.0.1:8080}"

cd "$AGENT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -e .

export LLAMA_URL
echo "Starting Home Lab Agent (Air) on http://0.0.0.0:${PORT}"
echo "  LLAMA_URL=$LLAMA_URL"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
