"""
D20 Core: Deterministic D&D Rules Engine

The Heart of the Iron Frame - pure deterministic D&D logic.
No LLMs allowed here. Only math, rules, and state transitions.

Responsibilities:
- Dice rolling (d20 + modifiers)
- HP calculations
- Reputation changes
- Relationship state transitions
- Goal completion verification
"""

import random
from typing import Dict, List, Optional, Literal, Tuple
from dataclasses import dataclass

from loguru import logger
from pydantic import BaseModel, Field

from game_state import GameState, Goal, NPC
from quartermaster import DC_TABLE


@dataclass
class D20Result:
    """Result of a D20 resolution - pure data, no narrative."""
    success: bool
    roll: int
    total_score: int
    difficulty_class: int
    hp_delta: int
    reputation_deltas: Dict[str, int]
    relationship_changes: Dict[str, Dict]  # npc_id -> {disposition: int, tags: List[str]}
    npc_state_changes: Dict[str, str]  # npc_id -> new_state
    goals_completed: List[str]  # goal IDs
    narrative_context: str  # Technical explanation for Chronicler
    advantage_type: Optional[str] = None  # "advantage", "disadvantage", or None
    raw_rolls: Optional[Tuple[int, int]] = None  # For advantage/disadvantage transparency
    
    def string_summary(self) -> str:
        """
        Create a formatted string summary for UI display.
        
        Returns:
            Human-readable summary of the D20 resolution
        """
        parts = []
        
        # Roll information with advantage/disadvantage
        if self.advantage_type and self.raw_rolls:
            if self.advantage_type == "advantage":
                parts.append(f"🎲 Advantage: {self.raw_rolls[0]} & {self.raw_rolls[1]} → {self.roll}")
            else:
                parts.append(f"🎲 Disadvantage: {self.raw_rolls[0]} & {self.raw_rolls[1]} → {self.roll}")
        else:
            parts.append(f"🎲 Roll: {self.roll}")
        
        # Success/failure
        result_text = "✅ SUCCESS" if self.success else "❌ FAILURE"
        result_color = "green" if self.success else "red"
        parts.append(f"[{result_color}]{result_text}[/{result_color}]")
        
        # Math breakdown
        parts.append(f"Total: {self.total_score} vs DC {self.difficulty_class}")
        
        # Consequences
        if self.hp_delta != 0:
            hp_color = "red" if self.hp_delta < 0 else "green"
            hp_symbol = "+" if self.hp_delta > 0 else ""
            parts.append(f"[{hp_color}]HP: {hp_symbol}{self.hp_delta}[/{hp_color}]")
        
        # Reputation changes
        for faction, delta in self.reputation_deltas.items():
            if delta != 0:
                rep_color = "red" if delta < 0 else "green"
                rep_symbol = "+" if delta > 0 else ""
                faction_name = faction.replace("_", " ").title()
                parts.append(f"[{rep_color}]⚖️ {faction_name}: {rep_symbol}{delta}[/{rep_color}]")
        
        # State changes
        for npc_id, new_state in self.npc_state_changes.items():
            parts.append(f"[yellow]{npc_id} → {new_state}[/yellow]")
        
        # Goals completed
        if self.goals_completed:
            for goal_id in self.goals_completed:
                parts.append(f"[green]✨ Goal: {goal_id}[/green]")
        
        return " | ".join(parts)


class D20Resolver:
    """
    Deterministic D&D rulebook implementation.
    
    This is the ONLY place where game mechanics are calculated.
    All other modules just orchestrate or narrate.
    """
    
    def __init__(self):
        logger.info("D20 Core initialized - deterministic rules engine ready")
    
    def _roll_dice(self, advantage_type: Optional[str] = None) -> Tuple[int, Optional[Tuple[int, int]]]:
        """
        Roll dice with advantage/disadvantage logic.
        
        Args:
            advantage_type: "advantage", "disadvantage", or None
            
        Returns:
            Tuple of (final_roll, raw_rolls_for_transparency)
        """
        if advantage_type == "advantage":
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            final_roll = max(roll1, roll2)
            return final_roll, (roll1, roll2)
        elif advantage_type == "disadvantage":
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            final_roll = min(roll1, roll2)
            return final_roll, (roll1, roll2)
        else:
            roll = random.randint(1, 20)
            return roll, None
    
    def resolve_action(
        self,
        intent_id: str,
        player_input: str,
        game_state: GameState,
        room_tags: List[str],
        target_npc: Optional[str] = None
    ) -> D20Result:
        """
        Core resolution: Roll(d20) + Modifiers vs DC.
        
        Returns pure deterministic results for the orchestrator.
        """
        # 1. Calculate Difficulty Class
        dc, dc_reasoning = self._calculate_difficulty_class(intent_id, room_tags)
        
        # 2. Calculate player modifiers
        attribute_bonus, attr_name = self._get_attribute_bonus(intent_id, game_state.player.attributes)
        item_bonus = self._calculate_item_bonus(intent_id, game_state.player.inventory)
        
        # 3. Determine advantage/disadvantage based on state
        advantage_type = self._determine_advantage(intent_id, game_state, room_tags, target_npc)
        
        # 4. Roll the dice with advantage/disadvantage
        d20_roll, raw_rolls = self._roll_dice(advantage_type)
        
        # 5. Calculate total
        total_score = d20_roll + attribute_bonus + item_bonus
        
        # 6. Determine success
        success = total_score >= dc
        
        # 7. Calculate consequences
        hp_delta = self._calculate_hp_delta(success, total_score, dc)
        reputation_deltas = self._calculate_reputation_changes(intent_id, success, target_npc)
        relationship_changes = self._calculate_relationship_changes(intent_id, success, target_npc)
        npc_state_changes = self._calculate_npc_state_changes(intent_id, success, target_npc, game_state)
        goals_completed = self._check_goal_completion(intent_id, success, game_state, player_input)
        
        # 8. Build narrative context (technical, not creative)
        narrative_parts = [
            f"Roll: {d20_roll}",
            f"{attr_name.title()}: {attribute_bonus:+d}" if attribute_bonus != 0 else "",
            f"Items: {item_bonus:+d}" if item_bonus != 0 else "",
            f"vs DC {dc}",
            dc_reasoning
        ]
        
        # Add advantage/disadvantage info
        if advantage_type:
            narrative_parts.insert(0, f"{advantage_type.title()}: {raw_rolls[0]} & {raw_rolls[1]} → {d20_roll}")
        
        narrative_context = " | ".join(filter(None, narrative_parts))
        
        logger.info(
            f"D20 Resolution: {intent_id} -> {total_score} vs DC {dc} "
            f"({'SUCCESS' if success else 'FAILURE'})"
            + (f" ({advantage_type})" if advantage_type else "")
        )
        
        return D20Result(
            success=success,
            roll=d20_roll,
            total_score=total_score,
            difficulty_class=dc,
            hp_delta=hp_delta,
            reputation_deltas=reputation_deltas,
            relationship_changes=relationship_changes,
            npc_state_changes=npc_state_changes,
            goals_completed=goals_completed,
            narrative_context=narrative_context,
            advantage_type=advantage_type,
            raw_rolls=raw_rolls
        )
    
    def _calculate_difficulty_class(self, intent_id: str, room_tags: List[str]) -> Tuple[int, str]:
        """Calculate DC using deterministic table lookup."""
        intent = intent_id.lower()
        
        # Base DC from table
        base_dc = DC_TABLE.get(intent, DC_TABLE["default"])
        reasons = [f"Base DC {base_dc}"]
        
        # Apply tag modifiers
        modifiers = DC_TABLE.get("modifiers", {})
        tag_delta = 0
        
        for tag in room_tags:
            norm_tag = tag.lower().replace(" ", "_")
            if norm_tag in modifiers and intent in modifiers[norm_tag]:
                mod = modifiers[norm_tag][intent]
                tag_delta += mod
                reasons.append(f"{tag.title()} ({mod:+d})")
        
        final_dc = base_dc + tag_delta
        return final_dc, ", ".join(reasons)
    
    def _determine_advantage(
        self, 
        intent_id: str, 
        game_state: GameState, 
        room_tags: List[str], 
        target_npc: Optional[str]
    ) -> Optional[str]:
        """
        Determine if action has advantage or disadvantage based on state.
        
        This is the "Wit & Grit" system - mathematical enforcement of state consequences.
        """
        intent = intent_id.lower()
        
        # Check for disadvantage conditions
        disadvantage_conditions = []
        
        # Wanted state gives disadvantage on social actions
        if game_state.reputation.get("law", 0) <= -10:
            if intent in ["charm", "persuade", "social"]:
                disadvantage_conditions.append("Wanted status")
        
        # Hostile NPCs give disadvantage on social actions
        if target_npc:
            room = game_state.rooms.get(game_state.current_room)
            if room:
                for npc in room.npcs:
                    if npc.name.lower() == target_npc.lower() and npc.state == "hostile":
                        if intent in ["charm", "persuade", "social"]:
                            disadvantage_conditions.append(f"Hostile {target_npc}")
        
        # Environmental disadvantages
        if "dimly_lit" in room_tags and intent in ["investigate", "search", "perception"]:
            disadvantage_conditions.append("Dim lighting")
        
        if "sticky floors" in room_tags and intent in ["finesse", "stealth", "acrobatics"]:
            disadvantage_conditions.append("Sticky floors")
        
        # Check for advantage conditions
        advantage_conditions = []
        
        # Good reputation gives advantage on social actions
        if game_state.reputation.get("law", 0) >= 10:
            if intent in ["charm", "persuade", "social"]:
                advantage_conditions.append("Good reputation")
        
        # Charmed NPCs give advantage on social actions
        if target_npc:
            room = game_state.rooms.get(game_state.current_room)
            if room:
                for npc in room.npcs:
                    if npc.name.lower() == target_npc.lower() and npc.state == "charmed":
                        if intent in ["charm", "persuade", "social"]:
                            advantage_conditions.append(f"Charmed {target_npc}")
        
        # Environmental advantages
        if "dimly_lit" in room_tags and intent in ["stealth", "hide"]:
            advantage_conditions.append("Dim lighting")
        
        # Determine final result
        if disadvantage_conditions and advantage_conditions:
            # They cancel out
            logger.debug(f"Advantage and disadvantage cancel: {advantage_conditions} vs {disadvantage_conditions}")
            return None
        elif disadvantage_conditions:
            logger.debug(f"Disadvantage applied: {', '.join(disadvantage_conditions)}")
            return "disadvantage"
        elif advantage_conditions:
            logger.debug(f"Advantage applied: {', '.join(advantage_conditions)}")
            return "advantage"
        
        return None
    
    def _get_attribute_bonus(self, intent_id: str, attributes: Dict[str, int]) -> Tuple[int, str]:
        """Map intent to primary attribute and return bonus."""
        intent = intent_id.lower()
        
        mapping = {
            "force": "strength",
            "combat": "strength",
            "athletics": "strength",
            
            "finesse": "dexterity", 
            "stealth": "dexterity",
            "acrobatics": "dexterity",
            "leave_area": "dexterity",
            
            "investigate": "intelligence",
            "search": "intelligence",
            "perception": "wisdom",  # Perception uses wisdom
            
            "charm": "charisma",
            "persuade": "charisma",
            "social": "charisma",
            "distract": "charisma"
        }
        
        attr_name = mapping.get(intent, "luck")
        bonus = attributes.get(attr_name, 0)
        
        return bonus, attr_name
    
    def _calculate_item_bonus(self, intent_id: str, inventory) -> int:
        """Calculate total bonus from relevant items."""
        # Get target stat for this intent
        _, target_stat = self._get_attribute_bonus(intent_id, {})
        
        total_bonus = 0
        for item in inventory:
            if hasattr(item, 'target_stat') and item.target_stat == target_stat:
                total_bonus += getattr(item, 'modifier_value', 0)
        
        return total_bonus
    
    def _calculate_hp_delta(self, success: bool, total_score: int, dc: int) -> int:
        """Calculate HP change based on success/failure margin."""
        if success:
            return 0  # No healing on success unless specifically intended
        
        # Failure damage based on margin of failure
        margin = dc - total_score
        if margin >= 10:  # Critical failure
            return -random.randint(8, 15)
        elif margin >= 5:  # Bad failure
            return -random.randint(3, 8)
        else:  # Near miss
            return -random.randint(1, 3)
    
    def _calculate_reputation_changes(
        self, 
        intent_id: str, 
        success: bool, 
        target_npc: Optional[str]
    ) -> Dict[str, int]:
        """Calculate global reputation deltas."""
        deltas = {}
        intent = intent_id.lower()
        
        # Combat actions hurt law reputation
        if intent in ["combat", "force"]:
            deltas["law"] = -3 if success else -1
            
        # Social actions can help
        if intent in ["charm", "persuade"] and success:
            deltas["law"] = 1
            
        # Criminal actions affect underworld
        if intent in ["stealth", "finesse"] and success:
            deltas["underworld"] = 1
            
        return deltas
    
    def _calculate_relationship_changes(
        self,
        intent_id: str,
        success: bool,
        target_npc: Optional[str]
    ) -> Dict[str, Dict]:
        """Calculate NPC relationship disposition and tag changes."""
        if not target_npc:
            return {}
        
        changes = {}
        intent = intent_id.lower()
        
        # Initialize changes for target
        changes[target_npc] = {
            "disposition": 0,
            "tags": []
        }
        
        # Combat makes people hostile
        if intent in ["combat", "force"]:
            changes[target_npc]["disposition"] = -15 if success else -5
            if success:
                changes[target_npc]["tags"].append("hurt")
        
        # Social actions improve disposition
        elif intent in ["charm", "persuade"]:
            if success:
                changes[target_npc]["disposition"] = 10
                changes[target_npc]["tags"].append("friendly")
        
        # Stealth doesn't directly affect relationships unless caught
        elif intent == "stealth" and not success:
            changes[target_npc]["disposition"] = -5
            changes[target_npc]["tags"].append("suspicious")
        
        return changes
    
    def _calculate_npc_state_changes(
        self,
        intent_id: str,
        success: bool,
        target_npc: Optional[str],
        game_state: GameState
    ) -> Dict[str, str]:
        """Calculate NPC state transitions."""
        if not target_npc:
            return {}
        
        changes = {}
        intent = intent_id.lower()
        
        # Get current NPC state
        current_room = game_state.rooms.get(game_state.current_room)
        current_state = "neutral"
        
        if current_room:
            for npc in current_room.npcs:
                if npc.name.lower() == target_npc.lower():
                    current_state = npc.state
                    break
        
        # Determine new state
        new_state = current_state
        
        if intent in ["combat", "force"] and success:
            new_state = "hostile"
        elif intent == "charm" and success:
            new_state = "charmed"
        elif intent == "distract" and success:
            new_state = "distracted"
        elif intent in ["combat", "force"] and not success and current_state == "neutral":
            new_state = "hostile"  # Failed aggression still makes them hostile
        
        if new_state != current_state:
            changes[target_npc] = new_state
        
        return changes
    
    def _check_goal_completion(
        self,
        intent_id: str,
        success: bool,
        game_state: GameState,
        player_input: str
    ) -> List[str]:
        """Check if any goals are completed by this action."""
        completed = []
        
        if not success:
            return completed
        
        current_room = game_state.rooms.get(game_state.current_room)
        
        for goal in game_state.goal_stack:
            # Skip already completed goals
            if goal.status != "active":
                continue
            
            # Check intent-based completion
            if goal.required_intent == intent_id:
                # Check target tags if specified
                if goal.target_tags:
                    target_hit = any(
                        tag.lower() in player_input.lower() 
                        for tag in goal.target_tags
                    )
                    if target_hit:
                        completed.append(goal.id)
                else:
                    completed.append(goal.id)
                continue
            
            # Check state-based completion
            if goal.target_npc_state and current_room:
                for npc in current_room.npcs:
                    if npc.state == goal.target_npc_state:
                        # Check if this NPC is a target
                        if not goal.target_tags or any(
                            tag.lower() in npc.name.lower() 
                            for tag in goal.target_tags
                        ):
                            completed.append(goal.id)
                            break
        
        return completed


# Export for use by the engine
__all__ = ["D20Resolver", "D20Result"]
