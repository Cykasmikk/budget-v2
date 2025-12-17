from typing import List
import structlog
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = structlog.get_logger()

class EmbeddingService:
    """
    Service for generating text embeddings using SentenceTransformers.
    Implements a neuro-symbolic foundation for semantic search and classification.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformer model to use.
        """
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)
        logger.info("embedding_model_initialized", model_name=model_name)

    @lru_cache(maxsize=1024)
    def encode(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text.
        
        Args:
            text: Input text string.
            
        Returns:
            List of floats representing the embedding vector.
        """
        if not text:
            return []
            
        try:
            # sentence-transformers encode returns ndarray
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e), text=text[:50])
            raise

    @staticmethod
    def similarity(v1: List[float], v2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            v1: First vector.
            v2: Second vector.
            
        Returns:
            Cosine similarity score (-1.0 to 1.0).
        """
        if not v1 or not v2:
            return 0.0
            
        # Use simple dot product / norm approach for single vectors
        # or scikit-learn helper
        
        vec1 = np.array(v1)
        vec2 = np.array(v2)
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
