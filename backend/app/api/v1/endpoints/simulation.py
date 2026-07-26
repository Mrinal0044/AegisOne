from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.session import get_db
from app.services.simulation_engine import simulation_engine
from app.repositories.simulation import simulation_config_repo, simulation_state_repo
from app.repositories.profile import behavior_profile_repo
from app.schemas.simulation import (
    SimulationConfigUpdate,
    SimulationStatusResponse,
    SimulationConfigSchema,
)
from app.schemas.profile import BehaviorProfile
from app.models.user import User
from app.models.device import Device
from app.models.asset import IndustrialAsset

router = APIRouter()


@router.get("/simulation/status", response_model=SimulationStatusResponse)
def get_simulation_status(db: Session = Depends(get_db)) -> SimulationStatusResponse:
    """Retrieve active status parameters, database sizes, and the virtual time clock."""
    config = simulation_config_repo.get_active(db)
    state = simulation_state_repo.get_current(db)
    
    # Quick count queries
    active_emp = db.query(func.count(User.id)).scalar()
    active_dev = db.query(func.count(Device.id)).scalar()
    active_ast = db.query(func.count(IndustrialAsset.id)).scalar()
    
    v_time = simulation_engine.get_virtual_time(config.speed_multiplier)
    v_time_str = v_time.strftime("%Y-%m-%d %H:%M:%S")

    return SimulationStatusResponse(
        status=state.status,
        config=config,
        state=state,
        active_employees_count=active_emp or 0,
        active_devices_count=active_dev or 0,
        active_assets_count=active_ast or 0,
        virtual_system_time=v_time_str
    )


@router.post("/simulation/start", response_model=SimulationStatusResponse)
async def start_simulation(db: Session = Depends(get_db)) -> SimulationStatusResponse:
    """Initiate the simulation background process."""
    try:
        await simulation_engine.start()
        return get_simulation_status(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start simulation: {str(e)}"
        )


@router.post("/simulation/pause", response_model=SimulationStatusResponse)
async def pause_simulation(db: Session = Depends(get_db)) -> SimulationStatusResponse:
    """Pause the running simulation."""
    try:
        await simulation_engine.pause()
        return get_simulation_status(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause simulation: {str(e)}"
        )


@router.post("/simulation/resume", response_model=SimulationStatusResponse)
async def resume_simulation(db: Session = Depends(get_db)) -> SimulationStatusResponse:
    """Resume a paused simulation."""
    try:
        await simulation_engine.resume()
        return get_simulation_status(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume simulation: {str(e)}"
        )


@router.post("/simulation/stop", response_model=SimulationStatusResponse)
async def stop_simulation(db: Session = Depends(get_db)) -> SimulationStatusResponse:
    """Stop the simulation."""
    try:
        await simulation_engine.stop()
        return get_simulation_status(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop simulation: {str(e)}"
        )


@router.post("/simulation/reset", response_model=SimulationStatusResponse)
async def reset_simulation(db: Session = Depends(get_db)) -> SimulationStatusResponse:
    """Reset database tables and clear generated logs."""
    try:
        await simulation_engine.reset()
        return get_simulation_status(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset simulation: {str(e)}"
        )


@router.post("/simulation/config", response_model=SimulationConfigSchema)
def update_simulation_config(
    obj_in: SimulationConfigUpdate,
    db: Session = Depends(get_db)
) -> SimulationConfigSchema:
    """Modify simulation parameters (speed multiplier, target device/employee counts)."""
    config = simulation_config_repo.get_active(db)
    
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/behavior-profiles", response_model=List[BehaviorProfile])
def get_behavior_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[BehaviorProfile]:
    """Retrieve baseline normal behavioral profiles."""
    return behavior_profile_repo.get_multi(db, skip=skip, limit=limit)
