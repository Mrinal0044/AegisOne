import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class BehaviorProfileBase(BaseModel):
    name: str
    entity_type: str
    user_id: Optional[uuid.UUID] = None
    device_id: Optional[uuid.UUID] = None
    working_schedule: Dict[str, Any] = {}
    login_time: str
    logout_time: str
    avg_session_duration: int
    normal_devices: Dict[str, Any] = {}
    typical_apps: Dict[str, Any] = {}
    normal_assets: Dict[str, Any] = {}
    network_frequency: float
    avg_event_volume: int
    command_patterns: Dict[str, Any] = {}


class BehaviorProfileCreate(BehaviorProfileBase):
    pass


class BehaviorProfile(BehaviorProfileBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
