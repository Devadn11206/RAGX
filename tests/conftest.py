import pytest
import pytest_asyncio
import jwt
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
import asyncio
from app.main import app
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.embeddings.sentence_transformer import embedding_service
from app.reranking.cross_encoder import local_cross_encoder_reranker
import json

JWT_SECRET_KEY = "super_secret_phase_3_key_change_in_prod"


@pytest.fixture()
def client():
    # Hit the actual running server on port 8000
    return AsyncClient(base_url="http://localhost:8000")

def create_token(user_id: str, tenant_id: str, roles: list) -> str:
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_security_data():
    # Setup test data
    from app.infrastructure.neo4j import neo4j_client
    
    if not postgres_client.pool:
        await postgres_client.connect()
    if not qdrant_client.client:
        await qdrant_client.connect()
    if not neo4j_client.driver:
        await neo4j_client.connect()
        
    tenants = ["test_tenant_acme", "test_tenant_globex", "test_tenant_initech"]
    
    # 1. Clear old test data from Postgres
    async with postgres_client.pool.acquire() as conn:
        await conn.execute("DELETE FROM documents WHERE tenant_id LIKE 'test_tenant_%'")
        await conn.execute("DELETE FROM audit_events WHERE tenant_id LIKE 'test_tenant_%'")
        
    if neo4j_client.driver:
        async with neo4j_client.driver.session() as session:
            await session.run("MATCH (n) WHERE n.tenant_id STARTS WITH 'test_tenant_' DETACH DELETE n")
        
    from app.core.config import settings
    from qdrant_client.http import models as qmodels
    for tenant in tenants:
        await qdrant_client.client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="tenant_id",
                            match=qmodels.MatchValue(value=tenant)
                        )
                    ]
                )
            )
        )

    # Load canaries
    with open("data/security/canaries.json", "r") as f:
        canaries = json.load(f)

    from app.services.document_service import document_service
    
    docs_to_create = [
        {"tenant": "test_tenant_acme", "class": "public", "roles": [], "content": f"ACME Public Info. {canaries['test_tenant_acme']}"},
        {"tenant": "test_tenant_acme", "class": "internal", "roles": ["employee", "manager", "hr", "admin"], "content": "ACME Internal Guide."},
        {"tenant": "test_tenant_acme", "class": "confidential", "roles": ["manager", "hr", "admin"], "content": "ACME Confidential Strategy."},
        {"tenant": "test_tenant_acme", "class": "restricted", "roles": ["admin"], "content": "ACME Restricted Admin Ops."},
        
        {"tenant": "test_tenant_globex", "class": "public", "roles": [], "content": f"Globex Public Info. {canaries['test_tenant_globex']}"},
        {"tenant": "test_tenant_globex", "class": "restricted", "roles": ["admin"], "content": "Globex Restricted Salary Data."}
    ]
    
    for doc in docs_to_create:
        await document_service.upload_document(
            filename=f"doc_{doc['tenant']}_{doc['class']}.txt",
            content=doc["content"].encode("utf-8"),
            tenant_id=doc["tenant"],
            classification=doc["class"],
            allowed_roles=doc["roles"],
            allowed_users=[]
        )
    
    yield
    
    if postgres_client.pool:
        await postgres_client.pool.close()
        postgres_client.pool = None
    if neo4j_client.driver:
        await neo4j_client.driver.close()
        neo4j_client.driver = None

@pytest.fixture
def test_users():
    return {
        "acme_employee": create_token("acme_emp", "test_tenant_acme", ["employee"]),
        "acme_hr": create_token("acme_hr", "test_tenant_acme", ["hr"]),
        "acme_admin": create_token("acme_admin", "test_tenant_acme", ["admin"]),
        "globex_employee": create_token("globex_emp", "test_tenant_globex", ["employee"]),
        "globex_admin": create_token("globex_admin", "test_tenant_globex", ["admin"]),
    }
