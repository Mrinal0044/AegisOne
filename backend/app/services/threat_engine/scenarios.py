import uuid
import random
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.device import Device
from app.models.asset import IndustrialAsset
from app.services.threat_engine.interfaces import ThreatScenario


class TargetResolver:
    @staticmethod
    def resolve_targets(
        db: Session,
        user_id: Optional[uuid.UUID],
        device_id: Optional[uuid.UUID],
        asset_id: Optional[uuid.UUID]
    ) -> Dict[str, Any]:
        """Resolves target database models, falling back to random records if none provided."""
        user = None
        if user_id:
            user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            user = db.execute(select(User)).scalars().first()

        device = None
        if device_id:
            device = db.execute(select(Device).where(Device.id == device_id)).scalar_one_or_none()
        if not device:
            device = db.execute(select(Device)).scalars().first()

        asset = None
        if asset_id:
            asset = db.execute(select(IndustrialAsset).where(IndustrialAsset.id == asset_id)).scalar_one_or_none()
        if not asset:
            asset = db.execute(select(IndustrialAsset)).scalars().first()

        return {"user": user, "device": device, "asset": asset}


class InsiderThreatScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "insider_threat"

    @property
    def name(self) -> str:
        return "Insider Threat: Rogue Operator"

    @property
    def description(self) -> str:
        return (
            "An employee logs in outside standard shift working hours from an unauthorized device "
            "and department, downloads PLC engineering files, and attempts to modify control parameters."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d, ast = targets["user"], targets["device"], targets["asset"]

        username = u.username if u else "j.doe"
        user_id = u.id if u else None
        dev_hostname = d.hostname if d else "op-ws-01.aegisone.local"
        dev_ip = d.ip_address if d else "192.168.10.110"
        dev_id = d.id if d else None
        asset_ip = ast.ip_address if ast else "192.168.10.50"
        asset_name = ast.name if ast else "Turbine PLC 01"
        asset_id = ast.id if ast else None

        return [
            {
                "name": "Out-of-Hours Login Attempt",
                "event_type": "User Login",
                "protocol": "HTTP",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.10", # AD Server
                "payload_summary": f"Login succeeded for user {username} outside shift hours",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Access Unauthorized Department Network",
                "event_type": "SCADA Access",
                "protocol": "TCP",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.20", # SCADA Gateway
                "payload_summary": f"Unusual SCADA session initialized by employee {username} from Finance Host",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Unauthorized Sensitive File Download",
                "event_type": "File Download",
                "protocol": "FTP",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.30", # Historian / File Server
                "payload_summary": f"Downloaded: turbine_control_logic_v4.2.bin (Size: 154 MB)",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Attempt PLC Configuration Change",
                "event_type": "PLC Configuration",
                "protocol": "S7Comm",
                "source_ip": dev_ip,
                "destination_ip": asset_ip,
                "payload_summary": f"Attempted S7comm write parameter block to {asset_name}",
                "severity": "Critical",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": asset_id,
                "delay_seconds": 2.0
            },
            {
                "name": "Logout Session",
                "event_type": "User Logout",
                "protocol": "HTTP",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.10",
                "payload_summary": f"Session closed for user {username}",
                "severity": "Info",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 0.0
            }
        ]


class BruteForceScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "brute_force"

    @property
    def name(self) -> str:
        return "Brute Force Authentication"

    @property
    def description(self) -> str:
        return (
            "A series of rapid failed login attempts targeting an operator console from an external IP, "
            "followed by a successful compromise and privilege escalation query."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d = targets["user"], targets["device"]

        username = u.username if u else "operator_01"
        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.110"
        dev_id = d.id if d else None
        attacker_ip = "10.220.14.88" # External rogue IP

        steps = []
        # 5 failed login attempts in timeline
        for idx in range(5):
            steps.append({
                "name": f"Failed Auth Attempt #{idx+1}",
                "event_type": "Failed Login",
                "protocol": "SSH",
                "source_ip": attacker_ip,
                "destination_ip": dev_ip,
                "payload_summary": f"Login failed for user {username} - Incorrect password block",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 1.0
            })

        # Successful compromise
        steps.append({
            "name": "Successful Login Compromise",
            "event_type": "User Login",
            "protocol": "SSH",
            "source_ip": attacker_ip,
            "destination_ip": dev_ip,
            "payload_summary": f"Login succeeded for user {username} via SSH - Password guessed",
            "severity": "Critical",
            "user_id": user_id,
            "device_id": dev_id,
            "asset_id": None,
            "delay_seconds": 2.0
        })

        # Database queries escalation
        steps.append({
            "name": "Privilege Escalation Access",
            "event_type": "Database Query",
            "protocol": "SQL",
            "source_ip": dev_ip,
            "destination_ip": "192.168.10.30", # Historian DB
            "payload_summary": "Query executed: SELECT * FROM admin_credentials_cache",
            "severity": "Critical",
            "user_id": user_id,
            "device_id": dev_id,
            "asset_id": None,
            "delay_seconds": 0.0
        })

        return steps


class UsbMalwareScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "usb_malware"

    @property
    def name(self) -> str:
        return "USB Malware Injection"

    @property
    def description(self) -> str:
        return (
            "A USB drive is plugged into an engineering workstation. An unknown executable launches "
            "automatically, copies local PLC configuration logic, and writes logic directly to connected assets."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d, ast = targets["user"], targets["device"], targets["asset"]

        username = u.username if u else "eng_01"
        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.120"
        dev_id = d.id if d else None
        asset_ip = ast.ip_address if ast else "192.168.10.50"
        asset_id = ast.id if ast else None

        return [
            {
                "name": "USB Connection Detected",
                "event_type": "USB Connected",
                "protocol": "USB",
                "source_ip": dev_ip,
                "destination_ip": "127.0.0.1",
                "payload_summary": "Removable USB mass storage device connected: HardwareID USB\\VID_0951&PID_1666",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Malicious Executable Launch",
                "event_type": "Engineering Workstation Usage",
                "protocol": "Local",
                "source_ip": dev_ip,
                "destination_ip": "127.0.0.1",
                "payload_summary": "Process started: E:\\autorun.inf -> E:\\payload_installer.exe (Unsigned binary)",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Configuration Logic Backup Copy",
                "event_type": "File Download",
                "protocol": "Local",
                "source_ip": dev_ip,
                "destination_ip": "127.0.0.1",
                "payload_summary": "Copied local directory: C:\\Program Files\\Siemens\\TIA Portal\\Projects\\ -> E:\\Exfil\\",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Direct Unauthorized PLC Connection",
                "event_type": "PLC Access",
                "protocol": "S7Comm",
                "source_ip": dev_ip,
                "destination_ip": asset_ip,
                "payload_summary": "S7comm connection initiated - Handshake initialized bypass operator station",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": asset_id,
                "delay_seconds": 2.0
            },
            {
                "name": "PLC Config Modification",
                "event_type": "PLC Configuration",
                "protocol": "S7Comm",
                "source_ip": dev_ip,
                "destination_ip": asset_ip,
                "payload_summary": f"Uploaded program block DB1 (S7-Logic Write Block) - Mapped logic updated",
                "severity": "Critical",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": asset_id,
                "delay_seconds": 2.0
            },
            {
                "name": "USB Device Ejected",
                "event_type": "USB Removed",
                "protocol": "USB",
                "source_ip": dev_ip,
                "destination_ip": "127.0.0.1",
                "payload_summary": "Removable USB mass storage device disconnected",
                "severity": "Info",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 0.0
            }
        ]


class PlcManipulationScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "plc_manipulation"

    @property
    def name(self) -> str:
        return "PLC Command Manipulation"

    @property
    def description(self) -> str:
        return (
            "Direct network access is established to an operational field PLC, bypassing HMI systems. "
            "The attacker fires rapid command register write bursts, altering physical pump/boiler settings."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d, ast = targets["user"], targets["device"], targets["asset"]

        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.110"
        dev_id = d.id if d else None
        asset_ip = ast.ip_address if ast else "192.168.10.52"
        asset_id = ast.id if ast else None
        asset_name = ast.name if ast else "Cooling Pump PLC 02"

        steps = [
            {
                "name": "Direct Modbus Connection Established",
                "event_type": "PLC Access",
                "protocol": "Modbus/TCP",
                "source_ip": dev_ip,
                "destination_ip": asset_ip,
                "payload_summary": "Modbus/TCP Connection initialized on port 502",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": asset_id,
                "delay_seconds": 1.5
            }
        ]

        # Multi-command burst writes registers
        for reg in range(40001, 40005):
            steps.append({
                "name": f"Modify Register {reg}",
                "event_type": "PLC Configuration",
                "protocol": "Modbus/TCP",
                "source_ip": dev_ip,
                "destination_ip": asset_ip,
                "payload_summary": f"Modbus command Write Single Register {reg} = {random.randint(100, 500)} (Override flow limit)",
                "severity": "Critical",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": asset_id,
                "delay_seconds": 1.0
            })

        steps.append({
            "name": "Modbus Session Terminated",
            "event_type": "PLC Access",
            "protocol": "Modbus/TCP",
            "source_ip": dev_ip,
            "destination_ip": asset_ip,
            "payload_summary": "TCP Connection closed port 502",
            "severity": "Info",
            "user_id": user_id,
            "device_id": dev_id,
            "asset_id": asset_id,
            "delay_seconds": 0.0
        })

        return steps


class LateralMovementScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "lateral_movement"

    @property
    def name(self) -> str:
        return "Lateral Movement: Office to OT"

    @property
    def description(self) -> str:
        return (
            "Starting from a compromised corporate office PC, the attacker establishes remote desktop "
            "sessions into the SCADA network and accesses the database servers."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d = targets["user"], targets["device"]

        username = u.username if u else "admin"
        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.110"
        dev_id = d.id if d else None
        office_host = "192.168.40.15" # Corporate PC IP

        return [
            {
                "name": "Compromised Corporate Host Login",
                "event_type": "User Login",
                "protocol": "HTTP",
                "source_ip": office_host,
                "destination_ip": "192.168.10.10", # AD
                "payload_summary": f"Login succeeded for {username} via compromised token on office node",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": None,
                "asset_id": None,
                "delay_seconds": 2.5
            },
            {
                "name": "Pivot: Connect to Engineering Workstation",
                "event_type": "Remote Connection",
                "protocol": "RDP",
                "source_ip": office_host,
                "destination_ip": dev_ip,
                "payload_summary": f"RDP session initiated from corporate IP to {d.hostname if d else 'eng-ws-01'}",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.5
            },
            {
                "name": "SCADA Application Execution",
                "event_type": "SCADA Access",
                "protocol": "TCP",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.20",
                "payload_summary": "Launched SCADA runtime interface console (admin permission)",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.5
            },
            {
                "name": "Access Historian Database",
                "event_type": "Historian Access",
                "protocol": "SQL",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.30",
                "payload_summary": "Connected to PostgreSQL database: dbname=historian_logs",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.5
            },
            {
                "name": "Mass Database Query",
                "event_type": "Database Query",
                "protocol": "SQL",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.30",
                "payload_summary": "Executed query: SELECT * FROM plcs_ip_configuration_registry LIMIT 1000",
                "severity": "Critical",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 0.0
            }
        ]


class RemoteAccessScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "remote_access"

    @property
    def name(self) -> str:
        return "Remote Unauthorized Access"

    @property
    def description(self) -> str:
        return (
            "An external connection is established from an unknown geolocation VPN IP at an abnormal time. "
            "The attacker runs command sweeps across multiple plant PLCs."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d, ast = targets["user"], targets["device"], targets["asset"]

        username = u.username if u else "operator_01"
        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.110"
        dev_id = d.id if d else None
        asset_ip = ast.ip_address if ast else "192.168.10.50"
        asset_id = ast.id if ast else None
        vpn_ip = "185.220.101.44" # TOR exit node IP

        return [
            {
                "name": "VPN Session Tunnel Established",
                "event_type": "Remote Connection",
                "protocol": "OpenVPN",
                "source_ip": vpn_ip,
                "destination_ip": "192.168.10.5", # VPN Gateway
                "payload_summary": "Incoming SSL VPN connection authorized for profile: vendor-remote-access",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": None,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Unexpected Geolocation Login",
                "event_type": "User Login",
                "protocol": "HTTP",
                "source_ip": "192.168.10.5",
                "destination_ip": "192.168.10.10",
                "payload_summary": f"Session opened for {username} via VPN gateway from IP {vpn_ip} (Country: NL)",
                "severity": "Critical",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Sweep Assets: Scan PLC Status",
                "event_type": "Asset Inspection",
                "protocol": "S7Comm",
                "source_ip": dev_ip,
                "destination_ip": asset_ip,
                "payload_summary": "S7comm Read request - Query CPU Diagnostic Buffer Status",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": asset_id,
                "delay_seconds": 2.0
            },
            {
                "name": "Change Asset Parameters",
                "event_type": "Configuration Change",
                "protocol": "S7Comm",
                "source_ip": dev_ip,
                "destination_ip": asset_ip,
                "payload_summary": "S7comm write command - Set PLC operating state to STOP",
                "severity": "Critical",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": asset_id,
                "delay_seconds": 0.0
            }
        ]


class DataExfiltrationScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "data_exfiltration"

    @property
    def name(self) -> str:
        return "Industrial Data Exfiltration"

    @property
    def description(self) -> str:
        return (
            "The attacker connects to database repositories, runs large dumps of asset specifications, "
            "and transmits the files out of the plant network to an external cloud target."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d = targets["user"], targets["device"]

        username = u.username if u else "engineer_01"
        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.120"
        dev_id = d.id if d else None
        external_host = "45.76.104.22" # External dropzone server IP

        return [
            {
                "name": "Connect to Historian Database",
                "event_type": "Historian Access",
                "protocol": "SQL",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.30",
                "payload_summary": f"SQL session opened for user {username} to dump tables",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.0
            },
            {
                "name": "Generate Large Data Dump",
                "event_type": "Database Query",
                "protocol": "SQL",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.30",
                "payload_summary": "Executed query: SELECT * FROM sensor_readings_archive_2025 (Dump size: 450 MB)",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.5
            },
            {
                "name": "Compress Exfiltration Payload",
                "event_type": "File Download",
                "protocol": "Local",
                "source_ip": dev_ip,
                "destination_ip": "127.0.0.1",
                "payload_summary": "Process started: tar -czf dump_exfil.tar.gz /tmp/db_dump/*.csv (Success)",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.5
            },
            {
                "name": "Transmit Data to Dropzone",
                "event_type": "Network Connection",
                "protocol": "HTTPS",
                "source_ip": dev_ip,
                "destination_ip": external_host,
                "payload_summary": f"Exfiltrated payload via HTTPS POST to dropzone: dump_exfil.tar.gz (Size: 320 MB)",
                "severity": "Critical",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 0.0
            }
        ]


class CredentialStuffingScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "credential_stuffing"

    @property
    def name(self) -> str:
        return "Credential Stuffing Sweep"

    @property
    def description(self) -> str:
        return "High-frequency multi-account login failures originating from a single IP, concluding in a successful compromise."

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d, ast = targets["user"], targets["device"], targets["asset"]

        dev_ip = d.ip_address if d else "192.168.10.150"
        dev_id = d.id if d else None
        
        # Load up to 6 other user accounts to stuffing sweep
        users_stmt = select(User).limit(6)
        users = db.execute(users_stmt).scalars().all()
        
        steps = []
        # Generate login failures for each user account
        for idx, usr in enumerate(users):
            steps.append({
                "name": f"Failed authentication for user {usr.username}",
                "event_type": "Failed Login",
                "protocol": "HTTPS",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.10",
                "payload_summary": f"Failed login attempt for user: {usr.username} - Mismatched credentials",
                "severity": "Warning",
                "user_id": usr.id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 1.0,
                # Geolocation and fingerprint properties
                "country": "Ukraine",
                "city": "Kyiv",
                "latitude": 50.4501,
                "longitude": 30.5234,
                "timezone": "Europe/Kyiv",
                "auth_method": "Password",
                "browser_fingerprint": "chrome-windows-12847192",
                "device_model": "ThinkPad T14",
                "os_version": "Windows 11",
                "mac_address": "AA:BB:CC:DD:EE:01",
                "session_duration": 0,
                "ground_truth_label": "Credential Stuffing"
            })
            
        # Add the final successful compromise step
        steps.append({
            "name": f"Successful compromised login for user {u.username if u else 'admin'}",
            "event_type": "User Login",
            "protocol": "HTTPS",
            "source_ip": dev_ip,
            "destination_ip": "192.168.10.10",
            "payload_summary": f"Successful login for user: {u.username if u else 'admin'} from suspicious IP sweep",
            "severity": "Critical",
            "user_id": u.id if u else None,
            "device_id": dev_id,
            "asset_id": None,
            "delay_seconds": 0.0,
            "country": "Ukraine",
            "city": "Kyiv",
            "latitude": 50.4501,
            "longitude": 30.5234,
            "timezone": "Europe/Kyiv",
            "auth_method": "Password",
            "browser_fingerprint": "chrome-windows-12847192",
            "device_model": "ThinkPad T14",
            "os_version": "Windows 11",
            "mac_address": "AA:BB:CC:DD:EE:01",
            "session_duration": 4200,
            "ground_truth_label": "Credential Stuffing"
        })
        
        return steps


class LowAndSlowExfiltrationScenario(ThreatScenario):
    @property
    def scenario_id(self) -> str:
        return "low_slow_exfil"

    @property
    def name(self) -> str:
        return "Low-and-Slow Data Exfiltration"

    @property
    def description(self) -> str:
        return "Simulates small, periodic, off-hours transfers over several days to avoid standard volume threshold alerts."

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d, ast = targets["user"], targets["device"], targets["asset"]

        username = u.username if u else "rogue_engineer"
        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.110"
        dev_id = d.id if d else None
        
        steps = []
        for day in range(1, 6):
            steps.append({
                "name": f"Off-hours database export (Day {day})",
                "event_type": "Database Query",
                "protocol": "SQL",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.30",
                "payload_summary": f"Query executed: SELECT * FROM historian_logs LIMIT {5000 + day * 500} (Success)",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 1.5,
                "session_duration": 300,
                "resource_accessed": "historian_logs",
                "ground_truth_label": "Low-and-Slow Exfiltration"
            })
            steps.append({
                "name": f"Exfiltrate small chunk (Day {day})",
                "event_type": "File Upload",
                "protocol": "HTTPS",
                "source_ip": dev_ip,
                "destination_ip": "8.8.8.8",
                "payload_summary": f"Exfiltrated payload part_{day}.csv (Size: {5 + day} MB)",
                "severity": "Warning",
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": None,
                "delay_seconds": 2.5,
                "session_duration": 45,
                "resource_accessed": f"part_{day}.csv",
                "ground_truth_label": "Low-and-Slow Exfiltration"
            })
            
        return steps


class InsiderDriftScenario(ThreatScenario):
    def __init__(self, suspicious: bool = True):
        self._suspicious = suspicious

    @property
    def scenario_id(self) -> str:
        return "insider_drift_suspicious" if self._suspicious else "insider_drift_legitimate"

    @property
    def name(self) -> str:
        return "Insider Drift: Suspicious Expansion" if self._suspicious else "Insider Drift: Legitimate Expansion"

    @property
    def description(self) -> str:
        return (
            "Suspicious gradual drift in user privileges, department footprint, and PLC accesses."
            if self._suspicious else
            "Legitimate scaling of engineer workloads and assets coverage."
        )

    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        targets = TargetResolver.resolve_targets(db, target_user_id, target_device_id, target_asset_id)
        u, d, ast = targets["user"], targets["device"], targets["asset"]

        username = u.username if u else "drift_engineer"
        user_id = u.id if u else None
        dev_ip = d.ip_address if d else "192.168.10.110"
        dev_id = d.id if d else None
        
        label = "Insider Drift" if self._suspicious else "Normal"
        severity = "Warning" if self._suspicious else "Info"
        
        steps = []
        # Step 1: Login
        steps.append({
            "name": "Establish workstation session",
            "event_type": "User Login",
            "protocol": "Kerberos",
            "source_ip": dev_ip,
            "destination_ip": "192.168.10.10",
            "payload_summary": f"Successful domain logon for {username}",
            "severity": "Info",
            "user_id": user_id,
            "device_id": dev_id,
            "asset_id": None,
            "delay_seconds": 2.0,
            "ground_truth_label": label
        })
        # Step 2: Gradually increase PLC actions (PLC Manipulation / Remote Access)
        for i in range(1, 5):
            steps.append({
                "name": f"Interactive workstation control cycle {i}",
                "event_type": "PLC Write",
                "protocol": "S7Comm",
                "source_ip": dev_ip,
                "destination_ip": "192.168.10.50",
                "payload_summary": f"Sent payload S7Comm command code 0x{i:02x}: Modify controller variable (DB10.DBW2)",
                "severity": severity,
                "user_id": user_id,
                "device_id": dev_id,
                "asset_id": ast.id if ast else None,
                "delay_seconds": 1.5,
                "ground_truth_label": label
            })
            
        return steps
