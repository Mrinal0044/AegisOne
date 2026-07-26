from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LLMProvider(ABC):
    """Abstract base class representing a Large Language Model provider interface."""

    @abstractmethod
    def explain(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> str:
        """Explains what happened, why it is anomalous, and potential business impact."""
        pass

    @abstractmethod
    def recommend(self, alert_data: Dict[str, Any]) -> str:
        """Suggests actionable mitigation, containment, and response steps for analysts."""
        pass

    @abstractmethod
    def explain_timeline(self, timeline_data: List[Dict[str, Any]]) -> str:
        """Translates a sequence of raw telemetries into a human-readable investigation narrative."""
        pass

    @abstractmethod
    def executive_summary(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> str:
        """Generates a high-level summary suitable for security managers/executive directors."""
        pass

    @abstractmethod
    def generate_report(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compiles a complete, structured executive quality security investigation incident report."""
        pass
