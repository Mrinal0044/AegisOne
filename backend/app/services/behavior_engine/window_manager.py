from datetime import datetime, timedelta
from typing import Dict, List


class WindowManager:
    # Mapped durations in seconds
    WINDOW_DURATIONS: Dict[str, int] = {
        "5m": 5 * 60,
        "15m": 15 * 60,
        "1h": 60 * 60,
        "24h": 24 * 60 * 60,
        "7d": 7 * 24 * 60 * 60,
    }

    @classmethod
    def get_supported_windows(cls) -> List[str]:
        return list(cls.WINDOW_DURATIONS.keys())

    @classmethod
    def get_window_cutoff(cls, reference_time: datetime, window_size: str) -> datetime:
        """Returns the start boundary timestamp for the given window size relative to a reference time."""
        seconds = cls.WINDOW_DURATIONS.get(window_size, 3600)
        return reference_time - timedelta(seconds=seconds)

    @classmethod
    def is_in_window(cls, event_time: datetime, reference_time: datetime, window_size: str) -> bool:
        """Checks if an event's timestamp falls within the sliding window relative to the reference time."""
        cutoff = cls.get_window_cutoff(reference_time, window_size)
        return cutoff <= event_time <= reference_time


window_manager = WindowManager()
