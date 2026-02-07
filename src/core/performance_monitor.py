"""
Comprehensive performance monitoring and metrics collection for DGT Autonomous Movie System

Real-time performance tracking, alerting, and historical analysis for production monitoring.
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
from pathlib import Path

from loguru import logger


class MetricType(str, Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Performance alert definition"""
    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    level: AlertLevel
    message: str
    enabled: bool = True
    cooldown_seconds: int = 300  # 5 minutes default
    last_triggered: float = 0.0


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    fps: float
    frame_time_ms: float
    turn_count: int
    entities_count: int
    world_deltas_count: int


class MetricsCollector:
    """Collects and manages performance metrics"""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric"""
        with self._lock:
            full_name = self._make_full_name(name, labels)
            self.counters[full_name] += value
            self._add_metric_point(MetricType.COUNTER, full_name, self.counters[full_name], labels)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric"""
        with self._lock:
            full_name = self._make_full_name(name, labels)
            self.gauges[full_name] = value
            self._add_metric_point(MetricType.GAUGE, full_name, value, labels)
    
    def add_histogram_value(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Add a value to a histogram"""
        with self._lock:
            full_name = self._make_full_name(name, labels)
            self.histograms[full_name].append(value)
            self._add_metric_point(MetricType.HISTOGRAM, full_name, value, labels)
    
    def record_timer(self, name: str, duration_ms: float, labels: Dict[str, str] = None) -> None:
        """Record a timer duration"""
        with self._lock:
            full_name = self._make_full_name(name, labels)
            self.timers[full_name].append(duration_ms)
            self._add_metric_point(MetricType.TIMER, full_name, duration_ms, labels)
    
    def _make_full_name(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create full metric name with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"
    
    def _add_metric_point(self, metric_type: MetricType, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Add a metric point to history"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(point)
    
    def get_metric_history(self, name: str, since_seconds: Optional[float] = None) -> List[MetricPoint]:
        """Get metric history for a given name"""
        with self._lock:
            history = list(self.metrics.get(name, []))
            
            if since_seconds is not None:
                cutoff_time = time.time() - since_seconds
                history = [p for p in history if p.timestamp >= cutoff_time]
            
            return history
    
    def get_metric_summary(self, name: str, since_seconds: float = 300) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        history = self.get_metric_history(name, since_seconds)
        
        if not history:
            return {"count": 0}
        
        values = [p.value for p in history]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "trend": self._calculate_trend(values)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation based on first and last third
        third = len(values) // 3
        if third < 1:
            return "stable"
        
        first_avg = sum(values[:third]) / third
        last_avg = sum(values[-third:]) / third
        
        diff_percent = ((last_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if diff_percent > 10:
            return "increasing"
        elif diff_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def reset_metric(self, name: str) -> None:
        """Reset a specific metric"""
        with self._lock:
            self.metrics[name].clear()
            self.counters.pop(name, None)
            self.gauges.pop(name, None)
            self.histograms.pop(name, None)
            self.timers.pop(name, None)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values"""
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: {"count": len(v), "sum": sum(v)} for k, v in self.histograms.items()},
                "timers": {k: {"count": len(v), "avg_ms": sum(v) / len(v) if v else 0} for k, v in self.timers.items()}
            }


class AlertManager:
    """Manages performance alerts and notifications"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.notification_handlers: List[Callable] = []
        
        # Initialize default alerts
        self._initialize_default_alerts()
    
    def _initialize_default_alerts(self) -> None:
        """Initialize default performance alerts"""
        default_alerts = [
            Alert(
                name="high_cpu_usage",
                metric_name="system.cpu_percent",
                condition="gt",
                threshold=80.0,
                level=AlertLevel.WARNING,
                message="CPU usage is above 80%"
            ),
            Alert(
                name="high_memory_usage",
                metric_name="system.memory_mb",
                condition="gt",
                threshold=512.0,
                level=AlertLevel.WARNING,
                message="Memory usage is above 512MB"
            ),
            Alert(
                name="low_fps",
                metric_name="performance.fps",
                condition="lt",
                threshold=30.0,
                level=AlertLevel.ERROR,
                message="FPS dropped below 30"
            ),
            Alert(
                name="high_frame_time",
                metric_name="performance.frame_time_ms",
                condition="gt",
                threshold=50.0,
                level=AlertLevel.ERROR,
                message="Frame time exceeded 50ms"
            ),
            Alert(
                name="slow_turn_processing",
                metric_name="performance.turn_time_ms",
                condition="gt",
                threshold=100.0,
                level=AlertLevel.WARNING,
                message="Turn processing exceeded 100ms"
            ),
            Alert(
                name="critical_memory_usage",
                metric_name="system.memory_mb",
                condition="gt",
                threshold=1024.0,
                level=AlertLevel.CRITICAL,
                message="Memory usage is critical (>1GB)"
            )
        ]
        
        for alert in default_alerts:
            self.add_alert(alert)
    
    def add_alert(self, alert: Alert) -> None:
        """Add a new alert"""
        self.alerts[alert.name] = alert
        logger.debug(f"Added alert: {alert.name}")
    
    def remove_alert(self, name: str) -> None:
        """Remove an alert"""
        if name in self.alerts:
            del self.alerts[name]
            logger.debug(f"Removed alert: {name}")
    
    def check_alerts(self, metrics_collector: MetricsCollector) -> List[Dict[str, Any]]:
        """Check all alerts against current metrics"""
        triggered_alerts = []
        current_time = time.time()
        
        for alert in self.alerts.values():
            if not alert.enabled:
                continue
            
            # Check cooldown
            if current_time - alert.last_triggered < alert.cooldown_seconds:
                continue
            
            # Get metric value
            metric_summary = metrics_collector.get_metric_summary(alert.metric_name, since_seconds=60)
            
            if metric_summary["count"] == 0:
                continue  # No data for this metric
            
            value = metric_summary["latest"]
            
            # Check alert condition
            triggered = False
            if alert.condition == "gt" and value > alert.threshold:
                triggered = True
            elif alert.condition == "lt" and value < alert.threshold:
                triggered = True
            elif alert.condition == "gte" and value >= alert.threshold:
                triggered = True
            elif alert.condition == "lte" and value <= alert.threshold:
                triggered = True
            elif alert.condition == "eq" and value == alert.threshold:
                triggered = True
            
            if triggered:
                alert.last_triggered = current_time
                
                alert_data = {
                    "name": alert.name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "metric": alert.metric_name,
                    "value": value,
                    "threshold": alert.threshold,
                    "timestamp": current_time
                }
                
                triggered_alerts.append(alert_data)
                self.alert_history.append(alert_data)
                
                # Send notifications
                self._send_notifications(alert_data)
                
                logger.warning(f"Alert triggered: {alert.name} - {alert.message}")
        
        return triggered_alerts
    
    def _send_notifications(self, alert_data: Dict[str, Any]) -> None:
        """Send alert notifications"""
        for handler in self.notification_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")
    
    def add_notification_handler(self, handler: Callable) -> None:
        """Add a notification handler"""
        self.notification_handlers.append(handler)
    
    def get_alert_history(self, since_seconds: float = 3600) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        cutoff_time = time.time() - since_seconds
        return [alert for alert in self.alert_history if alert["timestamp"] >= cutoff_time]


class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.frame_times: deque = deque(maxlen=60)  # Last 60 frames
        self.turn_start_time: Optional[float] = None
        
        # System monitoring
        self.process = psutil.Process()
        
        # Add log notification handler
        self.alerts.add_notification_handler(self._log_alert)
    
    def start(self) -> None:
        """Start performance monitoring"""
        if not self.enabled:
            logger.info("Performance monitoring disabled")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop(self) -> None:
        """Stop performance monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                self._collect_system_metrics()
                self._check_alerts()
                time.sleep(5)  # Collect every 5 seconds
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)  # Back off on error
    
    def _collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        # CPU and memory
        cpu_percent = self.process.cpu_percent()
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = self.process.memory_percent()
        
        self.metrics.set_gauge("system.cpu_percent", cpu_percent)
        self.metrics.set_gauge("system.memory_mb", memory_mb)
        self.metrics.set_gauge("system.memory_percent", memory_percent)
        
        # FPS calculation
        if len(self.frame_times) > 1:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
            self.metrics.set_gauge("performance.fps", fps)
            self.metrics.set_gauge("performance.frame_time_ms", avg_frame_time)
    
    def _check_alerts(self) -> None:
        """Check for performance alerts"""
        triggered_alerts = self.alerts.check_alerts(self.metrics)
        
        # Handle critical alerts
        for alert in triggered_alerts:
            if alert["level"] == "critical":
                logger.critical(f"CRITICAL ALERT: {alert['message']}")
                # Could trigger emergency procedures here
    
    def _log_alert(self, alert_data: Dict[str, Any]) -> None:
        """Log alert notification"""
        level = alert_data["level"]
        message = f"[{level.upper()}] {alert_data['message']} (Value: {alert_data['value']:.2f})"
        
        if level == "critical":
            logger.critical(message)
        elif level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    
    def record_frame_start(self) -> None:
        """Record start of frame processing"""
        self.last_frame_time = time.time()
    
    def record_frame_end(self) -> None:
        """Record end of frame processing"""
        frame_time = (time.time() - self.last_frame_time) * 1000
        self.frame_times.append(frame_time)
        self.metrics.record_timer("performance.frame_time_ms", frame_time)
    
    def record_turn_start(self) -> None:
        """Record start of turn processing"""
        self.turn_start_time = time.time()
    
    def record_turn_end(self) -> None:
        """Record end of turn processing"""
        if self.turn_start_time is not None:
            turn_time = (time.time() - self.turn_start_time) * 1000
            self.metrics.record_timer("performance.turn_time_ms", turn_time)
            self.turn_start_time = None
    
    def increment_turn_count(self) -> None:
        """Increment turn counter"""
        self.metrics.increment_counter("game.turns")
    
    def record_entity_count(self, count: int) -> None:
        """Record number of entities"""
        self.metrics.set_gauge("game.entities", count)
    
    def record_world_deltas(self, count: int) -> None:
        """Record number of world deltas"""
        self.metrics.set_gauge("game.world_deltas", count)
    
    def record_pathfinding_duration(self, duration_ms: float) -> None:
        """Record pathfinding duration"""
        self.metrics.record_timer("performance.pathfinding_ms", duration_ms)
    
    def record_rendering_duration(self, duration_ms: float) -> None:
        """Record rendering duration"""
        self.metrics.record_timer("performance.rendering_ms", duration_ms)
    
    def get_performance_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        return PerformanceSnapshot(
            timestamp=time.time(),
            cpu_percent=self.process.cpu_percent(),
            memory_mb=self.process.memory_info().rss / 1024 / 1024,
            memory_percent=self.process.memory_percent(),
            fps=self.metrics.gauges.get("performance.fps", 0.0),
            frame_time_ms=self.metrics.gauges.get("performance.frame_time_ms", 0.0),
            turn_count=int(self.metrics.counters.get("game.turns", 0)),
            entities_count=int(self.metrics.gauges.get("game.entities", 0)),
            world_deltas_count=int(self.metrics.gauges.get("game.world_deltas", 0))
        )
    
    def get_performance_report(self, since_seconds: float = 300) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        snapshot = self.get_performance_snapshot()
        
        # Get metric summaries
        metric_summaries = {}
        for metric_name in ["performance.fps", "performance.frame_time_ms", "system.cpu_percent", "system.memory_mb"]:
            metric_summaries[metric_name] = self.metrics.get_metric_summary(metric_name, since_seconds)
        
        # Get recent alerts
        recent_alerts = self.alerts.get_alert_history(since_seconds)
        
        return {
            "snapshot": {
                "timestamp": snapshot.timestamp,
                "cpu_percent": snapshot.cpu_percent,
                "memory_mb": snapshot.memory_mb,
                "fps": snapshot.fps,
                "frame_time_ms": snapshot.frame_time_ms,
                "turn_count": snapshot.turn_count,
                "entities_count": snapshot.entities_count,
                "world_deltas_count": snapshot.world_deltas_count
            },
            "metrics": metric_summaries,
            "alerts": {
                "recent_count": len(recent_alerts),
                "recent_alerts": recent_alerts[-10:]  # Last 10 alerts
            },
            "status": "healthy" if len(recent_alerts) < 3 else "degraded"
        }
    
    def export_metrics(self, file_path: str, since_seconds: float = 3600) -> None:
        """Export metrics to file"""
        import json
        
        report = self.get_performance_report(since_seconds)
        
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Metrics exported to {file_path}")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def initialize_performance_monitoring(enabled: bool = True) -> PerformanceMonitor:
    """Initialize performance monitoring system"""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(enabled)
    
    if enabled:
        _performance_monitor.start()
    
    logger.info(f"Performance monitoring initialized (enabled: {enabled})")
    return _performance_monitor


# Context managers for easy timing
class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, metric_name: str, labels: Dict[str, str] = None):
        self.metric_name = metric_name
        self.labels = labels
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            monitor = get_performance_monitor()
            monitor.metrics.record_timer(self.metric_name, duration_ms, self.labels)


def time_operation(metric_name: str, labels: Dict[str, str] = None):
    """Decorator for timing operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TimerContext(metric_name, labels):
                return func(*args, **kwargs)
        return wrapper
    return decorator
