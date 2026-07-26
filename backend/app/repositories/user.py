from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        return db.execute(query).scalar_one_or_none()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        return db.execute(query).scalar_one_or_none()


user_repo = UserRepository()
