from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from src.shared.genetics.genome import SlimeGenome

class TeamRole(Enum):
    DUNGEON  = "dungeon"
    RACING   = "racing"
    CONQUEST = "conquest"
    UNASSIGNED = "unassigned"

@dataclass
class RosterSlime:
    slime_id: str
    name: str
    genome: SlimeGenome
    team: TeamRole = TeamRole.UNASSIGNED
    locked: bool = False      # True when on active mission
    alive: bool = True
    generation: int = 1
    
    # Progression
    level: int = 1
    experience: int = 0
    breeding_lock_level: int = 0 # Cannot breed if level <= breeding_lock_level
    
    @property
    def is_elder(self) -> bool:
        return self.level >= 10
    
    @property
    def can_breed(self) -> bool:
        """Min level 3 required, and must be above last bred level (drain mechanic)."""
        return self.level >= 3 and self.level > self.breeding_lock_level

    @property
    def xp_to_next_level(self) -> int:
        return 5 + (self.level * 2)

    def gain_exp(self, amount: int) -> bool:
        """Adds exp and returns True if leveled up."""
        self.experience += amount
        leveled_up = False
        while self.experience >= self.xp_to_next_level:
            self.experience -= self.xp_to_next_level
            self.level += 1
            leveled_up = True
        return leveled_up

@dataclass  
class Team:
    role: TeamRole
    slots: int = 4
    members: list[RosterSlime] = field(default_factory=list)
    
    def is_full(self) -> bool:
        return len(self.members) >= self.slots
    
    def assign(self, slime: RosterSlime) -> bool:
        if self.is_full():
            return False
        if slime.team != TeamRole.UNASSIGNED:
            return False
        slime.team = self.role
        self.members.append(slime)
        return True
    
    def remove(self, slime_id: str) -> bool:
        member = next(
            (s for s in self.members if s.slime_id == slime_id), 
            None
        )
        if not member or member.locked:
            return False
        member.team = TeamRole.UNASSIGNED
        self.members = [
            s for s in self.members 
            if s.slime_id != slime_id
        ]
        return True

@dataclass
class Roster:
    slimes: list[RosterSlime] = field(default_factory=list)
    teams: dict[TeamRole, Team] = field(default_factory=lambda: {
        TeamRole.DUNGEON: Team(role=TeamRole.DUNGEON, slots=4),
        TeamRole.RACING:  Team(role=TeamRole.RACING,  slots=1),
    })
    
    def add_slime(self, slime: RosterSlime):
        self.slimes.append(slime)
    
    def get_dungeon_team(self) -> Team:
        return self.teams[TeamRole.DUNGEON]
    
    def unassigned(self) -> list[RosterSlime]:
        return [s for s in self.slimes 
                if s.team == TeamRole.UNASSIGNED
                and s.alive]
    
    def to_dict(self) -> dict:
        return {
            "slimes": [
                {
                    "slime_id": s.slime_id,
                    "name": s.name,
                    "team": s.team.value,
                    "locked": s.locked,
                    "alive": s.alive,
                    "genome": {
                        "shape": s.genome.shape,
                        "size": s.genome.size,
                        "base_color": s.genome.base_color,
                        "pattern": s.genome.pattern,
                        "pattern_color": s.genome.pattern_color,
                        "accessory": s.genome.accessory,
                        "affection": s.genome.affection,
                        "shyness": s.genome.shyness,
                        "cultural_base": s.genome.cultural_base.value,
                        "base_hp": s.genome.base_hp,
                        "base_atk": s.genome.base_atk,
                        "base_spd": s.genome.base_spd,
                        "generation": s.genome.generation
                    },
                    "level": s.level,
                    "experience": s.experience,
                    "breeding_lock_level": s.breeding_lock_level
                }
                for s in self.slimes
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Roster":
        roster = cls()
        for s in data.get("slimes", []):
            g_data = s["genome"]
            # Cast culture string back to Enum
            from src.shared.genetics.cultural_base import CulturalBase
            g_data["cultural_base"] = CulturalBase(g_data.get("cultural_base", "mixed"))
            
            # Ensure base stats exist (for backward compatibility if needed)
            if "base_hp" not in g_data: g_data["base_hp"] = 20.0
            if "base_atk" not in g_data: g_data["base_atk"] = 5.0
            if "base_spd" not in g_data: g_data["base_spd"] = 5.0
            
            genome = SlimeGenome(**g_data)
            rs = RosterSlime(
                slime_id=s["slime_id"],
                name=s["name"],
                genome=genome,
                team=TeamRole(s["team"]),
                locked=s["locked"],
                alive=s["alive"],
                level=s.get("level", 1),
                experience=s.get("experience", 0),
                breeding_lock_level=s.get("breeding_lock_level", 0),
                generation=s.get("generation", 1)
            )
            roster.slimes.append(rs)
            if rs.team != TeamRole.UNASSIGNED:
                roster.teams[rs.team].members.append(rs)
        return roster
