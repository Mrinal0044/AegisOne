from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.event import Event
from app.services.event_service import event_service

router = APIRouter()


@router.get("", response_model=List[Event])
def read_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Event]:
    """
    Retrieve all behavioral and network protocol events.
    """
    return event_service.get_events(db, skip=skip, limit=limit)
