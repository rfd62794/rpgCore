"""
Main Heartbeat - Autonomous Movie System

The central nervous system connecting the four pillars:
World Engine (World) -> D&D Engine (Mind) -> Voyager (Actor) -> Graphics Engine (Body)

Autonomous D&D Movie with 60 FPS rendering, persistent world, and LLM-generated subtitles.
"""

import time
import sys
import json
from typing import Union, Optional
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from loguru import logger

# Import the four pillars
from engines.dd_engine import DD_Engine, MovementIntent, InteractionIntent
from engines.world_engine import WorldEngineFactory
from actors.voyager import Voyager
from graphics.ppu import GraphicsEngine
from chronicler import ChroniclerFactory


class MainHeartbeat:
    """Central coordination for Autonomous Movie System"""
    
    def __init__(self, assets_path: str = "assets/"):
        """Initialize the four pillars for autonomous movie"""
        logger.info("� Initializing Main Heartbeat - Autonomous Movie System")
        
        # Initialize The World (World Engine)
        self.world_engine = WorldEngineFactory.create_tavern_world()
        logger.info("🌍 The World (World Engine) - Deterministic data provider ready")
        
        # Initialize The Mind (D&D Engine)
        self.dd_engine = DD_Engine(assets_path, self.world_engine)
        logger.info("🧠 The Mind (D&D Engine) - Single Source of Truth ready")
        
        # Initialize The Actor (Voyager)
        self.voyager = Voyager(self.dd_engine)
        logger.info("🚶 The Actor (Voyager) - Pathfinding and Intent Generation ready")
        
        # Initialize The Body (Graphics Engine)
        self.graphics = GraphicsEngine(assets_path)
        logger.info("🎨 The Body (Graphics Engine) - 160x144 PPU Rendering ready")
        
        # Initialize The Chronicler (LLM Subtitles)
        self.chronicler = ChroniclerFactory.create_movie_chronicler()
        logger.info("📝 The Chronicler (LLM Subtitles) - Movie dialogue generator ready")
        
        # Heartbeat state
        self.running = True
        self.frame_count = 0
        self.start_time = time.time()
        self.target_fps = 60
        self.frame_delay = 1.0 / self.target_fps
        
        # Movie script (beacons for autonomous navigation)
        self.movie_script = [
            (10, 25),  # Forest edge
            (10, 20),  # Town gate
            (10, 10),  # Town square
            (20, 10),  # Tavern entrance
            (25, 30),  # Tavern interior
        ]
        self.current_script_index = 0
        
        # Persistence state
        self.persistence_interval = 10  # Save every 10 turns
        self.last_persistence_turn = 0
        
        # Previous state for change detection
        self.previous_state = None
        
        logger.info("🎬 Main Heartbeat initialized - Autonomous Movie System ready")
    
    def run(self) -> None:
        """Main autonomous movie loop - 60 FPS heartbeat"""
        logger.info("� Starting Autonomous Movie - 60 FPS Heartbeat")
        
        # Add movie intro subtitle
        self.chronicler.add_subtitle("Our story begins in the realm of adventure.", 4.0)
        
        last_frame_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # 1. Generate intent from movie script
            intent = self._get_next_scripted_intent()
            
            if intent:
                # 2. Submit intent to D&D Engine via Voyager
                success = self.voyager.submit_intent(intent)
                
                if success:
                    logger.debug(f"✅ Intent executed: {intent.intent_type}")
                    
                    # 3. Get current state from D&D Engine (Single Source of Truth)
                    current_state = self.dd_engine.get_current_state()
                    
                    # 4. Generate subtitle for state change
                    if self.previous_state:
                        subtitle = self.chronicler.observe_state_change(
                            self.previous_state, 
                            self._state_to_dict(current_state)
                        )
                        if subtitle:
                            logger.info(f"📝 Subtitle: {subtitle}")
                    
                    self.previous_state = self._state_to_dict(current_state)
                    
                    # 5. Check for persistence
                    self._check_persistence(current_state)
                    
                    # 6. Render frame via Graphics Engine
                    frame = self.graphics.render_state(current_state)
                    self.graphics.display_frame(frame)
                    
                    # 7. Update Voyager position from state
                    self.voyager.update_position(current_state.player_position)
                else:
                    logger.warning(f"❌ Intent failed: {intent.intent_type}")
            
            # 8. Heartbeat bookkeeping
            self.frame_count += 1
            last_frame_time = current_time
            
            # 9. Frame rate limiting (60 FPS)
            elapsed = time.time() - current_time
            if elapsed < self.frame_delay:
                time.sleep(self.frame_delay - elapsed)
            
            # 10. Check for movie completion
            if self._is_movie_complete():
                logger.info("🏁 Movie complete - adding outro subtitle")
                self.chronicler.add_subtitle("And so the tale continues...", 4.0)
                time.sleep(4.0)  # Let outro subtitle display
                self.running = False
        
        # Final summary
        self._print_movie_summary()
    
    def _get_next_scripted_intent(self) -> Optional[Union[MovementIntent, InteractionIntent]]:
        """Generate intent from movie script (autonomous navigation)"""
        current_state = self.dd_engine.get_current_state()
        current_pos = current_state.player_position
        
        # Check if we've reached current script position
        if self.current_script_index < len(self.movie_script):
            target_position = self.movie_script[self.current_script_index]
            
            # Check if close enough to target (within 1 tile)
            distance = abs(current_pos[0] - target_position[0]) + abs(current_pos[1] - target_position[1])
            
            if distance <= 1:
                # Reached target, move to next script position
                logger.info(f"🎯 Script position reached: {target_position}")
                self.current_script_index += 1
                
                # Generate interaction intent if this is a special location
                if self.current_script_index <= len(self.movie_script):
                    return self._generate_interaction_intent(target_position)
                
                return None
            
            # Generate movement intent toward current script position
            try:
                return self.voyager.generate_movement_intent(target_position)
            except Exception as e:
                logger.error(f"💥 Failed to generate movement intent: {e}")
                return None
        
        return None
    
    def _generate_interaction_intent(self, position: Tuple[int, int]) -> Optional[InteractionIntent]:
        """Generate interaction intent for special movie locations"""
        # Define interactions for specific positions
        interactions = {
            (10, 25): "forest_gate",
            (10, 20): "town_gate", 
            (20, 10): "tavern_entrance",
            (25, 30): "tavern_complete"
        }
        
        interaction_type = interactions.get(position)
        if interaction_type:
            return self.voyager.generate_interaction_intent(
                f"location_{position[0]}_{position[1]}",
                interaction_type
            )
        
        return None
    
    def _is_movie_complete(self) -> bool:
        """Check if movie script is complete"""
        return self.current_script_index >= len(self.movie_script)
    
    def _state_to_dict(self, state) -> Dict[str, Any]:
        """Convert GameState to dictionary for Chronicler"""
        return {
            "player_position": state.player_position,
            "turn_count": state.turn_count,
            "current_environment": state.current_environment,
            "player_health": state.player_health,
            "world_deltas": state.world_deltas
        }
    
    def _check_persistence(self, current_state) -> None:
        """Check if world state should be persisted"""
        if current_state.turn_count > self.last_persistence_turn + self.persistence_interval:
            self._persist_world_state(current_state)
            self.last_persistence_turn = current_state.turn_count
    
    def _persist_world_state(self, current_state) -> None:
        """Persist world state to file"""
        persistence_data = {
            "timestamp": time.time(),
            "turn_count": current_state.turn_count,
            "player_position": current_state.player_position,
            "world_deltas": current_state.world_deltas,
            "world_engine_seed": self.world_engine.seed_zero
        }
        
        try:
            with open("persistence.json", "w") as f:
                json.dump(persistence_data, f, indent=2)
            logger.info(f"💾 World state persisted at turn {current_state.turn_count}")
        except Exception as e:
            logger.error(f"❌ Failed to persist world state: {e}")
    
    def _print_movie_summary(self) -> None:
        """Print movie performance summary"""
        total_time = time.time() - self.start_time
        avg_fps = self.frame_count / total_time if total_time > 0 else 0
        
        logger.info("🎬 ============== MOVIE SUMMARY ================")
        logger.info(f"� Total Frames: {self.frame_count}")
        logger.info(f"⏱️ Total Time: {total_time:.2f}s")
        logger.info(f"🎯 Average FPS: {avg_fps:.1f}")
        logger.info(f"� Target FPS: {self.target_fps}")
        
        # Get final states
        final_state = self.dd_engine.get_current_state()
        voyager_status = self.voyager.get_status()
        graphics_status = self.graphics.get_status()
        chronicler_stats = self.chronicler.get_statistics()
        
        logger.info(f"🧠 D&D Engine: Turn {final_state.turn_count}, Position {final_state.player_position}")
        logger.info(f"🚶 Voyager: Health {voyager_status['health']}, Environment {voyager_status['environment']}")
        logger.info(f"🎨 Graphics: {graphics_status['ppu_resolution']}, Tile Bank {graphics_status['current_tile_bank']}")
        logger.info(f"📝 Chronicler: {chronicler_stats['total_subtitles']} subtitles generated")
        logger.info(f"💾 World Deltas: {len(final_state.world_deltas)} persistent changes")
        
        # Show current subtitles
        current_subtitles = self.chronicler.get_current_subtitles()
        if current_subtitles:
            logger.info(f"📝 Current Subtitle: {current_subtitles[0]}")
        
        logger.info("=" * 50)
    
    def stop(self) -> None:
        """Stop the heartbeat"""
        self.running = False
        logger.info("🛑 Main Heartbeat stopped")


def main():
    """Main entry point for Autonomous Movie System"""
    logger.info("� D&D Engine - Autonomous Movie System")
    logger.info("🌍 The World (World Engine) - Deterministic data provider")
    logger.info("🧠 The Mind (D&D Engine) - Single Source of Truth")
    logger.info("🚶 The Actor (Voyager) - Pathfinding and Intent Generation")
    logger.info("🎨 The Body (Graphics Engine) - 160x144 PPU Rendering")
    logger.info("📝 The Chronicler (LLM Subtitles) - Movie dialogue generator")
    logger.info("=" * 70)
    
    try:
        # Create and run autonomous movie
        heartbeat = MainHeartbeat()
        heartbeat.run()
        
        logger.info("🎉 Autonomous Movie completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️ Movie interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"💥 Movie crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_autonomous_movie():
    """The 'Big Red Button' - Launch complete autonomous movie"""
    print("🎬 Launching Autonomous D&D Movie...")
    print("🌍 World Engine: Generating deterministic world...")
    print("🧠 D&D Engine: Preparing logic and rules...")
    print("🚶 Voyager: Setting pathfinding and navigation...")
    print("🎨 Graphics Engine: Initializing 160x144 PPU...")
    print("📝 Chronicler: Preparing subtitle generator...")
    print("🎬 Starting autonomous movie - 60 FPS rendering...")
    
    # Create the four pillars
    world = WorldEngineFactory.create_tavern_world()
    mind = DD_Engine("assets/", world)
    actor = Voyager(mind)
    body = GraphicsEngine("assets/")
    chronicler = ChroniclerFactory.create_movie_chronicler()
    
    # Create heartbeat and run
    heartbeat = MainHeartbeat()
    heartbeat.run()
    
    print("🎬 Movie complete! Check persistence.json for saved world state.")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
