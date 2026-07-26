import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.copilot.engine import copilot_engine

router = APIRouter(prefix="/copilot")


class CopilotRequest(BaseModel):
    alert_id: uuid.UUID


@router.post("/explain")
def explain_alert(
    payload: CopilotRequest,
    db: Session = Depends(get_db)
):
    """Generate detailed AI security explanation for a specific alert."""
    explanation = copilot_engine.explain_alert(db, payload.alert_id)
    return {"explanation": explanation}


@router.post("/recommend")
def recommend_mitigation(
    payload: CopilotRequest,
    db: Session = Depends(get_db)
):
    """Generate actionable response mitigation steps for a specific alert."""
    recommendations = copilot_engine.recommend_mitigation(db, payload.alert_id)
    return {"recommendations": recommendations}


@router.post("/timeline")
def explain_timeline(
    payload: CopilotRequest,
    db: Session = Depends(get_db)
):
    """Translate raw log timestamps into a readable security narrative."""
    timeline_summary = copilot_engine.explain_timeline(db, payload.alert_id)
    return {"timeline_summary": timeline_summary}


@router.post("/summary")
def executive_summary(
    payload: CopilotRequest,
    db: Session = Depends(get_db)
):
    """Generate concise management executive brief summarizing the incident."""
    summary = copilot_engine.executive_summary(db, payload.alert_id)
    return {"summary": summary}


@router.post("/report")
def generate_report(
    payload: CopilotRequest,
    db: Session = Depends(get_db)
):
    """Generate complete incident investigation reports."""
    report = copilot_engine.generate_report(db, payload.alert_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])

    # Increment copilot requests counter in metrics_service
    from app.services.metrics_service import metrics_service
    metrics_service.copilot_requests += 1
        
    from app.services.audit_service import audit_service
    audit_service.log_action(
        db,
        action="Copilot Report Generated",
        details=f"AI Copilot compiled investigation file for alert ID: {payload.alert_id}"
    )
    return report
