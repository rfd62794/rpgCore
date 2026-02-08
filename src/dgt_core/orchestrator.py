"""
DGT Orchestrator - Unified Entry Point for the Architectural Singularity
ADR 165: Master Orchestrator for Brain/Body/Senses Coordination
"""

import time
import threading
from typing import Optional, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass

from loguru import logger

# Import version gatekeeper for Python 3.12 enforcement
from .kernel.gatekeeper import verify_python_version

from .engines.space import SpaceVoyagerEngineRunner, create_space_engine_runner
from .engines.shells import ShellEngine, create_shell_engine
from .view.view_coordinator import ViewCoordinator, create_view_coordinator
from .kernel.batch_processor import ThreadSafeBatchProcessor, create_batch_processor
from .kernel.universal_registry import UniversalRegistry, create_universal_registry


class EngineType(str, Enum):
    """Supported engine types"""
    SPACE = "space"
    SHELL = "shell"


class ViewType(str, Enum):
    """Supported view types"""
    RICH = "rich"
    PYGAME = "pygame"
    TERMINAL = "terminal"
    AUTO = "auto"


@dataclass
class OrchestratorConfig:
    """Configuration for DGT Orchestrator"""
    engine_type: EngineType
    view_type: ViewType = ViewType.AUTO
    fleet_size: int = 5
    party_size: int = 5
    refresh_rate: float = 1.0
    log_level: str = "INFO"
    enable_file_logging: bool = True
    enable_graphics: bool = False


class DGTOrchestrator:
    """The 'God Object' for the Singularity. Manages the lifecycle of a DGT session."""
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """Initialize the DGT Orchestrator with Python 3.12 enforcement"""
        # Enforce Python 3.12 requirement immediately
        verify_python_version()
        
        self.config = config or OrchestratorConfig()
        self.engine: Optional[Union[SpaceVoyagerEngineRunner, ShellEngine]] = None
        self.view_coordinator: Optional[ViewCoordinator] = None
        self.batch_processor: Optional[ThreadSafeBatchProcessor] = None
        self.universal_registry: Optional[UniversalRegistry] = None
        self.is_running = False
        self.start_time: Optional[float] = None
        self.stop_time: Optional[float] = None
        
        logger.info(f"🎖️ DGTOrchestrator initialized: engine={self.config.engine_type.value}, view={self.config.view_type.value}")
    
    def start(self) -> bool:
        """Start the complete DGT ecosystem"""
        try:
            logger.info("🎖️ Starting DGT Orchestrator...")
            
            # 1. Initialize core components
            self._initialize_core_components()
            
            # 2. Initialize engine
            self._initialize_engine()
            
            # 3. Initialize view system
            self._initialize_view_system()
            
            # 4. Start orchestration loop
            self._start_orchestration()
            
            logger.success("🎖️ DGT Orchestrator started successfully")
            return True
            
        except Exception as e:
            logger.error(f"🎖️ Failed to start orchestrator: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the DGT ecosystem gracefully"""
        logger.info("🎖️ Stopping DGT Orchestrator...")
        
        self._running = False
        
        # Stop orchestration thread
        if self._orchestration_thread:
            self._orchestration_thread.join(timeout=2.0)
        
        # Stop components in reverse order
        if self.view_coordinator:
            self.view_coordinator.stop_coordination()
        
        if self.batch_processor:
            self.batch_processor.force_process_batch()
        
        logger.info("🎖️ DGT Orchestrator stopped")
    
    def _initialize_core_components(self):
        """Initialize core infrastructure components"""
        # Initialize batch processor
        self.batch_processor = create_batch_processor()
        
        # Initialize universal registry
        self.universal_registry = create_universal_registry()
        
        # Configure logging
        from .view.cli.logger_config import configure_logging
        log_file = "logs/dgt_orchestrator.log" if self.config.enable_file_logging else None
        configure_logging(
            log_level=self.config.log_level,
            log_file=log_file,
            enable_rich=True
        )
        
        logger.debug("🎖️ Core components initialized")
    
    def _initialize_engine(self):
        """Initialize the appropriate engine"""
        if self.config.engine_type == EngineType.SPACE:
            self.engine = create_space_engine_runner(fleet_size=self.config.fleet_size)
            logger.info(f"🎖️ Space engine initialized: fleet_size={self.config.fleet_size}")
        elif self.config.engine_type == EngineType.SHELL:
            self.engine = create_shell_engine(party_size=self.config.party_size)
            logger.info(f"🎖️ Shell engine initialized: party_size={self.config.party_size}")
        else:
            raise ValueError(f"Unknown engine type: {self.config.engine_type}")
    
    def _initialize_view_system(self):
        """Initialize the view system with auto-detection"""
        # Auto-detect view type if needed
        view_type = self.config.view_type
        if view_type == ViewType.AUTO:
            view_type = self._auto_detect_view_type()
        
        # Initialize view coordinator
        self.view_coordinator = create_view_coordinator(max_workers=2)
        
        # Determine which views to enable
        enable_dashboard = view_type in [ViewType.RICH, ViewType.AUTO]
        enable_inspector = view_type in [ViewType.TERMINAL, ViewType.AUTO]
        enable_graphics = view_type == ViewType.PYGAME or self.config.enable_graphics
        
        # Initialize views
        self.view_coordinator.initialize_views(
            enable_dashboard=enable_dashboard,
            enable_inspector=enable_inspector
        )
        
        # Start view coordination
        self.view_coordinator.start_coordination()
        
        logger.info(f"🎖️ View system initialized: type={view_type.value}, graphics={enable_graphics}")
    
    def _auto_detect_view_type(self) -> ViewType:
        """Auto-detect appropriate view type based on environment"""
        try:
            # Check if we're in a terminal environment
            import sys
            if hasattr(sys, 'ps1') or not sys.stdout.isatty():
                return ViewType.RICH
            
            # Check if pygame is available and display is available
            if self.config.enable_graphics:
                try:
                    import pygame
                    pygame.display.init()
                    pygame.display.quit()
                    return ViewType.PYGAME
                except:
                    pass
            
            # Default to Rich
            return ViewType.RICH
            
        except Exception:
            return ViewType.RICH
    
    def _start_orchestration(self):
        """Start the main orchestration loop"""
        self._running = True
        self._orchestration_thread = threading.Thread(
            target=self._orchestration_loop, 
            daemon=True,
            name="dgt_orchestrator"
        )
        self._orchestration_thread.start()
    
    def _orchestration_loop(self):
        """Main orchestration loop - coordinates all components"""
        logger.info("🎖️ Entering orchestration loop")
        
        last_update = time.time()
        update_interval = 1.0 / 60.0  # 60 FPS
        
        while self._running:
            try:
                current_time = time.time()
                
                # Update engine
                if self.engine:
                    self._update_engine()
                
                # Update views
                if current_time - last_update >= self.config.refresh_rate:
                    self._update_views()
                    last_update = current_time
                
                # Process batch updates
                if self.batch_processor:
                    pending_count = self.batch_processor.get_pending_count()
                    if pending_count >= 10:  # Process when we have enough updates
                        self.batch_processor.force_process_batch()
                
                # Sleep to maintain frame rate
                time.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"🎖️ Orchestration loop error: {e}")
                time.sleep(0.1)  # Back off on error
    
    def _update_engine(self):
        """Update the active engine"""
        if self.config.engine_type == EngineType.SPACE:
            # Update space engine
            # This would be implemented with actual target assignments
            pass
        elif self.config.engine_type == EngineType.SHELL:
            # Update shell engine
            # This would be implemented with actual target assignments
            pass
    
    def _update_views(self):
        """Update all view components with current state"""
        if not self.view_coordinator:
            return
        
        # Collect current state
        fleet_state = self._collect_fleet_state()
        tactical_state = self._collect_tactical_state()
        system_health = self._collect_system_health()
        
        # Update views
        self.view_coordinator.update_fleet_view(fleet_state, tactical_state, system_health)
    
    def _collect_fleet_state(self) -> list[Dict[str, Any]]:
        """Collect current fleet state"""
        fleet_state = []
        
        if self.config.engine_type == EngineType.SPACE and hasattr(self.engine, 'ships'):
            for ship_id, ship in self.engine.ships.items():
                if ship.is_alive():
                    fleet_state.append({
                        'ship_id': ship_id,
                        'position': (ship.x, ship.y),
                        'health_percentage': ship.health / ship.max_health,
                        'thrust_active': abs(ship.velocity_x) > 0.1 or abs(ship.velocity_y) > 0.1,
                        'engine_type': 'space',
                        'role': 'fighter'  # Would be determined from genome
                    })
        
        elif self.config.engine_type == EngineType.SHELL and hasattr(self.engine, 'entities'):
            for entity_id, entity in self.engine.entities.items():
                if entity.is_alive():
                    fleet_state.append({
                        'ship_id': entity_id,
                        'position': (entity.x, entity.y),
                        'health_percentage': entity.shell.hit_points / entity.shell.max_hit_points,
                        'thrust_active': entity.can_act(),
                        'engine_type': 'shell',
                        'role': entity.shell.primary_role.value
                    })
        
        return fleet_state
    
    def _collect_tactical_state(self) -> Dict[str, Any]:
        """Collect current tactical state"""
        return {
            'total_ships': len(self._collect_fleet_state()),
            'active_engagements': 0,  # Would be calculated from actual engagements
            'fleet_dps': 0.0,  # Would be calculated from fleet
            'avg_accuracy': 0.0,  # Would be calculated from fleet
            'command_confidence': 1.0,  # Would come from admiral service
            'target_locks': 0  # Would be calculated from targeting system
        }
    
    def _collect_system_health(self) -> Dict[str, Any]:
        """Collect system health metrics"""
        return {
            'physics_status': 'HEALTHY',
            'physics_load': 0.1,
            'evolution_status': 'HEALTHY',
            'evolution_load': 0.05,
            'batch_status': 'HEALTHY',
            'batch_load': self.batch_processor.get_pending_count() / 100.0 if self.batch_processor else 0.0,
            'memory_mb': 100.0,  # Would be actual memory usage
            'memory_load': 0.2,
            'fps': 60.0,
            'frame_time_ms': 16.67
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            'running': self._running,
            'engine_type': self.config.engine_type.value,
            'view_type': self.config.view_type.value,
            'fleet_size': len(self._collect_fleet_state()),
            'view_status': self.view_coordinator.get_queue_status() if self.view_coordinator else {},
            'batch_status': {
                'pending': self.batch_processor.get_pending_count() if self.batch_processor else 0
            }
        }


# Factory functions for easy initialization
def create_space_orchestrator(fleet_size: int = 5, view_type: ViewType = ViewType.AUTO) -> DGTOrchestrator:
    """Create a DGT Orchestrator for Space engine"""
    config = OrchestratorConfig(
        engine_type=EngineType.SPACE,
        view_type=view_type,
        fleet_size=fleet_size
    )
    return DGTOrchestrator(config)


def create_shell_orchestrator(party_size: int = 5, view_type: ViewType = ViewType.AUTO) -> DGTOrchestrator:
    """Create a DGT Orchestrator for Shell engine"""
    config = OrchestratorConfig(
        engine_type=EngineType.SHELL,
        view_type=view_type,
        party_size=party_size
    )
    return DGTOrchestrator(config)


def create_auto_orchestrator(engine_type: EngineType, view_type: ViewType = ViewType.AUTO) -> DGTOrchestrator:
    """Create a DGT Orchestrator with auto-detection"""
    config = OrchestratorConfig(
        engine_type=engine_type,
        view_type=view_type
    )
    return DGTOrchestrator(config)


# Global instance for convenience
dgt_orchestrator = None
