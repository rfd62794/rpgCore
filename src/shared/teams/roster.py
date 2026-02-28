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
                        "curiosity": s.genome.curiosity,
                        "energy": s.genome.energy,
                        "affection": s.genome.affection,
                        "shyness": s.genome.shyness
                    }
                }
                for s in self.slimes
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Roster":
        roster = cls()
        for s in data.get("slimes", []):
            genome = SlimeGenome(**s["genome"])
            rs = RosterSlime(
                slime_id=s["slime_id"],
                name=s["name"],
                genome=genome,
                team=TeamRole(s["team"]),
                locked=s["locked"],
                alive=s["alive"]
            )
            roster.slimes.append(rs)
            if rs.team != TeamRole.UNASSIGNED:
                roster.teams[rs.team].members.append(rs)
        return roster
