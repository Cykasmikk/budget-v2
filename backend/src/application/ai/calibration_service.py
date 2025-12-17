import numpy as np
from typing import List, Tuple, Optional
import structlog
from sklearn.linear_model import LogisticRegression

logger = structlog.get_logger()

class CalibrationService:
    """
    Service to calibrate model probabilities.
    Implement Temperature Scaling or Platt Scaling.
    """
    def __init__(self):
        # Platt scaling model (Logistic Regression on logits/probs)
        self.calibrator = LogisticRegression(C=1.0, solver='lbfgs')
        self.is_calibrated = False
        
    def fit(self, proper_scores: List[float], y_true: List[int]):
        """
        Fit calibration map.
        Args:
            proper_scores: Uncalibrated confidence scores (max prob) or logits from model.
            y_true: 0 (incorrect) or 1 (correct).
        """
        if len(proper_scores) < 10:
            return # Not enough data
            
        X = np.array(proper_scores).reshape(-1, 1)
        y = np.array(y_true)
        
        try:
            self.calibrator.fit(X, y)
            self.is_calibrated = True
            logger.info("calibration_fitted", samples=len(y))
        except Exception as e:
            logger.error("calibration_fit_failed", error=str(e))

    def calibrate(self, uncalibrated_confidence: float) -> float:
        """
        Return P(Correct | uncalibrated_confidence).
        """
        if not self.is_calibrated:
            return uncalibrated_confidence
            
        try:
            X = np.array([[uncalibrated_confidence]])
            calibrated = self.calibrator.predict_proba(X)[0][1]
            return float(calibrated)
        except Exception:
            return uncalibrated_confidence

    def compute_ece(self, probs: List[float], y_true: List[int], n_bins: int = 10) -> float:
        """
        Compute Expected Calibration Error (ECE).
        """
        probs = np.array(probs)
        y_true = np.array(y_true)
        
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        
        for i in range(n_bins):
            bin_start = bin_boundaries[i]
            bin_end = bin_boundaries[i+1]
            
            mask = (probs > bin_start) & (probs <= bin_end)
            if not np.any(mask):
                continue
                
            bin_conf = np.mean(probs[mask])
            bin_acc = np.mean(y_true[mask])
            
            bin_prop = np.sum(mask) / len(probs)
            ece += np.abs(bin_conf - bin_acc) * bin_prop
            
        return float(ece)
