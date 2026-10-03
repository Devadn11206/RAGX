import os
import asyncio
import json
from datetime import datetime, timezone
from app.security.models import User
from app.services.rag_service import rag_service
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.infrastructure.neo4j import neo4j_client

GOLDEN_TEST_CASES = [
    {
        "id": "TC-SEM-01",
        "query": "What are the standard working hours?",
        "expected_facts": ["9:00 AM", "6:00 PM"],
        "expected_source": "company_policy.txt"
    },
    {
        "id": "TC-SEM-02",
        "query": "What is the company leave policy?",
        "expected_facts": ["24 days"],
        "expected_source": "leave_policy.txt"
    },
    {
        "id": "TC-SEM-03",
        "query": "What is the maximum upload size for a file?",
        "expected_facts": ["50 MB"],
        "expected_source": "technical_limits.txt"
    }
]

async def run_semantic_test():
    print("=" * 70)
    print("RAGX SEMANTIC GOLDEN TEST SUITE (PART 6)")
    print("Evaluating PIPELINE RESILIENCE & FACTUAL ANSWER CORRECTNESS")
    print("=" * 70)
    
    await postgres_client.connect()
    await qdrant_client.connect()
    await neo4j_client.connect()
    
    user = User(user_id="alice", tenant_id="tenant_a", roles=["employee", "admin"], active=True)
    results = []
    
    for tc in GOLDEN_TEST_CASES:
        print(f"\n--- Running Test: {tc['id']} ---")
        print(f"Query: \"{tc['query']}\"")
        print(f"Expected Facts: {tc['expected_facts']}")
        print(f"Expected Source: {tc['expected_source']}")
        
        try:
            res = await rag_service.process_query(tc["query"], user, top_k=5, mode="hybrid")
            answer = res.answer or ""
            sources = res.sources or []
            retrieval = res.retrieval
            
            print(f"Answer: {answer}")
            print(f"Sources: {[s.filename for s in sources]}")
            print(f"Provider: {retrieval.provider} | Model: {retrieval.model} | Fallback: {retrieval.fallback_used}")
            print(f"Cache Status: {retrieval.cache_type} | Latency: {retrieval.latency_ms} ms")
            
            pipeline_success = bool(answer and len(answer) > 10)
            
            answer_lower = answer.lower()
            facts_matched = [f for f in tc["expected_facts"] if f.lower() in answer_lower]
            all_facts_present = len(facts_matched) == len(tc["expected_facts"])
            
            refusal_phrases = ["couldn't find enough information", "cannot find", "do not have enough information", "not mentioned in the context"]
            is_refusal = any(p in answer_lower for p in refusal_phrases)
            
            answer_correct = all_facts_present and not is_refusal
            citation_matched = any(tc["expected_source"] in s.filename for s in sources)
            
            print(f"Pipeline Success: {'PASS' if pipeline_success else 'FAIL'}")
            print(f"Facts Matched: {facts_matched}/{tc['expected_facts']}")
            print(f"Answer Correctness: {'PASS (Factual match)' if answer_correct else 'FAIL (Facts missing or refusal)'}")
            print(f"Citation Correctness: {'PASS' if citation_matched else 'WARNING (Source filename not in top sources)'}")
            
            results.append({
                "id": tc["id"],
                "query": tc["query"],
                "answer": answer,
                "pipeline_success": pipeline_success,
                "answer_correct": answer_correct,
                "citation_matched": citation_matched,
                "provider": retrieval.provider,
                "fallback_used": retrieval.fallback_used,
                "latency_ms": retrieval.latency_ms,
                "sources": [s.filename for s in sources]
            })
            
        except Exception as e:
            print(f"[-] Exception: {e}")
            results.append({"id": tc["id"], "pipeline_success": False, "answer_correct": False, "error": str(e)})
            
    print("\n" + "=" * 70)
    print("SEMANTIC GOLDEN TEST SUMMARY")
    print("=" * 70)
    all_pipeline = all(r.get("pipeline_success") for r in results)
    all_semantic = all(r.get("answer_correct") for r in results)
    for r in results:
        print(f"[{r['id']}] Pipeline: {'PASS' if r.get('pipeline_success') else 'FAIL'} | Semantic Answer: {'PASS' if r.get('answer_correct') else 'FAIL'} | Provider: {r.get('provider')} (Fallback: {r.get('fallback_used')})")
        
    print(f"\nTotal Pipeline: {'ALL PASSED' if all_pipeline else 'SOME FAILED'}")
    print(f"Total Semantic Correctness: {'ALL PASSED' if all_semantic else 'SOME FAILED'}")
    
    os.makedirs("reports/evaluation", exist_ok=True)
    with open("reports/evaluation/semantic_golden_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results,
            "all_pipeline_success": all_pipeline,
            "all_semantic_correctness": all_semantic
        }, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_semantic_test())
