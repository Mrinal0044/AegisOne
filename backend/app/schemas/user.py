import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.department import Department


class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool = True
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


class UserCreate(UserBase):
    department_id: Optional[uuid.UUID] = None


class User(UserBase):
    id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    department: Optional[Department] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
