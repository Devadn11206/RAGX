import os
import asyncio
import httpx

async def main():
    data_dir = "data/raw"
    if not os.path.exists(data_dir):
        print("data/raw not found")
        return
        
    files = [f for f in os.listdir(data_dir) if f.endswith(('.md', '.txt', '.pdf'))]
    if not files:
        print("No documents found.")
        return
        
    print(f"Found {len(files)} documents\n")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        for idx, filename in enumerate(files, 1):
            path = os.path.join(data_dir, filename)
            with open(path, "rb") as f:
                content = f.read()
                
            try:
                files_payload = {'file': (filename, content)}
                res = await client.post("/documents/upload", files=files_payload)
                if res.status_code == 200:
                    data = res.json()
                    print(f"[{idx}/{len(files)}] {filename}\n      chunks: {data['chunks_created']}\n      status: {data['status']}\n")
                elif res.status_code == 409:
                    print(f"[{idx}/{len(files)}] {filename}\n      status: already indexed\n")
                else:
                    print(f"[{idx}/{len(files)}] {filename}\n      error: {res.text}\n")
            except Exception as e:
                print(f"[{idx}/{len(files)}] {filename}\n      failed: {str(e)}\n")
                
    print("Completed.")

if __name__ == "__main__":
    asyncio.run(main())
