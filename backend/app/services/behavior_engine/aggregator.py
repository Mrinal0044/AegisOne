import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.user import User
from app.models.feature_store import (
    UserBehaviorFeatures,
    DeviceBehaviorFeatures,
    AssetBehaviorFeatures,
    DepartmentBehaviorFeatures,
    BehaviorSnapshot,
)
from app.repositories.feature_store import (
    user_features_repo,
    device_features_repo,
    asset_features_repo,
    dept_features_repo,
    snapshot_repo,
)
from app.services.behavior_engine.window_manager import window_manager
from app.services.behavior_engine.event_processor import event_processor

logger = logging.getLogger("app.services.behavior_engine.aggregator")


class Aggregator:
    @staticmethod
    def aggregate_user_features(db: Session, user_id: uuid.UUID, reference_time: datetime, window_size: str) -> None:
        """Query and compute behavioral feature metrics for a single user in a rolling window."""
        cutoff = window_manager.get_window_cutoff(reference_time, window_size)
        duration_hours = window_manager.WINDOW_DURATIONS[window_size] / 3600.0

        # Query all events for the user in this window
        stmt = select(Event).where(
            Event.user_id == user_id,
            Event.timestamp >= cutoff,
            Event.timestamp <= reference_time
        )
        events = list(db.execute(stmt).scalars().all())
        total_events = len(events)

        # Get or create the feature vector row
        features = user_features_repo.get_or_create(db, user_id, window_size)

        if total_events == 0:
            # Clear features if no events exist in this window
            features.avg_session_duration = 0.0
            features.failed_login_count = 0
            features.unique_devices_count = 0
            features.unique_assets_count = 0
            features.commands_per_hour = 0.0
            features.weekend_activity_ratio = 0.0
            features.night_activity_ratio = 0.0
            features.remote_login_count = 0
            features.usb_usage_count = 0
            features.download_frequency = 0.0
            features.config_change_count = 0
            features.failed_auth_count = 0
            db.add(features)
            db.flush()
            return

        # Normalize events
        normalized = [event_processor.normalize_event(e) for e in events]

        # Calculate counts and metrics
        failed_logins = sum(1 for e in normalized if e["is_failed_login"])
        failed_auths = sum(1 for e in normalized if e["is_failed_auth"])
        usb_count = sum(1 for e in normalized if e["is_usb"])
        config_changes = sum(1 for e in normalized if e["is_config_change"])
        remote_logins = sum(1 for e in normalized if e["is_remote"])
        downloads = sum(1 for e in normalized if e["is_download"])
        
        # Commands: events that represent PLC write/read actions or modifications
        commands_count = sum(1 for e in normalized if e["is_plc_access"] or e["is_config_change"])
        commands_rate = commands_count / duration_hours

        # Unique counts
        unique_devices = len({e.device_id for e in events if e.device_id is not None})
        unique_assets = len({e.asset_id for e in events if e.asset_id is not None})

        # Ratios
        weekend_events = sum(1 for e in normalized if e["timestamp"].weekday() >= 5)
        weekend_ratio = weekend_events / total_events

        night_events = sum(1 for e in normalized if e["timestamp"].hour >= 18 or e["timestamp"].hour < 6)
        night_ratio = night_events / total_events

        # Simple session calculation: find login & logout pairs
        logins = sorted([e["timestamp"] for e in normalized if e["is_login"]])
        logouts = sorted([e["timestamp"] for e in normalized if e["is_logout"]])
        
        session_durations = []
        for login_t in logins:
            # find first logout after login
            matching_logouts = [lo for lo in logouts if lo > login_t]
            if matching_logouts:
                session_durations.append((matching_logouts[0] - login_t).total_seconds())
        
        avg_session = sum(session_durations) / len(session_durations) if session_durations else 28800.0

        # Update columns
        features.avg_session_duration = avg_session
        features.failed_login_count = failed_logins
        features.unique_devices_count = unique_devices
        features.unique_assets_count = unique_assets
        features.commands_per_hour = commands_rate
        features.weekend_activity_ratio = weekend_ratio
        features.night_activity_ratio = night_ratio
        features.remote_login_count = remote_logins
        features.usb_usage_count = usb_count
        features.download_frequency = downloads / duration_hours
        features.config_change_count = config_changes
        features.failed_auth_count = failed_auths
        
        db.add(features)
        db.flush()

    @staticmethod
    def aggregate_device_features(db: Session, device_id: uuid.UUID, reference_time: datetime, window_size: str) -> None:
        """Compute metrics for a device in a rolling window."""
        cutoff = window_manager.get_window_cutoff(reference_time, window_size)
        duration_hours = window_manager.WINDOW_DURATIONS[window_size] / 3600.0

        stmt = select(Event).where(
            Event.device_id == device_id,
            Event.timestamp >= cutoff,
            Event.timestamp <= reference_time
        )
        events = list(db.execute(stmt).scalars().all())
        total_events = len(events)

        features = device_features_repo.get_or_create(db, device_id, window_size)

        if total_events == 0:
            features.active_hours = 0.0
            features.connected_users_count = 0
            features.avg_network_traffic_bytes = 0.0
            features.config_change_count = 0
            features.firmware_change_count = 0
            features.maintenance_frequency = 0.0
            features.unexpected_downtime_count = 0
            db.add(features)
            db.flush()
            return

        normalized = [event_processor.normalize_event(e) for e in events]

        connected_users = len({e.user_id for e in events if e.user_id is not None})
        config_changes = sum(1 for e in normalized if e["is_config_change"])
        firmware_changes = sum(1 for e in normalized if e["is_firmware_update"])
        maintenance_events = sum(1 for e in normalized if e["is_maintenance"])
        
        # Approximations for active hours and network traffic
        active_hours = min(duration_hours, total_events * 0.1)  # simple scaling metric
        traffic_bytes = sum(e["payload_length"] for e in normalized) * 150.0  # estimate packets size

        features.active_hours = active_hours
        features.connected_users_count = connected_users
        features.avg_network_traffic_bytes = traffic_bytes / max(1.0, total_events)
        features.config_change_count = config_changes
        features.firmware_change_count = firmware_changes
        features.maintenance_frequency = maintenance_events / duration_hours
        features.unexpected_downtime_count = sum(1 for e in normalized if e["severity"] == "critical" and e["is_maintenance"])
        
        db.add(features)
        db.flush()

    @staticmethod
    def aggregate_asset_features(db: Session, asset_id: uuid.UUID, reference_time: datetime, window_size: str) -> None:
        """Compute metrics for an industrial asset in a rolling window."""
        cutoff = window_manager.get_window_cutoff(reference_time, window_size)
        duration_hours = window_manager.WINDOW_DURATIONS[window_size] / 3600.0

        stmt = select(Event).where(
            Event.asset_id == asset_id,
            Event.timestamp >= cutoff,
            Event.timestamp <= reference_time
        )
        events = list(db.execute(stmt).scalars().all())
        total_events = len(events)

        features = asset_features_repo.get_or_create(db, asset_id, window_size)

        if total_events == 0:
            features.access_frequency = 0.0
            features.unique_operators_count = 0
            features.avg_commands_count = 0.0
            features.alarm_acknowledgements_count = 0
            features.maintenance_events_count = 0
            features.operational_hours = 0.0
            db.add(features)
            db.flush()
            return

        normalized = [event_processor.normalize_event(e) for e in events]

        operators = len({e.user_id for e in events if e.user_id is not None})
        commands = sum(1 for e in normalized if e["is_plc_access"] or e["is_config_change"])
        alarm_acks = sum(1 for e in normalized if e["is_alarm_ack"])
        maintenance_events = sum(1 for e in normalized if e["is_maintenance"])

        features.access_frequency = total_events / duration_hours
        features.unique_operators_count = operators
        features.avg_commands_count = commands / max(1.0, total_events)
        features.alarm_acknowledgements_count = alarm_acks
        features.maintenance_events_count = maintenance_events
        features.operational_hours = min(duration_hours, total_events * 0.2)

        db.add(features)
        db.flush()

    @staticmethod
    def aggregate_dept_features(db: Session, dept_id: uuid.UUID, reference_time: datetime, window_size: str) -> None:
        """Compute metrics for a department in a rolling window."""
        cutoff = window_manager.get_window_cutoff(reference_time, window_size)
        duration_hours = window_manager.WINDOW_DURATIONS[window_size] / 3600.0

        # Departments events are mapped via Users associated with that department
        # We find users in department
        stmt = select(User.id).where(User.department_id == dept_id)
        user_ids = list(db.execute(stmt).scalars().all())

        if not user_ids:
            return

        stmt = select(Event).where(
            Event.user_id.in_(user_ids),
            Event.timestamp >= cutoff,
            Event.timestamp <= reference_time
        )
        events = list(db.execute(stmt).scalars().all())
        total_events = len(events)

        features = dept_features_repo.get_or_create(db, dept_id, window_size)

        if total_events == 0:
            features.peak_activity_rate = 0.0
            features.avg_users_online = 0.0
            features.unique_assets_accessed_count = 0
            features.avg_network_usage = 0.0
            features.typical_working_hours_ratio = 1.0
            db.add(features)
            db.flush()
            return

        normalized = [event_processor.normalize_event(e) for e in events]

        unique_assets = len({e.asset_id for e in events if e.asset_id is not None})
        users_count = len({e.user_id for e in events if e.user_id is not None})
        
        # Calculate working hour ratios
        # Normal shifts are Morning/Afternoon (06:00 to 22:00)
        standard_hours = sum(1 for e in normalized if 6 <= e["timestamp"].hour < 22)
        ratio = standard_hours / total_events

        features.peak_activity_rate = total_events / duration_hours
        features.avg_users_online = float(users_count)
        features.unique_assets_accessed_count = unique_assets
        features.avg_network_usage = sum(e["payload_length"] for e in normalized) / max(1.0, total_events)
        features.typical_working_hours_ratio = ratio

        db.add(features)
        db.flush()


aggregator = Aggregator()
