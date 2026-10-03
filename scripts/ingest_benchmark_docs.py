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

async def main():
    tenant_id = "tenant_benchmark"
    token = create_token("bench_user", tenant_id, ["tenant_user", "admin"])
    headers = {"Authorization": f"Bearer {token}"}
    data_dir = "data/raw"
    
    print(f"\n=== INGESTING BENCHMARK DATASET FOR {tenant_id} ===")
    async with httpx.AsyncClient(base_url=API_URL, headers=headers, timeout=60.0) as client:
        files = [f for f in os.listdir(data_dir) if f.endswith(('.md', '.txt'))]
        for filename in files:
            path = os.path.join(data_dir, filename)
            with open(path, "rb") as f:
                content = f.read()
                
            files_payload = {"file": (filename, content, "text/plain")}
            data = {"classification": "internal", "allowed_roles": "tenant_user,admin,employee,hr,manager"}
            
            try:
                res = await client.post("/documents/upload", files=files_payload, data=data)
                if res.status_code == 200:
                    resp_data = res.json()
                    print(f"[+] Ingested {filename} -> Doc ID: {resp_data.get('document_id')}")
                elif res.status_code == 409:
                    print(f"[*] {filename} is already indexed.")
                else:
                    print(f"[-] Failed to ingest {filename}: HTTP {res.status_code} - {res.text}")
            except Exception as e:
                print(f"[-] Error uploading {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
