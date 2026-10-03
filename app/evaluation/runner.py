import time
import asyncio
import uuid
import json
import os
import pandas as pd
from datetime import datetime, timezone
from typing import List

from app.core.config import settings
from app.evaluation.schemas import EvalDataset, QuestionResult
from app.evaluation.retrieval_metrics import calculate_hit_at_k, calculate_recall_at_k, calculate_mrr
from app.evaluation.cost import calculate_cost
from app.evaluation.judge import LLMJudge

from app.retrieval.hybrid_retriever import hybrid_retriever
from app.llm.orchestrator import llm_orchestrator
from app.llm.prompts import RAG_SYSTEM_PROMPT
from app.rag.context import ContextBuilder

class EvaluationRunner:
    def __init__(self, use_judge: bool = False, retrieval_only: bool = False, top_k: int = 5):
        self.run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        self.use_judge = use_judge
        self.retrieval_only = retrieval_only
        self.top_k = top_k
        self.retriever = hybrid_retriever
        self.judge = LLMJudge() if use_judge else None

    async def run(self, dataset_path: str, limit: int = None):
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset = EvalDataset(**data)
        
        questions = dataset.questions[:limit] if limit else dataset.questions
        results = []
        
        for q in questions:
            res = await self._evaluate_question(q)
            results.append(res)
            
        self._save_results(dataset.dataset_version, results)
        
    async def _evaluate_question(self, q) -> QuestionResult:
        try:
            # Retrieval
            from app.security.models import User
            mock_user = User(user_id="eval_user", tenant_id="tenant_a", roles=["admin"], active=True)
            t0 = time.monotonic()
            results = await self.retriever.retrieve(q.question, user=mock_user, top_k=self.top_k, mode="auto")
            hits = [r.dict() for r in results]
            t1 = time.monotonic()
            retrieval_latency = (t1 - t0) * 1000
            
            retrieved_chunk_ids = [h['chunk_id'] for h in hits]
            
            # Retrieval metrics
            hit1 = calculate_hit_at_k(q.expected_chunk_ids, retrieved_chunk_ids, 1)
            hit3 = calculate_hit_at_k(q.expected_chunk_ids, retrieved_chunk_ids, 3)
            hit5 = calculate_hit_at_k(q.expected_chunk_ids, retrieved_chunk_ids, 5)
            rec5 = calculate_recall_at_k(q.expected_chunk_ids, retrieved_chunk_ids, 5)
            mrr = calculate_mrr(q.expected_chunk_ids, retrieved_chunk_ids)
            
            context = ContextBuilder.build(hits)
            
            # Generation
            generation_latency = 0.0
            generated_answer = None
            cost = None
            input_tokens = None
            output_tokens = None
            total_tokens = None
            
            correctness = None
            relevance = None
            faithfulness = None
            
            if not self.retrieval_only:
                prompt = RAG_SYSTEM_PROMPT.format(context=context, question=q.question)
                t2 = time.monotonic()
                res = llm_orchestrator.generate(prompt)
                generated_answer = res.content
                t3 = time.monotonic()
                generation_latency = (t3 - t2) * 1000
                
                # Use real cost/tokens if available from orchestrator response or mock it
                input_tokens = len(prompt) // 4
                output_tokens = len(generated_answer) // 4
                total_tokens = input_tokens + output_tokens
                cost = res.estimated_cost
                
                # Judging
                if self.judge:
                    j_out = self.judge.evaluate(q.question, q.reference_answer, context, generated_answer)
                    if j_out:
                        correctness = j_out.correctness
                        relevance = j_out.relevance
                        faithfulness = j_out.faithfulness

            total_latency = retrieval_latency + generation_latency
            
            return QuestionResult(
                run_id=self.run_id,
                question_id=q.question_id,
                question=q.question,
                question_type=q.question_type,
                difficulty=q.difficulty,
                reference_answer=q.reference_answer,
                generated_answer=generated_answer,
                expected_chunk_ids=q.expected_chunk_ids,
                retrieved_chunk_ids=retrieved_chunk_ids,
                retrieval_hit_at_1=hit1,
                retrieval_hit_at_3=hit3,
                retrieval_hit_at_5=hit5,
                recall_at_5=rec5,
                mrr=mrr,
                answer_correctness=correctness,
                answer_relevance=relevance,
                faithfulness=faithfulness,
                retrieval_latency_ms=retrieval_latency,
                generation_latency_ms=generation_latency,
                total_latency_ms=total_latency,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=cost,
                status="success"
            )
            
        except Exception as e:
            return QuestionResult(
                run_id=self.run_id,
                question_id=q.question_id,
                question=q.question,
                question_type=q.question_type,
                difficulty=q.difficulty,
                reference_answer=q.reference_answer,
                generated_answer=None,
                expected_chunk_ids=q.expected_chunk_ids,
                retrieved_chunk_ids=[],
                retrieval_hit_at_1=0.0,
                retrieval_hit_at_3=0.0,
                retrieval_hit_at_5=0.0,
                recall_at_5=0.0,
                mrr=0.0,
                answer_correctness=None,
                answer_relevance=None,
                faithfulness=None,
                retrieval_latency_ms=0.0,
                generation_latency_ms=0.0,
                total_latency_ms=0.0,
                input_tokens=None,
                output_tokens=None,
                total_tokens=None,
                estimated_cost_usd=None,
                status="error",
                error=str(e)
            )

    def _save_results(self, dataset_version: str, results: List[QuestionResult]):
        run_dir = f"data/evaluation/results/{self.run_id}"
        os.makedirs(run_dir, exist_ok=True)
        
        # Save JSON
        res_dicts = [r.dict() for r in results]
        with open(f"{run_dir}/evaluation_results.json", "w", encoding="utf-8") as f:
            json.dump(res_dicts, f, indent=2)
            
        # Save CSV
        df = pd.DataFrame(res_dicts)
        df.to_csv(f"{run_dir}/evaluation_results.csv", index=False)
        
        # Summary
        success_df = df[df['status'] == 'success']
        if not success_df.empty:
            summary = {
                "run_id": self.run_id,
                "dataset_version": dataset_version,
                "dataset_size": len(results),
                "successful_questions": len(success_df),
                "failed_questions": len(df) - len(success_df),
                "retrieval": {
                    "hit_at_1": success_df['retrieval_hit_at_1'].mean(),
                    "hit_at_3": success_df['retrieval_hit_at_3'].mean(),
                    "hit_at_5": success_df['retrieval_hit_at_5'].mean(),
                    "recall_at_5": success_df['recall_at_5'].mean(),
                    "mrr": success_df['mrr'].mean(),
                },
                "answer": {
                    "correctness": success_df['answer_correctness'].mean() if self.use_judge else None,
                    "relevance": success_df['answer_relevance'].mean() if self.use_judge else None,
                    "faithfulness": success_df['faithfulness'].mean() if self.use_judge else None,
                },
                "latency": {
                    "retrieval_p50_ms": success_df['retrieval_latency_ms'].median(),
                    "retrieval_p95_ms": success_df['retrieval_latency_ms'].quantile(0.95),
                    "generation_p50_ms": success_df['generation_latency_ms'].median() if not self.retrieval_only else None,
                    "generation_p95_ms": success_df['generation_latency_ms'].quantile(0.95) if not self.retrieval_only else None,
                    "total_p50_ms": success_df['total_latency_ms'].median(),
                    "total_p95_ms": success_df['total_latency_ms'].quantile(0.95),
                },
                "cost": {
                    "total_usd": success_df['estimated_cost_usd'].sum() if not self.retrieval_only else None,
                    "average_per_query_usd": success_df['estimated_cost_usd'].mean() if not self.retrieval_only else None
                }
            }
        else:
            summary = {"error": "All questions failed"}
            
        with open(f"{run_dir}/evaluation_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
            
        # Error Analysis
        error_df = df[(df['status'] == 'error') | ((df['answer_correctness'] < 0.5) & (df['answer_correctness'].notna()))]
        if not error_df.empty:
            error_analysis = []
            for _, row in error_df.iterrows():
                category = "system_error" if row['status'] == 'error' else "generation_failure"
                if row.get('recall_at_5', 0) == 0 and category != 'system_error':
                    category = "retrieval_failure"
                    
                error_analysis.append({
                    "question_id": row['question_id'],
                    "question": row['question'],
                    "expected_sources": row['expected_chunk_ids'],
                    "retrieved_sources": row['retrieved_chunk_ids'],
                    "answer": row['generated_answer'],
                    "failure_category": category,
                    "metrics": {
                        "mrr": row['mrr'],
                        "correctness": row.get('answer_correctness')
                    }
                })
            with open(f"{run_dir}/error_analysis.json", "w", encoding="utf-8") as f:
                json.dump(error_analysis, f, indent=2)
        else:
            with open(f"{run_dir}/error_analysis.json", "w", encoding="utf-8") as f:
                json.dump([], f)
                
        print(f"\nEvaluation complete. Results saved to {run_dir}")
