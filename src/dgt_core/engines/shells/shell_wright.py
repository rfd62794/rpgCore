"""
Shell Wright - Genetic-to-Shell Adapter for TurboShells
ADR 157: Legacy RPG to Modern Physics Bridge
"""

from typing import Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from ..space.ship_genetics import ShipGenome


class ShellRole(str, Enum):
    """TurboShell role classifications"""
    TANK = "tank"
    DPS = "dps" 
    HEALER = "healer"
    SUPPORT = "support"
    SCOUT = "scout"


@dataclass
class ShellAttributes:
    """TurboShell RPG attributes"""
    # Physical stats
    strength: float = 10.0
    dexterity: float = 10.0
    constitution: float = 10.0
    intelligence: float = 10.0
    wisdom: float = 10.0
    charisma: float = 10.0
    
    # Combat stats
    armor_class: float = 15.0
    hit_points: float = 100.0
    max_hit_points: float = 100.0
    attack_bonus: float = 5.0
    damage_bonus: float = 5.0
    
    # Speed/movement
    speed: float = 30.0  # Feet per round (D&D 5e standard)
    initiative: float = 0.0
    
    # Special abilities
    critical_chance: float = 0.05  # 5% base
    evasion: float = 0.10  # 10% base
    
    # Role classification
    primary_role: ShellRole = ShellRole.DPS
    secondary_role: Optional[ShellRole] = None


class ShellWright:
    """Adapter that maps ShipGenome to TurboShell attributes"""
    
    def __init__(self):
        # Mapping tables for trait conversion
        self.hull_to_role = {
            'light': ShellRole.SCOUT,
            'medium': ShellRole.DPS,
            'heavy': ShellRole.TANK,
            'stealth': ShellRole.SUPPORT
        }
        
        # Trait weight mappings for D&D-style stats
        self.trait_weights = {
            # Physical traits
            'plating_density': {'strength': 0.8, 'constitution': 0.6, 'armor_class': 1.0},
            'structural_integrity': {'constitution': 1.0, 'hit_points': 1.0},
            'thruster_output': {'dexterity': 0.6, 'speed': 1.0},
            'fuel_efficiency': {'constitution': 0.4, 'dexterity': 0.3},
            
            # Combat traits  
            'weapon_damage': {'strength': 0.4, 'damage_bonus': 1.0},
            'fire_rate': {'dexterity': 0.8, 'attack_bonus': 0.6},
            'targeting_system': {'dexterity': 0.4, 'attack_bonus': 0.8, 'intelligence': 0.3},
            'initiative': {'dexterity': 0.6, 'initiative': 1.0},
            'evasion': {'dexterity': 1.0, 'wisdom': 0.4},
            'critical_chance': {'dexterity': 0.4, 'intelligence': 0.3},
            
            # Systems traits
            'shield_frequency': {'intelligence': 0.6, 'wisdom': 0.4},
            'cooling_capacity': {'constitution': 0.6},
        }
        
        logger.debug("🐢 ShellWright initialized - ShipGenome to TurboShell adapter")
    
    def craft_shell_from_genome(self, genome: ShipGenome) -> ShellAttributes:
        """Convert ShipGenome to TurboShell attributes with asset integration"""
        try:
            # Start with base attributes
            shell = ShellAttributes()
            
            # Map hull type to role
            shell.primary_role = self.hull_to_role.get(genome.hull_type.value, ShellRole.DPS)
            
            # Apply trait mappings
            for trait_name, trait_value in genome.model_dump().items():
                if trait_name in self.trait_weights:
                    self._apply_trait_mapping(shell, trait_name, trait_value)
            
            # Apply role-based adjustments
            self._apply_role_adjustments(shell)
            
            # Calculate derived stats
            self._calculate_derived_stats(shell)
            
            # Apply material-based visual properties
            self._apply_material_properties(shell, genome)
            
            logger.debug(f"🐢 Crafted shell: {shell.primary_role.value} from genome")
            return shell
            
        except Exception as e:
            logger.error(f"🐢 Failed to craft shell from genome: {e}")
            return ShellAttributes()  # Return default shell on error
    
    def _apply_trait_mapping(self, shell: ShellAttributes, trait_name: str, trait_value: float):
        """Apply individual trait mapping to shell attributes"""
        mappings = self.trait_weights.get(trait_name, {})
        
        for attr_name, weight in mappings.items():
            if hasattr(shell, attr_name):
                current_value = getattr(shell, attr_name)
                
                # Apply weighted modification
                if attr_name in ['armor_class', 'attack_bonus', 'damage_bonus']:
                    # These are additive bonuses
                    modifier = (trait_value - 1.0) * weight * 5  # Scale to D&D bonus ranges
                    setattr(shell, attr_name, current_value + modifier)
                elif attr_name == 'hit_points':
                    # HP is multiplicative
                    modifier = trait_value * weight
                    setattr(shell, attr_name, current_value * modifier)
                    shell.max_hit_points = shell.hit_points
                elif attr_name == 'speed':
                    # Speed is in feet/round
                    modifier = trait_value * weight * 10  # Scale to movement ranges
                    setattr(shell, attr_name, current_value + modifier)
                elif attr_name in ['critical_chance', 'evasion']:
                    # These are percentages (0.0 to 1.0)
                    modifier = (trait_value - 1.0) * weight * 0.1  # Scale to percentage ranges
                    setattr(shell, attr_name, max(0.0, min(1.0, current_value + modifier)))
                else:
                    # Standard stats are multiplicative
                    modifier = trait_value * weight
                    setattr(shell, attr_name, current_value * modifier)
    
    def _apply_role_adjustments(self, shell: ShellAttributes):
        """Apply role-specific adjustments to shell attributes"""
        role_bonuses = {
            ShellRole.TANK: {
                'constitution': 1.2,
                'armor_class': 1.1,
                'hit_points': 1.3,
                'speed': 0.9
            },
            ShellRole.DPS: {
                'strength': 1.15,
                'dexterity': 1.1,
                'attack_bonus': 1.2,
                'damage_bonus': 1.15
            },
            ShellRole.HEALER: {
                'wisdom': 1.3,
                'intelligence': 1.2,
                'charisma': 1.1
            },
            ShellRole.SUPPORT: {
                'charisma': 1.2,
                'intelligence': 1.15,
                'wisdom': 1.1
            },
            ShellRole.SCOUT: {
                'dexterity': 1.2,
                'speed': 1.3,
                'evasion': 1.15,
                'initiative': 1.1
            }
        }
        
        bonuses = role_bonuses.get(shell.primary_role, {})
        
        for attr_name, multiplier in bonuses.items():
            if hasattr(shell, attr_name):
                current_value = getattr(shell, attr_name)
                setattr(shell, attr_name, current_value * multiplier)
    
    def _calculate_derived_stats(self, shell: ShellAttributes):
        """Calculate derived stats from base attributes"""
        # Armor class from dexterity and base
        shell.armor_class = 10 + shell.dexterity * 0.5 + shell.armor_class
        
        # Attack bonus from strength/dexterity
        if shell.primary_role in [ShellRole.TANK, ShellRole.DPS]:
            shell.attack_bonus = shell.strength * 0.5 + shell.attack_bonus
        else:
            shell.attack_bonus = shell.dexterity * 0.5 + shell.attack_bonus
        
        # Damage bonus from strength
        shell.damage_bonus = shell.strength * 0.5 + shell.damage_bonus
        
        # Initiative from dexterity
        shell.initiative = shell.dexterity * 0.5 + shell.initiative
        
        # Ensure HP doesn't exceed max
        shell.hit_points = min(shell.hit_points, shell.max_hit_points)
    
    def _apply_material_properties(self, shell: ShellAttributes, genome: ShipGenome):
        """Apply material-based visual properties from assets"""
        try:
            # For now, skip material integration until assets are properly set up
            logger.debug(f"🐢 Material properties skipped for {shell.primary_role.value}")
                
        except Exception as e:
            logger.error(f"🐢 Failed to apply material properties: {e}")
    
    def get_shell_summary(self, shell: ShellAttributes) -> Dict[str, Any]:
        """Get summary of shell attributes for display"""
        summary = {
            'role': shell.primary_role.value,
            'hp': f"{shell.hit_points:.0f}/{shell.max_hit_points:.0f}",
            'ac': f"{shell.armor_class:.0f}",
            'attack': f"+{shell.attack_bonus:.0f}",
            'damage': f"+{shell.damage_bonus:.0f}",
            'speed': f"{shell.speed:.0f} ft",
            'initiative': f"+{shell.initiative:.0f}",
            'critical': f"{shell.critical_chance:.1%}",
            'evasion': f"{shell.evasion:.1%}",
            'stats': {
                'STR': shell.strength,
                'DEX': shell.dexterity,
                'CON': shell.constitution,
                'INT': shell.intelligence,
                'WIS': shell.wisdom,
                'CHA': shell.charisma
            }
        }
        
        # Add visual properties if available
        if hasattr(shell, 'visual_properties'):
            summary['visual'] = shell.visual_properties
        
        return summary
    
    def validate_shell_compatibility(self, shell: ShellAttributes) -> bool:
        """Validate that shell attributes are within reasonable ranges"""
        # D&D 5e typical ranges
        valid_ranges = {
            'strength': (1, 30),
            'dexterity': (1, 30),
            'constitution': (1, 30),
            'intelligence': (1, 30),
            'wisdom': (1, 30),
            'charisma': (1, 30),
            'armor_class': (10, 30),
            'hit_points': (1, 500),
            'attack_bonus': (-5, 15),
            'damage_bonus': (-5, 15),
            'speed': (5, 100),
            'critical_chance': (0.0, 0.5),
            'evasion': (0.0, 0.5)
        }
        
        for attr_name, (min_val, max_val) in valid_ranges.items():
            if hasattr(shell, attr_name):
                value = getattr(shell, attr_name)
                if not (min_val <= value <= max_val):
                    logger.warning(f"🐢 Shell validation failed: {attr_name}={value} not in range [{min_val}, {max_val}]")
                    return False
        
        return True


# Factory function for easy initialization
def create_shell_wright() -> ShellWright:
    """Create a ShellWright instance"""
    return ShellWright()


# Global instance
shell_wright = create_shell_wright()
