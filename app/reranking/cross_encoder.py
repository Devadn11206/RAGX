import logging
import asyncio
from typing import List
from sentence_transformers import CrossEncoder
from app.core.config import settings
from app.retrieval.base import RetrievalResult
from app.reranking.base import Reranker
from app.reranking.scoring import ScoreNormalizer

logger = logging.getLogger(__name__)

class LocalCrossEncoderReranker(Reranker):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalCrossEncoderReranker, cls).__new__(cls)
            cls._instance.model = None
        return cls._instance
        
    def initialize(self):
        if self.model is None and settings.RERANKING_ENABLED:
            logger.info(f"Loading Phase 10 Cross-Encoder model: {settings.RERANKER_MODEL}")
            try:
                # Device will be automatically selected (CUDA if available, else CPU)
                self.model = CrossEncoder(settings.RERANKER_MODEL, max_length=512)
                logger.info("Cross-Encoder loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Cross-Encoder: {e}")
                self.model = None

    def warmup(self):
        """Warm up the cross-encoder model to prevent first-request cold start timeout."""
        if self.model is None:
            self.initialize()
        if self.model is not None:
            try:
                logger.info("Warming up Cross-Encoder model...")
                self.model.predict([["warmup query", "warmup passage context"]], show_progress_bar=False)
                logger.info("Cross-Encoder model warmup completed.")
            except Exception as e:
                logger.warning(f"Cross-Encoder warmup warning: {e}")

    async def rerank(self, query: str, candidates: List[RetrievalResult], top_k: int) -> List[RetrievalResult]:
        if self.model is None:
            self.initialize()
            
        if self.model is None or not candidates:
            # Fallback if model failed to load
            return sorted(candidates, key=lambda x: x.score, reverse=True)[:top_k]

        # Prepare inputs safely truncating if needed
        # We assume the model handles truncation via max_length=512 above
        pairs = [[query, c.text] for c in candidates]
        
        # We need to run inference. It's CPU/GPU bound, so it should run in a threadpool to not block the async event loop
        loop = asyncio.get_running_loop()
        try:
            scores = await loop.run_in_executor(
                None,
                lambda: self.model.predict(
                    pairs, 
                    batch_size=settings.RERANK_BATCH_SIZE, 
                    show_progress_bar=False
                ).tolist()
            )
        except Exception as e:
            logger.error(f"Reranking inference failed: {e}")
            return sorted(candidates, key=lambda x: x.score, reverse=True)[:top_k]
            
        # Check if model scores need normalization
        # minmax is safer if the model output is not constrained to [0,1]
        normalized_scores = ScoreNormalizer.minmax(scores)
        
        for idx, candidate in enumerate(candidates):
            candidate.retrieval_score = candidate.score
            candidate.rerank_score = normalized_scores[idx]
            
            # Hybrid Score calculation
            ret_w = settings.RERANK_RETRIEVAL_WEIGHT
            rerank_w = settings.RERANK_MODEL_WEIGHT
            
            candidate.final_score = (ret_w * candidate.retrieval_score) + (rerank_w * candidate.rerank_score)
            candidate.score = candidate.final_score # alias for backwards compatibility
            
        return candidates

local_cross_encoder_reranker = LocalCrossEncoderReranker()
