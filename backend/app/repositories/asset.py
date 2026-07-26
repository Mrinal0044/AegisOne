from app.models.asset import IndustrialAsset
from app.repositories.base import BaseRepository


class IndustrialAssetRepository(BaseRepository[IndustrialAsset]):
    def __init__(self) -> None:
        super().__init__(IndustrialAsset)


industrial_asset_repo = IndustrialAssetRepository()
