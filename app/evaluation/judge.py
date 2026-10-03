import logging
import json
from google import genai
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from app.evaluation.schemas import JudgeOutput

logger = logging.getLogger(__name__)

JUDGE_PROMPT = """You are an expert AI evaluator.
Evaluate the given answer based on the provided inputs.
Respond ONLY with a valid JSON object matching this schema:
{{
  "correctness": float (0.0 to 1.0),
  "relevance": float (0.0 to 1.0),
  "faithfulness": float (0.0 to 1.0),
  "reason": "Brief explanation"
}}

Correctness: Does the generated answer match the reference answer?
Relevance: Does the generated answer directly address the question without fluff?
Faithfulness: Is the generated answer fully supported by the retrieved context?

Question:
{question}

Reference Answer:
{reference_answer}

Retrieved Context:
{context}

Generated Answer:
{generated_answer}
"""

class LLMJudge:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options={"api_version": "v1"}
            )

    def evaluate(self, question: str, reference_answer: str, context: str, generated_answer: str) -> Optional[JudgeOutput]:
        if not settings.GEMINI_API_KEY:
            return None
            
        prompt = JUDGE_PROMPT.format(
            question=question,
            reference_answer=reference_answer,
            context=context,
            generated_answer=generated_answer
        )
        
        try:
            res = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(res.text)
            return JudgeOutput(**data)
        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            return None
