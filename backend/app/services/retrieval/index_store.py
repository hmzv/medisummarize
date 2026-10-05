"""Patient-record vector indexes. Authorize the record before searching."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.embeddings.providers import EmbeddingProvider

_INDEX_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    score: float
    text: str


def _record_lock(record_id: uuid.UUID) -> threading.Lock:
    key = str(record_id)
    with _LOCKS_GUARD:
        if key not in _INDEX_LOCKS:
            _INDEX_LOCKS[key] = threading.Lock()
        return _INDEX_LOCKS[key]


def _index_dir(record_id: uuid.UUID) -> Path:
    path = (get_settings().resolved_index_dir / str(record_id)).resolve()
    base = get_settings().resolved_index_dir
    if not path.is_relative_to(base):
        raise AppError(status_code=500, detail="Index path could not be resolved.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _meta_path(record_id: uuid.UUID) -> Path:
    return _index_dir(record_id) / "meta.json"


def _vectors_path(record_id: uuid.UUID) -> Path:
    return _index_dir(record_id) / "vectors.npy"


def write_record_index(
    record_id: uuid.UUID,
    chunk_ids: list[uuid.UUID],
    vectors: np.ndarray,
    provider: EmbeddingProvider,
) -> None:
    if len(chunk_ids) != len(vectors):
        raise AppError(status_code=500, detail="Index mapping is inconsistent.")
    if vectors.ndim != 2 or vectors.shape[1] != provider.dimension:
        raise AppError(status_code=500, detail="Embedding dimension mismatch.")
    with _record_lock(record_id):
        np.save(_vectors_path(record_id), vectors.astype(np.float32))
        _meta_path(record_id).write_text(
            json.dumps(
                {
                    "record_id": str(record_id),
                    "embedding_model": provider.model_id,
                    "dimension": provider.dimension,
                    "metric": "cosine_similarity",
                    "chunk_ids": [str(item) for item in chunk_ids],
                    "backend": "numpy_exact",
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def search_record_index(
    record_id: uuid.UUID,
    query_vector: list[float],
    top_k: int,
    expected_model: str,
    expected_dimension: int,
) -> list[tuple[uuid.UUID, float]]:
    with _record_lock(record_id):
        meta_file = _meta_path(record_id)
        vector_file = _vectors_path(record_id)
        if not meta_file.is_file() or not vector_file.is_file():
            return []
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if meta.get("embedding_model") != expected_model:
            raise AppError(status_code=409, detail="Index embedding model does not match the current provider.")
        if int(meta.get("dimension", 0)) != expected_dimension:
            raise AppError(status_code=409, detail="Index embedding dimension does not match the current provider.")
        matrix = np.load(vector_file)
        if len(matrix) == 0:
            return []
        query = np.asarray(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query) or 1.0
        query = query / query_norm
        row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        row_norms[row_norms == 0] = 1.0
        normalized = matrix / row_norms
        scores = normalized @ query
        k = min(top_k, len(scores))
        top_indices = np.argpartition(-scores, kth=k - 1)[:k]
        ordered = top_indices[np.argsort(-scores[top_indices])]
        chunk_ids = [uuid.UUID(item) for item in meta["chunk_ids"]]
        return [(chunk_ids[int(index)], float(scores[int(index)])) for index in ordered]


def delete_record_index(record_id: uuid.UUID) -> None:
    with _record_lock(record_id):
        folder = _index_dir(record_id)
        for child in folder.glob("*"):
            child.unlink(missing_ok=True)
