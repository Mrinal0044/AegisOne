from abc import ABC, abstractmethod
from typing import Dict, Any, List


class DetectionModel(ABC):
    """Abstract Base Class representing a modular behavioral anomaly detection model."""

    @abstractmethod
    def train(self, data: List[List[float]]) -> None:
        """Fit the detection model on normal baseline behavior vectors."""
        pass

    @abstractmethod
    def predict(self, vector: List[float]) -> Dict[str, Any]:
        """Evaluate a single behavior vector.
        
        Returns a dictionary containing:
        - "anomaly_score": raw score (float)
        - "prediction": 1 for normal, -1 for anomaly
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Serialize and save the model state to disk."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Deserialize and load the model state from disk."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata (algorithm name, parameters, etc.)."""
        pass
