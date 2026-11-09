import os

from infrastructure.llm.ollama_client import OllamaClient


class OllamaGenerator:
    """Application-facing adapter for Ollama text generation."""

    def __init__(self) -> None:
        self._model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str) -> str:
        with OllamaClient() as client:
            self._model_name = client.model
            return client.generate(prompt)
