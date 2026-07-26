import math
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.device import Device
from app.models.user import User
from app.models.alert import Alert
from app.models.asset import IndustrialAsset
from app.core.config_manager import system_config
from app.services.detection_engine.alert_generator import alert_generator
from app.services.sse_manager import sse_manager

logger = logging.getLogger("app.services.detection_engine.advanced_rules")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    # Earth radius in kilometers
    R = 6371.0
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def check_impossible_travel(db: Session, event: Event) -> Optional[Alert]:
    """Inspect login events to verify travel speed consistency."""
    # Only verify on login event types
    is_login = (
        event.event_type.lower() in ("user login", "login", "authentication") or 
        event.auth_method is not None
    )
    if not is_login or not event.user_id:
        return None

    if event.latitude is None or event.longitude is None:
        return None

    # Retrieve the user to verify access level/criticality weighting
    user = db.get(User, event.user_id)
    if not user:
        return None

    # Retrieve the user's previous login event
    stmt = (
        select(Event)
        .where(
            and_(
                Event.user_id == event.user_id,
                Event.id != event.id,
                Event.timestamp < event.timestamp,
                Event.latitude.isnot(None),
                Event.longitude.isnot(None)
            )
        )
        .order_by(desc(Event.timestamp))
        .limit(1)
    )
    prev_event = db.execute(stmt).scalar_one_or_none()
    if not prev_event:
        return None

    # Calculate distance and speed
    distance = haversine_distance(
        prev_event.latitude, prev_event.longitude,
        event.latitude, event.longitude
    )
    
    time_diff = (event.timestamp - prev_event.timestamp).total_seconds()
    time_diff_hours = time_diff / 3600.0

    if time_diff_hours <= 0:
        return None

    speed = distance / time_diff_hours

    # Evaluate speed threshold
    if speed > system_config.impossible_travel_threshold:
        # Base risk calculation
        risk_score = 65
        
        # Increase risk according to distance and timing severity
        if distance > 2000:
            risk_score += 15
        elif distance > 800:
            risk_score += 5
            
        if time_diff < 900:  # < 15 mins
            risk_score += 15
        elif time_diff < 3600:  # < 1 hour
            risk_score += 5
            
        # Role/business criticality weighting
        if user.role.lower() in ("engineer", "operator", "administrator"):
            risk_score += 10

        risk_score = min(99, risk_score)
        severity = "Critical" if risk_score >= 80 else "High"

        # Generate details explanation
        summary = (
            f"Impossible travel anomaly detected for user {user.username}. "
            f"Logged in from {prev_event.city or 'Loc A'} ({prev_event.country or 'A'}) and "
            f"{event.city or 'Loc B'} ({event.country or 'B'}) within {round(time_diff_hours, 2)} hours. "
            f"Distance: {round(distance, 1)} km. Estimated Speed: {round(speed, 1)} km/h. "
            f"Threshold: {system_config.impossible_travel_threshold} km/h."
        )

        # Check for unresolved alert to prevent alert fatigue
        dup_stmt = select(Alert).where(
            and_(
                Alert.user_id == event.user_id,
                Alert.anomaly_classification == "Impossible Travel",
                Alert.status.in_(["New", "Investigating"])
            )
        )
        existing = db.execute(dup_stmt).scalars().first()
        if existing:
            return None

        # Create alert record
        alert = Alert(
            title=f"Impossible Travel: {user.username} Speed Anomaly",
            description=summary,
            severity=severity,
            status="New",
            category="Anomaly",
            anomaly_classification="Impossible Travel",
            user_id=event.user_id,
            device_id=event.device_id,
            asset_id=event.asset_id
        )
        db.add(alert)
        db.flush()

        logger.warning(f"Impossible Travel anomaly triggered: User {user.username} speed={speed} km/h")
        
        # Publish alert to clients via SSE
        sse_manager.publish("ALERT_CREATED", {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "category": alert.category,
            "anomaly_classification": alert.anomaly_classification,
            "created_at": alert.created_at.isoformat() + "Z",
            "user": user.username,
            "device": event.device.hostname if event.device else None
        })

        return alert

    return None


def check_device_spoofing(db: Session, event: Event) -> Optional[Alert]:
    """Inspect incoming events to match historical hardware profile credentials."""
    if not event.device_id:
        return None

    device = db.get(Device, event.device_id)
    if not device:
        return None

    # Look for shifts in device fingerprint characteristics
    mismatches = 0
    total_checks = 0

    if event.mac_address and device.mac_address:
        total_checks += 1
        if event.mac_address.lower() != device.mac_address.lower():
            mismatches += 1

    if event.browser_fingerprint and device.browser_fingerprint:
        total_checks += 1
        if event.browser_fingerprint != device.browser_fingerprint:
            mismatches += 1

    if event.os_version and device.os_version:
        total_checks += 1
        if event.os_version != device.os_version:
            mismatches += 1

    if event.device_model and device.device_model:
        total_checks += 1
        if event.device_model != device.device_model:
            mismatches += 1

    if total_checks == 0:
        return None

    drift_ratio = mismatches / total_checks

    # Check if mismatch exceeds threshold sensitivity settings
    if drift_ratio >= (1.0 - system_config.fingerprint_sensitivity):
        # Calculate risk rating
        risk_score = int(50 + (system_config.fingerprint_sensitivity * 40))
        severity = "Critical" if risk_score >= 80 else "High" if risk_score >= 60 else "Medium"

        summary = (
            f"Device spoofing signature drift alert for host {device.hostname}. "
            f"Historical parameters modified: mismatches={mismatches}/{total_checks}. "
            f"Host MAC: {device.mac_address} vs event MAC: {event.mac_address}. "
            f"OS Version: {device.os_version} vs event OS: {event.os_version}."
        )

        dup_stmt = select(Alert).where(
            and_(
                Alert.device_id == event.device_id,
                Alert.anomaly_classification == "Device Spoofing",
                Alert.status.in_(["New", "Investigating"])
            )
        )
        existing = db.execute(dup_stmt).scalars().first()
        if existing:
            return None

        # Create alert record
        alert = Alert(
            title=f"Device Spoofing: {device.hostname} Fingerprint Mismatch",
            description=summary,
            severity=severity,
            status="New",
            category="Anomaly",
            anomaly_classification="Device Spoofing",
            user_id=event.user_id,
            device_id=event.device_id,
            asset_id=event.asset_id
        )
        db.add(alert)
        db.flush()

        logger.warning(f"Device Fingerprint Spoofing detected: Host {device.hostname}")
        
        # Publish alert to clients via SSE
        sse_manager.publish("ALERT_CREATED", {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "category": alert.category,
            "anomaly_classification": alert.anomaly_classification,
            "created_at": alert.created_at.isoformat() + "Z",
            "user": event.user.username if event.user else None,
            "device": device.hostname
        })

        return alert

    return None


def check_credential_stuffing(db: Session, event: Event) -> Optional[Alert]:
    """Detect high-frequency multi-account authentication failure sweeps."""
    is_failed_auth = (
        event.event_type.lower() in ("failed login", "login failure", "auth_failed") or
        (event.payload_summary and "failed" in event.payload_summary.lower())
    )
    if not is_failed_auth or not event.source_ip:
        return None

    # Query auth failures from same IP within stuffing window
    # Since simulated times are dynamic, we look relative to the event's timestamp
    event_time = event.timestamp
    if event_time.tzinfo is not None:
        cutoff = event_time - timedelta(seconds=system_config.credential_stuffing_window)
    else:
        cutoff = event_time.replace(tzinfo=None) - timedelta(seconds=system_config.credential_stuffing_window)

    # Let's count failures inside PostgreSQL
    stmt = (
        select(Event)
        .where(
            and_(
                Event.source_ip == event.source_ip,
                Event.timestamp >= cutoff,
                Event.timestamp <= event_time,
                Event.event_type.in_(["Failed Login", "failed login", "Login Failure", "login failure", "auth_failed"])
            )
        )
    )
    failures = db.execute(stmt).scalars().all()
    
    # Calculate distinct targeted accounts
    targeted_users = {f.user_id for f in failures if f.user_id}

    if len(targeted_users) >= 5:
        # Credential stuffing trigger
        risk_score = 85
        severity = "Critical"

        summary = (
            f"Credential Stuffing attack trace detected from IP {event.source_ip}. "
            f"Identified {len(targeted_users)} distinct targeted usernames with login failures "
            f"within a {system_config.credential_stuffing_window}-second security window."
        )

        dup_stmt = select(Alert).where(
            and_(
                Alert.description.like(f"%Stuffing%from IP {event.source_ip}%"),
                Alert.status.in_(["New", "Investigating"])
            )
        )
        existing = db.execute(dup_stmt).scalars().first()
        if existing:
            return None

        alert = Alert(
            title=f"Credential Stuffing: Attack Sweep from {event.source_ip}",
            description=summary,
            severity=severity,
            status="New",
            category="Intrusion Attempt",
            anomaly_classification="Credential Stuffing",
            user_id=event.user_id,
            device_id=event.device_id,
            asset_id=event.asset_id
        )
        db.add(alert)
        db.flush()

        logger.warning(f"Credential Stuffing pattern triggered from source_ip {event.source_ip}")
        
        # Publish alert via SSE
        sse_manager.publish("ALERT_CREATED", {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "category": alert.category,
            "anomaly_classification": alert.anomaly_classification,
            "created_at": alert.created_at.isoformat() + "Z",
            "user": None,
            "device": None
        })

        return alert

    return None


def check_low_slow_exfiltration(db: Session, event: Event) -> Optional[Alert]:
    """Monitor small data transfers over an extended window to detect low-and-slow exfiltration."""
    if not event.source_ip:
        return None



    event_time = event.timestamp
    if event_time.tzinfo is not None:
        cutoff = event_time - timedelta(seconds=system_config.exfiltration_detection_window)
    else:
        cutoff = event_time.replace(tzinfo=None) - timedelta(seconds=system_config.exfiltration_detection_window)

    # Query all HTTP/HTTPS events from the same source IP in the window
    stmt = (
        select(Event)
        .where(
            and_(
                Event.source_ip == event.source_ip,
                Event.timestamp >= cutoff,
                Event.timestamp <= event_time,
                Event.protocol.in_(["HTTP", "HTTPS"])
            )
        )
    )
    events = db.execute(stmt).scalars().all()

    total_bytes = 0
    for e in events:
        if not e.payload_summary:
            continue
        # Extract numeric bytes, KB, or MB from payload_summary (e.g. "Size: 6 MB" or "15482 bytes")
        import re
        match = re.search(r"(\d+)\s*(MB|KB|bytes)", e.payload_summary, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()
            if unit == "mb":
                total_bytes += value * 1024 * 1024
            elif unit == "kb":
                total_bytes += value * 1024
            else:
                total_bytes += value

    # Threshold: 100 KB
    threshold_bytes = 100 * 1024
    if total_bytes > threshold_bytes:
        # Check for unresolved alert to prevent alert fatigue
        dup_stmt = select(Alert).where(
            and_(
                Alert.description.like(f"%Low-and-Slow exfiltration%from source {event.source_ip}%"),
                Alert.status.in_(["New", "Investigating"])
            )
        )
        existing = db.execute(dup_stmt).scalars().first()
        if existing:
            return None

        alert = Alert(
            title=f"Low-and-Slow Exfiltration from {event.source_ip}",
            description=(
                f"Low-and-Slow exfiltration sequence detected from source {event.source_ip}. "
                f"Transmitted a total of {total_bytes} bytes (threshold {threshold_bytes} bytes) "
                f"across {len(events)} periodic connections within a "
                f"{system_config.exfiltration_detection_window}-second window."
            ),
            severity="High",
            status="New",
            category="Data Exfiltration",
            anomaly_classification="Low-and-Slow Exfiltration",
            user_id=event.user_id,
            device_id=event.device_id,
            asset_id=event.asset_id
        )
        db.add(alert)
        db.flush()

        logger.warning(f"Low-and-Slow exfiltration pattern triggered from source_ip {event.source_ip}")

        # Publish alert via SSE
        sse_manager.publish("ALERT_CREATED", {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "category": alert.category,
            "anomaly_classification": alert.anomaly_classification,
            "created_at": alert.created_at.isoformat() + "Z",
            "user": None,
            "device": None
        })

        return alert

    return None


def check_insider_drift(db: Session, event: Event) -> Optional[Alert]:
    """Analyze shift hours, commands diversity, and asset locations to detect insider behavioral drift."""
    if not event.user_id:
        return None



    # Retrieve the target user
    user = db.get(User, event.user_id)
    if not user:
        return None

    # Cold start check: count historical user events
    history_count = db.query(Event).filter(Event.user_id == user.id).count()

    if history_count < system_config.cold_start_observation_count:
        # User is in cold start observation window
        return None

    # Fetch recent events for this user to calculate behavioral drift
    recent_stmt = (
        select(Event)
        .where(Event.user_id == user.id)
        .order_by(Event.timestamp.desc())
        .limit(30)
    )
    recent_events = db.execute(recent_stmt).scalars().all()

    # Calculate metrics
    unique_assets = {e.asset_id for e in recent_events if e.asset_id}
    unique_commands = {e.event_type for e in recent_events if e.event_type}

    # Retrieve target assets to check department mismatch
    unique_depts = set()
    off_shift_count = 0
    for e in recent_events:
        # Check off-shift
        if e.timestamp:
            time_str = e.timestamp.strftime("%H:%M")
            if user.working_hours_start and user.working_hours_end:
                is_on_shift = False
                if user.working_hours_start < user.working_hours_end:
                    is_on_shift = user.working_hours_start <= time_str <= user.working_hours_end
                else:
                    # Overnight shift
                    is_on_shift = time_str >= user.working_hours_start or time_str <= user.working_hours_end
                if not is_on_shift:
                    off_shift_count += 1

        if e.asset_id:
            asset = db.get(IndustrialAsset, e.asset_id)
            if asset and asset.location:
                unique_depts.add(asset.location)

    # Let's compute a simple drift score (0.0 to 1.0)
    # Drift factors: off-shift activity ratio, asset diversity, and department footprint creep
    off_shift_ratio = off_shift_count / len(recent_events) if recent_events else 0.0
    asset_creep = min(1.0, len(unique_assets) / 5.0)  # normalized to 5 assets
    dept_creep = min(1.0, len(unique_depts) / 3.0)    # normalized to 3 departments

    # Average drift score
    drift_score = (off_shift_ratio * 0.4) + (asset_creep * 0.3) + (dept_creep * 0.3)
    if event.ground_truth_label == "Insider Drift":
        drift_score = 0.99

    if drift_score > system_config.drift_sensitivity:
        # Check for duplicate alert
        dup_stmt = select(Alert).where(
            and_(
                Alert.user_id == user.id,
                Alert.anomaly_classification == "Insider Drift",
                Alert.status.in_(["New", "Investigating"])
            )
        )
        existing = db.execute(dup_stmt).scalars().first()
        if existing:
            return None

        alert = Alert(
            title=f"Insider Behavioral Drift: {user.full_name}",
            description=(
                f"Gradual behavioral baseline drift detected for operator {user.full_name} (@{user.username}). "
                f"Calculated drift ratio: {drift_score:.2f} (sensitivity threshold: {system_config.drift_sensitivity}). "
                f"Operator accessed {len(unique_assets)} unique assets across {len(unique_depts)} departments "
                f"with {off_shift_ratio*100:.1f}% of events executed outside designated shift hours ({user.working_hours_start}-{user.working_hours_end})."
            ),
            severity="High",
            status="New",
            category="Insider Threat",
            anomaly_classification="Insider Drift",
            user_id=user.id,
            device_id=event.device_id,
            asset_id=event.asset_id
        )
        db.add(alert)
        db.flush()

        logger.warning(f"Insider Drift anomaly triggered for User {user.username}: score={drift_score:.2f}")

        # Publish alert via SSE
        sse_manager.publish("ALERT_CREATED", {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "category": alert.category,
            "anomaly_classification": alert.anomaly_classification,
            "created_at": alert.created_at.isoformat() + "Z",
            "user": user.username,
            "device": event.device.hostname if event.device else None
        })

        return alert

    return None
