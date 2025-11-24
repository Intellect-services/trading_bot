"""System monitoring for IntellectTrader."""

import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system metrics and performance."""

    def __init__(self) -> None:
        """Initialize system monitor."""
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.utcnow()

        # Metrics storage (last 1000 data points)
        self.metrics_history: dict[str, deque[dict[str, Any]]] = {
            "api_latency": deque(maxlen=1000),
            "order_success": deque(maxlen=1000),
            "order_failure": deque(maxlen=1000),
            "errors": deque(maxlen=1000),
        }

        # Counters
        self.total_orders = 0
        self.successful_orders = 0
        self.failed_orders = 0
        self.total_errors = 0

    def get_uptime(self) -> timedelta:
        """Get bot uptime.

        Returns:
            Uptime as timedelta
        """
        return datetime.utcnow() - self.start_time

    def get_uptime_percentage(self, total_time: timedelta) -> float:
        """Calculate uptime percentage.

        Args:
            total_time: Total time period

        Returns:
            Uptime percentage (0-100)
        """
        uptime = self.get_uptime()
        if total_time.total_seconds() == 0:
            return 100.0
        return (uptime.total_seconds() / total_time.total_seconds()) * 100

    def record_api_latency(self, latency_ms: float) -> None:
        """Record API latency.

        Args:
            latency_ms: Latency in milliseconds
        """
        self.metrics_history["api_latency"].append(
            {"timestamp": datetime.utcnow(), "value": latency_ms}
        )

    def record_order_success(self) -> None:
        """Record successful order."""
        self.total_orders += 1
        self.successful_orders += 1
        self.metrics_history["order_success"].append({"timestamp": datetime.utcnow()})

    def record_order_failure(self) -> None:
        """Record failed order."""
        self.total_orders += 1
        self.failed_orders += 1
        self.metrics_history["order_failure"].append({"timestamp": datetime.utcnow()})

    def record_error(self, error_type: str) -> None:
        """Record error.

        Args:
            error_type: Type of error
        """
        self.total_errors += 1
        self.metrics_history["errors"].append({"timestamp": datetime.utcnow(), "type": error_type})

    def get_order_success_rate(self) -> float:
        """Get order success rate.

        Returns:
            Success rate as percentage (0-100)
        """
        if self.total_orders == 0:
            return 100.0
        return (self.successful_orders / self.total_orders) * 100

    def get_average_api_latency(self) -> float:
        """Get average API latency.

        Returns:
            Average latency in milliseconds
        """
        if not self.metrics_history["api_latency"]:
            return 0.0

        latencies = [float(m["value"]) for m in self.metrics_history["api_latency"]]
        return sum(latencies) / len(latencies)

    def get_system_metrics(self) -> dict[str, Any]:
        """Get system resource metrics.

        Returns:
            Dictionary of system metrics
        """
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_mb": psutil.virtual_memory().used / (1024 * 1024),
                "disk_percent": psutil.disk_usage("/").percent,
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all monitoring metrics.

        Returns:
            Dictionary of all metrics
        """
        uptime = self.get_uptime()

        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime),
            "total_orders": self.total_orders,
            "successful_orders": self.successful_orders,
            "failed_orders": self.failed_orders,
            "order_success_rate": self.get_order_success_rate(),
            "average_api_latency_ms": self.get_average_api_latency(),
            "total_errors": self.total_errors,
            "system": self.get_system_metrics(),
        }

    def check_health(self) -> dict[str, Any]:
        """Check system health.

        Returns:
            Health status dictionary
        """
        metrics = self.get_all_metrics()
        issues = []

        # Check order success rate
        if metrics["order_success_rate"] < 90:
            issues.append(f"Low order success rate: {metrics['order_success_rate']:.1f}%")

        # Check API latency
        if metrics["average_api_latency_ms"] > 1000:
            issues.append(f"High API latency: {metrics['average_api_latency_ms']:.0f}ms")

        # Check system resources
        system = metrics["system"]
        if system.get("cpu_percent", 0) > 80:
            issues.append(f"High CPU usage: {system['cpu_percent']:.1f}%")

        if system.get("memory_percent", 0) > 80:
            issues.append(f"High memory usage: {system['memory_percent']:.1f}%")

        return {"healthy": len(issues) == 0, "issues": issues, "metrics": metrics}


# Global monitor instance
system_monitor = SystemMonitor()
