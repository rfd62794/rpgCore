"""
Voyager Agent: Automated Player for Self-Testing

The fourth Council member that sits at the top of the game loop,
replacing manual input with character-aware decision making.

Design:
- Uses llama3.2:3b for "common sense" navigation
- Personality-driven (Curious, Aggressive, Cautious)
- Sees full scene context and player stats
- Vends natural language action strings
"""

import os
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from loguru import logger


class VoyagerDecision(BaseModel):
    """Single action decision from the Voyager."""
    
    selected_intent: str = Field(description="The intent_id chosen from the library (e.g., 'force', 'charm', 'stealth')")
    action: str = Field(description="The natural language command to send to the loop")
    strategic_reasoning: str = Field(description="Why this choice makes sense given my stats/tags")
    internal_monologue: str = Field(description="My current emotional state (e.g., 'I'm tired of these sticky floors')")


class VoyagerAgent:
    """
    Automated player agent for self-testing and auto-adventure mode.
    
    Replaces human input with LLM-driven decisions based on:
    - Current scene context
    - Player stats (HP, Gold, Inventory)
    - Personality traits
    """
    
    PERSONALITY_PROMPTS = {
        "curious": (
            "You are a curious adventurer who loves to explore and investigate. "
            "You ask questions, search for secrets, and talk to NPCs. "
            "You avoid violence unless necessary."
        ),
        "aggressive": (
            "You are a bold warrior who solves problems with force. "
            "You intimidate NPCs, kick down doors, and attack when threatened. "
            "You value strength over subtlety."
        ),
        "tactical": (
            "You are a strategic thinker who weighs risks carefully. "
            "You use stealth, distraction, and charm to achieve goals. "
            "You only fight when you have the advantage."
        ),
        "chaotic": (
            "You are unpredictable and chaotic. "
            "You do unexpected things, sometimes helpful, sometimes destructive. "
            "You follow whims and create chaos for entertainment."
        )
    }
    
    def __init__(self, personality: str = "curious", model_name: str = "llama3.2:1b"):
        """
        Initialize Voyager agent.
        
        Args:
            personality: Character personality (curious, aggressive, tactical, chaotic)
            model_name: Ollama model to use
        """
        # Ensure OLLAMA_BASE_URL is set
        if "OLLAMA_BASE_URL" not in os.environ:
            os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
        
        self.personality = personality.lower()
        
        # Build system prompt
        personality_trait = self.PERSONALITY_PROMPTS.get(
            self.personality,
            self.PERSONALITY_PROMPTS["curious"]
        )
        
        system_prompt = (
            "You are an expert RPG STRATEGIST playing a D&D-style game.\n\n"
            f"Personality: {personality_trait}\n\n"
            "OBJECTIVE: Choose the action with the HIGHEST PROBABILITY of success.\n"
            "1. Analyze your Player Stats (Strength, Dex, etc.)\n"
            "2. Analyze Room Tags (e.g., 'Sticky Floors' punishes Dexterity)\n"
            "3. Select an Intent that leverages your high stats and avoids penalties.\n\n"
            "Rules:\n"
            "- Output `selected_intent` (e.g., 'force', 'charm')\n"
            "- Output `action` in natural language (first person)\n"
            "- Explain your `strategic_reasoning` (e.g., 'I have high Strength and sticky floors punish Dex, so I will Smash')\n"
            "- Include `internal_monologue` reflecting your personality\n"
            "- Consider Inventory bonuses (e.g., 'Iron Key' helps Lockpicking)\n\n"
            "Examples:\n"
            "- Sticky Floor + High Str: Intent='force', Action='I smash the table', Reasoning='Avoiding Dex check due to floors'\n"
            "- Rowdy Crowd + High Cha: Intent='charm', Action='I buy a round', Reasoning='Leveraging Cha to calm crowd'\n"
        )
        
        # Initialize Pydantic AI agent
        # Use OpenAIModel for better compatibility with local Ollama
        # This fixes 404 errors by explicitly setting the base_url
        model = OpenAIModel(
            model_name=model_name,
            base_url=f"{os.environ['OLLAMA_BASE_URL']}/v1",
            api_key='ollama',  # Required but ignored
        )
        
        self.agent = Agent(
            model=model,
            output_type=VoyagerDecision,
            system_prompt=system_prompt
        )
        
        logger.info(f"Voyager initialized with '{self.personality}' personality")
    
    async def decide_action(
        self,
        scene_context: str,
        player_stats: dict,
        turn_history: list[str] | None = None
    ) -> VoyagerDecision:
        """
        Decide next action based on current game state.
        
        Args:
            scene_context: Current room description, NPCs, items
            player_stats: Player HP, Gold, Inventory
            turn_history: Last 3 actions (for stutter check)
        
        Returns:
            VoyagerDecision with action string and reasoning
        """
        # Build prompt
        prompt = (
            f"Current Scene:\n{scene_context}\n\n"
            f"Your Stats:\n"
            f"- HP: {player_stats.get('hp', 100)}/{player_stats.get('max_hp', 100)}\n"
            f"- Gold: {player_stats.get('gold', 0)}\n"
            f"- Attributes: {player_stats.get('attributes', {})}\n"
        )
        
        if player_stats.get('inventory'):
            # Inventory is now list of Item objects (dicts), need to parse
            items = []
            for item in player_stats['inventory']:
                # Handle both dict (if serialized) and Item object
                if isinstance(item, dict):
                    name = item.get('name', 'Unknown')
                    bonus = item.get('stat_bonus', '')
                else:
                    name = item.name
                    bonus = item.stat_bonus
                items.append(f"{name} ({bonus})")
            prompt += f"- Inventory: {', '.join(items)}\n"
        
        if turn_history:
            prompt += f"\nRecent Actions:\n"
            for action in turn_history[-3:]:
                prompt += f"  - {action}\n"
            prompt += "\n(Avoid repeating the same action)\n"
        
        prompt += "\nWhat is your strategic move?"
        
        logger.debug(f"Voyager deciding action...")
        
        # Call LLM
        result = await self.agent.run(prompt)
        
        logger.info(f"Voyager decided: {result.data.action[:50]}...")
        
        return result.data
