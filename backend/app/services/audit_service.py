import uuid
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.repositories.audit_log import audit_log_repo

logger = logging.getLogger("app.services.audit_service")


class AuditService:
    def log_action(
        self,
        db: Session,
        action: str,
        details: str,
        ip_address: str = "127.0.0.1",
        user_id: Optional[uuid.UUID] = None
    ) -> AuditLog:
        """Create and persist a centralized audit log record in PostgreSQL."""
        try:
            log = AuditLog(
                action=action,
                details=details,
                ip_address=ip_address,
                user_id=user_id
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            logger.info(f"Audit log commited: [{action}] - {details}")
            
            # Publish audit log creation via SSE for operations dashboard update
            from app.services.sse_manager import sse_manager
            sse_manager.publish("AUDIT_LOG_CREATED", {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat() + "Z" if hasattr(log.timestamp, "isoformat") else str(log.timestamp),
                "action": log.action,
                "ip_address": log.ip_address,
                "details": log.details,
                "user_id": str(log.user_id) if log.user_id else None
            })
            
            return log
        except Exception as e:
            logger.error(f"Failed to write audit log action {action}: {e}", exc_info=True)
            db.rollback()
            raise

    def get_logs(self, db: Session, skip: int = 0, limit: int = 200) -> List[AuditLog]:
        """Fetch chronological audit records sorted by descending timestamp."""
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())


audit_service = AuditService()
