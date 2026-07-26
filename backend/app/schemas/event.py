import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.device import Device
from app.schemas.asset import IndustrialAsset


class UserMinimal(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)


class EventBase(BaseModel):
    timestamp: datetime
    source_ip: str
    destination_ip: str
    protocol: str
    event_type: str
    payload_summary: Optional[str] = None
    severity: str
    
    # Geolocation information
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

    # Auth method
    auth_method: Optional[str] = None

    # Fingerprints details
    device_model: Optional[str] = None
    browser_fingerprint: Optional[str] = None
    tls_cert_id: Optional[str] = None

    # Host specifications
    os_version: Optional[str] = None
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None

    # Session & classification metadata
    session_duration: Optional[int] = None
    resource_accessed: Optional[str] = None
    ground_truth_label: Optional[str] = None


class EventCreate(EventBase):
    device_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None


class Event(EventBase):
    id: uuid.UUID
    device_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    device: Optional[Device] = None
    asset: Optional[IndustrialAsset] = None
    user: Optional[UserMinimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
