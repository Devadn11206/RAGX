import asyncio
import time
import json
from app.services.rag_service import rag_service
from app.security.models import User
from app.cache.semantic_cache import semantic_cache
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.main import lifespan
from contextlib import asynccontextmanager

async def run_benchmark():
    await postgres_client.connect()
    await qdrant_client.connect()
    await semantic_cache.initialize_collection()
    
    await semantic_cache.clear_cache()

    user = User(user_id="bench_user", tenant_id="test_tenant_acme", roles=["employee"])
    
    queries = [
        "What is the company leave policy?",
        "What is the company leave policy?", # EXACT HIT
        "How many days off do I get?", # SEMANTIC HIT
        "What is the internal guide?",
        "Tell me about the internal guide", # SEMANTIC HIT
        "What is my salary?", # REJECTED
        "Public info for ACME",
        "Give me ACME public information" # SEMANTIC HIT
    ]
    
    total_latency_miss = []
    total_latency_hit = []
    
    results = []
    hits = 0
    misses = 0
    rejected = 0
    
    for q in queries:
        res = await rag_service.process_query(q, user)
        lat = res.retrieval.latency_ms
        ct = res.retrieval.cache_type
        if ct == "MISS":
            misses += 1
            total_latency_miss.append(lat)
        elif ct in ["EXACT_HIT", "SEMANTIC_HIT"]:
            hits += 1
            total_latency_hit.append(lat)
        else:
            rejected += 1
        results.append({"query": q, "cache_type": ct, "latency_ms": lat})
        
    avg_miss = sum(total_latency_miss) / len(total_latency_miss) if total_latency_miss else 0
    avg_hit = sum(total_latency_hit) / len(total_latency_hit) if total_latency_hit else 0
    
    # Calculate costs (dummy calculation based on LLM calls avoided)
    # Assume 1 LLM call = $0.001
    baseline_cost = len(queries) * 0.001
    cached_cost = misses * 0.001
    savings = (baseline_cost - cached_cost) / baseline_cost * 100
    
    report = {
        "total_requests": len(queries),
        "cache_hits": hits,
        "cache_misses": misses,
        "security_rejected": rejected,
        "cache_hit_rate": hits / len(queries) * 100,
        "llm_calls_avoided": hits,
        "estimated_savings_percent": savings,
        "average_latency_miss_ms": avg_miss,
        "average_latency_hit_ms": avg_hit,
        "details": results
    }
    
    with open("reports/semantic_cache/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print("Benchmark complete!")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(run_benchmark())
