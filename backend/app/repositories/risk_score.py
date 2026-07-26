from app.models.risk_score import RiskScore
from app.repositories.base import BaseRepository


class RiskScoreRepository(BaseRepository[RiskScore]):
    def __init__(self) -> None:
        super().__init__(RiskScore)


risk_score_repo = RiskScoreRepository()
