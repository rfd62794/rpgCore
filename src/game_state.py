"""
Game State Machine

Deterministic state management for RPG world, player, and NPCs.
Uses Pydantic for validation and JSON serialization.
"""

from pathlib import Path
from typing import Dict, List, Literal, Optional, Any, Tuple
import numpy as np

from loguru import logger
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid

from world_ledger import Coordinate, WorldChunk
from logic.orientation import Orientation

class Goal(BaseModel):
    """A narrative objective for the player/agent."""
    id: str
    description: str
    target_tags: List[str] = Field(default_factory=list) # Tags to look for to complete
    method_weights: Dict[str, float] = Field(default_factory=dict) # Weighting for intents
    is_completed: bool = False # Legacy, kept for compat
    status: Literal["active", "success", "failed"] = "active"
    required_intent: str | None = None # Intent that triggers completion
    target_npc_state: str | None = None # NPC state that triggers completion
    reward_gold: int = 0
    type: Literal["short", "medium", "long"] = "short"


class PlayerStats(BaseModel):
    """Player character statistics with vector trait support."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    name: str = "Adventurer"
    hp: int = Field(default=100, ge=0, le=100)
    max_hp: int = 100
    gold: int = Field(default=50, ge=0)
    inventory: List[Item] = Field(default_factory=list)
    attributes: Dict[str, int] = Field(
        default_factory=lambda: {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10
        }
    )
    
    # Additional fields for character factory
    archetype_name: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)
    skill_proficiencies: List[str] = Field(default_factory=list)
    
    # Phase 2: Vectorized World Engine fields
    vector_traits: List = Field(default_factory=list)  # Trait objects
    trait_description: Optional[str] = None  # Generated description
    
    def __init__(self, **data):
        """Initialize with constitution-based HP calculation."""
        super().__init__(**data)
        # Calculate HP based on constitution (10 + constitution modifier)
        con_mod = (self.attributes.get("constitution", 10) - 10) // 2
        self.max_hp = 10 + con_mod * 5  # 5 HP per constitution modifier
        self.hp = self.max_hp
    
    def is_alive(self) -> bool:
        """Check if player is still alive."""
        return self.hp > 0
    
    def take_damage(self, amount: int) -> None:
        """Apply damage to player."""
        self.hp = max(0, self.hp - amount)
        logger.info(f"Player took {amount} damage. HP: {self.hp}/{self.max_hp}")
    
    def heal(self, amount: int) -> None:
        """Restore player HP."""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        healed = self.hp - old_hp
        logger.info(f"Player healed for {healed}. HP: {self.hp}/{self.max_hp}")
    
    def modify_gold(self, amount: int) -> bool:
        """
        Add or remove gold.
        
        Returns:
            True if transaction succeeded, False if insufficient gold
        """
        if amount < 0 and self.gold < abs(amount):
            logger.warning(f"Insufficient gold: have {self.gold}, need {abs(amount)}")
            return False
        
        self.gold += amount
        logger.info(f"Gold {'gained' if amount > 0 else 'spent'}: {abs(amount)}. Total: {self.gold}")
        return True


class NPC(BaseModel):
    """Non-player character."""
    
    name: str
    state: Literal["neutral", "hostile", "distracted", "charmed", "dead"] = "neutral"
    hp: int = Field(default=50, ge=0)
    description: str = "An ordinary person"
    
    def is_alive(self) -> bool:
        """Check if NPC is still alive."""
        return self.state != "dead" and self.hp > 0
    
    def update_state(self, new_state: str) -> None:
        """Change NPC state (e.g., from neutral to hostile)."""
        old_state = self.state
        self.state = new_state  # type: ignore
        logger.info(f"{self.name}: {old_state} → {new_state}")


class Room(BaseModel):
    """A location in the game world."""
    
    name: str
    description: str
    npcs: List[NPC] = Field(default_factory=list)
    items: List[str] = Field(default_factory=list)
    exits: Dict[str, str] = Field(default_factory=dict)  # direction -> room_name
    tags: List[str] = Field(default_factory=list)  # Environmental affixes (e.g., "Sticky Floors", "Dimly Lit")


class Relationship(BaseModel):
    """
    NPC relationship tracking for persistent social memory.
    
    Design:
    - disposition: -100 (Hate) to 100 (Love)
    - tags: Behavioral flags like "grudge", "knows_secret", "ally"
    - last_interaction_turn: For time-based effects
    """
    disposition: int = Field(default=0, ge=-100, le=100)
    tags: List[str] = Field(default_factory=list)
    last_interaction_turn: int = 0


class GameState(BaseModel):
    """Complete state of the game world with coordinate-based persistence."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    player: PlayerStats = Field(default_factory=PlayerStats)
    position: Coordinate = Field(default_factory=lambda: Coordinate(0, 0, 0))  # x, y, time
    player_angle: float = 0.0  # Facing angle in degrees for 3D rendering
    world_time: int = 0  # Global world clock (turns since epoch)
    rooms: Dict[str, Room] = Field(default_factory=dict)  # Legacy compatibility
    turn_count: int = 0
    
    # Global standing with world powers
    reputation: Dict[str, int] = Field(
        default_factory=lambda: {
            "law": 0,
            "underworld": 0,
            "clergy": 0
        }
    )

    # Narrative Objectives (The Goal Stack)
    goal_stack: List[Goal] = Field(default_factory=list)
    completed_goals: List[str] = Field(default_factory=list)
    
    @property
    def current_goal(self) -> Goal | None:
        """Return the top (most recent) goal in the stack."""
        return self.goal_stack[-1] if self.goal_stack else None
    
    # DGT Social Graph: Location-scoped NPC relationships
    # Format: { "tavern": { "Bartender": Relationship(...), "Guard": Relationship(...) } }
    social_graph: Dict[str, Dict[str, Relationship]] = Field(default_factory=dict)
    
    # Phase 2: Vectorized World Engine fields
    latent_context: Dict[str, Any] = Field(default_factory=dict)  # Active world vectors
    lore_index: List[Dict[str, Any]] = Field(default_factory=list)  # Historical event vectors
    active_vectors: Dict[str, np.ndarray] = Field(default_factory=dict)  # Currently loaded vectors
    
    # Phase 3: Spatial-Temporal fields
    current_chunk: Optional[WorldChunk] = None  # Currently loaded world chunk
    travel_stamina: int = 100  # Constitution-based travel stamina
    last_rest_turn: int = 0  # When player last rested
    discovered_coordinates: List[Tuple[int, int]] = Field(default_factory=list)  # Discovered locations
    
    @property
    def current_room(self) -> str:
        """Legacy compatibility property."""
        if self.current_chunk:
            return self.current_chunk.name
        return "unknown"
    
    @current_room.setter
    def current_room(self, value: str):
        """Legacy compatibility setter."""
        # This is deprecated but kept for backward compatibility
        pass
    
    def get_local_context(self) -> str:
        """
        Generate scoped social context for current location only.
        
        This prevents VRAM bloat by only sending relevant NPC data to AI.
        Returns relationship tags and disposition for NPCs in current room.
        """
        local_rels = self.social_graph.get(self.current_room, {})
        
        if not local_rels:
            return ""
        
        context = "\n\nLocal Relationships:\n"
        for npc_id, rel in local_rels.items():
            if rel.tags:
                tags_str = ", ".join(rel.tags)
                context += f"  - {npc_id}: [{tags_str}] (Disposition: {rel.disposition:+d})\n"
            elif rel.disposition != 0:
                context += f"  - {npc_id}: Disposition {rel.disposition:+d}\n"
        
        return context
    
    def get_context_str(self) -> str:
        """
        Generate a text description of current context for LLM prompting.
        
        This is what the Narrative Engine sees when generating outcomes.
        """
        room = self.rooms.get(self.current_room)
        
        if not room:
            return "You are in an undefined location."
        
        context = f"Location: {room.name}\n{room.description}\n\n"
        
        if room.npcs:
            context += "NPCs present:\n"
            for npc in room.npcs:
                state_emoji = {
                    "neutral": "😐",
                    "hostile": "⚔️",
                    "distracted": "👀",
                    "charmed": "😍",
                    "dead": "💀"
                }
                emoji = state_emoji.get(npc.state, "")
                context += f"  - {npc.name} {emoji} ({npc.state}): {npc.description}\n"
        
        if room.tags:
            context += f"\nEnvironment: {', '.join(room.tags)}\n"
        
        if room.items:
            context += f"\nItems: {', '.join(room.items)}\n"
        
        # Append scoped social graph data
        context += self.get_local_context()
        
        return context
    
    def update_relationship(
        self,
        location_id: str,
        npc_id: str,
        delta_disposition: int = 0,
        new_tags: List[str] | None = None
    ) -> None:
        """
        Update NPC relationship in social graph.
        
        Args:
            location_id: Room/location identifier
            npc_id: NPC name
            delta_disposition: Change to disposition (-100 to +100)
            new_tags: Tags to add (e.g., ["grudge"], ["knows_secret"])
        """
        # Ensure location exists in graph
        if location_id not in self.social_graph:
            self.social_graph[location_id] = {}
        
        # Get or create relationship
        if npc_id not in self.social_graph[location_id]:
            self.social_graph[location_id][npc_id] = Relationship()
        
        rel = self.social_graph[location_id][npc_id]
        
        # Update disposition (clamped to -100/+100)
        rel.disposition = max(-100, min(100, rel.disposition + delta_disposition))
        
        # Add new tags (avoid duplicates)
        if new_tags:
            for tag in new_tags:
                if tag not in rel.tags:
                    rel.tags.append(tag)
        
        # Update turn counter
        rel.last_interaction_turn = self.turn_count
        
        logger.info(
            f"Relationship updated: {npc_id} @ {location_id} "
            f"(disp: {rel.disposition:+d}, tags: {rel.tags})"
        )
    
    def apply_outcome(self, outcome: "ActionOutcome", target_npc: str | None = None) -> None:  # type: ignore
        """
        Update game state based on action outcome.
        
        Args:
            outcome: Result from NarrativeEngine
            target_npc: Name of NPC to update (if applicable)
        """
        # Update player HP
        if outcome.hp_change < 0:
            self.player.take_damage(abs(outcome.hp_change))
        elif outcome.hp_change > 0:
            self.player.heal(outcome.hp_change)
        
        # Update gold
        if outcome.gold_change != 0:
            self.player.modify_gold(outcome.gold_change)
        
        # Update NPC state
        if target_npc and self.current_room in self.rooms:
            room = self.rooms[self.current_room]
            for npc in room.npcs:
                if npc.name.lower() == target_npc.lower():
                    npc.update_state(outcome.npc_state)
                    break
        
        self.turn_count += 1
    
    def save_to_file(self, path: Path) -> None:
        """Persist game state to JSON."""
        path.write_text(self.model_dump_json(indent=2))
        logger.info(f"Game saved to {path}")
    
    @classmethod
    def load_from_file(cls, path: Path) -> "GameState":
        """Load game state from JSON."""
        data = path.read_text()
        logger.info(f"Game loaded from {path}")
        return cls.model_validate_json(data)


GameState.model_rebuild()


def create_tavern_scenario() -> GameState:
    """Create a pre-configured tavern scenario for testing."""
    state = GameState()
    
    # Build the tavern room
    tavern = Room(
        name="The Rusty Flagon",
        description=(
            "A dimly lit tavern filled with the smell of ale and roasted meat. "
            "Rowdy patrons fill the wooden tables."
        ),
        npcs=[
            NPC(
                name="Guard",
                state="neutral",
                hp=80,
                description="A stern-looking town guard watching the entrance"
            ),
            NPC(
                name="Bartender",
                state="neutral",
                hp=30,
                description="A burly man wiping mugs behind the bar"
            )
        ],
        items=["wooden table", "beer mug", "chair"],
        exits={"north": "town_square", "east": "alley"},
        tags=["Sticky Floors", "Rowdy Crowd", "Dimly Lit"]  # Environmental affixes
    )
    
    state.rooms["tavern"] = tavern
    state.current_room = "tavern"
    
    return state
