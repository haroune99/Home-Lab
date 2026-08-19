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
    return None


async def ollama_ps() -> list:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_url.rstrip('/')}/api/ps")
            resp.raise_for_status()
            return resp.json().get("models", [])
    except Exception:
        return []
