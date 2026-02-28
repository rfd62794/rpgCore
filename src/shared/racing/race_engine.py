"""Deterministic Race Engine for Slimes.
Adapted from TurboShells.
"""

import time
import math
from typing import List, Optional
from src.shared.genetics.genome import SlimeGenome, calculate_race_stats
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
        
        # Lap tracking
        self.laps_complete = 0
        self.finish_position = 0
        
        # Calculate race stats from genome
        race_stats = calculate_race_stats(slime.genome)
        self.mass = race_stats["mass"]
        self.heft_power = race_stats["heft_power"]
        self.strength = race_stats["strength"]
        
        # Jump state
        self.jump_phase = 0.0      # 0.0 = grounded, 0-1 = in jump arc
        self.jump_height = 0.0     # current visual height
        self.is_jumping = False
        self.jump_cooldown = 0.0   # recovery time after landing
        
        # Jump stats from race calculation
        self.jump_distance = race_stats["jump_distance"]
        self.jump_speed = 0.8 + slime.genome.energy * 0.4  # Still use energy for rhythm
        self.jump_recovery = race_stats["jump_cooldown"]
        self.max_jump_height = race_stats["jump_height"]  # Store max height separately
        
        # Physics constants
        self.acceleration_base = self.base_speed * 15.0  # Scales with stats
        self.drag_coefficient = 0.95                    # Simple air/ground resistance
        
    def update(self, dt: float, terrain: str):
        if self.finished:
            self.velocity *= 0.9 # Slow down after finish
            return
            
        # Jump physics update
        self._update_jump(dt)
        
        # Terrain affects jump performance based on mass and strength
        terrain_mod = get_terrain_speed_modifier(terrain, self.slime.genome.cultural_base.value)
        
        # Additional terrain modifiers based on mass
        if terrain == "water":
            # Heavy slimes sink more in water
            water_penalty = self.mass * 0.3  # Heavy slimes get extra penalty
            terrain_mod = max(0.3, terrain_mod - water_penalty)
        elif terrain == "rock":
            # Heavy slimes carry momentum through rock
            if self.mass > 0.7:  # Heavy slimes
                terrain_mod = min(1.2, terrain_mod + 0.2)  # Bonus for heavy mass
            else:  # Light slimes bounce off
                terrain_mod = max(0.4, terrain_mod - 0.3)
        elif terrain == "mud":
            # Heavy slimes get stuck in mud
            mud_penalty = self.mass * 0.4
            terrain_mod = max(0.2, terrain_mod - mud_penalty)
        
        # Distance gained during jump (affected by terrain)
        distance_gained = 0.0
        if self.is_jumping:
            # Jumping OVER terrain: reduced penalty
            jump_terrain_mod = min(1.0, terrain_mod + 0.3)  # 30% less penalty when jumping
            distance_gained = self.jump_distance * jump_terrain_mod * dt
        elif self.jump_cooldown > 0:
            # Recovery: slower movement
            distance_gained = self.jump_distance * 0.1 * terrain_mod * dt
        else:
            # Auto-jump: normal movement
            distance_gained = self.jump_distance * terrain_mod * dt
        
        self.distance += distance_gained
        
        # Update velocity for compatibility (distance gained per second)
        self.velocity = distance_gained / dt if dt > 0 else 0.0
    
    def _update_jump(self, dt: float):
        """Update jump physics."""
        if self.is_jumping:
            self.jump_phase += self.jump_speed * dt
            
            # Arc: sin curve for smooth up/down
            # Use calculated jump height from race stats
            self.jump_height = math.sin(self.jump_phase * math.pi) * self.max_jump_height
            
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
        self.total_laps = 3
        self.lap_distance = length / self.total_laps
        self._finish_order = []
        self._finished = False
        
    def tick(self, dt: float):
        if self._finished:
            return
            
        for p in self.participants:
            if not p.finished:
                terrain = get_terrain_at(self.track, p.distance)
                p.update(dt, terrain)
                
                # Lap crossing check
                if p.distance >= self.lap_distance:
                    p.distance -= self.lap_distance  # wrap position
                    p.laps_complete += 1
                    
                    # Check if race finished
                    if p.laps_complete >= self.total_laps:
                        p.finished = True
                        p.finish_position = len(self._finish_order) + 1
                        self._finish_order.append(p)
                        p.rank = p.finish_position
                    
                # Also check if reached final distance (backup)
                elif p.distance >= self.length:
                    p.distance = self.length
                    if not p.finished:
                        p.finished = True
                        p.finish_position = len(self._finish_order) + 1
                        self._finish_order.append(p)
                        p.rank = p.finish_position
                    
        if all(p.finished for p in self.participants):
            self._finished = True
            
    def is_finished(self) -> bool:
        return self._finished
