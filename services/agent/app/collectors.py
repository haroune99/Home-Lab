from pathlib import Path

import httpx
import psutil

from app.config import settings


def system_metrics() -> dict:
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_used_mb": round(mem.used / (1024 * 1024), 1),
        "ram_total_mb": round(mem.total / (1024 * 1024), 1),
        "ram_used_percent": round(mem.percent, 1),
    }


async def ollama_loaded_model() -> str | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_url.rstrip('/')}/api/ps")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            if models:
                return models[0].get("name")
    except Exception:
        pass
    return await llama_loaded_model()


async def llama_loaded_model() -> str | None:
    if not settings.llama_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.llama_url.rstrip('/')}/v1/models")
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if data:
                mid = data[0].get("id", "")
                return Path(mid).name if mid else None
    except Exception:
        pass
    return None


async def ollama_ps() -> list:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_url.rstrip('/')}/api/ps")
            resp.raise_for_status()
            return resp.json().get("models", [])
    except Exception:
        return []
