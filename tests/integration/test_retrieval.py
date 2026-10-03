import pytest
from app.embeddings.sentence_transformer import embedding_service
from app.retrieval.qdrant_store import qdrant_store

@pytest.mark.asyncio
async def test_embedding_generation():
    embedding_service.initialize()
    vectors = embedding_service.embed_documents(["Test doc"])
    assert len(vectors) == 1
    assert len(vectors[0]) == embedding_service.dimension
