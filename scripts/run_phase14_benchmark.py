import json
import time
import os
import asyncio
import math
from collections import defaultdict
from typing import List, Dict, Any

# Set environment before importing app modules
os.environ["APP_ENV"] = "test"

# Import app modules
from app.core.config import settings
from app.services.rag_service import rag_service
from app.security.models import User
from app.telemetry.service import telemetry_service
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.infrastructure.redis import redis_client
from app.infrastructure.neo4j import neo4j_client
from app.services.document_service import document_service
from app.retrieval.qdrant_store import qdrant_store
from app.cache.semantic_cache import semantic_cache
from app.services.graph_service import graph_service
from app.embeddings.sentence_transformer import embedding_service
from app.reranking.cross_encoder import local_cross_encoder_reranker

bench_user = User(
    user_id="bench_user",
    tenant_id="tenant_benchmark",
    email="bench@example.com",
    roles=["tenant_user"]
)

def compute_f1(pred: str, truth: str) -> float:
    pred_tokens = set(pred.lower().split())
    truth_tokens = set(truth.lower().split())
    if not pred_tokens or not truth_tokens:
        return 0.0
    common = pred_tokens.intersection(truth_tokens)
    if not common:
        return 0.0
    prec = len(common) / len(pred_tokens)
    rec = len(common) / len(truth_tokens)
    return 2 * (prec * rec) / (prec + rec)

def compute_em(pred: str, truth: str) -> int:
    return 1 if truth.lower() in pred.lower() or pred.lower() == truth.lower() else 0

def compute_recall_at_k(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
    retrieved_k = set(retrieved_docs[:k])
    relevant_set = set(relevant_docs)
    if not relevant_set: return 1.0
    hits = len(retrieved_k.intersection(relevant_set))
    return hits / len(relevant_set)

def compute_mrr(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
    relevant_set = set(relevant_docs)
    for i, doc in enumerate(retrieved_docs):
        if doc in relevant_set:
            return 1.0 / (i + 1)
    return 0.0

def compute_ndcg(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
    relevant_set = set(relevant_docs)
    dcg = 0.0
    idcg = 0.0
    for i in range(min(k, len(retrieved_docs))):
        if retrieved_docs[i] in relevant_set:
            dcg += 1.0 / math.log2(i + 2)
    for i in range(min(k, len(relevant_set))):
        idcg += 1.0 / math.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0

def compute_diversity(chunks: List[str]) -> float:
    if not chunks: return 0.0
    unique = set(chunks)
    return len(unique) / len(chunks)

async def run_pipeline_benchmark(name: str, questions: List[Dict], mode: str, rerank: bool, mmr: bool) -> Dict:
    settings.RERANKING_ENABLED = rerank
    settings.RERANK_SELECTION = "mmr" if mmr else "score"
    settings.HYBRID_FINAL_K = 10
    
    results = []
    
    for q in questions:
        start = time.time()
        try:
            res = await rag_service.process_query(q["question"], bench_user, top_k=10, mode=mode, is_test_run=True)
            total_latency = (time.time() - start) * 1000
            
            ans = res.answer
            sources = [s.filename for s in res.sources]
            chunks = [s.chunk_id for s in res.sources]
            
            f1 = compute_f1(ans, q["reference_answer"])
            em = compute_em(ans, q["reference_answer"])
            
            r1 = compute_recall_at_k(sources, q["source_documents"], 1)
            r3 = compute_recall_at_k(sources, q["source_documents"], 3)
            r5 = compute_recall_at_k(sources, q["source_documents"], 5)
            r10 = compute_recall_at_k(sources, q["source_documents"], 10)
            
            mrr = compute_mrr(sources, q["source_documents"])
            ndcg = compute_ndcg(sources, q["source_documents"], 10)
            diversity = compute_diversity(chunks)
            
            retrieval_latency = getattr(res.retrieval, "latency_ms", 0)
            reranking_latency = getattr(res.reranking, "latency_ms", 0) if res.reranking else 0
            gen_latency = total_latency - retrieval_latency - reranking_latency
            
            results.append({
                "question_type": q["question_type"],
                "f1": f1,
                "em": em,
                "recall_1": r1,
                "recall_3": r3,
                "recall_5": r5,
                "recall_10": r10,
                "mrr": mrr,
                "ndcg": ndcg,
                "diversity": diversity,
                "total_latency": total_latency,
                "retrieval_latency": retrieval_latency,
                "reranking_latency": reranking_latency,
                "gen_latency": gen_latency,
                "cost": getattr(res.retrieval, "estimated_cost", 0.0)
            })
            await asyncio.sleep(3.5)
        except Exception as e:
            import traceback
            print(f"Error on question {q['question_id']}: {e}")
            traceback.print_exc()
            
    if not results: return {}
    
    def avg(key, res_list): return sum(r[key] for r in res_list) / len(res_list)
    
    total_lats = sorted(r["total_latency"] for r in results)
    p50 = total_lats[len(total_lats)//2]
    p95 = total_lats[int(len(total_lats)*0.95)] if len(total_lats) >= 20 else total_lats[-1]
    p99 = total_lats[int(len(total_lats)*0.99)] if len(total_lats) >= 50 else total_lats[-1]
    
    multi_hop = [r for r in results if r["question_type"] == "multi_hop"]
    single_hop = [r for r in results if r["question_type"] != "multi_hop"]
    
    return {
        "pipeline": name,
        "f1": avg("f1", results),
        "em": avg("em", results),
        "recall_1": avg("recall_1", results),
        "recall_3": avg("recall_3", results),
        "recall_5": avg("recall_5", results),
        "recall_10": avg("recall_10", results),
        "mrr": avg("mrr", results),
        "ndcg": avg("ndcg", results),
        "diversity": avg("diversity", results),
        "p50_latency": p50,
        "p95_latency": p95,
        "p99_latency": p99,
        "avg_retrieval_latency": avg("retrieval_latency", results),
        "avg_reranking_latency": avg("reranking_latency", results),
        "avg_gen_latency": avg("gen_latency", results),
        "avg_cost": avg("cost", results),
        "multi_hop_f1": avg("f1", multi_hop) if multi_hop else 0,
        "single_hop_f1": avg("f1", single_hop) if single_hop else 0,
        "raw_results": results
    }

async def main():
    print("Setting up infrastructure...")
    await postgres_client.connect()
    await qdrant_client.connect()
    await redis_client.connect()
    await neo4j_client.connect()
    
    await document_service.init_db()
    await qdrant_store.initialize_collection()
    await semantic_cache.initialize_collection()
    await graph_service.initialize_schema()
    
    embedding_service.warmup()
    local_cross_encoder_reranker.warmup()
    print("Infrastructure ready.")
    
    os.makedirs("reports/phase14", exist_ok=True)
    
    with open("data/evaluation/phase14_benchmark_dataset.json", "r") as f:
        dataset = json.load(f)["questions"]
        
    print(f"Loaded {len(dataset)} questions. Starting benchmark...")
    
    pipelines = [
        {"name": "Vector", "mode": "vector", "rerank": False, "mmr": False},
        {"name": "Vector + Lexical", "mode": "vector,lexical", "rerank": False, "mmr": False},
        {"name": "Hybrid", "mode": "auto", "rerank": False, "mmr": False},
        {"name": "Hybrid + GraphRAG", "mode": "vector,lexical,graph", "rerank": False, "mmr": False},
        {"name": "Hybrid + Reranking", "mode": "vector,lexical,graph", "rerank": True, "mmr": False},
        {"name": "Hybrid + Reranking + MMR", "mode": "vector,lexical,graph", "rerank": True, "mmr": True},
    ]
    
    summary = []
    
    for p in pipelines:
        print(f"\nRunning {p['name']}...")
        res = await run_pipeline_benchmark(p["name"], dataset, p["mode"], p["rerank"], p["mmr"])
        summary.append(res)
        
        safe_name = p["name"].lower().replace(" ", "").replace("+", "_")
        with open(f"reports/phase14/{safe_name}_results.json", "w") as f:
            json.dump(res, f, indent=2)
            
    csv_lines = ["Pipeline,Recall@5,MRR,nDCG,F1,Exact Match,P50 Latency,P95 Latency,P99 Latency,Retrieval Latency,Reranking Latency,Generation Latency,Cost Per Query"]
    for s in summary:
        if not s: continue
        line = f"{s['pipeline']},{s['recall_5']:.3f},{s['mrr']:.3f},{s['ndcg']:.3f},{s['f1']:.3f},{s['em']:.3f},{s['p50_latency']:.0f},{s['p95_latency']:.0f},{s['p99_latency']:.0f},{s['avg_retrieval_latency']:.0f},{s['avg_reranking_latency']:.0f},{s['avg_gen_latency']:.0f},{s['avg_cost']:.6f}"
        csv_lines.append(line)
        
    with open("reports/phase14/final_benchmark_table.csv", "w") as f:
        f.write("\n".join(csv_lines))
        
    # Generate Cache Benchmark
    print("\nRunning Cache Benchmark...")
    settings.RERANKING_ENABLED = False
    cache_qs = dataset[:5]
    
    # Cold run
    for q in cache_qs:
        await rag_service.process_query(q["question"], bench_user, mode="vector", is_test_run=True)
        await asyncio.sleep(1.5)
        
    # Warm run
    cache_hits = 0
    cache_latencies = []
    for q in cache_qs:
        start = time.time()
        res = await rag_service.process_query(q["question"], bench_user, mode="vector", is_test_run=True)
        latency = (time.time() - start) * 1000
        cache_latencies.append(latency)
        if getattr(res.retrieval, "cache_type", "") != "MISS":
            cache_hits += 1
            
    cache_res = {
        "hit_rate": cache_hits / len(cache_qs),
        "avg_latency": sum(cache_latencies) / len(cache_latencies)
    }
    with open("reports/phase14/cache_results.json", "w") as f:
        json.dump(cache_res, f, indent=2)
    print(f"Cache Hit Rate: {cache_res['hit_rate']*100}%, Avg Latency: {cache_res['avg_latency']:.0f}ms")
        
    print("\nBenchmark Complete!")
    await postgres_client.close()
    await qdrant_client.close()
    await redis_client.close()
    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
