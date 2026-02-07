"""
run_systemic_game.py - The "Dwarf Fortress" Session-Zero Runner

Lean, autonomous game runner that executes the systemic simulation.
The seed generates the story - no manual scripting required.

Execution Flow:
1. World-Gen generates the mathematical skeleton
2. Chronos scans for high-value coordinates and injects tasks  
3. Voyager receives priority task and generates A* intent
4. Mind processes every step with D20 chaos
5. Body renders 160x144 proof-of-life
"""

import asyncio
import argparse
import signal
import sys
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Rich for deterministic event logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from loguru import logger

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import core system configuration
from core.system_config import SystemConfig, create_default_config

# Import pillar engines (stateless initialization)
from engines.world import WorldEngine, WorldEngineFactory
from engines.mind import DDEngine, DDEngineFactory
from engines.body import GraphicsEngine, GraphicsEngineFactory

# Import narrative engines
from narrative.chronos import ChronosEngine, ChronosEngineFactory
from narrative.persona import PersonaEngine, PersonaEngineFactory

# Import actor
from actors.voyager import Voyager, VoyagerFactory


class SystemicGameRunner:
    """The 'Dwarf Fortress' autonomous game runner"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.running = False
        
        # Rich console for deterministic event logging
        self.console = Console()
        self.live_display: Optional[Live] = None
        
        # Pillar instances (stateless)
        self.world_engine: Optional[WorldEngine] = None
        self.dd_engine: Optional[DDEngine] = None
        self.graphics_engine: Optional[GraphicsEngine] = None
        self.chronos_engine: Optional[ChronosEngine] = None
        self.persona_engine: Optional[PersonaEngine] = None
        self.voyager: Optional[Voyager] = None
        
        # Performance tracking
        self.turn_count = 0
        self.start_time = time.time()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.console.print(f"[bold green]🏰 Systemic Game Runner initialized with seed: {config.seed}[/]")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.console.print(f"[bold red]🛑 Received signal {signum}, shutting down...[/]")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self) -> bool:
        """Initialize all pillars with stateless configuration"""
        try:
            self.console.print("[bold blue]🚀 Initializing 6-pillar architecture...[/]")
            
            # 1. World Engine - Mathematical skeleton
            self.world_engine = WorldEngineFactory.create_world(self.config.world)
            self.console.print(f"[dim]🌍 World Engine initialized: {self.config.world.size_x}x{self.config.world.size_y}[/]")
            
            # 2. Mind Engine - D20 chaos processor
            self.dd_engine = DDEngineFactory.create_engine(self.config.mind)
            self.dd_engine.set_world_engine(self.world_engine)
            self.console.print("[dim]🧠 Mind Engine initialized - D20 chaos ready[/]")
            
            # 3. Body Engine - 160x144 PPU renderer
            if self.config.enable_graphics:
                self.graphics_engine = GraphicsEngineFactory.create_engine(self.config.body)
                self.console.print("[dim]🎨 Graphics Engine initialized - 160x144 PPU[/]")
            
            # 4. Chronos Engine - Systemic DM
            self.chronos_engine = ChronosEngineFactory.create_engine(self.config.chronos)
            self.chronos_engine.set_world_engine(self.world_engine)
            self.console.print("[dim]⏳ Chronos Engine initialized - Systemic DM ready[/]")
            
            # 5. Persona Engine - Social soul
            self.persona_engine = PersonaEngineFactory.create_engine(self.config.persona)
            self.chronos_engine.set_persona_engine(self.persona_engine)
            self.console.print("[dim]👥 Persona Engine initialized - Social dynamics ready[/]")
            
            # 6. Voyager - Autonomous actor
            self.voyager = VoyagerFactory.create_voyager(self.config.voyager, self.dd_engine, self.chronos_engine)
            self.console.print("[dim]🚶 Voyager initialized - Autonomous mode enabled[/]")
            
            # Connect pillar dependencies
            self.world_engine.set_chronos_engine(self.chronos_engine)
            self.console.print("[dim]🔗 Pillar dependencies connected[/]")
            
            # Generate initial objectives from world math
            await self.chronos_engine.scan_world_for_objectives()
            self.console.print("[dim]🎯 Initial objectives generated from world seed[/]")
            
            # Set Voyager spawn position from config or default
            spawn_point = self.config.default_spawn_points.get("tavern", (10, 25))
            self.voyager.current_position = spawn_point
            self.console.print(f"[dim]📍 Voyager spawned at {spawn_point}[/]")
            
            self.console.print("[bold green]✅ 6-pillar architecture initialization complete[/]")
            return True
            
        except Exception as e:
            self.console.print(f"[bold red]💥 Initialization failed: {e}[/]")
            logger.error(f"System initialization failed: {e}")
            return False
    
    async def run_autonomous_simulation(self) -> None:
        """Run the autonomous systemic simulation"""
        self.console.print("[bold green]🎬 Starting autonomous systemic simulation...[/]")
        self.running = True
        
        # Setup Rich live display for deterministic event logging
        layout = self._create_dashboard_layout()
        self.live_display = Live(layout, refresh_per_second=10, console=self.console)
        self.live_display.start()
        
        try:
            while self.running:
                turn_start = time.time()
                
                # === SYSTEMIC LOOP ===
                
                # 1. Chronos: Update procedural objectives
                await self.chronos_engine.update_procedural_quests()
                
                # 2. Voyager: Generate intent from current objective
                current_state = self.dd_engine.get_current_state()
                intent = await self.voyager.generate_next_intent(current_state)
                
                if intent:
                    # Log intent generation
                    self._log_systemic_event(f"🎯 Voyager intent: {intent.intent_type} -> {intent.target_position}")
                    
                    # 3. Mind: Process intent with D20 chaos
                    success = await self.voyager.submit_intent(intent)
                    
                    # 4. Log deterministic outcome
                    if success:
                        self._log_systemic_event(f"✅ Intent successful: {intent.intent_type}")
                    else:
                        self._log_systemic_event(f"❌ Intent failed: {intent.intent_type}")
                    
                    # 5. Check for quest completion
                    await self._check_quest_completion()
                
                # 6. Body: Render frame (if enabled)
                if self.graphics_engine and self.config.enable_graphics:
                    frame = await self.graphics_engine.render_state(current_state)
                    await self.graphics_engine.display_frame(frame)
                
                # Update turn counter and dashboard
                self.turn_count += 1
                self._update_dashboard(layout)
                
                # Maintain target FPS
                turn_time = time.time() - turn_start
                target_turn_time = 1.0 / self.config.target_fps
                sleep_time = max(0, target_turn_time - turn_time)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                elif self.turn_count % 60 == 0:  # Log performance warning every 60 turns
                    self._log_systemic_event(f"⚠️ Frame overrun: {turn_time*1000:.1f}ms")
                
        except KeyboardInterrupt:
            self.console.print("[bold yellow]🛑 Simulation interrupted by user[/]")
        except Exception as e:
            self.console.print(f"[bold red]💥 Simulation error: {e}[/]")
            logger.error(f"Simulation error: {e}")
        finally:
            self.running = False
            if self.live_display:
                self.live_display.stop()
            self.console.print("[bold blue]🎬 Autonomous simulation ended[/]")
    
    def _log_systemic_event(self, event: str) -> None:
        """Log deterministic systemic event with Rich"""
        timestamp = f"[{self.turn_count:04d}]"
        self.console.print(f"[dim cyan]{timestamp}[/] [white]{event}[/]")
        
        # Also log to file for persistence
        logger.info(f"[SEED_LOG] {event}")
    
    async def _check_quest_completion(self) -> None:
        """Check if current quest objective was reached"""
        if not self.voyager or not self.chronos_engine:
            return
        
        current_pos = self.voyager.current_position
        objective = await self.chronos_engine.get_current_objective()
        
        if objective and current_pos == objective:
            # Quest completed!
            self._log_systemic_event(f"🎉 Quest objective reached at {current_pos}")
            
            # Complete the quest
            active_quests = self.chronos_engine.quest_stack.get_active_quests()
            if active_quests:
                quest = active_quests[0]
                await self.chronos_engine.complete_quest(quest.quest_id, {"experience": 50})
                self._log_systemic_event(f"✅ Quest completed: {quest.title}")
    
    def _create_dashboard_layout(self) -> Layout:
        """Create Rich dashboard layout for systemic logging"""
        layout = Layout()
        
        # Main sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="events", ratio=2),
            Layout(name="status", ratio=1)
        )
        
        # Header
        layout["header"].update(
            Panel(f"[bold green]🏰 Systemic Simulation - Seed: {self.config.seed}[/]", 
                  border_style="green")
        )
        
        # Events panel
        layout["events"].update(
            Panel("[dim]📜 Systemic events will appear here...[/]", 
                  title="📜 Seed-Generated History", 
                  border_style="blue")
        )
        
        # Status panel
        status_table = Table(show_header=False, box=None)
        status_table.add_row("Turn:", "0")
        status_table.add_row("Position:", str(self.voyager.current_position if self.voyager else (0, 0)))
        status_table.add_row("Active Quests:", "0")
        status_table.add_row("FPS:", f"{self.config.target_fps}")
        
        layout["status"].update(
            Panel(status_table, title="📊 System Status", border_style="yellow")
        )
        
        # Footer
        layout["footer"].update(
            Panel("[dim]Press Ctrl+C to stop simulation[/]", 
                  border_style="red")
        )
        
        return layout
    
    def _update_dashboard(self, layout: Layout) -> None:
        """Update dashboard with current state"""
        if not self.live_display:
            return
        
        # Update status table
        status_table = Table(show_header=False, box=None)
        status_table.add_row("Turn:", str(self.turn_count))
        status_table.add_row("Position:", str(self.voyager.current_position if self.voyager else (0, 0)))
        
        active_quests = len(self.chronos_engine.quest_stack.get_active_quests()) if self.chronos_engine else 0
        status_table.add_row("Active Quests:", str(active_quests))
        
        uptime = time.time() - self.start_time
        status_table.add_row("Uptime:", f"{uptime:.1f}s")
        
        layout["status"].update(
            Panel(status_table, title="📊 System Status", border_style="yellow")
        )
        
        # Update events panel with recent events
        # (In a full implementation, we'd maintain an event buffer)
        events_text = f"[dim]Turn {self.turn_count}: Voyager navigating...[/]"
        layout["events"].update(
            Panel(events_text, title="📜 Seed-Generated History", border_style="blue")
        )


async def main():
    """Main entry point for the systemic game runner"""
    parser = argparse.ArgumentParser(description="Systemic Game Runner - Dwarf Fortress Mode")
    parser.add_argument("--seed", default="TAVERN_SEED", help="World generation seed")
    parser.add_argument("--config", type=Path, help="Path to configuration YAML file")
    parser.add_argument("--fps", type=int, default=60, help="Target FPS")
    parser.add_argument("--no-graphics", action="store_true", help="Disable graphics rendering")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Load configuration
    console = Console()
    console.print(f"[bold blue]🏰 Systemic Game Runner - Seed: {args.seed}[/]")
    
    try:
        if args.config and args.config.exists():
            config = SystemConfig.from_yaml(args.config, args.seed)
            console.print(f"[dim]✅ Configuration loaded from {args.config}[/]")
        else:
            config = create_default_config(args.seed)
            console.print("[dim]✅ Using default configuration[/]")
        
        # Override command line options
        config.target_fps = args.fps
        config.enable_graphics = not args.no_graphics
        
        # Create and run the systemic simulation
        runner = SystemicGameRunner(config)
        
        if await runner.initialize():
            await runner.run_autonomous_simulation()
        else:
            console.print("[bold red]💥 Failed to initialize system[/]")
            return 1
            
    except Exception as e:
        console.print(f"[bold red]💥 Fatal error: {e}[/]")
        logger.error(f"Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
