from datetime import datetime, timezone

from app.db import db


async def log_inference(
    *,
    node: str,
    model: str,
    routing_mode: str,
    routing_reason: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    tokens_per_sec: float | None,
    status: str,
    error: str | None = None,
) -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    cursor = await db.conn.execute(
        """
        INSERT INTO inference_logs
        (timestamp, node, model, routing_mode, routing_reason,
         prompt_tokens, completion_tokens, latency_ms, tokens_per_sec, status, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            node,
            model,
            routing_mode,
            routing_reason,
            prompt_tokens,
            completion_tokens,
            latency_ms,
            tokens_per_sec,
            status,
            error,
        ),
    )
    await db.conn.commit()
    return cursor.lastrowid or 0


async def get_historical_tokens_per_sec(node: str, model: str) -> float | None:
    cursor = await db.conn.execute(
        """
        SELECT AVG(tokens_per_sec) as avg_tps
        FROM inference_logs
        WHERE node = ? AND model = ? AND status = 'success' AND tokens_per_sec IS NOT NULL
        """,
        (node, model),
    )
    row = await cursor.fetchone()
    if row and row["avg_tps"] is not None:
        return float(row["avg_tps"])
    return None
