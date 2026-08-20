from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    model: str
    prompt: str
    node: str = "auto"
    stream: bool = False
    system: str | None = None


class InferenceResponse(BaseModel):
    node: str
    model: str
    routing_mode: str
    routing_reason: str | None
    response: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float
    tokens_per_sec: float | None = None


class RoutingPreviewRequest(BaseModel):
    model: str
    node: str = "auto"


class RoutingPreviewResponse(BaseModel):
    node: str
    routing_mode: str
    routing_reason: str
    model_available: bool


class PullModelRequest(BaseModel):
    model: str
    node: str


class NodeStatus(BaseModel):
    id: str
    display_name: str
    online: bool
    ollama_online: bool
    agent_online: bool | None = None
    latency_ms: float | None = None
    cpu_percent: float | None = None
    ram_used_mb: float | None = None
    ram_total_mb: float | None = None
    ram_used_percent: float | None = None
    ollama_version: str | None = None
    ollama_loaded_model: str | None = None
    error: str | None = None


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None


class ModelsByNode(BaseModel):
    mac: list[ModelInfo] = Field(default_factory=list)
    hp: list[ModelInfo] = Field(default_factory=list)
    air: list[ModelInfo] = Field(default_factory=list)


class AvailableModels(BaseModel):
    mac: list[str] = Field(default_factory=list)
    hp: list[str] = Field(default_factory=list)
    air: list[str] = Field(default_factory=list)
    all_models: list[str] = Field(default_factory=list)


class MetricsSummary(BaseModel):
    requests_today: int = 0
    avg_tokens_per_sec: float | None = None
    avg_latency_ms: float | None = None
    total_requests: int = 0


class InferenceLogEntry(BaseModel):
    id: int
    timestamp: str
    node: str
    model: str
    routing_mode: str
    routing_reason: str | None
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    tokens_per_sec: float | None
    status: str
    error: str | None


class TimeseriesPoint(BaseModel):
    timestamp: str
    node: str | None = None
    model: str | None = None
    avg_latency_ms: float | None = None
    avg_tokens_per_sec: float | None = None
    count: int = 0
