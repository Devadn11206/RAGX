import asyncio
import os
import json
from datetime import timedelta
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.retrieval.qdrant_store import qdrant_store
from app.services.document_service import document_service
from app.security.jwt import create_access_token
from app.core.config import settings
from app.embeddings.sentence_transformer import embedding_service

async def init_services():
    await postgres_client.connect()
    await qdrant_client.connect()
    embedding_service.initialize()
    await document_service.init_db()
    await qdrant_store.initialize_collection()

async def seed():
    print("Initializing services...")
    await init_services()

    tenants = ["tenant_acme", "tenant_globex", "tenant_initech"]
    docs = {
        "Employee Handbook": "public",
        "Engineering Guide": "internal",
        "HR Salary Data": "confidential",
        "Executive Compensation": "restricted"
    }
    
    contents = {
        "Employee Handbook": "This is the employee handbook for {tenant}. Everyone gets 20 days of leave.",
        "Engineering Guide": "This is the engineering guide for {tenant}. We use Python and Go.",
        "HR Salary Data": "HR Salary Data for {tenant}. Average salary is $100,000.",
        "Executive Compensation": "Executive Compensation for {tenant}. The CEO makes $1,000,000."
    }

    print("Seeding documents...")
    for tenant in tenants:
        for title, classification in docs.items():
            filename = f"{title.replace(' ', '_').lower()}.txt"
            content_str = contents[title].format(tenant=tenant)
            
            allowed_roles = []
            if classification == "internal":
                allowed_roles = ["employee", "manager", "hr", "admin"]
            elif classification == "confidential":
                allowed_roles = ["hr", "admin"]
            elif classification == "restricted":
                allowed_roles = ["admin"]

            try:
                res = await document_service.upload_document(
                    filename=filename,
                    content=content_str.encode('utf-8'),
                    tenant_id=tenant,
                    classification=classification,
                    allowed_roles=allowed_roles,
                    allowed_users=[]
                )
                print(f"Uploaded {filename} for {tenant} -> {res['document_id']}")
            except Exception as e:
                if "Duplicate" in str(e) or "already indexed" in str(e):
                    print(f"Skipping {filename} for {tenant} (already indexed)")
                else:
                    print(f"Failed to upload {filename} for {tenant}: {e}")

    # Generate JWTs for test users
    print("\nGenerating JWTs for Test Users:")
    users = [
        {"user_id": "alice", "tenant_id": "tenant_acme", "roles": ["employee"]},
        {"user_id": "bob", "tenant_id": "tenant_acme", "roles": ["hr"]},
        {"user_id": "charlie", "tenant_id": "tenant_globex", "roles": ["employee"]},
        {"user_id": "diana", "tenant_id": "tenant_globex", "roles": ["admin"]},
        {"user_id": "eve", "tenant_id": "tenant_initech", "roles": ["manager"]}
    ]
    
    for u in users:
        token = create_access_token(data={"sub": u["user_id"], "tenant_id": u["tenant_id"], "roles": u["roles"]}, expires_delta=timedelta(days=365))
        print(f"User: {u['user_id']} ({u['tenant_id']}, {u['roles']})")
        print(f"Token: {token}\n")

    print("Seed complete.")
    await postgres_client.close()
    await qdrant_client.close()

if __name__ == "__main__":
    asyncio.run(seed())
