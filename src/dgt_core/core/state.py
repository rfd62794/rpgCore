"""
DGT Core State - Game State Components
Core state classes for the DGT engine
"""

import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class TileType(Enum):
    """Tile types for world generation"""
    GRASS = "grass"
    STONE = "stone"
    WATER = "water"
    DIRT = "dirt"
    SAND = "sand"
    SNOW = "snow"
    LAVA = "lava"

class BiomeType(Enum):
    """Biome types for world generation"""
    FOREST = "forest"
    DESERT = "desert"
    TUNDRA = "tundra"
    OCEAN = "ocean"
    MOUNTAIN = "mountain"
    SWAMP = "swamp"

@dataclass
class SubtitleEvent:
    """Subtitle event for display"""
    text: str
    duration: float = 3.0
    timestamp: float = field(default_factory=time.time)
    priority: int = 0
    
    def __post_init__(self):
        if isinstance(self.text, str):
            self.text = self.text.strip()

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
    """Complete game state"""
    width: int = 160
    height: int = 144
    entities: List[Entity] = field(default_factory=list)
    background: str = "grass"
    hud: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    frame_count: int = 0
    
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
            'width': self.width,
            'height': self.height,
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
            'frame_count': self.frame_count
        }

__all__ = [
    'TileType', 'BiomeType', 'SubtitleEvent', 'Entity', 'GameState'
]
