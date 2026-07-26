import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.event import Event
from app.models.alert import Alert
from app.services.threat_engine.scenario_registry import scenario_registry
from app.services.behavior_engine.behavior_pipeline import behavior_pipeline
from app.services.simulation_engine import simulation_engine

logger = logging.getLogger("app.services.threat_engine.engine")


class ThreatEngine:
    _instance: Optional["ThreatEngine"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ThreatEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        
        # State stores
        self._active_simulations: Dict[str, Dict[str, Any]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._timeline: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def start_scenario(
        self,
        scenario_id: str,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None,
        delay_scale: float = 1.0
    ) -> Dict[str, Any]:
        """Launches a threat scenario in an independent background async task."""
        if scenario_id in self._active_simulations and self._active_simulations[scenario_id]["status"] == "RUNNING":
            raise ValueError(f"Scenario {scenario_id} is already running.")

        scenario = scenario_registry.get(scenario_id)
        if not scenario:
            raise KeyError(f"Threat scenario {scenario_id} not registered.")

        db = SessionLocal()
        try:
            steps = scenario.get_steps(db, target_user_id, target_device_id, target_asset_id)
        finally:
            db.close()

        # Parse target identifiers
        first_step = steps[0]
        t_user = first_step.get("user_id")
        t_device = first_step.get("device_id")
        t_asset = first_step.get("asset_id")

        sim_state = {
            "scenario_id": scenario_id,
            "name": scenario.name,
            "status": "RUNNING",
            "current_step_index": 0,
            "total_steps": len(steps),
            "progress": 0.0,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "target_user_id": t_user,
            "target_device_id": t_device,
            "target_asset_id": t_asset,
            "detected": False,
            "risk_level": "Low"
        }
        self._active_simulations[scenario_id] = sim_state

        # Spawn background runner task
        task = asyncio.create_task(
            self._run_scenario(scenario_id, steps, delay_scale)
        )
        self._tasks[scenario_id] = task

        logger.info(f"Threat Scenario {scenario_id} started in background.")

        # Record threat scenario execution count in metrics_service
        from app.services.metrics_service import metrics_service
        metrics_service.threats_executed += 1

        return sim_state

    def stop_scenario(self, scenario_id: str) -> None:
        """Terminates a running threat scenario simulation."""
        if scenario_id in self._tasks:
            self._tasks[scenario_id].cancel()
            del self._tasks[scenario_id]
            
        if scenario_id in self._active_simulations:
            sim = self._active_simulations[scenario_id]
            if sim["status"] == "RUNNING":
                sim["status"] = "STOPPED"
                sim["ended_at"] = datetime.utcnow().isoformat() + "Z"
                self._history.append(dict(sim))
                
            del self._active_simulations[scenario_id]
            
        logger.info(f"Threat Scenario {scenario_id} stopped.")

    def reset_all(self) -> None:
        """Clears all running attack states, active timelines, and completed histories."""
        for scenario_id in list(self._tasks.keys()):
            self.stop_scenario(scenario_id)
        self._active_simulations.clear()
        self._tasks.clear()
        self._timeline.clear()
        self._history.clear()
        logger.info("Threat Engine states completely reset.")

    async def _run_scenario(self, scenario_id: str, steps: List[Dict[str, Any]], delay_scale: float) -> None:
        """Sequential loop executing attack timeline checkpoints."""
        sim = self._active_simulations[scenario_id]
        try:
            for idx, step in enumerate(steps):
                sim["current_step_index"] = idx + 1
                sim["progress"] = round((idx + 1) / len(steps) * 100.0, 1)

                db = SessionLocal()
                try:
                    # Resolve virtual time from simulation clock
                    from app.repositories.simulation import simulation_config_repo
                    config = simulation_config_repo.get_active(db)
                    v_now = simulation_engine.get_virtual_time(config.speed_multiplier)
                    
                    # Create raw event
                    event = Event(
                        timestamp=v_now,
                        source_ip=step["source_ip"],
                        destination_ip=step["destination_ip"],
                        protocol=step["protocol"],
                        event_type=step["event_type"],
                        payload_summary=step["payload_summary"],
                        severity=step["severity"],
                        user_id=step.get("user_id"),
                        device_id=step.get("device_id"),
                        asset_id=step.get("asset_id"),
                        country=step.get("country"),
                        city=step.get("city"),
                        latitude=step.get("latitude"),
                        longitude=step.get("longitude"),
                        timezone=step.get("timezone"),
                        auth_method=step.get("auth_method"),
                        device_model=step.get("device_model"),
                        browser_fingerprint=step.get("browser_fingerprint"),
                        tls_cert_id=step.get("tls_cert_id"),
                        os_version=step.get("os_version"),
                        firmware_version=step.get("firmware_version"),
                        mac_address=step.get("mac_address"),
                        session_duration=step.get("session_duration"),
                        resource_accessed=step.get("resource_accessed"),
                        ground_truth_label=step.get("ground_truth_label")
                    )
                    db.add(event)
                    db.flush()
                    event_id = event.id
                    db.commit()

                    # Push to behavior pipeline (triggers incremental feature extraction and AI scoring)
                    behavior_pipeline.enqueue_event(event_id)

                    # Log timeline audit check
                    timeline_log = {
                        "id": str(uuid.uuid4()),
                        "timestamp": v_now.isoformat() + "Z",
                        "scenario_id": scenario_id,
                        "scenario_name": sim["name"],
                        "current_step": step["name"],
                        "event_type": step["event_type"],
                        "payload_summary": step["payload_summary"],
                        "severity": step["severity"],
                        "target_user_id": step.get("user_id"),
                        "target_device_id": step.get("device_id"),
                        "target_asset_id": step.get("asset_id")
                    }
                    self._timeline.append(timeline_log)

                    # Publish threat progress update to clients
                    from app.services.sse_manager import sse_manager
                    sse_manager.publish("THREAT_PROGRESS", {
                        "scenario_id": scenario_id,
                        "name": sim["name"],
                        "current_step_index": sim["current_step_index"],
                        "total_steps": sim["total_steps"],
                        "progress": sim["progress"],
                        "status": sim["status"],
                        "timeline_event": timeline_log
                    })
                except Exception as e:
                    logger.error(f"Error executing step {idx} in threat scenario {scenario_id}: {e}", exc_info=True)
                    db.rollback()
                finally:
                    db.close()

                # Sleep before next step
                delay = step.get("delay_seconds", 2.0) * delay_scale
                await asyncio.sleep(max(0.1, delay))

            # Completed
            sim["status"] = "COMPLETED"
            sim["progress"] = 100.0
            sim["ended_at"] = datetime.utcnow().isoformat() + "Z"
            self._history.append(dict(sim))

            from app.services.sse_manager import sse_manager
            sse_manager.publish("THREAT_PROGRESS", {
                "scenario_id": scenario_id,
                "name": sim["name"],
                "current_step_index": sim["current_step_index"],
                "total_steps": sim["total_steps"],
                "progress": 100.0,
                "status": "COMPLETED"
            })
        except asyncio.CancelledError:
            sim["status"] = "STOPPED"
            sim["ended_at"] = datetime.utcnow().isoformat() + "Z"
            self._history.append(dict(sim))
            from app.services.sse_manager import sse_manager
            sse_manager.publish("THREAT_PROGRESS", {
                "scenario_id": scenario_id,
                "name": sim["name"],
                "current_step_index": sim["current_step_index"],
                "total_steps": sim["total_steps"],
                "progress": sim["progress"],
                "status": "STOPPED"
            })
            raise

    def get_status(self) -> List[Dict[str, Any]]:
        """Return active running simulations states, querying SQL alerts to see if AI has detected them."""
        db = SessionLocal()
        try:
            for scenario_id, sim in self._active_simulations.items():
                # Query DB to check if AI Detection Engine has raised alerts for targets in this window
                t_user = sim.get("target_user_id")
                t_device = sim.get("target_device_id")
                t_asset = sim.get("target_asset_id")

                stmt = select(Alert).where(
                    and_(
                        Alert.status.in_(["New", "Investigating"]),
                        Alert.created_at >= datetime.fromisoformat(sim["started_at"].replace("Z", "")),
                        Alert.user_id == t_user if t_user else
                        Alert.device_id == t_device if t_device else
                        Alert.asset_id == t_asset if t_asset else False
                    )
                )
                alerts = db.execute(stmt).scalars().all()
                if alerts:
                    sim["detected"] = True
                    max_severity = "Low"
                    for a in alerts:
                        if a.severity == "Critical":
                            max_severity = "Critical"
                        elif a.severity == "High" and max_severity != "Critical":
                            max_severity = "High"
                        elif a.severity == "Medium" and max_severity not in ["Critical", "High"]:
                            max_severity = "Medium"
                    sim["risk_level"] = max_severity
                else:
                    sim["detected"] = False
                    sim["risk_level"] = "Low"
        finally:
            db.close()

        return list(self._active_simulations.values())

    def get_timeline(self) -> List[Dict[str, Any]]:
        return self._timeline

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history


threat_engine = ThreatEngine()
