"""
Deterministic Arbiter: Rule-based Logic Core (Iron Frame)

Replaces ArbiterEngine (LLM) with hardcoded rules.
- Maps intents & tags to difficulty modifiers.
- Manages NPC state transitions.
- Provides static narrative seeds for the Chronicler.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from quartermaster import DC_TABLE
from loguru import logger

class ArbiterLogic(BaseModel):
    """Contextual evaluation (Deterministic version)."""
    
    difficulty_mod: int = Field(default=0)
    internal_logic: str = Field(description="Step-by-step reasoning (Hardcoded)")
    target_npc_id: Optional[str] = None
    new_npc_state: Literal["neutral", "hostile", "distracted", "charmed", "dead"] = "neutral"
    reasoning: str = Field(description="Brief tactical reason")
    narrative_seed: str = Field(default="")

class DeterministicArbiter:
    """
    Standardizes game logic into a predictable rule-based system.
    Eliminates VRAM usage for the logic layer.
    """
    
    def __init__(self):
        logger.info("Deterministic Arbiter (Iron Frame) initialized.")

    def resolve_action(
        self,
        intent_id: str,
        player_input: str,
        context: str, # Mostly for logging/compat
        room_tags: List[str]
    ) -> ArbiterLogic:
        """
        Evaluate difficulty mod and NPC state using DC_TABLE and rules.
        """
        intent = intent_id.lower()
        
        # 1. Calculate Difficulty Mod based on Room Tags
        # This mirrors the logic in Quartermaster but provides the 'Arbiter' half
        difficulty_mod = 0
        reasons = []
        
        modifiers = DC_TABLE.get("modifiers", {})
        for tag in room_tags:
            norm_tag = tag.lower().replace(" ", "_")
            if norm_tag in modifiers:
                tag_mods = modifiers[norm_tag]
                if intent in tag_mods:
                    mod = tag_mods[intent]
                    # Arbiter mod is the INVERSE of DC mod in terms of "difficulty"
                    # If tag makes DC +5, difficulty_mod is +5.
                    difficulty_mod += mod
                    reasons.append(f"{tag.title()} impact: {mod:+d}")

        # 2. State Rules
        new_npc_state = "neutral"
        if "hostile" in context.lower():
            new_npc_state = "hostile"
            
        if intent == "combat":
            new_npc_state = "hostile"
            difficulty_mod += 2 # Combat is inherently tense
        elif intent == "distract":
            new_npc_state = "distracted"
        elif intent == "charm":
            # If they are already hostile, charm is harder
            if new_npc_state == "hostile":
                difficulty_mod += 5
            new_npc_state = "charmed"

        # 3. Build Logic Trace
        internal_logic = f"Deterministic Logic: Intent '{intent}' evaluated against tags {room_tags}. "
        if reasons:
            internal_logic += " | ".join(reasons)
        else:
            internal_logic += "Standard environmental conditions."
            
        reasoning = f"Calculated base resolution for {intent}."

        # 4. Narrative Seed (Static hints for Chronicler)
        seeds = {
            "force": "A display of raw power.",
            "combat": "The air crackles with aggression.",
            "finesse": "A delicate, precise movement.",
            "investigate": "A keen eye for detail.",
            "charm": "A silver-tongued approach.",
            "stealth": "A shadow in the corner.",
            "distract": "A clever diversion."
        }
        seed = seeds.get(intent, "A standard attempt.")

        return ArbiterLogic(
            difficulty_mod=difficulty_mod,
            internal_logic=internal_logic,
            new_npc_state=new_npc_state, # type: ignore
            reasoning=reasoning,
            narrative_seed=seed
        )

    def resolve_action_sync(self, *args, **kwargs) -> ArbiterLogic:
        """Sync compat wrapper."""
        return self.resolve_action(*args, **kwargs)
