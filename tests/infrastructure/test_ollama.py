import pytest

# Cần dịch vụ thật (PostgreSQL/Ollama) nên CI bỏ qua: pytest -m "not integration".
pytestmark = pytest.mark.integration

from infrastructure.llm.ollama_client import OllamaClient


def test_ollama_generate():
    with OllamaClient() as client:
        result = client.generate(
            "Hãy trả lời bằng một câu ngắn: điện là gì?"
        )

        assert isinstance(result, str)
        assert result.strip() != ""


def test_ollama_rejects_empty_prompt():
    with OllamaClient() as client:
        try:
            client.generate("")
            assert False, "Expected ValueError"
        except ValueError:
            pass