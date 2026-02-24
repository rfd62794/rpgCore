import math
import random
from typing import Tuple, Optional
from src.shared.genetics import SlimeGenome
from src.shared.physics import Kinematics, Vector2

class Slime:
    def __init__(self, name: str, genome: SlimeGenome, position: Tuple[float, float]):
        self.name = name
        self.genome = genome
        self.age = 0  # ticks lived
        
        # Physics
        self.kinematics = Kinematics(
            position=Vector2(*position),
            velocity=Vector2(0, 0)
        )
        self.max_speed = 50.0 + (self.genome.energy * 150.0) # Energy affects speed
        
        self.mood = "happy"
        self._target_pos: Optional[Vector2] = None
        self._wander_timer = 0.0

    def update(self, dt: float, cursor_pos: Optional[Tuple[float, float]] = None) -> None:
        self.age += 1
        self._wander_timer -= dt
        
        target_force = Vector2(0, 0)
        
        # 1. Shyness: Retreat from fast cursor movement (or just being near if VERY shy)
        if cursor_pos:
            cursor_vec = Vector2(*cursor_pos)
            dist_to_cursor = (self.kinematics.position - cursor_vec).magnitude()
            
            if dist_to_cursor < 150.0:
                # Shy slimes retreat
                if self.genome.shyness > 0.3:
                    retreat_dir = (self.kinematics.position - cursor_vec).normalize()
                    # Scale force by shyness
                    target_force += retreat_dir * (self.genome.shyness * 300.0)
                
                # Affectionate slimes follow (if not too shy)
                if self.genome.affection > 0.5 and self.genome.shyness < 0.7:
                    follow_dir = (cursor_vec - self.kinematics.position).normalize()
                    target_force += follow_dir * (self.genome.affection * 150.0)

        # 2. Curiosity: Wander toward edges/random points
        if self._wander_timer <= 0:
            # Pick a new random target or just a random direction
            if self.genome.curiosity > 0.5:
                # Random point in a "large" garden (assume 800x600 for now, logic should be bounds-aware)
                self._target_pos = Vector2(random.uniform(50, 750), random.uniform(50, 550))
            else:
                self._target_pos = None # Just drift
            self._wander_timer = random.uniform(2.0, 5.0)

        if self._target_pos:
            dir_to_target = (self._target_pos - self.kinematics.position).normalize()
            target_force += dir_to_target * (self.genome.energy * 50.0 + 20.0)

        # Apply friction/damping
        self.kinematics.velocity *= 0.95
        
        # Apply force to velocity (simplistic integration)
        self.kinematics.velocity += target_force * dt
        
        # Clamp speed
        speed = self.kinematics.velocity.magnitude()
        if speed > self.max_speed:
            self.kinematics.velocity = self.kinematics.velocity.normalize() * self.max_speed
        
        # Update position
        self.kinematics.update(dt)
        
        # Keep in bounds (soft bounce)
        margin = 20
        # Assume 800x600 for now, until garden state provides bounds
        if self.kinematics.position.x < margin:
            self.kinematics.position.x = margin
            self.kinematics.velocity.x *= -0.5
        elif self.kinematics.position.x > 800 - margin:
            self.kinematics.position.x = 800 - margin
            self.kinematics.velocity.x *= -0.5
            
        if self.kinematics.position.y < margin:
            self.kinematics.position.y = margin
            self.kinematics.velocity.y *= -0.5
        elif self.kinematics.position.y > 600 - margin:
            self.kinematics.position.y = 600 - margin
            self.kinematics.velocity.y *= -0.5

        self._update_mood()

    def _update_mood(self) -> None:
        speed = self.kinematics.velocity.magnitude()
        if speed > 100:
            self.mood = "excited"
        elif speed > 20:
            self.mood = "playful"
        elif self.genome.shyness > 0.8:
            self.mood = "timid"
        else:
            self.mood = "happy"

    def get_mood(self) -> str:
        return self.mood
