#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ROOT
cd "$ROOT"

if [ ! -f .env ]; then
  echo "Missing .env — copy .env.example and set HP_OLLAMA_URL."
  exit 1
fi

# shellcheck disable=SC1091
source .env

pull_to_node() {
  local node_name="$1"
  local url="$2"
  local model="$3"
  echo "Pulling $model on $node_name ($url)..."
  curl -sf -X POST "$url/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$model\", \"stream\": false}" \
    && echo "  OK" || echo "  FAILED"
}

# Parse models.yaml with python
python3 << 'PY'
import yaml
import os
import subprocess

root = os.environ.get("ROOT", ".")
with open(os.path.join(root, "config/models.yaml")) as f:
    cfg = yaml.safe_load(f)

mac_url = os.environ.get("MAC_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
hp_url = os.environ.get("HP_OLLAMA_URL", "").rstrip("/")

def pull(url, model):
    print(f"Pulling {model} -> {url}")
    r = subprocess.run(
        ["curl", "-sf", "-X", "POST", f"{url}/api/pull",
         "-H", "Content-Type: application/json",
         "-d", f'{{"name": "{model}", "stream": false}}'],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        print(f"  OK: {model}")
    else:
        print(f"  FAILED: {model} — {r.stderr}")

for entry in cfg.get("models", []):
    name = entry["name"]
    preferred = entry.get("preferred_node", "mac")
    also_on = entry.get("also_on", [])

    targets = {preferred} | set(also_on)
    for node in targets:
        url = mac_url if node == "mac" else hp_url
        if url:
            pull(url, name)
PY

echo "Done."
