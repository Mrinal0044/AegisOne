from typing import Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.config_manager import system_config
from app.repositories.simulation import simulation_config_repo
from app.services.audit_service import audit_service

router = APIRouter(prefix="/config")


class ConfigUpdatePayload(BaseModel):
    risk_threshold: int = Field(..., ge=10, le=95)
    alert_threshold: int = Field(..., ge=10, le=95)
    threat_delay_scale: float = Field(..., ge=0.05, le=5.0)
    simulation_speed: float = Field(..., ge=1.0, le=100.0)
    impossible_travel_threshold: float = Field(..., ge=100.0, le=2000.0)
    fingerprint_sensitivity: float = Field(..., ge=0.0, le=1.0)
    credential_stuffing_window: int = Field(..., ge=10, le=3600)
    exfiltration_detection_window: int = Field(..., ge=60, le=86400)
    cold_start_observation_count: int = Field(..., ge=1, le=100)
    drift_sensitivity: float = Field(..., ge=0.0, le=1.0)


@router.get("", response_model=Dict[str, Any])
def get_system_config(db: Session = Depends(get_db)):
    """Retrieve all current system threshold variables and simulation config configurations."""
    sim_config = simulation_config_repo.get_active(db)
    sim_speed = sim_config.speed_multiplier if sim_config else 1.0
    
    return {
        "risk_threshold": system_config.risk_threshold,
        "alert_threshold": system_config.alert_threshold,
        "threat_delay_scale": system_config.threat_delay_scale,
        "simulation_speed": sim_speed,
        "impossible_travel_threshold": system_config.impossible_travel_threshold,
        "fingerprint_sensitivity": system_config.fingerprint_sensitivity,
        "credential_stuffing_window": system_config.credential_stuffing_window,
        "exfiltration_detection_window": system_config.exfiltration_detection_window,
        "cold_start_observation_count": system_config.cold_start_observation_count,
        "drift_sensitivity": system_config.drift_sensitivity
    }


@router.put("", response_model=Dict[str, Any])
def update_system_config(
    payload: ConfigUpdatePayload,
    db: Session = Depends(get_db)
):
    """Modify system thresholds and speed multipliers dynamically with validation checks."""
    # 1. Update in-memory configuration values
    system_config.risk_threshold = payload.risk_threshold
    system_config.alert_threshold = payload.alert_threshold
    system_config.threat_delay_scale = payload.threat_delay_scale
    system_config.impossible_travel_threshold = payload.impossible_travel_threshold
    system_config.fingerprint_sensitivity = payload.fingerprint_sensitivity
    system_config.credential_stuffing_window = payload.credential_stuffing_window
    system_config.exfiltration_detection_window = payload.exfiltration_detection_window
    system_config.cold_start_observation_count = payload.cold_start_observation_count
    system_config.drift_sensitivity = payload.drift_sensitivity
    
    # 2. Update database simulation config parameters
    sim_config = simulation_config_repo.get_active(db)
    if sim_config:
        sim_config.speed_multiplier = payload.simulation_speed
        db.add(sim_config)
        db.commit()

    # 3. Log administrative audit action
    audit_service.log_action(
        db,
        action="Configuration Changed",
        details=(
            f"Admin updated settings -> Risk: {payload.risk_threshold}, "
            f"Threat Delay: {payload.threat_delay_scale}x, "
            f"Sim Speed: {payload.simulation_speed}x, "
            f"Travel Limit: {payload.impossible_travel_threshold} km/h, "
            f"Fingerprint: {payload.fingerprint_sensitivity}"
        )
    )

    # 4. Publish configuration update via SSE for real-time notification
    from app.services.sse_manager import sse_manager
    sse_manager.publish("CONFIGURATION_UPDATED", {
        "risk_threshold": payload.risk_threshold,
        "alert_threshold": payload.alert_threshold,
        "threat_delay_scale": payload.threat_delay_scale,
        "simulation_speed": payload.simulation_speed,
        "impossible_travel_threshold": payload.impossible_travel_threshold,
        "fingerprint_sensitivity": payload.fingerprint_sensitivity,
        "credential_stuffing_window": payload.credential_stuffing_window,
        "exfiltration_detection_window": payload.exfiltration_detection_window,
        "cold_start_observation_count": payload.cold_start_observation_count,
        "drift_sensitivity": payload.drift_sensitivity
    })

    return {
        "message": "System configurations updated successfully.",
        "risk_threshold": system_config.risk_threshold,
        "alert_threshold": system_config.alert_threshold,
        "threat_delay_scale": system_config.threat_delay_scale,
        "simulation_speed": payload.simulation_speed,
        "impossible_travel_threshold": system_config.impossible_travel_threshold,
        "fingerprint_sensitivity": system_config.fingerprint_sensitivity,
        "credential_stuffing_window": system_config.credential_stuffing_window,
        "exfiltration_detection_window": system_config.exfiltration_detection_window,
        "cold_start_observation_count": system_config.cold_start_observation_count,
        "drift_sensitivity": system_config.drift_sensitivity
    }
