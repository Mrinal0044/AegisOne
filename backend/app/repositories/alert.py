from app.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self) -> None:
        super().__init__(Alert)


alert_repo = AlertRepository()
