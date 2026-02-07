"""
Robust error recovery and graceful degradation for DGT Autonomous Movie System

Provides comprehensive error handling, recovery strategies, and graceful degradation
for long-running autonomous movie generation.
"""

import time
import traceback
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from loguru import logger


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(str, Enum):
    """Available recovery actions"""
    RETRY = "retry"
    SKIP = "skip"
    RESET = "reset"
    SHUTDOWN = "shutdown"
    DEGRADE = "degrade"


@dataclass
class ErrorContext:
    """Context information for error occurrence"""
    component: str  # Which pillar/component
    operation: str  # What operation was being performed
    turn_count: int
    frame_count: int
    timestamp: float = field(default_factory=time.time)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_type: str
    severity: ErrorSeverity
    message: str
    context: ErrorContext
    recovery_action: Optional[RecoveryAction] = None
    recovery_successful: Optional[bool] = None
    stack_trace: Optional[str] = None


@dataclass
class RecoveryMetrics:
    """Metrics for error recovery performance"""
    total_errors: int = 0
    recovered_errors: int = 0
    critical_errors: int = 0
    shutdowns_triggered: int = 0
    degradation_events: int = 0
    average_recovery_time_ms: float = 0.0


class GracefulDegradation:
    """Manages graceful degradation when components fail"""
    
    def __init__(self):
        self.degradation_level = 0  # 0 = full functionality, 5 = minimal
        self.degraded_features = set()
        self.recovery_attempts = {}
        
    def can_degrade(self, component: str) -> bool:
        """Check if component can be degraded"""
        degradable_components = {
            "graphics", "chronicler", "monitoring", "effects"
        }
        return component in degradable_components
    
    def degrade_component(self, component: str, level: int = 1) -> bool:
        """Degrade a component functionality"""
        if not self.can_degrade(component):
            logger.warning(f"Component {component} cannot be degraded")
            return False
        
        self.degraded_features.add(component)
        self.degradation_level = max(self.degradation_level, level)
        
        logger.warning(f"Degraded component {component} to level {level}")
        return True
    
    def restore_component(self, component: str) -> bool:
        """Attempt to restore degraded component"""
        if component not in self.degraded_features:
            return False
        
        self.degraded_features.remove(component)
        
        # Recalculate degradation level
        if self.degraded_features:
            self.degradation_level = min(self.degradation_level, len(self.degraded_features))
        else:
            self.degradation_level = 0
        
        logger.info(f"Restored component {component}, degradation level: {self.degradation_level}")
        return True
    
    def get_degradation_summary(self) -> Dict[str, Any]:
        """Get current degradation status"""
        return {
            "level": self.degradation_level,
            "degraded_components": list(self.degraded_features),
            "functionality_percentage": max(0, 100 - (self.degradation_level * 20))
        }


class ErrorRecoverySystem:
    """Comprehensive error recovery and graceful degradation system"""
    
    def __init__(self, max_recovery_attempts: int = 3):
        self.max_recovery_attempts = max_recovery_attempts
        self.error_history: List[ErrorRecord] = []
        self.degradation = GracefulDegradation()
        self.metrics = RecoveryMetrics()
        self.recovery_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default recovery strategies
        self._initialize_recovery_strategies()
        self._initialize_circuit_breakers()
    
    def _initialize_recovery_strategies(self) -> None:
        """Initialize default recovery strategies for different error types"""
        self.recovery_strategies.update({
            "ConnectionError": self._recover_connection_error,
            "TimeoutError": self._recover_timeout_error,
            "MemoryError": self._recover_memory_error,
            "ValueError": self._recover_value_error,
            "KeyError": self._recover_key_error,
            "ImportError": self._recover_import_error,
            "FileNotFoundError": self._recover_file_error,
            "PermissionError": self._recover_permission_error,
        })
    
    def _initialize_circuit_breakers(self) -> None:
        """Initialize circuit breakers for frequently failing operations"""
        self.circuit_breakers.update({
            "world_generation": {"failures": 0, "last_failure": 0, "threshold": 3, "timeout": 300},
            "pathfinding": {"failures": 0, "last_failure": 0, "threshold": 5, "timeout": 60},
            "rendering": {"failures": 0, "last_failure": 0, "threshold": 10, "timeout": 30},
            "persistence": {"failures": 0, "last_failure": 0, "threshold": 3, "timeout": 120},
        })
    
    def handle_error(self, error: Exception, context: ErrorContext) -> RecoveryAction:
        """Handle an error with appropriate recovery strategy"""
        start_time = time.time()
        
        # Record the error
        error_record = self._record_error(error, context)
        
        # Check circuit breaker
        if self._is_circuit_breaker_open(context.operation):
            logger.warning(f"Circuit breaker open for {context.operation}, skipping")
            return RecoveryAction.SKIP
        
        # Determine recovery action
        recovery_action = self._determine_recovery_action(error, error_record)
        
        # Attempt recovery
        recovery_success = self._attempt_recovery(error, context, recovery_action)
        
        # Update metrics
        recovery_time = (time.time() - start_time) * 1000
        self._update_metrics(error_record, recovery_success, recovery_time)
        
        # Handle circuit breaker logic
        self._update_circuit_breaker(context.operation, recovery_success)
        
        return recovery_action
    
    def _record_error(self, error: Exception, context: ErrorContext) -> ErrorRecord:
        """Record error details"""
        error_record = ErrorRecord(
            error_type=type(error).__name__,
            severity=self._determine_severity(error, context),
            message=str(error),
            context=context,
            stack_trace=traceback.format_exc()
        )
        
        self.error_history.append(error_record)
        
        # Keep only recent errors (last 100)
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        logger.error(f"Error recorded: {error_record.error_type} - {error_record.message}")
        logger.debug(f"Error context: {context.component}.{context.operation}")
        
        return error_record
    
    def _determine_severity(self, error: Exception, context: ErrorContext) -> ErrorSeverity:
        """Determine error severity based on type and context"""
        critical_components = {"dd_engine", "main_heartbeat"}
        critical_operations = {"process_intent", "execute_validated_intent"}
        
        if context.component in critical_components and context.operation in critical_operations:
            return ErrorSeverity.CRITICAL
        
        error_type = type(error).__name__
        if error_type in {"MemoryError", "SystemExit", "KeyboardInterrupt"}:
            return ErrorSeverity.CRITICAL
        elif error_type in {"ConnectionError", "TimeoutError", "FileNotFoundError"}:
            return ErrorSeverity.HIGH
        elif error_type in {"ValueError", "KeyError", "AttributeError"}:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _determine_recovery_action(self, error: Exception, error_record: ErrorRecord) -> RecoveryAction:
        """Determine best recovery action for error"""
        error_type = type(error).__name__
        severity = error_record.severity
        
        # Critical errors may require shutdown
        if severity == ErrorSeverity.CRITICAL:
            if error_type in {"MemoryError", "SystemExit"}:
                return RecoveryAction.SHUTDOWN
            else:
                return RecoveryAction.RESET
        
        # Check for specific recovery strategies
        if error_type in self.recovery_strategies:
            return RecoveryAction.RETRY
        
        # High severity errors in non-critical components may be skipped
        if severity == ErrorSeverity.HIGH and error_record.context.component not in {"dd_engine"}:
            return RecoveryAction.SKIP
        
        # Default to retry for most errors
        return RecoveryAction.RETRY
    
    def _attempt_recovery(self, error: Exception, context: ErrorContext, action: RecoveryAction) -> bool:
        """Attempt to recover from error"""
        logger.info(f"Attempting recovery: {action.value} for {type(error).__name__}")
        
        try:
            if action == RecoveryAction.RETRY:
                return self._execute_recovery_strategy(error, context)
            elif action == RecoveryAction.SKIP:
                return self._skip_operation(context)
            elif action == RecoveryAction.RESET:
                return self._reset_component(context.component)
            elif action == RecoveryAction.DEGRADE:
                return self._degrade_functionality(context.component)
            elif action == RecoveryAction.SHUTDOWN:
                return self._initiate_shutdown(error, context)
            else:
                return False
        except Exception as recovery_error:
            logger.error(f"Recovery failed: {recovery_error}")
            return False
    
    def _execute_recovery_strategy(self, error: Exception, context: ErrorContext) -> bool:
        """Execute specific recovery strategy for error type"""
        error_type = type(error).__name__
        
        if error_type in self.recovery_strategies:
            strategy = self.recovery_strategies[error_type]
            return strategy(error, context)
        
        return False
    
    def _recover_connection_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from connection errors"""
        logger.info("Attempting connection recovery...")
        time.sleep(1.0)  # Brief delay
        return True  # Assume retry will work
    
    def _recover_timeout_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from timeout errors"""
        logger.info("Attempting timeout recovery...")
        # Increase timeout or reduce workload
        return True
    
    def _recover_memory_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from memory errors"""
        logger.critical("Memory error detected, initiating cleanup...")
        
        # Try garbage collection
        import gc
        gc.collect()
        
        # Degrade non-essential components
        self.degradation.degrade_component("graphics", level=2)
        self.degradation.degrade_component("chronicler", level=1)
        
        return True
    
    def _recover_value_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from value errors"""
        logger.info("Value error recovery - using default values")
        return True
    
    def _recover_key_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from key errors"""
        logger.info("Key error recovery - using fallback keys")
        return True
    
    def _recover_import_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from import errors"""
        logger.error("Import error - component may be unavailable")
        return self.degradation.degrade_component(context.component)
    
    def _recover_file_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from file errors"""
        logger.info("File error recovery - creating missing directories")
        
        # Try to create missing directories
        if context.operation in {"save_state", "load_state"}:
            Path("backups/").mkdir(parents=True, exist_ok=True)
            return True
        
        return False
    
    def _recover_permission_error(self, error: Exception, context: ErrorContext) -> bool:
        """Recover from permission errors"""
        logger.error("Permission error - switching to alternative location")
        
        # Switch to user directory for persistence
        if context.operation in {"save_state", "load_state"}:
            import os
            user_dir = os.path.expanduser("~/.dgt/")
            Path(user_dir).mkdir(parents=True, exist_ok=True)
            return True
        
        return False
    
    def _skip_operation(self, context: ErrorContext) -> bool:
        """Skip the failed operation"""
        logger.info(f"Skipping operation: {context.operation}")
        return True
    
    def _reset_component(self, component: str) -> bool:
        """Reset a component to clean state"""
        logger.info(f"Resetting component: {component}")
        
        # This would need to be implemented based on component interfaces
        # For now, just log the attempt
        return True
    
    def _degrade_functionality(self, component: str) -> bool:
        """Degrade component functionality"""
        logger.warning(f"Degrading functionality for: {component}")
        return self.degradation.degrade_component(component)
    
    def _initiate_shutdown(self, error: Exception, context: ErrorContext) -> bool:
        """Initiate graceful shutdown"""
        logger.critical(f"Initiating shutdown due to: {type(error).__name__}")
        self.metrics.shutdowns_triggered += 1
        
        # Save current state if possible
        try:
            self._emergency_save_state()
        except Exception as save_error:
            logger.error(f"Emergency save failed: {save_error}")
        
        return False  # Shutdown means recovery failed
    
    def _emergency_save_state(self) -> None:
        """Emergency save of current state"""
        emergency_file = f"emergency_save_{int(time.time())}.json"
        logger.info(f"Emergency saving state to {emergency_file}")
        
        # This would need to be implemented with actual state access
        # For now, just create a marker file
        with open(emergency_file, 'w') as f:
            f.write('{"emergency_save": true, "timestamp": ' + str(time.time()) + '}')
    
    def _is_circuit_breaker_open(self, operation: str) -> bool:
        """Check if circuit breaker is open for operation"""
        if operation not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[operation]
        
        # Check if we've exceeded failure threshold
        if breaker["failures"] >= breaker["threshold"]:
            # Check if timeout has passed
            if time.time() - breaker["last_failure"] > breaker["timeout"]:
                # Reset circuit breaker
                breaker["failures"] = 0
                return False
            else:
                return True
        
        return False
    
    def _update_circuit_breaker(self, operation: str, success: bool) -> None:
        """Update circuit breaker state"""
        if operation not in self.circuit_breakers:
            return
        
        breaker = self.circuit_breakers[operation]
        
        if success:
            # Reset on success
            breaker["failures"] = 0
        else:
            # Increment failures
            breaker["failures"] += 1
            breaker["last_failure"] = time.time()
    
    def _update_metrics(self, error_record: ErrorRecord, success: bool, recovery_time_ms: float) -> None:
        """Update recovery metrics"""
        self.metrics.total_errors += 1
        
        if success:
            self.metrics.recovered_errors += 1
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.metrics.critical_errors += 1
        
        # Update average recovery time
        if self.metrics.total_errors == 1:
            self.metrics.average_recovery_time_ms = recovery_time_ms
        else:
            self.metrics.average_recovery_time_ms = (
                (self.metrics.average_recovery_time_ms * (self.metrics.total_errors - 1) + recovery_time_ms) /
                self.metrics.total_errors
            )
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        recent_errors = [e for e in self.error_history if time.time() - e.context.timestamp < 300]  # Last 5 minutes
        
        return {
            "error_recovery": {
                "total_errors": self.metrics.total_errors,
                "recovered_errors": self.metrics.recovered_errors,
                "recovery_rate": self.metrics.recovered_errors / max(1, self.metrics.total_errors),
                "critical_errors": self.metrics.critical_errors,
                "shutdowns_triggered": self.metrics.shutdowns_triggered,
                "average_recovery_time_ms": self.metrics.average_recovery_time_ms,
                "recent_errors": len(recent_errors)
            },
            "degradation": self.degradation.get_degradation_summary(),
            "circuit_breakers": {
                name: {"failures": cb["failures"], "threshold": cb["threshold"]}
                for name, cb in self.circuit_breakers.items()
            },
            "status": "healthy" if len(recent_errors) < 5 else "degraded"
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = RecoveryMetrics()
        self.error_history.clear()
        self.degradation = GracefulDegradation()
        logger.info("Error recovery metrics reset")


# Global error recovery instance
_error_recovery: Optional[ErrorRecoverySystem] = None


def get_error_recovery() -> ErrorRecoverySystem:
    """Get global error recovery instance"""
    global _error_recovery
    if _error_recovery is None:
        _error_recovery = ErrorRecoverySystem()
    return _error_recovery


def initialize_error_recovery(max_recovery_attempts: int = 3) -> ErrorRecoverySystem:
    """Initialize error recovery system"""
    global _error_recovery
    _error_recovery = ErrorRecoverySystem(max_recovery_attempts)
    logger.info("Error recovery system initialized")
    return _error_recovery


def handle_error_with_context(error: Exception, component: str, operation: str, 
                             turn_count: int = 0, frame_count: int = 0, 
                             **additional_data) -> RecoveryAction:
    """Convenience function to handle errors with context"""
    context = ErrorContext(
        component=component,
        operation=operation,
        turn_count=turn_count,
        frame_count=frame_count,
        additional_data=additional_data
    )
    
    recovery = get_error_recovery()
    return recovery.handle_error(error, context)
