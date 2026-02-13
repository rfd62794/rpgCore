"""
Asteroid Pilot — Steering Behavior AI

Craig Reynolds' steering behaviors applied to Newtonian physics.
Operates directly on KineticEntity.acceleration — pure vector math,
zero coupling to the RPG AIController or tile-grid pathfinding.

Behaviors:
  - Seek:   Steer toward a waypoint
  - Avoid:  Repulsion from nearby asteroids
  - Wander: Pick new waypoints when current one is reached

Usage:
    pilot = AsteroidPilot()
    steering = pilot.compute_steering(ship_kinetics, asteroids, waypoint)
    ship_kinetics.acceleration = steering
"""

import math
import random
import time
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field

from foundation.vector import Vector2
from engines.body.kinetics import KineticEntity


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class SteeringConfig:
    """Tuning knobs for the pilot's steering behaviors."""

    # Detection & avoidance
    avoid_radius: float = 25.0        # How far out do we see threats?
    avoid_weight: float = 2.5         # How hard do we dodge?
    avoid_urgency_power: float = 2.0  # How much stronger at close range (1/d^n)

    # Seeking
    seek_weight: float = 0.8          # How hard do we chase the waypoint?
    arrival_radius: float = 8.0       # "Close enough" to waypoint

    # Steering limits
    max_steer_force: float = 80.0     # Cap on total steering magnitude

    # Waypoint generation
    waypoint_margin: float = 20.0     # Keep waypoints this far from edges
    waypoint_safety_radius: float = 30.0  # Avoid placing waypoints near rocks


# ---------------------------------------------------------------------------
# Survival Log — telemetry
# ---------------------------------------------------------------------------

@dataclass
class SurvivalLog:
    """Tracks AI performance during a survival run."""

    frames_survived: int = 0
    avoidance_maneuvers: int = 0
    closest_call_distance: float = float("inf")
    waypoints_reached: int = 0
    total_collisions: int = 0
    total_steering_magnitude: float = 0.0

    _maneuver_cooldown: int = field(default=0, repr=False)

    def record_maneuver(self) -> None:
        """Record an avoidance maneuver (with cooldown to avoid spam)."""
        if self._maneuver_cooldown <= 0:
            self.avoidance_maneuvers += 1
            self._maneuver_cooldown = 15  # Don't count again for 15 frames
        else:
            self._maneuver_cooldown -= 1

    def tick(self) -> None:
        """Advance one frame."""
        self.frames_survived += 1
        if self._maneuver_cooldown > 0:
            self._maneuver_cooldown -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frames_survived": self.frames_survived,
            "time_survived_s": self.frames_survived / 60.0,
            "avoidance_maneuvers": self.avoidance_maneuvers,
            "closest_call_px": round(self.closest_call_distance, 2),
            "waypoints_reached": self.waypoints_reached,
            "total_collisions": self.total_collisions,
            "avg_steering": round(
                self.total_steering_magnitude / max(self.frames_survived, 1), 3
            ),
        }


# ---------------------------------------------------------------------------
# AsteroidPilot — the Mind
# ---------------------------------------------------------------------------

class AsteroidPilot:
    """Steering-behavior AI that flies a KineticEntity-backed ship
    through an asteroid field using seek + obstacle avoidance.

    Stateless per tick — call compute_steering() each frame.
    """

    def __init__(self, config: Optional[SteeringConfig] = None) -> None:
        self.config = config or SteeringConfig()
        self.log = SurvivalLog()
        self._current_waypoint: Optional[Vector2] = None

    def _get_toroidal_vector(self, source: Vector2, target: Vector2, bounds: Tuple[int, int]) -> Vector2:
        """
        Calculate the shortest vector from source to target in toroidal space.
        ADR 195: Modular Arithmetic for Navigation.
        """
        width, height = bounds
        dx = target.x - source.x
        dy = target.y - source.y
        
        # Wrap X shortest path
        if dx > width / 2:
            dx -= width
        elif dx < -width / 2:
            dx += width
            
        # Wrap Y shortest path
        if dy > height / 2:
            dy -= height
        elif dy < -height / 2:
            dy += height
            
        return Vector2(dx, dy)

    def _select_new_waypoint(
        self,
        ship_position: Vector2,
        asteroids: List,
        bounds: Tuple[int, int],
    ) -> None:
        """Pick a waypoint that is far from nearby asteroids, using toroidal distance."""
        margin = self.config.waypoint_margin
        safety = self.config.waypoint_safety_radius
        w, h = bounds

        best_wp = None
        best_clearance = -1.0

        # Try 10 random candidates, pick the safest
        for _ in range(10):
            candidate = Vector2(
                random.uniform(margin, w - margin),
                random.uniform(margin, h - margin),
            )
            # Minimum toroidal distance to any asteroid
            min_dist = float("inf")
            for asteroid in asteroids:
                vec_to_ast = self._get_toroidal_vector(candidate, asteroid.kinetics.position, bounds)
                d = vec_to_ast.magnitude()
                if d < min_dist:
                    min_dist = d

            if min_dist > best_clearance:
                best_clearance = min_dist
                best_wp = candidate
        
        self._current_waypoint = best_wp or Vector2(w / 2, h / 2)


    def _avoid(self, ship: KineticEntity, asteroids: List, bounds: Tuple[int, int]) -> Tuple[Vector2, float, bool]:
        """Calculates repulsion vector from nearby threats (Toroidal aware)."""
        avoid_vector = Vector2.zero()
        nearest_dist = float('inf')
        is_dodging = False
        
        # Standard constants for tuning (could move to config)
        lookahead = self.config.avoid_radius # Pixels
        
        for asteroid in asteroids:
            if not asteroid.active:
                continue
                
            # Use toroidal vector for distance
            vec_to_asteroid = self._get_toroidal_vector(ship.position, asteroid.kinetics.position, bounds)
            dist = vec_to_asteroid.magnitude()
            
            # Account for asteroid radius
            surface_dist = dist - asteroid.radius
            if surface_dist < 0.1:
                surface_dist = 0.1 # Prevent division by zero or negative
            
            nearest_dist = min(nearest_dist, surface_dist)
            
            # If threat is within lookahead
            if surface_dist < lookahead:
                # Calculate threat level (inverse square law for stronger close-range repulsion)
                # Using the original urgency power for consistency
                strength = 1.0 / (surface_dist ** self.config.avoid_urgency_power)
                
                # Direction AWAY from asteroid (normalized)
                # vec_to_asteroid points AT the asteroid, so negate it
                flee_dir = vec_to_asteroid.normalize() * -1
                
                # Weight by strength
                avoid_vector += flee_dir * strength
                is_dodging = True
                
        # Normalize result if any avoidance happened and apply overall avoid_weight
        if is_dodging:
            avoid_vector = avoid_vector.normalize() * self.config.avoid_weight
            
        return avoid_vector, nearest_dist, is_dodging

    # -- Core steering -------------------------------------------------------

    def compute_steering(
        self,
        ship: KineticEntity,
        asteroids: List,  # List[Asteroid] — kept loose to avoid circular import
        bounds: Tuple[int, int] = (160, 144),
    ) -> Vector2:
        """
        Main decision loop: blend Seeking + Avoiding.
        Returns: Steering force vector (truncated to max_force).
        """
        # 0. Update internal state if needed (e.g., select new waypoint)
        if self._current_waypoint is None:
            self._select_new_waypoint(ship.position, asteroids, bounds)
            
        # Check waypoint arrival (using toroidal distance too for consistency)
        vec_to_wp = self._get_toroidal_vector(ship.position, self._current_waypoint, bounds)
        dist_to_wp = vec_to_wp.magnitude()
            
        if dist_to_wp < self.config.waypoint_tolerance:
            self.log.waypoints_reached += 1
            self._select_new_waypoint(ship.position, asteroids, bounds)
            
        # 1. Seek — steer toward waypoint
        # Re-calculate with possibly new waypoint
        seek_vector = self._get_toroidal_vector(ship.position, self._current_waypoint, bounds)
        desired_velocity = seek_vector.normalize() * ship.max_velocity
        seek_force = (desired_velocity - ship.velocity) * self.config.seek_weight

        # 2. Avoid — repulsion from nearby asteroids
        avoid_force, nearest_dist, is_dodging = self._avoid(ship, asteroids, bounds)

        # Track closest call
        if nearest_dist < self.log.closest_call_distance:
            self.log.closest_call_distance = nearest_dist

        # Track avoidance maneuvers
        if is_dodging:
            self.log.record_maneuver()

        # 3. Combine — avoidance dominates when threats are near
        combined = seek_force * self.config.seek_weight + avoid_force * self.config.avoid_weight
        combined = combined.clamp_magnitude(self.config.max_steer_force)

        # Track telemetry
        self.log.total_steering_magnitude += combined.magnitude()
        self.log.tick()

        return combined

    @property
    def waypoint(self) -> Optional[Vector2]:
        """Current waypoint for visualization."""
        return self._current_waypoint

    # -- Seek behavior -------------------------------------------------------

    def _seek(self, ship: KineticEntity, target: Vector2) -> Vector2:
        """Steer toward target position."""
        desired = target - ship.position
        if desired.magnitude_squared() < 0.01:
            return Vector2.zero()
        return desired.normalize() * ship.max_velocity

    # -- Avoid behavior ------------------------------------------------------

    def _avoid(
        self,
        ship: KineticEntity,
        asteroids: List,
    ) -> Tuple[Vector2, float, bool]:
        """Compute repulsion from nearby asteroids.

        Returns: (avoidance_force, nearest_distance, is_actively_dodging)
        """
        avoid = Vector2.zero()
        nearest_dist = float("inf")
        is_dodging = False
        detection = self.config.avoid_radius

        for asteroid in asteroids:
            if not asteroid.active:
                continue
            ast_pos = asteroid.kinetics.position
            offset = ship.position - ast_pos
            dist = offset.magnitude()

            # Account for asteroid radius
            surface_dist = dist - asteroid.radius
            if surface_dist < 0.1:
                surface_dist = 0.1  # Prevent division by zero

            if surface_dist < nearest_dist:
                nearest_dist = surface_dist

            if surface_dist < detection:
                # Repulsion: stronger the closer we are (inverse power)
                strength = 1.0 / (surface_dist ** self.config.avoid_urgency_power)
                repulsion = offset.normalize() * strength * 100
                avoid = avoid + repulsion
                is_dodging = True

        return avoid, nearest_dist, is_dodging

    # -- Waypoint generation -------------------------------------------------

    def _pick_safe_waypoint(
        self,
        current_pos: Vector2,
        asteroids: List,
        bounds: Tuple[int, int],
    ) -> Vector2:
        """Pick a waypoint that is far from nearby asteroids."""
        margin = self.config.waypoint_margin
        safety = self.config.waypoint_safety_radius
        w, h = bounds

        best_wp = None
        best_clearance = -1.0

        # Try 10 random candidates, pick the safest
        for _ in range(10):
            candidate = Vector2(
                random.uniform(margin, w - margin),
                random.uniform(margin, h - margin),
            )
            # Minimum distance to any asteroid
            min_dist = float("inf")
            for asteroid in asteroids:
                d = candidate.distance_to(asteroid.kinetics.position)
                if d < min_dist:
                    min_dist = d

            if min_dist > best_clearance:
                best_clearance = min_dist
                best_wp = candidate

        return best_wp or Vector2(w / 2, h / 2)

    # -- Heading control helper ----------------------------------------------

    @staticmethod
    def apply_to_ship(
        steering: Vector2,
        ship: KineticEntity,
        dt: float,
        turn_rate: float = 6.0,
    ) -> None:
        """Apply steering vector to ship: rotate heading toward steering
        direction, then thrust forward.

        This separates intent (steering) from execution (rotation + thrust),
        simulating how a real ship with a fixed thruster works.
        """
        if steering.magnitude_squared() < 0.01:
            ship.acceleration = Vector2.zero()
            return

        # Desired heading
        desired_heading = math.atan2(steering.y, steering.x)

        # Shortest angular distance
        diff = desired_heading - ship.heading
        # Normalize to [-pi, pi]
        diff = (diff + math.pi) % (2 * math.pi) - math.pi

        # Turn toward desired heading
        max_turn = turn_rate * dt
        if abs(diff) < max_turn:
            ship.heading = desired_heading
        elif diff > 0:
            ship.heading += max_turn
        else:
            ship.heading -= max_turn
        ship.heading %= (2 * math.pi)

        # Thrust in current heading direction
        thrust_magnitude = min(steering.magnitude(), ship.max_velocity * 0.6)
        ship.set_thrust(thrust_magnitude)
