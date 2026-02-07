"""
Asset Loader - Pre-Baked Asset Registry and Loader

Loads YAML definitions and sprite sheets into the GameState.
Treats assets as prefabs with systemic characteristics rather than raw pixels.

Asset Types:
- Tile: Pre-baked biome tiles (Grass, Dirt, Stone)
- Object: Interactive entities with characteristics (Chests, Doors)
- Actor: Living entities with states (Voyager, Personas)
- Effect: Systemic overlays (Fire, Water, Blood)
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from loguru import logger

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from core.state import TileType, BiomeType
from core.constants import TILE_SIZE_PIXELS, COLOR_PALETTE


class AssetType(Enum):
    """Types of assets in the registry"""
    TILE = "tile"
    OBJECT = "object"
    ACTOR = "actor"
    EFFECT = "effect"


@dataclass
class ObjectCharacteristics:
    """Systemic characteristics for world objects"""
    material: str
    state: str
    rarity: float
    integrity: int
    triggers: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    interaction_hooks: List[str] = field(default_factory=list)
    d20_checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    combat_stats: Dict[str, Any] = field(default_factory=dict)
    resistances: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    def has_tag(self, tag: str) -> bool:
        """Check if object has specific tag"""
        return tag in self.tags
    
    def can_interact(self, action: str) -> bool:
        """Check if object supports specific interaction"""
        return action in self.interaction_hooks
    
    def get_combat_stat(self, stat: str, default: Any = 0) -> Any:
        """Get combat stat with default fallback"""
        return self.combat_stats.get(stat, default)
    
    def has_resistance(self, damage_type: str) -> bool:
        """Check if object has resistance to damage type"""
        return damage_type in self.resistances
    
    def has_weakness(self, damage_type: str) -> bool:
        """Check if object has weakness to damage type"""
        return damage_type in self.weaknesses


@dataclass
class AssetDefinition:
    """Complete asset definition with metadata"""
    asset_id: str
    asset_type: AssetType
    sprite_id: Optional[str] = None
    characteristics: Optional[ObjectCharacteristics] = None
    collision: bool = False
    friction: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AssetLoader:
    """Loads and manages pre-baked assets from YAML and image files"""
    
    def __init__(self, assets_path: str = "assets/"):
        self.assets_path = Path(assets_path)
        self.registry: Dict[str, AssetDefinition] = {}
        
        # Sprite cache
        self.tile_sprites: Dict[TileType, Image.Image] = {}
        self.object_sprites: Dict[str, Image.Image] = {}
        self.actor_sprites: Dict[str, Dict[str, Image.Image]] = {}
        self.effect_sprites: Dict[str, Image.Image] = {}
        
        # Load all assets
        self._load_assets()
        
        logger.info(f"🎨 Asset Loader initialized - {len(self.registry)} assets loaded")
    
    def _load_assets(self) -> None:
        """Load all asset definitions and sprites"""
        try:
            # Load YAML definitions
            self._load_object_definitions()
            self._load_prefab_definitions()
            
            # Generate procedural sprites if PIL available
            if PIL_AVAILABLE:
                self._generate_tile_sprites()
                self._generate_object_sprites()
                self._generate_actor_sprites()
                self._generate_effect_sprites()
            else:
                logger.warning("⚠️ PIL not available - using placeholder sprites")
                self._generate_placeholder_sprites()
                
        except Exception as e:
            logger.error(f"💥 Failed to load assets: {e}")
            raise
    
    def _load_object_definitions(self) -> None:
        """Load object definitions from YAML"""
        objects_file = self.assets_path / "objects.yaml"
        
        if not objects_file.exists():
            logger.warning(f"⚠️ Objects file not found: {objects_file}")
            return
        
        try:
            with open(objects_file, 'r') as f:
                objects_data = yaml.safe_load(f)
            
            for object_id, obj_data in objects_data.items():
                # Parse characteristics
                characteristics = None
                if 'characteristics' in obj_data:
                    char_data = obj_data['characteristics']
                    characteristics = ObjectCharacteristics(
                        material=char_data.get('material', 'unknown'),
                        state=char_data.get('state', 'normal'),
                        rarity=char_data.get('rarity', 1.0),
                        integrity=char_data.get('integrity', 100),
                        triggers=char_data.get('triggers', {}),
                        tags=char_data.get('tags', []),
                        interaction_hooks=char_data.get('interaction_hooks', []),
                        d20_checks=char_data.get('d20_checks', {}),
                        combat_stats=char_data.get('combat_stats', {}),
                        resistances=char_data.get('resistances', []),
                        weaknesses=char_data.get('weaknesses', [])
                    )
                
                # Create asset definition
                asset_def = AssetDefinition(
                    asset_id=object_id,
                    asset_type=AssetType.OBJECT,
                    sprite_id=obj_data.get('sprite_id', object_id),
                    characteristics=characteristics,
                    collision=obj_data.get('collision', False),
                    friction=obj_data.get('friction', 1.0),
                    metadata=obj_data.get('metadata', {})
                )
                
                self.registry[object_id] = asset_def
                
            logger.info(f"📦 Loaded {len(objects_data)} object definitions")
            
        except Exception as e:
            logger.error(f"💥 Failed to load objects.yaml: {e}")
    
    def _load_prefab_definitions(self) -> None:
        """Load prefab definitions from YAML"""
        prefabs_file = self.assets_path / "prefabs.yaml"
        
        if not prefabs_file.exists():
            logger.warning(f"⚠️ Prefabs file not found: {prefabs_file}")
            return
        
        try:
            with open(prefabs_file, 'r') as f:
                prefabs_data = yaml.safe_load(f)
            
            for prefab_id, prefab_data in prefabs_data.items():
                asset_def = AssetDefinition(
                    asset_id=prefab_id,
                    asset_type=AssetType.OBJECT,
                    sprite_id=prefab_data.get('sprite_id', prefab_id),
                    collision=prefab_data.get('collision', False),
                    friction=prefab_data.get('friction', 1.0),
                    metadata=prefab_data.get('metadata', {})
                )
                
                self.registry[prefab_id] = asset_def
                
            logger.info(f"🏗️ Loaded {len(prefabs_data)} prefab definitions")
            
        except Exception as e:
            logger.error(f"💥 Failed to load prefabs.yaml: {e}")
    
    def _generate_tile_sprites(self) -> None:
        """Generate procedural tile sprites"""
        for tile_type in TileType:
            sprite = self._create_tile_sprite(tile_type)
            self.tile_sprites[tile_type] = sprite
        
        logger.info(f"🎨 Generated {len(self.tile_sprites)} tile sprites")
    
    def _generate_object_sprites(self) -> None:
        """Generate procedural object sprites based on characteristics"""
        for asset_id, asset_def in self.registry.items():
            if asset_def.asset_type == AssetType.OBJECT:
                sprite = self._create_object_sprite(asset_def)
                self.object_sprites[asset_id] = sprite
        
        logger.info(f"🎨 Generated {len(self.object_sprites)} object sprites")
    
    def _generate_actor_sprites(self) -> None:
        """Generate procedural actor sprites with states"""
        # Voyager sprites
        voyager_states = ["idle", "moving", "pondering", "interacting"]
        self.actor_sprites["voyager"] = {}
        
        for state in voyager_states:
            sprite = self._create_actor_sprite("voyager", state)
            self.actor_sprites["voyager"][state] = sprite
        
        # Generic persona sprites
        persona_states = ["idle", "talking", "working"]
        self.actor_sprites["persona"] = {}
        
        for state in persona_states:
            sprite = self._create_actor_sprite("persona", state)
            self.actor_sprites["persona"][state] = sprite
        
        logger.info(f"🎨 Generated actor sprites for multiple states")
    
    def _generate_effect_sprites(self) -> None:
        """Generate procedural effect sprites"""
        try:
            effect_types = ["fire", "water", "blood", "magic", "smoke"]
            
            for effect_type in effect_types:
                sprite = self._create_effect_sprite(effect_type)
                self.effect_sprites[effect_type] = sprite
            
            logger.info(f"🎨 Generated {len(self.effect_sprites)} effect sprites")
        
        except Exception as e:
            logger.error(f"💥 Failed to generate effect sprites: {e}")
    
    def _create_effect_sprite(self, effect_type: str) -> Image.Image:
        """Create a procedural effect sprite"""
        sprite = Image.new((8, 8), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sprite)
        
        if effect_type == "fire":
            # Orange/red fire pattern
            draw.ellipse([1, 1, 7, 7], fill=(255, 100, 0, 255))
            draw.ellipse([2, 2, 6, 6], fill=(255, 200, 0, 255))
            draw.ellipse([3, 3, 5, 5], fill=(255, 255, 0, 255))
        elif effect_type == "water":
            # Blue water droplet
            draw.ellipse([1, 2, 7, 6], fill=(0, 100, 200, 255))
            draw.ellipse([2, 3, 6, 5], fill=(0, 150, 255, 255))
        elif effect_type == "blood":
            # Red blood splatter
            draw.ellipse([1, 1, 7, 7], fill=(200, 0, 0, 255))
            draw.ellipse([3, 3, 5, 5], fill=(255, 0, 0, 255))
        elif effect_type == "magic":
            # Purple magic spark
            draw.polygon([(4, 1), (7, 4), (4, 7), (1, 4)], fill=(200, 0, 255, 255))
            draw.ellipse([3, 3, 5, 5], fill=(255, 150, 255, 255))
        elif effect_type == "smoke":
            # Gray smoke cloud
            draw.ellipse([1, 2, 7, 6], fill=(100, 100, 100, 128))
            draw.ellipse([2, 3, 6, 5], fill=(150, 150, 150, 128))
        
        return sprite
    
    def _generate_placeholder_sprites(self) -> None:
        """Generate placeholder sprites when PIL is not available"""
        # Create simple colored rectangles as placeholders
        for tile_type in TileType:
            # This would be replaced with actual PIL-based sprites
            pass
    
    def _create_tile_sprite(self, tile_type: TileType) -> Image.Image:
        """Create procedural tile sprite"""
        sprite = Image.new('RGB', (TILE_SIZE_PIXELS, TILE_SIZE_PIXELS), COLOR_PALETTE["darkest"])
        draw = ImageDraw.Draw(sprite)
        
        # Generate tile pattern based on type
        if tile_type == TileType.GRASS:
            # Simple grass pattern
            draw.rectangle([0, 0, TILE_SIZE_PIXELS-1, TILE_SIZE_PIXELS-1], 
                         fill=COLOR_PALETTE["light"])
            # Add some texture
            for i in range(0, TILE_SIZE_PIXELS, 2):
                for j in range(0, TILE_SIZE_PIXELS, 2):
                    if (i + j) % 4 == 0:
                        draw.point([i, j], fill=COLOR_PALETTE["dark"])
                        
        elif tile_type == TileType.STONE:
            # Stone pattern
            draw.rectangle([0, 0, TILE_SIZE_PIXELS-1, TILE_SIZE_PIXELS-1], 
                         fill=COLOR_PALETTE["dark"])
            # Add some variation
            draw.point([2, 2], fill=COLOR_PALETTE["lightest"])
            draw.point([5, 3], fill=COLOR_PALETTE["light"])
            draw.point([3, 6], fill=COLOR_PALETTE["dark"])
            
        elif tile_type == TileType.WATER:
            # Water pattern
            draw.rectangle([0, 0, TILE_SIZE_PIXELS-1, TILE_SIZE_PIXELS-1], 
                         fill=COLOR_PALETTE["dark"])
            # Add wave effect
            for i in range(0, TILE_SIZE_PIXELS, 3):
                draw.line([i, 2, i+2, 4], fill=COLOR_PALETTE["light"])
                
        elif tile_type == TileType.FOREST:
            # Forest pattern
            draw.rectangle([0, 0, TILE_SIZE_PIXELS-1, TILE_SIZE_PIXELS-1], 
                         fill=COLOR_PALETTE["light"])
            # Add tree pattern
            draw.ellipse([2, 2, 6, 6], fill=COLOR_PALETTE["dark"])
            draw.rectangle([3, 6, 5, 7], fill=COLOR_PALETTE["dark"])
            
        else:
            # Default pattern
            draw.rectangle([0, 0, TILE_SIZE_PIXELS-1, TILE_SIZE_PIXELS-1], 
                         fill=COLOR_PALETTE["light"])
        
        return sprite
    
    def _create_object_sprite(self, asset_def: AssetDefinition) -> Image.Image:
        """Create procedural object sprite based on characteristics"""
        sprite = Image.new('RGB', (TILE_SIZE_PIXELS, TILE_SIZE_PIXELS), COLOR_PALETTE["darkest"])
        draw = ImageDraw.Draw(sprite)
        
        # Generate sprite based on object type and characteristics
        if asset_def.characteristics:
            char = asset_def.characteristics
            
            if "container" in char.tags:
                # Draw chest/container
                if char.material == "iron":
                    color = COLOR_PALETTE["dark"]
                elif char.material == "wood":
                    color = (139, 69, 19)  # Brown
                else:
                    color = COLOR_PALETTE["light"]
                
                draw.rectangle([1, 3, 6, 6], fill=color, outline=COLOR_PALETTE["darkest"])
                
                # Draw lock if locked
                if char.state == "locked":
                    draw.rectangle([3, 4, 4, 5], fill=COLOR_PALETTE["lightest"])
                    
            elif "door" in char.tags:
                # Draw door
                draw.rectangle([1, 1, 6, 7], fill=COLOR_PALETTE["dark"], outline=COLOR_PALETTE["light"])
                # Draw handle
                draw.point([5, 4], fill=COLOR_PALETTE["lightest"])
                
            elif "fire" in char.tags or char.tags == ["fire"]:
                # Draw fire
                draw.ellipse([2, 2, 6, 6], fill=COLOR_PALETTE["light"])
                draw.ellipse([3, 3, 5, 5], fill=COLOR_PALETTE["lightest"])
                
            elif "thorns" in char.tags:
                # Draw thorns
                for i in range(0, TILE_SIZE_PIXELS, 2):
                    for j in range(0, TILE_SIZE_PIXELS, 2):
                        if (i + j) % 3 == 0:
                            draw.line([i, j, i+1, j+1], fill=COLOR_PALETTE["dark"])
                            
            else:
                # Default object
                draw.rectangle([2, 2, 5, 5], fill=COLOR_PALETTE["light"], outline=COLOR_PALETTE["dark"])
        else:
            # Simple placeholder
            draw.rectangle([2, 2, 5, 5], fill=COLOR_PALETTE["light"], outline=COLOR_PALETTE["dark"])
        
        return sprite
    
    def _create_actor_sprite(self, actor_type: str, state: str) -> Image.Image:
        """Create procedural actor sprite with state"""
        sprite = Image.new('RGB', (TILE_SIZE_PIXELS, TILE_SIZE_PIXELS), COLOR_PALETTE["darkest"])
        draw = ImageDraw.Draw(sprite)
        
        if actor_type == "voyager":
            # Voyager sprite
            if state == "idle":
                color = COLOR_PALETTE["lightest"]
            elif state == "moving":
                color = COLOR_PALETTE["light"]
            elif state == "pondering":
                color = (255, 255, 0)  # Yellow when thinking
            elif state == "interacting":
                color = (0, 255, 255)  # Cyan when interacting
            else:
                color = COLOR_PALETTE["light"]
            
            # Draw simple humanoid figure
            draw.ellipse([3, 1, 4, 2], fill=color)  # Head
            draw.rectangle([3, 3, 4, 6], fill=color)  # Body
            
        elif actor_type == "persona":
            # Persona sprite
            if state == "talking":
                color = (255, 200, 0)  # Orange when talking
            elif state == "working":
                color = COLOR_PALETTE["dark"]
            else:
                color = COLOR_PALETTE["light"]
            
            # Draw simple figure
            draw.ellipse([3, 1, 4, 2], fill=color)
            draw.rectangle([3, 3, 4, 6], fill=color)
        
        return sprite
    
    def _generate_actor_sprites(self) -> None:
        """Generate actor sprites for multiple states"""
        try:
            # Generate Voyager sprites
            voyager_states = ["idle", "moving", "interacting", "combat"]
            
            for state in voyager_states:
                # Generate voyager sprite
                voyager_img = Image.new((16, 16), (255, 255, 255, 0))
                voyager_draw = ImageDraw.Draw(voyager_img)
                
                if state == "idle":
                    # Blue circle for idle
                    voyager_draw.ellipse([2, 2, 14, 14], fill=(0, 100, 255, 255))
                elif state == "moving":
                    # Blue triangle for moving
                    voyager_draw.polygon([(8, 2), (2, 14), (14, 14)], fill=(0, 150, 255, 255))
                elif state == "interacting":
                    # Blue square with interaction indicator
                    voyager_draw.rectangle([2, 2, 14, 14], fill=(0, 200, 255, 255))
                    voyager_draw.ellipse([6, 6, 10, 10], fill=(255, 255, 0, 255))
                elif state == "combat":
                    # Blue diamond for combat
                    voyager_draw.polygon([(8, 2), (14, 8), (8, 14), (2, 8)], fill=(0, 100, 255, 255))
                
                # Create both left and right facing versions for combat
                self._create_sprite_variant(voyager_img, f"voyager_{state}_left")
                self._create_sprite_variant(voyager_img, f"voyager_{state}_right")
                
                # Default sprite (left-facing for combat)
                self._create_sprite_variant(voyager_img, f"voyager_{state}")
            
            # Generate enemy sprites with orientations
            enemy_types = ["guardian", "forest_imp", "shadow_beast"]
            
            for enemy_type in enemy_types:
                # Generate base enemy sprite
                enemy_img = Image.new((16, 16), (255, 255, 255, 0))
                enemy_draw = ImageDraw.Draw(enemy_img)
                
                if enemy_type == "guardian":
                    # Stone guardian - gray diamond
                    enemy_draw.polygon([(8, 2), (14, 8), (8, 14), (2, 8)], fill=(128, 128, 128, 255))
                    enemy_draw.polygon([(8, 4), (12, 8), (8, 12), (4, 8)], fill=(96, 96, 96, 255))
                elif enemy_type == "forest_imp":
                    # Forest imp - green triangle
                    enemy_draw.polygon([(8, 2), (2, 14), (14, 14)], fill=(0, 128, 0, 255))
                    enemy_draw.ellipse([6, 6, 10, 10], fill=(255, 0, 0, 255))
                elif enemy_type == "shadow_beast":
                    # Shadow beast - purple circle
                    enemy_draw.ellipse([2, 2, 14, 14], fill=(128, 0, 128, 255))
                    enemy_draw.ellipse([4, 4, 12, 12], fill=(64, 0, 64, 255))
                
                # Create both left and right facing versions
                self._create_sprite_variant(enemy_img, f"{enemy_type}_left")
                self._create_sprite_variant(enemy_img, f"{enemy_type}_right")
                
                # Default sprite
                self._create_sprite_variant(enemy_img, enemy_type)
            
            logger.info("🎨 Generated actor sprites for multiple states and orientations")
        
        except Exception as e:
            logger.error(f"💥 Failed to generate actor sprites: {e}")
            # Generate minimal fallback sprites
            self._generate_fallback_sprites()
    
    def _generate_fallback_sprites(self) -> None:
        """Generate minimal fallback sprites"""
        try:
            # Generate simple colored squares as fallbacks
            basic_sprites = {
                "voyager_idle": (0, 100, 255),
                "voyager_combat": (0, 150, 255),
                "guardian": (128, 128, 128),
                "forest_imp": (0, 128, 0),
                "shadow_beast": (128, 0, 128)
            }
            
            for sprite_id, color in basic_sprites.items():
                img = Image.new((16, 16), (255, 255, 255, 0))
                draw = ImageDraw.Draw(img)
                draw.rectangle([2, 2, 14, 14], fill=color + (255,))
                
                photo = ImageTk.PhotoImage(img)
                self.registry[sprite_id] = photo
                self._sprite_refs.append(photo)
            
            logger.info("🎨 Generated fallback sprites")
        
        except Exception as e:
            logger.error(f"💥 Failed to generate fallback sprites: {e}")
    
    def _create_sprite_variant(self, image: Image.Image, sprite_id: str) -> None:
        """Create a sprite variant and store it"""
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(image)
        
        # Store in registry
        self.registry[sprite_id] = photo
        
        # Store reference to prevent garbage collection
        self._sprite_refs.append(photo)
    
    def get_actor_sprite(self, actor_id: str, state: str = "idle", orientation: str = "left") -> Optional[ImageTk.PhotoImage]:
        """Get actor sprite with state and orientation"""
        sprite_id = f"{actor_id}_{state}_{orientation}"
        return self.registry.get(sprite_id)
    
    def get_combat_sprite(self, entity_id: str, orientation: str = "left") -> Optional[ImageTk.PhotoImage]:
        """Get combat-oriented sprite"""
        # Try combat state first, then fallback to idle
        combat_sprite = self.get_actor_sprite(entity_id, "combat", orientation)
        if combat_sprite:
            return combat_sprite
        
        return self.get_actor_sprite(entity_id, "idle", orientation)
    
    def get_effect_sprite(self, effect_type: str) -> Optional[Image.Image]:
        """Get effect sprite"""
        return self.effect_sprites.get(effect_type)
    
    def get_asset_definition(self, asset_id: str) -> Optional[AssetDefinition]:
        """Get complete asset definition"""
        return self.registry.get(asset_id)
    
    def get_objects_by_tag(self, tag: str) -> List[AssetDefinition]:
        """Get all objects with specific tag"""
        return [
            asset_def for asset_def in self.registry.values()
            if asset_def.characteristics and asset_def.characteristics.has_tag(tag)
        ]
    
    def get_spawnable_objects(self) -> List[AssetDefinition]:
        """Get all objects that can be spawned in the world"""
        return [
            asset_def for asset_def in self.registry.values()
            if asset_def.asset_type == AssetType.OBJECT and asset_def.characteristics
        ]


class ObjectRegistry:
    """Registry for managing world objects with systemic characteristics"""
    
    def __init__(self, asset_loader: AssetLoader):
        self.asset_loader = asset_loader
        self.world_objects: Dict[str, AssetDefinition] = {}
        
        logger.info("🏗️ Object Registry initialized")
    
    def spawn_object(self, object_id: str, position: Tuple[int, int]) -> Optional[AssetDefinition]:
        """Spawn object at position"""
        asset_def = self.asset_loader.get_asset_definition(object_id)
        if not asset_def:
            logger.warning(f"⚠️ Object not found: {object_id}")
            return None
        
        # Store in world objects registry
        world_key = f"{position[0]}_{position[1]}_{object_id}"
        self.world_objects[world_key] = asset_def
        
        logger.debug(f"🏗️ Spawned {object_id} at {position}")
        return asset_def
    
    def get_object_at(self, position: Tuple[int, int]) -> Optional[AssetDefinition]:
        """Get object at specific position"""
        # Check if position key exists directly (tuple key)
        if position in self.world_objects:
            return self.world_objects[position]
        
        # Legacy support for string keys
        for key, asset_def in self.world_objects.items():
            # Parse position from key
            if isinstance(key, str):
                parts = key.split('_')
                if len(parts) >= 3:
                    obj_pos = (int(parts[0]), int(parts[1]))
                    if obj_pos == position:
                        return asset_def
        return None
    
    def get_objects_in_radius(self, center: Tuple[int, int], radius: int) -> List[Tuple[Tuple[int, int], AssetDefinition]]:
        """Get all objects within radius"""
        objects = []
        for key, asset_def in self.world_objects.items():
            parts = key.split('_')
            if len(parts) >= 3:
                obj_pos = (int(parts[0]), int(parts[1]))
                distance = abs(center[0] - obj_pos[0]) + abs(center[1] - obj_pos[1])
                if distance <= radius:
                    objects.append((obj_pos, asset_def))
        return objects
    
    def can_interact_with(self, position: Tuple[int, int], action: str) -> bool:
        """Check if object at position supports interaction"""
        asset_def = self.get_object_at(position)
        if asset_def and asset_def.characteristics:
            return asset_def.characteristics.can_interact(action)
        return False
    
    def get_interaction_options(self, position: Tuple[int, int]) -> List[str]:
        """Get available interactions for object at position"""
        asset_def = self.get_object_at(position)
        if asset_def and asset_def.characteristics:
            return asset_def.characteristics.interaction_hooks
        return []
