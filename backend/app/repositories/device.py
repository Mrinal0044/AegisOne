from app.models.device import Device
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    def __init__(self) -> None:
        super().__init__(Device)


device_repo = DeviceRepository()
