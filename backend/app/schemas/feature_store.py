import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user import User
from app.schemas.device import Device
from app.schemas.asset import IndustrialAsset
from app.schemas.department import Department


class UserBehaviorFeaturesSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    window_size: str
    avg_session_duration: float
    failed_login_count: int
    unique_devices_count: int
    unique_assets_count: int
    commands_per_hour: float
    weekend_activity_ratio: float
    night_activity_ratio: float
    remote_login_count: int
    usb_usage_count: int
    download_frequency: float
    config_change_count: int
    failed_auth_count: int
    last_updated: datetime
    
    user: Optional[User] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceBehaviorFeaturesSchema(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    window_size: str
    active_hours: float
    connected_users_count: int
    avg_network_traffic_bytes: float
    config_change_count: int
    firmware_change_count: int
    maintenance_frequency: float
    unexpected_downtime_count: int
    last_updated: datetime

    device: Optional[Device] = None

    model_config = ConfigDict(from_attributes=True)


class AssetBehaviorFeaturesSchema(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    window_size: str
    access_frequency: float
    unique_operators_count: int
    avg_commands_count: float
    alarm_acknowledgements_count: int
    maintenance_events_count: int
    operational_hours: float
    last_updated: datetime

    asset: Optional[IndustrialAsset] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentBehaviorFeaturesSchema(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    window_size: str
    peak_activity_rate: float
    avg_users_online: float
    unique_assets_accessed_count: int
    avg_network_usage: float
    typical_working_hours_ratio: float
    last_updated: datetime

    department: Optional[Department] = None

    model_config = ConfigDict(from_attributes=True)


class BehaviorSnapshotSchema(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    window_size: str
    timestamp: datetime
    features: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
