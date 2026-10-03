import asyncio
import json
import os
import time
from app.services.rag_service import rag_service
from app.security.models import User
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.cache.semantic_cache import semantic_cache
from app.llm.gemini import llm_client as gemini_client
from app.llm.circuit_breaker import gemini_circuit_breaker
from app.llm.models import ProviderTimeoutError, ProviderError

queries = [
    {"q": "What is the company leave policy?", "trigger": None},
    {"q": "What is the internal guide?", "trigger": "timeout"},
    {"q": "Why does the internal guide exist?", "trigger": "500"},
    {"q": "What happens if I fail on purpose?", "trigger": "timeout"}, 
    {"q": "Tell me about ACME.", "trigger": "timeout"},
    {"q": "Tell me about Globex.", "trigger": "timeout"},
    {"q": "Tell me about security.", "trigger": "timeout"},
    {"q": "Tell me about benefits.", "trigger": "timeout"}, # circuit breaker opens here
    {"q": "Tell me about remote work.", "trigger": None},
    {"q": "Tell me about offices.", "trigger": None},
]

async def run_benchmark():
    await postgres_client.connect()
    await qdrant_client.connect()
    await semantic_cache.initialize_collection()
    
    user = User(user_id="bench_user", tenant_id="test_tenant_acme", roles=["employee"])
    results = []
    
    await semantic_cache.clear_cache()
    
    total = len(queries)
    gemini_success = 0
    groq_fallback = 0
    final_success = 0
    total_cost = 0.0
    total_latency = 0
    
    # Save original generate
    original_generate = gemini_client.generate
    
    for item in queries:
        query_text = item['q']
        
        # Mock behavior based on trigger
        if item['trigger'] == "timeout":
            def mock_generate(*args, **kwargs):
                raise ProviderTimeoutError("Simulated Timeout")
            gemini_client.generate = mock_generate
        elif item['trigger'] == "500":
            def mock_generate(*args, **kwargs):
                raise ProviderError("Simulated 500")
            gemini_client.generate = mock_generate
        else:
            gemini_client.generate = original_generate
            
        start = time.time()
        res = await rag_service.process_query(query_text, user)
        latency = int((time.time() - start) * 1000)
        
        provider = res.retrieval.provider
        fallback_used = res.retrieval.fallback_used
        
        if provider == "gemini":
            gemini_success += 1
            final_success += 1
        elif provider == "groq":
            groq_fallback += 1
            final_success += 1
            
        total_cost += (res.retrieval.estimated_cost or 0)
        total_latency += latency
        
        results.append({
            "query": item['q'],
            "provider": provider,
            "fallback_used": fallback_used,
            "fallback_reason": res.retrieval.fallback_reason,
            "latency_ms": latency
        })
        
        time.sleep(0.1)
        
    report = {
        "total_requests": total,
        "gemini_success_rate": (gemini_success / total) * 100,
        "groq_fallback_rate": (groq_fallback / total) * 100,
        "final_success_rate": (final_success / total) * 100,
        "average_cost": total_cost / total,
        "average_latency_ms": total_latency / total,
        "circuit_breaker_state": gemini_circuit_breaker.state,
        "details": results
    }
    
    os.makedirs("reports/provider", exist_ok=True)
    with open("reports/provider/benchmark_results.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(run_benchmark())
