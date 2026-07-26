import logging
from typing import Dict, Any, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.device import Device
from app.models.asset import IndustrialAsset
from app.models.department import Department

logger = logging.getLogger("app.services.detection_engine.risk_engine")


class RiskEngine:
    @staticmethod
    def get_criticality_factor(db: Session, entity_type: str, entity_id: uuid.UUID) -> float:
        """Calculate a normalization weight [0.1 - 1.0] for the entity based on business criticality."""
        try:
            if entity_type == "User":
                stmt = select(User).where(User.id == entity_id)
                user = db.execute(stmt).scalar_one_or_none()
                if user:
                    role = user.role.lower()
                    if "admin" in role or "it" in role:
                        return 0.9
                    if "engineer" in role or "operator" in role:
                        return 0.7
                    return 0.3
            
            elif entity_type == "Device":
                stmt = select(Device).where(Device.id == entity_id)
                dev = db.execute(stmt).scalar_one_or_none()
                if dev:
                    dtype = dev.device_type.lower()
                    if "workstation" in dtype or "plc" in dtype:
                        return 1.0
                    if "operator" in dtype or "hmi" in dtype:
                        return 0.8
                    return 0.4
            
            elif entity_type == "IndustrialAsset":
                stmt = select(IndustrialAsset).where(IndustrialAsset.id == entity_id)
                asset = db.execute(stmt).scalar_one_or_none()
                if asset:
                    criticality = asset.criticality.lower()
                    if criticality == "critical":
                        return 1.0
                    if criticality == "high":
                        return 0.8
                    if criticality == "medium":
                        return 0.5
                    return 0.2
            
            elif entity_type == "Department":
                stmt = select(Department).where(Department.id == entity_id)
                dept = db.execute(stmt).scalar_one_or_none()
                if dept:
                    code = dept.code.upper()
                    if code in ["ICS", "ENG"]:
                        return 1.0
                    if code in ["MNT", "PRD"]:
                        return 0.8
                    return 0.4
        except Exception as e:
            logger.error(f"Error resolving criticality for {entity_type} {entity_id}: {e}")
            
        return 0.5

    @classmethod
    def calculate_normalized_risk(
        cls,
        db: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        anomaly_score: float,
        feature_vector: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine anomaly factors and entity properties into a normalized score between 0 and 100."""
        # 1. Criticality Factor (0.1 - 1.0)
        criticality = cls.get_criticality_factor(db, entity_type, entity_id)
        
        # 2. Activity Frequency Factor (0.0 - 1.0)
        frequency = 0.0
        deviation = 0.0
        
        if entity_type == "User":
            # commands rate
            commands_rate = feature_vector.get("commands_per_hour", 0.0)
            frequency = min(1.0, commands_rate / 30.0)  # scale rate max 30 cmds/hr
            # Deviation: night and weekend activity
            deviation = (feature_vector.get("night_activity_ratio", 0.0) * 0.5) + (feature_vector.get("weekend_activity_ratio", 0.0) * 0.5)
            
        elif entity_type == "Device":
            active_hours = feature_vector.get("active_hours", 0.0)
            frequency = min(1.0, active_hours / 24.0)
            deviation = min(1.0, feature_vector.get("unexpected_downtime_count", 0) / 3.0)
            
        elif entity_type == "IndustrialAsset":
            access_freq = feature_vector.get("access_frequency", 0.0)
            frequency = min(1.0, access_freq / 50.0)
            deviation = min(1.0, feature_vector.get("maintenance_events_count", 0) / 5.0)
            
        elif entity_type == "Department":
            peak_rate = feature_vector.get("peak_activity_rate", 0.0)
            frequency = min(1.0, peak_rate / 100.0)
            # Deviation from normal hours
            deviation = 1.0 - feature_vector.get("typical_working_hours_ratio", 1.0)

        # 3. Weighted Scoring Formula
        # Anomaly = 40%, Criticality = 30%, Deviation = 20%, Frequency = 10%
        raw_score = (
            (anomaly_score * 40.0) +
            (criticality * 30.0) +
            (deviation * 20.0) +
            (frequency * 10.0)
        )
        
        # Apply anomaly boost of +15 to ensure alert triggering for confirmed anomalies
        if anomaly_score > 0.5:
            raw_score += 15.0
        
        # Clamp score between 0 and 100
        risk_score = int(max(0, min(100, round(raw_score))))
        
        # Resolve Severity
        if risk_score <= 30:
            severity = "Low"
        elif risk_score <= 60:
            severity = "Medium"
        elif risk_score <= 80:
            severity = "High"
        else:
            severity = "Critical"

        # Formulate reason for anomaly
        reasons = []
        if anomaly_score > 0.6:
            reasons.append("High model anomaly score")
        if deviation > 0.7:
            reasons.append("Abnormal operation timeframe/deviation")
        if frequency > 0.8:
            reasons.append("Excessive transaction frequency")
        if criticality > 0.8:
            reasons.append("Critical business infrastructure target")
            
        reason_str = " & ".join(reasons) if reasons else "Slight behavioral baseline deviation"

        return {
            "risk_score": risk_score,
            "severity": severity,
            "reason": reason_str,
            "anomaly_score": anomaly_score,
            "criticality": criticality,
            "deviation": deviation,
            "frequency": frequency
        }


risk_engine = RiskEngine()
