import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.threat_engine.engine import threat_engine
from app.services.threat_engine.scenario_registry import scenario_registry

router = APIRouter(prefix="/threats")


@router.get("/scenarios", response_model=List[Dict[str, Any]])
def list_threat_scenarios(db: Session = Depends(get_db)):
    """Retrieve details for all registered industrial cyberattack simulation scenarios."""
    scenarios = scenario_registry.list_all()
    # Execute step list parsing to output length
    return [
        {
            "scenario_id": s.scenario_id,
            "name": s.name,
            "description": s.description,
            "total_steps": len(s.get_steps(db))
        }
        for s in scenarios
    ]


@router.post("/start/{scenario_id}")
async def start_threat_scenario(
    scenario_id: str,
    target_user_id: Optional[uuid.UUID] = Query(None, description="Target user UUID (optional)"),
    target_device_id: Optional[uuid.UUID] = Query(None, description="Target device UUID (optional)"),
    target_asset_id: Optional[uuid.UUID] = Query(None, description="Target asset UUID (optional)"),
    delay_scale: float = Query(1.0, description="Speed modifier: lower scale accelerates event injection"),
    db: Session = Depends(get_db)
):
    """Instantiate and launch an attack simulation scenario in the background."""
    try:
        sim = threat_engine.start_scenario(
            scenario_id, target_user_id, target_device_id, target_asset_id, delay_scale
        )
        from app.services.audit_service import audit_service
        audit_service.log_action(
            db, 
            action="Threat Scenario Started", 
            details=f"Launched threat scenario '{sim['name']}' ({scenario_id})"
        )
        return {"message": f"Successfully launched scenario: {sim['name']}", "state": sim}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start threat scenario: {str(e)}")


@router.post("/stop/{scenario_id}")
def stop_threat_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Stop a running threat simulation scenario."""
    threat_engine.stop_scenario(scenario_id)
    from app.services.audit_service import audit_service
    audit_service.log_action(
        db, 
        action="Threat Scenario Stopped", 
        details=f"Stopped threat scenario '{scenario_id}'"
    )
    return {"message": f"Terminated simulation scenario: {scenario_id}"}


@router.post("/reset")
def reset_threat_engine(db: Session = Depends(get_db)):
    """Clear all simulation runs, histories, and logs from memory."""
    threat_engine.reset_all()
    from app.services.audit_service import audit_service
    audit_service.log_action(
        db, 
        action="Threat Engine Reset", 
        details="All simulation states cleared"
    )
    return {"message": "Threat simulation engine state reset complete."}


@router.get("/status", response_model=List[Dict[str, Any]])
@router.get("", response_model=List[Dict[str, Any]])
def get_running_scenarios_status():
    """Retrieve the execution states, anomaly detection status, and risk level of active simulations."""
    return threat_engine.get_status()


@router.get("/timeline", response_model=List[Dict[str, Any]])
def get_threat_timeline():
    """Retrieve the chronological log of all simulation actions injected by threat tasks."""
    return threat_engine.get_timeline()


@router.get("/history", response_model=List[Dict[str, Any]])
def get_threat_history():
    """Retrieve logs of all completed and stopped simulation runs."""
    return threat_engine.get_history()
