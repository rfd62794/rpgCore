import math
import random
from typing import Tuple, Optional
from src.shared.genetics import SlimeGenome
from src.shared.physics import Kinematics, Vector2

class Slime:
    def __init__(self, name: str, genome: SlimeGenome, position: Tuple[float, float], level: int = 1):
        self.name = name
        self.genome = genome
        self.level = level
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
        
        # 1. Shyness: Retreat from cursor
        if cursor_pos:
            cursor_vec = Vector2(*cursor_pos)
            diff = self.kinematics.position - cursor_vec
            dist_to_cursor = diff.magnitude()
            
            if dist_to_cursor < 200.0:
                # Shy slimes retreat (Priority 1)
                if self.genome.shyness > 0.7:
                    retreat_dir = diff.normalize()
                    # Retreat faster if shy
                    target_force += retreat_dir * (self.genome.shyness * 400.0)
                
                # Affectionate slimes follow (if not too shy)
                elif self.genome.affection > 0.7:
                    if dist_to_cursor > 40.0: # Stop when close
                        follow_dir = (cursor_vec - self.kinematics.position).normalize()
                        target_force += follow_dir * (self.genome.affection * 200.0)

        # 2. Curiosity: Wander toward edges/random points
        if self._wander_timer <= 0:
            # High energy slimes change direction more often
            self._wander_timer = random.uniform(1.0, 3.0) / (0.5 + self.genome.energy)
            
            if self.genome.curiosity > 0.7:
                # Target points near edges or random
                if random.random() < 0.5:
                    self._target_pos = Vector2(random.choice([30, 770]), random.uniform(30, 570))
                else:
                    self._target_pos = Vector2(random.uniform(50, 750), random.uniform(50, 550))
            elif self.genome.energy > 0.3:
                # Random drift point
                self._target_pos = self.kinematics.position + Vector2(random.uniform(-100, 100), random.uniform(-100, 100))
            else:
                self._target_pos = None # Slow/Sleepy

        if self._target_pos:
            diff = self._target_pos - self.kinematics.position
            if diff.magnitude() > 10.0:
                dir_to_target = diff.normalize()
                # Energy affects force
                force_mag = 20.0 + (self.genome.energy * 80.0)
                target_force += dir_to_target * force_mag
            else:
                self._target_pos = None

        # Apply friction (Energy affects how "slippery" they are)
        friction = 0.92 + (self.genome.energy * 0.05)
        self.kinematics.velocity *= min(0.98, friction)
        
        # Apply force to velocity (simplistic integration)
        self.kinematics.velocity += target_force * dt
        
        # Clamp speed
        speed = self.kinematics.velocity.magnitude()
        if speed > self.max_speed:
            self.kinematics.velocity = self.kinematics.velocity.normalize() * self.max_speed
        
        # Update position
        self.kinematics.update(dt)
        
        # Keep in bounds
        # Assume 1024x768 context but garden area is roughly 784x688
        # We'll use 800x600 as a safe logic zone for now
        self._handle_bounds(800, 600)
        self._update_mood()

    def _handle_bounds(self, width: int, height: int):
        margin = 30
        if self.kinematics.position.x < margin:
            self.kinematics.position.x = margin
            self.kinematics.velocity.x *= -0.5
            self._target_pos = None
        elif self.kinematics.position.x > width - margin:
            self.kinematics.position.x = width - margin
            self.kinematics.velocity.x *= -0.5
            self._target_pos = None
            
        if self.kinematics.position.y < margin:
            self.kinematics.position.y = margin
            self.kinematics.velocity.y *= -0.5
            self._target_pos = None
        elif self.kinematics.position.y > height - margin:
            self.kinematics.position.y = height - margin
            self.kinematics.velocity.y *= -0.5
            self._target_pos = None

        self._update_mood()

    def _update_mood(self) -> None:
        if self.genome.energy < 0.3:
            self.mood = "Sleepy"
        elif self.genome.shyness > 0.7:
            self.mood = "Shy"
        elif self.genome.affection > 0.7:
            self.mood = "Playful"
        elif self.genome.curiosity > 0.7:
            self.mood = "Curious"
        else:
            self.mood = "Happy"

    def get_mood(self) -> str:
        return self.mood
