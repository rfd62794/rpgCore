"""
Core Foundation - GameState, Intent Dataclasses, and System Constants

The immutable foundation of the DGT Autonomous Movie System.
All data structures and constants that define the system's behavior.
"""

import time
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Any, Optional, Union
from enum import Enum

# === TILE SYSTEM CONSTANTS ===

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
    TOWN = "town"
    TAVERN = "tavern"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    TUNDRA = "tundra"

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
    """Types of intents the system can process"""
    MOVEMENT = "movement"
    INTERACTION = "interaction"
    PONDER = "ponder"  # LLM query intent
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
class TileData:
    """Immutable tile data structure"""
    tile_type: TileType
    walkable: bool
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
    
    # Persistence
    world_deltas: Dict[Tuple[int, int], WorldDelta] = field(default_factory=dict)
    
    # Session State
    turn_count: int = 0
    frame_count: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Effects and Triggers
    active_effects: List['Effect'] = field(default_factory=list)
    active_triggers: List['Trigger'] = field(default_factory=list)
    
    def copy(self) -> 'GameState':
        """Create an immutable deep copy"""
        return GameState(
            version=self.version,
            timestamp=self.timestamp,
            player_position=self.player_position,
            player_health=self.player_health,
            player_status=self.player_status.copy(),
            voyager_state=self.voyager_state,
            current_environment=self.current_environment,
            world_seed=self.world_seed,
            interest_points=[InterestPoint(
                position=ip.position,
                interest_type=ip.interest_type,
                seed_value=ip.seed_value,
                discovered=ip.discovered,
                manifestation=ip.manifestation,
                manifestation_timestamp=ip.manifestation_timestamp
            ) for ip in self.interest_points],
            world_deltas={pos: WorldDelta(
                position=delta.position,
                delta_type=delta.delta_type,
                timestamp=delta.timestamp,
                data=delta.data.copy()
            ) for pos, delta in self.world_deltas.items()},
            turn_count=self.turn_count,
            frame_count=self.frame_count,
            performance_metrics=self.performance_metrics.copy(),
            active_effects=self.active_effects.copy(),
            active_triggers=self.active_triggers.copy()
        )

# === INTENT DATA STRUCTURES ===

@dataclass
class MovementIntent:
    """Movement intent with pathfinding data"""
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
    "IntentType", "ValidationResult",
    
    # Constants
    "VIEWPORT_WIDTH", "VIEWPORT_HEIGHT", "TILE_SIZE",
    "WORLD_SIZE_X", "WORLD_SIZE_Y", "CHUNK_SIZE",
    "TARGET_FPS", "FRAME_DELAY_MS", "MOVEMENT_RANGE",
    
    # Data Classes
    "TileData", "InterestPoint", "WorldDelta", "GameState",
    "MovementIntent", "InteractionIntent", "PonderIntent",
    "IntentValidation", "Command", "CommandResult",
    "Effect", "Trigger", "SubtitleEvent", "PerformanceMetrics",
    
    # Exceptions
    "SystemError", "WorldGenerationError", "ValidationError", 
    "PersistenceError", "LLMError",
    
    # Utilities
    "validate_position", "validate_tile_type", "validate_intent",
    "create_initial_game_state", "DIRECTION_VECTORS"
]
