from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.user import User
from app.services.user_service import user_service

router = APIRouter()


@router.get("", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[User]:
    """
    Retrieve all registered users and operators.
    """
    return user_service.get_users(db, skip=skip, limit=limit)
