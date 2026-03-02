"""
SceneContext - Data carrier for scene-ECS interaction
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.state.entity_registry import EntityRegistry
    from src.shared.session.game_session import GameSession
    from src.shared.dispatch.dispatch_system import DispatchSystem
    from src.shared.ui.theme import UITheme


@dataclass
class SceneContext:
    """
    Everything a scene needs to interact with the ECS world.
    Passed explicitly. Replaces ad-hoc kwargs and direct state access.
    
    SceneContext is optional everywhere. Scenes that don't need ECS access
    don't need it. Scenes that do have a clean interface instead of reaching
    into internals.
    """
    entity_registry: Optional['EntityRegistry'] = None
    game_session: Optional['GameSession'] = None
    dispatch_system: Optional['DispatchSystem'] = None
    roster: Any = None
    theme: Optional['UITheme'] = None
    
    # Convenience accessors
    def get_team(self, role: str) -> List[Any]:
        """Get team members by role"""
        if self.entity_registry and hasattr(self.entity_registry, 'get_team'):
            return self.entity_registry.get_team(role)
        elif self.roster and hasattr(self.roster, f'get_{role}_team'):
            team = getattr(self.roster, f'get_{role}_team')()
            return team.members if team else []
        return []
    
    def get_entity(self, entity_id: str) -> Any:
        """Get entity by ID"""
        if self.entity_registry:
            return self.entity_registry.get(entity_id)
        return None
    
    def add_resource(self, resource: str, amount: int) -> bool:
        """Add resources to game session"""
        if self.game_session and hasattr(self.game_session, 'resources'):
            current = self.game_session.resources.get(resource, 0)
            self.game_session.resources[resource] = current + amount
            return True
        return False
    
    def get_resource(self, resource: str) -> int:
        """Get resource amount from game session"""
        if self.game_session and hasattr(self.game_session, 'resources'):
            return self.game_session.resources.get(resource, 0)
        return 0
    
    def get_entities(self) -> List[Any]:
        """Get all entities from registry"""
        if self.entity_registry and hasattr(self.entity_registry, 'get_all'):
            return self.entity_registry.get_all()
        return []
    
    def create_entity(self, entity_type: str, **kwargs) -> Any:
        """Create entity through registry"""
        if self.entity_registry and hasattr(self.entity_registry, 'create'):
            return self.entity_registry.create(entity_type, **kwargs)
        return None
    
    def remove_entity(self, entity_id: str) -> bool:
        """Remove entity through registry"""
        if self.entity_registry and hasattr(self.entity_registry, 'remove'):
            return self.entity_registry.remove(entity_id)
        return False
