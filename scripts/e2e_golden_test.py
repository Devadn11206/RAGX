import asyncio
import sys
import io
import time
from app.services.rag_service import rag_service
from app.security.models import User
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.cache.semantic_cache import semantic_cache
from app.telemetry.service import telemetry_service

# Windows cp1252 workaround -- force UTF-8 output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

async def run_e2e_golden():
    print("Starting E2E Golden Pipeline Test...")
    
    # 1. Initialize infra
    await postgres_client.connect()
    await qdrant_client.connect()
    await semantic_cache.initialize_collection()
    
    user = User(user_id="e2e_tester", tenant_id="tenant_a", roles=["admin"])
    
    # 2. Run queries
    queries = [
        "What are the standard working hours?",
        "Tell me about the company leave policy.",
        "What is the maximum upload size for a file?"
    ]
    
    passed = 0
    total_checks = len(queries) + 1  # +1 for telemetry check
    
    for q in queries:
        print(f"\nEvaluating: '{q}'")
        try:
            res = await rag_service.process_query(q, user, is_test_run=True)
            
            provider = res.retrieval.provider or "none"
            tier = res.retrieval.router_tier or "unknown"
            cost = res.retrieval.estimated_cost or 0.0
            answer_preview = (res.answer or "")[:80]
            
            print(f"  Provider   : {provider}")
            print(f"  Router Tier: {tier}")
            print(f"  Cost       : ${cost:.5f}")
            print(f"  Answer     : {answer_preview}...")
            
            if res.answer and len(res.answer) > 10:
                print("  [PASS] Answer generated successfully")
                passed += 1
            else:
                print("  [FAIL] Empty or very short answer returned")
        except Exception as e:
            print(f"  [FAIL] Exception during query: {e}")
            
    # 3. Check telemetry
    print("\nTelemetry Check:")
    try:
        metrics = telemetry_service.get_global_metrics()
        print(f"  Total logged queries: {metrics['total_queries']}")
        print(f"  Gemini calls        : {metrics.get('gemini_count', 0)}")
        print(f"  Groq calls          : {metrics.get('groq_count', 0)}")
        print(f"  Avg latency         : {metrics.get('avg_latency', 0):.0f} ms")
        if metrics['total_queries'] > 0:
            print("  [PASS] Telemetry aggregation working")
            passed += 1
        else:
            print("  [FAIL] No telemetry events recorded")
    except Exception as e:
        print(f"  [FAIL] Telemetry check error: {e}")
        
    print(f"\nGolden Test Complete: {passed}/{total_checks} checks passed.")

if __name__ == "__main__":
    asyncio.run(run_e2e_golden())
