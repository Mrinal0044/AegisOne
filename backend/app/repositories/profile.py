from app.models.profile import BehaviorProfile
from app.repositories.base import BaseRepository


class BehaviorProfileRepository(BaseRepository[BehaviorProfile]):
    def __init__(self) -> None:
        super().__init__(BehaviorProfile)


behavior_profile_repo = BehaviorProfileRepository()
