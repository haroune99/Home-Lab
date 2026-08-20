from pathlib import Path

from app.config import NODE_IDS, get_settings, load_yaml_config
from app.schemas import RoutingPreviewResponse
from app.services.inference_client import get_inference_client
from app.services.metrics_collector import get_historical_tokens_per_sec
from app.services.node_health import get_all_nodes


class RoutingError(Exception):
    pass


async def get_models_on_nodes() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for node_id in NODE_IDS:
        client = get_inference_client(node_id)
        try:
            models = await client.list_models()
            names = sorted({m.get("name", "") for m in models if m.get("name")})
            result[node_id] = names
        except Exception:
            result[node_id] = []
    return result


def model_installed_on_node(
    installed: dict[str, list[str]], node: str, model: str
) -> bool:
    names = installed.get(node, [])
    if model in names:
        return True
    model_base = Path(model).name
    model_stem = Path(model_base).stem.lower()
    for n in names:
        if n == model or Path(n).name == model_base:
            return True
        n_stem = Path(n).stem.lower()
        if model_stem and (model_stem in n_stem or n_stem in model_stem):
            return True
        base = model.split(":")[0] if ":" in model else model
        if n == base or n.startswith(f"{base}:"):
            return True
    return False


async def resolve_routing(
    model: str, node: str
) -> tuple[str, str, str]:
    """
    Returns (selected_node, routing_mode, routing_reason).
    """
    if node in NODE_IDS:
        installed = await get_models_on_nodes()
        if not model_installed_on_node(installed, node, model):
            raise RoutingError(
                f"Model '{model}' is not installed on node '{node}'. "
                f"Available: {installed.get(node, [])}"
            )
        return node, "manual", f"{node}: explicitly selected"

    return await auto_route(model)


async def preview_routing(model: str, node: str) -> RoutingPreviewResponse:
    if node in NODE_IDS:
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
        entry_name = entry.get("name", "")
        if entry_name == model or entry_name.split(":")[0] == model.split(":")[0]:
            preferred_node = entry.get("preferred_node")
            break
        if Path(entry_name).stem.lower() in Path(model).stem.lower():
            preferred_node = entry.get("preferred_node")
            break

    installed = await get_models_on_nodes()
    nodes_status = await get_all_nodes()
    node_status_map = {n.id: n for n in nodes_status}

    candidates: list[str] = []
    for node_id in NODE_IDS:
        status = node_status_map.get(node_id)
        if not status or not status.online:
            continue
        if not model_installed_on_node(installed, node_id, model):
            continue
        ram_pct = status.ram_used_percent or 0
        # Air has no remote RAM metrics — don't exclude on missing RAM
        if status.ram_used_percent is not None and ram_pct > ram_threshold:
            continue
        candidates.append(node_id)

    if not candidates:
        for node_id in NODE_IDS:
            status = node_status_map.get(node_id)
            if status and status.online and model_installed_on_node(installed, node_id, model):
                candidates.append(node_id)

    if not candidates:
        raise RoutingError(
            f"No available node has model '{model}' installed. "
            f"Mac: {installed.get('mac', [])}, HP: {installed.get('hp', [])}, "
            f"Air: {installed.get('air', [])}"
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

        # Prefer mac/hp over air for equal models unless preferred
        if node_id == "air":
            score -= 2
            reasons[node_id].append("legacy_node")

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
