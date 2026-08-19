from fastapi import FastAPI

from app.collectors import ollama_ps, ollama_loaded_model, system_metrics

app = FastAPI(title="Home Lab Agent", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "homelab-agent"}


@app.get("/metrics")
async def metrics():
    sys = system_metrics()
    loaded = await ollama_loaded_model()
    return {
        **sys,
        "ollama_loaded_model": loaded,
    }


@app.get("/ollama/ps")
async def ollama_processes():
    return {"models": await ollama_ps()}
