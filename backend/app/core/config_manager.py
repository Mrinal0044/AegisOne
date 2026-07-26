class SystemConfig:
    def __init__(self) -> None:
        self.risk_threshold: int = 60
        self.alert_threshold: int = 60
        self.threat_delay_scale: float = 1.0
        self.impossible_travel_threshold: float = 800.0
        self.fingerprint_sensitivity: float = 0.5
        self.credential_stuffing_window: int = 60
        self.exfiltration_detection_window: int = 3600
        self.cold_start_observation_count: int = 10
        self.drift_sensitivity: float = 0.5


system_config = SystemConfig()
