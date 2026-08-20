import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import _repo_root, get_settings
from app.db import db
from app.routers import health, inference, metrics, models, nodes
from app.services.node_health import poll_nodes_loop


def _dashboard_dist() -> Path | None:
    dist = _repo_root() / "dashboard" / "dist"
    if dist.is_dir() and (dist / "index.html").is_file():
        return dist
    return None


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

    origins = settings.cors_origin_list
    allow_all = origins == ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else origins,
        allow_credentials=not allow_all,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["nodes"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
    app.include_router(inference.router, prefix="/api/v1/inference", tags=["inference"])
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])

    dist = _dashboard_dist()
    if dist is not None:
        assets = dist / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/")
        async def dashboard_root():
            return FileResponse(dist / "index.html")

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):
            # API routes are matched first; this catches SPA deep links
            candidate = dist / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
