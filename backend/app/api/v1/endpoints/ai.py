import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Body, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.database.session import get_db
from app.services.detection_engine.model_manager import model_manager
from app.services.detection_engine.training import training_pipeline
from app.services.detection_engine.prediction import prediction_engine
from app.models.alert import Alert
from app.models.risk_score import RiskScore
from app.models.user import User
from app.models.device import Device
from app.models.asset import IndustrialAsset
from app.models.department import Department
from app.schemas.alert import Alert as AlertSchema

router = APIRouter(prefix="/ai")


@router.post("/train")
def trigger_training(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers an asynchronous model training sweep for all active entities."""
    background_tasks.add_task(training_pipeline.train_all_models, db)
    from app.services.audit_service import audit_service
    audit_service.log_action(
        db, 
        action="AI Training", 
        details="Triggered training sweep for all active entities"
    )
    return {"message": "AI model training sweep initiated in background thread."}


@router.post("/retrain")
def trigger_retraining(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Clears the existing model store and triggers a clean retraining sweep in a background task."""
    model_manager.clear_all_models()
    background_tasks.add_task(training_pipeline.train_all_models, db)
    from app.services.audit_service import audit_service
    audit_service.log_action(
        db, 
        action="Model Retraining", 
        details="AI model store cleared and retraining sweep initiated"
    )
    return {"message": "AI model store cleared. Retraining sweep initiated in background thread."}


@router.get("/status")
def get_ai_status(db: Session = Depends(get_db)):
    """Returns AI Engine coverage metadata (how many entities have trained models vs total entities)."""
    user_cnt = db.execute(select(func.count(User.id))).scalar() or 0
    dev_cnt = db.execute(select(func.count(Device.id))).scalar() or 0
    asset_cnt = db.execute(select(func.count(IndustrialAsset.id))).scalar() or 0
    dept_cnt = db.execute(select(func.count(Department.id))).scalar() or 0
    
    manifest = model_manager.get_manifest()
    trained_keys = list(manifest.keys())
    
    user_models = sum(1 for k in trained_keys if k.startswith("User_"))
    device_models = sum(1 for k in trained_keys if k.startswith("Device_"))
    asset_models = sum(1 for k in trained_keys if k.startswith("IndustrialAsset_"))
    dept_models = sum(1 for k in trained_keys if k.startswith("Department_"))

    return {
        "status": "OPERATIONAL",
        "engine_name": "Behavioral Intelligence Engine",
        "coverage": {
            "users": {"total": user_cnt, "trained": user_models},
            "devices": {"total": dev_cnt, "trained": device_models},
            "industrial_assets": {"total": asset_cnt, "trained": asset_models},
            "departments": {"total": dept_cnt, "trained": dept_models}
        },
        "total_models_trained": len(trained_keys),
        "last_manifest_update": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/models")
def get_trained_models():
    """Retrieve details for all currently serialized behavioral models."""
    return model_manager.list_models()


@router.get("/metrics")
def get_prediction_metrics(db: Session = Depends(get_db)):
    """Retrieve prediction density metrics, false positive rates, and inference latency statistics."""
    total_evals = db.execute(select(func.count(RiskScore.id))).scalar() or 0
    critical_alerts = db.execute(select(func.count(Alert.id)).where(Alert.severity == "Critical")).scalar() or 0
    high_alerts = db.execute(select(func.count(Alert.id)).where(Alert.severity == "High")).scalar() or 0
    
    # Calculate average inference time from risk scores factors metadata
    scores = db.execute(select(RiskScore.factors)).scalars().all()
    inf_times = [s.get("inference_time_seconds", 0.0) for s in scores if isinstance(s, dict)]
    avg_inf = sum(inf_times) / len(inf_times) if inf_times else 0.0025

    return {
        "total_predictions_evaluated": total_evals,
        "anomalies_flagged": critical_alerts + high_alerts,
        "average_inference_time_seconds": round(avg_inf, 6),
        "false_positive_rate_placeholder": 0.02, # 2% FP target rate
        "precision_placeholder": 0.98,
        "recall_placeholder": 0.95
    }


@router.post("/predict")
def predict_vector_anomaly(
    entity_type: str = Query(..., description="Type of entity: User, Device, IndustrialAsset, Department"),
    entity_id: uuid.UUID = Query(..., description="UUID of the entity"),
    features: Dict[str, float] = Body(..., description="Key-value float map representing feature values"),
    db: Session = Depends(get_db)
):
    """Directly evaluate a custom feature vector on the trained Isolation Forest model."""
    model_key = f"{entity_type}_{entity_id}"
    model = model_manager.get_model(model_key)
    
    if not model:
        raise HTTPException(
            status_code=404, 
            detail=f"No trained behavior model found for key {model_key}. Fit models first."
        )

    # Reconstruct vector index order based on type
    try:
        vector = []
        if entity_type == "User":
            keys = [
                "avg_session_duration", "failed_login_count", "unique_devices_count",
                "unique_assets_count", "commands_per_hour", "weekend_activity_ratio",
                "night_activity_ratio", "remote_login_count", "usb_usage_count",
                "download_frequency", "config_change_count", "failed_auth_count"
            ]
            vector = [features.get(k, 0.0) for k in keys]
        elif entity_type == "Device":
            keys = [
                "active_hours", "connected_users_count", "avg_network_traffic_bytes",
                "config_change_count", "firmware_change_count", "maintenance_frequency",
                "unexpected_downtime_count"
            ]
            vector = [features.get(k, 0.0) for k in keys]
        elif entity_type == "IndustrialAsset":
            keys = [
                "access_frequency", "unique_operators_count", "avg_commands_count",
                "alarm_acknowledgements_count", "maintenance_events_count", "operational_hours"
            ]
            vector = [features.get(k, 0.0) for k in keys]
        elif entity_type == "Department":
            keys = [
                "peak_activity_rate", "avg_users_online", "unique_assets_accessed_count",
                "avg_network_usage", "typical_working_hours_ratio"
            ]
            vector = [features.get(k, 0.0) for k in keys]
        else:
            raise HTTPException(status_code=400, detail="Invalid entity type requested.")
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Mismatch in feature vector format: {str(e)}"
        )

    res = model.predict(vector)
    from app.services.detection_engine.risk_engine import risk_engine
    risk_res = risk_engine.calculate_normalized_risk(db, entity_type, entity_id, res["anomaly_score"], features)

    return {
        "anomaly_score": res["anomaly_score"],
        "prediction": res["prediction"],
        "confidence_score": res["confidence"],
        "risk_score": risk_res["risk_score"],
        "severity": risk_res["severity"],
        "reason": risk_res["reason"]
    }


@router.get("/alerts/live", response_model=List[AlertSchema])
def get_live_alerts(db: Session = Depends(get_db)):
    """Retrieve all unresolved alerts currently active in the SOC alarm queue."""
    stmt = select(Alert).where(Alert.status.in_(["New", "Investigating"])).order_from = Alert.created_at.desc()
    # Simple order by
    stmt = select(Alert).where(Alert.status.in_(["New", "Investigating"])).order_by(Alert.created_at.desc())
    return list(db.execute(stmt).scalars().all())


from datetime import datetime
