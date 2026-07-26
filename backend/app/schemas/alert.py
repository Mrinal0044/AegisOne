import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.device import Device
from app.schemas.asset import IndustrialAsset
from app.schemas.event import UserMinimal


class AlertBase(BaseModel):
    title: str
    description: str
    severity: str
    status: str
    category: str
    anomaly_classification: Optional[str] = None


class AlertCreate(AlertBase):
    asset_id: Optional[uuid.UUID] = None
    device_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None


class Alert(AlertBase):
    id: uuid.UUID
    asset_id: Optional[uuid.UUID] = None
    device_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    asset: Optional[IndustrialAsset] = None
    device: Optional[Device] = None
    user: Optional[UserMinimal] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
