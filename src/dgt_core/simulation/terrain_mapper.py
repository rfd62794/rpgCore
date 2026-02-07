"""
DGT Terrain Mapper
Maps Tiny Farm assets to TurboShells terrain types
Bridge between Volume 2 asset pipeline and Volume 3 racing system
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from enum import Enum

from loguru import logger
from .genetics import TerrainType


class AssetTerrainMapper:
    """Maps Tiny Farm assets to terrain types for racing"""
    
    def __init__(self, asset_manifest_path: Optional[Path] = None):
        self.asset_manifest_path = asset_manifest_path or Path(__file__).parent.parent.parent.parent / "assets" / "ASSET_MANIFEST.yaml"
        self.terrain_mapping = self._load_terrain_mapping()
        self.asset_terrain_cache = {}
        
        logger.info(f"🗺️ Terrain Mapper initialized: {self.asset_manifest_path}")
    
    def _load_terrain_mapping(self) -> Dict[str, TerrainType]:
        """Load or create terrain mapping for Tiny Farm assets"""
        default_mapping = {
            # Grass assets
            'grass': TerrainType.GRASS,
            'grass_tile': TerrainType.GRASS,
            'lawn': TerrainType.GRASS,
            'meadow': TerrainType.GRASS,
            'field': TerrainType.GRASS,
            
            # Water assets
            'water': TerrainType.WATER,
            'water_tile': TerrainType.WATER,
            'pond': TerrainType.WATER,
            'lake': TerrainType.WATER,
            'river': TerrainType.WATER,
            'ocean': TerrainType.WATER,
            
            # Sand assets
            'sand': TerrainType.SAND,
            'sand_tile': TerrainType.SAND,
            'desert': TerrainType.SAND,
            'beach': TerrainType.SAND,
            'dune': TerrainType.SAND,
            
            # Rock assets
            'rock': TerrainType.ROCKS,
            'stone': TerrainType.ROCKS,
            'mountain': TerrainType.ROCKS,
            'cliff': TerrainType.ROCKS,
            'boulder': TerrainType.ROCKS,
            
            # Mud assets
            'mud': TerrainType.MUD,
            'dirt': TerrainType.MUD,
            'soil': TerrainType.MUD,
            'earth': TerrainType.MUD,
            'ground': TerrainType.MUD,
            
            # Boost/special assets
            'boost': TerrainType.BOOST,
            'powerup': TerrainType.BOOST,
            'special': TerrainType.BOOST,
            'magic': TerrainType.BOOST,
            
            # Default
            'default': TerrainType.NORMAL,
            'normal': TerrainType.NORMAL,
            'tile': TerrainType.NORMAL,
            'floor': TerrainType.NORMAL,
            'path': TerrainType.NORMAL
        }
        
        # Try to load custom mapping from file
        custom_mapping_file = Path(__file__).parent.parent.parent.parent / "config" / "terrain_mapping.yaml"
        if custom_mapping_file.exists():
            try:
                with open(custom_mapping_file, 'r') as f:
                    custom_data = yaml.safe_load(f)
                
                if 'asset_terrain_mapping' in custom_data:
                    # Merge with defaults
                    for asset_name, terrain_name in custom_data['asset_terrain_mapping'].items():
                        try:
                            terrain_type = TerrainType(terrain_name.lower())
                            default_mapping[asset_name.lower()] = terrain_type
                        except ValueError:
                            logger.warning(f"Invalid terrain type in mapping: {terrain_name}")
                
                logger.info("🗺️ Loaded custom terrain mapping")
                
            except Exception as e:
                logger.warning(f"🗺️ Failed to load custom mapping: {e}")
        
        return default_mapping
    
    def get_terrain_for_asset(self, asset_name: str) -> TerrainType:
        """Get terrain type for asset name"""
        if asset_name in self.asset_terrain_cache:
            return self.asset_terrain_cache[asset_name]
        
        # Normalize asset name
        asset_lower = asset_name.lower()
        
        # Check exact matches first
        if asset_lower in self.terrain_mapping:
            terrain = self.terrain_mapping[asset_lower]
            self.asset_terrain_cache[asset_name] = terrain
            return terrain
        
        # Check partial matches
        for keyword, terrain in self.terrain_mapping.items():
            if keyword in asset_lower:
                self.asset_terrain_cache[asset_name] = terrain
                return terrain
        
        # Default to normal
        self.asset_terrain_cache[asset_name] = TerrainType.NORMAL
        return TerrainType.NORMAL
    
    def scan_asset_manifest(self) -> Dict[str, TerrainType]:
        """Scan asset manifest and create terrain mapping"""
        if not self.asset_manifest_path.exists():
            logger.warning(f"🗺️ Asset manifest not found: {self.asset_manifest_path}")
            return {}
        
        try:
            with open(self.asset_manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            asset_terrain_map = {}
            
            # Process assets
            if 'assets' in manifest:
                for asset_id, asset_data in manifest['assets'].items():
                    asset_name = asset_data.get('name', asset_id)
                    terrain = self.get_terrain_for_asset(asset_name)
                    asset_terrain_map[asset_id] = terrain
            
            # Process harvested assets
            if 'harvested_assets' in manifest:
                for asset_id, asset_data in manifest['harvested_assets'].items():
                    asset_name = asset_data.get('name', asset_id)
                    terrain = self.get_terrain_for_asset(asset_name)
                    asset_terrain_map[asset_id] = terrain
            
            logger.info(f"🗺️ Mapped {len(asset_terrain_map)} assets to terrain types")
            return asset_terrain_map
            
        except Exception as e:
            logger.error(f"🗺️ Failed to scan asset manifest: {e}")
            return {}
    
    def create_terrain_metadata(self, asset_id: str, terrain: TerrainType) -> Dict[str, Any]:
        """Create terrain metadata for asset"""
        terrain_modifiers = {
            TerrainType.NORMAL: {'speed_mod': 1.0, 'stamina_mod': 1.0},
            TerrainType.GRASS: {'speed_mod': 1.1, 'stamina_mod': 0.9},
            TerrainType.WATER: {'speed_mod': 0.8, 'stamina_mod': 1.3},
            TerrainType.SAND: {'speed_mod': 0.7, 'stamina_mod': 1.4},
            TerrainType.MUD: {'speed_mod': 0.4, 'stamina_mod': 2.0},
            TerrainType.ROCKS: {'speed_mod': 0.6, 'stamina_mod': 1.2},
            TerrainType.BOOST: {'speed_mod': 1.5, 'stamina_mod': 0.8}
        }
        
        modifiers = terrain_modifiers.get(terrain, terrain_modifiers[TerrainType.NORMAL])
        
        return {
            'asset_id': asset_id,
            'terrain_type': terrain.value,
            'speed_modifier': modifiers['speed_mod'],
            'stamina_modifier': modifiers['stamina_mod'],
            'visual_effects': self._get_terrain_effects(terrain)
        }
    
    def _get_terrain_effects(self, terrain: TerrainType) -> Dict[str, Any]:
        """Get visual effects for terrain type"""
        effects = {
            TerrainType.NORMAL: {'particles': False, 'color_tint': None},
            TerrainType.GRASS: {'particles': True, 'particle_type': 'grass', 'color_tint': (34, 139, 34)},
            TerrainType.WATER: {'particles': True, 'particle_type': 'splash', 'color_tint': (100, 150, 255)},
            TerrainType.SAND: {'particles': True, 'particle_type': 'dust', 'color_tint': (238, 203, 173)},
            TerrainType.MUD: {'particles': True, 'particle_type': 'mud', 'color_tint': (101, 67, 33)},
            TerrainType.ROCKS: {'particles': False, 'color_tint': (139, 137, 137)},
            TerrainType.BOOST: {'particles': True, 'particle_type': 'sparkle', 'color_tint': (255, 215, 0)}
        }
        
        return effects.get(terrain, effects[TerrainType.NORMAL])
    
    def export_terrain_mapping(self, output_path: Optional[Path] = None):
        """Export terrain mapping to YAML file"""
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent.parent / "config" / "generated_terrain_mapping.yaml"
        
        try:
            # Scan assets and create mapping
            asset_terrain_map = self.scan_asset_manifest()
            
            # Create export data
            export_data = {
                'metadata': {
                    'generated_at': time.time(),
                    'total_assets': len(asset_terrain_map),
                    'terrain_types': list(set(asset_terrain_map.values()))
                },
                'asset_terrain_mapping': {
                    asset_id: terrain.value 
                    for asset_id, terrain in asset_terrain_map.items()
                },
                'terrain_metadata': {
                    terrain.value: self.create_terrain_metadata('sample', terrain)
                    for terrain in set(asset_terrain_map.values())
                }
            }
            
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(output_path, 'w') as f:
                yaml.dump(export_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"🗺️ Terrain mapping exported: {output_path}")
            
        except Exception as e:
            logger.error(f"🗺️ Failed to export terrain mapping: {e}")
    
    def get_terrain_for_position(self, x: float, y: float, background_data: Dict[str, Any]) -> TerrainType:
        """Get terrain type at world position based on background assets"""
        # This would integrate with the PPU background system
        # For now, return default terrain
        return TerrainType.NORMAL
    
    def validate_terrain_coverage(self, track_checkpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that track has adequate terrain variety"""
        terrain_counts = {}
        terrain_types = set()
        
        for checkpoint in track_checkpoints:
            # Get terrain at checkpoint position
            terrain = self.get_terrain_for_asset(checkpoint.get('asset_name', 'default'))
            terrain_counts[terrain.value] = terrain_counts.get(terrain.value, 0) + 1
            terrain_types.add(terrain)
        
        # Calculate variety score
        max_variety = len(TerrainType)
        actual_variety = len(terrain_types)
        variety_score = actual_variety / max_variety
        
        validation_result = {
            'variety_score': variety_score,
            'terrain_distribution': terrain_counts,
            'total_checkpoints': len(track_checkpoints),
            'recommendations': []
        }
        
        # Add recommendations
        if variety_score < 0.5:
            validation_result['recommendations'].append("Low terrain variety - consider adding more diverse terrain types")
        
        if terrain_counts.get('normal', 0) > len(track_checkpoints) * 0.6:
            validation_result['recommendations'].append("Too much normal terrain - add more specialized terrain")
        
        if terrain_counts.get('boost', 0) == 0:
            validation_result['recommendations'].append("No boost terrain - consider adding boost areas for strategic racing")
        
        return validation_result


# Global terrain mapper instance
terrain_mapper = AssetTerrainMapper()
