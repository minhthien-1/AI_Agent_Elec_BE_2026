from __future__ import annotations

import logging
import os
import time
from typing import Optional

import httpx


logger = logging.getLogger(__name__)


class OllamaError(RuntimeError):
    """Base error for Ollama-related failures."""


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            )
        ).rstrip("/")

        self.model = (
            model
            or os.getenv(
                "OLLAMA_MODEL",
                "qwen2.5:3b",
            )
        )

        self.timeout = timeout or float(
            os.getenv(
                "OLLAMA_TIMEOUT",
                "60",
            )
        )

        if max_retries < 0:
            raise ValueError(
                "max_retries must be >= 0"
            )

        self.max_retries = max_retries

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def __enter__(self) -> "OllamaClient":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()

    def generate(self, prompt: str) -> str:
        """
        Send prompt to Ollama and return generated text.

        Includes:
        - input validation
        - timeout
        - retry
        - latency measurement
        """

        if not prompt or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty"
            )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        last_error = None

        for attempt in range(
            1,
            self.max_retries + 2,
        ):
            start_time = time.perf_counter()

            try:
                response = self._client.post(
                    "/api/generate",
                    json=payload,
                )

                elapsed_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                response.raise_for_status()

                data = response.json()

                generated_text = data.get(
                    "response"
                )

                if not isinstance(
                    generated_text,
                    str,
                ):
                    raise OllamaError(
                        "Ollama response does not contain "
                        "a valid 'response' field"
                    )

                logger.info(
                    "Ollama generation succeeded | "
                    "model=%s | attempt=%d | "
                    "latency_ms=%.2f",
                    self.model,
                    attempt,
                    elapsed_ms,
                )

                return generated_text

            except httpx.TimeoutException as exc:
                last_error = exc

                elapsed_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                logger.warning(
                    "Ollama timeout | "
                    "attempt=%d | latency_ms=%.2f",
                    attempt,
                    elapsed_ms,
                )

            except httpx.NetworkError as exc:
                last_error = exc

                elapsed_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                logger.warning(
                    "Ollama network error | "
                    "attempt=%d | latency_ms=%.2f",
                    attempt,
                    elapsed_ms,
                )

            except httpx.HTTPStatusError as exc:
                status_code = (
                    exc.response.status_code
                )

                # Retry only 5xx server errors.
                if status_code >= 500:
                    last_error = exc

                    logger.warning(
                        "Ollama server error | "
                        "status=%d | attempt=%d",
                        status_code,
                        attempt,
                    )
                else:
                    raise OllamaError(
                        "Ollama returned HTTP "
                        f"{status_code}: "
                        f"{exc.response.text}"
                    ) from exc

            except ValueError as exc:
                raise OllamaError(
                    "Ollama returned invalid JSON"
                ) from exc

            except OllamaError:
                raise

            except Exception as exc:
                raise OllamaError(
                    f"Unexpected Ollama error: {exc}"
                ) from exc

            if attempt <= self.max_retries:
                delay = 0.5 * (
                    2 ** (attempt - 1)
                )

                logger.info(
                    "Retrying Ollama request in "
                    "%.1f seconds...",
                    delay,
                )

                time.sleep(delay)

        raise OllamaError(
            "Failed to call Ollama after "
            f"{self.max_retries + 1} attempts"
        ) from last_error


ollama_client = OllamaClient()