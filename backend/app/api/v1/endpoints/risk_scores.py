from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.risk_score import RiskScore
from app.services.risk_score_service import risk_score_service

router = APIRouter()


@router.get("", response_model=List[RiskScore])
def read_risk_scores(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[RiskScore]:
    """
    Retrieve calculated threat risk scores for OT assets, devices, and users.
    """
    return risk_score_service.get_risk_scores(db, skip=skip, limit=limit)
