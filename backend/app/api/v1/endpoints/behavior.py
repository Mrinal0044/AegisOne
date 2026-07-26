import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.session import get_db
from app.repositories import (
    user_features_repo,
    device_features_repo,
    asset_features_repo,
    dept_features_repo,
    user_repo,
    device_repo,
    industrial_asset_repo,
    department_repo,
    behavior_profile_repo,
)
from app.schemas.feature_store import (
    UserBehaviorFeaturesSchema,
    DeviceBehaviorFeaturesSchema,
    AssetBehaviorFeaturesSchema,
    DepartmentBehaviorFeaturesSchema,
)
from app.services.behavior_engine.behavior_pipeline import behavior_pipeline
from app.services.behavior_engine.window_manager import window_manager
from app.models.feature_store import (
    UserBehaviorFeatures,
    DeviceBehaviorFeatures,
    AssetBehaviorFeatures,
    DepartmentBehaviorFeatures,
    BehaviorSnapshot,
)

router = APIRouter()


@router.get("/features/users", response_model=List[UserBehaviorFeaturesSchema])
def get_user_features(
    window: str = Query("1h", description="Window size (5m, 15m, 1h, 24h, 7d)"),
    db: Session = Depends(get_db)
):
    """Retrieve engineered behavioral feature vectors for all users under the selected window size."""
    if window not in window_manager.get_supported_windows():
        raise HTTPException(status_code=400, detail=f"Unsupported window size: {window}")
    return user_features_repo.get_all_by_window(db, window)


@router.get("/features/devices", response_model=List[DeviceBehaviorFeaturesSchema])
def get_device_features(
    window: str = Query("1h", description="Window size (5m, 15m, 1h, 24h, 7d)"),
    db: Session = Depends(get_db)
):
    """Retrieve engineered behavioral features for all network terminals under the selected window size."""
    if window not in window_manager.get_supported_windows():
        raise HTTPException(status_code=400, detail=f"Unsupported window size: {window}")
    return device_features_repo.get_all_by_window(db, window)


@router.get("/features/assets", response_model=List[AssetBehaviorFeaturesSchema])
def get_asset_features(
    window: str = Query("1h", description="Window size (5m, 15m, 1h, 24h, 7d)"),
    db: Session = Depends(get_db)
):
    """Retrieve engineered behavioral features for all industrial assets under the selected window size."""
    if window not in window_manager.get_supported_windows():
        raise HTTPException(status_code=400, detail=f"Unsupported window size: {window}")
    return asset_features_repo.get_all_by_window(db, window)


@router.get("/features/departments", response_model=List[DepartmentBehaviorFeaturesSchema])
def get_department_features(
    window: str = Query("1h", description="Window size (5m, 15m, 1h, 24h, 7d)"),
    db: Session = Depends(get_db)
):
    """Retrieve department-level behavioral aggregations."""
    if window not in window_manager.get_supported_windows():
        raise HTTPException(status_code=400, detail=f"Unsupported window size: {window}")
    return dept_features_repo.get_all_by_window(db, window)


@router.get("/profile/{entity_id}", response_model=Dict[str, Any])
def get_entity_behavior_profile(entity_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve a comprehensive behavioral analysis profile for any entity ID (User, Device, Asset, Dept)."""
    # 1. Check if it is a User
    user = user_repo.get(db, entity_id)
    if user:
        # Load features for all windows
        features_stmt = select(UserBehaviorFeatures).where(UserBehaviorFeatures.user_id == entity_id)
        feats = db.execute(features_stmt).scalars().all()
        # Look up baseline profile
        bp_stmt = select(user_repo.model).where(user_repo.model.id == entity_id)
        # We can also search behavior_profiles table
        bp = behavior_profile_repo.get(db, entity_id)
        
        return {
            "entity_type": "User",
            "metadata": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
            },
            "baseline_profile": bp,
            "rolling_windows": {f.window_size: UserBehaviorFeaturesSchema.model_validate(f) for f in feats}
        }

    # 2. Check if Device
    device = device_repo.get(db, entity_id)
    if device:
        features_stmt = select(DeviceBehaviorFeatures).where(DeviceBehaviorFeatures.device_id == entity_id)
        feats = db.execute(features_stmt).scalars().all()
        return {
            "entity_type": "Device",
            "metadata": {
                "id": device.id,
                "hostname": device.hostname,
                "ip_address": device.ip_address,
                "device_type": device.device_type,
            },
            "rolling_windows": {f.window_size: DeviceBehaviorFeaturesSchema.model_validate(f) for f in feats}
        }

    # 3. Check if Asset
    asset = industrial_asset_repo.get(db, entity_id)
    if asset:
        features_stmt = select(AssetBehaviorFeatures).where(AssetBehaviorFeatures.asset_id == entity_id)
        feats = db.execute(features_stmt).scalars().all()
        return {
            "entity_type": "IndustrialAsset",
            "metadata": {
                "id": asset.id,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "vendor": asset.vendor,
            },
            "rolling_windows": {f.window_size: AssetBehaviorFeaturesSchema.model_validate(f) for f in feats}
        }

    # 4. Check if Department
    dept = department_repo.get(db, entity_id)
    if dept:
        features_stmt = select(DepartmentBehaviorFeatures).where(DepartmentBehaviorFeatures.department_id == entity_id)
        feats = db.execute(features_stmt).scalars().all()
        return {
            "entity_type": "Department",
            "metadata": {
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
            },
            "rolling_windows": {f.window_size: DepartmentBehaviorFeaturesSchema.model_validate(f) for f in feats}
        }

    raise HTTPException(status_code=404, detail="Entity profile not found for the specified ID.")


@router.get("/statistics", response_model=Dict[str, Any])
def get_behavior_statistics(db: Session = Depends(get_db)):
    """Retrieve database metrics about the Feature Store tables size and snapshot logs count."""
    user_cnt = db.execute(select(func.count(UserBehaviorFeatures.id))).scalar()
    device_cnt = db.execute(select(func.count(DeviceBehaviorFeatures.id))).scalar()
    asset_cnt = db.execute(select(func.count(AssetBehaviorFeatures.id))).scalar()
    dept_cnt = db.execute(select(func.count(DepartmentBehaviorFeatures.id))).scalar()
    snapshot_cnt = db.execute(select(func.count(BehaviorSnapshot.id))).scalar()

    return {
        "user_features_count": user_cnt,
        "device_features_count": device_cnt,
        "asset_features_count": asset_cnt,
        "department_features_count": dept_cnt,
        "snapshots_count": snapshot_cnt,
        "supported_windows": window_manager.get_supported_windows(),
    }


@router.get("/windows", response_model=List[str])
def get_behavior_windows():
    """Retrieve the list of rolling windows configured in the pipeline."""
    return window_manager.get_supported_windows()


@router.post("/rebuild")
def rebuild_behavior_features(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Initiates a background task to rebuild the complete Feature Store from raw database logs."""
    background_tasks.add_task(behavior_pipeline.rebuild_feature_store, db)
    return {"message": "Feature store rebuild task initiated in background thread."}
