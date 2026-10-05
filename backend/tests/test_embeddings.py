"""Embedding providers must stay labeled and dimensionally consistent."""

from app.services.embeddings.providers import (
    HashedTokenEmbeddingProvider,
    TestHashEmbeddingProvider,
    get_embedding_provider,
)


def test_test_hash_provider_is_deterministic() -> None:
    provider = TestHashEmbeddingProvider()
    first = provider.embed(["denied chest pain"])
    second = provider.embed(["denied chest pain"])
    assert provider.model_id == "test-hash-v1"
    assert len(first[0]) == provider.dimension == 32
    assert first == second
    other = provider.embed(["unrelated laboratory comment"])
    assert first != other


def test_get_embedding_provider_uses_test_double_in_tests() -> None:
    provider = get_embedding_provider()
    assert provider.model_id == "test-hash-v1"
    assert not isinstance(provider, HashedTokenEmbeddingProvider)
