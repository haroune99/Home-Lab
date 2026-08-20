from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ollama (HP / Mac) and/or llama-server (Air)
    ollama_url: str = "http://127.0.0.1:11434"
    llama_url: str = ""
    agent_host: str = "0.0.0.0"
    agent_port: int = 8001


settings = Settings()
