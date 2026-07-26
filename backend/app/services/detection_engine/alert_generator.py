import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.risk_score import RiskScore

logger = logging.getLogger("app.services.detection_engine.alert_generator")


class AlertGenerator:
    @staticmethod
    def log_risk_score(
        db: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        score: int,
        factors: Dict[str, Any]
    ) -> RiskScore:
        """Create and log a RiskScore record for an entity's behavioral evaluation history."""
        # Find if a record already exists to update, or create a new one
        stmt = select(RiskScore).where(
            and_(
                RiskScore.entity_type == entity_type,
                RiskScore.entity_id == entity_id
            )
        )
        record = db.execute(stmt).scalar_one_or_none()
        if not record:
            record = RiskScore(
                entity_type=entity_type,
                entity_id=entity_id,
                score=score,
                factors=factors
            )
            db.add(record)
        else:
            record.score = score
            record.factors = factors
            record.last_calculated = datetime.utcnow()
            db.add(record)
            
        db.flush()
        return record

    @staticmethod
    def generate_alert_if_required(
        db: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        risk_score: int,
        severity: str,
        reason: str,
        behavior_summary: str,
        anomaly_classification: Optional[str] = None
    ) -> Optional[Alert]:
        """Fire a security alert if the risk exceeds threshold (60+). Prevents duplicate alerts for unresolved assets."""
        # Threshold check: Alert is raised based on dynamic config threshold
        from app.core.config_manager import system_config
        if risk_score <= system_config.risk_threshold:
            return None

        # Check if an unresolved alert ("New" or "Investigating") already exists for this entity to prevent fatigue
        stmt = select(Alert).where(
            and_(
                Alert.status.in_(["New", "Investigating"]),
                Alert.user_id == entity_id if entity_type == "User" else
                Alert.device_id == entity_id if entity_type == "Device" else
                Alert.asset_id == entity_id if entity_type == "IndustrialAsset" else False
            )
        )
        existing_alert = db.execute(stmt).scalars().first()
        if existing_alert:
            # Update the existing alert description and severity if it is more critical
            if risk_score > 70:  # Escalation trigger
                existing_alert.description = f"{behavior_summary} (Updated: {reason})"
                existing_alert.severity = severity
                if anomaly_classification:
                    existing_alert.anomaly_classification = anomaly_classification
                db.add(existing_alert)
                db.flush()
                # Publish ALERT_UPDATED
                from app.services.sse_manager import sse_manager
                sse_manager.publish("ALERT_UPDATED", {
                    "id": str(existing_alert.id),
                    "title": existing_alert.title,
                    "description": existing_alert.description,
                    "severity": existing_alert.severity,
                    "status": existing_alert.status,
                    "anomaly_classification": existing_alert.anomaly_classification
                })
            return existing_alert

        # Map entity details
        user_id = entity_id if entity_type == "User" else None
        device_id = entity_id if entity_type == "Device" else None
        asset_id = entity_id if entity_type == "IndustrialAsset" else None

        alert = Alert(
            title=f"Behavioral Anomaly: {entity_type} {severity} Risk Alert",
            description=behavior_summary,
            severity=severity,
            status="New",
            category="Anomaly",
            anomaly_classification=anomaly_classification or "Normal",
            user_id=user_id,
            device_id=device_id,
            asset_id=asset_id
        )
        db.add(alert)
        db.flush()

        # Increment alerts counter in metrics_service
        try:
            from app.services.metrics_service import metrics_service
            metrics_service.alerts_generated += 1
        except Exception:
            pass

        # Log alert audit record
        try:
            from app.services.audit_service import audit_service
            audit_service.log_action(
                db,
                action="Alert Created",
                details=f"Fired Security Alert for {entity_type} {entity_id}: '{alert.title}'"
            )
        except Exception:
            pass

        # Publish ALERT_CREATED to clients
        from app.services.sse_manager import sse_manager
        username = alert.user.username if alert.user else None
        hostname = alert.device.hostname if alert.device else None
        asset_name = alert.asset.name if alert.asset else None

        sse_manager.publish("ALERT_CREATED", {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "category": alert.category,
            "anomaly_classification": alert.anomaly_classification,
            "created_at": alert.created_at.isoformat() + "Z" if hasattr(alert.created_at, "isoformat") else str(alert.created_at),
            "user": username,
            "device": hostname,
            "asset": asset_name
        })

        logger.info(f"Fired Security Alert for {entity_type} {entity_id} with severity {severity}.")
        return alert


alert_generator = AlertGenerator()
