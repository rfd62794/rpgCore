"""
Game Engine: Orchestrator

The thin orchestrator that moves data between specialized modules.
Replaces the God Class GameREPL with clean separation of concerns.

Flow: Sense → Resolve → Act → Narrate
"""

import asyncio
from pathlib import Path
from typing import Optional

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.live import Live

from game_state import GameState
from semantic_engine import SemanticResolver, create_default_intent_library
from d20_core import D20Resolver, D20Result
from narrator import Narrator
from world_factory import WorldFactory
from character_factory import CharacterFactory
from loot_system import LootSystem
from utils.context_manager import ContextManager


class GameEngine:
    """
    Thin orchestrator - the traffic controller of the D&D Framework.
    
    Only responsibility: coordinate data flow between specialized modules.
    """
    
    def __init__(
        self,
        state: Optional[GameState] = None,
        save_path: Optional[Path] = None,
        personality: str = "curious"
    ):
        """Initialize the engine with all specialized modules."""
        self.console = Console()
        self.save_path = save_path or Path("savegame.json")
        
        # Initialize game state or load existing
        self.state = state or self._create_fresh_state(personality)
        if self.save_path.exists():
            try:
                self.console.print(f"[green]Loading saved game from {self.save_path}[/green]")
                self.state = GameState.load_from_file(self.save_path)
            except Exception as e:
                logger.error(f"Failed to load save: {e}. Starting fresh.")
                self.state = self._create_fresh_state(personality)
        
        # Initialize specialized modules
        self.semantic_resolver = SemanticResolver(
            create_default_intent_library(), 
            confidence_threshold=0.35
        )
        self.d20_resolver = D20Resolver()
        self.narrator = Narrator()
        self.world_factory = WorldFactory()
        self.loot_system = LootSystem()
        self.context_manager = ContextManager()
        
        # Sync world data to state
        self._sync_world_to_state()
        
        logger.info("Game Engine initialized with Domain-Driven Design")
    
    def _create_fresh_state(self, personality: str) -> GameState:
        """Create fresh game state with character."""
        player = CharacterFactory.create(personality)
        state = GameState(player=player)
        state.current_room = "tavern"
        return state
    
    def _sync_world_to_state(self):
        """Sync world factory data into game state."""
        current_location = self.state.current_room
        
        # If location doesn't exist in state, create it from world factory
        if current_location not in self.state.rooms:
            location_data = self.world_factory.get_location(current_location)
            if location_data:
                self.state.rooms[current_location] = location_data
    
    async def process_action(self, player_input: str) -> bool:
        """
        Main action processing pipeline.
        
        Returns:
            True to continue game, False to quit
        """
        # Handle meta commands
        if player_input.lower() in ["quit", "exit", "q"]:
            return False
        
        if player_input.lower() in ["save"]:
            self.state.save_to_file(self.save_path)
            self.console.print("[green]Game saved![/green]")
            return True
        
        # Step 1: Sense - Resolve intent
        self.console.print("[dim]🔍 Resolving intent...[/dim]")
        intent_match = self.semantic_resolver.resolve_intent(player_input)
        
        if not intent_match:
            self.console.print(
                "[red]❌ I don't understand that action. Try rephrasing?[/red]"
            )
            return True
        
        self.console.print(
            f"[cyan]🎲 Intent: {intent_match.intent_id} "
            f"(confidence: {intent_match.confidence:.2f})[/cyan]"
        )
        
        # Step 2: Resolve - D20 Core calculations
        self.console.print("[dim]⚖️  D20 Core calculating...[/dim]")
        
        room = self.state.rooms.get(self.state.current_room)
        room_tags = room.tags if room else []
        
        # Detect target NPC
        target_npc = self._detect_target_npc(player_input, room)
        
        d20_result = self.d20_resolver.resolve_action(
            intent_id=intent_match.intent_id,
            player_input=player_input,
            game_state=self.state,
            room_tags=room_tags,
            target_npc=target_npc
        )
        
        self.console.print(
            f"[dim]🎲 Math: {d20_result.total_score} vs DC {d20_result.difficulty_class} "
            f"({'SUCCESS' if d20_result.success else 'FAILURE'})[/dim]"
        )
        
        # Step 3: Act - Apply state changes
        self._apply_d20_result(d20_result, intent_match.intent_id, player_input)
        
        # Step 4: Check for loot
        loot_item = self._check_for_loot(d20_result, intent_match.intent_id, room)
        
        # Step 5: Narrate - Generate narrative
        await self._narrate_outcome(player_input, intent_match.intent_id, d20_result, loot_item)
        
        # Step 6: Auto-save
        self.state.save_to_file(self.save_path)
        
        # Step 7: Check win/loss conditions
        return self._check_game_over()
    
    def _detect_target_npc(self, player_input: str, room) -> Optional[str]:
        """Detect which NPC the player is targeting."""
        if not room or not room.npcs:
            return None
        
        input_lower = player_input.lower()
        
        # Check for explicit NPC names
        for npc in room.npcs:
            if npc.name.lower() in input_lower:
                return npc.name
        
        # If only one NPC, assume that's the target
        if len(room.npcs) == 1:
            return room.npcs[0].name
        
        return None
    
    def _apply_d20_result(self, result: D20Result, intent_id: str, player_input: str):
        """Apply all state changes from D20 resolution."""
        # Apply HP changes
        if result.hp_delta != 0:
            if result.hp_delta < 0:
                self.state.player.take_damage(abs(result.hp_delta))
            else:
                self.state.player.heal(result.hp_delta)
        
        # Apply reputation changes
        for faction, delta in result.reputation_deltas.items():
            self.state.reputation[faction] = self.state.reputation.get(faction, 0) + delta
            if delta != 0:
                self.console.print(
                    f"[bold yellow]⚖️ Reputation: {faction.replace('_', ' ').title()} "
                    f"{'increased' if delta > 0 else 'decreased'}! ({self.state.reputation[faction]})[/bold yellow]"
                )
        
        # Apply relationship changes
        for npc_id, changes in result.relationship_changes.items():
            self.state.update_relationship(
                self.state.current_room,
                npc_id,
                delta_disposition=changes["disposition"],
                new_tags=changes["tags"]
            )
        
        # Apply NPC state changes
        room = self.state.rooms.get(self.state.current_room)
        if room:
            for npc_id, new_state in result.npc_state_changes.items():
                for npc in room.npcs:
                    if npc.name.lower() == npc_id.lower():
                        npc.update_state(new_state)
                        break
        
        # Apply goal completion
        for goal_id in result.goals_completed:
            for goal in self.state.goal_stack:
                if goal.id == goal_id:
                    goal.status = "success"
                    self.state.completed_goals.append(goal_id)
                    self.console.print(f"[bold green]✨ Objective Complete: {goal.description}[/bold green]")
                    self.state.goal_stack.remove(goal)
                    break
        
        # Handle room transitions
        if result.success and intent_id == "leave_area":
            self._handle_room_transition()
        
        # Increment turn counter
        self.state.turn_count += 1
    
    def _check_for_loot(self, d20_result: D20Result, intent_id: str, room) -> Optional:
        """Check if action generates loot."""
        if not d20_result.success or intent_id not in ["investigate", "force"]:
            return None
        
        if not room:
            return None
        
        loot_item = self.loot_system.generate_loot(
            location=room.name,
            intent=intent_id
        )
        
        if loot_item:
            self.state.player.inventory.append(loot_item)
            logger.info(f"Loot added to inventory: {loot_item.name}")
        
        return loot_item
    
    async def _narrate_outcome(self, player_input: str, intent_id: str, d20_result: D20Result, loot_item):
        """Generate and display narrative output."""
        self.console.print("[dim]📖 Narrator generating story...[/dim]")
        
        narrative_color = "green" if d20_result.success else "yellow"
        success_icon = "✅" if d20_result.success else "❌"
        
        # Stream narrative generation
        async def _stream_bridge():
            narrative_text = ""
            title_text = f"[bold {narrative_color}]{success_icon} Outcome[/bold {narrative_color}]"
            
            with Live(
                Panel(narrative_text, title=title_text, border_style=narrative_color),
                console=self.console,
                refresh_per_second=12
            ) as live:
                async for token in self.narrator.narrate_stream(
                    player_input=player_input,
                    intent_id=intent_id,
                    d20_result=d20_result,
                    context=self.state.get_context_str()
                ):
                    narrative_text += token
                    live.update(Panel(narrative_text, title=title_text, border_style=narrative_color))
            
            return narrative_text
        
        final_narrative = await _stream_bridge()
        
        # Append loot notification if any
        output_text = final_narrative
        if loot_item:
            output_text += f"\n\n💎 **Loot found**: {loot_item.name} ({loot_item.description})"
            if hasattr(loot_item, 'stat_bonus') and loot_item.stat_bonus:
                output_text += f" [{loot_item.stat_bonus}]"
        
        self.console.print(
            Panel(
                output_text,
                title=f"[bold {narrative_color}]{success_icon} Outcome[/bold {narrative_color}]",
                border_style=narrative_color
            )
        )
    
    def _handle_room_transition(self):
        """Handle transitioning to a new room."""
        room = self.state.rooms.get(self.state.current_room)
        if not room or not room.exits:
            return
        
        # Take the first exit (simple logic for now)
        next_room_id = list(room.exits.values())[0]
        self.state.current_room = next_room_id
        
        # Sync new location data
        self._sync_world_to_state()
        
        self.console.print(f"\n[bold yellow]🚙 Transitioning to {self.state.rooms[next_room_id].name}...[/bold yellow]")
        
        # Clear scene-specific goals
        self.state.goal_stack = [g for g in self.state.goal_stack if g.type != "short"]
    
    def _check_game_over(self) -> bool:
        """Check if game should end."""
        if not self.state.player.is_alive():
            self.console.print(
                Panel(
                    "[bold red]You have died. Game Over.[/bold red]",
                    border_style="red"
                )
            )
            return False
        
        return True
    
    def display_context(self) -> None:
        """Display current game context."""
        room_context = self.state.get_context_str()
        self.console.print(
            Panel(room_context, title="[bold blue]Current Scene[/bold blue]", border_style="blue")
        )
        
        # Player stats table
        from rich.table import Table
        stats_table = Table(show_header=False, box=None)
        stats_table.add_row("❤️  HP:", f"{self.state.player.hp}/{self.state.player.max_hp}")
        stats_table.add_row("💰 Gold:", str(self.state.player.gold))
        
        self.console.print(
            Panel(stats_table, title="[bold green]Player Stats[/bold green]", border_style="green")
        )


# Export for use by main game loop
__all__ = ["GameEngine"]
