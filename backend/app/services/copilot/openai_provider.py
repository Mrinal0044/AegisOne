import logging
import json
from typing import Dict, Any, List
import httpx

from app.core.config import settings
from app.services.copilot.interfaces import LLMProvider

logger = logging.getLogger("app.services.copilot.openai_provider")


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE.rstrip("/")
        self.model = settings.OPENAI_MODEL

    def _query_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Helper to send HTTP POST chat completions request to the configured LLM API."""
        if not self.api_key:
            return "Error: OpenAI API Key not configured."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        url = f"{self.api_base}/chat/completions"
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"OpenAI API responded with error status {response.status_code}: {response.text}")
                    return f"Error: LLM endpoint responded with status {response.status_code}."
        except Exception as e:
            logger.error(f"Failed to query OpenAI-compatible endpoint: {e}", exc_info=True)
            return f"Error: Failed to connect to LLM gateway."

    def explain(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> str:
        sys = "You are an experienced industrial Security Operations Center (SOC) incident responder analyst."
        user = (
            f"Analyze the following security alert:\n{json.dumps(alert_data, indent=2)}\n\n"
            f"Chronological incident timeline steps:\n{json.dumps(timeline_data, indent=2)}\n\n"
            "Provide a concise, professional explanation covering:\n"
            "- What happened\n- Why it is suspicious\n- Which behaviors deviated from normal boundaries\n- Potential business/operational impact\n"
            "- Affected assets/users\n- Assessed confidence and risk explanation."
        )
        return self._query_llm(sys, user)

    def recommend(self, alert_data: Dict[str, Any]) -> str:
        sys = "You are an experienced industrial Security Operations Center (SOC) incident responder analyst."
        user = (
            f"Recommend immediate response actions for the following security incident:\n{json.dumps(alert_data, indent=2)}\n\n"
            "List actionable containment, mitigation, and investigative response steps. Keep recommendations brief and bulleted."
        )
        return self._query_llm(sys, user)

    def explain_timeline(self, timeline_data: List[Dict[str, Any]]) -> str:
        sys = "You are an experienced industrial Security Operations Center (SOC) incident responder analyst."
        user = (
            f"Translate the following raw event timeline into a concise human-readable narrative summary:\n"
            f"{json.dumps(timeline_data, indent=2)}\n\n"
            "Focus on explaining the flow of actions logically (e.g. login outside shift -> USB plug-in -> PLC writes) without listing timestamps explicitly."
        )
        return self._query_llm(sys, user)

    def executive_summary(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> str:
        sys = "You are an experienced industrial Security Operations Center (SOC) incident responder analyst."
        user = (
            f"Generate a concise executive summary suitable for managers/executives:\n"
            f"Alert: {json.dumps(alert_data, indent=2)}\n"
            f"Timeline: {json.dumps(timeline_data, indent=2)}\n\n"
            "Include:\n1. Incident Overview\n2. Potential Business Impact\n3. Current Mitigation Status\n4. Top Recommended Action."
        )
        return self._query_llm(sys, user)

    def generate_report(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "explanation": self.explain(alert_data, timeline_data),
            "recommendations": self.recommend(alert_data),
            "timeline_summary": self.explain_timeline(timeline_data),
            "executive_summary": self.executive_summary(alert_data, timeline_data)
        }
