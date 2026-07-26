from typing import Dict, List, Optional
from app.services.threat_engine.interfaces import ThreatScenario
from app.services.threat_engine.scenarios import (
    InsiderThreatScenario,
    BruteForceScenario,
    UsbMalwareScenario,
    PlcManipulationScenario,
    LateralMovementScenario,
    RemoteAccessScenario,
    DataExfiltrationScenario,
    CredentialStuffingScenario,
    LowAndSlowExfiltrationScenario,
    InsiderDriftScenario,
)


class ScenarioRegistry:
    def __init__(self) -> None:
        self._scenarios: Dict[str, ThreatScenario] = {}
        self._register_default_scenarios()

    def _register_default_scenarios(self) -> None:
        self.register(InsiderThreatScenario())
        self.register(BruteForceScenario())
        self.register(UsbMalwareScenario())
        self.register(PlcManipulationScenario())
        self.register(LateralMovementScenario())
        self.register(RemoteAccessScenario())
        self.register(DataExfiltrationScenario())
        self.register(CredentialStuffingScenario())
        self.register(LowAndSlowExfiltrationScenario())
        self.register(InsiderDriftScenario(suspicious=True))
        self.register(InsiderDriftScenario(suspicious=False))

    def register(self, scenario: ThreatScenario) -> None:
        self._scenarios[scenario.scenario_id] = scenario

    def get(self, scenario_id: str) -> Optional[ThreatScenario]:
        return self._scenarios.get(scenario_id)

    def list_all(self) -> List[ThreatScenario]:
        return list(self._scenarios.values())


scenario_registry = ScenarioRegistry()
