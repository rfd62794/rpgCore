"""
ASCII Doom Renderer

Phase 1: Raycasting Engine Implementation
Phase 12: Sprite Billboarding Integration
Renders 3D ASCII world using raycasting with entity billboarding.

ADR 029: Isometric "Ghosting" & Threat Depth
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from loguru import logger

from world_ledger import WorldLedger, Coordinate, WorldChunk
from game_state import GameState
from .sprite_billboard import SpriteBillboardSystem, BillboardType


@dataclass
class Ray3D:
    """A 3D ray for raycasting."""
    origin_x: float
    origin_y: float
    angle: float  # Direction in degrees
    length: float
    
    def get_direction(self) -> Tuple[float, float]:
        """Get the direction vector for this ray."""
        angle_rad = math.radians(self.angle)
        return (math.cos(angle_rad), math.sin(angle_rad))


@dataclass
class HitResult:
    """Result of a raycast against the world."""
    hit: bool
    distance: float
    height: float
    content: str
    coordinate: Optional[Coordinate]
    entity_id: Optional[str]


class ASCIIDoomRenderer:
    """
    ASCII-Doom style 3D renderer for tactical depth.
    
    Implements Wolfenstein-style raycasting with perception-based FoV
    and visual threat indicators for hostile NPCs.
    """
    
    def __init__(self, world_ledger: WorldLedger, width: int = 80, height: int = 24, faction_system=None):
        """Initialize the ASCII Doom renderer."""
        self.world_ledger = world_ledger
        self.faction_system = faction_system
        self.width = width
        self.height = height
        
        # Initialize sprite billboard system
        self.sprite_billboard = SpriteBillboardSystem(world_ledger, faction_system)
        
        # Raycasting parameters
        self.fov = math.radians(60)  # Field of view
        self.max_distance = 20
        self.wall_height = 10
        
        # Rendering buffers
        self.buffer = [[" " " for _ in range(width)] for _ in range(height)]
        self.depth_buffer = [[self.max_distance for _ in range(width)] for _ in range(height)]
        
        # Color scheme
        self.colors = {
            "wall": "#",
            "floor": ".",
            "entity": "!",
            "player": "@",
            "empty": " "
        }
        
        logger.info(f"ASCII-Doom Renderer initialized: {width}x{height} viewport, {math.degrees(self.fov):.0f} FoV")
        
        # Visual elements mapping
        self.wall_chars = ['#', '#', '=', '=', '+', '-', '|', '/', '\\']
        self.floor_chars = ['.', ',', '-', '_', '~', '^']
        self.entity_chars = ['@', '&', '%', '*', '!']
        self.item_chars = ['$', '%', '^', '+', '?']
        
        # Threat indicator characters
        self.threat_chars = ['!', '?', 'X', '@', '#']
        self.threat_mode = False  # Whether to show threat indicators
        logger.info(f"ASCII-Doom Renderer initialized: {width}x{height} viewport, {self.fov}° FoV")
    
    def set_threat_mode(self, enabled: bool):
        """Enable or disable threat indicator mode."""
        self.threat_mode = enabled
        logger.info(f"Threat mode {'enabled' if enabled else 'disabled'}")
    
    def render_frame(
        self, 
        game_state: GameState, 
        player_angle: float,
        perception_range: int,
        npc_mood: Optional[str] = None
    ) -> List[List[str]]:
        """
        Render a 3D frame using raycasting.
        
        Args:
            game_state: Current game state
            player_angle: Player's facing angle in degrees
            perception_range: Player's perception range
            npc_mood: Current NPC mood for threat indicators
            
        Returns:
            List of strings representing the rendered frame
        """
        # Clear buffer
        self.buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Get player position
        player_x = game_state.position.x
        player_y = game_state.position.y
        
        # Calculate FoV based on perception
        effective_fov = min(self.fov, perception_range * 2)  # Scale FoV by perception
        half_fov = effective_fov / 2
        
        # Determine if threat mode should be active
        threat_active = self.threat_mode and npc_mood in ["hostile", "unfriendly"]
        
        # Cast rays across the viewport
        for x in range(self.width):
            # Calculate ray angle for this column
            ray_angle = player_angle - half_fov + (x / self.width) * effective_fov
            
            # Create ray
            ray = Ray3D(
                origin_x=player_x,
                origin_y=player_y,
                angle=ray_angle,
                length=self.max_distance
            )
            
            # Cast ray and get hit result
            hit_result = self._cast_ray(ray, game_state)
            
            # Apply threat indicators if active
            if threat_active and hit_result.hit:
                hit_result.content = self._apply_threat_indicator(hit_result.content, hit_result.distance)
            
            # Render column based on hit result
            self._render_column(x, hit_result)
        
        return self.buffer
    
    def _apply_threat_indicator(self, char: str, distance: float) -> str:
        """Apply threat indicator to character based on distance."""
        if distance < 3:
            return self.threat_chars[0]  # ! - immediate threat
        elif distance < 6:
            return self.threat_chars[1]  # ? - potential threat
        elif distance < 10:
            return self.threat_chars[2]  # X - distant threat
        elif distance < 15:
            return self.threat_chars[3]  # @ - warning
        else:
            return self.threat_chars[4]  # # - distant warning
    
    def _cast_ray(self, ray: Ray3D, game_state: GameState) -> HitResult:
        """
        Cast a single ray and return hit information.
        
        Args:
            ray: The ray to cast
            game_state: Current game state
            
        Returns:
            HitResult with distance and content
        """
        direction = ray.get_direction()
        
        # Step through the ray
        for distance in range(1, int(ray.length)):
            # Calculate position along ray
            check_x = ray.origin_x + direction[0] * distance
            check_y = ray.origin_y + direction[1] * distance
            
            # Get coordinate
            coord = Coordinate(int(check_x), int(check_y), 0)
            
            # Check for chunk at this coordinate
            chunk = self.world_ledger.get_chunk(coord, 0)
            
            # Check if this is a wall
            if self._is_wall(chunk, check_x, check_y):
                return HitResult(
                    hit=True,
                    distance=distance,
                    height=1.0,
                    content=self._get_wall_char(chunk, distance),
                    coordinate=coord,
                    entity_id=None
                )
            
            # Check for entities
            entity = self._get_entity_at(coord, game_state)
            if entity:
                return HitResult(
                    hit=True,
                    distance=distance,
                    height=1.0,
                    content=self._get_entity_char(entity, distance),
                    coordinate=coord,
                    entity_id=entity.id
                )
            
            # Check for items
            item = self._get_item_at(coord, game_state)
            if item:
                return HitResult(
                    hit=True,
                    distance=distance,
                    height=0.5,
                    content=self._get_item_char(item, distance),
                    coordinate=coord,
                    entity_id=None
                )
        
        # No hit
        return HitResult(
            hit=False,
            distance=ray.length,
            height=0.0,
            content='',
            coordinate=None,
            entity_id=None
        )
    
    def _is_wall(self, chunk: WorldChunk, x: float, y: float) -> bool:
        """Check if a position is a wall."""
        # Check if coordinate is outside chunk boundaries
        chunk_x, chunk_y, chunk_t = chunk.coordinate
        
        # Simple boundary check
        if x < chunk_x or x >= chunk_x + 1 or y < chunk_y or y >= chunk_y + 1:
            return True
        
        # Check for wall-like tags
        wall_tags = ["wall", "stone", "barrier", "obstacle", "blocked"]
        return any(tag in chunk.tags for tag in wall_tags)
    
    def _get_wall_char(self, chunk: WorldChunk, distance: float) -> str:
        """Get wall character based on distance."""
        # Distance-based wall rendering
        if distance < 2:
            return self.wall_chars[0]  # Closest wall
        elif distance < 5:
            return self.wall_chars[1]  # Mid-range wall
        elif distance < 10:
            return self.wall_chars[2]  # Far wall
        else:
            return self.wall_chars[3]  # Distant wall
    
    def _get_entity_at(self, coord: Coordinate, game_state: GameState) -> Optional[Any]:
        """Get entity at a coordinate."""
        # This would integrate with the EntityAI system
        # For now, return None
        return None
    
    def _get_entity_char(self, entity: Any, distance: float) -> str:
        """Get entity character based on distance."""
        if distance < 3:
            return self.entity_chars[0]  # Close entity
        elif distance < 6:
            return self.entity_chars[1]  # Mid-range entity
        else:
            return self.entity_chars[2]  # Distant entity
    
    def _get_item_at(self, coord: Coordinate, game_state: GameState) -> Optional[Any]:
        """Get item at a coordinate."""
        # This would integrate with the loot system
        # For now, return None
        return None
    
    def _get_item_char(self, item: Any, distance: float) -> str:
        """Get item character based on distance."""
        if distance < 2:
            return self.item_chars[0]  # Close item
        elif distance < 4:
            return self.item_chars[1]  # Mid-range item
        else:
            return self.item_chars[2]  # Distant item
    
    def _render_column(self, x: int, hit_result: HitResult):
        """Render a single column of the 3D view."""
        if not hit_result.hit:
            # No hit - render as empty space
            for y in range(self.height):
                self.buffer[y][x] = ' '
            return
        
        # Calculate height scaling
        height_scale = min(1.0, hit_result.height)
        column_height = int(self.height * height_scale)
        
        # Render the hit
        char = hit_result.content
        
        # Add distance-based shading
        if hit_result.distance > 10:
            char = self._apply_distance_shading(char, hit_result.distance)
        
        # Render from bottom to top
        start_y = self.half_height - column_height // 2
        end_y = self.half_height + column_height // 2
        
        for y in range(start_y, end_y):
            if 0 <= y < self.height and 0 <= x < self.width:
                self.buffer[y][x] = char
    
    def _apply_distance_shading(self, char: str, distance: float) -> str:
        """Apply distance-based shading to a character."""
        # Darker characters for distant objects
        if distance > 15:
            return '░'
        elif distance > 10:
            return '▒'
        elif distance > 5:
            return '▓'
        else:
            return char
    
    def get_frame_as_string(self, buffer: List[List[str]]) -> str:
        """Convert the render buffer to a string."""
        return '\n'.join(''.join(row) for row in buffer)
    
    def calculate_fov_distance(self, perception_range: int) -> float:
        """Calculate effective FoV distance based on perception."""
        # Scale FoV by perception range
        perception_multiplier = perception_range / 10.0  # Base perception range is 10
        return self.fov * perception_multiplier
    
    def get_viewport_summary(self) -> Dict[str, Any]:
        """Get summary of the renderer configuration."""
        return {
            "width": self.width,
            "height": self.height,
            "fov": self.fov,
            "max_distance": self.max_distance,
            "wall_chars": self.wall_chars,
            "floor_chars": self.floor_chars,
            "entity_chars": self.entity_chars,
            "item_chars": self.item_chars
        }


# Export for use by game engine
__all__ = ["ASCIIDoomRenderer", "Ray3D", "HitResult"]
