"""Deterministic Race Engine for Slimes.
Adapted from TurboShells.
"""

import time
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
        
        # Physics constants
        self.acceleration_base = self.base_speed * 15.0  # Scales with stats
        self.drag_coefficient = 0.95                    # Simple air/ground resistance
        
    def update(self, dt: float, terrain: str):
        if self.finished:
            self.velocity *= 0.9 # Slow down after finish
            return
            
        # 1. Calculate Acceleration with terrain and cultural advantage
        cultural_base = self.slime.genome.cultural_base.value
        terrain_mod = get_terrain_speed_modifier(terrain, cultural_base)
        
        accel = self.acceleration_base * terrain_mod
        
        # 2. Update Velocity
        self.velocity += accel * dt
        
        # 3. Apply Drag (Dynamic friction)
        # Faster slimes hit a higher terminal velocity where drag matches accel
        self.velocity *= (self.drag_coefficient ** (dt * 60)) 
        
        # 4. Update Position
        self.distance += self.velocity * dt

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
