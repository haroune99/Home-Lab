import aiosqlite
from pathlib import Path

from app.config import get_settings, _repo_root

SCHEMA = """
CREATE TABLE IF NOT EXISTS inference_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    node TEXT NOT NULL,
    model TEXT NOT NULL,
    routing_mode TEXT NOT NULL,
    routing_reason TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    latency_ms REAL NOT NULL,
    tokens_per_sec REAL,
    status TEXT NOT NULL,
    error TEXT
);

CREATE TABLE IF NOT EXISTS node_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    node TEXT NOT NULL,
    cpu_percent REAL,
    ram_used_mb REAL,
    ram_total_mb REAL,
    ollama_loaded_model TEXT,
    online INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_inference_logs_timestamp ON inference_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_inference_logs_node ON inference_logs(node);
CREATE INDEX IF NOT EXISTS idx_node_snapshots_timestamp ON node_snapshots(timestamp);
"""


async def get_db() -> aiosqlite.Connection:
    settings = get_settings()
    db_path = Path(settings.database_path)
    if not db_path.is_absolute():
        db_path = _repo_root() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(db_path))
    conn.row_factory = aiosqlite.Row
    await conn.executescript(SCHEMA)
    await conn.commit()
    return conn


class Database:
    def __init__(self) -> None:
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await get_db()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected")
        return self._conn


db = Database()
