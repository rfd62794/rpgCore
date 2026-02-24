from typing import List, Optional, Tuple, Dict
from src.apps.slime_breeder.entities.slime import Slime
from src.shared.genetics import SlimeGenome

class GardenState:
    def __init__(self):
        self.slimes: List[Slime] = []
        self.selected: Optional[Slime] = None

    def add_slime(self, slime: Slime) -> None:
        self.slimes.append(slime)

    def remove_slime(self, name: str) -> None:
        self.slimes = [s for s in self.slimes if s.name != name]
        if self.selected and self.selected.name == name:
            self.selected = None

    def get_slime(self, name: str) -> Optional[Slime]:
        for s in self.slimes:
            if s.name == name:
                return s
        return None

    def update(self, dt: float, cursor_pos: Optional[Tuple[float, float]] = None) -> None:
        for slime in self.slimes:
            slime.update(dt, cursor_pos)

    def save(self) -> dict:
        """Serialize for persistence."""
        data = {
            "slimes": []
        }
        for slime in self.slimes:
            g = slime.genome
            data["slimes"].append({
                "name": slime.name,
                "position": (slime.kinematics.position.x, slime.kinematics.position.y),
                "genome": {
                    "shape": g.shape,
                    "size": g.size,
                    "base_color": g.base_color,
                    "pattern": g.pattern,
                    "pattern_color": g.pattern_color,
                    "accessory": g.accessory,
                    "curiosity": g.curiosity,
                    "energy": g.energy,
                    "affection": g.affection,
                    "shyness": g.shyness
                }
            })
        return data

    def load(self, data: dict) -> None:
        """Restore from save."""
        self.slimes = []
        for s_data in data.get("slimes", []):
            g_data = s_data["genome"]
            genome = SlimeGenome(**g_data)
            slime = Slime(s_data["name"], genome, s_data["position"])
            self.add_slime(slime)
