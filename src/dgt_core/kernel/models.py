"""
DGT Core Models - Pydantic Data Contracts for Assets and Entities
ADR 166: Asset-Logic Separation with Type-Safe Contracts
"""

import json
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field, validator, HttpUrl
from loguru import logger
import time


# === ADR 182: Universal Packet Handshake ===
# Common language for SectorManager (Producer) and TriModalEngine (Consumer)

class DisplayMode(str, Enum):
    """Three display lenses for different environmental pressures"""
    TERMINAL = "terminal"  # Console/CLI - High-speed, low-overhead
    COCKPIT = "cockpit"    # Glass/Grid - Modular dashboards
    PPU = "ppu"           # Near-Gameboy - 60Hz dithered rendering


@dataclass
class RenderLayer:
    """Universal render layer specification"""
    depth: int
    type: str  # "baked", "dynamic", "effect"
    id: str
    x: Optional[int] = None
    y: Optional[int] = None
    effect: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass 
class HUDData:
    """Heads-up display data"""
    line_1: str = ""
    line_2: str = ""
    line_3: str = ""
    line_4: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RenderPacket(BaseModel):
    """Universal render packet for stateless rendering - ADR 182"""
    mode: DisplayMode
    layers: List[RenderLayer] = Field(default_factory=list)
    hud: HUDData = Field(default_factory=HUDData)
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('layers', pre=True)
    def validate_layers(cls, v):
        """Ensure layers are RenderLayer objects"""
        if isinstance(v, list):
            return [RenderLayer(**layer) if isinstance(layer, dict) else layer for layer in v]
        return v
    
    @validator('hud', pre=True)
    def validate_hud(cls, v):
        """Ensure HUD is HUDData object"""
        if isinstance(v, dict):
            return HUDData(**v)
        return v


class MaterialType(str, Enum):
    """Material types for rendering"""
    METAL = "metal"
    STONE = "stone"
    WOOD = "wood"
    FABRIC = "fabric"
    GLASS = "glass"
    ENERGY = "energy"
    ORGANIC = "organic"
    PLASMA = "plasma"
    ETHEREAL = "ether"


class SurfaceProperty(str, Enum):
    """Surface properties for materials"""
    NORMAL = "normal"
    REFLECTIVE = "reflective"
    EMISSIVE = "emissive"
    TRANSPARENT = "transparent"
    GLOWING = "glowing"
    WET = "wet"
    ICY = "icy"
    BURNED = "burned"
    CORRODED = "corroded"


class VisualStyle(str, Enum):
    """Visual rendering styles"""
    SOLID = "solid"
    PATTERNED = "patterned"
    GRADIENT = "gradient"
    ANIMATED = "animated"
    PROCEDURAL = "procedural"
    PIXEL_ART = "pixel_art"


@dataclass
class ColorPalette:
    """Color palette for material rendering"""
    primary: Tuple[int, int, int] = (255, 255, 255)
    secondary: Tuple[int, int, int] = (200, 200, 200)
    accent: Tuple[int, int, int] = (150, 150, 255)
    dark: Tuple[int, int, int] = (50, 50, 50)
    light: Tuple[int, int, int] = (220, 220, 220)
    
    def to_dict(self) -> Dict[str, Tuple[int, int, int]]:
        """Convert to dictionary"""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "dark": self.dark,
            "light": self.light
        }


class MaterialAsset(BaseModel):
    """Pydantic model for material assets"""
    asset_id: str = Field(..., description="Unique material identifier")
    name: str = Field(..., description="Human-readable material name")
    material_type: MaterialType = Field(..., description="Base material type")
    surface_properties: List[SurfaceProperty] = Field(default_factory=list, description="Surface properties")
    
    # Visual properties
    base_color: Tuple[int, int, int] = Field(default=(128, 128, 128), description="Base RGB color")
    accent_color: Optional[Tuple[int, int, int]] = Field(None, description="Accent RGB color")
    palette: Optional[ColorPalette] = Field(None, description="Color palette")
    visual_style: VisualStyle = Field(VisualStyle.SOLID, description="Visual rendering style")
    
    # Physical properties
    hardness: float = Field(default=1.0, ge=0.0, le=10.0, description="Material hardness (0-10)")
    density: float = Field(default=1.0, ge=0.0, le=10.0, description="Material density")
    durability: float = Field(default=100.0, ge=0.0, le=1000.0, description="Durability points")
    reflectivity: float = Field(default=0.0, ge=0.0, le=1.0, description="Reflectivity coefficient")
    emissivity: float = Field(default=0.0, ge=0.0, e=1.0, description="Emissivity coefficient")
    
    # Procedural properties
    noise_scale: float = Field(default=1.0, ge=0.1, le=10.0, description="Procedural noise scale")
    pattern_frequency: float = Field(default=1.0, ge=0.1, le=10.0, description="Pattern frequency")
    animation_speed: float = Field(default=1.0, ge=0.0, le=10.0, description="Animation speed multiplier")
    
    # Asset references
    texture_path: Optional[str] = Field(None, description="Path to texture file")
    shader_path: Optional[str] = Field(None, description="Path to custom shader")
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        use_enum_values = True
    
    @validator('accent_color')
    def validate_accent_color(cls, v, values):
        """Validate accent color is different from base color"""
        if v and v == values['base_color']:
            raise ValueError("Accent color must be different from base color")
        return v
    
    def get_rendering_data(self) -> Dict[str, Any]:
        """Get rendering data for PPU consumption"""
        return {
            "asset_id": self.asset_id,
            "base_color": self.base_color,
            "accent_color": self.accent_color or self.base_color,
            "palette": self.palette.to_dict() if self.palette else None,
            "visual_style": self.visual_style.value,
            "surface_properties": [prop.value for prop in self.surface_properties],
            "physical_properties": {
                "hardness": self.hardness,
                "density": self.density,
                "durability": self.durability,
                "reflectivity": self.reflectivity,
                "emissivity": self.emissivity
            },
            "procedural_properties": {
                "noise_scale": self.noise_scale,
                "pattern_frequency": self.pattern_frequency,
                "animation_speed": self.animation_speed
            },
            "asset_paths": {
                "texture": self.texture_path,
                "shader": self.shader_path
            }
        }


class EntityBlueprint(BaseModel):
    """Pydantic model for entity blueprints"""
    blueprint_id: str = Field(..., description="Unique blueprint identifier")
    name: str = Field(..., description="Human-readable entity name")
    entity_type: str = Field(..., description="Entity type classification")
    category: str = Field(default="generic", description="Entity category")
    
    # Base stats (D&D-style)
    strength: int = Field(default=10, ge=1, le=20, description="Strength attribute")
    dexterity: int = Field(default=10, ge=1, le=20, description="Dexterity attribute")
    constitution: int = Field(default=10, ge=1, le=20, description="Constitution attribute")
    intelligence: int = Field(default=10, ge=1, le=20, description="Intelligence attribute")
    wisdom: int = Field(default=10, ge=1, le=20, description="Wisdom attribute")
    charisma: int = Field(default=10, ge=1, le=20, description="Charisma attribute")
    
    # Combat stats
    armor_class: int = Field(default=10, ge=10, le=30, description="Armor class")
    hit_points: int = Field(default=100, ge=1, le=1000, description="Hit points")
    attack_bonus: int = Field(default=0, ge=-10, le=10, description="Attack bonus")
    damage_bonus: int = Field(default=0, ge=-10, le=10, description="Damage bonus")
    
    # Movement and speed
    speed: int = Field(default=30, ge=5, le=100, description="Movement speed (feet/round)")
    initiative: int = Field(default=0, ge=-10, le=10, description="Initiative modifier")
    
    # Special abilities
    special_abilities: List[str] = Field(default_factory=list, description="Special abilities list")
    resistances: Dict[str, float] = Field(default_factory=dict, description="Damage resistances")
    vulnerabilities: Dict[str, float] = Field(default_factory=dict, description="Damage vulnerabilities")
    
    # Visual properties
    sprite_path: Optional[str] = Field(None, description="Path to sprite file")
    color_scheme: str = Field(default="default", description="Color scheme identifier")
    size_category: str = Field(default="medium", description="Size category (tiny/small/medium/large/huge)")
    
    # Asset references
    material_id: Optional[str] = Field(None, description="Associated material asset ID")
    equipment_slots: List[str] = Field(default_factory=list, description="Equipment slot identifiers")
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        use_enum_values = True
    
    def get_combat_rating(self) -> float:
        """Calculate overall combat rating"""
        # D&D 5e style CR calculation
        hp_mod = (self.hit_points - 10) / 10
        ac_mod = (self.armor_class - 10) / 2
        attack_mod = (self.attack_bonus + self.damage_bonus) / 2
        
        return hp_mod + ac_mod + attack_mod
    
    def get_ability_scores(self) -> Dict[str, int]:
        """Get ability scores for skill checks"""
        return {
            "athletics": self.dexterity,
            "acrobatics": self.dexterity,
            "stealth": self.dexterity,
            "arcana": self.intelligence,
            "history": self.intelligence,
            "investigation": self.wisdom,
            "nature": self.wisdom,
            "religion": self.wisdom,
            "animal_handling": self.wisdom,
            "insight": self.charisma,
            "intimidation": self.charisma,
            "performance": self.charisma,
            "deception": self.charisma
        }
    
    def get_visual_data(self) -> Dict[str, Any]:
        """Get visual data for rendering"""
        return {
            "blueprint_id": self.blueprint_id,
            "entity_type": self.entity_type,
            "category": self.category,
            "sprite_path": self.sprite_path,
            "color_scheme": self.color_scheme,
            "size_category": self.size_category,
            "material_id": self.material_id
        }


class StoryFragment(BaseModel):
    """Pydantic model for LLM-ready narrative fragments"""
    fragment_id: str = Field(..., description="Unique fragment identifier")
    title: str = Field(..., description="Story fragment title")
    content: str = Field(..., description="Story content")
    fragment_type: str = Field(default="generic", description="Fragment type")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Story tags")
    mood: str = Field(default="neutral", description="Story mood")
    setting: str = Field(default="unknown", description="Story setting")
    
    # LLM integration
    prompt_template: Optional[str] = Field(None, description="LLM prompt template")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Context data for LLM")
    
    # Asset references
    entity_references: List[str] = Field(default_factory=list, description="Referenced entity blueprints")
    location_references: List[str] = Field(default_factory=list, description="Referenced locations")
    
    # Narrative structure
    requires_choice: bool = Field(default=False, description="Requires user choice")
    choice_options: List[str] = Field(default_factory=list, description="Available choice options")
    choice_outcomes: Dict[str, str] = Field(default_factory=dict, description="Choice outcomes")
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        use_enum_values = True
    
    def get_llm_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Get LLM-ready prompt"""
        if self.prompt_template:
            # Use custom template if available
            try:
                merged_context = {**context, **self.context_data} if context else self.context_data
                return self.prompt_template.format(**merged_context)
            except KeyError as e:
                logger.warning(f"Template variable not found: {e}")
                return self.content
        
        # Default prompt
        prompt_parts = [f"Title: {self.title}"]
        prompt_parts.append(f"Content: {self.content}")
        
        if self.tags:
            prompt_parts.append(f"Tags: {', '.join(self.tags)}")
        
        if context:
            prompt_parts.append(f"Context: {context}")
        
        return "\n\n".join(prompt_parts)


class AssetRegistry:
    """Registry for managing assets with type-safe contracts"""
    
    def __init__(self, assets_dir: Optional[str] = None):
        self.assets_dir = Path(assets_dir) if assets_dir else Path("src/dgt_core/assets")
        self.materials: Dict[str, MaterialAsset] = {}
        self.blueprints: Dict[str, EntityBlueprint] = {}
        self.stories: Dict[str, StoryFragment] = {}
        
        logger.debug(f"📦 AssetRegistry initialized: {self.assets_dir}")
    
    def load_material(self, material_id: str) -> Optional[MaterialAsset]:
        """Load material from file"""
        try:
            material_path = self.assets_dir / "materials" / f"{material_id}.json"
            if not material_path.exists():
                logger.warning(f"📦 Material not found: {material_id}")
                return None
            
            with open(material_path, 'r') as f:
                data = json.load(f)
            
            material = MaterialAsset(**data)
            self.materials[material_id] = material
            logger.debug(f"📦 Loaded material: {material_id}")
            return material
            
        except Exception as e:
            logger.error(f"📦 Failed to load material {material_id}: {e}")
            return None
    
    def load_blueprint(self, blueprint_id: str) -> Optional[EntityBlueprint]:
        """Load entity blueprint from file"""
        try:
            blueprint_path = self.assets_dir / "entities" / f"{blueprint_id}.json"
            if not blueprint_path.exists():
                logger.warning(f"📦 Blueprint not found: {blueprint_id}")
                return None
            
            with open(blueprint_path, 'r') as f:
                data = json.load(f)
            
            blueprint = EntityBlueprint(**data)
            self.blueprints[blueprint_id] = blueprint
            logger.debug(f"📦 Loaded blueprint: {blueprint_id}")
            return blueprint
            
        except Exception as e:
            logger.error(f"📦 Failed to load blueprint {blueprint_id}: {e}")
            return None
    
    def load_story(self, story_id: str) -> Optional[StoryFragment]:
        """Load story fragment from file"""
        try:
            story_path = self.assets_dir / "stories" / f"{story_id}.json"
            if not story_path.exists():
                logger.warning(f"📦 Story not found: {story_id}")
                return None
            
            with open(story_path, 'r') as f:
                data = json.load(f)
            
            story = StoryFragment(**data)
            self.stories[story_id] = story
            logger.debug(f"📦 Loaded story: {story_id}")
            return story
            
        except Exception as e:
            logger.error(f"📦 Failed to load story {story_id}: {e}")
            return None
    
    def get_material(self, material_id: str) -> Optional[MaterialAsset]:
        """Get material by ID"""
        return self.materials.get(material_id)
    
    def get_blueprint(self, blueprint_id: str) -> Optional[EntityBlueprint]:
        """Get blueprint by ID"""
        return self.blueprints.get(blueprint_id)
    
    def get_story(self, story_id: str) -> Optional[StoryFragment]:
        """Get story fragment by ID"""
        return self.stories.get(story_id)
    
    def list_materials(self) -> List[str]:
        """List all material IDs"""
        return list(self.materials.keys())
    
    def list_blueprints(self) -> List[str]:
        """List all blueprint IDs"""
        return list(self.blueprints.keys())
    
    def list_stories(self) -> List[str]:
        """List all story IDs"""
        return list(self.stories.keys())


# Factory function for easy initialization
def create_asset_registry(assets_dir: Optional[str] = None) -> AssetRegistry:
    """Create an AssetRegistry instance"""
    return AssetRegistry(assets_dir)


# Global instance
asset_registry = create_asset_registry()
