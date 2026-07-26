import logging
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models.alert import Alert
from app.services.copilot.interfaces import LLMProvider
from app.services.copilot.openai_provider import OpenAIProvider
from app.services.copilot.fallback_provider import FallbackProvider
from app.services.threat_engine.engine import threat_engine

logger = logging.getLogger("app.services.copilot.engine")


class CopilotEngine:
    def __init__(self) -> None:
        self._openai_provider = OpenAIProvider()
        self._fallback_provider = FallbackProvider()

    def get_provider(self) -> LLMProvider:
        """Resolve LLM provider based on environment credentials configuration."""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
            logger.debug("Resolving OpenAI LLM Provider (API Key found).")
            return self._openai_provider
        logger.debug("Resolving Rule-Based Fallback Provider (No API Key found).")
        return self._fallback_provider

    def _get_context(self, db: Session, alert_id: uuid.UUID) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Aggregate database parameters and chronologies matching target alert."""
        # Query Alert
        stmt = select(Alert).where(Alert.id == alert_id)
        alert = db.execute(stmt).scalar_one_or_none()
        if not alert:
            return {}, []

        # Serialize Alert minimal context
        alert_data = {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "category": alert.category,
            "anomaly_classification": alert.anomaly_classification,
            "created_at": alert.created_at.isoformat() + "Z" if hasattr(alert.created_at, "isoformat") else str(alert.created_at),
            "user_id": str(alert.user_id) if alert.user_id else None,
            "device_id": str(alert.device_id) if alert.device_id else None,
            "asset_id": str(alert.asset_id) if alert.asset_id else None,
            "user": {"username": alert.user.username, "full_name": alert.user.full_name, "role": alert.user.role} if alert.user else None,
            "device": {"hostname": alert.device.hostname, "ip_address": alert.device.ip_address, "os_version": alert.device.os_version} if alert.device else None,
            "asset": {"name": alert.asset.name, "ip_address": alert.asset.ip_address, "location": alert.asset.location, "criticality": alert.asset.criticality, "vendor": alert.asset.vendor} if alert.asset else None
        }

        # Filter Threat timeline records matching alert target entities
        all_timeline = threat_engine.get_timeline()
        timeline_data = []
        for step in all_timeline:
            if (
                (alert.user_id and step.get("target_user_id") == str(alert.user_id)) or
                (alert.device_id and step.get("target_device_id") == str(alert.device_id)) or
                (alert.asset_id and step.get("target_asset_id") == str(alert.asset_id))
            ):
                timeline_data.append(step)

        return alert_data, timeline_data

    def explain_alert(self, db: Session, alert_id: uuid.UUID) -> str:
        alert_data, timeline_data = self._get_context(db, alert_id)
        if not alert_data:
            return "Alert not found."
        return self.get_provider().explain(alert_data, timeline_data)

    def recommend_mitigation(self, db: Session, alert_id: uuid.UUID) -> str:
        alert_data, _ = self._get_context(db, alert_id)
        if not alert_data:
            return "Alert not found."
        return self.get_provider().recommend(alert_data)

    def explain_timeline(self, db: Session, alert_id: uuid.UUID) -> str:
        _, timeline_data = self._get_context(db, alert_id)
        return self.get_provider().explain_timeline(timeline_data)

    def executive_summary(self, db: Session, alert_id: uuid.UUID) -> str:
        alert_data, timeline_data = self._get_context(db, alert_id)
        if not alert_data:
            return "Alert not found."
        return self.get_provider().executive_summary(alert_data, timeline_data)

    def generate_report(self, db: Session, alert_id: uuid.UUID) -> Dict[str, Any]:
        alert_data, timeline_data = self._get_context(db, alert_id)
        if not alert_data:
            return {"error": "Alert not found"}
        return self.get_provider().generate_report(alert_data, timeline_data)


# Singleton instance
copilot_engine = CopilotEngine()
