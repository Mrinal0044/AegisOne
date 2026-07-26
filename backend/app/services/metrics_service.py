import logging
from typing import Dict, Any, List

logger = logging.getLogger("app.services.metrics_service")


class MetricsService:
    def __init__(self) -> None:
        self.total_requests: int = 0
        self.total_errors: int = 0
        self.slow_requests_count: int = 0
        self.endpoint_counts: Dict[str, int] = {}
        self.endpoint_latencies: Dict[str, float] = {}
        self.active_sse: int = 0
        self.threats_executed: int = 0
        self.alerts_generated: int = 0
        self.copilot_requests: int = 0

    def record_request(self, path: str, duration: float, is_error: bool) -> None:
        """Register API latency metrics and check for performance bottlenecks."""
        self.total_requests += 1
        if is_error:
            self.total_errors += 1
        if duration > 1.0:  # Threshold of 1.0 seconds is classified as slow
            self.slow_requests_count += 1

        # Strip variable UUID path parameters for clean endpoint aggregation
        clean_path = path
        # Simple regex-free UUID replacement
        parts = path.split("/")
        for idx, part in enumerate(parts):
            if len(part) == 36 and part.count("-") == 4:  # standard UUID length and count
                parts[idx] = "{id}"
        clean_path = "/".join(parts)

        self.endpoint_counts[clean_path] = self.endpoint_counts.get(clean_path, 0) + 1

        # Calculate moving average latency for clean tracking
        current_avg = self.endpoint_latencies.get(clean_path, 0.0)
        count = self.endpoint_counts[clean_path]
        self.endpoint_latencies[clean_path] = current_avg + (duration - current_avg) / count

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Compile a summary of operational performance benchmarks."""
        error_rate = (self.total_errors / self.total_requests * 100.0) if self.total_requests > 0 else 0.0
        avg_latency = sum(self.endpoint_latencies.values()) / len(self.endpoint_latencies) if self.endpoint_latencies else 0.0
        
        return {
            "total_requests": self.total_requests,
            "error_rate_percent": round(error_rate, 2),
            "slow_requests_count": self.slow_requests_count,
            "average_latency_seconds": round(avg_latency, 4),
            "active_sse_connections": self.active_sse,
            "threats_executed": self.threats_executed,
            "alerts_generated": self.alerts_generated,
            "copilot_requests": self.copilot_requests,
            "endpoints": {
                k: {
                    "count": self.endpoint_counts[k],
                    "average_latency_seconds": round(self.endpoint_latencies[k], 4)
                }
                for k in self.endpoint_counts
            }
        }


# Singleton instance
metrics_service = MetricsService()
