import asyncio
import argparse
from app.evaluation.runner import EvaluationRunner
from app.infrastructure.qdrant import qdrant_client
from app.infrastructure.postgres import postgres_client

async def main():
    parser = argparse.ArgumentParser(description="Run RAGX Evaluation")
    parser.add_argument("--judge", action="store_true", help="Enable LLM Judge (costs money)")
    parser.add_argument("--retrieval-only", action="store_true", help="Run only retrieval metrics")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions")
    parser.add_argument("--top-k", type=int, default=5, help="Top K retrieval")
    args = parser.parse_args()
    
    await qdrant_client.connect()
    await postgres_client.connect()
    
    try:
        runner = EvaluationRunner(use_judge=args.judge, retrieval_only=args.retrieval_only, top_k=args.top_k)
        await runner.run("data/evaluation/evaluation_dataset.json", limit=args.limit)
    finally:
        await qdrant_client.close()
        await postgres_client.close()

if __name__ == "__main__":
    asyncio.run(main())
