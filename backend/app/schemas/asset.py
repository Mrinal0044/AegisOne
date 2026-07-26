import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    name: str
    ip_address: str
    mac_address: str
    vendor: str
    model: str
    asset_type: str
    location: str
    criticality: str
    status: str


class AssetCreate(AssetBase):
    pass


class IndustrialAsset(AssetBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
