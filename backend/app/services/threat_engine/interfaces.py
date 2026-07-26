from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.orm import Session


class ThreatScenario(ABC):
    """Abstract base class representing a threat scenario simulation script."""

    @property
    @abstractmethod
    def scenario_id(self) -> str:
        """Unique ID string of the scenario (e.g. 'insider_threat')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the scenario."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Text summary explaining the attack steps and impact."""
        pass

    @abstractmethod
    def get_steps(
        self,
        db: Session,
        target_user_id: Optional[uuid.UUID] = None,
        target_device_id: Optional[uuid.UUID] = None,
        target_asset_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """Compiles the sequence of steps for this attack.
        
        Dynamically substitutes IP addresses, hostnames, and credentials from target entities.
        
        Each step dict must contain:
        - "name": step name (str)
        - "event_type": normalized event type (str)
        - "protocol": network protocol used (str)
        - "source_ip": source IP address (str)
        - "destination_ip": destination IP address (str)
        - "payload_summary": payload text (str)
        - "severity": severity level Info/Warning/Critical (str)
        - "delay_seconds": duration delay after this step (float)
        """
        pass
