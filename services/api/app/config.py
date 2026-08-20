from pathlib import Path
from functools import lru_cache

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

NODE_IDS = ("mac", "hp", "air")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _env_file() -> str:
    for candidate in (Path(".env"), _repo_root() / ".env"):
        if candidate.exists():
            return str(candidate)
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mac_ollama_url: str = "http://127.0.0.1:11434"
    hp_ollama_url: str = "http://192.168.1.100:11434"
    hp_agent_url: str = "http://192.168.1.100:8001"
    air_llama_url: str = "http://192.168.1.143:8080"
    air_agent_url: str = "http://192.168.1.143:8002"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_path: str = "./data/homelab.db"
    cors_origins: str = "*"
    config_dir: str = "./config"
    ram_threshold_percent: int = 85

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def config_path(self) -> Path:
        p = Path(self.config_dir)
        if p.is_absolute():
            return p
        root_candidate = _repo_root() / p
        if root_candidate.exists():
            return root_candidate
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml_config(filename: str) -> dict:
    settings = get_settings()
    path = settings.config_path / filename
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_node_urls() -> dict[str, str]:
    settings = get_settings()
    return {
        "mac": settings.mac_ollama_url.rstrip("/"),
        "hp": settings.hp_ollama_url.rstrip("/"),
        "air": settings.air_llama_url.rstrip("/"),
    }


def get_node_backend(node_id: str) -> str:
    """Return 'ollama' or 'llamacpp'."""
    if node_id == "air":
        return "llamacpp"
    return "ollama"


def get_agent_urls() -> dict[str, str | None]:
    settings = get_settings()
    return {
        "mac": None,
        "hp": settings.hp_agent_url.rstrip("/"),
        "air": settings.air_agent_url.rstrip("/"),
    }
