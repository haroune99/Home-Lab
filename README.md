# Home Lab

A private two-node local LLM home lab with a control plane API, metrics dashboard, and flexible inference routing across your Mac and HP laptop.

## Architecture

```
Browser (React dashboard :5173)
        │
        ▼
Mac — FastAPI control plane (:8000)
   ├── Ollama (:11434) — fast inference
   ├── SQLite metrics
   └── proxies to ──► HP — Ollama (:11434) + Agent (:8001)
```

Both nodes are **peer inference targets**. Route manually (pick Mac or HP + model) or use **Auto** mode and let the orchestrator score nodes by RAM headroom, preferred node, and historical tokens/sec.

## Prerequisites

- **Mac:** Python 3.11+, Ollama running
- **HP:** Python 3.11+, Ollama running, reachable on LAN
- **Both:** Node.js 18+ (for dashboard)

## Quick start

### 1. Configure

```bash
cp .env.example .env
# Edit .env — set HP_OLLAMA_URL and HP_AGENT_URL to your HP's LAN IP
```

### 2. Start API (Mac)

```bash
./scripts/start-api.sh
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

### 3. Start agent (HP — PowerShell)

Manual (dev):

```powershell
.\scripts\start-agent.ps1
```

Autostart at Windows logon (recommended):

```powershell
# From the Home-Lab repo on the HP — run once
.\scripts\install-agent-task.ps1 -Setup
```

See [HP agent autostart](#hp-agent-autostart) below.

### 4. Start dashboard (Mac)

```bash
cd dashboard
npm install
npm run dev
```

Dashboard: http://localhost:5173

### 5. Pull models

```bash
./scripts/pull-models.sh
```

Or pull from the **Models** page in the dashboard.

## LAN setup checklist (HP)

1. **Ollama listens on LAN** — ensure Ollama accepts connections beyond localhost. On Windows, set `OLLAMA_HOST=0.0.0.0` in environment variables and restart Ollama.

2. **Windows Firewall** — allow inbound TCP on ports `11434` (Ollama) and `8001` (agent).

3. **Verify from Mac:**
   ```bash
   curl http://<hp-ip>:11434/api/tags
   curl http://<hp-ip>:8001/health
   ```

4. **Fixed IP recommended** — assign a static LAN IP to the HP so `.env` doesn't break.

5. **Agent autostart** — see below so the HP stays online after reboot.

## HP agent autostart

Registers a Windows Scheduled Task (`HomeLab-Agent`) that starts the metrics agent at logon (with a delay so Ollama can come up first).

### One-time install (on HP)

1. Open **PowerShell** in the Home-Lab repo folder on the HP (normal user is fine — admin not required).
2. Run:

```powershell
.\scripts\install-agent-task.ps1 -Setup
```

This installs:
- A **Startup folder** launcher (primary — no admin)
- A **Scheduled Task** if Windows allows it (optional bonus)

If the repo is elsewhere:

```powershell
.\scripts\install-agent-task.ps1 -RepoPath "C:\Users\YourName\Home-Lab" -Setup
```

Optional: change the post-logon delay (default 60 seconds, waits inside the agent script so Ollama can start first):

```powershell
.\scripts\install-agent-task.ps1 -DelaySeconds 90 -Setup
```

### Verify

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-agent.ps1
# In another PowerShell window:
curl http://127.0.0.1:8001/health
Get-Content $env:LOCALAPPDATA\HomeLab\logs\agent.log -Tail 20
```

From the **Mac**:

```bash
curl http://<hp-ip>:8001/health
```

Reboot the HP, wait ~2 minutes, then check Overview — HP should show online without opening PowerShell.

### Uninstall

```powershell
.\scripts\uninstall-agent-task.ps1
```

### Manual Task Scheduler (GUI fallback)

If the installer script fails:

1. Press Win+R → `shell:startup` → Enter.
2. Create `HomeLab-Agent.cmd` with:
   ```bat
   @echo off
   powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\path\to\Home-Lab\scripts\run-agent.ps1" -StartupDelaySeconds 60
   ```
3. Or use **Task Scheduler** → Create Task (At log on) pointing at the same `run-agent.ps1`.

Also confirm **Ollama** is enabled under Settings → Apps → Startup.

## Dashboard pages

| Page | Purpose |
|---|---|
| **Overview** | Fleet status, requests today, avg latency/tokens/sec |
| **Nodes** | Per-node CPU/RAM, Ollama version, loaded model |
| **Models** | Models installed on Mac vs HP, pull new models |
| **Playground** | Interactive inference — pick node + model or Auto, streaming response |
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

Edit [`config/models.yaml`](config/models.yaml) to set `preferred_node` hints and `also_on` for multi-node pulls.

**Auto routing** scores nodes by:
- Model installed (required)
- RAM headroom (skip if > 85% used)
- Preferred node from config
- Historical tokens/sec for that model on that node

**Manual routing** — set `node: "mac"` or `node: "hp"` in Playground or API calls.

## Project structure

```
config/           — nodes.yaml, models.yaml
services/api/     — FastAPI control plane (Mac)
services/agent/   — HP metrics sidecar
dashboard/        — React + Vite dashboard
scripts/          — start-api.sh, start-agent.ps1, run-agent.ps1,
                    install-agent-task.ps1, uninstall-agent-task.ps1, pull-models.sh
data/             — SQLite DB (gitignored)
```

## Ready for projects

Once both nodes show green in Overview and Playground runs inference successfully:

1. Projects call `POST /api/v1/inference` with `{ model, prompt, node }`
2. Metrics are logged automatically
3. Add new models via `config/models.yaml` + `pull-models.sh`

## Optional next steps

- **HP agent autostart** — [done above](#hp-agent-autostart)
- **Tailscale** — access lab from phone away from home
- **iOS Shortcuts** — POST to `http://<mac-ip>:8000/api/v1/inference`
- **Serve dashboard in prod** — `cd dashboard && npm run build`, then serve `dist/` from FastAPI

## Hardware reference

| Device | Role |
|---|---|
| Mac M2 Pro 16GB | Orchestrator + fast inference (8B–14B) |
| HP Ultra 7 32GB | Heavy inference (27B+) or fast models when Mac is busy |
| iPhone / Oppo | Clients (future) |

See [`Claude-stategy.md`](Claude-stategy.md) for experiment ideas and content strategy.
