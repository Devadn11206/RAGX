import os
import asyncio
import httpx
from datetime import datetime, timedelta, timezone
import jwt

JWT_SECRET_KEY = "super_secret_phase_3_key_change_in_prod"
API_URL = "http://localhost:8000/api/v1"

def create_token(user_id: str, tenant_id: str, roles: list):
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

FILES_TO_INGEST = [
    "company_policy.txt",
    "leave_policy.txt",
    "technical_limits.txt",
    "employee_handbook.txt"
]

async def ingest_for_tenant(tenant_id: str, user_id: str = "admin_user"):
    token = create_token(user_id, tenant_id, ["admin", "employee", "hr", "manager"])
    headers = {"Authorization": f"Bearer {token}"}
    data_dir = "data/raw"
    
    print(f"\n=== INGESTING GOLDEN DATASET FOR {tenant_id} ===")
    async with httpx.AsyncClient(base_url=API_URL, headers=headers, timeout=60.0) as client:
        for filename in FILES_TO_INGEST:
            path = os.path.join(data_dir, filename)
            if not os.path.exists(path):
                print(f"[!] File not found: {path}")
                continue
                
            with open(path, "rb") as f:
                content = f.read()
                
            files = {"file": (filename, content, "text/plain")}
            data = {"classification": "internal", "allowed_roles": "admin,employee,hr,manager,user"}
            
            try:
                res = await client.post("/documents/upload", files=files, data=data)
                if res.status_code == 200:
                    resp_data = res.json()
                    print(f"[+] Ingested {filename} -> Doc ID: {resp_data.get('document_id')} ({resp_data.get('chunks_created')} chunks)")
                elif res.status_code == 409:
                    print(f"[*] {filename} is already indexed for {tenant_id}.")
                else:
                    print(f"[-] Failed to ingest {filename}: HTTP {res.status_code} - {res.text}")
            except Exception as e:
                print(f"[-] Error uploading {filename}: {e}")

async def main():
    # Ingest for both tenant_a (for golden tests) and tenant_acme (for dashboard default user)
    await ingest_for_tenant("tenant_a", "admin_a")
    await ingest_for_tenant("tenant_acme", "admin_acme")
    print("\n=== ALL INGESTION COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(main())
