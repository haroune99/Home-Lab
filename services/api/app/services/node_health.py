from datetime import datetime, timezone
from typing import Any

import httpx
import psutil

from app.config import NODE_IDS, get_agent_urls, get_node_backend, get_node_urls, load_yaml_config
from app.db import db
from app.schemas import NodeStatus
from app.services.inference_client import get_inference_client


async def fetch_agent_metrics(agent_url: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{agent_url}/metrics")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


def local_system_metrics() -> dict[str, Any]:
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_used_mb": mem.used / (1024 * 1024),
        "ram_total_mb": mem.total / (1024 * 1024),
        "ram_used_percent": mem.percent,
    }


async def get_node_status(node_id: str) -> NodeStatus:
    nodes_config = load_yaml_config("nodes.yaml").get("nodes", {})
    node_meta = nodes_config.get(node_id, {})
    display_name = node_meta.get("display_name", node_id.upper())

    agent_urls = get_agent_urls()
    agent_url = agent_urls.get(node_id)

    client = get_inference_client(node_id)
    online, latency_ms, error = await client.ping()
    backend_version = await client.version() if online else None
    loaded_models = await client.ps() if online else []
    loaded_model = loaded_models[0]["name"] if loaded_models else None

    cpu_percent: float | None = None
    ram_used_mb: float | None = None
    ram_total_mb: float | None = None
    ram_used_percent: float | None = None
    agent_online: bool | None = None

    if node_id == "mac":
        metrics = local_system_metrics()
        cpu_percent = metrics["cpu_percent"]
        ram_used_mb = metrics["ram_used_mb"]
        ram_total_mb = metrics["ram_total_mb"]
        ram_used_percent = metrics["ram_used_percent"]
    elif agent_url:
        agent_metrics = await fetch_agent_metrics(agent_url)
        if agent_metrics:
            agent_online = True
            cpu_percent = agent_metrics.get("cpu_percent")
            ram_used_mb = agent_metrics.get("ram_used_mb")
            ram_total_mb = agent_metrics.get("ram_total_mb")
            ram_used_percent = agent_metrics.get("ram_used_percent")
            if not loaded_model:
                loaded_model = agent_metrics.get("ollama_loaded_model")
        else:
            agent_online = False

    # Shorten long GGUF paths for display
    if loaded_model and "/" in loaded_model:
        loaded_model = loaded_model.rsplit("/", 1)[-1]

    backend = get_node_backend(node_id)
    version_label = backend_version
    if backend == "llamacpp" and online:
        version_label = "llamacpp"

    return NodeStatus(
        id=node_id,
        display_name=display_name,
        online=online,
        ollama_online=online,
        agent_online=agent_online,
        latency_ms=latency_ms,
        cpu_percent=cpu_percent,
        ram_used_mb=ram_used_mb,
        ram_total_mb=ram_total_mb,
        ram_used_percent=ram_used_percent,
        ollama_version=version_label,
        ollama_loaded_model=loaded_model,
        error=error,
    )


async def get_all_nodes() -> list[NodeStatus]:
    return [await get_node_status(n) for n in NODE_IDS]


async def snapshot_all_nodes() -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    nodes = await get_all_nodes()
    for node in nodes:
        await db.conn.execute(
            """
            INSERT INTO node_snapshots
            (timestamp, node, cpu_percent, ram_used_mb, ram_total_mb, ollama_loaded_model, online)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                node.id,
                node.cpu_percent,
                node.ram_used_mb,
                node.ram_total_mb,
                node.ollama_loaded_model,
                1 if node.online else 0,
            ),
        )
    await db.conn.commit()


async def poll_nodes_loop(interval: int = 30) -> None:
    import asyncio

    while True:
        try:
            await snapshot_all_nodes()
        except Exception:
            pass
        await asyncio.sleep(interval)
