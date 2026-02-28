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
    ENHANCED: Chat with user, use Agent Swarm for complex tasks
    Single LLM for simple chat, swarm for complex work
    """
    
    def __init__(self, project_root, ollama_client=None):
        self.project_root = project_root
        self.ollama = ollama_client
        self.context = {}
        self.conversation_history = []
        
        # Initialize swarm using existing BaseAgent framework
        if self.ollama:
            try:
                # Import swarm schemas to ensure registration
                import src.tools.apj.agents.swarm_schemas
                
                from .swarm_agent import SwarmCoordinator
                from .base_agent import AgentConfig, PromptConfig
                
                # Create swarm coordinator config
                swarm_config = AgentConfig(
                    name="swarm_coordinator",
                    role="Coordinate swarm tasks and manage agent orchestration",
                    department="planning",
                    model_preference="local",
                    prompts=PromptConfig(
                        system="docs/agents/prompts/coordinator_system.md",
                        fewshot="docs/agents/prompts/generic_system.md"
                    ),
                    schema_name="SwarmTaskAssignment",
                    fallback={
                        "recommended": {
                            "label": "FALLBACK",
                            "title": "Use single agent analysis",
                            "rationale": "Swarm coordination failed",
                            "risk": "low"
                        }
                    }
                )
                
                self.swarm = SwarmCoordinator(swarm_config)
                print("🐝 Agent Swarm initialized with BaseAgent framework")
                
            except Exception as e:
                print(f"⚠️  Failed to initialize swarm: {e}")
                self.swarm = None
        else:
            print("⚠️  No Ollama model available - Swarm disabled")
            self.swarm = None
    
    def run_chat_loop(self, initial_context: Dict = None) -> None:
        """
        Enhanced chat loop with swarm support
        User types → Simple LLM response OR Swarm processing
        """
        
        if initial_context:
            self.context = initial_context
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              ADJ INTERACTIVE CHAT (WITH SWARM)                ║
╚══════════════════════════════════════════════════════════════╝

Just chat naturally about what you want to do.
I'll understand what you mean and suggest actions.

For complex tasks, I'll use the Agent Swarm:
- Multiple specialized agents working together
- Coordinated code generation and testing
- Comprehensive analysis and planning

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
                
                # Determine if this needs swarm processing
                if self._needs_swarm_processing(user_input):
                    print(f"\n🐝 Using Agent Swarm for: {user_input}")
                    swarm_result = self._process_with_swarm(user_input)
                    print(f"\nadj> Swarm result:\n{swarm_result}\n")
                else:
                    # Try to get extension template
                    from src.tools.apj.agents.swarm_manager import get_extension_template
                    template = get_extension_template("documentation")
                    
                    if template:
                        manager.add_agent_template(template)
                        manager.create_agent_from_template(template.name)
                    else:
                        print(f"❌ Unknown template: documentation")
                        print("Available extensions: documentation, performance, security, deployment")
                
                # Add to history
                self.conversation_history.append(("assistant", "Swarm processing complete"))
                
            except KeyboardInterrupt:
                print("\n\nExiting ADJ")
                break
            except EOFError:
                break
    
    def _needs_swarm_processing(self, user_input: str) -> bool:
        """Determine if request needs swarm processing"""
        
        swarm_keywords = [
            "implement", "build", "create", "generate", "refactor",
            "test", "analyze", "plan", "execute", "code", "system",
            "component", "feature", "complex", "architecture"
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in swarm_keywords)
    
    def _process_with_swarm(self, user_input: str) -> str:
        """Process request using SwarmAgent with BaseAgent framework"""
        
        # Swarm should already be initialized
        if not self.swarm:
            return "❌ Agent Swarm not available"
        
        # Process through swarm using existing framework
        try:
            result = self.swarm.process_request(user_input, self.context)
            
            # Format result for display
            if "error" in result:
                return f"❌ Error: {result['error']}"
            
            formatted_result = "🐝 Swarm Processing Results:\n\n"
            
            for task_id, task_result in result.items():
                if "error" in task_result:
                    formatted_result += f"❌ {task_id}: {task_result['error']}\n\n"
                else:
                    formatted_result += f"✅ {task_id} ({task_result.get('agent', 'unknown')}):\n"
                    
                    # Extract meaningful content from the result
                    result_content = task_result.get('result', 'No result')
                    if hasattr(result_content, 'summary'):
                        formatted_result += f"   {result_content.summary}\n"
                    elif hasattr(result_content, 'response'):
                        formatted_result += f"   {result_content.response}\n"
                    elif isinstance(result_content, str):
                        formatted_result += f"   {result_content[:200]}...\n"
                    else:
                        formatted_result += f"   {str(result_content)[:200]}...\n"
            
            return formatted_result
            
        except Exception as e:
            return f"❌ Swarm processing failed: {e}"
    
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
        
        # Check if swarm is available
        swarm_available = self.swarm is not None
        swarm_status = f"\nAgent Swarm: {'✅ Available' if swarm_available else '❌ Not initialized'}"
        
        prompt = f"""
You are ADJ, an intelligent development assistant.
You understand project state and help the user accomplish their goals.

CURRENT PROJECT STATE:
{status_str}

CRITICAL BLOCKERS:
{blockers_str}

RECOMMENDED NEXT ACTIONS:
{actions_str}

{swarm_status}

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
7. For complex tasks (implement, build, code, test), mention that the Agent Swarm can help

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
