"""
Chronicler Engine: Pure Narrative Generation

The Chronicler is responsible for ONLY writing D&D-style prose.
No mechanics - just vivid storytelling based on what the Arbiter calculated.
"""

import os

from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from model_factory import get_model



class ChroniclerProse(BaseModel):
    """D&D-style narrative prose."""
    
    narrative: str = Field(
        description="DM-style narration of what happened (2-3 sentences, vivid and flavorful)"
    )


class ChroniclerEngine:
    """
    The Narrative Chronicler: Writes D&D prose from Arbiter results.
    
    Design:
    - Uses larger, creative model (llama3.2:3b)
    - Prompt focuses ONLY on storytelling
    - Receives Arbiter's state changes as input
    """
    
    def __init__(
        self,
        model_name: str = 'ollama:llama3.2:latest',
        tone: str = "humorous"
    ):
        """
        Initialize chronicler engine.
        
        Args:
            model_name: Larger Ollama model for creative prose
            tone: Narrative style (humorous, serious, gritty)
        """
        # Set Ollama base URL
        if 'OLLAMA_BASE_URL' not in os.environ:
            os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
            
        # Use factory to get shared model connection
        # High temperature for creativity
        model = get_model(model_name, temperature=0.8)
        
        self.tone = tone
        system_prompt = self._build_chronicler_prompt(tone)
        
        logger.info(f"Initializing Chronicler with {model_name}")
        
        self.agent = Agent(
            model=model,
            output_type=ChroniclerProse,
            system_prompt=system_prompt
        )
    
    def _build_chronicler_prompt(self, tone: str) -> str:
        """
        Build the system prompt for the narrative engine.
        Optimized for Qwen 2.5 0.5B (Iron Frame).
        """
        return (
            "SYSTEM: You are a snarky D&D narrator.\n"
            "TASK: Write 1-2 short, punchy sentences describing the action result.\n"
            "RULES:\n"
            "- Use the Input Data to ground your narration.\n"
            "- Mention the Room Environment tags (e.g., Sticky Floors).\n"
            "- Mention the 'Item Found' if successful.\n"
            "- Be brief. Do not ramble.\n\n"
            "INPUT DATA STRUCTURE:\n"
            "- Action: [Player input]\n"
            "- Result: [SUCCESS/FAILURE]\n"
            "- Roll: [Number]\n"
            "- Environment: [Tags]\n"
            "- Item Found: [Item Name]\n\n"
            "Example Output:\n"
            "'You roar and smash the table into splinters, your boots barely peeling off the sticky floor in time to grab a rusty key from the wreckage. Talk about a lucky break.'"
        )
    
    async def narrate_outcome(
        self,
        player_input: str,
        intent_id: str,
        arbiter_result: dict,
        context: str
    ) -> ChroniclerProse:
        """
        Generate narrative prose from Arbiter results.
        
        Args:
            player_input: Original player text
            intent_id: Resolved intent
            arbiter_result: Dictionary with success, hp_delta, npc_state, etc.
            context: Room description and NPC states
        
        Returns:
            ChroniclerProse with vivid D&D narration
        """
        prompt = (
            f"Context: {context}\n\n"
            f"Player Action: \"{player_input}\"\n"
            f"Intent: {intent_id}\n\n"
            f"Arbiter Result:\n"
            f"- Success: {arbiter_result.get('success')}\n"
            f"- HP Change: {arbiter_result.get('hp_delta', 0)}\n"
            f"- Gold Change: {arbiter_result.get('gold_delta', 0)}\n"
            f"- NPC State: {arbiter_result.get('new_npc_state')}\n"
            f"- Reasoning: {arbiter_result.get('reasoning')}\n"
            f"- Narrative Seed: {arbiter_result.get('narrative_seed', 'N/A')}\n\n"
            f"Write vivid D&D narration using the context and narrative seed:\n"
        )
        
        logger.debug(f"Chronicler narrating: {intent_id}")
        
        try:
            result = await self.agent.run(prompt)
            prose = result.data
            
            logger.info(f"Chronicler generated: {prose.narrative[:50]}...")
            return prose
            
            
        except Exception as e:
            logger.error(f"Chronicler failed: {e}")
            
            # Fallback narrative
            return self._fallback_prose(player_input, arbiter_result)

    async def narrate_stream(
        self,
        player_input: str,
        intent_id: str,
        arbiter_result: dict,
        context: str
    ):
        """
        Stream narrative prose token by token.
        Yields: str keywords/tokens
        """
        prompt = (
            f"Context: {context}\n\n"
            f"Player Action: \"{player_input}\"\n"
            f"Intent: {intent_id}\n\n"
            f"Arbiter Result:\n"
            f"- Success: {arbiter_result.get('success')}\n"
            f"- HP Change: {arbiter_result.get('hp_delta', 0)}\n"
            f"- Gold Change: {arbiter_result.get('gold_delta', 0)}\n"
            f"- NPC State: {arbiter_result.get('new_npc_state')}\n"
            f"- Reasoning: {arbiter_result.get('reasoning')}\n"
            f"- Narrative Seed: {arbiter_result.get('narrative_seed', 'N/A')}\n\n"
            f"Write vivid D&D narration using the context and narrative seed:\n"
        )
        
        logger.debug(f"Chronicler streaming: {intent_id}")
        
        try:
            # We use result_type=str to get raw text streaming
            # escaping the JSON structure for the sake of immediate user feedback
            async with self.agent.run_stream(prompt, result_type=str) as result:
                async for message in result.stream_text():
                    yield message
                    
        except Exception as e:
            logger.error(f"Chronicler stream failed: {e}")
            yield f"You attempt {player_input}."
            if arbiter_result.get('success'):
                yield " It succeeds."
            else:
                yield " It fails."
    
    def _fallback_prose(self, player_input: str, arbiter_result: dict) -> ChroniclerProse:
        """Fallback narrative if LLM fails."""
        logger.warning("Using fallback chronicler prose")
        
        success = arbiter_result.get('success', False)
        
        if success:
            narrative = f"You attempt {player_input}. {arbiter_result.get('reasoning', 'The action succeeds')}."
        else:
            narrative = f"You attempt {player_input}, but the action fails."
        
        return ChroniclerProse(narrative=narrative)
