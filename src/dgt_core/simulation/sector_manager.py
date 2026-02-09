"""
DGT Sector Manager - ADR 168
Component-Lite Entity Manager with Miyoo-First Screen Wrap
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from loguru import logger

from src.dgt_core.kernel.components import PhysicsComponent, RenderComponent, InventoryComponent, EntityID
from src.dgt_core.engines.space.space_physics import SpaceVoyagerEngine

# Miyoo Mini Logical Resolution
LOGICAL_WIDTH = 160
LOGICAL_HEIGHT = 144

@dataclass
class Entity:
    """Component container"""
    id: EntityID
    physics: Optional[PhysicsComponent] = None
    render: Optional[RenderComponent] = None
    inventory: Optional[InventoryComponent] = None

class SectorManager:
    """Manages entities, physics updates, and boundary wrapping"""
    
    def __init__(self):
        self.entities: List[Entity] = []
        self.physics_engine = SpaceVoyagerEngine()
        self.time_elapsed: float = 0.0
        self.portal_spawned: bool = False
        self.game_over: bool = False
        self.victory: bool = False
        
        logger.info("🌌 Sector Manager initialized (160x144 Logic)")
        
    def add_entity(self, entity: Entity):
        """Add entity to sector"""
        self.entities.append(entity)
        logger.debug(f"➕ Entity added: {entity.id.id}")
        
    def update(self, dt: float) -> List[str]:
        """Main Sector Loop: Logic -> Physics -> Wrap -> Mass"""
        events = []
        
        if self.game_over or self.victory:
            return events

        self.time_elapsed += dt
        
        # 0. Survival Hook Events
        if self.time_elapsed >= 60.0 and not self.portal_spawned:
            self._spawn_portal()
            events.append("PORTAL_SPAWNED")
            
        for entity in self.entities:
            # 1. Mass-Link System (Inventory -> Mass)
            if entity.physics and entity.inventory:
                self._update_mass_from_inventory(entity)
            
            # 2. Physics System
            if entity.physics:
                self.physics_engine.update(entity.physics, dt)
                
                # Check Collisions for Player
                if entity.id.id == "player_01":
                    event = self._check_player_collisions(entity)
                    if event:
                        events.append(event)
            
            # 3. Boundary System (Screen Wrap)
            if entity.physics:
                self._apply_screen_wrap(entity.physics)
                
        return events
    
    def _spawn_portal(self):
        """Spawn exit portal at bottom center"""
        portal = Entity(
            id=EntityID(id="portal_exit", type="portal"),
            physics=PhysicsComponent(
                x=80, y=134, # Bottom Center
                mass=1000.0,
                max_thrust=0.0
            ),
            render=RenderComponent(
                sprite_id="portal", # Needs to be added to PPU or generic
                layer=2,
                color="#00FFFF" # Cyan
            )
        )
        self.add_entity(portal)
        self.portal_spawned = True
        logger.info("🌀 PORTAL ANOMALY DETECTED AT [80, 134]")

    def _check_player_collisions(self, player: Entity) -> Optional[str]:
        """Check player collisions for Win/Loss"""
        player_r = 4 # Approx radius
        
        for other in self.entities:
            if other.id.id == player.id.id:
                continue
                
            if not other.physics:
                continue
                
            # Simple Distance Check
            dx = player.physics.x - other.physics.x
            dy = player.physics.y - other.physics.y
            dist = (dx**2 + dy**2)**0.5
            
            if dist < (player_r + 4): # Assume other radius ~4
                # Hit Logic
                if other.id.type == "portal":
                    self.victory = True
                    return "VICTORY"
                elif other.id.type == "asteroid":
                    # Check velocity
                    speed = (player.physics.velocity_x**2 + player.physics.velocity_y**2)**0.5
                    if speed > 5.0:
                        self.game_over = True
                        return "CRASH_FAIL"
                    else:
                        # Bump logic (optional, just bounce for now)
                        pass
        return None

    def _update_mass_from_inventory(self, entity: Entity):
        """Update physics mass based on inventory"""
        base_mass = 10.0 # Default base mass, could be in a 'StructureComponent' later
        added_mass = entity.inventory.get_total_mass_impact()
        entity.physics.mass = base_mass + added_mass
        
    def _apply_screen_wrap(self, physics: PhysicsComponent):
        """Apply Pac-Man style screen wrapping"""
        if physics.x < 0:
            physics.x += LOGICAL_WIDTH
        elif physics.x > LOGICAL_WIDTH:
            physics.x -= LOGICAL_WIDTH
            
        if physics.y < 0:
            physics.y += LOGICAL_HEIGHT
        elif physics.y > LOGICAL_HEIGHT:
            physics.y -= LOGICAL_HEIGHT
            
    def get_render_data(self) -> List[Dict]:
        """Get flattened render data for PPU"""
        render_packet = []
        for entity in self.entities:
            if entity.render and entity.physics:
                if entity.render.visible:
                    render_packet.append({
                        "id": entity.id.id,
                        "x": entity.physics.x,
                        "y": entity.physics.y,
                        "sprite_id": entity.render.sprite_id,
                        "layer": entity.render.layer,
                        "color": entity.render.color
                    })
        return render_packet
