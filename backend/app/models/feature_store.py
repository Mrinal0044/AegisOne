import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.session import Base


class UserBehaviorFeatures(Base):
    __tablename__ = "user_behavior_features"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    window_size: Mapped[str] = mapped_column(String(10), index=True)  # 5m, 15m, 1h, 24h, 7d
    
    # Feature Metrics
    avg_session_duration: Mapped[float] = mapped_column(Float, default=0.0)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_devices_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_assets_count: Mapped[int] = mapped_column(Integer, default=0)
    commands_per_hour: Mapped[float] = mapped_column(Float, default=0.0)
    weekend_activity_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    night_activity_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    remote_login_count: Mapped[int] = mapped_column(Integer, default=0)
    usb_usage_count: Mapped[int] = mapped_column(Integer, default=0)
    download_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    config_change_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_auth_count: Mapped[int] = mapped_column(Integer, default=0)
    
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship()


class DeviceBehaviorFeatures(Base):
    __tablename__ = "device_behavior_features"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    window_size: Mapped[str] = mapped_column(String(10), index=True)
    
    # Feature Metrics
    active_hours: Mapped[float] = mapped_column(Float, default=0.0)
    connected_users_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_network_traffic_bytes: Mapped[float] = mapped_column(Float, default=0.0)
    config_change_count: Mapped[int] = mapped_column(Integer, default=0)
    firmware_change_count: Mapped[int] = mapped_column(Integer, default=0)
    maintenance_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    unexpected_downtime_count: Mapped[int] = mapped_column(Integer, default=0)
    
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    device: Mapped["Device"] = relationship()


class AssetBehaviorFeatures(Base):
    __tablename__ = "asset_behavior_features"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("industrial_assets.id", ondelete="CASCADE"), index=True)
    window_size: Mapped[str] = mapped_column(String(10), index=True)
    
    # Feature Metrics
    access_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    unique_operators_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_commands_count: Mapped[float] = mapped_column(Float, default=0.0)
    alarm_acknowledgements_count: Mapped[int] = mapped_column(Integer, default=0)
    maintenance_events_count: Mapped[int] = mapped_column(Integer, default=0)
    operational_hours: Mapped[float] = mapped_column(Float, default=0.0)
    
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    asset: Mapped["IndustrialAsset"] = relationship()


class DepartmentBehaviorFeatures(Base):
    __tablename__ = "department_behavior_features"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), index=True)
    window_size: Mapped[str] = mapped_column(String(10), index=True)
    
    # Feature Metrics
    peak_activity_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_users_online: Mapped[float] = mapped_column(Float, default=0.0)
    unique_assets_accessed_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_network_usage: Mapped[float] = mapped_column(Float, default=0.0)
    typical_working_hours_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    department: Mapped["Department"] = relationship()


class BehaviorSnapshot(Base):
    __tablename__ = "behavior_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(20), index=True)  # User, Device, Asset, Department
    entity_id: Mapped[uuid.UUID] = mapped_column(index=True)
    window_size: Mapped[str] = mapped_column(String(10), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Raw feature vector values
    features: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
