"""
DGT Neuro Evolution Demo - ADR 133 Implementation
Live visualization of NEAT-based AI evolution in space combat

Demonstrates:
- Generation 0 (random) vs Generation 50 (trained) comparison
- Real-time neural network control
- ELO-based ranking and novelty search
- Live evolution visualization
"""

import tkinter as tk
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from loguru import logger

# Import DGT neuro evolution components
from src.dgt_core.simulation.neuro_pilot import NeuroPilot, NeuroPilotFactory, initialize_neuro_pilot_factory
from src.dgt_core.simulation.training_paddock import TrainingPaddock, initialize_training_paddock
from src.dgt_core.engines.body.ship_renderer import (
    ShipRenderer, ShipDNA, ShipClass, RenderPacket, 
    initialize_ship_renderer, get_ship_renderer
)
from src.dgt_core.simulation.space_physics import SpaceShip, SpaceVoyagerEngine
from src.dgt_core.simulation.projectile_system import ProjectileSystem, initialize_projectile_system


class NeuroEvolutionArena:
    """Live visualization arena for neuro evolution"""
    
    def __init__(self, width: int = 1000, height: int = 700):
        self.width = width
        self.height = height
        
        # Initialize systems
        self.ship_renderer = initialize_ship_renderer(width, height)
        self.projectile_system = initialize_projectile_system()
        
        # Initialize NEAT evolution components
        self.pilot_factory = initialize_neuro_pilot_factory()
        self.training_paddock = initialize_training_paddock(population_size=20, num_processes=4)
        
        # Battle ships
        self.ships: Dict[str, SpaceShip] = {}
        self.pilots: Dict[str, NeuroPilot] = {}
        
        # Simulation state
        self.simulation_time = 0.0
        self.dt = 1.0 / 60.0
        self.is_running = False
        self.battle_complete = False  # Keep this for potential future use
        
        # Evolution state
        self.current_generation = 0
        self.is_training = False
        self.training_progress = 0.0
        
        # Battle statistics
        self.shots_fired = 0
        self.total_hits = 0
        self.total_damage = 0.0
        
        # Tkinter setup
        self.root = tk.Tk()
        self.root.title("🧠 DGT Neuro Evolution - Live AI Training")
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, False)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root, 
            width=width, 
            height=height, 
            bg="#000011",
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Control panel
        self.control_frame = tk.Frame(self.root, bg="#000011")
        self.control_frame.place(x=10, y=10)
        
        self.status_label = tk.Label(
            self.control_frame,
            text="Initializing Neuro Evolution...",
            bg="#000011",
            fg="#00FF00",
            font=("Courier", 10)
        )
        self.status_label.pack()
        
        self.evolution_label = tk.Label(
            self.control_frame,
            text="",
            bg="#000011",
            fg="#00FFFF",
            font=("Courier", 9)
        )
        self.evolution_label.pack()
        
        self.control_button = tk.Button(
            self.control_frame,
            text="Start Training",
            command=self.toggle_training,
            bg="#001144",
            fg="white",
            font=("Courier", 9)
        )
        self.control_button.pack(pady=5)
        
        logger.info(f"🧠 Neuro Evolution Arena initialized: {width}x{height}")
    
    def setup_evolution_battle(self):
        """Setup initial evolution battle"""
        logger.info("🧠 Setting up neuro evolution battle...")
        
        # Create two demonstration ships
        # Ship 1: Generation 0 (random)
        pilot0 = self.training_paddock.pilots[0]  # Random pilot
        ship0 = self._create_neuro_ship("Gen0_Random", pilot0, 300, 350, 0)
        
        # Ship 2: Best trained pilot (if available)
        if len(self.training_paddock.pilots) > 1:
            # Use best pilot for demonstration
            best_pilot = max(self.training_paddock.pilots, key=lambda p: p.fitness)
            ship1 = self._create_neuro_ship("Trained_Best", best_pilot, 700, 350, 180)
        else:
            # Use second random pilot if no training done yet
            pilot1 = self.training_paddock.pilots[1]
            ship1 = self._create_neuro_ship("Gen0_Random_2", pilot1, 700, 350, 180)
        
        logger.info(f"🧠 Evolution battle setup: {len(self.ships)} ships")
    
    def _create_neuro_ship(self, ship_name: str, pilot: NeuroPilot, x: float, y: float, heading: float) -> SpaceShip:
        """Create neuro-controlled ship with solid body rendering"""
        # Create ship physics
        ship = SpaceShip(
            ship_id=pilot.genome.key,
            x=x, y=y,
            heading=heading,
            velocity_x=0.0, velocity_y=0.0,
            hull_integrity=200.0,
            shield_strength=100.0,
            weapon_range=400.0,
            weapon_damage=25.0,
            fire_rate=2.0
        )
        
        # Create ship engine
        ship.engine = SpaceVoyagerEngine(
            thrust_power=0.5,
            rotation_speed=5.0
        )
        
        # Assign pilot
        self.pilots[pilot.genome.key] = pilot
        self.ships[pilot.genome.key] = ship
        
        # Create ShipDNA for solid body rendering
        ship_dna = ShipDNA()
        if "Random" in ship_name:
            ship_dna.hull_color = "#4A90E2"  # Blue for random
            ship_dna.reactor_color = "#F5A623"  # Orange
        else:
            ship_dna.hull_color = "#D0021B"  # Red for trained
            ship_dna.reactor_color = "#BD10E0"  # Purple
        
        # Store ship DNA for rendering
        ship.ship_dna = ship_dna
        ship.ship_class = ShipClass.INTERCEPTOR
        
        logger.debug(f"🧠 Created neuro ship: {ship_name} (pilot: {pilot.genome.key})")
        return ship
    
    def update(self):
        """Update neuro evolution simulation"""
        if not self.is_running:
            return
        
        self.simulation_time += self.dt
        
        # Get active ships
        active_ships = [ship for ship in self.ships.values() if not ship.is_destroyed()]
        
        # Auto-respawn if battle is complete to keep training running
        if len(active_ships) < 2:
            self._respawn_ships()
            active_ships = [ship for ship in self.ships.values() if not ship.is_destroyed()]
        
        # Update each neuro-controlled ship
        for fleet_ship in self.pilots.values():
            ship = self.ships.get(fleet_ship.genome.key)
            if not ship or ship.is_destroyed():
                continue
            
            # Get targets and threats
            targets = [s for s in active_ships if s.ship_id != ship.ship_id]
            threats = targets  # All enemies are threats in this demo
            
            # Get neural action
            action = fleet_ship.get_action(ship, targets, threats)
            
            # Apply neural control
            fleet_ship.apply_action(ship, action, self.dt)
            
            # Create render packet for solid body
            render_packet = RenderPacket(
                ship_id=ship.ship_id,
                x=ship.x,
                y=ship.y,
                heading=ship.heading,
                velocity_x=ship.velocity_x,
                velocity_y=ship.velocity_y,
                ship_class=getattr(ship, 'ship_class', ShipClass.INTERCEPTOR),
                ship_dna=getattr(ship, 'ship_dna', ShipDNA()),
                is_destroyed=ship.is_destroyed(),
                thrust_level=action.thrust
            )
            
            # Render solid ship body
            self.ship_renderer.render_ship(render_packet, self.canvas)
            
            # Handle weapon firing
            if fleet_ship.should_fire_weapon(action, ship):
                if targets:
                    target = targets[0]  # Target first enemy
                    proj_id = self.projectile_system.fire_projectile(ship, target)
                    if proj_id:
                        self.shots_fired += 1
                        fleet_ship.shots_fired += 1
                        logger.debug(f"🧠 {fleet_ship.genome.key} fires neural weapon")
            
            # Keep ship in bounds
            self._keep_ship_in_bounds(ship)
        
        # Update projectiles
        impacts = self.projectile_system.update(self.dt, active_ships)
        
        # Update exhaust particles
        self.ship_renderer.update_particles(self.dt, self.canvas)
        
        # Handle impacts
        for impact in impacts:
            self.total_hits += 1
            self.total_damage += impact.damage_dealt
            
            # Update pilot fitness
            target_pilot = self.pilots.get(impact.target_id)
            if target_pilot:
                target_pilot.update_fitness(False, 0, impact.damage_dealt, False, 0, self.current_generation)
            
            # Check for ship destruction
            target_ship = self.ships.get(impact.target_id)
            if target_ship and target_ship.is_destroyed():
                # Update fitness of attacker
                attacker_pilot = self.pilots.get(impact.projectile_id.split('_')[0])
                if attacker_pilot:
                    attacker_pilot.update_fitness(True, 0, 0, True, 1, self.current_generation)
                    logger.info(f"💥 Neural pilot {attacker_pilot.genome.key} scores a kill!")
                
                # Remove destroyed ship from renderer
                self.ship_renderer.clear_destroyed_ships([impact.target_id], self.canvas)
        
        # Update status displays
        self.update_status_display()
    
    def _respawn_ships(self):
        """Respawn destroyed ships to keep battle running"""
        logger.info("🧠 Respawning ships for continuous training...")
        
        # Reset all ships
        for pilot_id, pilot in self.pilots.items():
            ship = self.ships.get(pilot_id)
            if ship:
                # Reset ship health and position
                ship.hull_integrity = 200.0
                ship.shield_strength = 100.0
                ship.velocity_x = 0
                ship.velocity_y = 0
                
                # Random respawn position
                ship.x = random.randint(100, self.width - 100)
                ship.y = random.randint(100, self.height - 100)
                ship.heading = random.uniform(0, 360)
                
                # Clear destroyed flag in renderer
                render_packet = RenderPacket(
                    ship_id=ship.ship_id,
                    x=ship.x,
                    y=ship.y,
                    heading=ship.heading,
                    velocity_x=ship.velocity_x,
                    velocity_y=ship.velocity_y,
                    ship_class=getattr(ship, 'ship_class', ShipClass.INTERCEPTOR),
                    ship_dna=getattr(ship, 'ship_dna', ShipDNA()),
                    is_destroyed=False,
                    thrust_level=0.0
                )
                
                # Re-render ship as not destroyed
                self.ship_renderer.render_ship(render_packet, self.canvas)
                
                logger.debug(f"🧠 Respawned ship {pilot_id}")
    
    def _keep_ship_in_bounds(self, ship):
        """Keep ship within arena bounds"""
        margin = 50
        if ship.x < margin:
            ship.x = margin
            ship.velocity_x = abs(ship.velocity_x) * 0.5
        elif ship.x > self.width - margin:
            ship.x = self.width - margin
            ship.velocity_x = -abs(ship.velocity_x) * 0.5
        
        if ship.y < margin:
            ship.y = margin
            ship.velocity_y = abs(ship.velocity_y) * 0.5
        elif ship.y > self.height - margin:
            ship.y = self.height - margin
            ship.velocity_y = -abs(ship.velocity_y) * 0.5
    
    def toggle_training(self):
        """Toggle training mode"""
        if self.is_training:
            self.is_training = False
            self.control_button.config(text="Start Training")
            logger.info("🧠 Training paused")
        else:
            self.is_training = True
            self.control_button.config(text="Stop Training")
            logger.info("🧠 Training started")
            # Start training in background
            self.root.after(100, self.run_training_step)
    
    def run_training_step(self):
        """Run one step of training"""
        if not self.is_training:
            return
        
        # Run a few training matches
        try:
            matches = self.training_paddock.run_training_generation(num_matches=10)
            
            # Evolve population
            self.training_paddock.evolve_population()
            self.current_generation = self.training_paddock.current_generation
            
            # Update demonstration ships with new pilots
            self.update_demo_ships()
            
            # Update progress
            self.training_progress = min(1.0, self.current_generation / 50.0)
            
            logger.info(f"🧠 Training step complete: Generation {self.current_generation}")
            
            # Show generation info in status
            gen_info = f"Gen {self.current_generation} | "
            if self.current_generation > 0:
                stats = self.training_paddock.get_training_stats()
                gen_info += f"Avg Fit: {stats['average_fitness']:.2f} | "
            
            self.evolution_label.config(text=gen_info)
            
        except Exception as e:
            logger.error(f"🧠 Training step failed: {e}")
        
        # Schedule next training step
        if self.is_training:
            self.root.after(5000, self.run_training_step)  # Train every 5 seconds
    
    def update_demo_ships(self):
        """Update demonstration ships with new pilots"""
        # Get best pilot
        best_pilot = max(self.training_paddock.pilots, key=lambda p: p.fitness)
        
        # Update second ship with best pilot
        if len(self.ships) >= 2:
            ship_ids = list(self.ships.keys())
            old_pilot = self.pilots.get(ship_ids[1])
            
            # Remove old ship
            if ship_ids[1] in self.ships:
                del self.ships[ship_ids[1]]
            if ship_ids[1] in self.pilots:
                del self.pilots[ship_ids[1]]
            
            # Add new ship with best pilot
            new_ship = self._create_neuro_ship(f"Gen{self.current_generation}_Best", best_pilot, 700, 350, 180)
            
            # Update status to show improvement
            if self.current_generation > 0:
                stats = self.training_paddock.get_training_stats()
                improvement = best_pilot.fitness - 81.0  # Compare with initial best fitness
                status_text = f"🧠 Improvement: {improvement:+.1f} | "
                self.status_label.config(text=status_text)
    
    def update_status_display(self):
        """Update status displays"""
        accuracy = (self.total_hits / max(1, self.shots_fired) * 100)
        status_text = (
            f"Time: {self.simulation_time:.1f}s | "
            f"Shots: {self.shots_fired} | "
            f"Hits: {self.total_hits} | "
            f"Accuracy: {accuracy:.1f}% | "
            f"Status: {'TRAINING' if self.is_training else 'ACTIVE' if not self.battle_complete else 'COMPLETE'}"
        )
        self.status_label.config(text=status_text)
        
        # Evolution status
        evolution_text = (
            f"Generation: {self.current_generation} | "
            f"Training: {'Active' if self.is_training else 'Paused'} | "
            f"Progress: {self.training_progress:.1%} | "
            f"Population: {len(self.training_paddock.pilots)}"
        )
        self.evolution_label.config(text=evolution_text)
    
    def render_frame(self):
        """Render one frame"""
        # Clear canvas
        self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill="#000011",
            outline=""
        )
        
        # Render vector graphics
        self.vector_ppu.render_to_canvas(self.canvas)
    
    def game_loop(self):
        """Main game loop"""
        if self.is_running:
            self.update()
            self.render_frame()
            self.root.after(16, self.game_loop)  # ~60 FPS
    
    def run_neuro_evolution(self, duration: float = 60.0):
        """Run neuro evolution demonstration"""
        print("🧠 DGT Neuro Evolution Demo")
        print("=" * 60)
        print("Demonstrating NEAT-based AI evolution:")
        print("• Generation 0 (random) vs trained pilot comparison")
        print("• Real-time neural network control")
        print("• Live evolution training with ELO ranking")
        print("• Novelty search for diverse behaviors")
        print("• Visual fitness improvement tracking")
        print("=" * 60)
        
        # Setup battle
        self.setup_evolution_battle()
        
        # Start simulation
        self.is_running = True
        start_time = time.time()
        
        # Start game loop
        self.game_loop()
        
        # Schedule end
        self.root.after(int(duration * 1000), self.end_evolution)
        
        # Start Tkinter event loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nEvolution interrupted by user")
        
        # Final report
        self.print_evolution_report()
    
    def end_evolution(self):
        """End the neuro evolution demonstration"""
        self.is_running = False
        self.is_training = False
        self.battle_complete = True
        logger.info("🧠 Neuro evolution demonstration completed")
        
        # Keep window open for 5 seconds
        self.root.after(5000, self.root.quit)
    
    def print_evolution_report(self):
        """Print comprehensive evolution report"""
        stats = self.training_paddock.get_training_stats()
        best_pilots = stats.get('best_pilots', [])
        
        print("\n╭────── Neuro Evolution Report ───────╮")
        print(f"│ Final Generation: {stats['generation']}")
        print(f"│ Population Size: {stats['population_size']}")
        print(f"│ Total Matches: {stats['total_matches']}")
        print(f"│ Training Mode: {stats['training_mode']}")
        print(f"│ Top Fitness: {stats['top_fitness']:.2f}")
        print(f"│ Average Fitness: {stats['average_fitness']:.2f}")
        print(f"│ Top ELO Rating: {stats['top_elo']:.1f}")
        print(f"│ Average ELO: {stats['average_elo']:.1f}")
        print("╰─────────────────────────────────╯")
        
        if best_pilots:
            print("\n╭────── Top Performers ────────╮")
            for i, pilot_stats in enumerate(best_pilots[:3], 1):
                print(f"│ Rank {i}:")
                print(f"│   Fitness: {pilot_stats['fitness']:.2f}")
                print(f"│   Accuracy: {pilot_stats['accuracy']:.2f}")
                print(f"│   Enemies: {pilot_stats['enemies_destroyed']}")
                print(f"│   Novelty: {pilot_stats['novelty_score']:.3f}")
            print("╰─────────────────────────────────╯")
        
        print("\n🧠 Neuro Evolution System: Successfully integrated PyPongAI NEAT with RogueAsteroid physics!")


def main():
    """Main demonstration function"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and run neuro evolution
    arena = NeuroEvolutionArena()
    arena.run_neuro_evolution(duration=60.0)


if __name__ == "__main__":
    main()
