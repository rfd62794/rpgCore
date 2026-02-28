"""Deterministic Race Engine for Slimes.
Adapted from TurboShells.
"""

import time
import math
from typing import List, Optional
from src.shared.genetics.genome import SlimeGenome
from src.shared.teams.roster import RosterSlime
from src.shared.teams.stat_calculator import calculate_speed
from .race_track import get_terrain_at, get_terrain_speed_modifier

class RaceParticipant:
    def __init__(self, slime: RosterSlime):
        self.slime = slime
        self.distance = 0.0
        self.velocity = 0.0
        self.finished = False
        self.rank = 0
        self.base_speed = calculate_speed(slime.genome, slime.level)
        
        # Jump state
        self.jump_phase = 0.0      # 0.0 = grounded, 0-1 = in jump arc
        self.jump_height = 0.0     # current visual height
        self.is_jumping = False
        self.jump_cooldown = 0.0   # recovery time after landing
        
        # Jump stats derived from genome
        self.jump_speed = 0.8 + slime.genome.wobble_frequency * 0.4
        self.jump_distance = slime.genome.body_size * 0.5 + self.base_speed * 0.3
        self.jump_recovery = max(0.1, 0.5 - self.base_speed * 0.1)
        
        # Physics constants
        self.acceleration_base = self.base_speed * 15.0  # Scales with stats
        self.drag_coefficient = 0.95                    # Simple air/ground resistance
        
    def update(self, dt: float, terrain: str):
        if self.finished:
            self.velocity *= 0.9 # Slow down after finish
            return
            
        # Jump physics update
        self._update_jump(dt)
        
        # Terrain affects jump performance
        terrain_mod = get_terrain_speed_modifier(terrain, self.slime.genome.cultural_base.value)
        
        # Distance gained during jump (affected by terrain)
        if self.is_jumping:
            # Jumping OVER terrain: reduced penalty
            jump_terrain_mod = min(1.0, terrain_mod + 0.3)  # 30% less penalty when jumping
            self.distance += self.jump_distance * jump_terrain_mod * dt
        elif self.jump_cooldown > 0:
            # Recovery: slower movement
            self.distance += self.jump_distance * 0.1 * terrain_mod * dt
        else:
            # Auto-jump: normal movement
            self.distance += self.jump_distance * terrain_mod * dt
    
    def _update_jump(self, dt: float):
        """Update jump physics."""
        if self.is_jumping:
            self.jump_phase += self.jump_speed * dt
            
            # Arc: sin curve for smooth up/down
            self.jump_height = math.sin(self.jump_phase * math.pi) * 20  # max 20px visual height
            
            # Land when arc complete
            if self.jump_phase >= 1.0:
                self.is_jumping = False
                self.jump_phase = 0.0
                self.jump_height = 0.0
                self.jump_cooldown = self.jump_recovery
        
        elif self.jump_cooldown > 0:
            # Recovery — brief pause on ground
            self.jump_cooldown -= dt
        
        else:
            # Auto-jump: slimes jump continuously
            self.is_jumping = True
            self.jump_phase = 0.0

class RaceEngine:
    def __init__(self, participants: List[RosterSlime], track: List[str], length: int = 1500):
        self.participants = [RaceParticipant(p) for p in participants]
        self.track = track
        self.length = length
        self._finish_order = []
        self._finished = False
        
    def tick(self, dt: float):
        if self._finished:
            return
            
        for p in self.participants:
            if not p.finished:
                terrain = get_terrain_at(self.track, p.distance)
                p.update(dt, terrain)
                
                if p.distance >= self.length:
                    p.distance = self.length
                    p.finished = True
                    self._finish_order.append(p)
                    p.rank = len(self._finish_order)
                    
        if all(p.finished for p in self.participants):
            self._finished = True
            
    def is_finished(self) -> bool:
        return self._finished
