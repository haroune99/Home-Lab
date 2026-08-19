from datetime import datetime, timezone

from fastapi import APIRouter, Query

from app.db import db
from app.schemas import InferenceLogEntry, MetricsSummary, TimeseriesPoint

router = APIRouter()


@router.get("/summary", response_model=MetricsSummary)
async def metrics_summary():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cursor = await db.conn.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN timestamp LIKE ? THEN 1 ELSE 0 END) as today_count,
            AVG(CASE WHEN status = 'success' THEN tokens_per_sec END) as avg_tps,
            AVG(CASE WHEN status = 'success' THEN latency_ms END) as avg_latency
        FROM inference_logs
        """,
        (f"{today}%",),
    )
    row = await cursor.fetchone()
    return MetricsSummary(
        requests_today=row["today_count"] or 0,
        avg_tokens_per_sec=row["avg_tps"],
        avg_latency_ms=row["avg_latency"],
        total_requests=row["total"] or 0,
    )


@router.get("/inference", response_model=list[InferenceLogEntry])
async def inference_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    node: str | None = None,
    model: str | None = None,
):
    query = "SELECT * FROM inference_logs WHERE 1=1"
    params: list = []
    if node:
        query += " AND node = ?"
        params.append(node)
    if model:
        query += " AND model = ?"
        params.append(model)
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = await db.conn.execute(query, params)
    rows = await cursor.fetchall()
    return [
        InferenceLogEntry(
            id=r["id"],
            timestamp=r["timestamp"],
            node=r["node"],
            model=r["model"],
            routing_mode=r["routing_mode"],
            routing_reason=r["routing_reason"],
            prompt_tokens=r["prompt_tokens"],
            completion_tokens=r["completion_tokens"],
            latency_ms=r["latency_ms"],
            tokens_per_sec=r["tokens_per_sec"],
            status=r["status"],
            error=r["error"],
        )
        for r in rows
    ]


@router.get("/timeseries", response_model=list[TimeseriesPoint])
async def metrics_timeseries(
    hours: int = Query(24, ge=1, le=168),
    group_by: str = Query("hour", pattern="^(hour|node|model)$"),
):
    if group_by == "hour":
        cursor = await db.conn.execute(
            """
            SELECT
                substr(timestamp, 1, 13) as ts_bucket,
                AVG(latency_ms) as avg_latency_ms,
                AVG(tokens_per_sec) as avg_tokens_per_sec,
                COUNT(*) as cnt
            FROM inference_logs
            WHERE status = 'success'
              AND timestamp >= datetime('now', ?)
            GROUP BY ts_bucket
            ORDER BY ts_bucket
            """,
            (f"-{hours} hours",),
        )
    elif group_by == "node":
        cursor = await db.conn.execute(
            """
            SELECT
                node,
                AVG(latency_ms) as avg_latency_ms,
                AVG(tokens_per_sec) as avg_tokens_per_sec,
                COUNT(*) as cnt,
                MAX(timestamp) as ts_bucket
            FROM inference_logs
            WHERE status = 'success'
              AND timestamp >= datetime('now', ?)
            GROUP BY node
            """,
            (f"-{hours} hours",),
        )
    else:
        cursor = await db.conn.execute(
            """
            SELECT
                model,
                AVG(latency_ms) as avg_latency_ms,
                AVG(tokens_per_sec) as avg_tokens_per_sec,
                COUNT(*) as cnt,
                MAX(timestamp) as ts_bucket
            FROM inference_logs
            WHERE status = 'success'
              AND timestamp >= datetime('now', ?)
            GROUP BY model
            """,
            (f"-{hours} hours",),
        )

    rows = await cursor.fetchall()
    points = []
    for r in rows:
        ts = r["ts_bucket"]
        node = r["node"] if group_by == "node" and "node" in r.keys() else None
        model = r["model"] if group_by == "model" and "model" in r.keys() else None
        points.append(
            TimeseriesPoint(
                timestamp=str(ts),
                node=node,
                model=model,
                avg_latency_ms=r["avg_latency_ms"],
                avg_tokens_per_sec=r["avg_tokens_per_sec"],
                count=r["cnt"],
            )
        )
    return points


@router.get("/snapshots")
async def node_snapshots(limit: int = Query(100, ge=1, le=1000)):
    cursor = await db.conn.execute(
        """
        SELECT * FROM node_snapshots
        ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
