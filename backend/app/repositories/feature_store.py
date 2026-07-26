from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.feature_store import (
    UserBehaviorFeatures,
    DeviceBehaviorFeatures,
    AssetBehaviorFeatures,
    DepartmentBehaviorFeatures,
    BehaviorSnapshot,
)


class UserBehaviorFeaturesRepository(BaseRepository[UserBehaviorFeatures]):
    def __init__(self) -> None:
        super().__init__(UserBehaviorFeatures)

    def get_or_create(self, db: Session, user_id: Any, window_size: str) -> UserBehaviorFeatures:
        query = select(UserBehaviorFeatures).where(
            UserBehaviorFeatures.user_id == user_id,
            UserBehaviorFeatures.window_size == window_size
        )
        record = db.execute(query).scalar_one_or_none()
        if not record:
            record = UserBehaviorFeatures(user_id=user_id, window_size=window_size)
            db.add(record)
            db.flush()
        return record

    def get_all_by_window(self, db: Session, window_size: str) -> List[UserBehaviorFeatures]:
        query = select(UserBehaviorFeatures).where(UserBehaviorFeatures.window_size == window_size)
        return list(db.execute(query).scalars().all())


class DeviceBehaviorFeaturesRepository(BaseRepository[DeviceBehaviorFeatures]):
    def __init__(self) -> None:
        super().__init__(DeviceBehaviorFeatures)

    def get_or_create(self, db: Session, device_id: Any, window_size: str) -> DeviceBehaviorFeatures:
        query = select(DeviceBehaviorFeatures).where(
            DeviceBehaviorFeatures.device_id == device_id,
            DeviceBehaviorFeatures.window_size == window_size
        )
        record = db.execute(query).scalar_one_or_none()
        if not record:
            record = DeviceBehaviorFeatures(device_id=device_id, window_size=window_size)
            db.add(record)
            db.flush()
        return record

    def get_all_by_window(self, db: Session, window_size: str) -> List[DeviceBehaviorFeatures]:
        query = select(DeviceBehaviorFeatures).where(DeviceBehaviorFeatures.window_size == window_size)
        return list(db.execute(query).scalars().all())


class AssetBehaviorFeaturesRepository(BaseRepository[AssetBehaviorFeatures]):
    def __init__(self) -> None:
        super().__init__(AssetBehaviorFeatures)

    def get_or_create(self, db: Session, asset_id: Any, window_size: str) -> AssetBehaviorFeatures:
        query = select(AssetBehaviorFeatures).where(
            AssetBehaviorFeatures.asset_id == asset_id,
            AssetBehaviorFeatures.window_size == window_size
        )
        record = db.execute(query).scalar_one_or_none()
        if not record:
            record = AssetBehaviorFeatures(asset_id=asset_id, window_size=window_size)
            db.add(record)
            db.flush()
        return record

    def get_all_by_window(self, db: Session, window_size: str) -> List[AssetBehaviorFeatures]:
        query = select(AssetBehaviorFeatures).where(AssetBehaviorFeatures.window_size == window_size)
        return list(db.execute(query).scalars().all())


class DepartmentBehaviorFeaturesRepository(BaseRepository[DepartmentBehaviorFeatures]):
    def __init__(self) -> None:
        super().__init__(DepartmentBehaviorFeatures)

    def get_or_create(self, db: Session, department_id: Any, window_size: str) -> DepartmentBehaviorFeatures:
        query = select(DepartmentBehaviorFeatures).where(
            DepartmentBehaviorFeatures.department_id == department_id,
            DepartmentBehaviorFeatures.window_size == window_size
        )
        record = db.execute(query).scalar_one_or_none()
        if not record:
            record = DepartmentBehaviorFeatures(department_id=department_id, window_size=window_size)
            db.add(record)
            db.flush()
        return record

    def get_all_by_window(self, db: Session, window_size: str) -> List[DepartmentBehaviorFeatures]:
        query = select(DepartmentBehaviorFeatures).where(DepartmentBehaviorFeatures.window_size == window_size)
        return list(db.execute(query).scalars().all())


class BehaviorSnapshotRepository(BaseRepository[BehaviorSnapshot]):
    def __init__(self) -> None:
        super().__init__(BehaviorSnapshot)


user_features_repo = UserBehaviorFeaturesRepository()
device_features_repo = DeviceBehaviorFeaturesRepository()
asset_features_repo = AssetBehaviorFeaturesRepository()
dept_features_repo = DepartmentBehaviorFeaturesRepository()
snapshot_repo = BehaviorSnapshotRepository()
