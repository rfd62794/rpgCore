"""
Tournament Mode - Live Evolution Spectator
Multi-AI competition with visual debugging and scrap collection
"""

import pygame
import sys
import math
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rpg_core.foundation.types import Result
from rpg_core.foundation.constants import SOVEREIGN_WIDTH, SOVEREIGN_HEIGHT, DEBUG_INFINITE_ENERGY
from rpg_core.systems.mind.neat.neat_engine import NeuralNetwork
from apps.space.logic.ai_controller import create_ai_controller
from apps.space.arcade_visual_asteroids import ArcadeVisualAsteroids


class TournamentPilot:
    """Individual AI pilot for tournament mode"""
    
    def __init__(self, pilot_id: str, color: Tuple[int, int, int], 
                 generation: int, network_file: Optional[str] = None):
        self.pilot_id = pilot_id
        self.color = color
        self.generation = generation
        
        # Create AI controller
        neural_network = None
        if network_file and Path(network_file).exists():
            neural_network = self._load_network(network_file)
        
        self.controller = create_ai_controller(
            controller_id=pilot_id,
            use_neural_network=(neural_network is not None),
            neural_network=neural_network
        )
        
        # Performance metrics
        self.survival_time = 0.0
        self.asteroids_destroyed = 0
        self.scrap_collected = 0
        self.fitness = 0.0
        
        # Visual position (for tournament display)
        self.visual_x = 0
        self.visual_y = 0
        self.visual_angle = 0
        
        logger.info(f"🤖 Tournament pilot {pilot_id} (Gen {generation}) initialized")
    
    def _load_network(self, filename: str) -> Optional[NeuralNetwork]:
        """Load neural network from file"""
        try:
            with open(filename, 'r') as f:
                network_data = json.load(f)
            
            # Reconstruct neural network
            network = NeuralNetwork(
                num_inputs=network_data['num_inputs'],
                num_hidden=network_data['num_hidden'],
                num_outputs=network_data['num_outputs']
            )
            
            # Restore weights and biases
            network.weights_input_hidden = network_data['weights_input_hidden']
            network.weights_hidden_output = network_data['weights_hidden_output']
            network.bias_hidden = network_data['bias_hidden']
            network.bias_output = network_data['bias_output']
            
            logger.info(f"📖 Loaded neural network from {filename}")
            return network
            
        except Exception as e:
            logger.error(f"Failed to load network {filename}: {e}")
            return None
    
    def update_fitness(self, survival_time: float, asteroids_destroyed: int, scrap_collected: int) -> None:
        """Update pilot fitness with scrap awareness"""
        self.survival_time = survival_time
        self.asteroids_destroyed = asteroids_destroyed
        self.scrap_collected = scrap_collected
        
        # Fitness = Survival + (Rocks * 10) + (Scrap * 25)
        self.fitness = survival_time + (asteroids_destroyed * 10) + (scrap_collected * 25)
    
    def get_mental_vector(self) -> Dict[str, Any]:
        """Get the AI's current mental vector for debugging"""
        if hasattr(self.controller, 'get_mental_vector'):
            return self.controller.get_mental_vector()
        return {'x': 0, 'y': 0, 'target': None, 'type': None}


class TournamentMode:
    """Live evolution tournament with multiple AI pilots"""
    
    def __init__(self):
        self.running = True
        
        # Initialize PyGame
        pygame.init()
        
        # Create display with 4x scaling for desktop visibility
        scale_factor = 4
        self.screen_width = SOVEREIGN_WIDTH * scale_factor
        self.screen_height = SOVEREIGN_HEIGHT * scale_factor
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("DGT Platform - AI Tournament Mode")
        
        # Create surface for game rendering (160x144)
        self.game_surface = pygame.Surface((SOVEREIGN_WIDTH, SOVEREIGN_HEIGHT))
        
        # Tournament pilots
        self.pilots = []
        
        # Pilot colors
        self.pilot_colors = [
            (255, 100, 100),  # Red - Gen 0
            (100, 255, 100),  # Green - Gen 25  
            (100, 100, 255),  # Blue - Gen 50
        ]
        
        # Initialize pilots
        self._initialize_pilots()
        
        # Game state
        self.game_time = 0.0
        self.dt = 1.0 / 60.0
        
        # Colors
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'light_gray': (192, 192, 192),
            'dark_gray': (64, 64, 64),
            'green': (0, 255, 0),
            'red': (255, 0, 0),
            'blue': (0, 100, 255),
            'yellow': (255, 255, 0),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'cyan': (0, 255, 255)
        }
        
        # Pilot colors
        self.pilot_colors = [
            (255, 100, 100),  # Red - Gen 0
            (100, 255, 100),  # Green - Gen 25  
            (100, 100, 255),  # Blue - Gen 50
        ]
        
        # Font
        try:
            self.font = pygame.font.Font(None, 8)
        except:
            self.font = pygame.font.SysFont('monospace', 6)
        
        # Scrap entities
        self.scrap_entities = []
        self._spawn_scrap()
        
        # Asteroids
        self.asteroids = []
        self._spawn_asteroids()
        
        # Environmental noise
        self.noise_factor = 0.1  # 10% velocity variation
        
        logger.info("🏆 Tournament Mode initialized")
    
    def _initialize_pilots(self) -> None:
        """Initialize tournament pilots"""
        pilot_configs = [
            #("GEN_0_PILOT", self.pilot_colors[0], 0, None),  # Rule-based
            ("GEN_25_PILOT", self.pilot_colors[1], 25, "best_pilot_network.json"),  # Load best network for Green
            #("GEN_50_PILOT", self.pilot_colors[2], 50, "best_pilot_network.json"),  # Load best network
        ]
        
        for pilot_id, color, generation, network_file in pilot_configs:
            pilot = TournamentPilot(pilot_id, color, generation, network_file)
            self.pilots.append(pilot)
    
    def _spawn_scrap(self) -> None:
        """Spawn scrap entities for collection"""
        scrap_configs = [
            {'x': 80, 'y': 40, 'value': 5, 'radius': 3},
            {'x': 40, 'y': 100, 'value': 10, 'radius': 4},
            {'x': 120, 'y': 80, 'value': 15, 'radius': 5},
            {'x': 60, 'y': 60, 'value': 8, 'radius': 3},
        ]
        
        for config in scrap_configs:
            self.scrap_entities.append(config.copy())
    
    def _spawn_asteroids(self) -> None:
        """Spawn asteroids with environmental noise"""
        base_asteroids = [
            {'x': 50, 'y': 50, 'vx': 30, 'vy': 20, 'size': 3, 'radius': 8.0, 'health': 3, 'color': 'dark_gray'},
            {'x': 120, 'y': 80, 'vx': -25, 'vy': 35, 'size': 2, 'radius': 4.0, 'health': 2, 'color': 'gray'},
            {'x': 30, 'y': 100, 'vx': 40, 'vy': -30, 'size': 2, 'radius': 4.0, 'health': 2, 'color': 'light_gray'},
        ]
        
        noise_factor = 0.1  # 10% velocity variation
        
        for asteroid in base_asteroids:
            # Apply environmental noise
            noisy_asteroid = asteroid.copy()
            noisy_asteroid['vx'] *= (1.0 + random.uniform(-noise_factor, noise_factor))
            noisy_asteroid['vy'] *= (1.0 + random.uniform(-noise_factor, noise_factor))
            self.asteroids.append(noisy_asteroid)
    
    def handle_events(self) -> None:
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Reset tournament
                    self._reset_tournament()
    
    def update_game_state(self) -> None:
        """Update tournament game state"""
        self.game_time += self.dt
        
        # Update asteroids
        for asteroid in self.asteroids:
            asteroid['x'] += asteroid['vx'] * self.dt
            asteroid['y'] += asteroid['vy'] * self.dt
            
            # Wrap around screen
            asteroid['x'] = asteroid['x'] % SOVEREIGN_WIDTH
            asteroid['y'] = asteroid['y'] % SOVEREIGN_HEIGHT
        
        # Update each pilot
        for pilot in self.pilots:
            self._update_pilot(pilot)
        
        # Check collisions
        self._check_collisions()
        
        # Respawn entities if needed
        if len(self.asteroids) < 2:
            self._spawn_asteroids()
        
        if len(self.scrap_entities) < 3:
            self._spawn_scrap()
    
    def _update_pilot(self, pilot: TournamentPilot) -> None:
        """Update individual pilot"""
        # Create mock entity state
        entity_state = {
            'x': SOVEREIGN_WIDTH // 2,
            'y': SOVEREIGN_HEIGHT // 2,
            'vx': 0.0,
            'vy': 0.0,
            'angle': 0.0,
            'energy': 100.0
        }
        
        # Create world data
        world_data = {
            'asteroids': self.asteroids,
            'scrap': self.scrap_entities
        }
        
        # Update controller
        control_result = pilot.controller.update(self.dt, entity_state, world_data)
        
        if control_result.success:
            controls = control_result.value
            
            # Update visual position based on controls
            if controls.thrust != 0:
                thrust_magnitude = controls.thrust * 50.0
                pilot.visual_x += thrust_magnitude * math.cos(pilot.visual_angle) * self.dt
                pilot.visual_y += thrust_magnitude * math.sin(pilot.visual_angle) * self.dt
            
            if controls.rotation != 0:
                pilot.visual_angle += controls.rotation * 3.0 * self.dt
                pilot.visual_angle = pilot.visual_angle % (2 * math.pi)
            
            # Wrap position
            pilot.visual_x = pilot.visual_x % SOVEREIGN_WIDTH
            pilot.visual_y = pilot.visual_y % SOVEREIGN_HEIGHT
            
            # Update fitness
            pilot.update_fitness(self.game_time, 0, 0)  # Simplified for tournament
    
    def _check_collisions(self) -> None:
        """Check collisions for all pilots"""
        for pilot in self.pilots:
            # Check scrap collection
            scrap_to_remove = []
            for scrap_idx, scrap in enumerate(self.scrap_entities):
                distance = math.sqrt((pilot.visual_x - scrap['x'])**2 + 
                                   (pilot.visual_y - scrap['y'])**2)
                if distance < scrap['radius'] + 3:  # Ship radius
                    scrap_to_remove.append(scrap_idx)
                    pilot.scrap_collected += scrap['value']
            
            # Remove collected scrap
            for scrap_idx in sorted(scrap_to_remove, reverse=True):
                del self.scrap_entities[scrap_idx]
    
    def render_game(self) -> None:
        """Render tournament mode"""
        # Clear surface
        self.game_surface.fill(self.colors['black'])
        
        # Draw scrap entities
        self._draw_scrap()
        
        # Draw asteroids
        self._draw_asteroids()
        
        # Draw pilots
        self._draw_pilots()
        
        # Draw mental vectors
        self._draw_mental_vectors()
        
        # Draw tournament HUD
        self._draw_tournament_hud()
        
        # Scale to screen
        scaled_surface = pygame.transform.scale(self.game_surface, (self.screen_width, self.screen_height))
        self.screen.blit(scaled_surface, (0, 0))
        
        pygame.display.flip()
    
    def _draw_scrap(self) -> None:
        """Draw scrap entities"""
        for scrap in self.scrap_entities:
            # Draw scrap as diamond
            size = scrap['radius']
            points = [
                (scrap['x'], scrap['y'] - size),
                (scrap['x'] + size, scrap['y']),
                (scrap['x'], scrap['y'] + size),
                (scrap['x'] - size, scrap['y'])
            ]
            pygame.draw.polygon(self.game_surface, self.colors['yellow'], points)
            pygame.draw.polygon(self.game_surface, self.colors['orange'], points, 1)
    
    def _draw_asteroids(self) -> None:
        """Draw asteroids"""
        for asteroid in self.asteroids:
            color = self.colors[asteroid['color']]
            pygame.draw.circle(self.game_surface, color, 
                             (int(asteroid['x']), int(asteroid['y'])), 
                             int(asteroid['radius']))
            pygame.draw.circle(self.game_surface, self.colors['white'], 
                             (int(asteroid['x']), int(asteroid['y'])), 
                             int(asteroid['radius']), 1)
    
    def _draw_pilots(self) -> None:
        """Draw tournament pilots"""
        for pilot in self.pilots:
            # Draw triangle ship
            ship_points = [
                (pilot.visual_x + 6 * math.cos(pilot.visual_angle), 
                 pilot.visual_y + 6 * math.sin(pilot.visual_angle)),
                (pilot.visual_x + 6 * math.cos(pilot.visual_angle + 2.4), 
                 pilot.visual_y + 6 * math.sin(pilot.visual_angle + 2.4)),
                (pilot.visual_x + 6 * math.cos(pilot.visual_angle - 2.4), 
                 pilot.visual_y + 6 * math.sin(pilot.visual_angle - 2.4))
            ]
            
            pygame.draw.polygon(self.game_surface, pilot.color, ship_points)
            pygame.draw.polygon(self.game_surface, self.colors['white'], ship_points, 1)
    
    def _draw_mental_vectors(self) -> None:
        """Draw mental vectors for debugging"""
        for pilot in self.pilots:
            mental_vector = pilot.get_mental_vector()
            
            if mental_vector['target']:
                # Draw line from pilot to target
                target_x = pilot.visual_x + mental_vector['x']
                target_y = pilot.visual_y + mental_vector['y']
                
                # Choose color based on target type
                if mental_vector['type'] == 'threat':
                    vector_color = self.colors['red']
                elif mental_vector['type'] == 'resource':
                    vector_color = self.colors['yellow']
                else:
                    vector_color = self.colors['gray']
                
                # Draw mental vector line
                pygame.draw.line(self.game_surface, vector_color,
                               (int(pilot.visual_x), int(pilot.visual_y)),
                               (int(target_x), int(target_y)), 1)
                
                # Draw target indicator
                pygame.draw.circle(self.game_surface, vector_color,
                                 (int(target_x), int(target_y)), 2)
    
    def _draw_tournament_hud(self) -> None:
        """Draw tournament HUD"""
        y_offset = 2
        
        # Title
        title_text = "AI TOURNAMENT"
        title_surface = self.font.render(title_text, True, self.colors['white'])
        self.game_surface.blit(title_surface, (2, y_offset))
        y_offset += 10
        
        # Pilot scores
        for pilot in self.pilots:
            pilot_text = f"{pilot.pilot_id}: S={pilot.scrap_collected} F={pilot.fitness:.1f}"
            pilot_surface = self.font.render(pilot_text, True, pilot.color)
            self.game_surface.blit(pilot_surface, (2, y_offset))
            y_offset += 8
        
        # Instructions
        instructions = [
            "ESC: Exit",
            "R: Reset",
            "Lines: AI thinking"
        ]
        
        y_offset = SOVEREIGN_HEIGHT - 30
        for instruction in instructions:
            inst_surface = self.font.render(instruction, True, self.colors['green'])
            self.game_surface.blit(inst_surface, (2, y_offset))
            y_offset += 8
    
    def _reset_tournament(self) -> None:
        """Reset tournament"""
        # Reset pilots
        for pilot in self.pilots:
            pilot.visual_x = SOVEREIGN_WIDTH // 2
            pilot.visual_y = SOVEREIGN_HEIGHT // 2
            pilot.visual_angle = 0.0
            pilot.survival_time = 0.0
            pilot.asteroids_destroyed = 0
            pilot.scrap_collected = 0
            pilot.fitness = 0.0
        
        # Reset entities
        self.scrap_entities.clear()
        self.asteroids.clear()
        self._spawn_scrap()
        self._spawn_asteroids()
        
        # Reset time
        self.game_time = 0.0
        
        logger.info("🔄 Tournament reset")
    
    def run(self) -> Result[bool]:
        """Main tournament loop"""
        try:
            clock = pygame.time.Clock()
            
            logger.info("🏆 Starting AI Tournament")
            
            while self.running:
                # Handle events
                self.handle_events()
                
                # Update game state
                self.update_game_state()
                
                # Render
                self.render_game()
                
                # Control frame rate
                clock.tick(60)
            
            return Result(success=True, value=True)
            
        except Exception as e:
            return Result(success=False, error=f"Tournament failed: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        pygame.quit()
        logger.info("🧹 Tournament Mode cleanup complete")


def main():
    """Main entry point for Tournament Mode"""
    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="{time:HH:mm:ss} | {level} | {message}"
    )
    
    print("🏆 DGT Platform - AI Tournament Mode")
    print("=" * 45)
    print("Live Evolution Spectator")
    print("Single Pilot Mode: Gen 25 (Green)")
    print("Scrap collection prioritized over survival")
    print()
    
    # Create and run tournament
    tournament = TournamentMode()
    
    try:
        result = tournament.run()
        
        if result.success:
            print("🏆 Tournament completed successfully!")
            return 0
        else:
            print(f"❌ Tournament failed: {result.error}")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Tournament interrupted by user")
        return 0
    finally:
        tournament.cleanup()


if __name__ == "__main__":
    exit(main())
