import uuid
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import String, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database.session import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Asset, Device, User
    entity_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    
    # Store dynamic key-value security details (reasons, telemetry context, etc.)
    factors: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    last_calculated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
