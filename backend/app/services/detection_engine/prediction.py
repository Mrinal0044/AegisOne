import logging
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.feature_store import (
    UserBehaviorFeatures,
    DeviceBehaviorFeatures,
    AssetBehaviorFeatures,
    DepartmentBehaviorFeatures,
)
from app.services.detection_engine.model_manager import model_manager
from app.services.detection_engine.risk_engine import risk_engine
from app.services.detection_engine.alert_generator import alert_generator
from app.services.detection_engine.training import training_pipeline

logger = logging.getLogger("app.services.detection_engine.prediction")


class PredictionEngine:
    @staticmethod
    def evaluate_entity(db: Session, entity_type: str, entity_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Evaluate the active behavior vector of an entity, calculate risk, and fire alerts."""
        model_key = f"{entity_type}_{entity_id}"
        
        # 1. Retrieve the latest 1h feature vector from the Feature Store
        vector_data = None
        raw_dict = {}
        
        if entity_type == "User":
            stmt = select(UserBehaviorFeatures).where(
                and_(UserBehaviorFeatures.user_id == entity_id, UserBehaviorFeatures.window_size == "1h")
            )
            features = db.execute(stmt).scalar_one_or_none()
            if features:
                vector_data = training_pipeline.extract_user_vector(features)
                raw_dict = {
                    "avg_session_duration": features.avg_session_duration,
                    "failed_login_count": features.failed_login_count,
                    "unique_devices_count": features.unique_devices_count,
                    "unique_assets_count": features.unique_assets_count,
                    "commands_per_hour": features.commands_per_hour,
                    "weekend_activity_ratio": features.weekend_activity_ratio,
                    "night_activity_ratio": features.night_activity_ratio,
                    "remote_login_count": features.remote_login_count,
                    "usb_usage_count": features.usb_usage_count,
                    "download_frequency": features.download_frequency,
                    "config_change_count": features.config_change_count,
                    "failed_auth_count": features.failed_auth_count,
                }
                
        elif entity_type == "Device":
            stmt = select(DeviceBehaviorFeatures).where(
                and_(DeviceBehaviorFeatures.device_id == entity_id, DeviceBehaviorFeatures.window_size == "1h")
            )
            features = db.execute(stmt).scalar_one_or_none()
            if features:
                vector_data = training_pipeline.extract_device_vector(features)
                raw_dict = {
                    "active_hours": features.active_hours,
                    "connected_users_count": features.connected_users_count,
                    "avg_network_traffic_bytes": features.avg_network_traffic_bytes,
                    "config_change_count": features.config_change_count,
                    "firmware_change_count": features.firmware_change_count,
                    "maintenance_frequency": features.maintenance_frequency,
                    "unexpected_downtime_count": features.unexpected_downtime_count,
                }
                
        elif entity_type == "IndustrialAsset":
            stmt = select(AssetBehaviorFeatures).where(
                and_(AssetBehaviorFeatures.asset_id == entity_id, AssetBehaviorFeatures.window_size == "1h")
            )
            features = db.execute(stmt).scalar_one_or_none()
            if features:
                vector_data = training_pipeline.extract_asset_vector(features)
                raw_dict = {
                    "access_frequency": features.access_frequency,
                    "unique_operators_count": features.unique_operators_count,
                    "avg_commands_count": features.avg_commands_count,
                    "alarm_acknowledgements_count": features.alarm_acknowledgements_count,
                    "maintenance_events_count": features.maintenance_events_count,
                    "operational_hours": features.operational_hours,
                }
                
        elif entity_type == "Department":
            stmt = select(DepartmentBehaviorFeatures).where(
                and_(DepartmentBehaviorFeatures.department_id == entity_id, DepartmentBehaviorFeatures.window_size == "1h")
            )
            features = db.execute(stmt).scalar_one_or_none()
            if features:
                vector_data = training_pipeline.extract_dept_vector(features)
                raw_dict = {
                    "peak_activity_rate": features.peak_activity_rate,
                    "avg_users_online": features.avg_users_online,
                    "unique_assets_accessed_count": features.unique_assets_accessed_count,
                    "avg_network_usage": features.avg_network_usage,
                    "typical_working_hours_ratio": features.typical_working_hours_ratio,
                }

        # --- Cold Start Baseline Handling ---
        from app.models.user import User
        from app.models.device import Device
        from app.models.event import Event
        from app.core.config_manager import system_config
        import numpy as np

        if vector_data and entity_type in ("User", "Device"):
            # 1. Count historical interactions/observations
            if entity_type == "User":
                event_count_stmt = select(Event.id).where(Event.user_id == entity_id)
            else:
                event_count_stmt = select(Event.id).where(Event.device_id == entity_id)
            obs_count = len(db.execute(event_count_stmt).scalars().all())

            # 2. Check if observation count is under the threshold
            if obs_count < system_config.cold_start_observation_count:
                weight = obs_count / max(1, system_config.cold_start_observation_count)
                
                # Derive baseline feature vectors from peer categories
                baseline_vectors = []
                if entity_type == "User":
                    user = db.get(User, entity_id)
                    if user:
                        # Try to find peers in same department & role
                        peer_stmt = select(User.id).where(
                            and_(
                                User.department_id == user.department_id,
                                User.role == user.role,
                                User.id != entity_id
                            )
                        )
                        peer_ids = list(db.execute(peer_stmt).scalars().all())
                        if not peer_ids:
                            # Fallback to role only
                            peer_stmt = select(User.id).where(
                                and_(User.role == user.role, User.id != entity_id)
                            )
                            peer_ids = list(db.execute(peer_stmt).scalars().all())
                        if not peer_ids:
                            peer_stmt = select(User.id).where(User.id != entity_id)
                            peer_ids = list(db.execute(peer_stmt).scalars().all())

                        if peer_ids:
                            peer_feat_stmt = select(UserBehaviorFeatures).where(
                                and_(UserBehaviorFeatures.user_id.in_(peer_ids), UserBehaviorFeatures.window_size == "1h")
                            )
                            peer_feats = db.execute(peer_feat_stmt).scalars().all()
                            for f in peer_feats:
                                baseline_vectors.append(training_pipeline.extract_user_vector(f))
                
                else:  # Device type
                    device = db.get(Device, entity_id)
                    if device:
                        peer_stmt = select(Device.id).where(
                            and_(Device.device_type == device.device_type, Device.id != entity_id)
                        )
                        peer_ids = list(db.execute(peer_stmt).scalars().all())
                        if not peer_ids:
                            peer_stmt = select(Device.id).where(Device.id != entity_id)
                            peer_ids = list(db.execute(peer_stmt).scalars().all())

                        if peer_ids:
                            peer_feat_stmt = select(DeviceBehaviorFeatures).where(
                                and_(DeviceBehaviorFeatures.device_id.in_(peer_ids), DeviceBehaviorFeatures.window_size == "1h")
                            )
                            peer_feats = db.execute(peer_feat_stmt).scalars().all()
                            for f in peer_feats:
                                baseline_vectors.append(training_pipeline.extract_device_vector(f))

                # If baseline peers are available, calculate average and blend
                if baseline_vectors:
                    baseline_avg = np.mean(np.array(baseline_vectors), axis=0)
                    personal_arr = np.array(vector_data)
                    # Blend mathematically
                    blended_arr = weight * personal_arr + (1.0 - weight) * baseline_avg
                    vector_data = blended_arr.tolist()

        if not vector_data:
            return None

        # 2. Perform Anomaly Prediction
        model = model_manager.get_model(model_key)
        start_inf = time.time()
        
        if model:
            pred_res = model.predict(vector_data)
            anomaly_score = pred_res["anomaly_score"]
            prediction = pred_res["prediction"]
            confidence = pred_res["confidence"]
        else:
            # Fallback if no model is trained yet (treat as normal baseline)
            anomaly_score = 0.0
            prediction = 1
            confidence = 1.0

        inference_time = time.time() - start_inf

        # 3. Calculate Normalized Risk Score (0-100)
        risk_res = risk_engine.calculate_normalized_risk(
            db, entity_type, entity_id, anomaly_score, raw_dict
        )
        risk_score = risk_res["risk_score"]
        severity = risk_res["severity"]
        reason = risk_res["reason"]

        # Track execution metrics inside stats payload
        factors = {
            "anomaly_score": round(anomaly_score, 4),
            "criticality": round(risk_res["criticality"], 4),
            "deviation": round(risk_res["deviation"], 4),
            "frequency": round(risk_res["frequency"], 4),
            "inference_time_seconds": round(inference_time, 6),
            "confidence": round(confidence, 4),
            "reason": reason,
            "prediction_value": prediction
        }

        # 4. Save/Update RiskScore history record
        alert_generator.log_risk_score(db, entity_type, entity_id, risk_score, factors)

        # Publish risk update to clients
        from app.services.sse_manager import sse_manager
        sse_manager.publish("RISK_UPDATED", {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "risk_score": risk_score,
            "severity": severity,
            "reason": reason,
            "factors": factors
        })

        # 5. Fire Alert if risk score exceeds configured threshold
        from app.core.config_manager import system_config
        if risk_score > system_config.risk_threshold:
            # Classify anomaly dynamically based on reasoning triggers
            anomaly_class = "Normal"
            reason_l = reason.lower()
            if "download" in reason_l or raw_dict.get("download_frequency", 0) > 0.7:
                anomaly_class = "Data Exfiltration"
            elif "usb" in reason_l or raw_dict.get("usb_usage_count", 0) > 0.7:
                anomaly_class = "USB Malware"
            elif "failed_auth" in reason_l or raw_dict.get("failed_login_count", 0) > 0.7:
                anomaly_class = "Brute Force"
            elif "remote" in reason_l or raw_dict.get("remote_login_count", 0) > 0.7:
                anomaly_class = "Remote Access"
            elif "command" in reason_l and entity_type == "User":
                anomaly_class = "PLC Manipulation"
            elif "drift" in reason_l:
                anomaly_class = "Insider Drift"
            elif "insider" in reason_l:
                anomaly_class = "Insider Threat"
            elif "asset" in reason_l:
                anomaly_class = "Lateral Movement"

            summary = (
                f"Abnormal behavioral signature identified for {entity_type}. "
                f"Risk Score: {risk_score}/100. Severity: {severity}. Reason: {reason}."
            )
            alert_generator.generate_alert_if_required(
                db, entity_type, entity_id, risk_score, severity, reason, summary, anomaly_class
            )

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "anomaly_score": anomaly_score,
            "prediction": prediction,
            "confidence_score": confidence,
            "risk_score": risk_score,
            "severity": severity,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "supporting_features": raw_dict
        }


prediction_engine = PredictionEngine()
