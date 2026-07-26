from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.simulation import SimulationConfig, SimulationState
from app.repositories.base import BaseRepository


class SimulationConfigRepository(BaseRepository[SimulationConfig]):
    def __init__(self) -> None:
        super().__init__(SimulationConfig)

    def get_active(self, db: Session) -> SimulationConfig:
        # Retrieve active config, or create default if none exists
        query = select(SimulationConfig).where(SimulationConfig.is_active == True)
        config = db.execute(query).scalars().first()
        if not config:
            config = SimulationConfig(
                speed_multiplier=1.0,
                num_employees=20,
                num_devices=30,
                event_rate=1.0,
                is_active=True
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return config


class SimulationStateRepository(BaseRepository[SimulationState]):
    def __init__(self) -> None:
        super().__init__(SimulationState)

    def get_current(self, db: Session) -> SimulationState:
        # Retrieve current state, or initialize default
        query = select(SimulationState)
        state = db.execute(query).scalars().first()
        if not state:
            state = SimulationState(
                status="IDLE",
                total_events_generated=0
            )
            db.add(state)
            db.commit()
            db.refresh(state)
        return state


simulation_config_repo = SimulationConfigRepository()
simulation_state_repo = SimulationStateRepository()
