"""
DGT Core State - Game State Components
DGT Kernel Implementation - The Universal Truths

The immutable foundation of the DGT Autonomous Movie System.
All data structures and constants that define the system's behavior.
"""

import time
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Any, Optional, Union, Set
from enum import Enum

# === TILE SYSTEM CONSTANTS ===

class SurfaceState(Enum):
    """Environmental surface states for BG3-style reactivity"""
    NORMAL = "normal"
    FIRE = "fire"
    ICE = "ice"
    WATER = "water"
    GOO = "goo"
    STEAM = "steam"
    ELECTRIC = "electric"
    POISON = "poison"
    BLESSED = "blessed"
    CURSED = "cursed"
    BURNED = "burned"
    FROZEN = "frozen"
    WET = "wet"


class TileType(Enum):
    """Core tile types for the deterministic world"""
    GRASS = 0
    STONE = 1
    WATER = 2
    FOREST = 3
    MOUNTAIN = 4
    SAND = 5
    SNOW = 6
    DOOR_CLOSED = 7
    DOOR_OPEN = 8
    WALL = 9
    FLOOR = 10

class BiomeType(Enum):
    """World biome types for terrain generation"""
    FOREST = "forest"
    GRASS = "grass"
    TOWN = "town"
    TAVERN = "tavern"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    TUNDRA = "tundra"
    WATER = "water"

class InterestType(Enum):
    """Types of interest points for LLM manifestation"""
    STRUCTURE = "structure"
    NATURAL = "natural"
    MYSTERIOUS = "mysterious"
    RESOURCE = "resource"
    DANGER = "danger"
    STORY = "story"

# === VIEWPORT AND RENDERING CONSTANTS ===

VIEWPORT_WIDTH = 160
VIEWPORT_HEIGHT = 144
VIEWPORT_WIDTH_PIXELS = 160
VIEWPORT_HEIGHT_PIXELS = 144
TILE_SIZE_PIXELS = 8
VIEWPORT_TILES_X = 20
VIEWPORT_TILES_Y = 18

# === RENDERING CONSTANTS ===

class RenderLayer(Enum):
    """Rendering layers for composition"""
    BACKGROUND = 0
    TERRAIN = 1
    ENTITIES = 2
    EFFECTS = 3
    UI = 4
    SUBTITLES = 5

# === COLOR PALETTE ===

COLOR_PALETTE = {
    "lightest": (255, 255, 255),
    "light": (170, 170, 170),
    "dark": (85, 85, 85),
    "darkest": (0, 0, 0)
}

RENDER_LAYERS = list(RenderLayer)
TILE_SIZE = 8

# === WORLD GENERATION CONSTANTS ===

WORLD_SIZE_X = 50
WORLD_SIZE_Y = 50
CHUNK_SIZE = 10
PERMUTATION_TABLE_SIZE = 256

# === PERFORMANCE CONSTANTS ===

TARGET_FPS = 60
FRAME_DELAY_MS = 1000 // TARGET_FPS
INTENT_COOLDOWN_MS = 10
MOVEMENT_RANGE = 15
PERSISTENCE_INTERVAL_TURNS = 10

# === VOYAGER STATES ===

class VoyagerState(Enum):
    """Voyager operational states"""
    STATE_IDLE = "idle"
    STATE_MOVING = "moving"
    STATE_PONDERING = "pondering"  # LLM processing state
    STATE_INTERACTING = "interacting"
    STATE_WAITING = "waiting"

# === INTENT SYSTEM ===

class IntentType(Enum):
    """Types of intents for the D&D Engine"""
    MOVEMENT = "movement"
    INTERACTION = "interaction"
    PONDER = "ponder"
    COMBAT = "combat"
    WAIT = "wait"

class ValidationResult(Enum):
    """Validation results for intent processing"""
    VALID = "valid"
    INVALID_POSITION = "invalid_position"
    INVALID_PATH = "invalid_path"
    OBSTRUCTED = "obstructed"
    OUT_OF_RANGE = "out_of_range"
    RULE_VIOLATION = "rule_violation"
    COOLDOWN_ACTIVE = "cooldown_active"

# === CORE DATA STRUCTURES ===

@dataclass
class Tile:
    """Individual tile with surface state and tags"""
    tile_type: TileType
    walkable: bool = True
    surface_state: SurfaceState = SurfaceState.NORMAL
    overlay_state: Optional[SurfaceState] = None  # For temporary effects
    tags: Set[str] = field(default_factory=set)  # For special properties
    metadata: Dict[str, Any] = field(default_factory=dict)  # For custom data
    
    def apply_surface_state(self, new_state: SurfaceState, duration: Optional[float] = None) -> None:
        """Apply surface state with optional duration"""
        self.surface_state = new_state
        if duration:
            self.metadata["state_duration"] = duration
            self.metadata["state_applied_time"] = time.time()
    
    def add_overlay(self, overlay: SurfaceState, duration: float) -> None:
        """Add temporary overlay state"""
        self.overlay_state = overlay
        self.metadata["overlay_duration"] = duration
        self.metadata["overlay_applied_time"] = time.time()
    
    def update_overlays(self) -> None:
        """Update and expire overlay states"""
        current_time = time.time()
        
        # Check surface state duration
        if "state_duration" in self.metadata:
            elapsed = current_time - self.metadata["state_applied_time"]
            if elapsed > self.metadata["state_duration"]:
                self.surface_state = SurfaceState.NORMAL
                del self.metadata["state_duration"]
                del self.metadata["state_applied_time"]
        
        # Check overlay duration
        if self.overlay_state and "overlay_duration" in self.metadata:
            elapsed = current_time - self.metadata["overlay_applied_time"]
            if elapsed > self.metadata["overlay_duration"]:
                self.overlay_state = None
                del self.metadata["overlay_duration"]
                del self.metadata["overlay_applied_time"]
    
    def has_tag(self, tag: str) -> bool:
        """Check if tile has specific tag"""
        return tag in self.tags
    
    def add_tag(self, tag: str) -> None:
        """Add tag to tile"""
        self.tags.add(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove tag from tile"""
        self.tags.discard(tag)

@dataclass
class TileData:
    """Immutable tile data structure"""
    tile: Tile
    biome: BiomeType
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure metadata is immutable
        object.__setattr__(self, 'metadata', dict(self.metadata))

@dataclass
class InterestPoint:
    """Interest point for LLM manifestation (Deterministic Chaos)"""
    position: Tuple[int, int]
    interest_type: InterestType
    seed_value: int
    discovered: bool = False
    manifestation: Optional[str] = None  # LLM's interpretation
    manifestation_timestamp: Optional[float] = None
    tags: Set[str] = field(default_factory=set)  # Tags for quest logic
    
    def add_tag(self, tag: str) -> None:
        """Add tag to interest point"""
        self.tags.add(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if interest point has tag"""
        return tag in self.tags

@dataclass
class Chunk:
    """World chunk for procedural generation"""
    position: Tuple[int, int]  # Chunk coordinates
    size: int = 10  # Chunk size in tiles
    seed: str = ""  # Seed for deterministic generation
    tiles: Dict[Tuple[int, int], Tile] = field(default_factory=dict)
    interest_points: List[InterestPoint] = field(default_factory=list)
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get tile at local coordinates"""
        return self.tiles.get((x, y))
    
    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        """Set tile at local coordinates"""
        self.tiles[(x, y)] = tile
    
    def add_interest_point(self, ip: InterestPoint) -> None:
        """Add interest point to chunk"""
        self.interest_points.append(ip)

@dataclass
class WorldDelta:
    """Immutable world state change"""
    position: Tuple[int, int]
    delta_type: str
    timestamp: float
    data: Dict[str, Any]
    
    def __post_init__(self):
        # Ensure data is immutable
        object.__setattr__(self, 'data', dict(self.data))

@dataclass
class Entity:
    """Base entity class"""
    id: str
    x: int
    y: int
    entity_type: str = "generic"
    visible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GameState:
    """Single Source of Truth for the entire system"""
    version: str = "2.0.0"
    timestamp: float = field(default_factory=time.time)
    
    # Entity State
    player_position: Tuple[int, int] = (10, 25)
    player_health: int = 100
    player_status: List[str] = field(default_factory=list)
    voyager_state: VoyagerState = VoyagerState.STATE_IDLE
    
    # World State
    current_environment: str = "forest"
    world_seed: str = "SEED_ZERO"
    interest_points: List[InterestPoint] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list) # Added for compatibility with GraphicsEngine
    hud: Dict[str, str] = field(default_factory=dict) # Added for compatibility with GraphicsEngine
    background: str = "grass" # Added for compatibility with GraphicsEngine
    
    # Persistence
    world_deltas: Dict[Tuple[int, int], WorldDelta] = field(default_factory=dict)
    
    # Session State
    turn_count: int = 0
    frame_count: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Effects and Triggers
    active_effects: List['Effect'] = field(default_factory=list)
    active_triggers: List['Trigger'] = field(default_factory=list)
    
    # Global state tags
    tags: Set[str] = field(default_factory=set)
    
    def add_tag(self, tag: str) -> None:
        """Add global tag"""
        self.tags.add(tag)
        self.timestamp = time.time()
    
    def remove_tag(self, tag: str) -> None:
        """Remove global tag"""
        self.tags.discard(tag)
        self.timestamp = time.time()
    
    def has_tag(self, tag: str) -> bool:
        """Check if global tag exists"""
        return tag in self.tags
        
    def add_entity(self, entity: Entity):
        """Add entity to game state"""
        self.entities.append(entity)
    
    def remove_entity(self, entity_id: str) -> bool:
        """Remove entity by ID"""
        for i, entity in enumerate(self.entities):
            if entity.id == entity_id:
                del self.entities[i]
                return True
        return False
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Universal Packet"""
        return {
            'width': VIEWPORT_WIDTH_PIXELS,
            'height': VIEWPORT_HEIGHT_PIXELS,
            'entities': [
                {
                    'id': e.id,
                    'x': e.x,
                    'y': e.y,
                    'type': e.entity_type,
                    'metadata': e.metadata
                }
                for e in self.entities
            ],
            'background': {'id': self.background},
            'hud': self.hud,
            'timestamp': self.timestamp,
            'frame_count': self.frame_count,
            'player_position': self.player_position,
            'voyager_state': self.voyager_state.value
        }
    
    def copy(self) -> 'GameState':
        """Create an immutable deep copy"""
        # Note: Shallow copying lists for performance in Hot Loop, deep copy would be safer but slower
        new_state = GameState(
            version=self.version,
            timestamp=self.timestamp,
            player_position=self.player_position,
            player_health=self.player_health,
            player_status=self.player_status.copy(),
            voyager_state=self.voyager_state,
            current_environment=self.current_environment,
            world_seed=self.world_seed,
            # interest_points deep copy omitted for brevity in bridge, assuming standard pickle/copy works or lists are replaced
            turn_count=self.turn_count,
            frame_count=self.frame_count,
            performance_metrics=dict(self.performance_metrics),
            # active_effects/triggers lists copy
            active_effects=list(self.active_effects),
            active_triggers=list(self.active_triggers),
            tags=set(self.tags),
            
            # Compatibility fields
            entities=list(self.entities),
            hud=dict(self.hud),
            background=self.background
        )
        return new_state

# === INTENT TYPES ===

@dataclass
class MovementIntent:
    """Movement intent for navigation"""
    intent_type: str = IntentType.MOVEMENT.value
    target_position: Tuple[int, int] = (0, 0)
    path: List[Tuple[int, int]] = field(default_factory=list)
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class InteractionIntent:
    """Interaction intent for entities and objects"""
    intent_type: str = IntentType.INTERACTION.value
    target_entity: str = ""
    interaction_type: str = ""
    target_position: Tuple[int, int] = (0, 0)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class CombatIntent:
    """Combat intent for engaging hostile entities"""
    intent_type: str = IntentType.COMBAT.value
    target_entity: str = ""
    combat_type: str = "engage"  # engage, flee, negotiate
    target_position: Tuple[int, int] = (0, 0)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class PonderIntent:
    """Ponder intent for LLM processing (Deterministic Chaos)"""
    intent_type: str = IntentType.PONDER.value
    interest_point: InterestPoint = None
    query_context: str = ""
    timestamp: float = field(default_factory=time.time)

@dataclass
class IntentValidation:
    """Intent validation result"""
    is_valid: bool
    validation_result: ValidationResult
    message: str = ""
    corrected_position: Optional[Tuple[int, int]] = None

# === COMMAND AND RESULT PATTERNS ===

@dataclass
class Command:
    """Base command for D&D Engine"""
    command_type: str
    intent: Union[MovementIntent, InteractionIntent, PonderIntent]
    timestamp: float = field(default_factory=time.time)

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    new_state: Optional[GameState] = None
    delta: Optional[WorldDelta] = None
    message: str = ""
    execution_time_ms: float = 0.0

# === EFFECT AND TRIGGER SYSTEMS ===

@dataclass
class Effect:
    """Active effect in the game world"""
    effect_type: str
    duration: float
    parameters: Dict[str, Any]
    start_time: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if effect has expired"""
        return time.time() - self.start_time > self.duration

@dataclass
class Trigger:
    """Interaction trigger in the world"""
    position: Tuple[int, int]
    trigger_type: str
    parameters: Dict[str, Any]
    active: bool = True

# === NARRATIVE SYSTEM ===

@dataclass
class SubtitleEvent:
    """Subtitle event for narrative display"""
    text: str
    duration: float
    style: str = "typewriter"
    timestamp: float = field(default_factory=time.time)
    position: Tuple[int, int] = (0, 0)  # Screen position
    priority: int = 0
    
    def __post_init__(self):
        if isinstance(self.text, str):
            self.text = self.text.strip()

# === PERSISTENCE CONSTANTS ===

PERSISTENCE_FORMAT = "json"
PERSISTENCE_COMPRESSION = True
BACKUP_INTERVAL_TURNS = 50
MAX_BACKUP_FILES = 5

# === ERROR HANDLING ===

class SystemError(Exception):
    """Base system error"""
    pass

class WorldGenerationError(SystemError):
    """World generation failure"""
    pass

class ValidationError(SystemError):
    """Intent validation failure"""
    pass

class PersistenceError(SystemError):
    """Persistence operation failure"""
    pass

class LLMError(SystemError):
    """LLM processing failure"""
    pass

# === UTILITY CONSTANTS ===

DIRECTION_VECTORS = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
    "northeast": (1, -1),
    "northwest": (-1, -1),
    "southeast": (1, 1),
    "southwest": (-1, 1)
}

# === SYSTEM VALIDATION ===

def validate_position(position: Tuple[int, int]) -> bool:
    """Validate world position"""
    x, y = position
    return 0 <= x < WORLD_SIZE_X and 0 <= y < WORLD_SIZE_Y

def validate_tile_type(tile_type: TileType) -> bool:
    """Validate tile type"""
    return isinstance(tile_type, TileType)

def validate_intent(intent: Union[MovementIntent, InteractionIntent, PonderIntent]) -> bool:
    """Validate intent structure"""
    required_fields = {
        MovementIntent: ["intent_type", "target_position"],
        InteractionIntent: ["intent_type", "target_entity"],
        PonderIntent: ["intent_type", "interest_point"]
    }
    
    intent_class = type(intent)
    if intent_class not in required_fields:
        return False
    
    for field_name in required_fields[intent_class]:
        if not hasattr(intent, field_name):
            return False
    
    return True

# === PERFORMANCE METRICS ===

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    fps: float = 0.0
    frame_time_ms: float = 0.0
    turn_time_ms: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    llm_response_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for persistence"""
        return {
            "fps": self.fps,
            "frame_time_ms": self.frame_time_ms,
            "turn_time_ms": self.turn_time_ms,
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "llm_response_time_ms": self.llm_response_time_ms
        }

# === SYSTEM INITIALIZATION ===

def create_initial_game_state(seed: str = "SEED_ZERO") -> GameState:
    """Create initial game state with proper defaults"""
    return GameState(
        world_seed=seed,
        timestamp=time.time(),
        voyager_state=VoyagerState.STATE_IDLE
    )

# === EXPORT CONSTANTS FOR MODULE ACCESS ===

__all__ = [
    # Enums
    "TileType", "BiomeType", "InterestType", "VoyagerState", 
    "IntentType", "ValidationResult", "RenderLayer", "SurfaceState",
    
    # Constants
    "VIEWPORT_WIDTH", "VIEWPORT_HEIGHT", "TILE_SIZE",
    "WORLD_SIZE_X", "WORLD_SIZE_Y", "CHUNK_SIZE",
    "TARGET_FPS", "FRAME_DELAY_MS", "MOVEMENT_RANGE",
    "COLOR_PALETTE", "RENDER_LAYERS", "TILE_SIZE_PIXELS",
    "VIEWPORT_WIDTH_PIXELS", "VIEWPORT_HEIGHT_PIXELS", "VIEWPORT_TILES_X", "VIEWPORT_TILES_Y",
    
    # Data Classes
    "TileData", "InterestPoint", "WorldDelta", "GameState",
    "MovementIntent", "InteractionIntent", "PonderIntent",
    "IntentValidation", "Command", "CommandResult",
    "Effect", "Trigger", "SubtitleEvent", "PerformanceMetrics", "Entity", "Tile",
    
    # Exceptions
    "SystemError", "WorldGenerationError", "ValidationError", 
    "PersistenceError", "LLMError",
    
    # Utilities
    "validate_position", "validate_tile_type", "validate_intent",
    "create_initial_game_state", "DIRECTION_VECTORS"
]
