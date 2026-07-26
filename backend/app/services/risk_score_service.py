from typing import List
from sqlalchemy.orm import Session
from app.models.risk_score import RiskScore
from app.repositories.risk_score import risk_score_repo


class RiskScoreService:
    def get_risk_scores(self, db: Session, skip: int = 0, limit: int = 100) -> List[RiskScore]:
        return risk_score_repo.get_multi(db, skip=skip, limit=limit)


risk_score_service = RiskScoreService()
