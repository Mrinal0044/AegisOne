import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    hostname: str
    ip_address: str
    mac_address: str
    os_version: str
    device_type: str
    status: str
    device_model: Optional[str] = None
    browser_fingerprint: Optional[str] = None
    tls_cert_id: Optional[str] = None
    protocol: Optional[str] = None
    firmware_version: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class Device(DeviceBase):
    id: uuid.UUID
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
