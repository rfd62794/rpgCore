"""
Pure Tkinter PPU - Native Implementation with Multi-Mode Support
ADR 075: Pure Tkinter Implementation + ADR 078: Multi-Mode Viewport Protocol

High-performance pixel rendering using native Tkinter PhotoImage.
Supports OVERWORLD (top-down) and COMBAT (side-view) rendering modes.
"""

import tkinter as tk
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger

from core.constants import DISPLAY_SCALE, TARGET_FPS
from utils.asset_loader import AssetLoader
from .ppu_modes import PPUMode, PPULayouts, CombatPositions, AnimationFrames, PPUTransitionEffects

# Viewport Constants (Game Boy Parity)
TILE_SIZE_PIXELS = 8
VIEWPORT_WIDTH_PIXELS = 160
VIEWPORT_HEIGHT_PIXELS = 144
VIEWPORT_TILES_X = 20
VIEWPORT_TILES_Y = 18

# Display Scaling (4x for better visibility)
DISPLAY_SCALE = 4
DISPLAY_WIDTH_PIXELS = VIEWPORT_WIDTH_PIXELS * DISPLAY_SCALE
DISPLAY_HEIGHT_PIXELS = VIEWPORT_HEIGHT_PIXELS * DISPLAY_SCALE

class RenderLayer(Enum):
    """Canvas Z-index layers for proper compositing"""
    BACKGROUND = 0
    SURFACES = 1
    FRINGE = 2  # Objects
    ACTORS = 3
    UI = 4

@dataclass
class CanvasEntity:
    """Entity rendered on canvas with native PhotoImage"""
    canvas_id: int  # Canvas object ID
    layer: RenderLayer
    world_pos: Tuple[int, int]  # World coordinates (tiles)
    sprite_id: str
    last_update: float = 0.0

@dataclass
class RenderEntity:
    """Entity data for rendering"""
    world_pos: Tuple[int, int]
    sprite_id: str
    layer: RenderLayer
    visible: bool = True
    metadata: Dict[str, Any] = None

class NativeTkinterPPU:
    """
    Pure Tkinter PPU using native PhotoImage objects and Canvas layering
    
    This treats the Canvas as VRAM and uses Canvas object IDs for efficient updates
    instead of redrawing pixels each frame.
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Canvas setup (acts as VRAM)
        self.canvas = tk.Canvas(
            root,
            width=DISPLAY_WIDTH_PIXELS,
            height=DISPLAY_HEIGHT_PIXELS,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Sprite registry (native PhotoImage objects)
        self.sprites: Dict[str, PhotoImage] = {}
        
        # Keep references to prevent garbage collection
        self._sprite_refs: List[PhotoImage] = []
        
        # Canvas entity registry (maps world positions to canvas IDs)
        self.canvas_entities: Dict[Tuple[int, int], CanvasEntity] = {}
        
        # View registry for fast updates (layer -> list of canvas IDs)
        self.view_registry: Dict[RenderLayer, List[int]] = {
            layer: [] for layer in RenderLayer
        }
        
        # Viewport position in world coordinates
        self.viewport_world_pos: Tuple[int, int] = (0, 0)
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.fps_history: List[float] = []
        self.max_fps_history = 60
        
        # Initialize sprite system
        self._initialize_sprites()
        
        logger.info("🎨 Pure Tkinter PPU initialized with native PhotoImage system")
    
    def _initialize_sprites(self) -> None:
        """Initialize native PhotoImage sprites for all asset types"""
        # Create procedural 8x8 sprites using PhotoImage
        self._create_tile_sprites()
        self._create_object_sprites()
        self._create_actor_sprites()
        
        logger.info(f"🎨 Generated {len(self.sprites)} native PhotoImage sprites")
    
    def _create_tile_sprites(self) -> None:
        """Create procedural tile sprites using PhotoImage"""
        tile_types = [
            'grass', 'stone', 'dirt', 'water', 'sand', 
            'wood_floor', 'stone_wall', 'void', 'path', 'mud'
        ]
        
        colors = {
            'grass': '#2d5016',
            'stone': '#808080', 
            'dirt': '#8b4513',
            'water': '#1e90ff',
            'sand': '#f4a460',
            'wood_floor': '#8b4513',
            'stone_wall': '#696969',
            'void': '#000000',
            'path': '#daa520',
            'mud': '#654321'
        }
        
        for tile_type in tile_types:
            sprite = self._create_procedural_sprite(colors.get(tile_type, '#ffffff'))
            self.sprites[f'tile_{tile_type}'] = sprite
    
    def _create_object_sprites(self) -> None:
        """Create procedural object sprites using PhotoImage"""
        object_types = [
            'tree', 'boulder', 'chest', 'door', 'campfire',
            'crystal', 'fountain', 'altar', 'throne', 'signpost'
        ]
        
        colors = {
            'tree': '#228b22',
            'boulder': '#696969',
            'chest': '#8b4513',
            'door': '#654321',
            'campfire': '#ff4500',
            'crystal': '#9370db',
            'fountain': '#4682b4',
            'altar': '#dcdcdc',
            'throne': '#ffd700',
            'signpost': '#8b4513'
        }
        
        for obj_type in object_types:
            sprite = self._create_procedural_sprite(colors.get(obj_type, '#ffffff'))
            self.sprites[f'object_{obj_type}'] = sprite
    
    def _create_actor_sprites(self) -> None:
        """Create procedural actor sprites using PhotoImage"""
        actor_types = ['voyager', 'npc', 'creature', 'spirit']
        
        colors = {
            'voyager': '#ff0000',
            'npc': '#0000ff', 
            'creature': '#800080',
            'spirit': '#ffffff'
        }
        
        for actor_type in actor_types:
            sprite = self._create_procedural_sprite(colors.get(actor_type, '#ffffff'))
            self.sprites[f'actor_{actor_type}'] = sprite
    
    def _create_procedural_sprite(self, base_color: str) -> PhotoImage:
        """Create an 8x8 procedural sprite using PhotoImage with display scaling"""
        # Create base sprite at tile size
        base_sprite = PhotoImage(width=TILE_SIZE_PIXELS, height=TILE_SIZE_PIXELS)
        
        # Convert hex color to RGB
        if base_color.startswith('#'):
            hex_color = base_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
        else:
            # Default to gray for invalid colors
            r = g = b = 128
        
        # Fill sprite with base color and add some variation
        for y in range(TILE_SIZE_PIXELS):
            for x in range(TILE_SIZE_PIXELS):
                # Add some procedural variation
                if (x + y) % 3 == 0:
                    # Lighter variant
                    r = min(255, r + 30)
                    g = min(255, g + 30)
                    b = min(255, b + 30)
                elif (x + y) % 5 == 0:
                    # Darker variant
                    r = max(0, r - 30)
                    g = max(0, g - 30)
                    b = max(0, b - 30)
                
                # Set pixel color
                color_hex = f'#{r:02x}{g:02x}{b:02x}'
                base_sprite.put(color_hex, (x, y))
        
        # Scale sprite for display using zoom
        scaled_sprite = base_sprite.zoom(DISPLAY_SCALE, DISPLAY_SCALE)
        
        # Keep reference to prevent garbage collection
        self._sprite_refs.append(scaled_sprite)
        
        return scaled_sprite
    
    def world_to_canvas_coords(self, world_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert world coordinates to canvas pixel coordinates"""
        world_x, world_y = world_pos
        
        # Calculate position relative to viewport
        rel_x = world_x - self.viewport_world_pos[0]
        rel_y = world_y - self.viewport_world_pos[1]
        
        # Convert to pixels and scale for display
        canvas_x = rel_x * TILE_SIZE_PIXELS * DISPLAY_SCALE
        canvas_y = rel_y * TILE_SIZE_PIXELS * DISPLAY_SCALE
        
        return canvas_x, canvas_y
    
    def add_entity(self, entity: RenderEntity) -> int:
        """Add an entity to the canvas and return its canvas ID"""
        if entity.sprite_id not in self.sprites:
            logger.warning(f"Sprite {entity.sprite_id} not found in registry")
            return -1
        
        sprite = self.sprites[entity.sprite_id]
        canvas_x, canvas_y = self.world_to_canvas_coords(entity.world_pos)
        
        # Create canvas image with proper scaling
        canvas_id = self.canvas.create_image(
            canvas_x,
            canvas_y,
            image=sprite,
            anchor='nw',
            tags=(entity.layer.name.lower(),)
        )
        
        # Note: PhotoImage scaling is handled by zoom() method during sprite creation
        # Canvas itemconfig doesn't support width/height for images
        
        # Create canvas entity record
        canvas_entity = CanvasEntity(
            canvas_id=canvas_id,
            layer=entity.layer,
            world_pos=entity.world_pos,
            sprite_id=entity.sprite_id,
            last_update=time.time()
        )
        
        # Register in both registries
        self.canvas_entities[entity.world_pos] = canvas_entity
        self.view_registry[entity.layer].append(canvas_id)
        
        return canvas_id
    
    def update_entity_position(self, world_pos: Tuple[int, int], new_pos: Tuple[int, int]) -> bool:
        """Update entity position efficiently using canvas.coords"""
        if world_pos not in self.canvas_entities:
            return False
        
        canvas_entity = self.canvas_entities[world_pos]
        canvas_x, canvas_y = self.world_to_canvas_coords(new_pos)
        
        # Update canvas position (very efficient)
        self.canvas.coords(canvas_entity.canvas_id, canvas_x, canvas_y)
        
        # Update registries
        del self.canvas_entities[world_pos]
        canvas_entity.world_pos = new_pos
        canvas_entity.last_update = time.time()
        self.canvas_entities[new_pos] = canvas_entity
        
        return True
    
    def remove_entity(self, world_pos: Tuple[int, int]) -> bool:
        """Remove entity from canvas"""
        if world_pos not in self.canvas_entities:
            return False
        
        canvas_entity = self.canvas_entities[world_pos]
        
        # Remove from canvas
        self.canvas.delete(canvas_entity.canvas_id)
        
        # Remove from registries
        self.view_registry[canvas_entity.layer].remove(canvas_entity.canvas_id)
        del self.canvas_entities[world_pos]
        
        return True
    
    def set_viewport(self, world_pos: Tuple[int, int]) -> None:
        """Set viewport position and update all entities"""
        self.viewport_world_pos = world_pos
        
        # Update all entity positions relative to new viewport
        for world_pos, canvas_entity in list(self.canvas_entities.items()):
            canvas_x, canvas_y = self.world_to_canvas_coords(world_pos)
            self.canvas.coords(canvas_entity.canvas_id, canvas_x, canvas_y)
    
    def render_layer(self, entities: List[RenderEntity]) -> None:
        """Render a complete layer of entities"""
        for entity in entities:
            if entity.visible:
                self.add_entity(entity)
    
    def clear_layer(self, layer: RenderLayer) -> None:
        """Clear all entities in a layer"""
        if layer in self.view_registry:
            for canvas_id in self.view_registry[layer]:
                self.canvas.delete(canvas_id)
            self.view_registry[layer].clear()
    
    def clear_all(self) -> None:
        """Clear all canvas entities"""
        self.canvas.delete("all")
        self.canvas_entities.clear()
        for layer in self.view_registry:
            self.view_registry[layer].clear()
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        fps = 1.0 / frame_time if frame_time > 0 else 0
        
        self.fps_history.append(fps)
        if len(self.fps_history) > self.max_fps_history:
            self.fps_history.pop(0)
        
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        
        self.last_frame_time = current_time
        
        return {
            'fps': fps,
            'avg_fps': avg_fps,
            'entities': len(self.canvas_entities),
            'sprites': len(self.sprites)
        }
    
    def get_sprite(self, sprite_id: str) -> Optional[PhotoImage]:
        """Get a native PhotoImage sprite by ID"""
        return self.sprites.get(sprite_id)

class NativeTkinterGameWindow:
    """Complete game window using Pure Tkinter PPU"""
    
    def __init__(self, title: str = "rpgCore - Pure Tkinter"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        
        # Create PPU
        self.ppu = NativeTkinterPPU(self.root)
        
        # Game state
        self.running = False
        self.frame_count = 0
        
        # Performance display
        self.perf_label = tk.Label(
            self.root,
            text="FPS: 0",
            bg='black',
            fg='white',
            font=('Courier', 10)
        )
        self.perf_label.place(x=10, y=10)
        
        logger.info("🎮 Pure Tkinter Game Window initialized")
    
    def update(self) -> None:
        """Main update loop"""
        if not self.running:
            return
        
        # Update performance display
        stats = self.ppu.get_performance_stats()
        self.perf_label.config(
            text=f"FPS: {stats['fps']:.1f} | Entities: {stats['entities']}"
        )
        
        # Schedule next update
        self.root.after(16, self.update)  # ~60 FPS target
    
    def start(self) -> None:
        """Start the game loop"""
        self.running = True
        self.update()
        logger.info("🎮 Pure Tkinter Game Window started")
    
    def stop(self) -> None:
        """Stop the game loop"""
        self.running = False
        logger.info("🎮 Pure Tkinter Game Window stopped")
    
    def run(self) -> None:
        """Run the main window"""
        self.start()
        self.root.mainloop()
        self.stop()

# Test implementation
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    window = NativeTkinterGameWindow("Pure Tkinter PPU Test")
    
    # Test rendering some entities
    from utils.asset_loader import AssetLoader
    
    asset_loader = AssetLoader()
    
    # Add some test entities
    test_entities = [
        RenderEntity((5, 5), 'tile_grass', RenderLayer.BACKGROUND),
        RenderEntity((5, 6), 'tile_stone', RenderLayer.BACKGROUND),
        RenderEntity((7, 7), 'object_tree', RenderLayer.FRINGE),
        RenderEntity((8, 8), 'actor_voyager', RenderLayer.ACTORS),
    ]
    
    window.ppu.render_layer(test_entities)
    
    window.run()
