from fastapi import APIRouter, HTTPException

from app.config import NODE_IDS, get_node_backend
from app.schemas import AvailableModels, ModelInfo, ModelsByNode, PullModelRequest
from app.services.inference_client import get_inference_client
from app.services.ollama_client import OllamaClient
from app.services.router import get_models_on_nodes

router = APIRouter()


def _to_model_info(raw: dict) -> ModelInfo:
    return ModelInfo(
        name=raw.get("name", ""),
        size=raw.get("size"),
        modified_at=raw.get("modified_at"),
        digest=raw.get("digest"),
    )


@router.get("", response_model=ModelsByNode)
async def list_models():
    result = ModelsByNode()
    for node_id in NODE_IDS:
        client = get_inference_client(node_id)
        try:
            models = await client.list_models()
            infos = [_to_model_info(m) for m in models]
            setattr(result, node_id, infos)
        except Exception:
            pass
    return result


@router.get("/available", response_model=AvailableModels)
async def available_models():
    installed = await get_models_on_nodes()
    all_models = sorted(
        set(
            installed.get("mac", [])
            + installed.get("hp", [])
            + installed.get("air", [])
        )
    )
    return AvailableModels(
        mac=installed.get("mac", []),
        hp=installed.get("hp", []),
        air=installed.get("air", []),
        all_models=all_models,
    )


@router.post("/pull")
async def pull_model(req: PullModelRequest):
    if req.node not in ("mac", "hp"):
        raise HTTPException(
            status_code=400,
            detail="Pull only supported for Ollama nodes (mac/hp). Load GGUF manually on Air.",
        )
    if get_node_backend(req.node) != "ollama":
        raise HTTPException(status_code=400, detail="node must be an Ollama node")
    client = get_inference_client(req.node)
    assert isinstance(client, OllamaClient)
    try:
        result = await client.pull(req.model)
        return {"status": "ok", "node": req.node, "model": req.model, "result": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
