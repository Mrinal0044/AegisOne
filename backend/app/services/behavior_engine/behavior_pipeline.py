import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, text, func
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.event import Event
from app.models.user import User
from app.models.device import Device
from app.models.asset import IndustrialAsset
from app.models.department import Department
from app.services.behavior_engine.aggregator import aggregator
from app.services.behavior_engine.window_manager import window_manager

logger = logging.getLogger("app.services.behavior_engine.behavior_pipeline")


class BehaviorPipeline:
    _instance: Optional["BehaviorPipeline"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BehaviorPipeline, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    def start_worker(self) -> None:
        """Boot up the background event consumer worker thread."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._consume_queue())
        logger.info("Behavior Engine Queue Consumer worker started.")

    def stop_worker(self) -> None:
        """Shut down the background consumer worker thread."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
        logger.info("Behavior Engine Queue Consumer worker stopped.")

    def enqueue_event(self, event_id: uuid.UUID) -> None:
        """Enqueue an event ID for behavioral processing."""
        self._queue.put_nowait(event_id)

    async def _consume_queue(self) -> None:
        """Background loop reading from queue and computing aggregates."""
        while self._running:
            try:
                event_id = await self._queue.get()
                db = SessionLocal()
                try:
                    # Fetch the event
                    stmt = select(Event).where(Event.id == event_id)
                    event = db.execute(stmt).scalar_one_or_none()
                    
                    if event:
                        ref_time = event.timestamp
                        windows = window_manager.get_supported_windows()
                        
                        # 1. Update User Features
                        if event.user_id:
                            # Retrieve user to check department
                            user_stmt = select(User).where(User.id == event.user_id)
                            user = db.execute(user_stmt).scalar_one_or_none()
                            
                            for w in windows:
                                aggregator.aggregate_user_features(db, event.user_id, ref_time, w)
                                if user and user.department_id:
                                    aggregator.aggregate_dept_features(db, user.department_id, ref_time, w)

                        # 2. Update Device Features
                        if event.device_id:
                            for w in windows:
                                aggregator.aggregate_device_features(db, event.device_id, ref_time, w)

                        # 3. Update Asset Features
                        if event.asset_id:
                            for w in windows:
                                aggregator.aggregate_asset_features(db, event.asset_id, ref_time, w)
                        
                        # 3.5 Execute Advanced Behavioral Rules Checkpoints
                        try:
                            from app.services.detection_engine.advanced_rules import (
                                check_impossible_travel,
                                check_device_spoofing,
                                check_credential_stuffing,
                                check_low_slow_exfiltration,
                                check_insider_drift
                            )
                            check_impossible_travel(db, event)
                            check_device_spoofing(db, event)
                            check_credential_stuffing(db, event)
                            check_low_slow_exfiltration(db, event)
                            check_insider_drift(db, event)
                        except Exception as e:
                            logger.error(f"Error checking advanced rules: {e}", exc_info=True)

                        # 4. Trigger AI Detection and Risk Evaluation
                        from app.services.detection_engine.prediction import prediction_engine
                        if event.user_id:
                            prediction_engine.evaluate_entity(db, "User", event.user_id)
                            # Get user's department to evaluate department risk
                            user_stmt = select(User).where(User.id == event.user_id)
                            user = db.execute(user_stmt).scalar_one_or_none()
                            if user and user.department_id:
                                prediction_engine.evaluate_entity(db, "Department", user.department_id)
                        if event.device_id:
                            prediction_engine.evaluate_entity(db, "Device", event.device_id)
                        if event.asset_id:
                            prediction_engine.evaluate_entity(db, "IndustrialAsset", event.asset_id)

                        # Load related models for serialization
                        username = event.user.username if event.user else None
                        hostname = event.device.hostname if event.device else None
                        asset_name = event.asset.name if event.asset else None

                        db.commit()

                        # Publish processed event to SSE listeners
                        from app.services.sse_manager import sse_manager
                        sse_manager.publish("EVENT_CREATED", {
                            "id": str(event.id),
                            "timestamp": event.timestamp.isoformat() + "Z" if hasattr(event.timestamp, "isoformat") else str(event.timestamp),
                            "event_type": event.event_type,
                            "severity": event.severity,
                            "protocol": event.protocol,
                            "source_ip": event.source_ip,
                            "destination_ip": event.destination_ip,
                            "payload_summary": event.payload_summary,
                            "user": username,
                            "device": hostname,
                            "asset": asset_name
                        })
                except Exception as e:
                    logger.error(f"Error processing enqueued event {event_id}: {str(e)}", exc_info=True)
                    db.rollback()
                finally:
                    db.close()
                    self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in behavior pipeline worker loop: {str(e)}", exc_info=True)
                await asyncio.sleep(1)

    def rebuild_feature_store(self, db: Session) -> None:
        """Truncates the feature store and rebuilds it based on all historical event logs."""
        logger.info("Initiating full rebuild of the Behavioral Feature Store...")
        try:
            # 1. Clear existing features
            db.execute(text("TRUNCATE TABLE user_behavior_features, device_behavior_features, asset_behavior_features, department_behavior_features, behavior_snapshots CASCADE"))
            db.commit()

            # Find maximum event timestamp to use as reference now
            ref_stmt = select(func.max(Event.timestamp))
            ref_time = db.execute(ref_stmt).scalar()
            
            if not ref_time:
                logger.info("No events found in database. Feature store is clear.")
                return

            windows = window_manager.get_supported_windows()

            # Rebuild Users
            users_stmt = select(User.id)
            user_ids = db.execute(users_stmt).scalars().all()
            for uid in user_ids:
                for w in windows:
                    aggregator.aggregate_user_features(db, uid, ref_time, w)

            # Rebuild Devices
            devs_stmt = select(Device.id)
            device_ids = db.execute(devs_stmt).scalars().all()
            for did in device_ids:
                for w in windows:
                    aggregator.aggregate_device_features(db, did, ref_time, w)

            # Rebuild Assets
            assets_stmt = select(IndustrialAsset.id)
            asset_ids = db.execute(assets_stmt).scalars().all()
            for aid in asset_ids:
                for w in windows:
                    aggregator.aggregate_asset_features(db, aid, ref_time, w)

            # Rebuild Departments
            depts_stmt = select(Department.id)
            dept_ids = db.execute(depts_stmt).scalars().all()
            for deid in dept_ids:
                for w in windows:
                    aggregator.aggregate_dept_features(db, deid, ref_time, w)

            db.commit()
            logger.info("Behavioral Feature Store rebuild completed successfully.")
        except Exception as e:
            logger.error(f"Error rebuilding feature store: {str(e)}", exc_info=True)
            db.rollback()
            raise e


behavior_pipeline = BehaviorPipeline()
