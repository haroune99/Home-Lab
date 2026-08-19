import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import db
from app.routers import health, inference, metrics, models, nodes
from app.services.node_health import poll_nodes_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    poll_task = asyncio.create_task(poll_nodes_loop(interval=30))
    yield
    poll_task.cancel()
    try:
        await poll_task
    except asyncio.CancelledError:
        pass
    await db.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Home Lab API",
        description="Control plane for local LLM home lab",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["nodes"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
    app.include_router(inference.router, prefix="/api/v1/inference", tags=["inference"])
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])

    return app


app = create_app()
