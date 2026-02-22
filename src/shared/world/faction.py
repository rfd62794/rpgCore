"""
Faction System - territorial simulation and causality.
Ported and decoupled from dgt_engine for shared use.
"""

import sqlite3
import random
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from loguru import logger

class FactionRelation(Enum):
    ALLIED = "allied"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"
    WAR = "war"

class FactionType(Enum):
    MILITARY = "military"
    RELIGIOUS = "religious"
    ECONOMIC = "economic"
    ISOLATIONIST = "isolationist"

@dataclass
class Faction:
    id: str
    name: str
    type: FactionType
    color: Any  # Can be Tuple (R,G,B) or name
    home_base: Tuple[int, int]
    current_power: float
    territories: List[Tuple[int, int]]
    relations: Dict[str, FactionRelation]
    expansion_rate: float
    aggression_level: float
    last_action_turn: int = 0

@dataclass
class FactionConflict:
    aggressor: str
    defender: str
    coordinate: Tuple[int, int]
    start_turn: int
    end_turn: Optional[int] = None
    outcome: Optional[str] = None

class FactionManager:
    """
    Manages faction simulation, territorial expansion, and persistence.
    """
    def __init__(self, db_path: str = "data/factions.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._initialize_database()
        self.factions: Dict[str, Faction] = {}
        self.conflicts: List[FactionConflict] = []
        
        # Sim params
        self.expansion_chance = 0.3
        
    def _initialize_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS factions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    color TEXT NOT NULL,
                    home_base TEXT NOT NULL,
                    current_power REAL,
                    territories TEXT,
                    relations TEXT,
                    expansion_rate REAL,
                    aggression_level REAL,
                    last_action_turn INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS territories (
                    coordinate TEXT PRIMARY KEY,
                    faction_id TEXT NOT NULL,
                    strength REAL,
                    acquired_turn INTEGER
                )
            """)
            conn.commit()

    def register_faction(self, faction: Faction):
        self.factions[faction.id] = faction
        self._save_faction(faction)
        self.claim_territory(faction.id, faction.home_base, 1.0, 0)

    def _save_faction(self, faction: Faction):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO factions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                faction.id, faction.name, faction.type.value, str(faction.color),
                f"{faction.home_base[0]},{faction.home_base[1]}",
                faction.current_power, json.dumps(faction.territories),
                json.dumps({k: v.value for k, v in faction.relations.items()}),
                faction.expansion_rate, faction.aggression_level, faction.last_action_turn
            ))

    def claim_territory(self, faction_id: str, coord: Tuple[int, int], strength: float, turn: int):
        coord_key = f"{coord[0]},{coord[1]}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO territories VALUES (?, ?, ?, ?)",
                        (coord_key, faction_id, strength, turn))
        
        if faction_id in self.factions:
            if coord not in self.factions[faction_id].territories:
                self.factions[faction_id].territories.append(coord)

    def get_owner(self, coord: Tuple[int, int]) -> Optional[str]:
        coord_key = f"{coord[0]},{coord[1]}"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT faction_id FROM territories WHERE coordinate = ?", (coord_key,))
            row = cursor.fetchone()
            return row[0] if row else None

    def simulate_step(self, current_turn: int, world_bounds: Optional[Tuple[int, int, int, int]] = None):
        """Perform one simulation tick."""
        for fid, faction in self.factions.items():
            if random.random() < self.expansion_chance * faction.expansion_rate:
                self._expand_faction(faction, current_turn, world_bounds)

    def _expand_faction(self, faction: Faction, turn: int, bounds: Optional[Tuple[int, int, int, int]]):
        if not faction.territories:
            return
            
        # Try to expand from a random existing territory
        origin = random.choice(faction.territories)
        adj = [(0,1), (0,-1), (1,0), (-1,0)]
        random.shuffle(adj)
        
        for dx, dy in adj:
            tx, ty = origin[0] + dx, origin[1] + dy
            
            # Check bounds if provided
            if bounds:
                min_x, min_y, max_x, max_y = bounds
                if not (min_x <= tx <= max_x and min_y <= ty <= max_y):
                    continue
            
            target = (tx, ty)
            owner = self.get_owner(target)
            
            if owner is None:
                # Claim neutral
                self.claim_territory(faction.id, target, 0.5, turn)
                logger.debug(f"Faction {faction.name} claimed neutral territory {target}")
                break
            elif owner != faction.id:
                # Potential conflict - Simplified Slime Clan logic: 
                # Factions don't auto-conquer each other unless powerful
                rel = faction.relations.get(owner, FactionRelation.NEUTRAL)
                if rel in [FactionRelation.HOSTILE, FactionRelation.WAR]:
                    if random.random() < faction.aggression_level * faction.current_power:
                        self.claim_territory(faction.id, target, 0.4, turn)
                        logger.info(f"Faction {faction.name} conquered {owner} territory {target}")
                        break
