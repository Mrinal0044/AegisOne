from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.device import Device
from app.services.device_service import device_service

router = APIRouter()


@router.get("", response_model=List[Device])
def read_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Device]:
    """
    Retrieve all devices and terminals.
    """
    return device_service.get_devices(db, skip=skip, limit=limit)
