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
        
        logger.info("🌌 Sector Manager initialized (160x144 Logic)")
        
    def add_entity(self, entity: Entity):
        """Add entity to sector"""
        self.entities.append(entity)
        logger.debug(f"➕ Entity added: {entity.id.id}")
        
    def update(self, dt: float):
        """Main Sector Loop: Logic -> Physics -> Wrap -> Mass"""
        
        for entity in self.entities:
            # 1. Mass-Link System (Inventory -> Mass)
            if entity.physics and entity.inventory:
                self._update_mass_from_inventory(entity)
            
            # 2. Physics System
            if entity.physics:
                self.physics_engine.update(entity.physics, dt)
            
            # 3. Boundary System (Screen Wrap)
            if entity.physics:
                self._apply_screen_wrap(entity.physics)
    
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
