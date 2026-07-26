import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # Operator, Engineer, Analyst, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    
    # Simulation Employee Parameters
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Morning, Afternoon, Night
    access_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Level 1 to 5
    working_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # e.g., "08:00"
    working_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # e.g., "16:00"
    
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Geolocation coordinates
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(back_populates="users")
    manager: Mapped[Optional["User"]] = relationship("User", remote_side=[id])
    events: Mapped[list["Event"]] = relationship(back_populates="user")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
