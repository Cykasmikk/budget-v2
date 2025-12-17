from typing import List, Tuple, Dict, Optional
import structlog
import numpy as np
from sklearn.linear_model import SGDClassifier
from src.application.ai.embedding_service import EmbeddingService
from src.application.ai.calibration_service import CalibrationService

logger = structlog.get_logger()

class ContinualModelService:
    """
    Centralized Classification Service supporting Continual Learning.
    Uses SGDClassifier for online learning (partial_fit).
    Wraps CalibrationService for uncertainty quantification.
    """
    def __init__(self, embedding_service: EmbeddingService, calibration_service: CalibrationService):
        self.embedding_service = embedding_service
        self.calibration_service = calibration_service
        
        # Online Learning Model
        self.model = SGDClassifier(loss='log_loss', penalty='l2', alpha=1e-4) # Logistic Regression effectively
        self.classes = []
        self.is_trained = False
        
        # Replay Buffer / Calibration Set
        self.calibration_buffer_X = []
        self.calibration_buffer_y = []
        self.update_count = 0
        self.CALIBRATION_INTERVAL = 10
        
    def train_initial(self, texts: List[str], labels: List[str]):
        """
        Initial training on batch data.
        """
        if not texts: return
        
        # Discover all potential classes first or just fit on what we have
        self.classes = sorted(list(set(labels)))
        
        vectors = [self.embedding_service.encode(t) for t in texts]
        self.model.partial_fit(vectors, labels, classes=self.classes)
        self.is_trained = True
        logger.info("continual_model_initialized", classes=len(self.classes), samples=len(texts))

    def update_with_feedback(self, text: str, correct_label: str):
        """
        Online update (Continual Learning).
        """
        vector = self.embedding_service.encode(text)
        
        # Heuristic: Check if label is new. If so, SGD might struggle if we defined classes fixed.
        # fast implementation: we re-call partial_fit with all known classes + new one
        if correct_label not in self.classes:
            self.classes.append(correct_label)
            self.classes.sort()
            
        self.model.partial_fit([vector], [correct_label], classes=self.classes)
        
        # Update Calibration Buffer
        self.calibration_buffer_X.append(vector)
        self.calibration_buffer_y.append(correct_label)
        self.update_count += 1
        
        # Auto-Calibrate
        if self.update_count % self.CALIBRATION_INTERVAL == 0:
            self._trigger_calibration()
            
        logger.info("continual_model_updated", label=correct_label)

    def _trigger_calibration(self):
        """
        Retrain scaler on buffered data.
        """
        if len(self.calibration_buffer_X) < 10: return
        
        # Get predictions on buffer
        # In a real scenario, we should use hold-out set, but here we use recent history
        # as a proxy for "current distribution"
        X = np.array(self.calibration_buffer_X)
        y = np.array(self.calibration_buffer_y)
        
        # We need raw probabilities from the model
        probs = self.model.predict_proba(X)
        max_probs = np.max(probs, axis=1)
        
        # Ideally we check correctness (y_pred == y_true)
        # But CalibrationService.fit takes (probs, labels) usually or (probs, true_labels)?
        # Our CalibrationService.fit takes (y_true, y_prob) of the POSITIVE class or similar.
        # Since it's multi-class, we might simplify to "Is Confidence Reliable?"
        # i.e. Calibrate "Confidence" -> "Probability of Correct"
        
        preds = self.model.classes_[np.argmax(probs, axis=1)]
        is_correct = (preds == y).astype(int)
        
        self.calibration_service.fit(max_probs, is_correct)
        logger.info("calibration_updated", buffer_size=len(X))
        
        # Optional: Trim buffer if too large (reservoir sampling)
        if len(self.calibration_buffer_X) > 100:
             self.calibration_buffer_X = self.calibration_buffer_X[-50:]
             self.calibration_buffer_y = self.calibration_buffer_y[-50:]

    def predict_proba(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Returns (Best Category, Calibrated Confidence, All Probabilities).
        """
        if not self.is_trained:
             return "Uncategorized", 0.0, {}
             
        vector = self.embedding_service.encode(text)
        probs = self.model.predict_proba([vector])[0]
        
        # Map probs to classes
        prob_dict = {cls: prob for cls, prob in zip(self.model.classes_, probs)}
        
        best_class = self.model.classes_[np.argmax(probs)]
        raw_conf = float(np.max(probs))
        
        calibrated_conf = self.calibration_service.calibrate(raw_conf)
        
        return best_class, calibrated_conf, prob_dict
