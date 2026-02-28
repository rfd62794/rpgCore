"""
Intent Parser - Understand natural language commands
Parse what user wants even if they don't use exact syntax
"""

from enum import Enum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


class Intent(Enum):
    """User intents we can understand"""
    EXECUTE_ACTION = "execute_action"
    CREATE_PLAN = "create_plan"
    CHECK_CAPABILITY = "check_capability"
    SHOW_STATUS = "show_status"
    POLISH_DEMO = "polish_demo"
    EXPLAIN_BLOCKER = "explain_blocker"
    LIST_OPTIONS = "list_options"
    GET_HELP = "get_help"
    QUIT = "quit"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Result of parsing user input"""
    intent: Intent
    action: Optional[str]  # "Build T_3_0", "Complete Dungeon", etc
    demo: Optional[str]    # "dungeon", "racing", etc
    target: Optional[str]  # More general target
    confidence: float      # 0-1, how sure are we?
    explanation: str       # Why we think this is what they want


class IntentParser:
    """
    Parse natural language user input
    Understand intent even if not perfectly phrased
    """
    
    def __init__(self, ollama_client=None):
        self.ollama = ollama_client
        
        # Keyword mappings for fast path (before LLM)
        self.intent_keywords = {
            Intent.EXECUTE_ACTION: [
                "execute", "run", "build", "start", "do", "begin", "implement",
                "create", "make", "set up", "go", "let's", "can we"
            ],
            Intent.CREATE_PLAN: [
                "plan", "plan for", "how", "what's the plan", "steps", "break down",
                "outline", "strategy", "approach", "way to"
            ],
            Intent.CHECK_CAPABILITY: [
                "can", "able", "could", "possible", "check", "verify", "test",
                "safe", "handle", "capable"
            ],
            Intent.SHOW_STATUS: [
                "status", "state", "what's", "show", "tell me", "current", "progress",
                "how far", "where are", "summary"
            ],
            Intent.POLISH_DEMO: [
                "polish", "complete", "finish", "perfect", "improve", "enhance",
                "work on demo", "demo"
            ],
            Intent.EXPLAIN_BLOCKER: [
                "why", "blocked", "blocker", "problem", "issue", "stuck",
                "what's stopping", "what's wrong"
            ],
            Intent.LIST_OPTIONS: [
                "what can", "what should", "options", "alternatives", "choices",
                "next", "available"
            ],
            Intent.GET_HELP: [
                "help", "how do", "what do", "guide", "explain", "tell me about"
            ],
            Intent.QUIT: [
                "quit", "exit", "bye", "done", "stop", "close", "leave"
            ]
        }
        
        # Demo names
        self.demo_names = {
            "dungeon": ["dungeon", "dungeon demo"],
            "racing": ["racing", "racing demo", "racer"],
            "tower defense": ["tower defense", "tower", "td"],
            "breeding": ["breeding", "breeder", "genetics"],
            "slime breeder": ["slime breeder", "slime_breeder"],
        }
        
        # Action names
        self.action_names = {
            "Build T_3_0": [
                "t_3_0", "rendering", "ecs rendering", "render system",
                "render component", "animation"
            ],
            "Complete Dungeon": [
                "complete dungeon", "finish dungeon", "dungeon complete",
                "dungeon polish"
            ],
            "Execute Tower Defense": [
                "tower defense", "phase 3", "tower defense phase 3",
                "full tower defense"
            ]
        }
    
    def parse(self, user_input: str, context: Dict = None) -> ParsedCommand:
        """
        Parse user input and extract intent
        
        Returns: ParsedCommand with intent and details
        """
        
        user_input = user_input.strip().lower()
        
        # Quick exit
        if not user_input:
            return ParsedCommand(
                intent=Intent.UNKNOWN,
                action=None,
                demo=None,
                target=None,
                confidence=0.0,
                explanation="No input provided"
            )
        
        # FAST PATH: Check for exact keyword matches
        fast_parse = self._fast_parse(user_input)
        if fast_parse.confidence > 0.7:
            return fast_parse
        
        # SLOW PATH: Use Ollama to understand intent
        if self.ollama:
            return self._llm_parse(user_input, context)
        
        return fast_parse
    
    def _fast_parse(self, user_input: str) -> ParsedCommand:
        """
        Fast keyword-based parsing
        Don't use LLM if we can understand from keywords
        """
        
        # Check each intent
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    
                    # Extract specific target
                    demo = self._extract_demo(user_input)
                    action = self._extract_action(user_input)
                    
                    return ParsedCommand(
                        intent=intent,
                        action=action,
                        demo=demo,
                        target=action or demo,
                        confidence=0.6,
                        explanation=f"Detected {intent.value} from keywords: {keyword}"
                    )
        
        return ParsedCommand(
            intent=Intent.UNKNOWN,
            action=None,
            demo=None,
            target=None,
            confidence=0.0,
            explanation="No matching keywords found"
        )
    
    def _llm_parse(self, user_input: str, context: Dict) -> ParsedCommand:
        """
        Use Ollama to understand intent - SIMPLIFIED VERSION
        No JSON parsing, just text pattern matching
        """
        
        available_actions = list(self.action_names.keys())
        available_demos = list(self.demo_names.keys())
        
        prompt = f"""
User said: "{user_input}"

What does the user want to do?

Available actions: {', '.join(available_actions)}
Available demos: {', '.join(available_demos)}

Respond in ONE LINE only:

If they want to EXECUTE: respond "EXECUTE: [action name]"
If they want a PLAN: respond "PLAN: [action/demo name]"
If they want to CHECK: respond "CHECK: [action name]"
If they want STATUS: respond "STATUS"
If they want to POLISH: respond "POLISH: [demo name]"
If they want to UNDERSTAND: respond "EXPLAIN: [blocker/system/etc]"
If they want OPTIONS: respond "OPTIONS"
If they want HELP: respond "HELP"
If they want QUIT: respond "QUIT"
If unsure: respond "UNCLEAR: [what you think they want]"

Just respond with the one-line command, nothing else.
"""
        
        try:
            response = self.ollama.analyze_blockers(prompt)
            
            # Simple text parsing - no JSON needed
            response = response.strip().upper()
            
            # Parse the one-line response
            if response.startswith("EXECUTE:"):
                action = response.replace("EXECUTE:", "").strip()
                return ParsedCommand(
                    intent=Intent.EXECUTE_ACTION,
                    action=action,
                    demo=None,
                    target=action,
                    confidence=0.85,
                    explanation=f"LLM detected execute intent for: {action}"
                )
            
            elif response.startswith("PLAN:"):
                target = response.replace("PLAN:", "").strip()
                demo = self._extract_demo_from_text(target)
                action = self._extract_action_from_text(target) if not demo else None
                return ParsedCommand(
                    intent=Intent.CREATE_PLAN,
                    action=action,
                    demo=demo,
                    target=target,
                    confidence=0.85,
                    explanation=f"LLM detected plan intent for: {target}"
                )
            
            elif response.startswith("CHECK:"):
                action = response.replace("CHECK:", "").strip()
                return ParsedCommand(
                    intent=Intent.CHECK_CAPABILITY,
                    action=action,
                    demo=None,
                    target=action,
                    confidence=0.85,
                    explanation=f"LLM detected check intent for: {action}"
                )
            
            elif response.startswith("STATUS"):
                return ParsedCommand(
                    intent=Intent.SHOW_STATUS,
                    action=None,
                    demo=None,
                    target=None,
                    confidence=0.85,
                    explanation="LLM detected status request"
                )
            
            elif response.startswith("POLISH:"):
                demo = response.replace("POLISH:", "").strip()
                return ParsedCommand(
                    intent=Intent.POLISH_DEMO,
                    action=None,
                    demo=demo,
                    target=demo,
                    confidence=0.85,
                    explanation=f"LLM detected polish intent for: {demo}"
                )
            
            elif response.startswith("EXPLAIN:"):
                target = response.replace("EXPLAIN:", "").strip()
                return ParsedCommand(
                    intent=Intent.EXPLAIN_BLOCKER,
                    action=None,
                    demo=None,
                    target=target,
                    confidence=0.85,
                    explanation=f"LLM detected explain intent for: {target}"
                )
            
            elif response.startswith("OPTIONS"):
                return ParsedCommand(
                    intent=Intent.LIST_OPTIONS,
                    action=None,
                    demo=None,
                    target=None,
                    confidence=0.85,
                    explanation="LLM detected options request"
                )
            
            elif response.startswith("HELP"):
                return ParsedCommand(
                    intent=Intent.GET_HELP,
                    action=None,
                    demo=None,
                    target=None,
                    confidence=0.85,
                    explanation="LLM detected help request"
                )
            
            elif response.startswith("QUIT"):
                return ParsedCommand(
                    intent=Intent.QUIT,
                    action=None,
                    demo=None,
                    target=None,
                    confidence=0.85,
                    explanation="LLM detected quit intent"
                )
            
            elif response.startswith("UNCLEAR:"):
                what = response.replace("UNCLEAR:", "").strip()
                return ParsedCommand(
                    intent=Intent.UNKNOWN,
                    action=None,
                    demo=None,
                    target=None,
                    confidence=0.3,
                    explanation=f"LLM unclear: {what}"
                )
            
            else:
                # Fallback to fast parse if response format unexpected
                return self._fast_parse(user_input)
        
        except Exception as e:
            # If LLM fails, fall back to fast parsing
            return self._fast_parse(user_input)
    
    def _extract_demo_from_text(self, text: str) -> str:
        """Extract demo name from text"""
        text = text.lower()
        for demo, keywords in self.demo_names.items():
            for keyword in keywords:
                if keyword in text:
                    return demo
        return None
    
    def _extract_action_from_text(self, text: str) -> str:
        """Extract action name from text"""
        text = text.lower()
        for action, keywords in self.action_names.items():
            for keyword in keywords:
                if keyword in text:
                    return action
        return None
    
    def _extract_demo(self, user_input: str) -> Optional[str]:
        """Extract demo name from input"""
        for demo, keywords in self.demo_names.items():
            for keyword in keywords:
                if keyword in user_input:
                    return demo
        return None
    
    def _extract_action(self, user_input: str) -> Optional[str]:
        """Extract action name from input"""
        for action, keywords in self.action_names.items():
            for keyword in keywords:
                if keyword in user_input:
                    return action
        return None


class ConversationalInterface:
    """Conversational chat interface for ADJ"""
    
    def __init__(self, project_root, ollama_client=None):
        self.project_root = project_root
        self.ollama = ollama_client
        self.parser = IntentParser(ollama_client)
        self.context = {}
    
    def run_chat_loop(self, initial_context: Dict = None) -> None:
        """Run interactive chat session"""
        
        if initial_context:
            self.context = initial_context
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              ADJ INTERACTIVE MODE                             ║
╚══════════════════════════════════════════════════════════════╝

You can now chat naturally about what you want to do.

Examples:
  "check if we can build T_3_0"
  "what should I do next"
  "plan the dungeon completion"
  "execute the rendering system"
  "show me the blockers"
  "help me understand why we're stuck"

Type 'quit' or 'exit' to leave.

""")
        
        while True:
            try:
                user_input = input("you> ").strip()
                
                if not user_input:
                    continue
                
                # Parse intent
                parsed = self.parser.parse(user_input, self.context)
                
                # Execute based on intent
                self._handle_intent(parsed)
                
            except KeyboardInterrupt:
                print("\n\nExiting ADJ")
                break
            except EOFError:
                break
    
    def _handle_intent(self, parsed: ParsedCommand) -> None:
        """Handle parsed intent"""
        
        if parsed.intent == Intent.QUIT:
            print("Exiting ADJ")
            exit(0)
        
        elif parsed.intent == Intent.EXECUTE_ACTION:
            if parsed.action:
                print(f"\n🚀 Executing: {parsed.action}...")
                self._execute_action(parsed.action)
            else:
                print("❓ Which action would you like to execute?")
                self._list_actions()
        
        elif parsed.intent == Intent.CREATE_PLAN:
            if parsed.action:
                print(f"\n📋 Creating plan for: {parsed.action}...")
                self._create_plan(parsed.action)
            elif parsed.demo:
                print(f"\n📋 Creating plan for: Complete {parsed.demo}...")
                self._create_plan(f"Complete {parsed.demo}")
            else:
                print("❓ What would you like to plan?")
                self._list_actions()
        
        elif parsed.intent == Intent.CHECK_CAPABILITY:
            if parsed.action:
                print(f"\n🔍 Checking if agent can handle: {parsed.action}...")
                self._check_capability(parsed.action)
            else:
                print("❓ Check capability for what?")
        
        elif parsed.intent == Intent.SHOW_STATUS:
            print(f"\n📊 Current project status:")
            self._show_status()
        
        elif parsed.intent == Intent.POLISH_DEMO:
            if parsed.demo:
                print(f"\n🎨 Polishing {parsed.demo} demo...")
                self._polish_demo(parsed.demo)
            else:
                print("❓ Which demo would you like to polish?")
                self._list_demos()
        
        elif parsed.intent == Intent.EXPLAIN_BLOCKER:
            print(f"\n📖 Explaining blockers...")
            self._explain_blockers()
        
        elif parsed.intent == Intent.LIST_OPTIONS:
            print(f"\n📋 Available options:")
            self._list_all_options()
        
        elif parsed.intent == Intent.GET_HELP:
            self._show_help()
        
        else:  # UNKNOWN
            print(f"\n❓ I'm not sure what you mean. Confidence: {parsed.confidence*100:.0f}%")
            print(f"   (Thought you said: {parsed.explanation})")
            print(f"\n   You can say things like:")
            self._show_help()
    
    def _execute_action(self, action: str) -> None:
        """Execute an action"""
        print(f"   [Would execute: {action}]")
        # TODO: Call actual execution
    
    def _create_plan(self, action: str) -> None:
        """Create a detailed plan"""
        print(f"   [Would create plan for: {action}]")
        # TODO: Call actual plan creation
    
    def _check_capability(self, action: str) -> None:
        """Check if agent can handle action"""
        print(f"   [Would check: Can agent handle {action}?]")
        # TODO: Call failure detector
    
    def _show_status(self) -> None:
        """Show project status"""
        print(f"   [Showing current project status]")
        # TODO: Show status from context
    
    def _polish_demo(self, demo: str) -> None:
        """Polish a specific demo"""
        print(f"   [Would polish: {demo}]")
        # TODO: Call actual polish
    
    def _explain_blockers(self) -> None:
        """Explain blockers"""
        print(f"   [Explaining blockers and dependencies]")
        # TODO: Show blockers and why
    
    def _list_all_options(self) -> None:
        """List all available options"""
        self._list_actions()
        print()
        self._list_demos()
    
    def _list_actions(self) -> None:
        """List available actions"""
        print("   Actions you can execute:")
        for action in self.parser.action_names.keys():
            print(f"     • {action}")
    
    def _list_demos(self) -> None:
        """List available demos"""
        print("   Demos you can work on:")
        for demo in self.parser.demo_names.keys():
            print(f"     • {demo}")
    
    def _show_help(self) -> None:
        """Show help"""
        print("""
   You can say things like:
     • "build T_3_0"
     • "plan the dungeon completion"
     • "check if we can do tower defense"
     • "what should I do next"
     • "show me blockers"
     • "polish the dungeon"
     • "help me understand the rendering system"
     • "what are my options"
""")
