from fastapi import APIRouter, HTTPException

from app.config import get_node_urls
from app.schemas import AvailableModels, ModelInfo, ModelsByNode, PullModelRequest
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
    urls = get_node_urls()
    result = ModelsByNode()
    for node_id, url in urls.items():
        client = OllamaClient(url)
        try:
            models = await client.list_models()
            infos = [_to_model_info(m) for m in models]
            if node_id == "mac":
                result.mac = infos
            else:
                result.hp = infos
        except Exception:
            pass
    return result


@router.get("/available", response_model=AvailableModels)
async def available_models():
    installed = await get_models_on_nodes()
    all_models = sorted(set(installed.get("mac", []) + installed.get("hp", [])))
    return AvailableModels(
        mac=installed.get("mac", []),
        hp=installed.get("hp", []),
        all_models=all_models,
    )


@router.post("/pull")
async def pull_model(req: PullModelRequest):
    if req.node not in ("mac", "hp"):
        raise HTTPException(status_code=400, detail="node must be 'mac' or 'hp'")
    urls = get_node_urls()
    client = OllamaClient(urls[req.node])
    try:
        result = await client.pull(req.model)
        return {"status": "ok", "node": req.node, "model": req.model, "result": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
