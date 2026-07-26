import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import String, DateTime, JSON, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database.session import Base


class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # User, Device
    
    # Optional link to user or device
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=True
    )
    
    # Profile parameters
    working_schedule: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    login_time: Mapped[str] = mapped_column(String(5), default="08:00", nullable=False)
    logout_time: Mapped[str] = mapped_column(String(5), default="17:00", nullable=False)
    avg_session_duration: Mapped[int] = mapped_column(Integer, default=28800, nullable=False)  # in seconds
    
    normal_devices: Mapped[Dict[str, Any]] = mapped_column(JSON, default=list, nullable=False)  # normal hostnames/IPs
    typical_apps: Mapped[Dict[str, Any]] = mapped_column(JSON, default=list, nullable=False)  # applications
    normal_assets: Mapped[Dict[str, Any]] = mapped_column(JSON, default=list, nullable=False)  # asset UUIDs
    
    network_frequency: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # requests per hour
    avg_event_volume: Mapped[int] = mapped_column(Integer, default=50, nullable=False)  # average daily events
    command_patterns: Mapped[Dict[str, Any]] = mapped_column(JSON, default=list, nullable=False)  # normal actions list
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
