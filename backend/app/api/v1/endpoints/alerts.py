import uuid
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.alert import Alert
from app.services.alert_service import alert_service
from app.repositories.alert import alert_repo

router = APIRouter()


@router.get("", response_model=List[Alert])
def read_alerts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Alert]:
    """
    Retrieve all security alerts and anomalies.
    """
    return alert_service.get_alerts(db, skip=skip, limit=limit)


@router.put("/{alert_id}", response_model=Alert)
def update_alert(
    alert_id: uuid.UUID,
    payload: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    Update status and parameters of a security alert.
    """
    alert = alert_repo.get(db, id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    if "status" in payload:
        alert.status = payload["status"]
        
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Log audit event
    from app.services.audit_service import audit_service
    audit_service.log_action(
        db, 
        action="Alert Updated", 
        details=f"Updated alert status to '{alert.status}' for alert ID: {alert.id}"
    )
    if alert.status == "Resolved":
        audit_service.log_action(
            db, 
            action="Alert Resolved", 
            details=f"Resolved alert ID: {alert.id}"
        )

    # Publish ALERT_UPDATED through SSE manager
    from app.services.sse_manager import sse_manager
    sse_manager.publish("ALERT_UPDATED", {
        "id": str(alert.id),
        "title": alert.title,
        "description": alert.description,
        "severity": alert.severity,
        "status": alert.status
    })

    return alert


@router.get("/export")
def export_alerts(
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db)
):
    """Export security alerts as CSV or JSON file downloads."""
    alerts = alert_service.get_alerts(db, limit=1000)
    data = [
        {
            "id": str(a.id),
            "timestamp": a.created_at.isoformat() + "Z" if hasattr(a.created_at, "isoformat") else str(a.created_at),
            "title": a.title,
            "description": a.description,
            "severity": a.severity,
            "status": a.status,
            "category": a.category,
            "entity": a.user.username if a.user else a.device.hostname if a.device else a.asset.name if a.asset else "N/A"
        }
        for a in alerts
    ]

    if format == "json":
        import json
        from fastapi.responses import Response
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="alerts.json"'}
        )

    import csv
    import io
    from fastapi.responses import StreamingResponse
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Alert ID", "Timestamp", "Title", "Severity", "Status", "Category", "Affected Entity", "Description"])
    for item in data:
        writer.writerow([
            item["id"],
            item["timestamp"],
            item["title"],
            item["severity"],
            item["status"],
            item["category"],
            item["entity"],
            item["description"]
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="alerts.csv"'}
    )
