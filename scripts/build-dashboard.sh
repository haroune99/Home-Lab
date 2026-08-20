#!/usr/bin/env bash
# Build the React dashboard into dashboard/dist for serving from the API.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/dashboard"

if [ ! -d node_modules ]; then
  npm install
fi

npm run build
echo "Dashboard built: $ROOT/dashboard/dist"
echo "Restart the API (./scripts/start-api.sh) then open http://localhost:8000"
