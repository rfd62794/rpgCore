"""
Theater Director - The Observer for Theater Architecture

Monitors the Playbook and gives the "Action" signal.
No longer moves the character directly - simply checks if the Actor is at the mark.

ADR 051: Theater-Driven Narrative Controller  
- Observes Voyager position relative to playbook targets
- Triggers StageManager cues when actor reaches marks
- Maintains narrative flow without direct movement control
"""

from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

from loguru import logger

# Forward references to avoid circular imports
try:
    from logic.playbook import Playbook, Act
    from core.stage_manager import StageManager
    from core.simulator import SimulatorHost
    from logic.pathfinding import NavigationSystem
except ImportError:
    Playbook = None
    Act = None
    StageManager = None
    SimulatorHost = None
    NavigationSystem = None


class DirectorState(Enum):
    """States of the Theater Director."""
    WAITING_FOR_ACTOR = "waiting_for_actor"
    ACTOR_AT_MARK = "actor_at_mark"
    EXECUTING_CUE = "executing_cue"
    PERFORMANCE_COMPLETE = "performance_complete"


@dataclass
class DirectorStatus:
    """Status information from the Theater Director."""
    current_state: DirectorState
    current_act: Optional[int]
    actor_position: Optional[Tuple[int, int]]
    target_position: Optional[Tuple[int, int]]
    distance_to_target: Optional[float]
    last_cue_executed: Optional[str]


class TheaterDirector:
    """
    The Director - Observer and Cue Coordinator.
    
    Monitors the Voyager's position relative to the Playbook's marks
    and coordinates with the StageManager to execute scene transitions.
    No longer directly controls movement - purely observational.
    """
    
    def __init__(self, playbook: 'Playbook', stage_manager: 'StageManager'):
        """
        Initialize the Theater Director.
        
        Args:
            playbook: The script containing acts and cues
            stage_manager: The stagehand for world mutations
        """
        self.playbook = playbook
        self.stage_manager = stage_manager
        
        # Director state
        self.current_state = DirectorState.WAITING_FOR_ACTOR
        self.current_act: Optional['Act'] = None
        
        # Navigation and simulation references
        self.navigation_system: Optional['NavigationSystem'] = None
        self.simulator: Optional['SimulatorHost'] = None
        
        # Tracking
        self.last_known_position: Optional[Tuple[int, int]] = None
        self.last_cue_executed: Optional[str] = None
        self.performance_start_time: Optional[float] = None
        
        logger.info("🎬 Theater Director initialized - ready to observe performance")
    
    def set_navigation_system(self, navigation_system: 'NavigationSystem') -> None:
        """Set the navigation system reference."""
        self.navigation_system = navigation_system
        logger.debug("🎬 Director navigation system reference set")
    
    def set_simulator(self, simulator: 'SimulatorHost') -> None:
        """Set the simulator host reference."""
        self.simulator = simulator
        logger.debug("🎬 Director simulator reference set")
    
    def begin_performance(self) -> bool:
        """
        Begin the theatrical performance.
        
        Returns:
            True if performance started successfully
        """
        if self.playbook.is_performance_complete:
            logger.warning("🎬 Playbook already complete")
            return False
        
        # Reset and start
        self.playbook.reset_performance()
        self.current_state = DirectorState.WAITING_FOR_ACTOR
        self.current_act = self.playbook.get_current_act()
        self.performance_start_time = self._get_current_time()
        
        if self.current_act:
            logger.info(f"🎬 Performance begun! Act {self.current_act.act_number}: {self.current_act.scene_type.value}")
            logger.info(f"🎯 Target position: {self.current_act.target_position}")
            return True
        
        logger.error("🎬 No current act available to start performance")
        return False
    
    def observe_actor_position(self, position: Tuple[int, int]) -> DirectorStatus:
        """
        Observe the actor's position and update director state.
        
        Args:
            position: Current position of the Voyager actor
            
        Returns:
            Current director status
        """
        self.last_known_position = position
        
        # Get current act information
        current_act = self.playbook.get_current_act()
        if not current_act:
            self.current_state = DirectorState.PERFORMANCE_COMPLETE
            return self._create_status()
        
        # Calculate distance to target
        target_pos = current_act.target_position
        distance = self._calculate_distance(position, target_pos)
        
        # Check if actor is at the mark
        is_at_mark = position == target_pos
        
        # Update state based on actor position
        if is_at_mark:
            if self.current_state != DirectorState.ACTOR_AT_MARK:
                logger.info(f"🎯 Actor at mark! Position: {position} (Act {current_act.act_number})")
                self.current_state = DirectorState.ACTOR_AT_MARK
                self._execute_arrival_cue(current_act, position)
        else:
            if self.current_state == DirectorState.ACTOR_AT_MARK:
                # Actor moved away from mark
                logger.debug(f"🎯 Actor moved away from mark: {position}")
                self.current_state = DirectorState.WAITING_FOR_ACTOR
            elif self.current_state == DirectorState.WAITING_FOR_ACTOR:
                # Still waiting for actor to reach mark
                logger.debug(f"🎯 Actor approaching mark: {position} (distance: {distance})")
        
        return self._create_status()
    
    def _execute_arrival_cue(self, act: 'Act', actor_position: Tuple[int, int]) -> None:
        """
        Execute the arrival cue for the current act.
        
        Args:
            act: The current act
            actor_position: Position where actor arrived
        """
        logger.info(f"🎭 Executing arrival cue for Act {act.act_number}: {act.on_arrival_cue}")
        
        self.current_state = DirectorState.EXECUTING_CUE
        
        # Execute the cue through stage manager
        success = self.stage_manager.execute_cue(act.on_arrival_cue, actor_position)
        
        if success:
            self.last_cue_executed = act.on_arrival_cue
            
            # Trigger narrative with act's tags
            if self.simulator:
                self.simulator.trigger_narrative_with_tags(
                    act.narrative_tags,
                    act.scene_description
                )
            
            # Mark act complete and advance
            self.playbook.mark_current_act_complete()
            
            # Check if performance is complete
            if self.playbook.is_performance_complete:
                self.current_state = DirectorState.PERFORMANCE_COMPLETE
                logger.info("🎬 Performance complete! All acts finished.")
            else:
                # Advance to next act
                if self.playbook.advance_to_next_act():
                    next_act = self.playbook.get_current_act()
                    if next_act:
                        logger.info(f"🎭 Advanced to Act {next_act.act_number}: {next_act.scene_type.value}")
                        logger.info(f"🎯 New target: {next_act.target_position}")
                        self.current_state = DirectorState.WAITING_FOR_ACTOR
                else:
                    logger.warning("🎬 Failed to advance to next act")
                    self.current_state = DirectorState.PERFORMANCE_COMPLETE
        else:
            logger.error(f"💥 Failed to execute cue: {act.on_arrival_cue}")
            self.current_state = DirectorState.WAITING_FOR_ACTOR
    
    def _calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _get_current_time(self) -> float:
        """Get current time (placeholder implementation)."""
        import time
        return time.time()
    
    def _create_status(self) -> DirectorStatus:
        """Create current director status."""
        current_act = self.playbook.get_current_act()
        target_pos = current_act.target_position if current_act else None
        
        distance = None
        if self.last_known_position and target_pos:
            distance = self._calculate_distance(self.last_known_position, target_pos)
        
        return DirectorStatus(
            current_state=self.current_state,
            current_act=current_act.act_number if current_act else None,
            actor_position=self.last_known_position,
            target_position=target_pos,
            distance_to_target=distance,
            last_cue_executed=self.last_cue_executed
        )
    
    def get_current_target(self) -> Optional[Tuple[int, int]]:
        """Get the current target position for the actor."""
        current_act = self.playbook.get_current_act()
        return current_act.target_position if current_act else None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the performance."""
        playbook_summary = self.playbook.get_performance_summary()
        director_status = self._create_status()
        
        performance_time = None
        if self.performance_start_time:
            performance_time = self._get_current_time() - self.performance_start_time
        
        return {
            "playbook": playbook_summary,
            "director": {
                "state": director_status.current_state.value,
                "last_cue": director_status.last_cue_executed,
                "performance_time_seconds": performance_time
            },
            "current_target": self.get_current_target(),
            "active_effects": len(self.stage_manager.get_active_effects())
        }
    
    def force_advance_act(self) -> bool:
        """
        Force advance to the next act (for testing/debugging).
        
        Returns:
            True if successfully advanced
        """
        logger.warning("🎬 Forcing act advance (debug mode)")
        
        current_act = self.playbook.get_current_act()
        if current_act and self.last_known_position:
            self._execute_arrival_cue(current_act, self.last_known_position)
            return True
        
        return False
    
    def reset_performance(self) -> None:
        """Reset the entire performance."""
        self.playbook.reset_performance()
        self.current_state = DirectorState.WAITING_FOR_ACTOR
        self.current_act = self.playbook.get_current_act()
        self.last_known_position = None
        self.last_cue_executed = None
        self.performance_start_time = None
        self.stage_manager.clear_all_effects()
        
        logger.info("🔄 Theater Director performance reset")


# Factory for creating theater directors
class TheaterDirectorFactory:
    """Factory for creating theater directors with proper dependencies."""
    
    @staticmethod
    def create_director(playbook: 'Playbook', stage_manager: 'StageManager') -> TheaterDirector:
        """Create a theater director with required dependencies."""
        return TheaterDirector(playbook, stage_manager)
    
    @staticmethod
    def create_tavern_voyage_director() -> Tuple[TheaterDirector, 'Playbook', 'StageManager']:
        """Create a complete Tavern Voyage production setup."""
        try:
            from src.logic.playbook import PlaybookFactory
            from src.core.stage_manager import StageManagerFactory
        except ImportError:
            from logic.playbook import PlaybookFactory
            from core.stage_manager import StageManagerFactory
        
        # Create components
        playbook = PlaybookFactory.create_tavern_voyage()
        stage_manager = StageManagerFactory.create_stage_manager()
        director = TheaterDirectorFactory.create_director(playbook, stage_manager)
        
        logger.info("🎬 Tavern Voyage production created")
        return director, playbook, stage_manager
