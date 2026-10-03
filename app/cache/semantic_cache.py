import logging
import uuid
import time
import json
import hashlib
from qdrant_client.http import models
from app.infrastructure.qdrant import qdrant_client
from app.embeddings.sentence_transformer import embedding_service
from app.security.models import User
from app.core.config import settings

logger = logging.getLogger(__name__)

CACHE_COLLECTION = "ragx_cache"
SEMANTIC_CACHE_THRESHOLD = 0.92

class QdrantSemanticCache:
    def __init__(self):
        self.collection_name = CACHE_COLLECTION

    async def initialize_collection(self):
        client = qdrant_client.client
        if not client:
            return
        try:
            exists = await client.collection_exists(self.collection_name)
            if not exists:
                logger.info(f"Creating Qdrant cache collection: {self.collection_name}")
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=embedding_service.dimension,
                        distance=models.Distance.COSINE
                    )
                )
                await client.create_payload_index(self.collection_name, "normalized_query", field_schema="keyword")
                await client.create_payload_index(self.collection_name, "security_scope_hash", field_schema="keyword")
                await client.create_payload_index(self.collection_name, "tenant_id", field_schema="keyword")
        except Exception as e:
            logger.error(f"Failed to init semantic cache collection: {str(e)}")

    def _get_security_scope_hash(self, user: User) -> str:
        # Deterministic representation of user's security scope
        # If user has specific ACL overrides (none in our Phase 3 yet, but maybe future), include them.
        scope = {
            "tenant_id": user.tenant_id,
            "roles": sorted(user.roles)
        }
        return hashlib.sha256(json.dumps(scope).encode()).hexdigest()
        
    def _normalize_query(self, query: str) -> str:
        return " ".join(query.lower().strip().split())

    async def _search_cache(self, filter_models: list, vector: list = None, threshold: float = None):
        client = qdrant_client.client
        if not client:
            return None

        # Add expiration filter automatically
        now = time.time()
        filter_models.append(
            models.FieldCondition(
                key="expires_at",
                range=models.Range(gte=now)
            )
        )

        query_filter = models.Filter(must=filter_models)

        if vector:
            results = await client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=query_filter,
                limit=1,
                with_payload=True,
                score_threshold=threshold
            )
            return results[0] if results else None
        else:
            results = await client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            return results[0][0] if results[0] else None

    async def get_exact(self, query: str, user: User, corpus_version: int):
        normalized = self._normalize_query(query)
        sec_hash = self._get_security_scope_hash(user)

        filters = [
            models.FieldCondition(key="normalized_query", match=models.MatchValue(value=normalized)),
            models.FieldCondition(key="security_scope_hash", match=models.MatchValue(value=sec_hash)),
            models.FieldCondition(key="tenant_id", match=models.MatchValue(value=user.tenant_id)),
            models.FieldCondition(key="corpus_version", match=models.MatchValue(value=corpus_version))
        ]
        
        hit = await self._search_cache(filters)
        if hit:
            logger.info(f"EXACT CACHE HIT for query: {query}")
            return hit.payload
        return None

    async def get_semantic(self, query: str, user: User, query_vector: list, corpus_version: int, threshold: float = SEMANTIC_CACHE_THRESHOLD):
        sec_hash = self._get_security_scope_hash(user)

        filters = [
            models.FieldCondition(key="security_scope_hash", match=models.MatchValue(value=sec_hash)),
            models.FieldCondition(key="tenant_id", match=models.MatchValue(value=user.tenant_id)),
            models.FieldCondition(key="corpus_version", match=models.MatchValue(value=corpus_version))
        ]

        hit = await self._search_cache(filters, vector=query_vector, threshold=threshold)
        if hit:
            logger.info(f"SEMANTIC CACHE HIT (Score: {hit.score:.4f}) for query: {query}")
            return hit.payload
        return None

    async def store(self, query: str, query_vector: list, answer: str, citations: list, user: User, corpus_version: int, ttl_seconds: int = 86400, source_document_ids: list = None):
        client = qdrant_client.client
        if not client:
            return

        normalized = self._normalize_query(query)
        sec_hash = self._get_security_scope_hash(user)
        now = time.time()
        
        cache_id = str(uuid.uuid4())
        
        payload = {
            "cache_id": cache_id,
            "query": query,
            "normalized_query": normalized,
            "tenant_id": user.tenant_id,
            "security_scope_hash": sec_hash,
            "answer": answer,
            "citations": citations,
            "corpus_version": corpus_version,
            "created_at": now,
            "expires_at": now + ttl_seconds,
            "source_document_ids": source_document_ids or []
        }

        await client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=cache_id,
                    vector=query_vector,
                    payload=payload
                )
            ]
        )

    async def invalidate_by_document(self, document_id: str):
        # Invalidates any cache entry that relied on this document
        client = qdrant_client.client
        if not client:
            return
            
        await client.delete(
            collection_name=self.collection_name,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_document_ids",
                        match=models.MatchValue(value=document_id)
                    )
                ]
            )
        )
        
    async def clear_cache(self):
        client = qdrant_client.client
        if not client:
            return
        # A simple hack for clearing is to delete the collection and recreate
        try:
            await client.delete_collection(self.collection_name)
        except Exception:
            pass
        await self.initialize_collection()

semantic_cache = QdrantSemanticCache()
