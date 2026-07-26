import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.endpoints.health import router as health_router
from app.middleware.error_handler import (
    AegisException,
    RequestLoggingMiddleware,
    aegis_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    global_exception_handler,
)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("app.main")


# --- Lifespan Manager (Startup & Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register main loop for thread-safe SSE
    import asyncio
    from app.services.sse_manager import sse_manager
    sse_manager.loop = asyncio.get_running_loop()

    # 1. Initialize tables (idempotent fallback)
    from app.database.session import engine, Base
    import app.models
    logger.info("Checking database tables configuration...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")

    # 2. Startup seeding execution
    from app.database.session import SessionLocal
    
    db = SessionLocal()
    try:
        if settings.SEED_DATABASE_ON_STARTUP:
            logger.info("SEED_DATABASE_ON_STARTUP is enabled. Running seeder check...")
            from app.services.seeding import seed_db
            seed_db(db)

        # Start behavioral pipeline background worker
        from app.services.behavior_engine.behavior_pipeline import behavior_pipeline
        behavior_pipeline.start_worker()

        # Resume simulation if it was running before restart
        from app.repositories.simulation import simulation_state_repo
        from app.services.simulation_engine import simulation_engine
        
        state = simulation_state_repo.get_current(db)
        if state.status == "RUNNING":
            logger.info("Resuming active simulation background thread...")
            # Toggle state to STOPPED so engine.start() triggers cleanly
            state.status = "STOPPED"
            db.add(state)
            db.commit()
            await simulation_engine.start()
    except Exception as e:
        logger.error(f"Error executing startup tasks: {str(e)}", exc_info=True)
    finally:
        db.close()
    yield
    # Shutdown operations
    from app.services.behavior_engine.behavior_pipeline import behavior_pipeline
    behavior_pipeline.stop_worker()
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AegisOne Industrial Behavioral Intelligence Platform Foundation API",
    lifespan=lifespan,
)

# --- CORS Middleware ---
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Custom Log Middleware ---
app.add_middleware(RequestLoggingMiddleware)

# --- Request Metrics Middleware ---
@app.middleware("http")
async def log_request_metrics(request, call_next):
    import time
    from app.services.metrics_service import metrics_service
    start_time = time.time()
    try:
        response = await call_next(request)
        is_error = response.status_code >= 400
        duration = time.time() - start_time
        if "/sse/stream" not in request.url.path:
            metrics_service.record_request(request.url.path, duration, is_error)
        return response
    except Exception as e:
        duration = time.time() - start_time
        metrics_service.record_request(request.url.path, duration, True)
        raise e

# --- Register Exception Handlers ---
app.add_exception_handler(AegisException, aegis_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# --- Mount API Router under V1 Prefix ---
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- Root Redirect/Endpoints for convenience ---
# Include health router directly at root so GET / and GET /health work on host root too.
app.include_router(health_router)
