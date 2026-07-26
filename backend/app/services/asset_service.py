from typing import List
from sqlalchemy.orm import Session
from app.models.asset import IndustrialAsset
from app.repositories.asset import industrial_asset_repo


class IndustrialAssetService:
    def get_assets(self, db: Session, skip: int = 0, limit: int = 100) -> List[IndustrialAsset]:
        return industrial_asset_repo.get_multi(db, skip=skip, limit=limit)


industrial_asset_service = IndustrialAssetService()
