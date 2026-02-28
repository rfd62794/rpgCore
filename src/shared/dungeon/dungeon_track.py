import random
from enum import Enum
from dataclasses import dataclass

class DungeonZoneType(Enum):
    SAFE     = "safe"
    COMBAT   = "combat"
    TRAP     = "trap"
    REST     = "rest"
    TREASURE = "treasure"
    BOSS     = "boss"

ZONE_COLORS = {
    DungeonZoneType.SAFE:     (55,  110, 55),
    DungeonZoneType.COMBAT:   (180, 50,  50),
    DungeonZoneType.TRAP:     (200, 120, 40),
    DungeonZoneType.REST:     (40,  100, 180),
    DungeonZoneType.TREASURE: (200, 170, 40),
    DungeonZoneType.BOSS:     (120, 40,  180),
}

ZONE_LABELS = {
    DungeonZoneType.SAFE:     "SAFE",
    DungeonZoneType.COMBAT:   "⚔ ENEMY",
    DungeonZoneType.TRAP:     "⚠ TRAP",
    DungeonZoneType.REST:     "☾ REST",
    DungeonZoneType.TREASURE: "★ TREASURE",
    DungeonZoneType.BOSS:     "☠ BOSS",
}

@dataclass
class DungeonZone:
    zone_type:  DungeonZoneType
    start_dist: float
    end_dist:   float
    resolved:   bool = False  # has this zone been cleared?

@dataclass
class DungeonTrack:
    zones:        list[DungeonZone]
    total_length: float
    
def generate_dungeon_track(depth: int = 1) -> DungeonTrack:
    # depth affects difficulty and zone density
    zones = []
    current = 0.0
    
    # Always start with SAFE zone
    zones.append(DungeonZone(DungeonZoneType.SAFE,
                             0, 300))
    current = 300.0
    
    # Middle zones — alternating safe + encounter
    for i in range(4 + depth):
        # Safe buffer between encounters
        safe_w = random.uniform(150, 250)
        zones.append(DungeonZone(DungeonZoneType.SAFE,
                                current,
                                current + safe_w))
        current += safe_w
        
        # Encounter zone
        zone_type = random.choices(
            [DungeonZoneType.COMBAT,
             DungeonZoneType.TRAP,
             DungeonZoneType.REST,
             DungeonZoneType.TREASURE],
            weights=[50, 20, 20, 10]
        )[0]
        enc_w = random.uniform(100, 200)
        zones.append(DungeonZone(zone_type,
                                current,
                                current + enc_w))
        current += enc_w
    
    # Always end with BOSS
    safe_w = random.uniform(150, 200)
    zones.append(DungeonZone(DungeonZoneType.SAFE,
                             current, current + safe_w))
    current += safe_w
    zones.append(DungeonZone(DungeonZoneType.BOSS,
                             current, current + 200))
    current += 200
    
    return DungeonTrack(zones=zones, total_length=current)
