"""
Unified SimulatorHost - Single Source of Truth

ADR 043: The "Great Pruning" & Unified Controller

This is the ONLY place where game_state lives. It runs at 30 FPS and
orchestrates the D20 math and PPU tile-updates simultaneously.
Both Terminal and GUI views observe this single simulation.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Protocol, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from game_state import GameState, create_tavern_scenario
from semantic_engine import SemanticResolver, create_default_intent_library
from deterministic_arbiter import DeterministicArbiter
from sync_engines import ChroniclerEngine
from quartermaster import Quartermaster
from loot_system import LootSystem
from core.world_map import get_world_map, EnvironmentType


class ViewMode(Enum):
    """Available view modes for the simulator."""
    TERMINAL = "terminal"
    GUI = "gui"
    BOTH = "both"


@dataclass
class ActionResult:
    """Result of a player action processed by the simulator."""
    success: bool
    prose: str
    intent: str
    hp_delta: int
    gold_delta: int
    new_npc_state: Optional[str]
    target_npc: Optional[str]
    turn_count: int
    narrative_seed: str
    room_changed: bool = False
    new_room: Optional[str] = None


@dataclass
class LLMResponse:
    """Structured LLM response with intent tagging."""
    prose: str
    intent: str
    confidence: float
    reasoning: Optional[str] = None


class Observer(Protocol):
    """Protocol for view observers."""
    
    def on_state_changed(self, state: GameState) -> None:
        """Called when game state changes."""
        ...
    
    def on_action_result(self, result: ActionResult) -> None:
        """Called when an action is processed."""
        ...
    
    def on_narrative_generated(self, prose: str) -> None:
        """Called when narrative is generated."""
        ...


class IntentTaggingProtocol:
    """
    Bridge between heuristic LLM output and deterministic D20 core.
    
    Enforces strict intent tagging to prevent LLM from hallucinating stats.
    """
    
    VALID_INTENTS = {
        "attack", "talk", "investigate", "use", "leave_area", 
        "trade", "steal", "force", "rest", "help"
    }
    
    def __init__(self):
        self.semantic_resolver = SemanticResolver(
            create_default_intent_library(), 
            confidence_threshold=0.35
        )
    
    def parse_player_input(self, player_input: str) -> LLMResponse:
        """
        Parse player input and extract intent with structured output.
        
        Args:
            player_input: Raw player input string
            
        Returns:
            Structured response with intent tag
        """
        # Use semantic resolver to get intent
        intent_match = self.semantic_resolver.resolve_intent(player_input)
        
        if not intent_match:
            return LLMResponse(
                prose="I don't understand that action. Try rephrasing?",
                intent="unknown",
                confidence=0.0
            )
        
        # Generate basic prose from intent (will be enhanced by Chronicler)
        prose_templates = {
            "attack": "You prepare to attack",
            "talk": "You attempt to talk",
            "investigate": "You investigate the area",
            "use": "You use an item",
            "leave_area": "You prepare to leave",
            "trade": "You attempt to trade",
            "steal": "You attempt to steal",
            "force": "You try to force something",
            "rest": "You take a rest",
            "help": "You ask for help"
        }
        
        prose = prose_templates.get(intent_match.intent_id, "You act")
        
        return LLMResponse(
            prose=prose,
            intent=intent_match.intent_id,
            confidence=intent_match.confidence,
            reasoning=intent_match.reasoning
        )
    
    def validate_intent(self, intent: str) -> bool:
        """Validate intent against allowed set."""
        return intent in self.VALID_INTENTS


class SimulatorHost:
    """
    Unified SimulatorHost - Single Source of Truth
    
    This is the ONLY place where game_state lives. It runs at 30 FPS and
    orchestrates the D20 math and PPU tile-updates simultaneously.
    """
    
    def __init__(self, save_path: Optional[Path] = None):
        """Initialize the unified simulator."""
        self.save_path = save_path or Path("savegame.json")
        
        # Single source of truth for game state
        self.state: Optional[GameState] = None
        
        # Observer pattern for views
        self.observers: List[Observer] = []
        
        # Core engines (Council of Three)
        self.intent_protocol = IntentTaggingProtocol()
        self.arbiter: Optional[DeterministicArbiter] = None
        self.chronicler: Optional[ChroniclerEngine] = None
        self.quartermaster: Optional[Quartermaster] = None
        self.loot_system: Optional[LootSystem] = None
        
        # World map for spatial authority
        self.world_map = get_world_map()
        
        # View management
        self.views: List[SimulatorView] = []
        self.view_mode: ViewMode = ViewMode.TERMINAL
        
        # Timing and loop control
        self.target_fps = 30
        self.frame_time = 1.0 / self.target_fps
        self.running = False
        self.last_frame_time = 0
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Action queue for processing
        self.action_queue: asyncio.Queue[str] = asyncio.Queue()
        
        # Autonomous mode flag
        self.is_autonomous = False
        
        logger.info("🏛️ SimulatorHost initialized - Single Source of Truth")
    
    def add_observer(self, observer: Observer) -> None:
        """Add a view observer."""
        self.observers.append(observer)
        logger.debug(f"👁️ Added observer: {type(observer).__name__}")
    
    def remove_observer(self, observer: Observer) -> None:
        """Remove a view observer."""
        if observer in self.observers:
            self.observers.remove(observer)
            logger.debug(f"👁️ Removed observer: {type(observer).__name__}")
    
    def notify_state_changed(self) -> None:
        """Notify all observers of state change."""
        if self.state:
            for observer in self.observers:
                try:
                    observer.on_state_changed(self.state)
                except Exception as e:
                    logger.error(f"❌ Observer notification failed: {e}")
    
    def notify_action_result(self, result: ActionResult) -> None:
        """Notify all observers of action result."""
        for observer in self.observers:
            try:
                observer.on_action_result(result)
            except Exception as e:
                logger.error(f"❌ Observer notification failed: {e}")
    
    def notify_narrative(self, prose: str) -> None:
        """Notify all observers of narrative generation."""
        for observer in self.observers:
            try:
                observer.on_narrative_generated(prose)
            except Exception as e:
                logger.error(f"❌ Observer notification failed: {e}")
    
    def initialize(self) -> bool:
        """
        Initialize the simulator with all engines and game state.
        
        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            logger.info("🚀 Initializing SimulatorHost...")
            
            # Load or create game state
            if self.save_path.exists():
                logger.info(f"📁 Loading saved game from {self.save_path}")
                self.state = GameState.load_from_file(self.save_path)
            else:
                logger.info("🆕 Creating new game state")
                self.state = create_tavern_scenario()
            
            # Initialize engines
            logger.info("⚖️ Loading Arbiter (Deterministic Logic Core)...")
            self.arbiter = DeterministicArbiter()
            
            logger.info("📖 Loading Chronicler (Narrative Engine)...")
            self.chronicler = ChroniclerEngine(
                model_name='ollama:llama3.2:1b', 
                tone='humorous'
            )
            
            logger.info("🎲 Loading Quartermaster...")
            self.quartermaster = Quartermaster()
            
            logger.info("💎 Loading Loot System...")
            self.loot_system = LootSystem()
            
            # Notify observers of initial state
            self.notify_state_changed()
            
            logger.info("✅ SimulatorHost initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ SimulatorHost initialization failed: {e}")
            return False
    
    async def process_action(self, player_input: str) -> ActionResult:
        """
        Process a player action through the unified pipeline.
        
        Args:
            player_input: Raw player input string
            
        Returns:
            ActionResult with all outcome data
        """
        if not self.state or not self.arbiter or not self.chronicler or not self.quartermaster:
            raise RuntimeError("Simulator not properly initialized")
        
        try:
            # Step 1: Parse intent with strict tagging
            logger.debug(f"🔍 Parsing intent for: {player_input}")
            llm_response = self.intent_protocol.parse_player_input(player_input)
            
            if not self.intent_protocol.validate_intent(llm_response.intent):
                return ActionResult(
                    success=False,
                    prose="I don't understand that action. Try rephrasing?",
                    intent="unknown",
                    hp_delta=0,
                    gold_delta=0,
                    new_npc_state=None,
                    target_npc=None,
                    turn_count=self.state.turn_count,
                    narrative_seed="invalid_action"
                )
            
            # Step 2: Arbiter resolves logic (deterministic D20 math)
            logger.debug(f"⚖️ Arbiter resolving: {llm_response.intent}")
            context = self.state.get_context_str()
            room = self.state.rooms.get(self.state.current_room)
            room_tags = room.tags if room else []
            
            arbiter_result = self.arbiter.resolve_action_sync(
                intent_id=llm_response.intent,
                player_input=player_input,
                context=context,
                room_tags=room_tags,
                reputation=self.state.reputation,
                player_hp=self.state.player.hp
            )
            
            # Step 3: Quartermaster calculates outcome (deterministic dice)
            logger.debug("🎲 Quartermaster calculating outcome...")
            outcome = self.quartermaster.calculate_outcome(
                intent_id=llm_response.intent,
                room_tags=room_tags,
                arbiter_mod=arbiter_result.difficulty_mod,
                player_stats=self.state.player.attributes,
                inventory_items=self.state.player.inventory
            )
            
            # Step 4: Apply state changes (BEFORE narration)
            logger.debug("🔄 Applying state changes...")
            
            # HP changes
            if outcome.hp_delta != 0:
                if outcome.hp_delta < 0:
                    self.state.player.take_damage(abs(outcome.hp_delta))
                else:
                    self.state.player.heal(outcome.hp_delta)
            
            # Social consequences
            self.arbiter.apply_social_consequences(
                self.state, 
                arbiter_result, 
                success=outcome.success
            )
            
            # Position changes (POSITIONAL AUTHORITY)
            room_changed = False
            new_room = None
            position_changed = False
            
            if llm_response.intent == "leave_area":
                # Handle room transitions AND coordinate mutation
                if room and room.exits:
                    next_room_id = list(room.exits.values())[0]
                    self.state.current_room = next_room_id
                    room_changed = True
                    new_room = next_room_id
                    logger.info(f"🚙️ Transitioned to {next_room_id}")
                else:
                    # If no room exits, treat as movement and update coordinates
                    direction = self._extract_direction_from_input(player_input)
                    if direction != "here":
                        self._update_voyager_position(direction)
                        position_changed = True
                        logger.info(f"🚶️ Voyager moved {direction} (leave_area intent)")
            elif llm_response.intent in ["move", "travel", "go", "walk"]:
                # Extract direction from action input for position update
                direction = self._extract_direction_from_input(player_input)
                self._update_voyager_position(direction)
                position_changed = True
                logger.info(f"🚶️ Voyager moved {direction}")
            
            # BIOME TRANSITION HOOK: Update location if position changed
            if position_changed:
                self._update_location_context()
                self._check_spatial_transitions()
            
            # Loot generation
            loot_item = None
            if outcome.success and llm_response.intent in ["investigate", "force"]:
                location_name = room.name if room else "unknown"
                loot_item = self.loot_system.generate_loot(
                    location=location_name,
                    intent=llm_response.intent
                )
                if loot_item:
                    self.state.player.inventory.append(loot_item)
            
            # Step 5: Generate narrative (async)
            logger.debug("📖 Generating narrative...")
            
            # Collect narrative tokens properly
            narrative_text = ""
            narrative_stream = self.chronicler.narrate_stream(
                player_input=player_input,
                intent_id=llm_response.intent,
                arbiter_result={
                    'success': outcome.success,
                    'hp_delta': outcome.hp_delta,
                    'gold_delta': outcome.gold_delta,
                    'new_npc_state': arbiter_result.new_npc_state,
                    'reasoning': f"{arbiter_result.reasoning}. {outcome.narrative_context}",
                    'narrative_seed': arbiter_result.narrative_seed
                },
                context=context
            )
            
            async for token in narrative_stream:
                narrative_text += token
            
            # Add loot notification to narrative
            if loot_item:
                narrative_text += f"\n\n💎 **Loot found**: {loot_item.name} ({loot_item.description})"
                if loot_item.stat_bonus:
                    narrative_text += f" [{loot_item.stat_bonus}]"
            
            # Step 6: Create result object
            result = ActionResult(
                success=outcome.success,
                prose=narrative_text,
                intent=llm_response.intent,
                hp_delta=outcome.hp_delta,
                gold_delta=outcome.gold_delta,
                new_npc_state=arbiter_result.new_npc_state,
                target_npc=arbiter_result.target_npc,
                turn_count=self.state.turn_count,
                narrative_seed=arbiter_result.narrative_seed,
                room_changed=room_changed,
                new_room=new_room
            )
            
            # Step 7: Update turn count and save
            self.state.turn_count += 1
            self.state.save_to_file(self.save_path)
            
            # Step 8: Notify observers
            self.notify_action_result(result)
            self.notify_narrative(narrative_text)
            self.notify_state_changed()
            
            logger.info(f"✅ Action processed: {llm_response.intent} -> {'SUCCESS' if outcome.success else 'FAILURE'}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Action processing failed: {e}")
            # Return error result
            return ActionResult(
                success=False,
                prose=f"Error processing action: {str(e)}",
                intent="error",
                hp_delta=0,
                gold_delta=0,
                new_npc_state=None,
                target_npc=None,
                turn_count=self.state.turn_count if self.state else 0,
                narrative_seed="error"
            )
    
    async def game_loop(self) -> None:
        """Main 30 FPS game loop."""
        logger.info("🎮 Starting 30 FPS game loop")
        
        self.running = True
        self.last_frame_time = time.time()
        
        while self.running:
            current_time = time.time()
            delta_time = current_time - self.last_frame_time
            
            if delta_time >= self.frame_time:
                # Process any queued actions
                try:
                    player_input = self.action_queue.get_nowait()
                    await self.process_action(player_input)
                except asyncio.QueueEmpty:
                    # No actions to process, just update display
                    self.notify_state_changed()
                
                self.last_frame_time = current_time
            
            # Small sleep to prevent busy waiting
            await asyncio.sleep(0.001)
        
        logger.info("⏹️ Game loop stopped")
    
    def submit_action(self, player_input: str) -> None:
        """
        Submit a player action for processing.
        
        Args:
            player_input: Raw player input string
        """
        try:
            asyncio.create_task(self.action_queue.put(player_input))
            logger.debug(f"📤 Action queued: {player_input}")
        except Exception as e:
            logger.error(f"❌ Failed to queue action: {e}")
    
    def start(self) -> None:
        """Start the simulator."""
        if not self.initialize():
            raise RuntimeError("Failed to initialize simulator")
        
        # Start game loop in background
        asyncio.create_task(self.game_loop())
        logger.info("🚀 SimulatorHost started")
    
    def _extract_direction_from_input(self, player_input: str) -> str:
        """Extract direction from player input string."""
        player_input = player_input.lower()
        
        # Common direction patterns
        if "north" in player_input:
            return "north"
        elif "south" in player_input:
            return "south"
        elif "east" in player_input:
            return "east"
        elif "west" in player_input:
            return "west"
        elif "northeast" in player_input:
            return "northeast"
        elif "northwest" in player_input:
            return "northwest"
        elif "southeast" in player_input:
            return "southeast"
        elif "southwest" in player_input:
            return "southwest"
        else:
            return "here"
    
    def _update_voyager_position(self, direction: str) -> None:
        """Update Voyager position based on direction."""
        if not self.state:
            return
        
        current_x, current_y = self.state.position.x, self.state.position.y
        
        # Calculate new position
        new_x, new_y = current_x, current_y
        
        if direction == "north":
            new_y = current_y - 1
        elif direction == "south":
            new_y = current_y + 1
        elif direction == "east":
            new_x = current_x + 1
        elif direction == "west":
            new_x = current_x - 1
        elif direction == "northeast":
            new_x = current_x + 1
            new_y = current_y - 1
        elif direction == "northwest":
            new_x = current_x - 1
            new_y = current_y - 1
        elif direction == "southeast":
            new_x = current_x + 1
            new_y = current_y + 1
        elif direction == "southwest":
            new_x = current_x - 1
            new_y = current_y + 1
        
        # Update position
        self.state.position.x = new_x
        self.state.position.y = new_y
        
        logger.debug(f"📍 Voyager position updated to ({new_x}, {new_y})")
    
    def _update_location_context(self) -> None:
        """Update location context based on current position."""
        if not self.state:
            return
        
        try:
            from logic.location_resolver import LocationResolverFactory
            resolver = LocationResolverFactory.create_location_resolver()
            
            # Get current location
            location_id = resolver.get_location_at(self.state.position.x, self.state.position.y)
            if location_id:
                location_data = resolver.get_location_data(location_id)
                if location_data:
                    # Update state with location information
                    self.state.current_location = location_data.name
                    logger.info(f"🗺️ Location updated: {location_data.name}")
                    
                    # Add discovered coordinate
                    coord = (self.state.position.x, self.state.position.y)
                    if coord not in self.state.discovered_coordinates:
                        self.state.discovered_coordinates.append(coord)
                        logger.debug(f"🗺️ Discovered new coordinate: {coord}")
                else:
                    logger.debug(f"🗺️ No location data found for {location_id}")
            else:
                logger.debug(f"🗺️ No location found at ({self.state.position.x}, {self.state.position.y})")
                
        except Exception as e:
            logger.error(f"❌ Failed to update location context: {e}")
    
    def stop(self) -> None:
        """Stop the simulator."""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("🛑 SimulatorHost stopped")
    
    def get_state(self) -> Optional[GameState]:
        """Get current game state (read-only)."""
        return self.state
    
    def is_running(self) -> bool:
        """Check if simulator is running."""
        return self.running
