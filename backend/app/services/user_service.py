from typing import List
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user import user_repo


class UserService:
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return user_repo.get_multi(db, skip=skip, limit=limit)


user_service = UserService()
