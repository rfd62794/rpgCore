"""
Main Game Loop: REPL for Semantic RPG

Orchestrates the Sense → Input → Resolve → Update cycle.
Main game loop (REPL) for the Semantic RPG Core.
"""

import argparse
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from game_state import GameState, create_tavern_scenario
from semantic_engine import SemanticResolver, create_default_intent_library

# Council of Three imports (sync wrappers)
from sync_engines import ArbiterEngine, ChroniclerEngine


class GameREPL:
    """
    Interactive game loop with Rich UI.
    
    Architecture (Council of Three):
    - SemanticResolver: Fast intent matching (~50ms)
    - ArbiterEngine: Pure logic/state resolution (~100ms, small model)
    - ChroniclerEngine: Narrative generation (~300ms, large model)
    - GameState: Deterministic state updates
    """
    
    def __init__(
        self,
        state: GameState | None = None,
        save_path: Path | None = None
    ):
        """
        Initialize game with optional saved state.
        
        Args:
            state: Existing GameState (or None to create new)
            save_path: Path for auto-saving (default: ./savegame.json)
        """
        self.console = Console()
        self.save_path = save_path or Path("savegame.json")
        
        # Initialize game state
        if state:
            self.state = state
        elif self.save_path.exists():
            self.console.print(f"[green]Loading saved game from {self.save_path}[/green]")
            self.state = GameState.load_from_file(self.save_path)
        else:
            self.console.print("[yellow]Starting new campaign...[/yellow]")
            # Use multi-location scenario with Social Graph
            from scenarios import create_multi_location_scenario
            self.state = create_multi_location_scenario()
            self.console.print("[cyan]Loaded: Rusty Flagon (Tavern) + Emerald City Plaza[/cyan]")
        
        # Initialize semantic engine
        self.console.print("[cyan]Loading semantic engine...[/cyan]")
        intent_library = create_default_intent_library()
        self.resolver = SemanticResolver(intent_library, confidence_threshold=0.35)
        
        # Initialize Council of Three
        self.console.print("[cyan]Loading Arbiter (logic engine)...[/cyan]")
        self.arbiter = ArbiterEngine(model_name='ollama:llama3.2:1b')
        
        self.console.print("[cyan]Loading Chronicler (narrative engine)...[/cyan]")
        self.chronicler = ChroniclerEngine(model_name='ollama:llama3.2:3b', tone='humorous')
        
        # Initialize Quartermaster (loot system)
        from loot_system import LootSystem
        self.loot = LootSystem()
        
        # Initialize Voyager (auto-play agent) if in auto mode
        self.auto_mode = auto_mode
        self.voyager = None
        if auto_mode:
            from voyager_sync import SyncVoyagerAgent
            personality = "curious"  # Can be overridden via CLI arg
            self.console.print(f"[magenta]Loading Voyager (auto-play) with '{personality}' personality...[/magenta]")
            self.voyager = SyncVoyagerAgent(personality=personality)
        
        # Turn history for stutter check (last 5 actions)
        self.turn_history: list[str] = []
        
        logger.info("Game initialized with Council of Three architecture")
    
    def display_context(self) -> None:
        """Display current game context using Rich panels."""
        # Room description
        room_context = self.state.get_context_str()
        self.console.print(
            Panel(room_context, title="[bold blue]Current Scene[/bold blue]", border_style="blue")
        )
        
        # Player stats table
        stats_table = Table(show_header=False, box=None)
        stats_table.add_row("❤️  HP:", f"{self.state.player.hp}/{self.state.player.max_hp}")
        stats_table.add_row("💰 Gold:", str(self.state.player.gold))
        
        self.console.print(
            Panel(stats_table, title="[bold green]Player Stats[/bold green]", border_style="green")
        )
    
    def process_action(self, player_input: str) -> bool:
        """
        Process a player action through the semantic pipeline.
        
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
        
        # Step 1: Resolve intent using semantic matching
        self.console.print("[dim]🔍 Resolving intent...[/dim]")
        
        intent_match = self.resolver.resolve_intent(player_input)
        
        if not intent_match:
            self.console.print(
                "[red]❌ I don't understand that action. Try rephrasing?[/red]"
            )
            return True
        
        self.console.print(
            f"[cyan]🎲 Intent: {intent_match.intent_id} "
            f"(confidence: {intent_match.confidence:.2f})[/cyan]"
        )
        
        # Step 2: Arbiter resolves logic (state changes)
        self.console.print("[dim]⚖️  Arbiter calculating...[/dim]")
        
        context = self.state.get_context_str()
        
        arbiter_result = self.arbiter.resolve_action_sync(
            intent_id=intent_match.intent_id,
            player_input=player_input,
            context=context,
            player_hp=self.state.player.hp,
            player_gold=self.state.player.gold
        )
        
        logger.info(
            f"Arbiter: success={arbiter_result.success}, "
            f"hp_delta={arbiter_result.hp_delta}, "
            f"npc_state={arbiter_result.new_npc_state}"
        )
        
        # Step 2.5: Quartermaster checks for loot (if investigate or force)
        loot_item = None
        if arbiter_result.success and intent_match.intent_id in ["investigate", "force"]:
            room = self.state.rooms.get(self.state.current_room)
            location_name = room.name if room else "unknown"
            loot_item = self.loot.generate_loot(
                location=location_name,
                intent=intent_match.intent_id
            )
            if loot_item:
                self.state.player.inventory.append(loot_item.name)
                logger.info(f"Loot added to inventory: {loot_item.name}")
        
        # Step 3: Update game state BEFORE narration
        # Infer target NPC
        target_npc = arbiter_result.target_npc_id
        if not target_npc:
            room = self.state.rooms.get(self.state.current_room)
            if room and room.npcs:
                for npc in room.npcs:
                    if npc.name.lower() in player_input.lower():
                        target_npc = npc.name
                        break
                
                if not target_npc and len(room.npcs) == 1:
                    target_npc = room.npcs[0].name
        
        # Apply state changes
        self.state.player.hp += arbiter_result.hp_delta
        self.state.player.gold += arbiter_result.gold_delta
        
        if target_npc:
            room = self.state.rooms.get(self.state.current_room)
            if room:
                for npc in room.npcs:
                    if npc.name == target_npc:
                        npc.state = arbiter_result.new_npc_state
                        break
        
        # Step 4: Chronicler generates narrative
        self.console.print("[dim]📖 Chronicler narrating...[/dim]")
        
        chronicler_result = self.chronicler.narrate_outcome_sync(
            player_input=player_input,
            intent_id=intent_match.intent_id,
            arbiter_result={
                'success': arbiter_result.success,
                'hp_delta': arbiter_result.hp_delta,
                'gold_delta': arbiter_result.gold_delta,
                'new_npc_state': arbiter_result.new_npc_state,
                'reasoning': arbiter_result.reasoning,
                'narrative_seed': arbiter_result.narrative_seed
            },
            context=context
        )
        
        # Step 5: Display narrative
        success_icon = "✅" if arbiter_result.success else "❌"
        narrative_color = "green" if arbiter_result.success else "yellow"
        
        # Build output with optional loot notification
        output_text = chronicler_result.narrative
        if loot_item:
            output_text += f"\n\n💎 **Loot found**: {loot_item.name} ({loot_item.description})"
            if loot_item.stat_bonus:
                output_text += f" [{loot_item.stat_bonus}]"
        
        self.console.print(
            Panel(
                output_text,
                title=f"[bold {narrative_color}]{success_icon} Outcome[/bold {narrative_color}]",
                border_style=narrative_color
            )
        )
        
        # Auto-save after each action
        self.state.save_to_file(self.save_path)
        
        # Check win/loss conditions
        if not self.state.player.is_alive():
            self.console.print(
                Panel(
                    "[bold red]You have died. Game Over.[/bold red]",
                    border_style="red"
                )
        return True
    
    def display_welcome(self):
        self.console.print(
            Panel(
                "[bold cyan]Welcome to the Semantic RPG![/bold cyan]\n\n"
                "Type natural language actions (e.g., 'I kick the table').\n"
                "Commands: [yellow]save[/yellow], [yellow]quit[/yellow]",
                border_style="cyan"
            )
        )
        
        while True:
            # Display current context
            self.console.print("\n" + "─" * 80 + "\n")
            self.display_context()
            
            # Get player input
            try:
                player_input = Prompt.ask("\n[bold]What do you do?[/bold]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            
            # Process action
            should_continue = self.process_action(player_input)
            
            if not should_continue:
                self.console.print("\n[yellow]Thanks for playing![/yellow]")
                break


def main():
    """Entry point for the game."""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Semantic RPG Core - D&D Terminal Game")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Enable auto-play mode with Voyager agent"
    )
    parser.add_argument(
        "--personality",
        choices=["curious", "aggressive", "tactical", "chaotic"],
        default="curious",
        help="Voyager personality (default: curious)"
    )
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        "game_debug.log",
        level="DEBUG",
        format="{time:HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        lambda msg: None,  # Suppress console logs (Rich handles UI)
        level="INFO"
    )
    
    # Start game
    game = GameREPL(auto_mode=args.auto)
    game.run()


if __name__ == "__main__":
    main()
