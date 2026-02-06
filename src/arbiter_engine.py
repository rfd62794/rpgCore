"""
Arbiter Engine: Pure Logic and State Resolution

The Arbiter is responsible for ONLY calculating game state changes.
No storytelling - just deterministic math based on intent and context.
"""

import os
from typing import Literal

from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent


class ArbiterLogic(BaseModel):
    """Deterministic state changes from player actions."""
    
    success: bool = Field(
        description="Did the action succeed based on intent and context?"
    )
    
    hp_delta: int = Field(
        default=0,
        ge=-100,
        le=100,
        description="HP change (negative = damage, positive = healing)"
    )
    
    gold_delta: int = Field(
        default=0,
        ge=-1000,
        le=1000,
        description="Gold change (negative = spent/lost, positive = gained)"
    )
    
    target_npc_id: str | None = Field(
        default=None,
        description="ID of NPC affected by this action (if any)"
    )
    
    new_npc_state: Literal["neutral", "hostile", "distracted", "charmed", "dead"] = Field(
        default="neutral",
        description="New state of the target NPC"
    )
    
    reasoning: str = Field(
        description="Brief tactical reason for the outcome (1 sentence)"
    )
    
    narrative_seed: str = Field(
        default="",
        description="Contextual 'vibe' for the Chronicler (e.g., 'The guard is helpful but tired', 'The bartender eyes you suspiciously')"
    )


class ArbiterEngine:
    """
    The Logic Arbiter: Calculates state changes from player actions.
    
    Design:
    - Uses small, fast model (phi3:mini or llama3.2:1b)
    - Prompt focuses ONLY on game mechanics
    - No narrative generation - pure math
    """
    
    def __init__(
        self,
        model_name: str = 'ollama:llama3.2:1b'
    ):
        """
        Initialize arbiter engine.
        
        Args:
            model_name: Small, fast Ollama model for logic
        """
        # Set Ollama base URL
        if 'OLLAMA_BASE_URL' not in os.environ:
            os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
        
        system_prompt = self._build_arbiter_prompt()
        
        logger.info(f"Initializing Arbiter with {model_name}")
        
        self.agent = Agent(
            model_name,
            output_type=ArbiterLogic,
            system_prompt=system_prompt
        )
    
    def _build_arbiter_prompt(self) -> str:
        """Construct focused prompt for logic resolution."""
        return (
            "You are the ARBITER: a game logic engine for a D&D-style RPG.\n\n"
            "Your ONLY job is to calculate state changes. DO NOT write narrative.\n\n"
            "Rules:\n"
            "- Analyze the player's intent and context\n"
            "- Decide: did the action succeed? (success: bool)\n"
            "- Calculate HP/Gold changes (delta values)\n"
            "- Determine NPC state changes\n"
            "- Provide a narrative_seed (1 phrase describing the vibe/mood)\n"
            "- ALWAYS check Room Environment tags for modifiers\n"
            "- PRIORITIZE relationship tags when calculating success\n\n"
            "Environmental Tag Logic (Room Properties):\n"
            "- 'Sticky Floors': -10% success to finesse/stealth actions\n"
            "- 'Dimly Lit': +10% success to finesse/stealth, -10% to investigate\n"
            "- 'Rowdy Crowd': +10% success to distract, -10% to charm (noise)\n"
            "- 'Slippery': -10% success to force/combat actions\n"
            "- 'Open Space': +10% success to force, -10% to finesse (no cover)\n\n"
            "NPC Tag Behavioral Logic:\n"
            "- If NPC has 'grudge' or negative disposition: Lower success for charm\n"
            "- If NPC has 'knows_secret' tag: Success on investigate/charm reveals it\n"
            "- If NPC has 'ally' tag: Bonus to all social interactions\n\n"
            "Examples:\n"
            "- 'finesse' in room with 'Sticky Floors' → success: False, narrative_seed: 'Your boot squeaks on the tacky floor'\n"
            "- 'distract' in 'Rowdy Crowd' → success: True, narrative_seed: 'Your shout blends perfectly with the chaos'\n"
            "- 'charm' intent with [knows_secret] tag → success: True, narrative_seed: 'The janitor leans in and whispers'\n\n"
            "CRITICAL: Even simple social actions should have success: True (unless tags/environment prevent it).\n"
            "Always provide a narrative_seed that gives the Chronicler flavor.\n"
            "DO NOT default to 'nothing happens'.\n"
        )
    
    async def resolve_action(
        self,
        intent_id: str,
        player_input: str,
        context: str,
        player_hp: int = 100,
        player_gold: int = 0
    ) -> ArbiterLogic:
        """
        Calculate state changes for a player action.
        
        Args:
            intent_id: Resolved intent (e.g., 'distract', 'charm')
            player_input: Original player text
            context: Room description and NPC states
            player_hp: Current player HP
            player_gold: Current player gold
        
        Returns:
            ArbiterLogic with state deltas and success flag
        """
        prompt = (
            f"Context: {context}\n\n"
            f"Player Stats: HP={player_hp}, Gold={player_gold}\n\n"
            f"Player Action: \"{player_input}\"\n"
            f"Resolved Intent: {intent_id}\n\n"
            f"Calculate the state changes:"
        )
        
        logger.debug(f"Arbiter resolving intent '{intent_id}'")
        
        try:
            result = await self.agent.run(prompt)
            logic = result.data
            
            logger.info(
                f"Arbiter: success={logic.success}, "
                f"hp_delta={logic.hp_delta}, "
                f"npc_state={logic.new_npc_state}"
            )
            return logic
            
        except Exception as e:
            logger.error(f"Arbiter failed: {e}")
            
            # Deterministic fallback
            return self._fallback_logic(intent_id)
    
    def _fallback_logic(self, intent_id: str) -> ArbiterLogic:
        """Deterministic fallback if LLM fails."""
        logger.warning("Using fallback arbiter logic")
        
        fallbacks = {
            "distract": ArbiterLogic(
                success=True,
                new_npc_state="distracted",
                reasoning="Distraction drew attention"
            ),
            "force": ArbiterLogic(
                success=True,
                hp_delta=-10,
                new_npc_state="hostile",
                reasoning="Direct attack landed"
            ),
            "charm": ArbiterLogic(
                success=True,
                reasoning="Social interaction succeeded"
            ),
            "finesse": ArbiterLogic(
                success=True,
                reasoning="Stealthy action executed"
            )
        }
        
        return fallbacks.get(
            intent_id,
            ArbiterLogic(success=True, reasoning="Action attempted")
        )
