"""
Main Heartbeat - Central Coordination Between Three Pillars

The Mind (D&D Engine) - Single Source of Truth
The Actor (Voyager) - Pathfinding and Intent Generation  
The Body (Graphics Engine) - 160x144 PPU Rendering

KISS Architecture: Clean interfaces, no drift, deterministic execution.
"""

import time
import sys
from typing import Union, Optional
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from loguru import logger

# Import the three pillars
from engines.dd_engine import DD_Engine, MovementIntent, InteractionIntent
from actors.voyager import Voyager
from graphics.ppu import GraphicsEngine


class MainHeartbeat:
    """Central coordination between three pillars"""
    
    def __init__(self, assets_path: str = "assets/"):
        """Initialize the three pillars"""
        logger.info("🏗️ Initializing Main Heartbeat - Three Pillar Architecture")
        
        # Initialize The Mind (D&D Engine)
        self.dd_engine = DD_Engine(assets_path)
        logger.info("🧠 The Mind (D&D Engine) - Single Source of Truth ready")
        
        # Initialize The Actor (Voyager)
        self.voyager = Voyager(self.dd_engine)
        logger.info("🚶 The Actor (Voyager) - Pathfinding and Intent Generation ready")
        
        # Initialize The Body (Graphics Engine)
        self.graphics = GraphicsEngine(assets_path)
        logger.info("🎨 The Body (Graphics Engine) - 160x144 PPU Rendering ready")
        
        # Heartbeat state
        self.running = True
        self.frame_count = 0
        self.start_time = time.time()
        self.target_fps = 60
        self.frame_delay = 1.0 / self.target_fps
        
        # Demo navigation goals
        self.demo_goals = [
            (10, 25),  # Forest edge
            (10, 20),  # Town gate
            (10, 10),  # Town square
            (20, 10),  # Tavern entrance
            (25, 30),  # Tavern interior
        ]
        self.current_goal_index = 0
        
        logger.info("💗 Main Heartbeat initialized - Three Pillars ready")
    
    def run(self) -> None:
        """Main game loop - Heartbeat between pillars"""
        logger.info("🎮 Starting Main Heartbeat loop")
        
        last_frame_time = time.time()
        
        while self.running:
            current_time = time.time()
            delta_time = current_time - last_frame_time
            
            # 1. Generate intent (Demo: scripted navigation)
            intent = self._generate_demo_intent()
            
            if intent:
                # 2. Submit intent to D&D Engine via Voyager
                success = self.voyager.submit_intent(intent)
                
                if success:
                    logger.debug(f"✅ Intent executed: {intent.intent_type}")
                else:
                    logger.warning(f"❌ Intent failed: {intent.intent_type}")
            
            # 3. Get current state from D&D Engine (Single Source of Truth)
            current_state = self.dd_engine.get_current_state()
            
            # 4. Render frame via Graphics Engine
            frame = self.graphics.render_state(current_state)
            self.graphics.display_frame(frame)
            
            # 5. Update Voyager position from state
            self.voyager.update_position(current_state.player_position)
            
            # 6. Heartbeat bookkeeping
            self.frame_count += 1
            last_frame_time = current_time
            
            # 7. Frame rate limiting
            elapsed = time.time() - current_time
            if elapsed < self.frame_delay:
                time.sleep(self.frame_delay - elapsed)
            
            # 8. Check for completion
            if self._is_demo_complete():
                logger.info("🏁 Demo complete - stopping heartbeat")
                self.running = False
        
        # Final summary
        self._print_performance_summary()
    
    def _generate_demo_intent(self) -> Optional[Union[MovementIntent, InteractionIntent]]:
        """Generate demo intent (scripted navigation)"""
        current_state = self.dd_engine.get_current_state()
        current_pos = current_state.player_position
        
        # Check if we've reached current goal
        if self.current_goal_index < len(self.demo_goals):
            target_goal = self.demo_goals[self.current_goal_index]
            
            # Check if close enough to goal (within 1 tile)
            distance = abs(current_pos[0] - target_goal[0]) + abs(current_pos[1] - target_goal[1])
            
            if distance <= 1:
                # Reached goal, move to next
                logger.info(f"🎯 Goal reached: {target_goal}")
                self.current_goal_index += 1
                
                # Generate interaction intent if this is a special location
                if self.current_goal_index <= len(self.demo_goals):
                    return self._generate_interaction_intent(target_goal)
                
                return None
            
            # Generate movement intent toward current goal
            try:
                return self.voyager.generate_movement_intent(target_goal)
            except Exception as e:
                logger.error(f"💥 Failed to generate movement intent: {e}")
                return None
        
        return None
    
    def _generate_interaction_intent(self, position: Tuple[int, int]) -> Optional[InteractionIntent]:
        """Generate interaction intent for special locations"""
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
    
    def _is_demo_complete(self) -> bool:
        """Check if demo navigation is complete"""
        return self.current_goal_index >= len(self.demo_goals)
    
    def _print_performance_summary(self) -> None:
        """Print performance summary"""
        total_time = time.time() - self.start_time
        avg_fps = self.frame_count / total_time if total_time > 0 else 0
        
        logger.info("📊 ============== PERFORMANCE SUMMARY ================")
        logger.info(f"🎮 Total Frames: {self.frame_count}")
        logger.info(f"⏱️ Total Time: {total_time:.2f}s")
        logger.info(f"🎯 Average FPS: {avg_fps:.1f}")
        logger.info(f"🏆 Target FPS: {self.target_fps}")
        
        # Get final states
        final_dd_state = self.dd_engine.get_current_state()
        voyager_status = self.voyager.get_status()
        graphics_status = self.graphics.get_status()
        
        logger.info(f"🧠 D&D Engine: Turn {final_dd_state.turn_count}, Position {final_dd_state.player_position}")
        logger.info(f"🚶 Voyager: Health {voyager_status['health']}, Environment {voyager_status['environment']}")
        logger.info(f"🎨 Graphics: {graphics_status['ppu_resolution']}, Tile Bank {graphics_status['current_tile_bank']}")
        logger.info("=" * 50)
    
    def stop(self) -> None:
        """Stop the heartbeat"""
        self.running = False
        logger.info("🛑 Main Heartbeat stopped")


def main():
    """Main entry point"""
    logger.info("🎮 D&D Engine - Three Pillar Architecture")
    logger.info("🧠 The Mind (D&D Engine) - Single Source of Truth")
    logger.info("🚶 The Actor (Voyager) - Pathfinding and Intent Generation")
    logger.info("🎨 The Body (Graphics Engine) - 160x144 PPU Rendering")
    logger.info("=" * 60)
    
    try:
        # Create and run heartbeat
        heartbeat = MainHeartbeat()
        heartbeat.run()
        
        logger.info("🎉 Main Heartbeat completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️ Heartbeat interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"💥 Heartbeat crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
