import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # Low, Medium, High, Critical
    status: Mapped[str] = mapped_column(String(20), default="New", nullable=False)  # New, Investigating, Resolved, False Positive
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Policy Violation, Anomaly, Intrusion Attempt
    anomaly_classification: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # e.g. Credential Stuffing, Device Spoofing, etc.

    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("industrial_assets.id", ondelete="SET NULL"), nullable=True
    )
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    device: Mapped[Optional["Device"]] = relationship(back_populates="alerts")
    asset: Mapped[Optional["IndustrialAsset"]] = relationship(back_populates="alerts")
    user: Mapped[Optional["User"]] = relationship(back_populates="alerts")
