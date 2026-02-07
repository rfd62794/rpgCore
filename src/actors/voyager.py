"""
Voyager - The Actor Pillar

Pathfinding, coordinate tracking, and intent generation.
Autonomous navigation and decision making.
"""

import time
from typing import Tuple, List, Dict, Any, Union, Optional
from dataclasses import dataclass

from loguru import logger

# Import from engines
from ..engines.dd_engine import (
    DD_Engine, GameState, MovementIntent, InteractionIntent, 
    IntentValidation, ValidationResult
)


@dataclass
class NavigationGoal:
    """Navigation goal for the Voyager"""
    target_position: Tuple[int, int]
    priority: int = 1
    timeout: float = 30.0
    created_time: float = 0.0
    
    def __post_init__(self):
        if self.created_time == 0.0:
            self.created_time = time.time()
    
    def is_expired(self) -> bool:
        """Check if goal has expired"""
        return time.time() - self.created_time > self.timeout


class PathfindingNavigator:
    """A* pathfinding and navigation logic"""
    
    def __init__(self, grid_width: int = 50, grid_height: int = 50):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.collision_map = [[False for _ in range(grid_width)] for _ in range(grid_height)]
        
        logger.info(f"🧭 Pathfinding Navigator initialized: {grid_width}x{grid_height}")
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int], 
                   collision_map: Optional[List[List[bool]]] = None) -> List[Tuple[int, int]]:
        """Find path from start to goal using A* algorithm"""
        if collision_map:
            self.collision_map = collision_map
        
        # Simple pathfinding implementation (placeholder for A*)
        path = self._simple_pathfinding(start, goal)
        
        if path:
            logger.debug(f"🛤️ Path found: {len(path)} steps from {start} to {goal}")
        else:
            logger.warning(f"❌ No path found from {start} to {goal}")
        
        return path
    
    def _simple_pathfinding(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Simple pathfinding implementation (straight line for now)"""
        # Placeholder for actual A* implementation
        # For now, return direct path if valid
        
        if not self._is_valid_position(goal):
            return []
        
        # Simple straight-line path
        path = []
        current = start
        
        while current != goal:
            # Move one step toward goal
            dx = 1 if goal[0] > current[0] else -1 if goal[0] < current[0] else 0
            dy = 1 if goal[1] > current[1] else -1 if goal[1] < current[1] else 0
            
            next_pos = (current[0] + dx, current[1] + dy)
            
            if self._is_valid_position(next_pos):
                path.append(next_pos)
                current = next_pos
            else:
                # Try alternative path
                if dx != 0 and self._is_valid_position((current[0] + dx, current[1])):
                    path.append((current[0] + dx, current[1]))
                    current = (current[0] + dx, current[1])
                elif dy != 0 and self._is_valid_position((current[0], current[1] + dy)):
                    path.append((current[0], current[1] + dy))
                    current = (current[0], current[1] + dy)
                else:
                    break  # No valid path
        
        return path
    
    def _is_valid_position(self, position: Tuple[int, int]) -> bool:
        """Check if position is valid within grid"""
        x, y = position
        
        if y < 0 or y >= self.grid_height:
            return False
        if x < 0 or x >= self.grid_width:
            return False
        
        return not self.collision_map[y][x]  # False = walkable, True = obstacle
    
    def update_collision_map(self, collision_map: List[List[bool]]) -> None:
        """Update collision map from D&D Engine"""
        self.collision_map = collision_map


class IntentGenerator:
    """Generate intents based on goals and current state"""
    
    def __init__(self, navigator: PathfindingNavigator):
        self.navigator = navigator
        self.current_goals: List[NavigationGoal] = []
        
        logger.info("🎯 Intent Generator initialized")
    
    def add_goal(self, goal: NavigationGoal) -> None:
        """Add navigation goal"""
        self.current_goals.append(goal)
        logger.debug(f"📍 Goal added: {goal.target_position}")
    
    def generate_movement_intent(self, current_position: Tuple[int, int], 
                                target_position: Tuple[int, int],
                                collision_map: Optional[List[List[bool]]] = None) -> MovementIntent:
        """Generate movement intent for target position"""
        # Update collision map if provided
        if collision_map:
            self.navigator.update_collision_map(collision_map)
        
        # Calculate path
        path = self.navigator.find_path(current_position, target_position)
        
        if not path:
            raise ValueError(f"No path found to {target_position}")
        
        # Calculate confidence based on path quality
        confidence = self._calculate_path_confidence(path)
        
        return MovementIntent(
            target_position=target_position,
            path=path,
            confidence=confidence,
            timestamp=time.time()
        )
    
    def generate_interaction_intent(self, target_entity: str, interaction_type: str,
                                   parameters: Optional[Dict[str, Any]] = None) -> InteractionIntent:
        """Generate interaction intent for entity"""
        return InteractionIntent(
            target_entity=target_entity,
            interaction_type=interaction_type,
            parameters=parameters or {},
            timestamp=time.time()
        )
    
    def get_next_goal(self) -> Optional[NavigationGoal]:
        """Get highest priority active goal"""
        if not self.current_goals:
            return None
        
        # Remove expired goals
        self.current_goals = [goal for goal in self.current_goals if not goal.is_expired()]
        
        if not self.current_goals:
            return None
        
        # Sort by priority (higher first)
        self.current_goals.sort(key=lambda g: g.priority, reverse=True)
        
        return self.current_goals[0]
    
    def _calculate_path_confidence(self, path: List[Tuple[int, int]]) -> float:
        """Calculate confidence score for path"""
        if not path:
            return 0.0
        
        # Base confidence on path length and complexity
        base_confidence = 1.0
        
        # Longer paths have slightly lower confidence
        length_penalty = min(len(path) * 0.01, 0.3)
        
        # Straight paths have higher confidence
        straightness_bonus = self._calculate_path_straightness(path) * 0.2
        
        confidence = base_confidence - length_penalty + straightness_bonus
        return max(0.1, min(1.0, confidence))
    
    def _calculate_path_straightness(self, path: List[Tuple[int, int]]) -> float:
        """Calculate how straight the path is"""
        if len(path) < 2:
            return 1.0
        
        # Calculate total path length
        total_length = len(path)
        
        # Calculate direct distance
        start = path[0]
        end = path[-1]
        direct_distance = abs(end[0] - start[0]) + abs(end[1] - start[1])
        
        # Straightness ratio
        if direct_distance == 0:
            return 1.0
        
        return direct_distance / total_length


class Voyager:
    """Pathfinding and intent generation - The Actor Pillar"""
    
    def __init__(self, dd_engine: DD_Engine):
        self.dd_engine = dd_engine
        self.navigator = PathfindingNavigator()
        self.intent_generator = IntentGenerator(self.navigator)
        
        # Navigation state
        self.current_position: Tuple[int, int] = (10, 25)
        self.last_intent_time: float = 0.0
        self.intent_cooldown: float = 0.1  # 100ms between intents
        
        logger.info("🚶 Voyager initialized - Actor Pillar ready")
    
    def update_position(self, new_position: Tuple[int, int]) -> None:
        """Update current position from D&D Engine state"""
        self.current_position = new_position
    
    def generate_movement_intent(self, target: Tuple[int, int]) -> MovementIntent:
        """Generate movement intent for target position"""
        current_state = self.dd_engine.get_current_state()
        collision_map = self.dd_engine.assets.get_collision_map(current_state.current_environment)
        
        return self.intent_generator.generate_movement_intent(
            self.current_position, target, collision_map
        )
    
    def generate_interaction_intent(self, entity: str, interaction_type: str,
                                   parameters: Optional[Dict[str, Any]] = None) -> InteractionIntent:
        """Generate interaction intent for entity"""
        return self.intent_generator.generate_interaction_intent(entity, interaction_type, parameters)
    
    def submit_intent(self, intent: Union[MovementIntent, InteractionIntent]) -> bool:
        """Submit intent to D&D Engine and handle response"""
        # Check intent cooldown
        current_time = time.time()
        if current_time - self.last_intent_time < self.intent_cooldown:
            logger.debug("⏱️ Intent cooldown - waiting")
            return False
        
        self.last_intent_time = current_time
        
        # Validate intent
        validation = self.dd_engine.process_intent(intent)
        
        if not validation.is_valid:
            logger.warning(f"❌ Intent rejected: {validation.validation_result.value} - {validation.message}")
            return False
        
        # Execute intent
        try:
            new_state = self.dd_engine.execute_validated_intent(intent)
            
            # Update internal position
            self.update_position(new_state.player_position)
            
            logger.info(f"✅ Intent executed successfully: {intent.intent_type}")
            return True
            
        except Exception as e:
            logger.error(f"💥 Intent execution failed: {e}")
            return False
    
    def navigate_to_position(self, target_position: Tuple[int, int]) -> bool:
        """Navigate to target position using pathfinding"""
        logger.info(f"🧭 Navigating to {target_position}")
        
        try:
            # Generate movement intent
            intent = self.generate_movement_intent(target_position)
            
            # Submit intent
            success = self.submit_intent(intent)
            
            if success:
                logger.info(f"🎯 Navigation successful: {self.current_position} → {target_position}")
            else:
                logger.warning(f"❌ Navigation failed: {target_position}")
            
            return success
            
        except Exception as e:
            logger.error(f"💥 Navigation error: {e}")
            return False
    
    def interact_with_entity(self, entity: str, interaction_type: str,
                           parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Interact with entity at current position"""
        logger.info(f"🤝 Interacting with {entity}: {interaction_type}")
        
        try:
            # Generate interaction intent
            intent = self.generate_interaction_intent(entity, interaction_type, parameters)
            
            # Submit intent
            success = self.submit_intent(intent)
            
            if success:
                logger.info(f"✅ Interaction successful: {entity}")
            else:
                logger.warning(f"❌ Interaction failed: {entity}")
            
            return success
            
        except Exception as e:
            logger.error(f"💥 Interaction error: {e}")
            return False
    
    def add_navigation_goal(self, target_position: Tuple[int, int], priority: int = 1,
                           timeout: float = 30.0) -> None:
        """Add navigation goal to intent generator"""
        goal = NavigationGoal(
            target_position=target_position,
            priority=priority,
            timeout=timeout
        )
        self.intent_generator.add_goal(goal)
    
    def process_next_goal(self) -> bool:
        """Process the next highest priority goal"""
        goal = self.intent_generator.get_next_goal()
        
        if not goal:
            return False
        
        logger.debug(f"🎯 Processing goal: {goal.target_position}")
        return self.navigate_to_position(goal.target_position)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Voyager status"""
        current_state = self.dd_engine.get_current_state()
        
        return {
            "position": self.current_position,
            "health": current_state.player_health,
            "environment": current_state.current_environment,
            "active_goals": len(self.intent_generator.current_goals),
            "last_intent_time": self.last_intent_time
        }


# Factory for creating Voyager instances
class VoyagerFactory:
    """Factory for creating Voyager instances"""
    
    @staticmethod
    def create_voyager(dd_engine: DD_Engine) -> Voyager:
        """Create a Voyager with default configuration"""
        return Voyager(dd_engine)
    
    @staticmethod
    def create_test_voyager() -> Voyager:
        """Create a Voyager for testing"""
        from ..engines.dd_engine import DDEngineFactory
        test_engine = DDEngineFactory.create_test_engine()
        return Voyager(test_engine)
