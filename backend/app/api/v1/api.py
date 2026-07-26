from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    users,
    devices,
    assets,
    events,
    alerts,
    risk_scores,
    simulation,
    behavior,
    ai,
    threats,
    sse,
    copilot,
    config,
    audit,
)

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(assets.router, prefix="/industrial-assets", tags=["Industrial Assets"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(risk_scores.router, prefix="/risk-scores", tags=["Risk Scores"])
api_router.include_router(simulation.router, tags=["Simulation Engine"])
api_router.include_router(behavior.router, prefix="/behavior", tags=["Behavioral Intelligence"])
api_router.include_router(ai.router, tags=["Behavioral Intelligence Engine"])
api_router.include_router(threats.router, tags=["Threat Scenario Engine"])
api_router.include_router(sse.router, tags=["Real-time Streaming"])
api_router.include_router(copilot.router, tags=["AI Security Copilot"])
api_router.include_router(config.router, tags=["Admin Configuration"])
api_router.include_router(audit.router, tags=["Audit Trail"])
