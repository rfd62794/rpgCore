"""
Quartermaster: Deterministic Logic Engine

Separates "Hard Math" from "Soft Logic".
Calculates final outcomes based on:
1. Base Difficulty (from Arbiter/Context)
2. Environmental Tags (Room properties)
3. Player Stats & Inventory
4. Dice Rolls (d20)
"""

import random
from dataclasses import dataclass
from typing import List, Dict, Optional, Literal

from loguru import logger
from pydantic import BaseModel, Field


class QuartermasterOutcome(BaseModel):
    """Final calculated outcome of an action."""
    
    success: bool
    total_score: int
    difficulty_class: int
    hp_delta: int = 0
    gold_delta: int = 0
    narrative_context: str = ""  # Explanation for the Chronicler (e.g., "Slipped on sticky floor")


class Quartermaster:
    """
    The Quartermaster handles all deterministic math.
    
    It takes the Arbiter's "Vibe Check" (difficulty mod) and combines it
    with hardcoded tag logic to produce a final True/False result.
    """
    
    def __init__(self):
        self.base_dc = 10  # Standard difficulty
    
    def calculate_outcome(
        self,
        intent_id: str,
        room_tags: List[str],
        base_difficulty: int = 10,
        arbiter_mod: int = 0,
        player_stats: Dict[str, int] | None = None
    ) -> QuartermasterOutcome:
        """
        Resolve the final outcome of an action.
        
        Formula:
        Roll (d20) + Player Bonus + Tag Modifiers >= Base DC + Arbiter Mod
        """
        
        # 1. Calculate Target Number (DC)
        # Arbiter mod: Positive = Harder, Negative = Easier
        target_dc = base_difficulty + arbiter_mod
        
        # 2. Calculate Modifiers from Tags
        tag_mod, tag_reason = self._calculate_tag_modifiers(intent_id, room_tags)
        
        # 2b. Calculate Attribute Bonus
        attr_bonus = 0
        attr_reason = ""
        if player_stats:
            attr_name, attr_val = self._get_attribute_bonus(intent_id, player_stats)
            if attr_val != 0:
                attr_bonus = attr_val
                attr_reason = f"{attr_name.title()} ({attr_val:+d})"
        
        # 3. Roll the Die
        d20_roll = random.randint(1, 20)
        
        # 4. Total Score
        total_score = d20_roll + attr_bonus + tag_mod
        
        # 5. Determine Success
        success = total_score >= target_dc
        
        # 6. Calculate Crit/Fail consequences (HP/Gold)
        hp_delta = 0
        if not success:
            # Standard failure damage
            margin = target_dc - total_score
            if margin >= 5: # Bad fail
                hp_delta = -random.randint(5, 10)
            else: # Near miss
                hp_delta = -random.randint(1, 4)
        
        # Log the math for debugging
        log_msg = (
            f"Action: {intent_id} | Tags: {room_tags} | "
            f"Roll: {d20_roll} + Bonus: {attr_bonus} + TagMod: {tag_mod} = {total_score} "
            f"vs DC: {target_dc} ({base_difficulty} + {arbiter_mod}) -> "
            f"{'SUCCESS' if success else 'FAILURE'}"
        )
        logger.debug(log_msg)

        
        # Construct narrative context
        context_parts = []
        if tag_reason:
            context_parts.append(tag_reason)
        if attr_reason:
            context_parts.append(attr_reason)
        context_parts.append(f"Rolled {d20_roll}")
        
        return QuartermasterOutcome(
            success=success,
            total_score=total_score,
            difficulty_class=target_dc,
            hp_delta=hp_delta,
            narrative_context=" | ".join(context_parts)
        )

    def _get_attribute_bonus(self, intent_id: str, stats: Dict[str, int]) -> tuple[str, int]:
        """Map intent to primary attribute."""
        intent = intent_id.lower()
        
        # Mapping Logic
        mapping = {
            "force": "strength",
            "combat": "strength",
            "athletics": "strength",
            
            "finesse": "dexterity",
            "stealth": "dexterity",
            "acrobatics": "dexterity",
            
            "investigate": "intelligence",
            "search": "intelligence",
            "perception": "intelligence",
            
            "charm": "charisma",
            "persuade": "charisma",
            "social": "charisma",
            "distract": "charisma"
        }
        
        attr_name = mapping.get(intent, "luck") # Default to luck (0) if unknown
        return attr_name, stats.get(attr_name, 0)

    def _calculate_tag_modifiers(self, intent_id: str, tags: List[str]) -> tuple[int, str]:
        """
        Apply deterministic tag logic.
        Returns: (modifier_value, reason_string)
        """
        modifier = 0
        reasons = []
        
        # Lowercase for consistent matching
        tags = [t.lower() for t in tags]
        intent = intent_id.lower()
        
        # --- Environment Logic ---
        
        # Sticky Floors
        if "sticky floors" in tags:
            if intent in ["finesse", "stealth", "acrobatics"]:
                modifier -= 5
                reasons.append("Sticky floors hindered movement")
            elif intent in ["force", "combat"]:
                modifier += 2
                reasons.append("Good footing on sticky floor")
                
        # Dimly Lit
        if "dimly lit" in tags:
            if intent in ["investigate", "perception", "search"]:
                modifier -= 5
                reasons.append("Too dark to see clearly")
            elif intent in ["stealth", "finesse"]:
                modifier += 5
                reasons.append("Shadows provided cover")
                
        # Rowdy Crowd
        if "rowdy crowd" in tags:
            if intent in ["charm", "social", "persuade"]:
                modifier -= 2
                reasons.append("Crowd noise drowned you out")
            elif intent in ["distract", "stealth"]:
                modifier += 5
                reasons.append("Chaos masked your actions")
                
        # Slippery
        if "slippery" in tags:
            if intent in ["force", "combat", "athletics"]:
                modifier -= 5
                reasons.append("Slipped on wet surface")
            elif intent in ["finesse"]:
                modifier -= 2
                reasons.append("Hard to keep balance")

        # Open Space
        if "open space" in tags:
            if intent in ["stealth", "hide"]:
                modifier -= 5
                reasons.append("No cover available")
            elif intent in ["force", "combat"]:
                modifier += 2
                reasons.append("Room to maneuver")
        
        return modifier, "; ".join(reasons)
