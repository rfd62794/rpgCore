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
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from loguru import logger


class VoyagerDecision(BaseModel):
    """Single action decision from the Voyager."""
    
    action: str  # Natural language action (e.g., "I bribe the janitor with 10 gold")
    reasoning: str  # Why this action was chosen (for debugging)


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
    
    def __init__(self, personality: str = "curious", model_name: str = "llama3.2"):
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
            "You are an RPG player making decisions in a D&D-style game.\n\n"
            f"Personality: {personality_trait}\n\n"
            "Rules:\n"
            "- Output ONLY the action you want to perform in natural language\n"
            "- Use first person ('I', not 'you')\n"
            "- Be specific and concrete (not 'explore' but 'I search the wooden table')\n"
            "- Consider your stats (HP, Gold, Inventory)\n"
            "- Respond to the current scene and NPCs\n"
            "- One action per turn\n\n"
            "Examples:\n"
            "- 'I try to bribe the janitor with 10 gold to show me the sewers'\n"
            "- 'I sneak past the guard while he's distracted'\n"
            "- 'I kick the table over to create a distraction'\n"
        )
        
        # Initialize Pydantic AI agent
        # Ollama compatibility through env var (already set above)
        self.agent = Agent(
            model=f"ollama:{model_name}",
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
        )
        
        if player_stats.get('inventory'):
            prompt += f"- Inventory: {', '.join(player_stats['inventory'])}\n"
        
        if turn_history:
            prompt += f"\nRecent Actions:\n"
            for action in turn_history[-3:]:
                prompt += f"  - {action}\n"
            prompt += "\n(Avoid repeating the same action)\n"
        
        prompt += "\nWhat do you do?"
        
        logger.debug(f"Voyager deciding action...")
        
        # Call LLM
        result = await self.agent.run(prompt)
        
        logger.info(f"Voyager decided: {result.data.action[:50]}...")
        
        return result.data
