from typing import Dict, Any, Optional
from datetime import datetime
from app.models.event import Event


class EventProcessor:
    @staticmethod
    def normalize_event(event: Event) -> Dict[str, Any]:
        """Convert a raw database Event model into a standard dictionary of behavior indicators."""
        event_type = event.event_type.lower()
        protocol = event.protocol.lower()
        severity = event.severity.lower()

        # Flags for common user behaviors
        is_login = "login" in event_type and "logout" not in event_type
        is_logout = "logout" in event_type
        is_failed_login = "failed" in event_type and "login" in event_type
        is_failed_auth = is_failed_login or "unauthorized" in event_type
        
        # Action types
        is_plc_access = "plc" in event_type or protocol in ["s7comm", "modbus/tcp"]
        is_config_change = "config" in event_type or "modify" in event_type or "recipe" in event_type
        is_firmware_update = "firmware" in event_type or "upgrade" in event_type
        is_usb = "usb" in event_type
        is_download = "download" in event_type or "file" in event_type
        is_sensor_read = "sensor" in event_type or "telemetry" in event_type or "read" in event_type
        is_alarm_ack = "ack" in event_type or "alarm" in event_type
        is_maintenance = "maintenance" in event_type or "inspect" in event_type
        
        # Network details
        is_remote = "remote" in event_type or "ssh" in event_type or "vnc" in event_type
        
        return {
            "id": event.id,
            "timestamp": event.timestamp,
            "user_id": event.user_id,
            "device_id": event.device_id,
            "asset_id": event.asset_id,
            "severity": severity,
            "is_login": is_login,
            "is_logout": is_logout,
            "is_failed_login": is_failed_login,
            "is_failed_auth": is_failed_auth,
            "is_plc_access": is_plc_access,
            "is_config_change": is_config_change,
            "is_firmware_update": is_firmware_update,
            "is_usb": is_usb,
            "is_download": is_download,
            "is_sensor_read": is_sensor_read,
            "is_alarm_ack": is_alarm_ack,
            "is_maintenance": is_maintenance,
            "is_remote": is_remote,
            "payload_length": len(event.payload_summary) if event.payload_summary else 0
        }


event_processor = EventProcessor()
