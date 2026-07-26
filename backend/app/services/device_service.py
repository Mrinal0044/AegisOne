from typing import List
from sqlalchemy.orm import Session
from app.models.device import Device
from app.repositories.device import device_repo


class DeviceService:
    def get_devices(self, db: Session, skip: int = 0, limit: int = 100) -> List[Device]:
        return device_repo.get_multi(db, skip=skip, limit=limit)


device_service = DeviceService()
