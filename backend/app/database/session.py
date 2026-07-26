from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Create DB engine with pre-ping validation to verify connection freshness
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Configured sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for declarative ORM models
class Base(DeclarativeBase):
    pass


# Dependency to inject DB session into FastAPI request context
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
