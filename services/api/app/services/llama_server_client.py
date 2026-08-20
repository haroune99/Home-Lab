import json
import time
from pathlib import Path
from typing import Any, AsyncIterator

import httpx


class LlamaServerClient:
    """Client for llama.cpp llama-server (OpenAI-compatible HTTP API)."""

    def __init__(self, base_url: str, timeout: float = 600.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def ping(self) -> tuple[bool, float | None, str | None]:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                resp.raise_for_status()
                latency = (time.perf_counter() - start) * 1000
                return True, latency, None
        except Exception as e:
            return False, None, str(e)

    async def version(self) -> str | None:
        return "llamacpp"

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/v1/models")
            resp.raise_for_status()
            data = resp.json().get("data", [])
            models: list[dict[str, Any]] = []
            for m in data:
                mid = m.get("id", "")
                meta = m.get("meta") or {}
                models.append(
                    {
                        "name": mid,
                        "size": meta.get("size"),
                        "modified_at": None,
                        "digest": None,
                    }
                )
            return models

    async def ps(self) -> list[dict[str, Any]]:
        # llama-server typically has one loaded model; expose it via /v1/models
        try:
            models = await self.list_models()
            return [{"name": m["name"]} for m in models if m.get("name")]
        except Exception:
            return []

    def resolve_model_id(self, models: list[dict[str, Any]], target: str) -> str | None:
        names = [m.get("name", "") for m in models if m.get("name")]
        if target in names:
            return target
        target_base = Path(target).name
        for name in names:
            if Path(name).name == target_base:
                return name
            if target.lower() in name.lower() or Path(name).stem.lower().startswith(
                target.lower().replace(".gguf", "")
            ):
                return name
        return None

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Resolve short names to full path ids returned by the server
        try:
            listed = await self.list_models()
            resolved = self.resolve_model_id(listed, model)
            if resolved:
                model = resolved
        except Exception:
            pass

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if stream:
            return self._chat_stream(payload)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            usage = data.get("usage") or {}
            content = message.get("content") or ""
            return {
                "response": content,
                "prompt_eval_count": usage.get("prompt_tokens", 0),
                "eval_count": usage.get("completion_tokens", 0),
            }

    async def _chat_stream(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                completion_tokens = 0
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        yield {"response": "", "done": True, "eval_count": completion_tokens}
                        break
                    try:
                        chunk = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    choice = (chunk.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    token = delta.get("content") or ""
                    if token:
                        completion_tokens += 1
                        yield {"response": token, "done": False}
                    if choice.get("finish_reason"):
                        usage = chunk.get("usage") or {}
                        yield {
                            "response": "",
                            "done": True,
                            "eval_count": usage.get("completion_tokens", completion_tokens),
                            "prompt_eval_count": usage.get("prompt_tokens", 0),
                        }
                        break
