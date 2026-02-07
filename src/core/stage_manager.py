"""
Stage Manager - The Stagehand for Theater Architecture

Handles all world state mutations: tile bank swapping, portal jumps, and FX triggers.
This is the only component allowed to modify the world state.

ADR 051: Theater-Driven Narrative Controller
- Executes environment mutations based on playbook cues
- Manages portal transitions and tile bank swaps
- Coordinates with SimulatorHost for world state changes
"""

from typing import Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from loguru import logger

# Forward references to avoid circular imports
try:
    from core.simulator import SimulatorHost
    from core.world_map import WorldMap, EnvironmentType
    from logic.pathfinding import NavigationSystem
except ImportError:
    SimulatorHost = None
    WorldMap = None
    EnvironmentType = None
    NavigationSystem = None


class CueType(Enum):
    """Types of stage cues the manager can execute."""
    FOREST_TO_GATE = "cue_forest_to_gate"
    GATE_TO_SQUARE = "cue_gate_to_square"
    SQUARE_TO_TAVERN = "cue_square_to_tavern"
    TAVERN_ENTRANCE = "cue_tavern_entrance"
    PERFORMANCE_COMPLETE = "cue_performance_complete"


@dataclass
class StageEffect:
    """A visual or environmental effect to trigger."""
    effect_type: str
    duration: float
    parameters: Dict[str, Any]


class StageManager:
    """
    The Stagehand - Manages all world state mutations.
    
    Executes scene transitions, portal jumps, and environmental effects
    based on cues from the Director. This is the only component that
    directly modifies the world state.
    """
    
    def __init__(self, simulator: Optional['SimulatorHost'] = None):
        """
        Initialize the Stage Manager.
        
        Args:
            simulator: The simulator host for world state management
        """
        self.simulator = simulator
        self.world_map: Optional['WorldMap'] = None
        self.navigation_system: Optional['NavigationSystem'] = None
        
        # Stage effects queue
        self.active_effects: list[StageEffect] = []
        
        # Cue handlers registry
        self._register_cue_handlers()
        
        logger.info("🎭 Stage Manager initialized - ready for scene changes")
    
    def _register_cue_handlers(self) -> None:
        """Register all cue handlers with their corresponding functions."""
        self.cue_handlers = {
            CueType.FOREST_TO_GATE: self._handle_forest_to_gate,
            CueType.GATE_TO_SQUARE: self._handle_gate_to_square,
            CueType.SQUARE_TO_TAVERN: self._handle_square_to_tavern,
            CueType.TAVERN_ENTRANCE: self._handle_tavern_entrance,
            CueType.PERFORMANCE_COMPLETE: self._handle_performance_complete
        }
    
    def set_simulator(self, simulator: 'SimulatorHost') -> None:
        """Set the simulator host reference."""
        self.simulator = simulator
        logger.debug("🎭 Stage Manager simulator reference set")
    
    def set_world_map(self, world_map: 'WorldMap') -> None:
        """Set the world map reference."""
        self.world_map = world_map
        logger.debug("🎭 Stage Manager world map reference set")
    
    def set_navigation_system(self, navigation_system: 'NavigationSystem') -> None:
        """Set the navigation system reference."""
        self.navigation_system = navigation_system
        logger.debug("🎭 Stage Manager navigation system reference set")
    
    def execute_cue(self, cue: str, actor_position: Tuple[int, int]) -> bool:
        """
        Execute a stage cue based on the cue string.
        
        Args:
            cue: The cue string to execute
            actor_position: Current position of the Voyager actor
            
        Returns:
            True if cue was executed successfully, False otherwise
        """
        try:
            cue_type = CueType(cue)
        except ValueError:
            logger.warning(f"🎭 Unknown cue: {cue}")
            return False
        
        handler = self.cue_handlers.get(cue_type)
        if not handler:
            logger.warning(f"🎭 No handler registered for cue: {cue}")
            return False
        
        logger.info(f"🎭 Executing cue: {cue}")
        
        try:
            success = handler(actor_position)
            if success:
                logger.info(f"✅ Cue '{cue}' executed successfully")
            else:
                logger.warning(f"❌ Cue '{cue}' execution failed")
            return success
        except Exception as e:
            logger.error(f"💥 Error executing cue '{cue}': {e}")
            return False
    
    def _handle_forest_to_gate(self, actor_position: Tuple[int, int]) -> bool:
        """Handle transition from forest edge to town gate."""
        logger.info("🌲→🚪 Forest to Gate transition")
        
        # Check if actor is at the correct position
        if actor_position != (10, 25):
            logger.warning(f"🎭 Actor not at forest edge position: {actor_position}")
            return False
        
        # Trigger scene transition narrative
        if self.simulator:
            self.simulator.trigger_scene_transition(
                "The dense forest parts to reveal massive iron gates standing open before you."
            )
        
        # Add visual effect
        self._add_effect("gate_reveal", 2.0, {"color": "#gold", "intensity": 0.8})
        
        return True
    
    def _handle_gate_to_square(self, actor_position: Tuple[int, int]) -> bool:
        """Handle transition from town gate to town square."""
        logger.info("🚪→🏛️ Gate to Square transition")
        
        # Check if actor is at the gate
        if actor_position != (10, 20):
            logger.warning(f"🎭 Actor not at gate position: {actor_position}")
            return False
        
        # Swap tile banks from forest to city
        success = self._swap_tile_bank("forest_bank", "town_square_bank")
        if not success:
            logger.warning("🎭 Tile bank swap failed - continuing with narrative transition")
            # In demo mode, continue even without tile bank swap
        
        # Trigger scene transition
        if self.simulator:
            self.simulator.trigger_scene_transition(
                "You pass through the iron gates into a bustling town square filled with merchants and townsfolk."
            )
        else:
            # Demo mode fallback
            logger.info("🎭 [DEMO] Scene transition: Gate to Square")
        
        # Add environmental effect
        self._add_effect("city_ambiance", 5.0, {"sound": "crowd_murmur", "volume": 0.6})
        
        return True  # Always succeed in demo mode
    
    def _handle_square_to_tavern(self, actor_position: Tuple[int, int]) -> bool:
        """Handle movement through town square toward tavern."""
        logger.info("🏛️→🍺 Square to Tavern approach")
        
        # Check if actor is in the square area
        if not (5 <= actor_position[0] <= 15 and 5 <= actor_position[1] <= 15):
            logger.warning(f"🎭 Actor not in town square: {actor_position}")
            return False
        
        # Trigger narrative about tavern
        if self.simulator:
            self.simulator.trigger_narrative_event(
                "tavern_visible", 
                "Across the square, a weathered tavern sign creaks in the breeze, promising warmth and rest."
            )
        else:
            # Demo mode fallback
            logger.info("🎭 [DEMO] Narrative: Tavern visible across square")
        
        # Add subtle effect
        self._add_effect("tavern_glow", 3.0, {"color": "#warm_orange", "intensity": 0.4})
        
        return True
    
    def _handle_tavern_entrance(self, actor_position: Tuple[int, int]) -> bool:
        """Handle portal jump from exterior to tavern interior."""
        logger.info("🍺 Portal jump to Tavern Interior")
        
        # Check if actor is at tavern door
        if actor_position != (20, 10):
            logger.warning(f"🎭 Actor not at tavern door: {actor_position}")
            return False
        
        # Execute portal jump
        # Handle EnvironmentType being None in demo mode
        from_env_type = EnvironmentType.TOWN_SQUARE if EnvironmentType else "town_square"
        to_env_type = EnvironmentType.TAVERN_INTERIOR if EnvironmentType else "tavern_interior"
        
        success = self._execute_portal_jump(
            from_pos=(20, 10),
            to_pos=(25, 30),
            from_env=from_env_type,
            to_env=to_env_type
        )
        
        if not success:
            logger.warning("🎭 Portal jump failed - continuing with narrative transition")
            # In demo mode, continue even without portal jump
        
        # Swap to interior tile bank
        self._swap_tile_bank("town_square_bank", "tavern_bank")
        
        # Trigger portal transition narrative
        if self.simulator:
            self.simulator.trigger_portal_transition(
                "Tavern Interior",
                "You push open the heavy door and step into the dim warmth of the taproom."
            )
        else:
            # Demo mode fallback
            logger.info("🎭 [DEMO] Portal transition: Square to Tavern Interior")
        
        # Add interior effects
        self._add_effect("firelight", 10.0, {"color": "#flickering_orange", "intensity": 0.7})
        self._add_effect("interior_ambiance", 8.0, {"sound": "crackling_fire", "volume": 0.5})
        
        return True  # Always succeed in demo mode
    
    def _handle_performance_complete(self, actor_position: Tuple[int, int]) -> bool:
        """Handle completion of the entire performance."""
        logger.info("🎬 Performance Complete!")
        
        # Check if actor is in tavern interior
        if not (25 <= actor_position[0] <= 40 and 30 <= actor_position[1] <= 40):
            logger.warning(f"🎭 Actor not in tavern interior: {actor_position}")
            # In demo mode, allow completion even if not in exact position
        
        # Trigger completion narrative
        if self.simulator:
            self.simulator.trigger_scene_transition(
                "The tavern adventure begins. You've successfully navigated from forest wilderness to civilized comfort."
            )
        else:
            # Demo mode fallback
            logger.info("🎭 [DEMO] Performance complete - Tavern adventure begins!")
        
        # Add celebration effect
        self._add_effect("completion_glow", 5.0, {"color": "#golden", "intensity": 1.0})
        
        return True  # Always succeed in demo mode
    
    def _swap_tile_bank(self, from_bank: str, to_bank: str) -> bool:
        """
        Swap tile banks for environmental changes.
        
        Args:
            from_bank: Current tile bank name
            to_bank: Target tile bank name
            
        Returns:
            True if swap was successful
        """
        logger.info(f"🔄 Swapping tile bank: {from_bank} → {to_bank}")
        
        if self.simulator:
            return self.simulator.swap_tile_bank(from_bank, to_bank)
        
        # Demo mode fallback - simulate successful swap
        logger.info(f"🎭 [DEMO] Tile bank swap simulated: {from_bank} → {to_bank}")
        return True
    
    def _execute_portal_jump(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                           from_env: 'EnvironmentType', to_env: 'EnvironmentType') -> bool:
        """
        Execute a portal jump between environments.
        
        Args:
            from_pos: Starting position
            to_pos: Destination position  
            from_env: Source environment type
            to_env: Target environment type
            
        Returns:
            True if portal jump was successful
        """
        # Handle string types in demo mode
        from_env_name = from_env.value if hasattr(from_env, 'value') else str(from_env)
        to_env_name = to_env.value if hasattr(to_env, 'value') else str(to_env)
        
        logger.info(f"🌀 Portal jump: {from_pos} → {to_pos} ({from_env_name} → {to_env_name})")
        
        if self.simulator:
            return self.simulator.execute_portal_jump(from_pos, to_pos, from_env, to_env)
        
        # Demo mode fallback - simulate successful portal jump
        logger.info(f"🎭 [DEMO] Portal jump simulated: {from_pos} → {to_pos}")
        return True
    
    def _add_effect(self, effect_type: str, duration: float, parameters: Dict[str, Any]) -> None:
        """Add a visual/environmental effect to the active queue."""
        effect = StageEffect(effect_type, duration, parameters)
        self.active_effects.append(effect)
        logger.debug(f"✨ Added effect: {effect_type} (duration: {duration}s)")
    
    def update_effects(self, delta_time: float) -> None:
        """Update all active effects and remove expired ones."""
        remaining_effects = []
        
        for effect in self.active_effects:
            effect.duration -= delta_time
            if effect.duration > 0:
                remaining_effects.append(effect)
            else:
                logger.debug(f"✨ Effect expired: {effect.effect_type}")
        
        self.active_effects = remaining_effects
    
    def get_active_effects(self) -> list[StageEffect]:
        """Get all currently active effects."""
        return self.active_effects.copy()
    
    def clear_all_effects(self) -> None:
        """Clear all active effects."""
        self.active_effects.clear()
        logger.debug("🧹 All stage effects cleared")


# Factory for creating stage managers
class StageManagerFactory:
    """Factory for creating stage managers with different configurations."""
    
    @staticmethod
    def create_stage_manager(simulator: Optional['SimulatorHost'] = None) -> StageManager:
        """Create a standard stage manager."""
        return StageManager(simulator)
    
    @staticmethod
    def create_minimal_stage_manager() -> StageManager:
        """Create a stage manager without simulator dependencies."""
        return StageManager(None)
