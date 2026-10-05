"""Embedding providers. Tests must use the labeled test double, never a silent fallback."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import numpy as np

from app.core.config import get_settings
from app.core.errors import AppError


class EmbeddingProvider(ABC):
    model_id: str
    dimension: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class TestHashEmbeddingProvider(EmbeddingProvider):
    """Deterministic test double. Not a retrieval-quality embedding model."""

    model_id = "test-hash-v1"
    dimension = 32

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
            rng = np.random.default_rng(seed)
            vector = rng.standard_normal(self.dimension)
            norm = np.linalg.norm(vector) or 1.0
            vectors.append((vector / norm).astype(float).tolist())
        return vectors


class HashedTokenEmbeddingProvider(EmbeddingProvider):
    """Lexical hashing baseline. No model download. Not a biomedical encoder."""

    model_id = "hashed-token-v1"
    dimension = 256

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = np.zeros(self.dimension, dtype=float)
            for token in _tokens(text):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimension
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign
            norm = np.linalg.norm(vector) or 1.0
            vectors.append((vector / norm).tolist())
        return vectors


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_id: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise AppError(
                status_code=500,
                detail="sentence-transformers is not installed. Use hashed-token embeddings or install the embeddings extra.",
            ) from exc
        self.model_id = model_id
        self._model = SentenceTransformer(model_id)
        self.dimension = int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        matrix = self._model.encode(texts, batch_size=16, convert_to_numpy=True, show_progress_bar=False)
        return [row.astype(float).tolist() for row in matrix]


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    provider = settings.embedding_provider
    if provider == "test_hash":
        return TestHashEmbeddingProvider()
    if provider == "hashed_token":
        return HashedTokenEmbeddingProvider()
    if provider == "sentence_transformers":
        return SentenceTransformerEmbeddingProvider(settings.embedding_model)
    raise AppError(status_code=500, detail="Unknown embedding provider.")


def _tokens(text: str) -> list[str]:
    return [part.lower() for part in "".join(ch if ch.isalnum() else " " for ch in text).split() if part]
