"""CPU embedding wrapper for intfloat/multilingual-e5-small."""

from __future__ import annotations

import os
from typing import Iterable, List, Optional


DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_DIMENSIONS = 384


class E5Embedder:
    """Loads the embedding model lazily, so ordinary API startup stays light."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device="cpu")
        return self._model

    def embed_passages(self, texts: Iterable[str], batch_size: int = 32) -> List[List[float]]:
        """Embed chunks with the E5 passage prefix and L2 normalization."""
        values = [f"passage: {text}" for text in texts]
        if not values:
            return []
        vectors = self.model.encode(
            values, batch_size=batch_size, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Use this later for cosine retrieval; E5 needs a distinct query prefix."""
        return self.model.encode(
            [f"query: {text}"], normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        )[0].tolist()
