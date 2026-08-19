import json
import time
from typing import Any, AsyncIterator

import httpx


class OllamaClient:
    def __init__(self, base_url: str, timeout: float = 600.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def ping(self) -> tuple[bool, float | None, str | None]:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                latency = (time.perf_counter() - start) * 1000
                return True, latency, None
        except Exception as e:
            return False, None, str(e)

    async def version(self) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/version")
                resp.raise_for_status()
                return resp.json().get("version")
        except Exception:
            return None

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            return resp.json().get("models", [])

    async def ps(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/ps")
                resp.raise_for_status()
                return resp.json().get("models", [])
        except Exception:
            return []

    async def pull(self, model: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system

        if stream:
            return self._generate_stream(payload)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def _generate_stream(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield json.loads(line)

    def model_names(self, models: list[dict[str, Any]]) -> set[str]:
        names: set[str] = set()
        for m in models:
            name = m.get("name", "")
            names.add(name)
            if ":" in name:
                base = name.split(":")[0]
                names.add(base)
        return names

    def has_model(self, models: list[dict[str, Any]], target: str) -> bool:
        names = self.model_names(models)
        if target in names:
            return True
        base = target.split(":")[0] if ":" in target else target
        return any(n == base or n.startswith(f"{base}:") for n in names)
