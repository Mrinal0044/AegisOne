import asyncio
import logging
import random
import uuid
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, text
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.department import Department
from app.models.user import User
from app.models.device import Device
from app.models.asset import IndustrialAsset
from app.models.profile import BehaviorProfile
from app.models.event import Event
from app.models.simulation import SimulationConfig, SimulationState
from app.repositories.simulation import simulation_config_repo, simulation_state_repo

logger = logging.getLogger("app.services.simulation_engine")


class SimulationEngine:
    _instance: Optional["SimulationEngine"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SimulationEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._virtual_start_time: Optional[datetime] = None
        self._real_start_time: Optional[datetime] = None
        self._accumulated_real_time: timedelta = timedelta()

        # Cached mappings for speed
        self._cached_employees: List[Dict[str, Any]] = []
        self._cached_assets: List[uuid.UUID] = []
        self._cached_devices: List[uuid.UUID] = []

    async def initialize_twin(self, db: Session, num_employees: int, num_devices: int) -> None:
        """Sets up the simulated organization structure if it does not already exist."""
        logger.info("Initializing industrial digital twin configuration...")

        # 1. Departments
        dept_names = [
            ("Production", "PRD"),
            ("Quality Assurance", "QA"),
            ("Maintenance", "MNT"),
            ("Operations", "OPS"),
            ("Logistics", "LOG"),
            ("Engineering", "ENG"),
            ("IT", "IT"),
            ("HR", "HR"),
            ("Finance", "FIN"),
            ("Administration", "ADM")
        ]
        
        depts = []
        for name, code in dept_names:
            stmt = select(Department).where(Department.name == name)
            dept = db.execute(stmt).scalar_one_or_none()
            if not dept:
                dept = Department(name=name, code=code)
                db.add(dept)
                db.flush()
            depts.append(dept)
        
        # 2. Industrial Assets
        asset_templates = [
            ("Production Line A", "PLC", "Production", "Siemens", "S7-1500", "Zone A"),
            ("Production Line B", "PLC", "Production", "Rockwell", "ControlLogix", "Zone B"),
            ("Steam Boiler 01", "PLC", "Operations", "Honeywell", "BoilerMax", "Utilities"),
            ("Conveyor Belt C", "PLC", "Logistics", "Schneider", "Modicon M580", "Warehouse"),
            ("Packaging Unit 02", "PLC", "Logistics", "Siemens", "S7-1200", "Warehouse"),
            ("Chemical Mixing Unit", "PLC", "Production", "Schneider", "Quantum", "Zone A"),
            ("Fuel Storage Tank 5", "RTU", "Operations", "Emerson", "FloBoss", "Tank Farm"),
            ("Cooling Tower System", "PLC", "Operations", "Siemens", "S7-1500", "Utilities"),
            ("Water Pump Station", "RTU", "Maintenance", "Schneider", "ScadaPack", "Utilities"),
            ("Assembling Robotic Arm", "PLC", "Engineering", "FANUC", "R-2000iC", "Zone B")
        ]

        assets = []
        for name, a_type, dept_name, vendor, model, loc in asset_templates:
            stmt = select(IndustrialAsset).where(IndustrialAsset.name == name)
            asset = db.execute(stmt).scalar_one_or_none()
            if not asset:
                ip = f"192.168.20.{random.randint(10, 99)}"
                mac = ":".join(["{:02x}".format(random.randint(0, 255)) for _ in range(6)]).upper()
                
                # Setup realistic initial operational telemetry values
                telemetry = {
                    "temperature": round(random.uniform(50.0, 90.0), 2),
                    "pressure": round(random.uniform(2.0, 8.0), 2),
                    "rpm": random.randint(1000, 3000),
                    "flow_rate": round(random.uniform(10.0, 50.0), 2),
                    "status": "running"
                }
                
                asset = IndustrialAsset(
                    name=name,
                    ip_address=ip,
                    mac_address=mac,
                    vendor=vendor,
                    model=model,
                    asset_type=a_type,
                    location=loc,
                    criticality="Critical" if "Line" in name or "Boiler" in name else "High",
                    status="Operational",
                    operational_state=telemetry
                )
                db.add(asset)
            assets.append(asset)
        db.flush()

        # 3. Devices
        device_types = [
            ("Office PC", "Corporate", "Windows 11"),
            ("Laptop", "Corporate", "Windows 11"),
            ("Engineering Workstation", "OT-Control", "Windows 10 IoT"),
            ("HMI Station", "OT-Control", "Windows 10 IoT"),
            ("SCADA Server", "OT-Control", "Windows Server 2022"),
            ("Historian Server", "OT-Control", "Windows Server 2022"),
            ("Industrial Gateway", "DMZ", "Linux Embedded"),
            ("IoT Sensor Node", "OT-Field", "FreeRTOS"),
            ("CCTV IP Camera", "Corporate", "Linux Embedded"),
            ("RFID Badge Reader", "Corporate", "Linux Embedded")
        ]

        # Generate devices
        existing_devices = list(db.execute(select(Device)).scalars().all())
        if len(existing_devices) < num_devices:
            needed = num_devices - len(existing_devices)
            for i in range(needed):
                d_type, zone, os_ver = random.choice(device_types)
                dev_id = f"DEV-{random.randint(1000, 9999)}"
                hostname = f"{d_type.replace(' ', '-').lower()}-{i:02d}.aegisone.local"
                ip = f"192.168.10.{random.randint(10, 250)}"
                mac = ":".join(["{:02x}".format(random.randint(0, 255)) for _ in range(6)]).upper()
                
                device = Device(
                    hostname=hostname,
                    ip_address=ip,
                    mac_address=mac,
                    os_version=os_ver,
                    device_type=d_type,
                    status="Authorized",
                    device_id=dev_id,
                    network_zone=zone,
                    operating_status="Active",
                    firmware_version=f"v{random.randint(1, 4)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                    device_model=random.choice(["Dell OptiPlex", "HP EliteDesk", "ThinkCentre M70", "Siemens IPC427E"]),
                    browser_fingerprint=f"browser-{random.randint(1000, 9999)}-chrome",
                    tls_cert_id=f"tls-{random.randint(10000, 99999)}-sha256",
                    protocol=random.choice(["HTTP", "HTTPS", "SSH", "RDP"])
                )
                db.add(device)
            db.flush()

        # 4. Users (Employees)
        role_templates = [
            ("Plant Manager", "Administration", "Level 5"),
            ("Production Engineer", "Production", "Level 3"),
            ("PLC Engineer", "Engineering", "Level 4"),
            ("Maintenance Technician", "Maintenance", "Level 3"),
            ("SCADA Operator", "Operations", "Level 3"),
            ("Quality Engineer", "Quality Assurance", "Level 3"),
            ("Warehouse Operator", "Logistics", "Level 2"),
            ("HR Executive", "HR", "Level 2"),
            ("Finance Analyst", "Finance", "Level 2"),
            ("IT Administrator", "IT", "Level 5"),
            ("Security Analyst", "IT", "Level 4")
        ]

        existing_users = list(db.execute(select(User)).scalars().all())
        if len(existing_users) < num_employees:
            needed = num_employees - len(existing_users)
            
            # Simple list of mock names
            first_names = ["Robert", "Linda", "James", "Patricia", "Michael", "Elizabeth", "William", "Barbara", "David", "Jennifer"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
            
            shifts = ["Morning", "Afternoon", "Night"]
            
            # Let's find some managers
            mgr_stmt = select(User).where(User.role == "Plant Manager")
            plant_manager = db.execute(mgr_stmt).scalars().first()

            for i in range(needed):
                first = random.choice(first_names)
                last = random.choice(last_names)
                full_name = f"{first} {last}"
                username = f"{first[0].lower()}.{last.lower()}{random.randint(10, 99)}"
                email = f"{username}@aegisone.local"
                
                role, dept_name, access = random.choice(role_templates)
                dept_stmt = select(Department).where(Department.name == dept_name)
                dept = db.execute(dept_stmt).scalars().first()
                
                emp_id = f"EMP-{random.randint(10000, 99999)}"
                shift = random.choice(shifts)
                
                # Shift working hour mappings
                if shift == "Morning":
                    start, end = "06:00", "14:00"
                elif shift == "Afternoon":
                    start, end = "14:00", "22:00"
                else:
                    start, end = "22:00", "06:00"
                
                loc = random.choice([
                    ("Germany", "Munich", 48.1351, 11.5820, "Europe/Berlin"),
                    ("USA", "Houston", 29.7604, -95.3698, "America/Chicago"),
                    ("France", "Paris", 48.8566, 2.3522, "Europe/Paris"),
                    ("Singapore", "Singapore", 1.3521, 103.8198, "Asia/Singapore")
                ])
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    role=role,
                    is_active=True,
                    department_id=dept.id if dept else None,
                    employee_id=emp_id,
                    shift=shift,
                    access_level=access,
                    working_hours_start=start,
                    working_hours_end=end,
                    manager_id=plant_manager.id if plant_manager else None,
                    country=loc[0],
                    city=loc[1],
                    latitude=loc[2],
                    longitude=loc[3],
                    timezone=loc[4]
                )
                db.add(user)
                db.flush()
                
                # Check for Plant Manager creation
                if role == "Plant Manager" and not plant_manager:
                    plant_manager = user
                
                # 5. Create Behavior Profile for User
                # Determine apps & assets they interact with
                user_assets = [a.id for a in assets if a.location == "Utilities"] if role in ["Maintenance Technician", "PLC Engineer"] else [a.id for a in assets]
                user_devices = list(db.execute(select(Device.hostname)).scalars().all())
                
                normal_apps = ["Outlook", "Slack", "Chrome"]
                if role == "PLC Engineer":
                    normal_apps.extend(["Siemens TIA Portal", "Schneider EcoStruxure"])
                elif role == "SCADA Operator":
                    normal_apps.extend(["Honeywell Experion Console", "Ignition SCADA Client"])
                elif role == "IT Administrator":
                    normal_apps.extend(["PowerShell", "Active Directory Admin", "VNC Viewer"])
                
                profile = BehaviorProfile(
                    name=f"Profile_{username}",
                    entity_type="User",
                    user_id=user.id,
                    working_schedule={"days": [0, 1, 2, 3, 4], "shift": shift},
                    login_time=start,
                    logout_time=end,
                    avg_session_duration=28000,
                    normal_devices={"hostnames": random.sample(user_devices, min(2, len(user_devices)))},
                    typical_apps={"apps": normal_apps},
                    normal_assets={"asset_ids": [str(uid) for uid in random.sample([a.id for a in assets], min(3, len(assets)))]},
                    network_frequency=random.uniform(5.0, 15.0),
                    avg_event_volume=random.randint(30, 80),
                    command_patterns={"actions": ["Read Sensor", "Acknowledge Alarm"] + (["Write Register", "Upload Firmware"] if role in ["PLC Engineer", "SCADA Operator"] else [])}
                )
                db.add(profile)
            db.flush()
        db.commit()

    async def start(self) -> None:
        async with self._lock:
            db = SessionLocal()
            try:
                state = simulation_state_repo.get_current(db)
                if state.status == "RUNNING":
                    logger.info("Simulation is already running.")
                    return
                
                config = simulation_config_repo.get_active(db)
                await self.initialize_twin(db, config.num_employees, config.num_devices)
                
                # Cache user objects to avoid heavy database queries in the hot loop
                users = db.execute(select(User).where(User.employee_id.isnot(None))).scalars().all()
                self._cached_employees = []
                for u in users:
                    prof = db.execute(select(BehaviorProfile).where(BehaviorProfile.user_id == u.id)).scalars().first()
                    self._cached_employees.append({
                        "id": u.id,
                        "username": u.username,
                        "role": u.role,
                        "shift": u.shift,
                        "dept_id": u.department_id,
                        "dept_code": u.department.code if u.department else "GEN",
                        "start_time": u.working_hours_start,
                        "end_time": u.working_hours_end,
                        "profile": {
                            "apps": prof.typical_apps.get("apps", []) if prof else [],
                            "devices": prof.normal_devices.get("hostnames", []) if prof else [],
                            "assets": prof.normal_assets.get("asset_ids", []) if prof else [],
                            "commands": prof.command_patterns.get("actions", []) if prof else []
                        }
                    })
                
                self._cached_assets = [a.id for a in db.execute(select(IndustrialAsset)).scalars().all()]
                self._cached_devices = [d.id for d in db.execute(select(Device)).scalars().all()]

                # Initialize virtual time
                self._real_start_time = datetime.now()
                self._virtual_start_time = datetime.now() - timedelta(hours=12)  # offset to make shifts active
                
                state.status = "RUNNING"
                state.started_at = datetime.now()
                db.add(state)
                db.commit()
                
                self._task = asyncio.create_task(self._run_loop())
                logger.info("Simulation engine started successfully in background.")
            finally:
                db.close()

    async def pause(self) -> None:
        async with self._lock:
            db = SessionLocal()
            try:
                state = simulation_state_repo.get_current(db)
                if state.status != "RUNNING":
                    logger.info("Cannot pause simulation that is not running.")
                    return
                
                state.status = "PAUSED"
                state.paused_at = datetime.now()
                db.add(state)
                db.commit()
                
                if self._task:
                    self._task.cancel()
                    self._task = None
                
                # Save timing state
                if self._real_start_time:
                    self._accumulated_real_time += (datetime.now() - self._real_start_time)
                
                logger.info("Simulation engine paused successfully.")
            finally:
                db.close()

    async def resume(self) -> None:
        async with self._lock:
            db = SessionLocal()
            try:
                state = simulation_state_repo.get_current(db)
                if state.status != "PAUSED":
                    logger.info("Cannot resume simulation that is not paused.")
                    return
                
                state.status = "RUNNING"
                db.add(state)
                db.commit()
                
                self._real_start_time = datetime.now()
                self._task = asyncio.create_task(self._run_loop())
                logger.info("Simulation engine resumed successfully.")
            finally:
                db.close()

    async def stop(self) -> None:
        async with self._lock:
            db = SessionLocal()
            try:
                state = simulation_state_repo.get_current(db)
                if state.status in ["IDLE", "STOPPED"]:
                    logger.info("Simulation engine is already stopped.")
                    return
                
                state.status = "STOPPED"
                db.add(state)
                db.commit()
                
                if self._task:
                    self._task.cancel()
                    self._task = None
                
                self._virtual_start_time = None
                self._real_start_time = None
                self._accumulated_real_time = timedelta()
                
                logger.info("Simulation engine stopped successfully.")
            finally:
                db.close()

    async def reset(self) -> None:
        await self.stop()
        db = SessionLocal()
        try:
            logger.info("Resetting simulation state and clearing generated events...")
            # Truncate events, risk scores, alerts
            db.execute(text("TRUNCATE TABLE events, alerts, risk_scores, audit_logs CASCADE"))
            
            state = simulation_state_repo.get_current(db)
            state.status = "IDLE"
            state.total_events_generated = 0
            state.started_at = None
            state.paused_at = None
            db.add(state)
            
            db.commit()
            logger.info("Simulation reset completed.")
        except Exception as e:
            logger.error(f"Error resetting simulation: {str(e)}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    def get_virtual_time(self, speed_multiplier: float) -> datetime:
        if not self._virtual_start_time or not self._real_start_time:
            return datetime.now()
        
        real_elapsed = datetime.now() - self._real_start_time + self._accumulated_real_time
        virtual_elapsed = real_elapsed * speed_multiplier
        return self._virtual_start_time + virtual_elapsed

    async def _run_loop(self) -> None:
        """Main simulation execution loop stepping through ticks and writing logs."""
        try:
            logger.info("Simulation loop task initiated.")
            while True:
                db = SessionLocal()
                try:
                    state = simulation_state_repo.get_current(db)
                    if state.status != "RUNNING":
                        break
                    
                    config = simulation_config_repo.get_active(db)
                    speed = config.speed_multiplier
                    rate = config.event_rate
                    
                    # Virtual time clock calculation
                    v_now = self.get_virtual_time(speed)
                    v_time_str = v_now.strftime("%H:%M:%S")
                    
                    # 1. Update physical asset telemetry fields dynamically (simulation variables)
                    created_event_ids = []
                    assets = list(db.execute(select(IndustrialAsset)).scalars().all())
                    for asset in assets:
                        state_data = dict(asset.operational_state)
                        # Add slight noise fluctuations
                        if "temperature" in state_data:
                            state_data["temperature"] = round(state_data["temperature"] + random.uniform(-0.5, 0.5), 2)
                        if "pressure" in state_data:
                            state_data["pressure"] = round(max(1.0, state_data["pressure"] + random.uniform(-0.1, 0.1)), 2)
                        asset.operational_state = state_data
                        db.add(asset)
                    db.flush()

                    # 2. Probability step: Trigger actions for employees active in the current shift
                    v_hour = v_now.hour
                    
                    # Loop employees
                    for emp in self._cached_employees:
                        # Determine if employee is in their shift
                        in_shift = False
                        start_h, start_m = map(int, emp["start_time"].split(":"))
                        end_h, end_m = map(int, emp["end_time"].split(":"))
                        
                        # Handle overnight night-shift
                        if start_h > end_h:
                            if v_hour >= start_h or v_hour < end_h:
                                in_shift = True
                        else:
                            if start_h <= v_hour < end_h:
                                in_shift = True
                        
                        if not in_shift:
                            continue
                        
                        # Probabilistic check for event generation (weighted by event rate)
                        # Scale probability by speed multiplier to ensure rate matches virtual progress
                        probability_scale = 0.05 * (speed / 10.0)
                        if random.random() < min(0.9, probability_scale):
                            # Employee performs an action
                            action = random.choice(emp["profile"]["commands"])
                            dev_name = random.choice(emp["profile"]["devices"]) if emp["profile"]["devices"] else "op-ws-01.aegisone.local"
                            asset_id = uuid.UUID(random.choice(emp["profile"]["assets"])) if emp["profile"]["assets"] else random.choice(self._cached_assets)
                            
                            # Resolve target device
                            dev_stmt = select(Device).where(Device.hostname == dev_name)
                            device = db.execute(dev_stmt).scalars().first()

                            # Resolve target user
                            emp_user = db.get(User, emp["id"])
                            user_country = emp_user.country if emp_user else "Germany"
                            user_city = emp_user.city if emp_user else "Munich"
                            user_lat = emp_user.latitude if emp_user else 48.1351
                            user_lon = emp_user.longitude if emp_user else 11.5820
                            user_tz = emp_user.timezone if emp_user else "Europe/Berlin"

                            # Construct the event
                            event = Event(
                                timestamp=v_now,
                                source_ip=device.ip_address if device else "192.168.10.50",
                                destination_ip=f"192.168.20.{random.randint(10,99)}",
                                protocol=random.choice(["Modbus/TCP", "S7Comm", "OPC-UA", "HTTP"]),
                                event_type=action,
                                payload_summary=f"Operation '{action}' executed by employee {emp['username']} via terminal {dev_name}",
                                severity="Info" if "Read" in action else "Warning",
                                device_id=device.id if device else None,
                                asset_id=asset_id,
                                user_id=emp["id"],
                                country=user_country,
                                city=user_city,
                                latitude=user_lat,
                                longitude=user_lon,
                                timezone=user_tz,
                                auth_method="Kerberos",
                                device_model=device.device_model if device else "Siemens IPC427E",
                                browser_fingerprint=device.browser_fingerprint if device else "browser-9812-chrome",
                                tls_cert_id=device.tls_cert_id if device else "tls-81726-sha256",
                                os_version=device.os_version if device else "Windows 10 IoT",
                                firmware_version=device.firmware_version if device else "v1.0.0",
                                mac_address=device.mac_address if device else "00:11:22:33:44:55",
                                session_duration=random.randint(1200, 7200),
                                resource_accessed=random.choice(["PLC_Config", "Historian_Table", "Modbus_Registers"]),
                                ground_truth_label="Normal"
                            )
                            db.add(event)
                            db.flush()
                            created_event_ids.append(event.id)
                            state.total_events_generated += 1
                    
                    # 3. Autonomous sensor telemetry events (always active)
                    if random.random() < 0.3:
                        asset_id = random.choice(self._cached_assets)
                        ast = db.execute(select(IndustrialAsset).where(IndustrialAsset.id == asset_id)).scalar_one_or_none()
                        
                        if ast:
                            if ast.operational_state:
                                key = list(ast.operational_state.keys())[0]
                                val = ast.operational_state[key]
                                payload_text = f"OPC-UA node update: {key} = {val}"
                            else:
                                payload_text = f"OPC-UA node update: status = {ast.status}"

                            event = Event(
                                timestamp=v_now,
                                source_ip=ast.ip_address,
                                destination_ip="192.168.10.10", # SCADA
                                protocol="OPC-UA",
                                event_type="Sensor Telemetry Push",
                                payload_summary=payload_text,
                                severity="Info",
                                asset_id=ast.id
                            )
                            db.add(event)
                            db.flush()
                            created_event_ids.append(event.id)
                            state.total_events_generated += 1
                    
                    db.add(state)
                    db.commit()

                    # Push to behavioral pipeline
                    from app.services.behavior_engine.behavior_pipeline import behavior_pipeline
                    for eid in created_event_ids:
                        behavior_pipeline.enqueue_event(eid)
                except Exception as e:
                    logger.error(f"Error inside simulation loop step: {str(e)}", exc_info=True)
                    db.rollback()
                finally:
                    db.close()
                
                # Sleep based on configure rate (higher rate -> shorter sleep)
                sleep_sec = max(0.1, 1.0 / rate)
                await asyncio.sleep(sleep_sec)
        except asyncio.CancelledError:
            logger.info("Simulation loop task was cancelled.")
        except Exception as e:
            logger.error(f"Fatal error in simulation background task: {str(e)}", exc_info=True)


simulation_engine = SimulationEngine()
