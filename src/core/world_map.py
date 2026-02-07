"""
World Map Registry - Geometric Sovereignty for DGT Perfect Simulator

This module implements the Spatial Authority Registry that defines the physical
geometry of the game world. It maps coordinate boundaries to asset prefabs
and handles deterministic transitions between areas.

ADR 049: The Spatial Authority Registry
- Defines hard coordinate boundaries for each environment
- Handles portal transitions and tile bank swapping
- Provides physical landmarks for Director beacon placement
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Types of environments in the world."""
    TOWN_SQUARE = "town_square"
    TAVERN_INTERIOR = "tavern_interior"
    FOREST_PATH = "forest_path"
    OVERWORLD = "overworld"


@dataclass
class Boundary:
    """Defines a rectangular boundary for an environment."""
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    
    def contains(self, x: int, y: int) -> bool:
        """Check if coordinates are within this boundary."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y
    
    def get_center(self) -> Tuple[int, int]:
        """Get the center point of this boundary."""
        return ((self.min_x + self.max_x) // 2, (self.min_y + self.max_y) // 2)
    
    def get_entry_point(self) -> Tuple[int, int]:
        """Get the designated entry point for this boundary."""
        return self.entry_point
    
    def get_size(self) -> Tuple[int, int]:
        """Get the size of this boundary."""
        return (self.max_x - self.min_x + 1, self.max_y - self.min_y + 1)


@dataclass
class Portal:
    """Defines a transition portal between two environments."""
    from_env: EnvironmentType
    to_env: EnvironmentType
    from_coords: Tuple[int, int]  # Trigger location
    to_coords: Tuple[int, int]    # Destination location
    name: str = "Portal"


@dataclass
class Landmark:
    """A physical landmark that can be used as a Director beacon target."""
    name: str
    env_type: EnvironmentType
    coords: Tuple[int, int]
    description: str
    interaction_type: Optional[str] = None  # "chest", "npc", "door", etc.


@dataclass
class EnvironmentZone:
    """Complete definition of an environment zone."""
    env_type: EnvironmentType
    name: str
    boundary: Boundary
    entry_point: Tuple[int, int]
    tile_bank: str  # Corresponds to assets.dgt tile bank
    landmarks: List[Landmark]
    exits: List[Portal]
    
    def __post_init__(self):
        """Set entry point in boundary."""
        self.boundary.entry_point = self.entry_point


class WorldMap:
    """
    The World Map Registry - Master Geometry of the DGT World
    
    This class maintains the spatial authority over all environments,
    handling transitions, boundary checks, and landmark management.
    """
    
    def __init__(self):
        """Initialize the world map with predefined zones."""
        self.zones: Dict[EnvironmentType, EnvironmentZone] = {}
        self.portals: List[Portal] = []
        self.landmarks: Dict[str, Landmark] = {}
        
        self._initialize_world_geometry()
        logger.info("🗺️ World Map initialized with geometric sovereignty")
    
    def _initialize_world_geometry(self) -> None:
        """Initialize the master coordinate map for all environments."""
        
        # Define Town Square (0, 0) to (20, 20)
        town_square_boundary = Boundary(0, 0, 20, 20)
        town_square_landmarks = [
            Landmark(
                name="North Gate",
                env_type=EnvironmentType.TOWN_SQUARE,
                coords=(10, 0),
                description="The grand northern entrance to the town square",
                interaction_type="exit"
            ),
            Landmark(
                name="Tavern Door",
                env_type=EnvironmentType.TOWN_SQUARE,
                coords=(20, 10),
                description="Heavy wooden door leading to the tavern",
                interaction_type="portal"
            ),
            Landmark(
                name="Town Well",
                env_type=EnvironmentType.TOWN_SQUARE,
                coords=(10, 10),
                description="Stone well in the center of the square",
                interaction_type="object"
            )
        ]
        
        self.zones[EnvironmentType.TOWN_SQUARE] = EnvironmentZone(
            env_type=EnvironmentType.TOWN_SQUARE,
            name="Town Square",
            boundary=town_square_boundary,
            entry_point=(10, 0),  # North Gate
            tile_bank="town_square_bank",
            landmarks=town_square_landmarks,
            exits=[]
        )
        
        # Define Tavern Interior (25, 30) to (40, 40) - Expanded for interior movement
        tavern_boundary = Boundary(25, 30, 40, 40)
        tavern_landmarks = [
            Landmark(
                name="Tavern Entrance",
                env_type=EnvironmentType.TAVERN_INTERIOR,
                coords=(25, 30),
                description="Heavy wooden door leading from the town square",
                interaction_type="portal"
            ),
            Landmark(
                name="Tavern Chest",
                env_type=EnvironmentType.TAVERN_INTERIOR,
                coords=(32, 32),
                description="Heavy iron chest bound with ancient runes, filled with treasure",
                interaction_type="chest"
            ),
            Landmark(
                name="Bar Counter",
                env_type=EnvironmentType.TAVERN_INTERIOR,
                coords=(35, 35),
                description="Long wooden bar where the bartender serves drinks",
                interaction_type="npc"
            ),
            Landmark(
                name="Hearth",
                env_type=EnvironmentType.TAVERN_INTERIOR,
                coords=(30, 32),
                description="Warm stone fireplace with crackling flames",
                interaction_type="object"
            ),
            Landmark(
                name="Wooden Tables",
                env_type=EnvironmentType.TAVERN_INTERIOR,
                coords=(30, 38),
                description="Rough wooden tables where patrons sit and drink",
                interaction_type="object"
            )
        ]
        
        self.zones[EnvironmentType.TAVERN_INTERIOR] = EnvironmentZone(
            env_type=EnvironmentType.TAVERN_INTERIOR,
            name="Tavern Interior",
            boundary=tavern_boundary,
            entry_point=(25, 30),  # Door from outside
            tile_bank="tavern_bank",
            landmarks=tavern_landmarks,
            exits=[]
        )
        
        # Define Forest Path (0, 21) to (20, 40) - South of Town Square
        forest_boundary = Boundary(0, 21, 20, 40)
        forest_landmarks = [
            Landmark(
                name="South Exit",
                env_type=EnvironmentType.FOREST_PATH,
                coords=(10, 21),
                description="Path leading south from the town square",
                interaction_type="exit"
            ),
            Landmark(
                name="Ancient Oak",
                env_type=EnvironmentType.FOREST_PATH,
                coords=(10, 30),
                description="Massive oak tree with carved initials",
                interaction_type="object"
            ),
            Landmark(
                name="Hidden Chest",
                env_type=EnvironmentType.FOREST_PATH,
                coords=(15, 35),
                description="Wooden chest concealed under foliage",
                interaction_type="chest"
            )
        ]
        
        self.zones[EnvironmentType.FOREST_PATH] = EnvironmentZone(
            env_type=EnvironmentType.FOREST_PATH,
            name="Forest Path",
            boundary=forest_boundary,
            entry_point=(10, 21),  # South entrance from town
            tile_bank="forest_bank",
            landmarks=forest_landmarks,
            exits=[]
        )
        
        # Define portals between zones
        self.portals = [
            Portal(
                from_env=EnvironmentType.TOWN_SQUARE,
                to_env=EnvironmentType.TAVERN_INTERIOR,
                from_coords=(20, 10),  # Tavern door in square
                to_coords=(25, 30),     # Inside tavern entrance
                name="Tavern Entrance"
            ),
            Portal(
                from_env=EnvironmentType.TAVERN_INTERIOR,
                to_env=EnvironmentType.TOWN_SQUARE,
                from_coords=(25, 30),   # Inside tavern entrance
                to_coords=(20, 10),     # Outside tavern door
                name="Tavern Exit"
            ),
            Portal(
                from_env=EnvironmentType.TOWN_SQUARE,
                to_env=EnvironmentType.FOREST_PATH,
                from_coords=(10, 20),   # South gate
                to_coords=(10, 21),     # Forest path entrance
                name="South Gate"
            ),
            Portal(
                from_env=EnvironmentType.FOREST_PATH,
                to_env=EnvironmentType.TOWN_SQUARE,
                from_coords=(10, 21),   # Forest path entrance
                to_coords=(10, 20),     # South gate
                name="North Gate"
            )
        ]
        
        # Build landmark registry
        for zone in self.zones.values():
            for landmark in zone.landmarks:
                self.landmarks[landmark.name] = landmark
        
        logger.info(f"🗺️ Defined {len(self.zones)} zones with {len(self.landmarks)} landmarks")
    
    def get_zone_at(self, x: int, y: int) -> Optional[EnvironmentZone]:
        """Get the environment zone at the given coordinates."""
        for zone in self.zones.values():
            if zone.boundary.contains(x, y):
                return zone
        return None
    
    def get_current_environment(self, x: int, y: int) -> Optional[EnvironmentType]:
        """Get the environment type at the given coordinates."""
        zone = self.get_zone_at(x, y)
        return zone.env_type if zone else None
    
    def get_landmarks_in_zone(self, env_type: EnvironmentType) -> List[Landmark]:
        """Get all landmarks within a specific environment."""
        zone = self.zones.get(env_type)
        return zone.landmarks if zone else []
    
    def get_landmark_at(self, x: int, y: int) -> Optional[Landmark]:
        """Get landmark at specific coordinates."""
        zone = self.get_zone_at(x, y)
        if zone:
            for landmark in zone.landmarks:
                if landmark.coords == (x, y):
                    return landmark
        return None
    
    def find_portal_at(self, x: int, y: int) -> Optional[Portal]:
        """Find portal at the given coordinates."""
        for portal in self.portals:
            if portal.from_coords == (x, y):
                return portal
        return None
    
    def get_landmark_by_name(self, name: str) -> Optional[Landmark]:
        """Get landmark by name."""
        return self.landmarks.get(name)
    
    def get_director_landmarks(self) -> List[Landmark]:
        """Get all landmarks suitable for Director beacon placement."""
        return [lm for lm in self.landmarks.values() 
                if lm.interaction_type in ["portal", "chest", "npc"]]
    
    def is_boundary_hit(self, x: int, y: int) -> bool:
        """Check if position hits any boundary or portal."""
        # Check for portal triggers
        portal = self.find_portal_at(x, y)
        if portal:
            return True
        
        # Check for boundary transitions
        current_zone = self.get_zone_at(x, y)
        if not current_zone:
            return False
        
        # Check if we're at a boundary edge
        return (x == current_zone.boundary.min_x or x == current_zone.boundary.max_x or
                y == current_zone.boundary.min_y or y == current_zone.boundary.max_y)
    
    def get_transition_target(self, x: int, y: int) -> Optional[Tuple[EnvironmentType, Tuple[int, int]]]:
        """Get the target environment and coordinates for a transition."""
        portal = self.find_portal_at(x, y)
        if portal:
            return (portal.to_env, portal.to_coords)
        return None
    
    def get_zone_entry_point(self, env_type: EnvironmentType) -> Optional[Tuple[int, int]]:
        """Get the entry point for a specific environment."""
        zone = self.zones.get(env_type)
        return zone.entry_point if zone else None
    
    def get_tile_bank_for_position(self, x: int, y: int) -> Optional[str]:
        """Get the tile bank for the given position."""
        zone = self.get_zone_at(x, y)
        return zone.tile_bank if zone else None
    
    def get_nearby_landmarks(self, x: int, y: int, radius: int = 3) -> List[Landmark]:
        """Get landmarks within radius of given position."""
        nearby = []
        zone = self.get_zone_at(x, y)
        if zone:
            for landmark in zone.landmarks:
                lm_x, lm_y = landmark.coords
                distance = abs(lm_x - x) + abs(lm_y - y)  # Manhattan distance
                if distance <= radius:
                    nearby.append(landmark)
        return nearby
    
    def validate_position(self, x: int, y: int) -> bool:
        """Validate that position is within a defined zone."""
        return self.get_zone_at(x, y) is not None


# Global world map instance
_world_map: Optional[WorldMap] = None


def get_world_map() -> WorldMap:
    """Get the global world map instance."""
    global _world_map
    if _world_map is None:
        _world_map = WorldMap()
    return _world_map


def create_world_map() -> WorldMap:
    """Create a new world map instance."""
    return WorldMap()
