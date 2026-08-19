from fastapi import APIRouter

from app.schemas import NodeStatus
from app.services.node_health import get_all_nodes

router = APIRouter()


@router.get("", response_model=list[NodeStatus])
async def list_nodes():
    return await get_all_nodes()
