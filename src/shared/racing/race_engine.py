"""Deterministic Race Engine for Slimes.
Adapted from TurboShells.
"""

import time
from typing import List, Optional
from src.shared.genetics.genome import SlimeGenome
from src.shared.teams.roster import RosterSlime
from src.shared.teams.stat_calculator import calculate_speed
from .race_track import get_terrain_at

class RaceParticipant:
    def __init__(self, slime: RosterSlime):
        self.slime = slime
        self.distance = 0.0
        self.finished = False
        self.rank = 0
        self.base_speed = calculate_speed(slime.genome, slime.level)
        
    def update(self, dt: float, terrain: str):
        if self.finished:
            return
            
        # Terrain modifiers
        mod = 1.0
        if terrain == "water": mod = 0.7
        elif terrain == "rock": mod = 0.5
        
        step = self.base_speed * mod * 10 * dt # scaling factor
        self.distance += step

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
