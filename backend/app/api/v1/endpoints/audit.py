import csv
import io
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit")


@router.get("", response_model=List[Dict[str, Any]])
def get_audit_trail(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve chronological system audit logs."""
    logs = audit_service.get_logs(db, skip=skip, limit=limit)
    return [
        {
            "id": str(log.id),
            "timestamp": log.timestamp.isoformat() + "Z" if hasattr(log.timestamp, "isoformat") else str(log.timestamp),
            "action": log.action,
            "ip_address": log.ip_address,
            "details": log.details,
            "user": log.user.username if log.user else "System"
        }
        for log in logs
    ]


@router.get("/export")
def export_audit_trail(
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db)
):
    """Export the central system audit logs as CSV or JSON file downloads."""
    logs = audit_service.get_logs(db, limit=1000)
    data = [
        {
            "id": str(log.id),
            "timestamp": log.timestamp.isoformat() + "Z" if hasattr(log.timestamp, "isoformat") else str(log.timestamp),
            "action": log.action,
            "ip_address": log.ip_address,
            "details": log.details,
            "user": log.user.username if log.user else "System"
        }
        for log in logs
    ]

    if format == "json":
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="audit_logs.json"'}
        )

    # Compile CSV bytes
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Audit ID", "Timestamp", "Actor", "Action", "IP Address", "Details"])
    for item in data:
        writer.writerow([
            item["id"],
            item["timestamp"],
            item["user"],
            item["action"],
            item["ip_address"],
            item["details"]
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit_logs.csv"'}
    )
