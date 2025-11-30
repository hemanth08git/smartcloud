from typing import List, Dict
import numpy as np
from pyod.models.iforest import IForest


class SensorAnomalyDetector:
    """
    Simple anomaly detector for sensor readings using PyOD's Isolation Forest.
    Features used: temperature, humidity.
    """

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        # Isolation Forest model from PyOD
        self.model = IForest(contamination=contamination, random_state=random_state)
        self.is_fitted = False

    def fit(self, history: List[Dict[str, float]]) -> None:
        """
        Fit the detector on historical sensor readings.

        history: list of dicts like:
          { "temperature": float, "humidity": float }
        """
        if not history:
            self.is_fitted = False
            return

        X = np.array([[h["temperature"], h["humidity"]] for h in history])
        self.model.fit(X)
        self.is_fitted = True

    def predict_one(self, current: Dict[str, float]) -> Dict[str, object]:
        """
        Predict whether a single current reading is anomalous.

        current: { "temperature": float, "humidity": float }

        Returns:
          {
            "is_anomaly": bool,
            "score": float,
            "level": str,
            "message": str
          }
        """
        if not self.is_fitted:
            return {
                "is_anomaly": False,
                "score": 0.0,
                "level": "UNKNOWN",
                "message": "Model not trained (no history provided); assuming normal."
            }

        X = np.array([[current["temperature"], current["humidity"]]])
        # In PyOD, predict() returns 1 for outliers, 0 for inliers
        label = int(self.model.predict(X)[0])
        # Higher decision_function score -> more normal, usually
        score = float(self.model.decision_function(X)[0])

        is_anomaly = bool(label)
        level = "HIGH" if is_anomaly else "NORMAL"
        message = "Abnormal sensor pattern detected." if is_anomaly else "Sensor reading within normal range."

        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "level": level,
            "message": message,
        }
