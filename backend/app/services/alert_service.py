from typing import List
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.repositories.alert import alert_repo


class AlertService:
    def get_alerts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
        return alert_repo.get_multi(db, skip=skip, limit=limit)


alert_service = AlertService()
