"""
Main Heartbeat Controller - The DGT Autonomous Movie System

Production-ready Service-Oriented Architecture implementation.
The Heartbeat coordinates all pillars and services at 60 FPS.

Key Features:
- SOA architecture with clean pillar separation
- Autonomous movie mode with configurable scenes
- 60 FPS asynchronous heartbeat loop
- Deterministic Chaos Protocol integration
- Production-grade error handling and monitoring
"""

import asyncio
import argparse
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger

# Import core components
try:
    from core import (
        HeartbeatController, get_heartbeat, initialize_heartbeat,
        get_environment, is_development, is_production
    )
except ImportError:
    # Fallback for development
    sys.path.append(str(Path(__file__).parent))
    from core import (
        HeartbeatController, get_heartbeat, initialize_heartbeat,
        get_environment, is_development, is_production
    )

# Import pillar engines
try:
    from engines import (
        WorldEngine, WorldEngineFactory,
        DDEngine, DDEngineFactory,
        GraphicsEngine, GraphicsEngineFactory
    )
except ImportError:
    # Fallback for development
    from engines.world import WorldEngine, WorldEngineFactory
    from engines.mind import DDEngine, DDEngineFactory
    from engines.body import GraphicsEngine, GraphicsEngineFactory

# Import narrative engines
try:
    from narrative import (
        ChronosEngine, ChronosEngineFactory,
        PersonaEngine, PersonaEngineFactory
    )
except ImportError:
    # Fallback for development
    from narrative.chronos import ChronosEngine, ChronosEngineFactory
    from narrative.persona import PersonaEngine, PersonaEngineFactory

# Import actor
try:
    from actors import Voyager, VoyagerFactory
except ImportError:
    # Fallback for development
    from actors.voyager import Voyager, VoyagerFactory

# Import utilities
try:
    from utils import initialize_logging, get_logger_manager
except ImportError:
    # Fallback for development
    from utils.logger import initialize_logging, get_logger_manager

# Import developer console
try:
    from tools import DeveloperConsole
except ImportError:
    # Fallback for development
    from tools.developer_console import DeveloperConsole


class DGTSystem:
    """Main DGT Autonomous Movie System"""
    
    def __init__(self):
        self.heartbeat: Optional[HeartbeatController] = None
        self.running = False
        
        # Pillar instances
        self.world_engine: Optional[WorldEngine] = None
        self.dd_engine: Optional[DDEngine] = None
        self.graphics_engine: Optional[GraphicsEngine] = None
        self.voyager: Optional[Voyager] = None
        
        # Narrative pillars
        self.chronos_engine: Optional[ChronosEngine] = None
        self.persona_engine: Optional[PersonaEngine] = None
        
        # Developer tools
        self.dev_console: Optional[DeveloperConsole] = None
        
        # Configuration
        self.config = self._load_config()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        logger.info("🏰 DGT System initialized - Production SOA Architecture")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load system configuration"""
        return {
            "mode": "autonomous",
            "scene": "tavern",
            "seed": "TAVERN_SEED",
            "target_fps": 60,
            "enable_graphics": True,
            "enable_persistence": True,
            "enable_logging": True
        }
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize all system components"""
        try:
            logger.info("🚀 Initializing DGT System components...")
            
            # Initialize logging
            if config.get("enable_logging", True):
                try:
                    initialize_logging()
                except NameError:
                    # Fallback if logging utilities not available
                    logger.info("📝 Using fallback logging")
            
            # Initialize World Engine with scene-specific seed
            seed = config.get("seed", "TAVERN_SEED")
            self.world_engine = WorldEngineFactory.create_world(seed)
            logger.info(f"🌍 World Engine initialized with seed: {seed}")
            
            # Initialize D&D Engine (Mind Pillar)
            self.dd_engine = DDEngineFactory.create_engine()
            self.dd_engine.set_world_engine(self.world_engine)
            logger.info("🧠 D&D Engine initialized")
            
            # Initialize Graphics Engine (Body Pillar)
            if config.get("enable_graphics", False):
                self.graphics_engine = GraphicsEngineFactory.create_engine("assets/")
                logger.info("🎨 Graphics Engine initialized")
            
            # Initialize Chronos Engine (Quest & Progression Pillar)
            self.chronos_engine = ChronosEngineFactory.create_engine()
            self.chronos_engine.initialize_main_quest([
                (10, 25), (10, 20), (10, 10), (20, 10), (25, 30), (32, 32)
            ])
            logger.info("⏳ Chronos Engine initialized")
            
            # Initialize Persona Engine (Social Soul Pillar)
            self.persona_engine = PersonaEngineFactory.create_engine(seed)
            self.persona_engine.seed_tavern_personas()
            logger.info("👥 Persona Engine initialized")
            
            # Initialize Voyager (Actor Pillar)
            self.voyager = VoyagerFactory.create_voyager(self.dd_engine, self.chronos_engine)
            logger.info("🚶 Voyager initialized")
            
            # Connect pillars with dependency injection
            self.world_engine.set_chronos_engine(self.chronos_engine)
            self.chronos_engine.set_persona_engine(self.persona_engine)
            logger.info("🔗 Pillar dependencies connected")
            
            # Initialize Developer Console
            if config.get("enable_console", True):
                self.dev_console = DeveloperConsole(self)
                await self.dev_console.start()
                logger.info("🖥️ Developer Console started")
            
            # Initialize Heartbeat Controller
            try:
                self.heartbeat = await initialize_heartbeat()
            except Exception as e:
                logger.warning(f"⚠️ Heartbeat initialization failed: {e}")
                # Create a simple fallback heartbeat
                self.heartbeat = None
            
            # Register all services with heartbeat
            await self._register_services()
            
            # Set scene-specific configuration
            await self._configure_scene(config.get("scene", "tavern"))
            
            logger.info("✅ DGT System initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"💥 System initialization failed: {e}")
            return False
    
    async def _register_services(self) -> None:
        """Register all services with heartbeat controller"""
        if not self.heartbeat:
            logger.debug("⚠️ No heartbeat available for service registration")
            return
        
        # Register all services with heartbeat
        self.heartbeat.register_services(
            world_engine=self.world_engine,
            dd_engine=self.dd_engine,
            voyager=self.voyager,
            graphics_engine=self.graphics_engine,
            chronos_engine=self.chronos_engine,
            persona_engine=self.persona_engine,
            chronicler=None,  # Not implemented yet
            persistence_manager=None  # Not implemented yet
        )
        
        logger.debug("📋 All services registered with heartbeat")
    
    async def _configure_scene(self, scene: str) -> None:
        """Configure scene-specific settings"""
        if scene == "tavern":
            await self._configure_tavern_scene()
        elif scene == "forest":
            await self._configure_forest_scene()
        else:
            logger.warning(f"Unknown scene: {scene}")
    
    async def _configure_tavern_scene(self) -> None:
        """Configure tavern scene with autonomous navigation"""
        if not self.voyager:
            return
        
        # Set tavern-specific movie script
        tavern_script = [
            (10, 25),  # Forest edge
            (10, 20),  # Town gate  
            (10, 10),  # Town square
            (20, 10),  # Tavern entrance
            (25, 30),  # Tavern interior
            (32, 32),  # Iron Chest (target)
        ]
        
        # Update Voyager's movie script
        self.voyager.movie_script = tavern_script
        self.voyager.current_script_index = 0
        
        # Set initial position
        self.voyager.current_position = (10, 25)
        
        logger.info("🍺 Tavern scene configured - Iron Chest at (32, 32)")
    
    async def _configure_forest_scene(self) -> None:
        """Configure forest scene"""
        if not self.voyager:
            return
        
        # Set forest-specific navigation
        forest_script = [
            (10, 25),  # Starting position
            (15, 30),  # Forest clearing
            (20, 35),  # Ancient tree
            (25, 25),  # Hidden path
        ]
        
        self.voyager.movie_script = forest_script
        self.voyager.current_script_index = 0
        
        self.voyager.current_position = (10, 25)
        
        logger.info("🌲 Forest scene configured")
    
    async def run_autonomous_mode(self) -> None:
        """Run autonomous movie mode"""
        logger.info("🎬 Starting autonomous movie mode...")
        self.running = True
        
        try:
            if self.heartbeat:
                # Start the heartbeat loop
                await self.heartbeat.start()
                # Wait for heartbeat to complete
                if self.heartbeat.loop_task:
                    await self.heartbeat.loop_task
            else:
                # Fallback simple loop
                await self._run_simple_autonomous_loop()
            
        except KeyboardInterrupt:
            logger.info("🛑 Autonomous mode interrupted")
        except Exception as e:
            logger.error(f"💥 Autonomous mode error: {e}")
        finally:
            self.running = False
            logger.info("🎬 Autonomous mode ended")
    
    async def _run_simple_autonomous_loop(self) -> None:
        """Simple autonomous loop fallback"""
        logger.info("🔄 Running simple autonomous loop")
        
        while self.running:
            try:
                # Get current state
                if self.dd_engine:
                    state = self.dd_engine.get_current_state()
                    logger.info(f"📍 Position: {state.player_position}, Turn: {state.turn_count}")
                
                # Generate next intent
                if self.voyager:
                    intent = await self.voyager.generate_next_intent(state)
                    if intent:
                        success = await self.voyager.submit_intent(intent)
                        logger.info(f"🎯 Intent: {intent.intent_type}, Success: {success}")
                
                # Wait for next frame
                await asyncio.sleep(1/60)  # 60 FPS
                
            except Exception as e:
                logger.error(f"💥 Loop error: {e}")
                await asyncio.sleep(1)
    
    async def run_interactive_mode(self) -> None:
        """Run interactive mode (for development)"""
        logger.info("🎮 Starting interactive mode...")
        
        # Interactive loop for testing
        while True:
            try:
                # Get current state
                if self.dd_engine:
                    state = self.dd_engine.get_current_state()
                    logger.info(f"📍 Position: {state.player_position}, Turn: {state.turn_count}")
                
                # Wait for user input
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                break
        
        logger.info("🎮 Interactive mode ended")
    
    async def run_demo_mode(self) -> None:
        """Run demo mode with predefined scenarios"""
        logger.info("🎭 Starting demo mode...")
        
        # Demo scenarios
        scenarios = [
            "tavern_chest_opening",
            "forest_exploration", 
            "town_navigation"
        ]
        
        for scenario in scenarios:
            logger.info(f"🎬 Running scenario: {scenario}")
            await self._run_scenario(scenario)
            await asyncio.sleep(2)  # Pause between scenarios
        
        logger.info("🎭 Demo mode completed")
    
    async def _run_scenario(self, scenario: str) -> None:
        """Run a specific demo scenario"""
        if scenario == "tavern_chest_opening":
            await self._run_tavern_chest_scenario()
        elif scenario == "forest_exploration":
            await self._run_forest_scenario()
        elif scenario == "town_navigation":
            await self._run_town_scenario()
    
    async def _run_tavern_chest_scenario(self) -> None:
        """Run tavern chest opening scenario"""
        if not self.voyager:
            return
        
        # Navigate to tavern
        logger.info("🍺 Navigating to tavern...")
        await self.voyager.navigate_to_position((25, 30))
        
        # Navigate to chest
        logger.info("📦 Navigating to iron chest...")
        await self.voyager.navigate_to_position((32, 32))
        
        # Interact with chest
        logger.info("🔓 Opening iron chest...")
        await self.voyager.interact_with_entity("iron_chest", "open")
    
    async def _run_forest_scenario(self) -> None:
        """Run forest exploration scenario"""
        if not self.voyager:
            return
        
        # Explore forest locations
        locations = [(15, 30), (20, 35), (25, 25), (30, 20)]
        
        for location in locations:
            logger.info(f"🌲 Exploring location: {location}")
            await self.voyager.navigate_to_position(location)
            await asyncio.sleep(1)
    
    async def _run_town_scenario(self) -> None:
        """Run town navigation scenario"""
        if not self.voyager:
            return
        
        # Navigate town landmarks
        landmarks = [
            ((10, 10), "town_square"),
            ((15, 15), "market"),
            ((20, 10), "tavern_entrance"),
            ((10, 20), "town_gate")
        ]
        
        for position, name in landmarks:
            logger.info(f"🏘️ Visiting: {name}")
            await self.voyager.navigate_to_position(position)
            await asyncio.sleep(1)
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("🛑 Shutting down DGT System...")
        
        self.running = False
        
        # Stop Developer Console
        if self.dev_console:
            self.dev_console.stop()
        
        if self.heartbeat:
            await self.heartbeat.stop()
        
        logger.info("✅ DGT System shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "running": self.running,
            "heartbeat_active": self.heartbeat.is_running() if self.heartbeat else False,
            "pillars": {
                "world_engine": self.world_engine is not None,
                "dd_engine": self.dd_engine is not None,
                "graphics_engine": self.graphics_engine is not None,
                "voyager": self.voyager is not None,
                "chronos_engine": self.chronos_engine is not None,
                "persona_engine": self.persona_engine is not None
            },
            "config": self.config
        }


# === MAIN ENTRY POINTS ===

async def run_tavern_autopilot():
    """Run autonomous tavern movie mode"""
    logger.info("🍺 Starting Tavern Autopilot Mode...")
    
    # Create system
    system = DGTSystem()
    
    # Configure for tavern
    config = {
        "mode": "autonomous",
        "scene": "tavern",
        "seed": "TAVERN_SEED",
        "target_fps": 60,
        "enable_graphics": False,
        "enable_persistence": True,
        "enable_logging": True
    }
    
    # Initialize and run
    if await system.initialize(config):
        await system.run_autonomous_mode()
    else:
        logger.error("💥 Failed to initialize system")
        return 1
    
    return 0


async def run_forest_autopilot():
    """Run autonomous forest exploration mode"""
    logger.info("🌲 Starting Forest Autopilot Mode...")
    
    # Create system
    system = DGTSystem()
    
    # Configure for forest
    config = {
        "mode": "autonomous",
        "scene": "forest",
        "seed": "FOREST_SEED",
        "target_fps": 60,
        "enable_graphics": True,
        "enable_persistence": True,
        "enable_logging": True
    }
    
    # Initialize and run
    if await system.initialize(config):
        await system.run_autonomous_mode()
    else:
        logger.error("💥 Failed to initialize system")
        return 1
    
    return 0


async def run_demo():
    """Run demo mode with all scenarios"""
    logger.info("🎭 Starting Demo Mode...")
    
    # Create system
    system = DGTSystem()
    
    # Configure for demo
    config = {
        "mode": "demo",
        "scene": "demo",
        "seed": "DEMO_SEED",
        "target_fps": 60,
        "enable_graphics": True,
        "enable_persistence": False,
        "enable_logging": True
    }
    
    # Initialize and run
    if await system.initialize(config):
        await system.run_demo_mode()
    else:
        logger.error("💥 Failed to initialize system")
        return 1
    
    return 0


async def run_interactive():
    """Run interactive mode for development"""
    logger.info("🎮 Starting Interactive Mode...")
    
    # Create system
    system = DGTSystem()
    
    # Configure for interactive
    config = {
        "mode": "interactive",
        "scene": "tavern",
        "seed": "INTERACTIVE_SEED",
        "target_fps": 60,
        "enable_graphics": True,
        "enable_persistence": True,
        "enable_logging": True
    }
    
    # Initialize and run
    if await system.initialize(config):
        await system.run_interactive_mode()
    else:
        logger.error("💥 Failed to initialize system")
        return 1
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DGT Autonomous Movie System")
    parser.add_argument("--mode", choices=["autonomous", "demo", "interactive"], 
                       default="autonomous", help="Running mode")
    parser.add_argument("--scene", choices=["tavern", "forest", "demo"], 
                       default="tavern", help="Scene to run")
    parser.add_argument("--seed", default="TAVERN_SEED", help="World seed")
    parser.add_argument("--fps", type=int, default=60, help="Target FPS")
    parser.add_argument("--no-graphics", action="store_true", help="Disable graphics")
    parser.add_argument("--no-persistence", action="store_true", help="Disable persistence")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    logger.info(f"🏰 DGT Autonomous Movie System - {args.mode} mode")
    logger.info(f"🎬 Scene: {args.scene}, Seed: {args.seed}")
    
    try:
        # Run appropriate mode
        if args.mode == "autonomous":
            if args.scene == "tavern":
                return asyncio.run(run_tavern_autopilot())
            elif args.scene == "forest":
                return asyncio.run(run_forest_autopilot())
            else:
                return asyncio.run(run_tavern_autopilot())
        elif args.mode == "demo":
            return asyncio.run(run_demo())
        elif args.mode == "interactive":
            return asyncio.run(run_interactive())
        else:
            logger.error(f"Unknown mode: {args.mode}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
