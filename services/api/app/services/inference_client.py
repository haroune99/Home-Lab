from app.config import get_node_backend, get_node_urls
from app.services.llama_server_client import LlamaServerClient
from app.services.ollama_client import OllamaClient


def get_inference_client(node_id: str) -> OllamaClient | LlamaServerClient:
    urls = get_node_urls()
    url = urls[node_id]
    if get_node_backend(node_id) == "llamacpp":
        return LlamaServerClient(url)
    return OllamaClient(url)
