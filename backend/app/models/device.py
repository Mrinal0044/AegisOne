import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    hostname: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), index=True, nullable=False)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=False)
    os_version: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PC, Switch, PLC, sensor, etc.
    status: Mapped[str] = mapped_column(String(20), default="Authorized", nullable=False)  # Authorized, Quarantined
    
    # Simulation Parameters
    device_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    network_zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Corporate, DMZ, OT-Control, OT-Field
    operating_status: Mapped[Optional[str]] = mapped_column(String(50), default="Active", nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Device fingerprinting attributes
    device_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    browser_fingerprint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tls_cert_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    assigned_user: Mapped[Optional["User"]] = relationship()
    events: Mapped[list["Event"]] = relationship(back_populates="device")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="device")
