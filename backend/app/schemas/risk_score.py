import uuid
from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class RiskScoreBase(BaseModel):
    score: int
    entity_type: str
    entity_id: uuid.UUID
    factors: Dict[str, Any] = {}


class RiskScoreCreate(RiskScoreBase):
    pass


class RiskScore(RiskScoreBase):
    id: uuid.UUID
    last_calculated: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
