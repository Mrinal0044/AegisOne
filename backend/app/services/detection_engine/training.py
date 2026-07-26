import logging
import uuid
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.device import Device
from app.models.asset import IndustrialAsset
from app.models.department import Department
from app.models.feature_store import (
    UserBehaviorFeatures,
    DeviceBehaviorFeatures,
    AssetBehaviorFeatures,
    DepartmentBehaviorFeatures,
)
from app.services.detection_engine.model_manager import model_manager, IsolationForestModel

logger = logging.getLogger("app.services.detection_engine.training")


class TrainingPipeline:
    @staticmethod
    def extract_user_vector(f: UserBehaviorFeatures) -> List[float]:
        return [
            float(f.avg_session_duration),
            float(f.failed_login_count),
            float(f.unique_devices_count),
            float(f.unique_assets_count),
            float(f.commands_per_hour),
            float(f.weekend_activity_ratio),
            float(f.night_activity_ratio),
            float(f.remote_login_count),
            float(f.usb_usage_count),
            float(f.download_frequency),
            float(f.config_change_count),
            float(f.failed_auth_count),
        ]

    @staticmethod
    def extract_device_vector(f: DeviceBehaviorFeatures) -> List[float]:
        return [
            float(f.active_hours),
            float(f.connected_users_count),
            float(f.avg_network_traffic_bytes),
            float(f.config_change_count),
            float(f.firmware_change_count),
            float(f.maintenance_frequency),
            float(f.unexpected_downtime_count),
        ]

    @staticmethod
    def extract_asset_vector(f: AssetBehaviorFeatures) -> List[float]:
        return [
            float(f.access_frequency),
            float(f.unique_operators_count),
            float(f.avg_commands_count),
            float(f.alarm_acknowledgements_count),
            float(f.maintenance_events_count),
            float(f.operational_hours),
        ]

    @staticmethod
    def extract_dept_vector(f: DepartmentBehaviorFeatures) -> List[float]:
        return [
            float(f.peak_activity_rate),
            float(f.avg_users_online),
            float(f.unique_assets_accessed_count),
            float(f.avg_network_usage),
            float(f.typical_working_hours_ratio),
        ]

    @classmethod
    def train_entity_model(cls, db: Session, entity_type: str, entity_id: uuid.UUID) -> bool:
        """Fetch historical feature store samples for an entity and fit an anomaly detection model."""
        start_time = time.time()
        model_key = f"{entity_type}_{entity_id}"
        
        # Query feature records (we search for 1h window primarily to train)
        vectors = []
        if entity_type == "User":
            stmt = select(UserBehaviorFeatures).where(
                and_(UserBehaviorFeatures.user_id == entity_id, UserBehaviorFeatures.window_size == "1h")
            )
            records = db.execute(stmt).scalars().all()
            vectors = [cls.extract_user_vector(r) for r in records]
            
        elif entity_type == "Device":
            stmt = select(DeviceBehaviorFeatures).where(
                and_(DeviceBehaviorFeatures.device_id == entity_id, DeviceBehaviorFeatures.window_size == "1h")
            )
            records = db.execute(stmt).scalars().all()
            vectors = [cls.extract_device_vector(r) for r in records]
            
        elif entity_type == "IndustrialAsset":
            stmt = select(AssetBehaviorFeatures).where(
                and_(AssetBehaviorFeatures.asset_id == entity_id, AssetBehaviorFeatures.window_size == "1h")
            )
            records = db.execute(stmt).scalars().all()
            vectors = [cls.extract_asset_vector(r) for r in records]
            
        elif entity_type == "Department":
            stmt = select(DepartmentBehaviorFeatures).where(
                and_(DepartmentBehaviorFeatures.department_id == entity_id, DepartmentBehaviorFeatures.window_size == "1h")
            )
            records = db.execute(stmt).scalars().all()
            vectors = [cls.extract_dept_vector(r) for r in records]

        if not vectors:
            logger.warning(f"No baseline data in feature store for {model_key}. Training skipped.")
            return False

        # If data is sparse (e.g. just started simulation), synthesize baseline samples
        # to prevent model fitting errors and define a robust boundary
        training_size = len(vectors)
        if training_size < 30:
            base_vector = vectors[0]
            synthesized = []
            for _ in range(50):
                # perturb features by +/- 10% gaussian noise
                sample = [v * (1.0 + random.gauss(0, 0.08)) for v in base_vector]
                synthesized.append(sample)
            vectors.extend(synthesized)
            training_size = len(vectors)

        try:
            model = IsolationForestModel(contamination=0.05)
            model.train(vectors)
            
            duration = time.time() - start_time
            model_manager.save_model(model_key, model, training_size, duration)
            logger.info(f"Model {model_key} trained successfully on {training_size} samples.")
            return True
        except Exception as e:
            logger.error(f"Failed to fit model {model_key}: {e}", exc_info=True)
            return False

    @classmethod
    def train_all_models(cls, db: Session) -> Dict[str, Any]:
        """Perform a complete retraining sweep over all registered twin entities."""
        logger.info("Executing global behavioral anomaly detection retraining sweep...")
        results = {
            "users_trained": 0,
            "devices_trained": 0,
            "assets_trained": 0,
            "departments_trained": 0,
            "status": "COMPLETED",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        try:
            # Users
            users = db.execute(select(User.id)).scalars().all()
            for uid in users:
                if cls.train_entity_model(db, "User", uid):
                    results["users_trained"] += 1

            # Devices
            devices = db.execute(select(Device.id)).scalars().all()
            for did in devices:
                if cls.train_entity_model(db, "Device", did):
                    results["devices_trained"] += 1

            # Assets
            assets = db.execute(select(IndustrialAsset.id)).scalars().all()
            for aid in assets:
                if cls.train_entity_model(db, "IndustrialAsset", aid):
                    results["assets_trained"] += 1

            # Departments
            depts = db.execute(select(Department.id)).scalars().all()
            for deid in depts:
                if cls.train_entity_model(db, "Department", deid):
                    results["departments_trained"] += 1

            logger.info(f"Retraining sweep complete: {results}")
        except Exception as e:
            logger.error(f"Retraining sweep failed: {e}", exc_info=True)
            results["status"] = "FAILED"

        return results


training_pipeline = TrainingPipeline()
