import json
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_node_urls
from app.schemas import InferenceRequest, InferenceResponse, RoutingPreviewRequest, RoutingPreviewResponse
from app.services.metrics_collector import log_inference
from app.services.ollama_client import OllamaClient
from app.services.router import RoutingError, preview_routing, resolve_routing

router = APIRouter()


@router.post("/preview", response_model=RoutingPreviewResponse)
async def routing_preview(req: RoutingPreviewRequest):
    return await preview_routing(req.model, req.node)


@router.post("")
async def run_inference(req: InferenceRequest):
    try:
        selected_node, routing_mode, routing_reason = await resolve_routing(
            req.model, req.node
        )
    except RoutingError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    urls = get_node_urls()
    client = OllamaClient(urls[selected_node])

    if req.stream:
        return await _stream_inference(
            client, req, selected_node, routing_mode, routing_reason
        )

    start = time.perf_counter()
    try:
        result = await client.generate(
            model=req.model,
            prompt=req.prompt,
            system=req.system,
            stream=False,
        )
        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="Unexpected response type")

        latency_ms = (time.perf_counter() - start) * 1000
        prompt_tokens = result.get("prompt_eval_count", 0)
        completion_tokens = result.get("eval_count", 0)
        tokens_per_sec = None
        if completion_tokens and latency_ms > 0:
            eval_duration_ns = result.get("eval_duration", 0)
            if eval_duration_ns:
                tokens_per_sec = completion_tokens / (eval_duration_ns / 1e9)
            else:
                tokens_per_sec = completion_tokens / (latency_ms / 1000)

        await log_inference(
            node=selected_node,
            model=req.model,
            routing_mode=routing_mode,
            routing_reason=routing_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            tokens_per_sec=tokens_per_sec,
            status="success",
        )

        return InferenceResponse(
            node=selected_node,
            model=req.model,
            routing_mode=routing_mode,
            routing_reason=routing_reason,
            response=result.get("response", ""),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            tokens_per_sec=tokens_per_sec,
        )
    except HTTPException:
        raise
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        error_msg = str(e) or type(e).__name__
        await log_inference(
            node=selected_node,
            model=req.model,
            routing_mode=routing_mode,
            routing_reason=routing_reason,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=latency_ms,
            tokens_per_sec=None,
            status="error",
            error=error_msg,
        )
        raise HTTPException(status_code=502, detail=error_msg) from e


async def _stream_inference(
    client: OllamaClient,
    req: InferenceRequest,
    selected_node: str,
    routing_mode: str,
    routing_reason: str,
):
    start = time.perf_counter()

    async def event_generator():
        full_response = ""
        completion_tokens = 0
        prompt_tokens = 0
        error = None
        try:
            meta = {
                "node": selected_node,
                "model": req.model,
                "routing_mode": routing_mode,
                "routing_reason": routing_reason,
            }
            yield f"data: {json.dumps({'type': 'meta', **meta})}\n\n"

            stream = await client.generate(
                model=req.model,
                prompt=req.prompt,
                system=req.system,
                stream=True,
            )
            async for chunk in stream:
                token = chunk.get("response", "")
                full_response += token
                completion_tokens = chunk.get("eval_count", completion_tokens)
                prompt_tokens = chunk.get("prompt_eval_count", prompt_tokens)
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                if chunk.get("done"):
                    break

            latency_ms = (time.perf_counter() - start) * 1000
            tokens_per_sec = None
            if completion_tokens and latency_ms > 0:
                tokens_per_sec = completion_tokens / (latency_ms / 1000)

            await log_inference(
                node=selected_node,
                model=req.model,
                routing_mode=routing_mode,
                routing_reason=routing_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                tokens_per_sec=tokens_per_sec,
                status="success",
            )
            yield f"data: {json.dumps({'type': 'done', 'latency_ms': latency_ms, 'tokens_per_sec': tokens_per_sec, 'completion_tokens': completion_tokens})}\n\n"
        except Exception as e:
            error = str(e)
            latency_ms = (time.perf_counter() - start) * 1000
            await log_inference(
                node=selected_node,
                model=req.model,
                routing_mode=routing_mode,
                routing_reason=routing_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                tokens_per_sec=None,
                status="error",
                error=error,
            )
            yield f"data: {json.dumps({'type': 'error', 'error': error})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
