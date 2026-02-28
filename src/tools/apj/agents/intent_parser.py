"""
Intent Parser - Simplified LLM-First Approach
Just ask Ollama what to do and execute what it says
"""

import json
from typing import Dict, Optional


class IntentParser:
    """
    SIMPLE: Just ask Ollama what the user wants and do it
    Stop trying to parse the response - just use what it says
    """
    
    def __init__(self, ollama_client=None):
        self.ollama = ollama_client
    
    def parse_and_suggest(self, user_input: str, context: Dict) -> str:
        """
        Ask LLM what to do and get back actionable response
        Don't parse - just use what it says
        """
        
        prompt = f"""
User wants: "{user_input}"

Current project state:
{json.dumps(context.get('project_status', {}), indent=2)}

Available actions:
- Build T_3_0: ECS Rendering System
- Complete Dungeon Demo
- Execute Tower Defense Phase 3

Available demos:
- dungeon, racing, breeding, tower_defense, slime_breeder

What should the user do? Respond with:
1. What action/demo they should work on
2. Why that makes sense given current state
3. Confidence in your recommendation (high/medium/low)

Be conversational and helpful.
"""
        
        if self.ollama:
            response = self.ollama.analyze_blockers(prompt)
            return response
        
        return "Unable to understand - no LLM available"


class ConversationalInterface:
    """
    SIMPLE: Chat with user, use LLM for everything
    Stop trying to parse commands - just chat
    """
    
    def __init__(self, project_root, ollama_client=None):
        self.project_root = project_root
        self.ollama = ollama_client
        self.context = {}
        self.conversation_history = []
    
    def run_chat_loop(self, initial_context: Dict = None) -> None:
        """
        Simple chat loop
        User types → LLM understands → Execute or clarify
        """
        
        if initial_context:
            self.context = initial_context
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              ADJ INTERACTIVE CHAT                             ║
╚══════════════════════════════════════════════════════════════╝

Just chat naturally about what you want to do.
I'll understand what you mean and suggest actions.

Type 'quit' or 'exit' to leave.

""")
        
        while True:
            try:
                user_input = input("you> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Exiting ADJ")
                    break
                
                # Add to history
                self.conversation_history.append(("user", user_input))
                
                # Ask LLM what to do
                response = self._get_llm_response(user_input)
                
                print(f"\nadj> {response}\n")
                
                # Add to history
                self.conversation_history.append(("assistant", response))
                
            except KeyboardInterrupt:
                print("\n\nExiting ADJ")
                break
            except EOFError:
                break
    
    def _get_llm_response(self, user_input: str) -> str:
        """
        Ask LLM what to do about user's request
        Return its response directly - no parsing
        """
        
        # Build context string
        project_status = self.context.get('project_status', {})
        blockers = self.context.get('blockers', [])
        next_actions = self.context.get('next_actions', [])
        
        status_str = json.dumps(project_status, indent=2)
        blockers_str = "\n".join([f"- {b['blocker']}" for b in blockers])
        actions_str = "\n".join([f"- {a['action']}: {a['effort']}" for a in next_actions])
        
        # Conversation history for context
        history_str = ""
        for role, msg in self.conversation_history[-4:]:  # Last 4 turns
            history_str += f"\n{role}: {msg}"
        
        prompt = f"""
You are ADJ, an intelligent development assistant.
You understand project state and help the user accomplish their goals.

CURRENT PROJECT STATE:
{status_str}

CRITICAL BLOCKERS:
{blockers_str}

RECOMMENDED NEXT ACTIONS:
{actions_str}

CONVERSATION SO FAR:
{history_str}

NEW USER MESSAGE: "{user_input}"

Now respond helpfully. You can:
1. Suggest what to do next
2. Answer questions about project state
3. Explain blockers and why things are blocked
4. Ask clarifying questions
5. Offer to execute actions (just say "Ready to execute X? (y/n)")
6. Help the user understand the project

Be conversational and helpful. Use project context to inform your response.
"""
        
        try:
            # Use pydantic_ai Agent with the model
            from pydantic_ai import Agent
            agent = Agent(self.ollama)
            
            # Run the agent synchronously
            import asyncio
            response = asyncio.run(agent.run(prompt))
            
            # Extract the actual data from the response
            response_text = response.data if hasattr(response, 'data') else str(response)
            return response_text
            
        except Exception as e:
            return f"Sorry, I couldn't process that: {e}"
