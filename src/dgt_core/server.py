"""
DGT Server - The "Mind" Simulation Engine
ADR 123: Local-First Microservice Bridge - Truth Provider

The Server generates world state independently of rendering concerns.
It runs as a separate process that can serve multiple UI clients.
"""

import time
import multiprocessing
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from queue import Queue, Empty
import json
import random
from pathlib import Path
import sys

# Add parent directories for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from loguru import logger
from .core.state import Entity, GameState, TileType, BiomeType
from .core.constants import TARGET_FPS, FRAME_DELAY_MS
from .simulation.breeding import GeneticBreedingService, UniversalTurtlePacket
from .simulation.genetics import TurboGenome, genetic_registry
from .simulation.racing import RacingService, RaceTrack
from .simulation.terrain_mapper import terrain_mapper

@dataclass
class SimulationConfig:
    """Configuration for simulation server"""
    world_width: int = 50
    world_height: int = 50
    target_fps: int = 60
    max_entities: int = 100
    enable_physics: bool = True
    enable_genetics: bool = True
    enable_racing: bool = True
    enable_d20: bool = True
    heartbeat_interval_ms: int = 16  # ~60Hz
    log_to_file: bool = True

class WorldGenerator:
    """Generates and manages the world state"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = {}
        self.biomes = {}
        self._generate_world()
    
    def _generate_world(self):
        """Generate world tiles and biomes"""
        # Generate tiles
        for x in range(self.width):
            for y in range(self.height):
                # Simple noise-based generation
                noise = (x * 7 + y * 13) % 100
                
                if noise < 30:
                    tile_type = TileType.WATER
                    biome = BiomeType.OCEAN
                elif noise < 50:
                    tile_type = TileType.SAND
                    biome = BiomeType.DESERT
                elif noise < 70:
                    tile_type = TileType.GRASS
                    biome = BiomeType.FOREST
                elif noise < 85:
                    tile_type = TileType.STONE
                    biome = BiomeType.MOUNTAIN
                else:
                    tile_type = TileType.DIRT
                    biome = BiomeType.SWAMP
                
                self.tiles[(x, y)] = tile_type
                self.biomes[(x, y)] = biome
    
    def get_tile(self, x: int, y: int) -> TileType:
        """Get tile at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles.get((x, y), TileType.GRASS)
        return TileType.GRASS
    
    def get_biome(self, x: int, y: int) -> BiomeType:
        """Get biome at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.biomes.get((x, y), BiomeType.FOREST)
        return BiomeType.FOREST

class EntitySystem:
    """Manages entities in the simulation"""
    
    def __init__(self, max_entities: int = 100):
        self.max_entities = max_entities
        self.entities: Dict[str, Entity] = {}
        self.next_id = 1
        
        # Create initial entities
        self._create_initial_entities()
    
    def _create_initial_entities(self):
        """Create initial entities for simulation"""
        # Player entity
        self.add_entity(Entity(
            id="player",
            x=25,
            y=25,
            entity_type="player",
            metadata={
                'health': 100,
                'level': 1,
                'experience': 0,
                'inventory': {'gold': 50, 'potions': 3}
            }
        ))
        
        # Some NPCs
        npcs = [
            ("turtle_1", 20, 20, "turtle"),
            ("turtle_2", 30, 30, "turtle"),
            ("merchant", 15, 15, "npc"),
            ("guard", 35, 35, "npc")
        ]
        
        for entity_id, x, y, entity_type in npcs:
            self.add_entity(Entity(
                id=entity_id,
                x=x,
                y=y,
                entity_type=entity_type,
                metadata={
                    'health': 50,
                    'speed': random.uniform(0.5, 2.0),
                    'direction': random.choice(['north', 'south', 'east', 'west'])
                }
            ))
    
    def add_entity(self, entity: Entity) -> bool:
        """Add entity to simulation"""
        if len(self.entities) >= self.max_entities:
            return False
        
        self.entities[entity.id] = entity
        return True
    
    def remove_entity(self, entity_id: str) -> bool:
        """Remove entity from simulation"""
        if entity_id in self.entities:
            del self.entities[entity_id]
            return True
        return False
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def update_entities(self, dt: float):
        """Update all entities"""
        for entity in list(self.entities.values()):
            self._update_entity(entity, dt)
    
    def _update_entity(self, entity: Entity, dt: float):
        """Update individual entity"""
        if entity.entity_type == "turtle":
            # Turtle genetics simulation
            speed = entity.metadata.get('speed', 1.0)
            direction = entity.metadata.get('direction', 'north')
            
            # Simple movement
            if random.random() < 0.1:  # 10% chance to change direction
                entity.metadata['direction'] = random.choice(['north', 'south', 'east', 'west'])
            
            # Move based on direction
            if direction == 'north' and entity.y > 0:
                entity.y -= 1
            elif direction == 'south' and entity.y < 49:
                entity.y += 1
            elif direction == 'east' and entity.x < 49:
                entity.x += 1
            elif direction == 'west' and entity.x > 0:
                entity.x -= 1
        
        elif entity.entity_type == "npc":
            # NPC behavior
            if random.random() < 0.05:  # 5% chance to move
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)
                entity.x = max(0, min(49, entity.x + dx))
                entity.y = max(0, min(49, entity.y + dy))

class PhysicsEngine:
    """Simple physics simulation"""
    
    def __init__(self):
        self.gravity = 9.81
        self.collision_enabled = True
    
    def update(self, entities: Dict[str, Entity], dt: float):
        """Update physics for all entities"""
        if not self.collision_enabled:
            return
        
        # Simple collision detection
        for entity in entities.values():
            # Apply gravity (simplified)
            if entity.entity_type not in ["player", "npc"]:
                entity.metadata.get('velocity_y', 0)
                # Physics would go here
        
        # Check entity collisions
        self._check_collisions(entities)
    
    def _check_collisions(self, entities: Dict[str, Entity]):
        """Check for entity collisions"""
        entity_list = list(entities.values())
        
        for i, entity1 in enumerate(entity_list):
            for entity2 in entity_list[i+1:]:
                if self._entities_collide(entity1, entity2):
                    self._handle_collision(entity1, entity2)
    
    def _entities_collide(self, entity1: Entity, entity2: Entity) -> bool:
        """Check if two entities collide"""
        return (entity1.x == entity2.x and entity1.y == entity2.y)
    
    def _handle_collision(self, entity1: Entity, entity2: Entity):
        """Handle collision between entities"""
        # Simple separation
        if entity1.x < entity2.x:
            entity1.x -= 1
        else:
            entity1.x += 1

class D20System:
    """D20 dice rolling system"""
    
    def __init__(self):
        self.rolls = []
        self.max_history = 100
    
    def roll(self, sides: int = 20, modifier: int = 0) -> int:
        """Roll a D20 with modifier"""
        roll = random.randint(1, sides) + modifier
        self.rolls.append(roll)
        
        # Keep history limited
        if len(self.rolls) > self.max_history:
            self.rolls.pop(0)
        
        return roll
    
    def check(self, dc: int, modifier: int = 0) -> tuple[bool, int]:
        """Perform a D20 check against DC"""
        roll = self.roll(20, modifier)
        success = roll >= dc
        return success, roll
    
    def get_stats(self) -> Dict[str, Any]:
        """Get D20 system statistics"""
        if not self.rolls:
            return {'total_rolls': 0, 'average': 0, 'critical_successes': 0, 'critical_failures': 0}
        
        return {
            'total_rolls': len(self.rolls),
            'average': sum(self.rolls) / len(self.rolls),
            'critical_successes': sum(1 for r in self.rolls if r == 20),
            'critical_failures': sum(1 for r in self.rolls if r == 1),
            'last_roll': self.rolls[-1] if self.rolls else 0
        }

class SimulationServer:
    """
    The "Mind" - Truth Provider
    
    Runs simulation independently and broadcasts state to UI clients.
    Implements ADR 123: Local-First Microservice Bridge
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.running = False
        self.frame_count = 0
        self.simulation_time = 0.0
        
        # Simulation components
        self.world = WorldGenerator(self.config.world_width, self.config.world_height)
        self.entity_system = EntitySystem(self.config.max_entities)
        self.physics_engine = PhysicsEngine() if self.config.enable_physics else None
        self.d20_system = D20System() if self.config.enable_d20 else None
        self.genetic_service = GeneticBreedingService() if self.config.enable_genetics else None
        self.racing_service = RacingService() if self.config.enable_racing else None
        
        # State management
        self.current_state = GameState()
        self.state_queue = Queue()  # For local clients
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.fps_history = []
        self.max_fps_history = 60
        
        # Threading
        self.simulation_thread: Optional[threading.Thread] = None
        
        logger.info("🧠 DGT Simulation Server initialized")
    
    def start(self) -> bool:
        """Start the simulation server"""
        if self.running:
            logger.warning("⚠️ Simulation server already running")
            return False
        
        self.running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        
        logger.info("🚀 Simulation server started")
        return True
    
    def stop(self):
        """Stop the simulation server"""
        if not self.running:
            return
        
        self.running = False
        
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
        
        logger.info("🛑 Simulation server stopped")
    
    def _simulation_loop(self):
        """Main simulation loop"""
        logger.info("🔄 Simulation loop started")
        
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Update simulation
            self._update_simulation(dt)
            
            # Broadcast state
            self._broadcast_state()
            
            # Frame rate limiting
            target_dt = 1.0 / self.config.target_fps
            sleep_time = max(0, target_dt - dt)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logger.info("🔄 Simulation loop ended")
    
    def _update_simulation(self, dt: float):
        """Update all simulation systems"""
        self.simulation_time += dt
        
        # Update entities
        self.entity_system.update_entities(dt)
        
        # Update physics
        if self.physics_engine:
            self.physics_engine.update(self.entity_system.entities, dt)
        
        # Update D20 system (random events)
        if self.d20_system and random.random() < 0.1:  # 10% chance per frame
            self._trigger_random_event()
        
        # Update genetic service (5-second generation cycles)
        if self.genetic_service:
            new_turtle_packets = self.genetic_service.update(dt)
            if new_turtle_packets:
                logger.info(f"🧬 {len(new_turtle_packets)} new turtles born")
                self._sync_turtles_to_entities(new_turtle_packets)
        
        # Update racing service (terrain-aware movement)
        if self.racing_service:
            race_state = self.racing_service.update_race(dt)
            if race_state:
                self._sync_race_to_entities(race_state)
        
        # Update frame count
        self.frame_count += 1
        
        # Update performance tracking
        self._update_performance_stats(dt)
    
    def _trigger_random_event(self):
        """Trigger random D20 events"""
        event_types = ['combat', 'skill_check', 'saving_throw', 'perception']
        event = random.choice(event_types)
        
        if event == 'combat':
            success, roll = self.d20_system.check(15)  # DC 15 combat check
            if success:
                logger.debug(f"⚔️ Combat success: {roll}")
            else:
                logger.debug(f"⚔️ Combat failure: {roll}")
        
        elif event == 'skill_check':
            success, roll = self.d20_system.check(12)  # DC 12 skill check
            skill = random.choice(['stealth', 'perception', 'athletics'])
            logger.debug(f"🎯 {skill.title()} check: {roll} - {'Success' if success else 'Failure'}")
        
        elif event == 'saving_throw':
            success, roll = self.d20_system.check(10)  # DC 10 saving throw
            logger.debug(f"🛡️ Saving throw: {roll} - {'Success' if success else 'Failure'}")
        
        elif event == 'perception':
            success, roll = self.d20_system.check(8)   # DC 8 perception check
            if success:
                logger.debug(f"👁️ Perception check: {roll} - Something noticed!")
    
    def _broadcast_state(self):
        """Broadcast current state to clients"""
        # Update current state
        self.current_state = self._create_state_snapshot()
        
        # Add to queue for local clients
        try:
            # Non-blocking put
            self.state_queue.put_nowait(self.current_state.to_dict())
        except:
            # Queue full, drop oldest
            try:
                self.state_queue.get_nowait()
                self.state_queue.put_nowait(self.current_state.to_dict())
            except:
                pass
        
        # Log state periodically
        if self.frame_count % 300 == 0:  # Every 5 seconds at 60 FPS
            logger.debug(f"📊 State broadcast: Frame {self.frame_count}, Entities {len(self.entity_system.entities)}")
    
    def _create_state_snapshot(self) -> GameState:
        """Create current state snapshot"""
        # Convert entities to state format
        state_entities = []
        for entity in self.entity_system.entities.values():
            state_entities.append(Entity(
                id=entity.id,
                x=entity.x,
                y=entity.y,
                entity_type=entity.entity_type,
                visible=entity.visible,
                metadata=entity.metadata.copy()
            ))
        
        # Create HUD data
        player = self.entity_system.get_entity("player")
        hud_data = {
            'line_1': f"Frame: {self.frame_count}",
            'line_2': f"Entities: {len(self.entity_system.entities)}",
            'line_3': f"Time: {self.simulation_time:.1f}s",
            'line_4': f"FPS: {self._get_current_fps():.1f}"
        }
        
        if player:
            hud_data.update({
                'line_1': f"HP: {player.metadata.get('health', 100)}",
                'line_2': f"Level: {player.metadata.get('level', 1)}",
                'line_3': f"Gold: {player.metadata.get('inventory', {}).get('gold', 0)}",
                'line_4': f"Pos: ({player.x}, {player.y})"
            })
        
        return GameState(
            width=160,
            height=144,
            entities=state_entities,
            background="world",
            hud=hud_data,
            timestamp=time.time(),
            frame_count=self.frame_count
        )
    
    def _sync_turtles_to_entities(self, turtle_packets: List[UniversalTurtlePacket]):
        """Sync genetic turtle data to entity system"""
        for packet in turtle_packets:
            # Check if turtle entity already exists
            if packet.turtle_id not in self.entity_system.entities:
                # Create new entity for turtle
                turtle_entity = Entity(
                    id=packet.turtle_id,
                    x=random.randint(5, 45),
                    y=random.randint(5, 45),
                    entity_type="genetic_turtle",
                    metadata={
                        'generation': packet.generation,
                        'shell_pattern': packet.shell_pattern,
                        'primary_color': packet.primary_color,
                        'secondary_color': packet.secondary_color,
                        'speed': packet.speed,
                        'stamina': packet.stamina,
                        'intelligence': packet.intelligence,
                        'fitness_score': packet.fitness_score,
                        'genome': packet.genome_serialized,
                        'birth_time': packet.birth_time,
                        'mutations': packet.mutations
                    }
                )
                self.entity_system.add_entity(turtle_entity)
            else:
                # Update existing turtle entity
                entity = self.entity_system.entities[packet.turtle_id]
                entity.metadata.update({
                    'generation': packet.generation,
                    'shell_pattern': packet.shell_pattern,
                    'primary_color': packet.primary_color,
                    'secondary_color': packet.secondary_color,
                    'speed': packet.speed,
                    'stamina': packet.stamina,
                    'intelligence': packet.intelligence,
                    'fitness_score': packet.fitness_score,
                    'genome': packet.genome_serialized,
                    'mutations': packet.mutations
                })
    
    def get_alpha_turtle_state(self) -> Optional[Dict[str, Any]]:
        """Get alpha turtle state for PPU visualization"""
        if not self.genetic_service:
            return None
        
        alpha_turtle = self.genetic_service.get_alpha_turtle()
        if not alpha_turtle:
            return None
        
        turtle_id, genome = alpha_turtle
        packet = self.genetic_service.create_turtle_packet(turtle_id)
        if not packet:
            return None
        
        return {
            'turtle_id': packet.turtle_id,
            'generation': packet.generation,
            'shell_pattern': packet.shell_pattern,
            'primary_color': packet.primary_color,
            'secondary_color': packet.secondary_color,
            'speed': packet.speed,
            'fitness_score': packet.fitness_score,
            'timestamp': packet.timestamp
        }
    
    def get_genetic_stats(self) -> Dict[str, Any]:
        """Get genetic breeding service statistics"""
        if not self.genetic_service:
            return {}
        
        return self.genetic_service.get_population_stats()
    
    def _sync_race_to_entities(self, race_state: Dict[str, Any]):
        """Sync racing state to entity system"""
        for turtle_id, racer_data in race_state.get('racers', {}).items():
            # Check if racer entity exists
            if turtle_id in self.entity_system.entities:
                entity = self.entity_system.entities[turtle_id]
                
                # Update position
                entity.x = int(racer_data['x'])
                entity.y = int(racer_data['y'])
                
                # Update racing metadata
                entity.metadata.update({
                    'race_position': racer_data['position'],
                    'race_speed': racer_data['speed'],
                    'race_stamina': racer_data['stamina'],
                    'race_checkpoint': racer_data['current_checkpoint'],
                    'race_distance': racer_data['distance'],
                    'race_finished': racer_data['finished']
                })
    
    def start_race(self, participants: List[str]) -> bool:
        """Start a race with specified participants"""
        if not self.racing_service:
            logger.warning("🏁 Racing service not enabled")
            return False
        
        # Register participants
        for turtle_id in participants:
            if turtle_id in self.entity_system.entities:
                entity = self.entity_system.entities[turtle_id]
                
                # Create genome from entity metadata or use default
                genome_data = entity.metadata.get('genome_data', {})
                if genome_data:
                    genome = TurboGenome(**genome_data)
                else:
                    # Create default genome
                    genome = TurboGenome(
                        turtle_id=turtle_id,
                        generation=entity.metadata.get('generation', 0)
                    )
                
                # Register with racing service
                self.racing_service.register_racer(turtle_id, genome)
        
        # Start the race
        return self.racing_service.start_race()
    
    def get_race_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get current race leaderboard"""
        if not self.racing_service:
            return []
        
        return self.racing_service.get_leaderboard(limit)
    
    def save_race_log(self, filename: Optional[str] = None):
        """Save race results to log"""
        if self.racing_service:
            self.racing_service.save_race_log(filename)
    
    def _update_performance_stats(self, dt: float):
        """Update performance statistics"""
        self.fps_history.append(dt)
        if len(self.fps_history) > self.max_fps_history:
            self.fps_history.pop(0)
    
    def _get_current_fps(self) -> float:
        """Get current FPS"""
        if self.fps_history:
            avg_dt = sum(self.fps_history) / len(self.fps_history)
            return 1.0 / avg_dt if avg_dt > 0 else 0
        return 0
    
    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get latest state for clients"""
        try:
            # Non-blocking get
            return self.state_queue.get_nowait()
        except Empty:
            # No new state available
            return self.current_state.to_dict()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get server performance statistics"""
        return {
            'server_type': 'simulation_server',
            'running': self.running,
            'frame_count': self.frame_count,
            'simulation_time': self.simulation_time,
            'current_fps': self._get_current_fps(),
            'target_fps': self.config.target_fps,
            'entities_count': len(self.entity_system.entities),
            'world_size': f"{self.config.world_width}x{self.config.world_height}",
            'physics_enabled': self.config.enable_physics,
            'genetics_enabled': self.config.enable_genetics,
            'd20_enabled': self.config.enable_d20,
            'queue_size': self.state_queue.qsize()
        }
    
    def cleanup(self):
        """Cleanup server resources"""
        self.stop()
        self.state_queue = None
        logger.info("🧹 Simulation server cleaned up")

# Factory function
def create_simulation_server(config: Optional[SimulationConfig] = None) -> SimulationServer:
    """Create simulation server with default configuration"""
    return SimulationServer(config)

# Standalone server runner
def run_standalone_server():
    """Run simulation server in standalone mode"""
    import signal
    import sys
    
    config = SimulationConfig(
        target_fps=60,
        max_entities=50,
        enable_physics=True,
        enable_genetics=True,
        enable_d20=True,
        log_to_file=True
    )
    
    server = create_simulation_server(config)
    
    def signal_handler(sig, frame):
        print("\n🛑 Stopping simulation server...")
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🧠 DGT Simulation Server - Standalone Mode")
    print("=" * 50)
    print("Running simulation independently...")
    print("Press Ctrl+C to stop")
    print()
    
    server.start()
    
    try:
        # Keep server running
        while server.running:
            time.sleep(1)
            
            # Print stats every 10 seconds
            if server.frame_count % 600 == 0:
                stats = server.get_performance_stats()
                print(f"📊 Server Stats: FPS: {stats['current_fps']:.1f}, Entities: {stats['entities_count']}, Frame: {stats['frame_count']}")
    
    except KeyboardInterrupt:
        pass
    finally:
        server.cleanup()
        print("✅ Simulation server stopped")

if __name__ == "__main__":
    run_standalone_server()
