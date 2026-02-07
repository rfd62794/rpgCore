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
from voyager_logic import STANDARD_ACTIONS

class VoyagerDecision(BaseModel):
    """Single action decision from the Voyager."""
    
    selected_action_id: str = Field(description="The ID of the pre-baked action chosen from the menu")
    custom_flair: str = Field(description="A short natural language flavor for the action (e.g., 'I slam my fist on the table')")
    strategic_reasoning: str = Field(description="Why this choice fits the personality and stats")
    internal_monologue: str = Field(description="My current emotional state")
    
    @property
    def action(self) -> str:
        """Compat property for game loop."""
        return self.custom_flair


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
    
    def __init__(self, personality: str = "curious", model_name: str = "llama3.2:3b"):
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
        # Use OpenAIModel with env vars for local Ollama
        os.environ["OPENAI_BASE_URL"] = f"{os.environ['OLLAMA_BASE_URL']}/v1"
        os.environ["OPENAI_API_KEY"] = "ollama"
        
        model = OpenAIModel(model_name)
        
        self.agent = Agent(
            model=model,
            output_type=VoyagerDecision,
            system_prompt=system_prompt,
            retries=3
        )
        
        logger.info(f"Voyager initialized with '{self.personality}' personality")
    
    async def decide_action(
        self,
        scene_context: str,
        player_stats: dict,
        turn_history: list[str] | None = None
    ) -> VoyagerDecision:
        """Decide next action using deterministic menu."""
        
        # Get pre-baked options
        options = STANDARD_ACTIONS.get(self.personality, STANDARD_ACTIONS["curious"])
        
        # Inject into prompt
        options_str = "\n".join([f"- ID: {o['id']} | Label: {o['label']} (Uses {o['stat']})" for o in options])
        
        # Build prompt
        prompt = (
            f"CONTEXT:\n{scene_context}\n\n"
            f"YOUR STATS:\n{player_stats}\n\n"
            f"AVAILABLE ACTIONS (CHOOSE ONE):\n{options_str}\n\n"
            "INSTRUCTIONS:\n"
            "1. Analyze your stats and the context.\n"
            "2. Choose the BEST Action ID from the list above.\n"
            "3. Write a short 'custom_flair' sentence to describe doing it.\n"
            "4. Explain your reasoning.\n\n"
            "Make your decision now."
        )
        
        logger.debug(f"Voyager deciding from menu...")
        
        # Call LLM
        result = await self.agent.run(prompt)
        
        logger.info(f"Voyager decided: {result.data.selected_action_id}")
        
        return result.data
