import unittest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.event import Event
from app.models.device import Device
from app.models.user import User
from app.models.alert import Alert
from app.models.asset import IndustrialAsset
from app.core.config_manager import system_config
from app.services.detection_engine.advanced_rules import (
    check_impossible_travel,
    check_device_spoofing,
    check_credential_stuffing,
    check_low_slow_exfiltration,
    check_insider_drift,
    haversine_distance
)

class TestHoneywellRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure in-memory SQLite engine
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        
        # Configure test defaults on system_config
        system_config.impossible_travel_threshold = 800.0
        system_config.fingerprint_sensitivity = 0.5
        system_config.credential_stuffing_window = 60
        system_config.exfiltration_detection_window = 3600
        system_config.cold_start_observation_count = 5
        system_config.drift_sensitivity = 0.5

        # Create baseline entities
        self.user_id = uuid.uuid4()
        self.user = User(
            id=self.user_id,
            username="test_user",
            email="test_user@aegisone.local",
            full_name="Test User",
            role="Operator",
            is_active=True,
            working_hours_start="08:00",
            working_hours_end="17:00",
            country="Germany",
            city="Munich",
            latitude=48.1351,
            longitude=11.5820,
            timezone="Europe/Berlin"
        )
        self.db.add(self.user)

        self.device_id = uuid.uuid4()
        self.device = Device(
            id=self.device_id,
            hostname="op-ws-test.aegisone.local",
            ip_address="192.168.10.150",
            mac_address="00:1A:2B:3C:4D:5E",
            os_version="Windows 10",
            device_type="Operator Station",
            status="Authorized",
            device_model="Dell OptiPlex",
            browser_fingerprint="browser-1234-chrome",
            tls_cert_id="tls-99999-sha256",
            protocol="HTTP",
            firmware_version="v1.0"
        )
        self.db.add(self.device)

        self.asset_id = uuid.uuid4()
        self.asset = IndustrialAsset(
            id=self.asset_id,
            name="Test PLC 01",
            ip_address="192.168.20.15",
            mac_address="AA:BB:CC:DD:EE:01",
            vendor="Siemens",
            model="S7-1500",
            asset_type="PLC",
            location="Zone A",
            criticality="High",
            status="Operational"
        )
        self.db.add(self.asset)
        
        self.db.commit()

    def tearDown(self):
        self.db.query(Alert).delete()
        self.db.query(Event).delete()
        self.db.query(User).delete()
        self.db.query(Device).delete()
        self.db.query(IndustrialAsset).delete()
        self.db.commit()
        self.db.close()

    def test_haversine_distance(self):
        # Distance between Munich and Paris (~684 km)
        dist = haversine_distance(48.1351, 11.5820, 48.8566, 2.3522)
        self.assertAlmostEqual(dist, 684.0, delta=15.0)

    def test_check_impossible_travel_triggers(self):
        base_time = datetime.utcnow()
        
        # Event 1: Munich, Germany
        e1 = Event(
            id=uuid.uuid4(),
            timestamp=base_time - timedelta(minutes=10),
            source_ip="192.168.10.150",
            destination_ip="192.168.20.15",
            protocol="HTTP",
            event_type="User Login",
            payload_summary="Successful authentication",
            severity="Info",
            user_id=self.user_id,
            latitude=48.1351,
            longitude=11.5820,
            country="Germany",
            city="Munich"
        )
        self.db.add(e1)
        self.db.commit()

        # Event 2: Houston, USA (~8200 km away) 10 minutes later (speed = ~49000 km/h)
        e2 = Event(
            id=uuid.uuid4(),
            timestamp=base_time,
            source_ip="192.168.10.150",
            destination_ip="192.168.20.15",
            protocol="HTTP",
            event_type="User Login",
            payload_summary="Successful authentication",
            severity="Info",
            user_id=self.user_id,
            latitude=29.7604,
            longitude=-95.3698,
            country="USA",
            city="Houston"
        )
        self.db.add(e2)
        self.db.commit()

        # Run travel speed checker
        alert = check_impossible_travel(self.db, e2)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.anomaly_classification, "Impossible Travel")
        self.assertIn("Impossible Travel", alert.title)
        self.assertIn("test_user", alert.description)

    def test_check_device_spoofing_triggers(self):
        # Event with mismatched MAC, OS version, and browser fingerprint
        e = Event(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            source_ip="192.168.10.150",
            destination_ip="192.168.20.15",
            protocol="HTTP",
            event_type="PLC Configuration",
            payload_summary="Config update",
            severity="Info",
            device_id=self.device_id,
            mac_address="AA:BB:CC:DD:EE:02",  # mismatch (baseline: 00:1A:2B:3C:4D:5E)
            os_version="Linux Ubuntu",        # mismatch (baseline: Windows 10)
            browser_fingerprint="browser-fake-firefox" # mismatch
        )
        self.db.add(e)
        self.db.commit()

        alert = check_device_spoofing(self.db, e)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.anomaly_classification, "Device Spoofing")
        self.assertIn("mismatches=3/3", alert.description)

    def test_check_credential_stuffing_triggers(self):
        # Generate 6 failed login attempts for 6 different users from the same IP within 10 seconds
        base_time = datetime.utcnow()
        ip_source = "192.168.1.100"
        
        for i in range(6):
            target_user = User(
                id=uuid.uuid4(),
                username=f"stuff_user_{i}",
                email=f"stuff_user_{i}@aegisone.local",
                full_name=f"Stuff User {i}",
                role="Operator",
                is_active=True
            )
            self.db.add(target_user)
            self.db.flush()

            e = Event(
                id=uuid.uuid4(),
                timestamp=base_time - timedelta(seconds=10 - i),
                source_ip=ip_source,
                destination_ip="192.168.10.10",
                protocol="HTTPS",
                event_type="Failed Login",
                payload_summary="Failed login attempt: Mismatched credentials",
                severity="Warning",
                user_id=target_user.id
            )
            self.db.add(e)
        
        self.db.commit()

        # Trigger check on the final failed login event
        alert = check_credential_stuffing(self.db, e)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.anomaly_classification, "Credential Stuffing")
        self.assertIn("Credential Stuffing: Attack Sweep", alert.title)

    def test_check_low_slow_exfiltration_triggers(self):
        base_time = datetime.utcnow()
        ip_source = "192.168.1.150"
        
        # Insert 4 events, each carrying 30 KB chunks (total 120 KB, exceeds 100 KB threshold)
        events = []
        for i in range(4):
            e = Event(
                id=uuid.uuid4(),
                timestamp=base_time - timedelta(minutes=5 * i),
                source_ip=ip_source,
                destination_ip="192.168.20.100",
                protocol="HTTPS",
                event_type="Database Sync",
                payload_summary="Outbound database synchronization sequence: 30 KB transmitted",
                severity="Info"
            )
            self.db.add(e)
            events.append(e)
        
        self.db.commit()

        # Run on the latest event (index 0, at base_time)
        alert = check_low_slow_exfiltration(self.db, events[0])
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.anomaly_classification, "Low-and-Slow Exfiltration")
        self.assertIn("122880 bytes", alert.description)  # 120 KB in bytes

    def test_check_insider_drift_triggers(self):
        base_time = datetime.utcnow()
        
        # Inject 10 normal historical events to pass the cold start observation window (threshold 5)
        for i in range(10):
            e = Event(
                id=uuid.uuid4(),
                timestamp=base_time - timedelta(hours=i + 1),
                source_ip="192.168.10.150",
                destination_ip="192.168.20.15",
                protocol="S7Comm",
                event_type="PLC Read",
                payload_summary="Read CPU state",
                severity="Info",
                user_id=self.user_id,
                asset_id=self.asset_id
            )
            self.db.add(e)
        self.db.commit()

        # Trigger event marked with "Insider Drift" ground truth label
        trigger_event = Event(
            id=uuid.uuid4(),
            timestamp=base_time,
            source_ip="192.168.10.150",
            destination_ip="192.168.20.15",
            protocol="S7Comm",
            event_type="PLC Write",
            payload_summary="Write DB config",
            severity="Warning",
            user_id=self.user_id,
            asset_id=self.asset_id,
            ground_truth_label="Insider Drift"
        )
        self.db.add(trigger_event)
        self.db.commit()

        alert = check_insider_drift(self.db, trigger_event)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.anomaly_classification, "Insider Drift")
        self.assertIn("Insider Behavioral Drift", alert.title)

if __name__ == "__main__":
    unittest.main()
