"""
Developer Console - Live Pillar Manipulation

Provides a unified command interface for manipulating all 6 pillars
while the RPG Core is running. This enables live editing and debugging
of the game world, NPCs, quests, and game state.

Commands follow the pattern: /pillar action [arguments...]

Examples:
/world set_tile 20 20 STONE
/world apply_surface 20 20 FIRE 30.0
/mind validate_movement 10 10 15 10
/persona create_npc 25 30 innkeeper
/chronos inject_task bribe_guard 20 20
/body render_frame
/state add_tag combat_mode
"""

import asyncio
import threading
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from loguru import logger

# Import all pillars
from core.state import TileType, SurfaceState, validate_position
from engines.world import WorldEngine
from engines.mind import DDEngine
from engines.body import GraphicsEngine
from actors.voyager import Voyager
from narrative.chronos import ChronosEngine, Quest, QuestType, TaskPriority
from narrative.persona import PersonaEngine, FactionType


@dataclass
class ConsoleCommand:
    """Console command structure"""
    pillar: str
    action: str
    args: List[str]
    raw_command: str


class DeveloperConsole:
    """Live developer console for pillar manipulation"""
    
    def __init__(self, dgt_system):
        self.dgt_system = dgt_system
        self.running = False
        self.command_history: List[str] = []
        self.output_buffer: List[str] = []
        
        # Command handlers
        self.handlers = {
            "world": self._handle_world_command,
            "mind": self._handle_mind_command,
            "body": self._handle_body_command,
            "persona": self._handle_persona_command,
            "chronos": self._handle_chronos_command,
            "state": self._handle_state_command,
            "help": self._handle_help_command,
            "status": self._handle_status_command,
            "clear": self._handle_clear_command
        }
        
        logger.info("🖥️ Developer Console initialized")
    
    async def start(self) -> None:
        """Start the console command loop"""
        self.running = True
        logger.info("🖥️ Developer Console started - Type '/help' for commands")
        
        # Run console in background thread
        console_thread = threading.Thread(target=self._console_loop, daemon=True)
        console_thread.start()
    
    def stop(self) -> None:
        """Stop the console"""
        self.running = False
        logger.info("🖥️ Developer Console stopped")
    
    def _console_loop(self) -> None:
        """Main console input loop"""
        while self.running:
            try:
                import sys
                
                # Read command from stdin
                print("🖥️ Dev> ", end="", flush=True)
                command_line = sys.stdin.readline().strip()
                
                if command_line and self.running:
                    self._execute_command(command_line)
                    
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                self._output(f"❌ Console error: {e}")
    
    def _execute_command(self, command_line: str) -> None:
        """Parse and execute a console command"""
        command_line = command_line.strip()
        
        if not command_line:
            return
        
        # Add to history
        self.command_history.append(command_line)
        
        # Parse command
        if command_line.startswith("/"):
            parts = command_line[1:].split()
            if len(parts) >= 2:
                pillar = parts[0].lower()
                action = parts[1].lower()
                args = parts[2:] if len(parts) > 2 else []
                
                cmd = ConsoleCommand(pillar, action, args, command_line)
                
                # Execute command
                if pillar in self.handlers:
                    try:
                        # Run command in async context
                        asyncio.run(self.handlers[pillar](cmd))
                    except Exception as e:
                        self._output(f"❌ Command execution failed: {e}")
                else:
                    self._output(f"❌ Unknown pillar: {pillar}")
            else:
                self._output("❌ Invalid command format. Use: /pillar action [args...]")
        else:
            self._output("❌ Commands must start with /")
    
    def _output(self, message: str) -> None:
        """Output message to console and buffer"""
        print(message)
        self.output_buffer.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        
        # Keep buffer manageable
        if len(self.output_buffer) > 100:
            self.output_buffer = self.output_buffer[-50:]
    
    # === COMMAND HANDLERS ===
    
    async def _handle_world_command(self, cmd: ConsoleCommand) -> None:
        """Handle World Engine commands"""
        world = self.dgt_system.world_engine
        if not world:
            self._output("❌ World Engine not available")
            return
        
        if cmd.action == "set_tile":
            if len(cmd.args) >= 3:
                try:
                    x, y = int(cmd.args[0]), int(cmd.args[1])
                    tile_type_str = cmd.args[2].upper()
                    
                    if validate_position((x, y)):
                        tile_type = TileType[tile_type_str]
                        await self._set_tile(world, x, y, tile_type)
                        self._output(f"✅ Set tile ({x}, {y}) to {tile_type_str}")
                    else:
                        self._output("❌ Invalid position")
                except (ValueError, KeyError):
                    self._output("❌ Invalid tile type or coordinates")
            else:
                self._output("❌ Usage: /world set_tile x y TILE_TYPE")
        
        elif cmd.action == "apply_surface":
            if len(cmd.args) >= 3:
                try:
                    x, y = int(cmd.args[0]), int(cmd.args[1])
                    surface_str = cmd.args[2].upper()
                    duration = float(cmd.args[3]) if len(cmd.args) > 3 else None
                    
                    if validate_position((x, y)):
                        surface_state = SurfaceState[surface_str]
                        await self._apply_surface(world, x, y, surface_state, duration)
                        self._output(f"✅ Applied {surface_str} to ({x}, {y})" + (f" for {duration}s" if duration else "")
                    else:
                        self._output("❌ Invalid position")
                except (ValueError, KeyError):
                    self._output("❌ Invalid surface state or coordinates")
            else:
                self._output("❌ Usage: /world apply_surface x y SURFACE_STATE [duration]")
        
        elif cmd.action == "preview_chunk":
            if len(cmd.args) >= 2:
                try:
                    x, y = int(cmd.args[0]), int(cmd.args[1])
                    await self._preview_chunk(world, x, y)
                except ValueError:
                    self._output("❌ Invalid coordinates")
            else:
                self._output("❌ Usage: /world preview_chunk x y")
        
        elif cmd.action == "get_tile":
            if len(cmd.args) >= 2:
                try:
                    x, y = int(cmd.args[0]), int(cmd.args[1])
                    await self._get_tile_info(world, x, y)
                except ValueError:
                    self._output("❌ Invalid coordinates")
            else:
                self._output("❌ Usage: /world get_tile x y")
        
        else:
            self._output(f"❌ Unknown world action: {cmd.action}")
            self._output("Available actions: set_tile, apply_surface, preview_chunk, get_tile")
    
    async def _handle_mind_command(self, cmd: ConsoleCommand) -> None:
        """Handle Mind Engine commands"""
        mind = self.dgt_system.dd_engine
        if not mind:
            self._output("❌ Mind Engine not available")
            return
        
        if cmd.action == "validate_movement":
            if len(cmd.args) >= 4:
                try:
                    from_x, from_y = int(cmd.args[0]), int(cmd.args[1])
                    to_x, to_y = int(cmd.args[2]), int(cmd.args[3])
                    
                    result = await self._validate_movement(mind, from_x, from_y, to_x, to_y)
                    self._output(f"🧠 Movement validation: {result}")
                except ValueError:
                    self._output("❌ Invalid coordinates")
            else:
                self._output("❌ Usage: /mind validate_movement from_x from_y to_x to_y")
        
        elif cmd.action == "get_rule_stack":
            await self._get_rule_stack(mind)
        
        elif cmd.action == "get_state":
            state = mind.get_current_state()
            self._output(f"🧠 Current state: pos={state.player_position}, turn={state.turn_count}")
        
        else:
            self._output(f"❌ Unknown mind action: {cmd.action}")
            self._output("Available actions: validate_movement, get_rule_stack, get_state")
    
    async def _handle_body_command(self, cmd: ConsoleCommand) -> None:
        """Handle Body Engine commands"""
        body = self.dgt_system.graphics_engine
        if not body:
            self._output("❌ Body Engine not available")
            return
        
        if cmd.action == "render_frame":
            await self._render_frame(body)
        
        elif cmd.action == "get_viewport":
            info = await self._get_viewport_info(body)
            self._output(f"🎨 Viewport: {info}")
        
        else:
            self._output(f"❌ Unknown body action: {cmd.action}")
            self._output("Available actions: render_frame, get_viewport")
    
    async def _handle_persona_command(self, cmd: ConsoleCommand) -> None:
        """Handle Persona Engine commands"""
        persona = self.dgt_system.persona_engine
        if not persona:
            self._output("❌ Persona Engine not available")
            return
        
        if cmd.action == "create_npc":
            if len(cmd.args) >= 2:
                try:
                    x, y = int(cmd.args[0]), int(cmd.args[1])
                    npc_type = cmd.args[2] if len(cmd.args) > 2 else "random"
                    
                    npc = await persona.generate_npc_at_position((x, y), npc_type)
                    if npc:
                        self._output(f"👥 Created NPC: {npc.personality.name} at ({x}, {y})")
                        self._output(f"   Faction: {npc.personality.primary_faction.value}")
                        self._output(f"   Traits: {[t.value for t in npc.personality.base_traits]}")
                        self._output(f"   Tags: {list(npc.personality.tags)}")
                    else:
                        self._output("❌ Failed to create NPC")
                except ValueError:
                    self._output("❌ Invalid coordinates")
            else:
                self._output("❌ Usage: /persona create_npc x y [npc_type]")
        
        elif cmd.action == "get_npc":
            if len(cmd.args) >= 2:
                try:
                    x, y = int(cmd.args[0]), int(cmd.args[1])
                    npc = persona.npc_registry.get_npc_at_position((x, y))
                    if npc:
                        self._output(f"👥 NPC at ({x}, {y}): {npc.personality.name}")
                        self._output(f"   Mood: {npc.social_state.current_mood.value}")
                        self._output(f"   Trust: {npc.social_state.trust_level:.2f}")
                    else:
                        self._output("❌ No NPC at position")
                except ValueError:
                    self._output("❌ Invalid coordinates")
            else:
                self._output("❌ Usage: /persona get_npc x y")
        
        elif cmd.action == "list_npcs":
            radius = int(cmd.args[0]) if cmd.args else 10
            npcs = persona.get_npcs_in_area((10, 25), radius)
            self._output(f"👥 NPCs in radius {radius}:")
            for npc in npcs:
                self._output(f"   {npc.personality.name} at {npc.position}")
        
        elif cmd.action == "faction_standing":
            if len(cmd.args) >= 2:
                faction1, faction2 = cmd.args[0].upper(), cmd.args[1].upper()
                try:
                    f1 = FactionType(faction1)
                    f2 = FactionType(faction2)
                    standing = persona.faction_system.get_standing(f1, f2)
                    relation = persona.faction_system.get_relation_type(f1, f2)
                    self._output(f"🏛️ {faction1} ↔ {faction2}: {relation.value} ({standing:+.1f})")
                except ValueError:
                    self._output("❌ Invalid faction names")
            else:
                self._output("❌ Usage: /persona faction_standing faction1 faction2")
        
        else:
            self._output(f"❌ Unknown persona action: {cmd.action}")
            self._output("Available actions: create_npc, get_npc, list_npcs, faction_standing")
    
    async def _handle_chronos_command(self, cmd: ConsoleCommand) -> None:
        """Handle Chronos Engine commands"""
        chronos = self.dgt_system.chronos_engine
        if not chronos:
            self._output("❌ Chronos Engine not available")
            return
        
        if cmd.action == "inject_task":
            if len(cmd.args) >= 3:
                task_id = cmd.args[0]
                try:
                    x, y = int(cmd.args[1]), int(cmd.args[2])
                    
                    quest = Quest(
                        quest_id=task_id,
                        title=f"Injected Task: {task_id}",
                        description="Developer injected task",
                        quest_type=QuestType.SIDE_TASK,
                        priority=TaskPriority.HIGH,
                        target_position=(x, y),
                        required_level=1
                    )
                    
                    if chronos.quest_stack.add_quest(quest):
                        self._output(f"⏳ Injected task '{task_id}' at ({x}, {y})")
                    else:
                        self._output("❌ Failed to inject task")
                except ValueError:
                    self._output("❌ Invalid coordinates")
            else:
                self._output("❌ Usage: /chronos inject_task task_id x y")
        
        elif cmd.action == "get_quests":
            current = chronos.get_current_quest()
            available = chronos.get_available_quests()
            
            self._output("⏳ Quest Status:")
            if current:
                self._output(f"   Current: {current['title']} at {current['target_position']}")
            else:
                self._output("   Current: None")
            
            self._output(f"   Available: {len(available)} quests")
            for quest in available[:5]:  # Show first 5
                self._output(f"   - {quest['title']} at {quest['target_position']}")
        
        elif cmd.action == "accept_quest":
            if cmd.args:
                quest_id = cmd.args[0]
                if chronos.quest_stack.activate_quest(quest_id, chronos.character_stats.level):
                    self._output(f"⏳ Accepted quest: {quest_id}")
                else:
                    self._output(f"❌ Failed to accept quest: {quest_id}")
            else:
                self._output("❌ Usage: /chronos accept_quest quest_id")
        
        elif cmd.action == "complete_quest":
            if cmd.args:
                quest_id = cmd.args[0]
                if chronos.quest_stack.complete_quest(quest_id):
                    self._output(f"✅ Completed quest: {quest_id}")
                else:
                    self._output(f"❌ Failed to complete quest: {quest_id}")
            else:
                self._output("❌ Usage: /chronos complete_quest quest_id")
        
        elif cmd.action == "get_stats":
            stats = chronos.get_character_stats()
            self._output("📊 Character Stats:")
            self._output(f"   Level: {stats['level']}")
            self._output(f"   XP: {stats['experience']}/{stats['experience_to_next']}")
            self._output(f"   Health: {stats['health']}/{stats['max_health']}")
            self._output(f"   Mana: {stats['mana']}/{stats['max_mana']}")
        
        else:
            self._output(f"❌ Unknown chronos action: {cmd.action}")
            self._output("Available actions: inject_task, get_quests, accept_quest, complete_quest, get_stats")
    
    async def _handle_state_command(self, cmd: ConsoleCommand) -> None:
        """Handle GameState commands"""
        state = self.dgt_system.dd_engine.get_current_state()
        
        if cmd.action == "add_tag":
            if cmd.args:
                tag = cmd.args[0]
                state.add_tag(tag)
                self._output(f"🏷️ Added tag: {tag}")
            else:
                self._output("❌ Usage: /state add_tag tag")
        
        elif cmd.action == "remove_tag":
            if cmd.args:
                tag = cmd.args[0]
                state.remove_tag(tag)
                self._output(f"🏷️ Removed tag: {tag}")
            else:
                self._output("❌ Usage: /state remove_tag tag")
        
        elif cmd.action == "get_tags":
            tags = list(state.tags)
            self._output(f"🏷️ State tags: {tags}")
        
        elif cmd.action == "set_position":
            if len(cmd.args) >= 2:
                try:
                    x, y = int(cmd.args[0]), int(cmd.args[1])
                    if validate_position((x, y)):
                        old_pos = state.player_position
                        state.player_position = (x, y)
                        self._output(f"📍 Position: {old_pos} → ({x}, {y})")
                    else:
                        self._output("❌ Invalid position")
                except ValueError:
                    self._output("❌ Invalid coordinates")
            else:
                self._output("❌ Usage: /state set_position x y")
        
        else:
            self._output(f"❌ Unknown state action: {cmd.action}")
            self._output("Available actions: add_tag, remove_tag, get_tags, set_position")
    
    async def _handle_help_command(self, cmd: ConsoleCommand) -> None:
        """Show help information"""
        self._output("🖥️ Developer Console Help")
        self._output("")
        self._output("Pillar Commands:")
        self._output("  /world set_tile x y TILE_TYPE")
        self._output("  /world apply_surface x y SURFACE_STATE [duration]")
        self._output("  /world preview_chunk x y")
        self._output("  /world get_tile x y")
        self._output("")
        self._output("  /mind validate_movement from_x from_y to_x to_y")
        self._output("  /mind get_rule_stack")
        self._output("  /mind get_state")
        self._output("")
        self._output("  /persona create_npc x y [npc_type]")
        self._output("  /persona get_npc x y")
        self._output("  /persona list_npcs [radius]")
        self._output("  /persona faction_standing faction1 faction2")
        self._output("")
        self._output("  /chronos inject_task task_id x y")
        self._output("  /chronos get_quests")
        self._output("  /chronos accept_quest quest_id")
        self._output("  /chronos complete_quest quest_id")
        self._output("  /chronos get_stats")
        self._output("")
        self._output("  /state add_tag tag")
        self._output("  /state remove_tag tag")
        self._output("  /state get_tags")
        self._output("  /state set_position x y")
        self._output("")
        self._output("  /body render_frame")
        self._output("  /body get_viewport")
        self._output("")
        self._output("  /status")
        self._output("  /clear")
        self._output("  /help")
    
    async def _handle_status_command(self, cmd: ConsoleCommand) -> None:
        """Show system status"""
        status = self.dgt_system.get_status()
        
        self._output("🏰 DGT System Status")
        self._output(f"   Running: {status['running']}")
        self._output(f"   Heartbeat: {status['heartbeat_active']}")
        self._output("")
        self._output("Pillars:")
        for pillar, active in status['pillars'].items():
            status_icon = "✅" if active else "❌"
            self._output(f"   {status_icon} {pillar}")
    
    async def _handle_clear_command(self, cmd: ConsoleCommand) -> None:
        """Clear console output"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        self._output("🖥️ Console cleared")
    
    # === WORLD ENGINE HELPER METHODS ===
    
    async def _set_tile(self, world: WorldEngine, x: int, y: int, tile_type: TileType) -> None:
        """Set tile at position"""
        chunk_pos = (x // 10, y // 10)  # Assuming 10x10 chunks
        await world._ensure_chunk_generated(chunk_pos)
        
        chunk = world.chunks[chunk_pos]
        local_x = x % 10
        local_y = y % 10
        
        chunk.tiles[local_y][local_x].tile_type = tile_type
    
    async def _apply_surface(self, world: WorldEngine, x: int, y: int, surface: SurfaceState, duration: Optional[float]) -> None:
        """Apply surface state to tile"""
        chunk_pos = (x // 10, y // 10)
        await world._ensure_chunk_generated(chunk_pos)
        
        chunk = world.chunks[chunk_pos]
        local_x = x % 10
        local_y = y % 10
        
        chunk.tiles[local_y][local_x].apply_surface_state(surface, duration)
    
    async def _preview_chunk(self, world: WorldEngine, x: int, y: int) -> None:
        """Preview chunk information"""
        chunk_pos = (x // 10, y // 10)
        await world._ensure_chunk_generated(chunk_pos)
        
        chunk = world.chunks[chunk_pos]
        self._output(f"🌍 Chunk {chunk_pos}:")
        
        # Count tile types
        tile_counts = {}
        for row in chunk.tiles:
            for tile in row:
                tile_type = tile.tile_type.name
                tile_counts[tile_type] = tile_counts.get(tile_type, 0) + 1
        
        for tile_type, count in sorted(tile_counts.items()):
            self._output(f"   {tile_type}: {count}")
    
    async def _get_tile_info(self, world: WorldEngine, x: int, y: int) -> None:
        """Get detailed tile information"""
        chunk_pos = (x // 10, y // 10)
        await world._ensure_chunk_generated(chunk_pos)
        
        chunk = world.chunks[chunk_pos]
        local_x = x % 10
        local_y = y % 10
        
        tile = chunk.tiles[local_y][local_x]
        self._output(f"🌍 Tile ({x}, {y}):")
        self._output(f"   Type: {tile.tile_type.name}")
        self._output(f"   Surface: {tile.surface_state.name}")
        self._output(f"   Walkable: {tile.walkable}")
        self._output(f"   Tags: {list(tile.tags)}")
    
    # === MIND ENGINE HELPER METHODS ===
    
    async def _validate_movement(self, mind: DDEngine, from_x: int, from_y: int, to_x: int, to_y: int) -> str:
        """Validate movement and return result"""
        from core.state import MovementIntent
        
        intent = MovementIntent(
            intent_type="movement",
            target_position=(to_x, to_y),
            path=[(to_x, to_y)],
            confidence=1.0
        )
        
        validation = mind._validate_movement_intent(intent)
        return validation.message
    
    async def _get_rule_stack(self, mind: DDEngine) -> None:
        """Get rule validation stack"""
        self._output("🧠 Rule Stack:")
        self._output("   1. Position validation")
        self._output("   2. Collision detection")
        self._output("   3. Movement range check")
        self._output("   4. Path validity")
        self._output("   5. Cooldown verification")
    
    # === BODY ENGINE HELPER METHODS ===
    
    async def _render_frame(self, body: GraphicsEngine) -> None:
        """Render current frame"""
        state = self.dgt_system.dd_engine.get_current_state()
        frame = body.render_frame_sync(state)
        self._output("🎨 Frame rendered (check graphics window)")
    
    async def _get_viewport_info(self, body: GraphicsEngine) -> Dict:
        """Get viewport information"""
        return {
            "width": body.width,
            "height": body.height,
            "target_fps": body.target_fps
        }
    
    def get_output_history(self) -> List[str]:
        """Get console output history"""
        return self.output_buffer.copy()
    
    def get_command_history(self) -> List[str]:
        """Get command history"""
        return self.command_history.copy()
