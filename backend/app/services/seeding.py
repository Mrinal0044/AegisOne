import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.user import User
from app.models.asset import IndustrialAsset
from app.models.device import Device
from app.models.event import Event
from app.models.alert import Alert
from app.models.risk_score import RiskScore
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def seed_db(db: Session) -> None:
    # 1. Check if db is already seeded
    existing_dept = db.execute(select(Department).limit(1)).scalar_one_or_none()
    if existing_dept is not None:
        logger.info("Database already seeded. Skipping initial seeding.")
        return

    logger.info("Seeding database with realistic OT cybersecurity data...")

    # 2. Seed Departments
    depts = [
        Department(name="ICS Operations", code="ICS"),
        Department(name="Security Operations Center", code="SOC"),
        Department(name="IT Support", code="ITS"),
    ]
    db.add_all(depts)
    db.flush()  # Generate IDs

    ics_dept = depts[0]
    soc_dept = depts[1]
    its_dept = depts[2]

    # 3. Seed Users
    users = [
        User(
            username="admin",
            email="admin@aegisone.local",
            full_name="System Administrator",
            role="Administrator",
            department_id=soc_dept.id,
            is_active=True,
            country="Germany",
            city="Munich",
            latitude=48.1351,
            longitude=11.5820,
            timezone="Europe/Berlin"
        ),
        User(
            username="j.doe",
            email="j.doe@aegisone.local",
            full_name="John Doe",
            role="Operator",
            department_id=ics_dept.id,
            is_active=True,
            country="USA",
            city="Houston",
            latitude=29.7604,
            longitude=-95.3698,
            timezone="America/Chicago"
        ),
        User(
            username="a.smith",
            email="a.smith@aegisone.local",
            full_name="Alice Smith",
            role="Security Analyst",
            department_id=soc_dept.id,
            is_active=True,
            country="France",
            city="Paris",
            latitude=48.8566,
            longitude=2.3522,
            timezone="Europe/Paris"
        ),
    ]
    db.add_all(users)
    db.flush()

    admin_user = users[0]
    doe_user = users[1]
    smith_user = users[2]

    # 4. Seed Industrial Assets (Physical OT hardware)
    assets = [
        IndustrialAsset(
            name="Turbine PLC 01",
            ip_address="192.168.10.50",
            mac_address="00:1A:2B:3C:4D:5E",
            vendor="Siemens",
            model="S7-1500",
            asset_type="PLC",
            location="Turbine Hall A",
            criticality="Critical",
            status="Operational",
        ),
        IndustrialAsset(
            name="Cooling Pump PLC 02",
            ip_address="192.168.10.52",
            mac_address="00:1A:2B:3C:4D:6F",
            vendor="Schneider Electric",
            model="Modicon M580",
            asset_type="PLC",
            location="Pump Room 1",
            criticality="High",
            status="Operational",
        ),
        IndustrialAsset(
            name="HMI Station 01",
            ip_address="192.168.10.100",
            mac_address="00:1A:2B:3C:4D:7A",
            vendor="Rockwell Automation",
            model="PanelView Plus 7",
            asset_type="HMI",
            location="Central Control Room",
            criticality="High",
            status="Operational",
        ),
        IndustrialAsset(
            name="SCADA Server",
            ip_address="192.168.10.10",
            mac_address="00:1A:2B:3C:4D:8B",
            vendor="Honeywell",
            model="Experion PKS",
            asset_type="SCADA Server",
            location="Server Room 2",
            criticality="Critical",
            status="Operational",
        ),
        IndustrialAsset(
            name="Security Gateway",
            ip_address="192.168.10.1",
            mac_address="00:1A:2B:3C:4D:9C",
            vendor="Cisco",
            model="ISA3000",
            asset_type="Gateway",
            location="Gateway Rack 1",
            criticality="Critical",
            status="Operational",
        ),
    ]
    db.add_all(assets)
    db.flush()

    turbine_plc = assets[0]
    pump_plc = assets[1]
    hmi_station = assets[2]
    scada_server = assets[3]
    gateway = assets[4]

    # 5. Seed Devices (Workstations/Computers interacting with OT)
    devices = [
        Device(
            hostname="op-ws-01.aegisone.local",
            ip_address="192.168.10.110",
            mac_address="00:1A:2B:4D:5E:6F",
            os_version="Windows 10 IoT Enterprise",
            device_type="Operator Station",
            status="Authorized",
            last_seen=datetime.now() - timedelta(minutes=2),
            device_model="Siemens Industrial PC",
            browser_fingerprint="browser-9812-chrome",
            tls_cert_id="tls-81726-sha256",
            protocol="HTTP"
        ),
        Device(
            hostname="eng-ws-01.aegisone.local",
            ip_address="192.168.10.120",
            mac_address="00:1A:2B:4D:5E:7A",
            os_version="Windows 10 Enterprise",
            device_type="Engineering Workstation",
            status="Authorized",
            last_seen=datetime.now() - timedelta(minutes=5),
            device_model="Dell OptiPlex",
            browser_fingerprint="browser-2831-chrome",
            tls_cert_id="tls-29381-sha256",
            protocol="HTTP"
        ),
        Device(
            hostname="rogue-laptop.local",
            ip_address="192.168.10.222",
            mac_address="00:1A:2B:4D:5E:8B",
            os_version="Kali Linux 2026.1",
            device_type="Laptop",
            status="Quarantined",
            last_seen=datetime.now() - timedelta(hours=1),
            device_model="Lenovo ThinkPad",
            browser_fingerprint="browser-5555-firefox",
            tls_cert_id="tls-11111-sha256",
            protocol="SSH"
        ),
    ]
    db.add_all(devices)
    db.flush()

    operator_ws = devices[0]
    eng_ws = devices[1]
    rogue_laptop = devices[2]

    # 6. Seed Events
    now = datetime.now()
    events = [
        Event(
            timestamp=now - timedelta(hours=2),
            source_ip=operator_ws.ip_address,
            destination_ip=pump_plc.ip_address,
            protocol="Modbus/TCP",
            event_type="Register Read",
            payload_summary="Read Holding Register 40001-40010 (Flow Rate Telemetry)",
            severity="Info",
            device_id=operator_ws.id,
            asset_id=pump_plc.id,
            user_id=doe_user.id,
        ),
        Event(
            timestamp=now - timedelta(hours=1, minutes=45),
            source_ip=eng_ws.ip_address,
            destination_ip=turbine_plc.ip_address,
            protocol="S7Comm",
            event_type="Connection Established",
            payload_summary="TCP Handshake Port 102, S7Comm session initialized",
            severity="Info",
            device_id=eng_ws.id,
            asset_id=turbine_plc.id,
            user_id=doe_user.id,
        ),
        Event(
            timestamp=now - timedelta(hours=1, minutes=30),
            source_ip=eng_ws.ip_address,
            destination_ip=turbine_plc.ip_address,
            protocol="S7Comm",
            event_type="CPU Control Stop",
            payload_summary="CPU STOP Command sent to Siemens S7-1500 Controller (0x29)",
            severity="Critical",
            device_id=eng_ws.id,
            asset_id=turbine_plc.id,
            user_id=doe_user.id,
        ),
        Event(
            timestamp=now - timedelta(hours=1, minutes=10),
            source_ip=rogue_laptop.ip_address,
            destination_ip=gateway.ip_address,
            protocol="HTTP",
            event_type="Unauthorized Port Scan",
            payload_summary="Multiple TCP connection attempts on ports 80, 443, 8080, 22",
            severity="Critical",
            device_id=rogue_laptop.id,
            asset_id=gateway.id,
            user_id=None,
        ),
        Event(
            timestamp=now - timedelta(minutes=50),
            source_ip=scada_server.ip_address,
            destination_ip=hmi_station.ip_address,
            protocol="OPC-UA",
            event_type="Telemetry Update",
            payload_summary="Monitored item value changed: ns=2;i=1084 (Turbine Speed = 3000 RPM)",
            severity="Info",
            device_id=None,
            asset_id=scada_server.id,
            user_id=None,
        ),
        Event(
            timestamp=now - timedelta(minutes=40),
            source_ip=operator_ws.ip_address,
            destination_ip=pump_plc.ip_address,
            protocol="Modbus/TCP",
            event_type="Register Write",
            payload_summary="Write Holding Register 40005 = 85 (Target Cooling Pump Flow Rate)",
            severity="Info",
            device_id=operator_ws.id,
            asset_id=pump_plc.id,
            user_id=doe_user.id,
        ),
        Event(
            timestamp=now - timedelta(minutes=15),
            source_ip=operator_ws.ip_address,
            destination_ip=scada_server.ip_address,
            protocol="OPC-UA",
            event_type="Session Created",
            payload_summary="OPC-UA Client Session Created: Endpoint url opc.tcp://192.168.10.10:4840",
            severity="Info",
            device_id=operator_ws.id,
            asset_id=scada_server.id,
            user_id=doe_user.id,
        ),
    ]
    db.add_all(events)
    db.flush()

    # 7. Seed Alerts
    alerts = [
        Alert(
            title="Unauthorized PLC Stop Command",
            description="A CPU Control Stop command (S7Comm) was sent to Turbine PLC 01 from Engineering Workstation 01. This could interrupt turbine operations.",
            severity="Critical",
            status="New",
            category="Command Manipulation",
            asset_id=turbine_plc.id,
            device_id=eng_ws.id,
            user_id=doe_user.id,
            created_at=now - timedelta(hours=1, minutes=30),
        ),
        Alert(
            title="Rogue Device Scanning Gateway",
            description="An unauthorized Kali Linux laptop (IP: 192.168.10.222) was detected scanning ports on the Security Gateway Cisco ISA3000.",
            severity="High",
            status="Investigating",
            category="Intrusion Attempt",
            asset_id=gateway.id,
            device_id=rogue_laptop.id,
            user_id=None,
            created_at=now - timedelta(hours=1, minutes=10),
        ),
        Alert(
            title="Abnormal Operation Timing",
            description="Operator Workstation 01 modified a holding register on Cooling Pump PLC 02 at 03:14 AM, which is outside the active operating schedule.",
            severity="Medium",
            status="Investigating",
            category="Policy Violation",
            asset_id=pump_plc.id,
            device_id=operator_ws.id,
            user_id=doe_user.id,
            created_at=now - timedelta(hours=3),
        ),
    ]
    db.add_all(alerts)
    db.flush()

    # 8. Seed Risk Scores
    risk_scores = [
        RiskScore(
            score=85,
            entity_type="Asset",
            entity_id=turbine_plc.id,
            factors={
                "criticality_factor": "Critical asset",
                "unauthorized_control_attempts": 1,
                "last_event_severity": "Critical",
            },
            last_calculated=now,
        ),
        RiskScore(
            score=95,
            entity_type="Device",
            entity_id=rogue_laptop.id,
            factors={
                "unknown_mac_vendor": True,
                "active_port_scans": 4,
                "quarantined_status": True,
            },
            last_calculated=now,
        ),
        RiskScore(
            score=65,
            entity_type="User",
            entity_id=doe_user.id,
            factors={
                "unauthorized_time_activity": 1,
                "critical_actions_performed": 1,
            },
            last_calculated=now,
        ),
        RiskScore(
            score=35,
            entity_type="Asset",
            entity_id=pump_plc.id,
            factors={"out_of_hours_write": 1},
            last_calculated=now,
        ),
        RiskScore(
            score=20,
            entity_type="Device",
            entity_id=operator_ws.id,
            factors={"active_sessions": 2},
            last_calculated=now,
        ),
    ]
    db.add_all(risk_scores)
    db.flush()

    # 9. Seed Audit Logs
    audit_logs = [
        AuditLog(
            timestamp=now - timedelta(hours=1),
            action="Quarantined Device",
            ip_address="192.168.10.100",
            details="Rogue device (MAC: 00:1A:2B:4D:5E:8B) placed in quarantined subnet.",
            user_id=admin_user.id,
        ),
        AuditLog(
            timestamp=now - timedelta(minutes=45),
            action="Updated Alert Status",
            ip_address="192.168.10.110",
            details="Alert status for 'Rogue Device Scanning Gateway' updated from New to Investigating.",
            user_id=smith_user.id,
        ),
    ]
    db.add_all(audit_logs)
    
    db.commit()
    logger.info("Initial seeding of database completed successfully.")
