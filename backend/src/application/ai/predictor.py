from typing import List, Tuple, Optional
import structlog
from src.application.ai.embedding_service import EmbeddingService
from src.domain.budget import BudgetEntry
from sklearn.neighbors import KNeighborsClassifier
import numpy as np

logger = structlog.get_logger()

class Predictor:
    """
    Neural classifier for budget transactions using Embeddings + K-Nearest Neighbors.
    """
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.knn = KNeighborsClassifier(n_neighbors=5, weights='distance')
        self.is_trained = False
        
    def train(self, entries: List[BudgetEntry]):
        """
        Train the classifier on historical budget entries.
        """
        if not entries:
            return

        texts = []
        labels = []
        
        # Filter valid labeled data
        for e in entries:
            if e.category and e.category not in ["Uncategorized", "General", "Misc"]:
                texts.append(e.description)
                labels.append(e.category)
        
        if not texts:
            return

        # Encode all texts
        # Note: In production, we'd batch this or use parallel encoding
        vectors = [self.embedding_service.encode(t) for t in texts]
        
        # Train KNN
        # We need at least one neighbor, but preferably min(5, len(samples))
        n_neighbors = min(5, len(vectors))
        self.knn = KNeighborsClassifier(n_neighbors=n_neighbors, weights='distance')
        self.knn.fit(vectors, labels)
        self.is_trained = True
        logger.info("predictor_trained", samples=len(texts), classes=len(set(labels)))

    def predict(self, description: str) -> Tuple[str, float]:
        """
        Predict category for a given description.
        Returns (category, confidence_score).
        """
        if not self.is_trained:
            return "Uncategorized", 0.0
            
        vector = self.embedding_service.encode(description)
        
        # Reshape for single prediction
        vector_np = np.array(vector).reshape(1, -1)
        
        # Predict
        probs = self.knn.predict_proba(vector_np)[0]
        max_prob_idx = np.argmax(probs)
        confidence = float(probs[max_prob_idx])
        category = self.knn.classes_[max_prob_idx]
        
        return category, confidence
