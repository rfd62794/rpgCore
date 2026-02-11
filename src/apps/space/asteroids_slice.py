"""
Asteroids Stress Test — Headless Simulation Slice

ADR 195: Kinetic Alignment Verification

Proves the full pipeline end-to-end:
  KineticEntity physics → ExhaustSystem VFX → frame-buffer rendering
  → circle-circle collision → PerformanceMonitor instrumentation

Usage:
  python -m apps.space.asteroids_slice            # from src/
  python src/apps/space/asteroids_slice.py         # from repo root
"""

import sys
import math
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

# Ensure src/ is importable when run as a script
_src = Path(__file__).resolve().parent.parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from foundation.vector import Vector2
from engines.body.kinetics import KineticEntity
from engines.graphics.fx.exhaust_system import ExhaustSystem

from foundation.utils.performance_monitor import (
    PerformanceMonitor,
    initialize_performance_monitor,
    get_performance_monitor,
)

from loguru import logger

# Sovereign resolution
WIDTH = 160
HEIGHT = 144


# ---------------------------------------------------------------------------
# Asteroid descriptor (thin wrapper over KineticEntity)
# ---------------------------------------------------------------------------

@dataclass
class Asteroid:
    """A space rock — pure KineticEntity + radius for collision."""
    kinetics: KineticEntity
    radius: float = 4.0
    active: bool = True


# ---------------------------------------------------------------------------
# AsteroidsSlice — orchestrator
# ---------------------------------------------------------------------------

class AsteroidsSlice:
    """Headless asteroids simulation proving the Kinetic Alignment pipeline.

    Creates 1 SpaceShip (KineticEntity-backed) + N asteroid KineticEntities,
    wires the ExhaustSystem to the ship's thrust, renders to a 160×144
    frame buffer, and measures per-pillar frame times.
    """

    def __init__(self, asteroid_count: int = 50) -> None:
        self.asteroid_count = asteroid_count

        # Import SpaceShip lazily to avoid heavy import chains at module level
        from apps.space.space_voyager_engine import SpaceShip
        from apps.space.ship_genetics import ShipGenome

        # --- Entities ---
        ship_kinetics = KineticEntity(
            position=Vector2(WIDTH / 2, HEIGHT / 2),
            velocity=Vector2.zero(),
            wrap_bounds=(WIDTH, HEIGHT),
        )
        self.ship: SpaceShip = SpaceShip(
            ship_id="player_001",
            genome=ShipGenome(),
            kinetics=ship_kinetics,
        )
        self.asteroids: List[Asteroid] = []

        # --- VFX ---
        self.exhaust = ExhaustSystem()

        # --- Rendering ---
        self.frame_buffer = bytearray(WIDTH * HEIGHT)

        # --- Metrics ---
        self.perf: Optional[PerformanceMonitor] = None

        # --- Simulation state ---
        self.frame_count = 0
        self.collisions = 0
        self.waypoint = Vector2(
            random.uniform(20, WIDTH - 20),
            random.uniform(20, HEIGHT - 20),
        )

    # -- Setup ---------------------------------------------------------------

    def spawn_asteroid_field(self) -> None:
        """Spawn *asteroid_count* rocks with random positions & velocities."""
        for _ in range(self.asteroid_count):
            radius = random.uniform(2.0, 6.0)
            kinetics = KineticEntity(
                position=Vector2(
                    random.uniform(0, WIDTH),
                    random.uniform(0, HEIGHT),
                ),
                velocity=Vector2(
                    random.uniform(-15, 15),
                    random.uniform(-15, 15),
                ),
                wrap_bounds=(WIDTH, HEIGHT),
                mass=radius * 2,
                drag=0.0,
            )
            self.asteroids.append(Asteroid(kinetics=kinetics, radius=radius))

    def wire_exhaust(self) -> None:
        """Register the ship's engine type with the ExhaustSystem."""
        engine_enum = getattr(self.ship.genome, "engine_type", "ion")
        engine_type = engine_enum.value if hasattr(engine_enum, "value") else str(engine_enum)
        self.exhaust.add_ship_emitter(
            self.ship.ship_id, engine_type, offset_x=0.0, offset_y=0.0
        )
        logger.info(
            f"🔥 Exhaust wired for {self.ship.ship_id} (engine={engine_type})"
        )

    # -- Simulation loop -----------------------------------------------------

    def update(self, dt: float) -> Dict[str, Any]:
        """Run one simulation tick (physics → VFX → render)."""

        # ---- Physics pillar ------------------------------------------------
        self.perf.start_pillar("physics")

        # Ship: thrust toward waypoint
        direction = self.waypoint - self.ship.position
        dist_to_wp = direction.magnitude()
        is_thrusting = dist_to_wp > 5.0

        if is_thrusting:
            desired_heading = math.atan2(direction.y, direction.x)
            self.ship.heading = desired_heading
            self.ship.kinetics.set_thrust(self.ship.kinetics.max_velocity * 0.6)
        else:
            self.ship.kinetics.acceleration = Vector2.zero()
            # Pick a new waypoint
            self.waypoint = Vector2(
                random.uniform(20, WIDTH - 20),
                random.uniform(20, HEIGHT - 20),
            )

        self.ship.kinetics.update(dt)

        # Asteroids
        for asteroid in self.asteroids:
            if asteroid.active:
                asteroid.kinetics.update(dt)

        self.perf.end_pillar("physics")

        # ---- VFX pillar ----------------------------------------------------
        self.perf.start_pillar("vfx")

        # Feed ship state to exhaust system
        heading_deg = math.degrees(self.ship.heading)
        self.exhaust.update_ship_thrust(
            self.ship.ship_id,
            self.ship.position.x,
            self.ship.position.y,
            heading_deg,
            is_thrusting,
            intensity=0.8,
        )
        self.exhaust.update(dt)

        self.perf.end_pillar("vfx")

        # ---- Collision pillar ----------------------------------------------
        self.perf.start_pillar("collision")
        frame_collisions = self._check_collisions()
        self.perf.end_pillar("collision")

        # ---- Render pillar -------------------------------------------------
        self.perf.start_pillar("render")
        self._render_frame()
        self.perf.end_pillar("render")

        self.frame_count += 1

        return {
            "frame": self.frame_count,
            "collisions": frame_collisions,
            "particles": self.exhaust.total_particles,
            "ship_pos": self.ship.position.to_tuple(),
        }

    # -- Collision -----------------------------------------------------------

    def _check_collisions(self) -> int:
        """Circle-circle collision: ship (radius 3) vs asteroids."""
        ship_radius = 3.0
        hits = 0
        for asteroid in self.asteroids:
            if not asteroid.active:
                continue
            dist_sq = self.ship.position.distance_squared_to(
                asteroid.kinetics.position
            )
            threshold = (ship_radius + asteroid.radius) ** 2
            if dist_sq < threshold:
                hits += 1
                self.collisions += 1
        return hits

    # -- Rendering -----------------------------------------------------------

    def _render_frame(self) -> None:
        """Software rasterize into the 160×144 buffer."""
        # Clear
        self.frame_buffer[:] = b"\x00" * (WIDTH * HEIGHT)

        # Draw asteroids as circles
        for asteroid in self.asteroids:
            if asteroid.active:
                self._draw_circle(
                    asteroid.kinetics.position, asteroid.radius, color=2
                )

        # Draw ship as triangle
        self._draw_ship()

        # Draw exhaust particles as single pixels
        for particle in self.exhaust.get_all_particles():
            px, py = int(particle.x), int(particle.y)
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                self.frame_buffer[py * WIDTH + px] = 3  # Bright particle

    def _draw_ship(self) -> None:
        """Draw ship as a small triangle at heading."""
        cx, cy = self.ship.position.to_int_tuple()
        h = self.ship.heading
        size = 4
        # Three vertices of the triangle
        nose = (int(cx + math.cos(h) * size), int(cy + math.sin(h) * size))
        left = (
            int(cx + math.cos(h + 2.4) * size * 0.7),
            int(cy + math.sin(h + 2.4) * size * 0.7),
        )
        right = (
            int(cx + math.cos(h - 2.4) * size * 0.7),
            int(cy + math.sin(h - 2.4) * size * 0.7),
        )
        self._draw_line(nose, left, color=1)
        self._draw_line(left, right, color=1)
        self._draw_line(right, nose, color=1)

    def _draw_circle(self, center: Vector2, radius: float, color: int) -> None:
        """Midpoint circle algorithm."""
        cx, cy = int(center.x), int(center.y)
        r = int(radius)
        x, y, d = 0, r, 1 - r
        self._circle_points(cx, cy, x, y, color)
        while x < y:
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1
            self._circle_points(cx, cy, x, y, color)

    def _circle_points(
        self, cx: int, cy: int, x: int, y: int, color: int
    ) -> None:
        for px, py in [
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x),
        ]:
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                self.frame_buffer[py * WIDTH + px] = color

    def _draw_line(
        self, p1: Tuple[int, int], p2: Tuple[int, int], color: int
    ) -> None:
        """Bresenham's line algorithm."""
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            if 0 <= x1 < WIDTH and 0 <= y1 < HEIGHT:
                self.frame_buffer[y1 * WIDTH + x1] = color
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    # -- Main runner ---------------------------------------------------------

    def run(self, frames: int = 300) -> Dict[str, Any]:
        """Execute *frames* simulation steps and return a performance report."""
        dt = 1.0 / 60.0  # 60 Hz

        # Setup
        self.spawn_asteroid_field()
        self.wire_exhaust()
        self.perf = initialize_performance_monitor(target_fps=60)

        logger.info(
            f"🚀 Asteroids Stress Test: {frames} frames, "
            f"1 ship + {self.asteroid_count} asteroids"
        )

        for _ in range(frames):
            self.perf.start_frame()
            self.update(dt)
            self.perf.end_frame()

        # Gather results
        stats = self.perf.get_current_stats()
        exhaust_stats = self.exhaust.get_system_stats()

        report = {
            "frames_rendered": self.frame_count,
            "total_collisions": self.collisions,
            "avg_fps": stats.avg_fps,
            "min_fps": stats.min_fps,
            "max_fps": stats.max_fps,
            "avg_frame_time_ms": stats.avg_frame_time * 1000,
            "pillar_avg_ms": {
                k: v * 1000 for k, v in stats.pillar_averages.items()
            },
            "pillar_max_ms": {
                k: v * 1000 for k, v in stats.pillar_max_times.items()
            },
            "exhaust_total_particles_peak": exhaust_stats["max_particles_seen"],
            "exhaust_avg_particles": exhaust_stats["average_particle_count"],
        }
        return report

# ---------------------------------------------------------------------------
# Visual mode (TK window)
# ---------------------------------------------------------------------------

# Palette: index → (R, G, B)
PALETTE = {
    0: (0, 0, 0),         # Background — black
    1: (0, 255, 100),     # Ship — neon green
    2: (140, 140, 160),   # Asteroids — cool grey
    3: (255, 160, 50),    # Exhaust particles — amber
}

SCALE = 4  # 160×144 → 640×576


class VisualRunner:
    """Wraps AsteroidsSlice with a tkinter game loop and key input."""

    def __init__(self, slice_sim: AsteroidsSlice) -> None:
        self.sim = slice_sim
        self.dt = 1.0 / 60.0

        # Input state (held keys)
        self._thrust = False
        self._rotate_left = False
        self._rotate_right = False

    def launch(self) -> None:
        """Open the TK window and start the game loop."""
        import tkinter as tk

        win_w = WIDTH * SCALE
        win_h = HEIGHT * SCALE

        self.root = tk.Tk()
        self.root.title("Asteroids Stress Test — Kinetic Alignment")
        self.root.resizable(False, False)
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(
            self.root, width=win_w, height=win_h,
            bg="black", highlightthickness=0,
        )
        self.canvas.pack()

        # PhotoImage at native resolution — we'll scale via zoom
        self._photo = tk.PhotoImage(width=WIDTH, height=HEIGHT)
        self._canvas_img = self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self._photo,
        )
        # Zoom PhotoImage to 4× via built-in subsample/zoom
        self._photo_scaled = self._photo.zoom(SCALE, SCALE)
        self.canvas.itemconfig(self._canvas_img, image=self._photo_scaled)

        # HUD text
        self._hud = self.canvas.create_text(
            8, 8, anchor=tk.NW, fill="#00FF66",
            font=("Consolas", 10), text="",
        )

        # Key bindings
        self.root.bind("<KeyPress-Left>", lambda e: self._set_rotate_left(True))
        self.root.bind("<KeyRelease-Left>", lambda e: self._set_rotate_left(False))
        self.root.bind("<KeyPress-Right>", lambda e: self._set_rotate_right(True))
        self.root.bind("<KeyRelease-Right>", lambda e: self._set_rotate_right(False))
        self.root.bind("<KeyPress-Up>", lambda e: self._set_thrust(True))
        self.root.bind("<KeyRelease-Up>", lambda e: self._set_thrust(False))
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        # Disable automatic waypoint navigation — player is in control
        self.sim.waypoint = None

        # Kick off the game loop
        self._tick()
        self.root.mainloop()

    # -- Input handlers ------------------------------------------------------

    def _set_thrust(self, val: bool) -> None:
        self._thrust = val

    def _set_rotate_left(self, val: bool) -> None:
        self._rotate_left = val

    def _set_rotate_right(self, val: bool) -> None:
        self._rotate_right = val

    # -- Game loop -----------------------------------------------------------

    def _tick(self) -> None:
        """One frame: input → physics → render → blit."""
        t0 = time.time()

        # Apply player input to ship kinetics
        rot_speed = 4.0  # rad/s
        if self._rotate_left:
            self.sim.ship.kinetics.angular_velocity = -rot_speed
        elif self._rotate_right:
            self.sim.ship.kinetics.angular_velocity = rot_speed
        else:
            self.sim.ship.kinetics.angular_velocity = 0.0

        if self._thrust:
            self.sim.ship.kinetics.set_thrust(
                self.sim.ship.kinetics.max_velocity * 0.6
            )
        else:
            self.sim.ship.kinetics.acceleration = Vector2.zero()

        # Override waypoint-based autopilot — manual mode
        is_thrusting = self._thrust

        # Physics
        self.sim.ship.kinetics.update(self.dt)
        for asteroid in self.sim.asteroids:
            if asteroid.active:
                asteroid.kinetics.update(self.dt)

        # VFX
        heading_deg = math.degrees(self.sim.ship.heading)
        self.sim.exhaust.update_ship_thrust(
            self.sim.ship.ship_id,
            self.sim.ship.position.x,
            self.sim.ship.position.y,
            heading_deg,
            is_thrusting,
            intensity=0.9,
        )
        self.sim.exhaust.update(self.dt)

        # Collision
        self.sim._check_collisions()

        # Render to buffer
        self.sim._render_frame()
        self.sim.frame_count += 1

        # Blit to PhotoImage
        self._blit_frame()

        # HUD
        elapsed_ms = (time.time() - t0) * 1000
        fps = 1000.0 / max(elapsed_ms, 0.001)
        particles = self.sim.exhaust.total_particles
        self.canvas.itemconfig(
            self._hud,
            text=(
                f"FPS: {fps:.0f}  |  "
                f"Particles: {particles}  |  "
                f"Collisions: {self.sim.collisions}  |  "
                f"Frame: {self.sim.frame_count}"
            ),
        )

        # Schedule next frame (16ms ≈ 60Hz)
        self.root.after(16, self._tick)

    def _blit_frame(self) -> None:
        """Convert palette-indexed frame_buffer to PPM and update PhotoImage."""
        # Build PPM P6 (binary RGB) data
        fb = self.sim.frame_buffer
        pixels = bytearray(WIDTH * HEIGHT * 3)
        for i, idx in enumerate(fb):
            r, g, b = PALETTE.get(idx, (0, 0, 0))
            off = i * 3
            pixels[off] = r
            pixels[off + 1] = g
            pixels[off + 2] = b

        header = f"P6 {WIDTH} {HEIGHT} 255\n".encode()
        ppm_data = header + bytes(pixels)

        import tkinter as tk
        self._photo = tk.PhotoImage(width=WIDTH, height=HEIGHT, data=ppm_data)
        self._photo_scaled = self._photo.zoom(SCALE, SCALE)
        self.canvas.itemconfig(self._canvas_img, image=self._photo_scaled)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Asteroids Stress Test.

    Usage:
        python -m apps.space.asteroids_slice            # headless benchmark
        python -m apps.space.asteroids_slice --visual    # TK window
    """
    logger.remove()
    logger.add(sys.stderr, level="WARNING")

    visual = "--visual" in sys.argv

    s = AsteroidsSlice(asteroid_count=50)

    if visual:
        # Setup entities but skip perf monitor (realtime mode)
        s.spawn_asteroid_field()
        s.wire_exhaust()
        runner = VisualRunner(s)
        runner.launch()
    else:
        report = s.run(frames=300)

        print("\n" + "=" * 60)
        print("  ASTEROIDS STRESS TEST - PERFORMANCE REPORT")
        print("=" * 60)
        print(f"  Frames rendered : {report['frames_rendered']}")
        print(f"  Total collisions: {report['total_collisions']}")
        print(f"  Avg FPS         : {report['avg_fps']:.1f}")
        print(f"  Min FPS         : {report['min_fps']:.1f}")
        print(f"  Max FPS         : {report['max_fps']:.1f}")
        print(f"  Avg frame time  : {report['avg_frame_time_ms']:.3f} ms")
        print("-" * 60)
        print("  Pillar Breakdown (avg / max ms):")
        for pillar in ["physics", "vfx", "collision", "render"]:
            avg = report["pillar_avg_ms"].get(pillar, 0)
            mx = report["pillar_max_ms"].get(pillar, 0)
            bar_len = int(avg * 100)
            bar = "█" * min(bar_len, 40)
            print(f"    {pillar:>10s}: {avg:7.3f} / {mx:7.3f}  {bar}")
        print("-" * 60)
        print(f"  Exhaust peak    : {report['exhaust_total_particles_peak']} particles")
        print(f"  Exhaust avg     : {report['exhaust_avg_particles']:.1f} particles")
        print("=" * 60)

        budget_ms = 16.667
        if report["avg_frame_time_ms"] < budget_ms:
            print(f"  PASS - under {budget_ms:.1f} ms frame budget")
        else:
            print(f"  WARN - avg {report['avg_frame_time_ms']:.3f} ms exceeds {budget_ms:.1f} ms budget")
        print()


if __name__ == "__main__":
    main()
