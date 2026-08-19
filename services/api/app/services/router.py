from app.config import get_settings, load_yaml_config
from app.schemas import RoutingPreviewResponse
from app.services.metrics_collector import get_historical_tokens_per_sec
from app.services.node_health import get_all_nodes
from app.services.ollama_client import OllamaClient
from app.config import get_node_urls


class RoutingError(Exception):
    pass


async def get_models_on_nodes() -> dict[str, list[str]]:
    urls = get_node_urls()
    result: dict[str, list[str]] = {}
    for node_id, url in urls.items():
        client = OllamaClient(url)
        try:
            models = await client.list_models()
            result[node_id] = sorted({m.get("name", "") for m in models if m.get("name")})
        except Exception:
            result[node_id] = []
    return result


def model_installed_on_node(
    installed: dict[str, list[str]], node: str, model: str
) -> bool:
    names = installed.get(node, [])
    if model in names:
        return True
    base = model.split(":")[0] if ":" in model else model
    return any(n == base or n.startswith(f"{base}:") for n in names)


async def resolve_routing(
    model: str, node: str
) -> tuple[str, str, str]:
    """
    Returns (selected_node, routing_mode, routing_reason).
    """
    if node in ("mac", "hp"):
        installed = await get_models_on_nodes()
        if not model_installed_on_node(installed, node, model):
            raise RoutingError(
                f"Model '{model}' is not installed on node '{node}'. "
                f"Available: {installed.get(node, [])}"
            )
        return node, "manual", f"{node}: explicitly selected"

    return await auto_route(model)


async def preview_routing(model: str, node: str) -> RoutingPreviewResponse:
    if node in ("mac", "hp"):
        installed = await get_models_on_nodes()
        available = model_installed_on_node(installed, node, model)
        return RoutingPreviewResponse(
            node=node,
            routing_mode="manual",
            routing_reason=f"{node}: explicitly selected",
            model_available=available,
        )

    try:
        selected, mode, reason = await auto_route(model)
        installed = await get_models_on_nodes()
        available = model_installed_on_node(installed, selected, model)
        return RoutingPreviewResponse(
            node=selected,
            routing_mode=mode,
            routing_reason=reason,
            model_available=available,
        )
    except RoutingError as e:
        return RoutingPreviewResponse(
            node="none",
            routing_mode="auto",
            routing_reason=str(e),
            model_available=False,
        )


async def auto_route(model: str) -> tuple[str, str, str]:
    settings = get_settings()
    models_config = load_yaml_config("models.yaml")
    routing_config = models_config.get("routing", {}).get("auto", {})
    ram_threshold = routing_config.get(
        "ram_threshold_percent", settings.ram_threshold_percent
    )

    preferred_node: str | None = None
    for entry in models_config.get("models", []):
        if entry.get("name") == model or entry.get("name", "").split(":")[0] == model.split(":")[0]:
            preferred_node = entry.get("preferred_node")
            break

    installed = await get_models_on_nodes()
    nodes_status = await get_all_nodes()
    node_status_map = {n.id: n for n in nodes_status}

    candidates: list[str] = []
    for node_id in ("mac", "hp"):
        status = node_status_map.get(node_id)
        if not status or not status.online:
            continue
        if not model_installed_on_node(installed, node_id, model):
            continue
        ram_pct = status.ram_used_percent or 0
        if ram_pct > ram_threshold:
            continue
        candidates.append(node_id)

    if not candidates:
        for node_id in ("mac", "hp"):
            status = node_status_map.get(node_id)
            if status and status.online and model_installed_on_node(installed, node_id, model):
                candidates.append(node_id)

    if not candidates:
        raise RoutingError(
            f"No available node has model '{model}' installed. "
            f"Mac: {installed.get('mac', [])}, HP: {installed.get('hp', [])}"
        )

    if len(candidates) == 1:
        only = candidates[0]
        reason_parts = [f"{only}: only eligible node"]
        if preferred_node == only:
            reason_parts.append("preferred_node match")
        return only, "auto", ", ".join(reason_parts)

    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {n: [] for n in candidates}

    for node_id in candidates:
        score = 0.0
        status = node_status_map[node_id]

        if preferred_node == node_id:
            score += 10
            reasons[node_id].append("preferred_node")

        if status.ram_used_percent is not None:
            headroom = max(0, 100 - status.ram_used_percent) / 20
            score += min(5, headroom)
            reasons[node_id].append(f"ram_headroom={100 - status.ram_used_percent:.0f}%")

        hist_tps = await get_historical_tokens_per_sec(node_id, model)
        if hist_tps:
            tps_score = min(5, hist_tps / 2)
            score += tps_score
            reasons[node_id].append(f"hist_tok/s={hist_tps:.1f}")

        scores[node_id] = score

    winner = max(candidates, key=lambda n: scores[n])
    reason_str = f"{winner}: " + ", ".join(reasons[winner]) + f" (score={scores[winner]:.1f})"
    return winner, "auto", reason_str
