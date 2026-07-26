from typing import List
from sqlalchemy.orm import Session
from app.models.event import Event
from app.repositories.event import event_repo


class EventService:
    def get_events(self, db: Session, skip: int = 0, limit: int = 100) -> List[Event]:
        return event_repo.get_multi(db, skip=skip, limit=limit)


event_service = EventService()
