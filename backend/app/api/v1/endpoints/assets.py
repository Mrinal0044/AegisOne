from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.asset import IndustrialAsset
from app.services.asset_service import industrial_asset_service

router = APIRouter()


@router.get("", response_model=List[IndustrialAsset])
def read_industrial_assets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[IndustrialAsset]:
    """
    Retrieve all industrial assets (PLCs, HMIs, RTUs, SCADA).
    """
    return industrial_asset_service.get_assets(db, skip=skip, limit=limit)
