"""
Shell Engine - TurboShell Physics Runner
ADR 158: Legacy RPG Physics with Modern Kernel Integration
"""

import time
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from .shell_wright import ShellWright, ShellAttributes, ShellRole
from ..space.ship_genetics import ShipGenome


class CombatAction(str, Enum):
    """TurboShell combat actions"""
    ATTACK = "attack"
    DEFEND = "defend"
    HEAL = "heal"
    BUFF = "buff"
    DEBUFF = "debuff"
    DODGE = "dodge"


@dataclass
class ShellEntity:
    """TurboShell entity with RPG attributes"""
    entity_id: str
    shell: ShellAttributes
    x: float = 0.0
    y: float = 0.0
    current_action: CombatAction = CombatAction.ATTACK
    action_cooldown: float = 0.0
    status_effects: List[str] = None
    
    def __post_init__(self):
        if self.status_effects is None:
            self.status_effects = []
    
    def is_alive(self) -> bool:
        """Check if entity is still alive"""
        return self.shell.hit_points > 0.0
    
    def take_damage(self, damage: float) -> float:
        """Apply damage and return actual damage dealt"""
        # Check for dodge
        if random.random() < self.shell.evasion:
            return 0.0  # Dodged
        
        # Apply damage with armor class reduction
        damage_reduction = max(0, (self.shell.armor_class - 10) * 0.1)  # AC 10 = 0 reduction
        actual_damage = max(1.0, damage - damage_reduction)
        
        self.shell.hit_points = max(0.0, self.shell.hit_points - actual_damage)
        return actual_damage
    
    def heal(self, amount: float) -> float:
        """Apply healing"""
        old_hp = self.shell.hit_points
        self.shell.hit_points = min(self.shell.max_hit_points, self.shell.hit_points + amount)
        return self.shell.hit_points - old_hp
    
    def can_act(self) -> bool:
        """Check if entity can perform action"""
        return self.action_cooldown <= 0.0 and self.is_alive()
    
    def get_attack_damage(self) -> float:
        """Calculate attack damage"""
        base_damage = 8.0  # D&D d8 average
        
        # Add strength bonus
        strength_bonus = (self.shell.strength - 10) * 0.5
        damage_bonus = self.shell.damage_bonus
        
        total_damage = base_damage + strength_bonus + damage_bonus
        
        # Check for critical hit
        if random.random() < self.shell.critical_chance:
            total_damage *= 2.0  # Critical hit
        
        return max(1.0, total_damage)


class ShellEngine:
    """TurboShell physics runner with RPG mechanics"""
    
    def __init__(self, party_size: int = 5):
        self.party_size = party_size
        self.shell_wright = ShellWright()
        self.entities: Dict[str, ShellEntity] = {}
        self.simulation_time: float = 0.0
        self.dt: float = 0.1  # 10 FPS for turn-based RPG
        
        logger.info(f"🐢 ShellEngine initialized: party_size={party_size}")
    
    def create_party_from_genomes(self, genomes: List[ShipGenome]) -> Dict[str, ShellEntity]:
        """Create party from list of genomes"""
        party = {}
        
        for i, genome in enumerate(genomes):
            entity_id = f"shell_{i:03d}"
            
            # Convert genome to shell attributes
            shell = self.shell_wright.craft_shell_from_genome(genome)
            
            # Create entity
            entity = ShellEntity(
                entity_id=entity_id,
                shell=shell,
                x=float(i * 30),  # Spread out entities
                y=float(100 + (i % 2) * 30)
            )
            
            party[entity_id] = entity
        
        self.entities = party
        logger.info(f"🐢 Created party: {len(party)} shells")
        return party
    
    def update_simulation(self, target_assignments: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Update one frame of simulation"""
        frame_results = {
            'entities_updated': 0,
            'damage_events': [],
            'healing_events': [],
            'deaths': [],
            'simulation_time': self.simulation_time
        }
        
        # Update each entity
        for entity_id, entity in self.entities.items():
            if not entity.is_alive():
                continue
            
            # Update cooldowns
            entity.action_cooldown = max(0.0, entity.action_cooldown - self.dt)
            
            # Determine action based on role and target
            if entity.can_act():
                target_entity_id = target_assignments.get(entity_id)
                
                if target_entity_id and target_entity_id in self.entities:
                    target_entity = self.entities[target_entity_id]
                    
                    # Perform action based on role
                    action_result = self._perform_role_action(entity, target_entity)
                    
                    if action_result:
                        frame_results.update(action_result)
                        entity.action_cooldown = 1.0  # 1 second cooldown
            
            frame_results['entities_updated'] += 1
        
        # Update simulation time
        self.simulation_time += self.dt
        
        return frame_results
    
    def _perform_role_action(self, actor: ShellEntity, target: ShellEntity) -> Optional[Dict[str, Any]]:
        """Perform action based on entity role"""
        if actor.shell.primary_role == ShellRole.HEALER:
            # Healers heal damaged allies
            if target.is_alive() and target.shell.hit_points < target.shell.max_hit_points * 0.8:
                healing = actor.shell.wisdom * 2.0  # Healing based on wisdom
                actual_healing = target.heal(healing)
                
                return {
                    'healing_events': [{
                        'healer': actor.entity_id,
                        'target': target.entity_id,
                        'healing': actual_healing
                    }]
                }
        
        elif actor.shell.primary_role == ShellRole.TANK:
            # Tanks defend or attack
            if random.random() < 0.3:  # 30% chance to defend
                actor.current_action = CombatAction.DEFEND
                return None
            else:
                return self._perform_attack(actor, target)
        
        elif actor.shell.primary_role == ShellRole.SUPPORT:
            # Support buffs or debuffs
            if random.random() < 0.4:  # 40% chance to buff
                return self._perform_buff(actor, target)
            else:
                return self._perform_attack(actor, target)
        
        # Default: attack
        return self._perform_attack(actor, target)
    
    def _perform_attack(self, attacker: ShellEntity, target: ShellEntity) -> Dict[str, Any]:
        """Perform attack action"""
        # Calculate attack roll
        attack_roll = random.randint(1, 20) + attacker.shell.attack_bonus
        target_ac = target.shell.armor_class
        
        if attack_roll >= target_ac:
            # Hit! Calculate damage
            damage = attacker.get_attack_damage()
            actual_damage = target.take_damage(damage)
            
            result = {
                'damage_events': [{
                    'attacker': attacker.entity_id,
                    'target': target.entity_id,
                    'damage': actual_damage,
                    'attack_roll': attack_roll,
                    'target_ac': target_ac
                }]
            }
            
            # Check for death
            if not target.is_alive():
                result['deaths'] = [target.entity_id]
            
            return result
        
        # Miss
        return {
            'damage_events': [{
                'attacker': attacker.entity_id,
                'target': target.entity_id,
                'damage': 0.0,
                'attack_roll': attack_roll,
                'target_ac': target_ac,
                'miss': True
            }]
        }
    
    def _perform_buff(self, supporter: ShellEntity, target: ShellEntity) -> Dict[str, Any]:
        """Perform buff action"""
        # Simple buff: temporary AC increase
        buff_amount = supporter.shell.charisma * 0.5
        target.shell.armor_class += buff_amount
        
        return {
            'buff_events': [{
                'supporter': supporter.entity_id,
                'target': target.entity_id,
                'buff_type': 'armor_class',
                'buff_amount': buff_amount
            }]
        }
    
    def get_party_status(self) -> Dict[str, Any]:
        """Get current party status"""
        alive_entities = [e for e in self.entities.values() if e.is_alive()]
        dead_entities = [e for e in self.entities.values() if not e.is_alive()]
        
        if not alive_entities:
            return {
                'alive_count': 0,
                'dead_count': len(dead_entities),
                'total_hp': 0.0,
                'avg_hp': 0.0,
                'party_center': (0.0, 0.0)
            }
        
        total_hp = sum(e.shell.hit_points for e in alive_entities)
        avg_hp = total_hp / len(alive_entities)
        
        # Calculate party center
        center_x = sum(e.x for e in alive_entities) / len(alive_entities)
        center_y = sum(e.y for e in alive_entities) / len(alive_entities)
        
        return {
            'alive_count': len(alive_entities),
            'dead_count': len(dead_entities),
            'total_hp': total_hp,
            'avg_hp': avg_hp,
            'party_center': (center_x, center_y)
        }
    
    def get_entity_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries of all entities"""
        summaries = {}
        
        for entity_id, entity in self.entities.items():
            shell_summary = self.shell_wright.get_shell_summary(entity.shell)
            shell_summary.update({
                'entity_id': entity_id,
                'position': (entity.x, entity.y),
                'alive': entity.is_alive(),
                'current_action': entity.current_action.value,
                'cooldown': entity.action_cooldown
            })
            summaries[entity_id] = shell_summary
        
        return summaries
    
    def reset_simulation(self):
        """Reset simulation state"""
        self.simulation_time = 0.0
        
        # Reset all entities to full health
        for entity in self.entities.values():
            entity.shell.hit_points = entity.shell.max_hit_points
            entity.action_cooldown = 0.0
            entity.current_action = CombatAction.ATTACK
        
        logger.info("🐢 Simulation reset")
    
    def get_entity_positions(self) -> Dict[str, Tuple[float, float]]:
        """Get all entity positions"""
        return {
            entity_id: (entity.x, entity.y) 
            for entity_id, entity in self.entities.items()
            if entity.is_alive()
        }


# Factory function for easy initialization
def create_shell_engine(party_size: int = 5) -> ShellEngine:
    """Create a ShellEngine instance"""
    return ShellEngine(party_size)
