import logging
import os
import warnings
from typing import List

# Suppress non-critical HF Hub warnings
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
warnings.filterwarnings("ignore", category=FutureWarning, module="sentence_transformers")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.dimension = 384 # Default for all-MiniLM-L6-v2
        return cls._instance

    def initialize(self):
        if self.model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            try:
                self.dimension = self.model.get_sentence_embedding_dimension()
            except Exception:
                self.dimension = 384
            logger.info(f"Model loaded with dimension: {self.dimension}")

    def warmup(self):
        if self.model is None:
            self.initialize()
        if self.model is not None:
            try:
                self.model.encode("warmup query", convert_to_numpy=True)
                logger.info("Embedding model warmed up.")
            except Exception as e:
                logger.warning(f"Embedding warmup warning: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.model is None:
            self.initialize()
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        if self.model is None:
            self.initialize()
        return self.model.encode(text, convert_to_numpy=True).tolist()

embedding_service = EmbeddingService()
