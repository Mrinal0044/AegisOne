import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.event import UserMinimal


class AuditLogBase(BaseModel):
    timestamp: datetime
    action: str
    ip_address: str
    details: str


class AuditLogCreate(AuditLogBase):
    user_id: Optional[uuid.UUID] = None


class AuditLog(AuditLogBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user: Optional[UserMinimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
