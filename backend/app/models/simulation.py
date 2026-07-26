import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database.session import Base


class SimulationConfig(Base):
    __tablename__ = "simulation_config"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    speed_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    num_employees: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    num_devices: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    event_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # target events per second
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SimulationState(Base):
    __tablename__ = "simulation_state"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), default="IDLE", nullable=False)  # IDLE, RUNNING, PAUSED, STOPPED
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_events_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
