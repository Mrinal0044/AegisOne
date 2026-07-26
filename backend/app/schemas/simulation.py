import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SimulationConfigBase(BaseModel):
    speed_multiplier: float
    num_employees: int
    num_devices: int
    event_rate: float
    is_active: bool


class SimulationConfigUpdate(BaseModel):
    speed_multiplier: Optional[float] = None
    num_employees: Optional[int] = None
    num_devices: Optional[int] = None
    event_rate: Optional[float] = None
    is_active: Optional[bool] = None


class SimulationConfigSchema(SimulationConfigBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationStateSchema(BaseModel):
    id: uuid.UUID
    status: str
    started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    total_events_generated: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationStatusResponse(BaseModel):
    status: str
    config: SimulationConfigSchema
    state: SimulationStateSchema
    active_employees_count: int
    active_devices_count: int
    active_assets_count: int
    virtual_system_time: str
