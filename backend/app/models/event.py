import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    destination_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    protocol: Mapped[str] = mapped_column(String(50), nullable=False)  # Modbus/TCP, S7Comm, EtherNet/IP, OPC-UA
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Register Read, Coil Write, Firmware Upgrade Request
    payload_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="Info", nullable=False)  # Info, Warning, Critical

    # Geolocation information
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Auth method
    auth_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Fingerprint details
    device_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    browser_fingerprint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tls_cert_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Spoofable host characteristics
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)

    # Session & ground truth metadata
    session_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resource_accessed: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ground_truth_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("industrial_assets.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    device: Mapped[Optional["Device"]] = relationship(back_populates="events")
    asset: Mapped[Optional["IndustrialAsset"]] = relationship(back_populates="events")
    user: Mapped[Optional["User"]] = relationship(back_populates="events")
