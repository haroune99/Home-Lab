# Home Lab

A private two-node local LLM home lab with a control plane API, metrics dashboard, and flexible inference routing across your Mac and HP laptop.

## Architecture

```
iPhone / browser ──(LAN or Tailscale)──► Mac :8000 (API + dashboard)
                                              ├── mac  → Ollama
                                              ├── hp   → Ollama
                                              └── air  → llama-server (Wi-Fi only)
```

Both Ollama nodes (Mac, HP) and the Air (`llama.cpp`) are **peer inference targets**. Route manually or use **Auto**.

## Prerequisites

- **Mac:** Python 3.11+, Ollama running, Node.js 18+ (to build the dashboard)
- **HP:** Python 3.11+, Ollama running, reachable on LAN
- **Optional:** Tailscale on Mac + iPhone (+ HP) for access away from home

## Quick start

### 1. Configure

```bash
cp .env.example .env
# Edit .env — set HP_OLLAMA_URL and HP_AGENT_URL to your HP's LAN IP
```

### 2. Build dashboard + start API (Mac)

```bash
./scripts/build-dashboard.sh   # once, or after UI changes
./scripts/start-api.sh         # serves API + dashboard on :8000
```

Or build on start: `./scripts/start-api.sh --build`

| URL | What |
|---|---|
| http://localhost:8000 | Dashboard + API (phone/LAN ready) |
| http://localhost:8000/docs | OpenAPI docs |
| http://localhost:5173 | Vite dev only (`cd dashboard && npm run dev`) |

### 3. Start agent (HP — PowerShell)

Manual (dev):

```powershell
.\scripts\start-agent.ps1
```

Autostart at Windows logon (recommended):

```powershell
.\scripts\install-agent-task.ps1 -Setup
```

See [HP agent autostart](#hp-agent-autostart) below.

### 4. Pull models

```bash
./scripts/pull-models.sh
```

Or use the **Models** page in the dashboard.

## iPhone access (home Wi-Fi + away)

### A. Same Wi-Fi

1. Mac API running with `API_HOST=0.0.0.0` (default in `.env`).
2. Find Mac LAN IP: System Settings → Network, or `ipconfig getifaddr en0`.
3. On iPhone Safari: `http://<mac-lan-ip>:8000`
4. Add to Home Screen (Share → Add to Home Screen) for an app-like icon.

Ensure the dashboard was built (`./scripts/build-dashboard.sh`) so `:8000` serves the UI.

### B. Away from home — Tailscale (recommended)

Do **not** port-forward 8000 on your router. Use Tailscale.

1. Create an account at [tailscale.com](https://tailscale.com).
2. Install Tailscale on **Mac**, **iPhone**, and optionally **HP**.
3. Sign in with the same account on each device.
4. On Mac, open the Tailscale menu → copy the Mac’s Tailscale IP (`100.x.x.x`).
5. On iPhone (cellular or other Wi-Fi), open Safari: `http://100.x.x.x:8000`

**Away-from-home checklist:**

- [ ] Tailscale connected on iPhone and Mac
- [ ] Mac awake (lid open / “Prevent automatic sleeping” while on power)
- [ ] `./scripts/start-api.sh` running (dashboard built)
- [ ] HP on if you need HP models (agent + Ollama)

Optional: put the Mac’s Tailscale IP in Notes or a Shortcut for one tap.

### C. iOS Shortcuts — “Ask Home Lab”

1. Open **Shortcuts** → New Shortcut.
2. Add **Ask for Input** (Text) → save as `Prompt`.
3. Add **Get Contents of URL**:
   - URL: `http://100.x.x.x:8000/api/v1/inference` (or Mac LAN IP at home)
   - Method: **POST**
   - Headers: `Content-Type` = `application/json`
   - Request Body: **JSON**
   ```json
   {
     "model": "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:latest",
     "prompt": "REPLACE_WITH_SHORTCUT_INPUT",
     "node": "auto"
   }
   ```
   In Shortcuts, use the **Prompt** variable for the `prompt` field instead of a fixed string.
4. Add **Get Dictionary from Input** → get value for key `response`.
5. Add **Show Result** (or **Speak Text**).

**Force HP / Mac:** set `"node": "hp"` or `"node": "mac"`.

**Tip:** Duplicate the Shortcut for “Ask HP” vs “Ask Mac” with different `node` values.

### Security note

The API has **no login**. That is fine on a private Tailscale network and home LAN. Do not expose port 8000 to the public internet. Add a shared token later if you invite others.

## LAN setup checklist (HP)

1. **Ollama listens on LAN** — on Windows, set `OLLAMA_HOST=0.0.0.0` and restart Ollama.

2. **Windows Firewall** — allow inbound TCP `11434` (Ollama) and `8001` (agent).

3. **Verify from Mac:**
   ```bash
   curl http://<hp-ip>:11434/api/tags
   curl http://<hp-ip>:8001/health
   ```

4. **Fixed IP recommended** — reserve the HP’s LAN IP on your router.

5. **Agent autostart** — see below.

## MacBook Air node (llama.cpp)

Old Intel MacBook Air (High Sierra) — **Wi-Fi only** (no Tailscale). Uses `llama-server`, not Ollama.

### Start on the Air

**Terminal 1 — llama-server:**

```bash
cd ~/Downloads/llama.cpp/build/bin
./llama-server -m /Users/harouneaaffoute/tinyllama-q4.gguf --host 0.0.0.0 --port 8080
```

**Terminal 2 — metrics agent (CPU/RAM, same as HP):**

Copy/sync the Home-Lab repo onto the Air, then:

```bash
cd /path/to/Home-Lab
chmod +x scripts/start-agent-air.sh
./scripts/start-agent-air.sh
```

Agent listens on **port 8002**. Set in Mac `.env`:

```bash
AIR_LLAMA_URL=http://192.168.1.143:8080
AIR_AGENT_URL=http://192.168.1.143:8002
```

Leave both windows open. Default lab URL: `http://192.168.1.143:8080` (update `.env` if the IP changes).

### Verify from Mac M2

```bash
curl http://192.168.1.143:8080/health
curl http://192.168.1.143:8002/health
curl http://192.168.1.143:8002/metrics
```

Then in the dashboard: Overview should show **MacBook Air (Intel)** online with RAM/CPU. Playground → node **Air** → run a short prompt.

### Notes

- Load GGUF models manually on the Air (dashboard pull is Mac/HP Ollama only).
- Keep models small (3B–7B Q4) on 8GB RAM.
- Air must stay on the same home Wi-Fi as the M2.

## HP agent autostart

Registers a Startup-folder launcher (and optionally a Scheduled Task) so the metrics agent starts at logon.

### One-time install (on HP)

1. Open **PowerShell** in the Home-Lab repo on the HP (admin not required).
2. Run:

```powershell
.\scripts\install-agent-task.ps1 -Setup
```

Optional delay (default 60s for Ollama):

```powershell
.\scripts\install-agent-task.ps1 -DelaySeconds 90 -Setup
```

### Verify

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-agent.ps1
# other window:
curl http://127.0.0.1:8001/health
Get-Content $env:LOCALAPPDATA\HomeLab\logs\agent.log -Tail 20
```

From the **Mac:** `curl http://<hp-ip>:8001/health`

### Uninstall

```powershell
.\scripts\uninstall-agent-task.ps1
```

## Dashboard pages

| Page | Purpose |
|---|---|
| **Overview** | Fleet status, requests today, avg latency/tokens/sec |
| **Nodes** | Per-node CPU/RAM, Ollama version, loaded model |
| **Models** | Models installed on Mac vs HP, pull new models |
| **Playground** | Interactive inference — pick node + model or Auto |
| **Inference** | History log, tokens/sec charts, filter by node |

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | API health |
| GET | `/api/v1/nodes` | Mac + HP status |
| GET | `/api/v1/models` | Models per node |
| GET | `/api/v1/models/available` | Model names grouped by node |
| POST | `/api/v1/models/pull` | Pull model to a node |
| POST | `/api/v1/inference` | Run inference (`node`: mac, hp, or auto) |
| POST | `/api/v1/inference/preview` | Dry-run auto routing |
| GET | `/api/v1/metrics/summary` | Fleet metrics summary |
| GET | `/api/v1/metrics/inference` | Inference history |
| GET | `/api/v1/metrics/timeseries` | Chart data |

## Routing

Edit [`config/models.yaml`](config/models.yaml) for `preferred_node` hints and `also_on`.

**Auto routing** scores: model installed, RAM headroom, preferred node, historical tokens/sec.

## Project structure

```
config/           — nodes.yaml, models.yaml
services/api/     — FastAPI control plane (Mac)
services/agent/   — HP metrics sidecar
dashboard/        — React UI (build → dist, served by API)
scripts/          — start-api.sh, build-dashboard.sh, agent scripts, pull-models.sh
data/             — SQLite DB (gitignored)
```

## Ready for projects

1. Call `POST /api/v1/inference` with `{ model, prompt, node }`
2. Metrics are logged automatically
3. Phone clients use the same API over LAN or Tailscale

## Optional next steps

- **Mac API autostart** (`launchd`) — so reboot does not kill remote access
- **API token** — if you share Tailscale access with others
- First app: pantry/grocery, document vault, or voice → tasks

## Hardware reference

| Device | Role |
|---|---|
| Mac M2 Pro 16GB | Orchestrator + fast inference + phone front door |
| HP Ultra 7 32GB | Heavy / peer inference |
| MacBook Air Intel 8GB | Small models via llama.cpp (Wi-Fi only) |
| iPhone | Client (Safari dashboard + Shortcuts) |

See [`Claude-stategy.md`](Claude-stategy.md) for experiment ideas and content strategy.
