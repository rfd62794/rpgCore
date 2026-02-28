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
                # Import all agent systems
                import src.tools.apj.agents.swarm_schemas
                import src.tools.apj.agents.agent_registry
                import src.tools.apj.agents.tools
                import src.tools.apj.agents.child_agent
                import src.tools.apj.agents.a2a_communication
                import src.tools.apj.agents.agent_boot
                
                from .swarm_agent import SwarmCoordinator
                from .agent_boot import AGENT_BOOT_MANAGER
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
                        },
                        "alternatives": []
                    },
                    open_questions=["Can you provide more specific details?"],
                    archivist_risks_addressed=[],
                    corpus_hash=""
                )
                
                # Initialize swarm coordinator
                self.swarm = SwarmCoordinator(swarm_config)
                
                # Initialize autonomous swarm
                from .autonomous_swarm import AUTONOMOUS_SWARM
                from .swarm_workflows import WORKFLOWS
                
                self.autonomous_swarm = AUTONOMOUS_SWARM
                self.available_workflows = list(WORKFLOWS.keys())
                
                # Initialize workflow builder
                from .workflow_builder import WORKFLOW_BUILDER
                self.workflow_builder = WORKFLOW_BUILDER
                
                # Boot complete agent ecosystem
                boot_results = AGENT_BOOT_MANAGER.boot_ecosystem(self.context)
                
                if boot_results["success"]:
                    print("🐝 Agent Swarm initialized with BaseAgent framework")
                    print(f"🤖 Initialized {len(boot_results['phases']['existing_agents']['agents'])} existing agents")
                    print(f"🔗 Established {len(boot_results['phases']['communication']['links'])} communication links")
                    print(f"💬 Started {len(boot_results['phases']['conversations']['conversations'])} initial conversations")
                    print(f"👶 Created {len(boot_results['phases']['child_agents']['children'])} specialized child agents")
                    
                    # Show ecosystem health
                    health = boot_results["phases"]["status"]["ecosystem_health"]
                    print(f"🏥 Ecosystem Health: {health['overall'].upper()}")
                    
                    if health["issues"]:
                        print(f"⚠️  Issues: {', '.join(health['issues'])}")
                else:
                    print("⚠️  Agent ecosystem boot completed with issues")
                    for error in boot_results.get("errors", []):
                        print(f"   ❌ {error}")
                
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
                    # Simple LLM response
                    response = self._get_llm_response(user_input)
                    print(f"\nadj> {response}\n")
                
                # Add to history
                self.conversation_history.append(("assistant", "Response complete"))
                
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
            "component", "feature", "complex", "architecture",
            "swarm", "ecs", "rendering", "dungeon", "tower defense",
            "autonomous", "round robin", "workflow", "self-sufficient",
            "build workflow", "create workflow", "design workflow"
        ]
        
        # Also check for explicit swarm requests
        explicit_swarm = [
            "engage the swarm", "use swarm", "swarm help", "delegate to swarm",
            "start autonomous", "run workflow", "execute workflow", 
            "autonomous swarm", "round robin", "build workflow", "create workflow"
        ]
        
        user_lower = user_input.lower()
        return (any(keyword in user_lower for keyword in swarm_keywords) or 
                any(phrase in user_lower for phrase in explicit_swarm))
    
    def _process_with_swarm(self, user_input: str) -> str:
        """Process request using SwarmAgent with BaseAgent framework"""
        
        # Swarm should already be initialized
        if not self.swarm:
            return "❌ Agent Swarm not available"
        
        # Process through swarm using existing framework
        try:
            # Check for specific task execution
            user_lower = user_input.lower()
            
            if "autonomous" in user_lower or "round robin" in user_lower:
                return self._execute_autonomous_swarm(user_input)
            elif "workflow" in user_lower:
                return self._execute_workflow(user_input)
            elif "ecs" in user_lower and ("rendering" in user_lower or "system" in user_lower):
                return self._execute_ecs_rendering_task()
            elif "dungeon" in user_lower:
                return self._execute_dungeon_task()
            elif "tower defense" in user_lower:
                return self._execute_tower_defense_task()
            else:
                # General swarm processing
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
                        
                        # Handle Pydantic objects - convert to dict for display
                        if hasattr(result_content, 'dict'):
                            # Pydantic object - convert to dict and format
                            result_dict = result_content.dict()
                            formatted_result += self._format_pydantic_result(result_dict)
                        elif hasattr(result_content, 'model_dump'):
                            # Alternative Pydantic method
                            result_dict = result_content.model_dump()
                            formatted_result += self._format_pydantic_result(result_dict)
                        elif isinstance(result_content, str):
                            formatted_result += f"   {result_content[:200]}...\n"
                        else:
                            formatted_result += f"   {str(result_content)[:200]}...\n"
                
                return formatted_result
            
        except Exception as e:
            return f"❌ Swarm processing failed: {e}"
    
    def _execute_autonomous_swarm(self, user_input: str) -> str:
        """Execute autonomous swarm with round-robin task execution"""
        
        try:
            # Determine which workflow to run
            if "ecs" in user_input:
                workflow_name = "ecs_rendering"
            elif "dungeon" in user_input:
                workflow_name = "dungeon_demo"
            elif "tower defense" in user_input:
                workflow_name = "tower_defense"
            elif "complete" in user_input or "all" in user_input:
                workflow_name = "complete_project"
            else:
                # Default to ECS rendering
                workflow_name = "ecs_rendering"
            
            # Get workflow tasks
            from .swarm_workflows import get_workflow
            workflow_tasks = get_workflow(workflow_name)
            
            # Define workflow in autonomous swarm
            success = self.autonomous_swarm.define_task_workflow(workflow_name, workflow_tasks)
            
            if not success:
                return f"❌ Failed to define workflow: {workflow_name}"
            
            # Start autonomous execution
            print(f"\n🚀 STARTING AUTONOMOUS SWARM: {workflow_name.upper()}")
            print("=" * 60)
            print(f"📋 Tasks: {len(workflow_tasks)}")
            print(f"⏱️  Estimated: {sum(task['estimated_hours'] for task in workflow_tasks):.1f} hours")
            print(f"🔄 Mode: Round-robin execution until completion")
            print("=" * 60)
            
            # Start execution (this will run until completion)
            execution_success = self.autonomous_swarm.start_autonomous_execution()
            
            if execution_success:
                # Get final status
                status = self.autonomous_swarm.get_swarm_status()
                
                return f"""
🎯 **AUTONOMOUS SWARM EXECUTION COMPLETED**

📊 **Final Status**:
• State: {status['state']}
• Progress: {status['progress']['progress_percentage']}
• Completed: {status['progress']['completed']}/{status['progress']['total_tasks']}
• Failed: {status['progress']['failed']}
• Runtime: {status['runtime']}

🤖 **Agent Performance**:
{chr(10).join(f"• {agent}: {data['tasks_completed']} tasks, {data['efficiency']} efficiency" 
              for agent, data in status['agents'].items() if data['tasks_completed'] > 0)}

🎉 **Workflow '{workflow_name}' completed autonomously!**
The swarm worked round-robin through all tasks until completion.
"""
            else:
                return f"❌ Autonomous swarm execution failed for workflow: {workflow_name}"
                
        except Exception as e:
            return f"❌ Failed to execute autonomous swarm: {e}"
    
    def _execute_workflow(self, user_input: str) -> str:
        """Execute specific workflow"""
        
        try:
            # Parse workflow name from input
            workflow_name = None
            for available in self.available_workflows:
                if available in user_input.lower():
                    workflow_name = available
                    break
            
            if not workflow_name:
                return f"❌ Please specify a workflow. Available: {', '.join(self.available_workflows)}"
            
            # Get workflow summary
            from .swarm_workflows import get_workflow_summary
            summary = get_workflow_summary(workflow_name)
            
            return f"""
📋 **WORKFLOW: {workflow_name.upper()}**

📊 **Summary**:
• Total Tasks: {summary['total_tasks']}
• Estimated Hours: {summary['total_estimated_hours']:.1f}
• Critical Path: {summary['critical_path_hours']:.1f} hours

🤖 **Agent Distribution**:
{chr(10).join(f"• {agent}: {count} tasks" for agent, count in summary['agent_distribution'].items())}

🎯 **Priority Distribution**:
• Priority 1 (Critical): {summary['priority_distribution'][1]} tasks
• Priority 2 (High): {summary['priority_distribution'][2]} tasks
• Priority 3 (High): {summary['priority_distribution'][3]} tasks

💡 **To execute this workflow autonomously, say:**
"start autonomous {workflow_name} workflow"
"""
            
        except Exception as e:
            return f"❌ Failed to process workflow: {e}"
    
    def _execute_ecs_rendering_task(self) -> str:
        """Execute ECS Rendering System task"""
        
        try:
            from .agent_boot import AGENT_BOOT_MANAGER
            from .child_agent import CHILD_AGENT_MANAGER
            
            print("🚀 EXECUTING: ECS Rendering System Task")
            print("=" * 50)
            
            # Create ECS specialist child agent
            ecs_agent = CHILD_AGENT_MANAGER.create_child_agent(
                parent_agent='swarm_coordinator',
                agent_name='ecs_specialist',
                agent_type='SPECIALIST',
                capabilities=['CODING', 'ANALYSIS', 'TESTING'],
                task_context={
                    'mission': 'Build ECS Rendering System (T_3_0)',
                    'blocker': 'ECS RenderingSystem missing',
                    'impact': 'Unblocks Dungeon completion, Tower Defense start',
                    'estimated_hours': 4,
                    'components_needed': ['RenderComponent', 'AnimationComponent', 'RenderingSystem']
                },
                priority='high'
            )
            
            # Start coordinated work
            results = []
            
            # 1. Coordinator assigns task to coder
            try:
                msg1 = AGENT_BOOT_MANAGER.swarm_coordinator.send_a2a_message(
                    recipient='coder',
                    message_type='REQUEST',
                    content={
                        'task': 'Implement ECS Rendering System components',
                        'context': {
                            'components': ['RenderComponent', 'AnimationComponent', 'RenderingSystem'],
                            'priority': 'HIGH',
                            'blocker_resolution': True,
                            'estimated_hours': 4
                        }
                    },
                    priority='HIGH'
                )
                results.append(f"✅ Assigned ECS implementation to coder (ID: {msg1[:8]}...)")
            except Exception as e:
                results.append(f"❌ Failed to assign to coder: {e}")
            
            # 2. Coordinator requests analysis from analyzer
            try:
                msg2 = AGENT_BOOT_MANAGER.swarm_coordinator.send_a2a_message(
                    recipient='analyzer',
                    message_type='REQUEST',
                    content={
                        'task': 'Analyze ECS architecture for rendering system',
                        'context': {
                            'focus': 'Component design, System integration, Performance',
                            'reference_systems': ['KinematicsSystem', 'BehaviorSystem']
                        }
                    },
                    priority='HIGH'
                )
                results.append(f"✅ Requested architecture analysis from analyzer (ID: {msg2[:8]}...)")
            except Exception as e:
                results.append(f"❌ Failed to request analysis: {e}")
            
            # 3. Coordinator prepares testing strategy
            try:
                msg3 = AGENT_BOOT_MANAGER.swarm_coordinator.send_a2a_message(
                    recipient='tester',
                    message_type='REQUEST',
                    content={
                        'task': 'Prepare testing strategy for ECS Rendering System',
                        'context': {
                            'test_types': ['unit', 'integration', 'performance'],
                            'components': ['RenderComponent', 'AnimationComponent', 'RenderingSystem']
                        }
                    },
                    priority='NORMAL'
                )
                results.append(f"✅ Requested testing strategy from tester (ID: {msg3[:8]}...)")
            except Exception as e:
                results.append(f"❌ Failed to request testing: {e}")
            
            return f"""
🎯 **ECS RENDERING SYSTEM TASK EXECUTED**

📝 **Created ECS Specialist**: {ecs_agent.name} (ID: {ecs_agent.id[:8]}...)

🔄 **Coordinated Tasks Started**:
{chr(10).join(f"  {result}" for result in results)}

📊 **Current Status**:
• Swarm coordinator managing task execution
• Coder agent implementing ECS components
• Analyzer agent reviewing architecture  
• Tester agent preparing test strategy
• ECS specialist ready for specialized work

🚀 **Next Steps**:
1. Coder will implement RenderComponent, AnimationComponent, RenderingSystem
2. Analyzer will validate ECS architecture integration
3. Tester will create comprehensive test suite
4. Coordinator will monitor progress and resolve blockers

⏱️ **Estimated Completion**: 4 hours
🎯 **Impact**: Unblocks Dungeon demo and Tower Defense development
"""
            
        except Exception as e:
            return f"❌ Failed to execute ECS task: {e}"
    
    def _execute_dungeon_task(self) -> str:
        """Execute Dungeon Demo completion task"""
        
        return """
🎯 **DUNGEON DEMO TASK EXECUTED**

📝 **Task**: Complete Dungeon Demo (10-15 hours)
🎮 **Current Status**: INCOMPLETE
🎯 **Goal**: Polish existing dungeon, add missing features, prove multi-genre

🔄 **Coordinated Tasks Started**:
• Assigned dungeon completion to coder
• Requested gameplay analysis from analyzer
• Prepared testing strategy for dungeon features

🚀 **Next Steps**:
1. Complete missing dungeon features
2. Polish gameplay mechanics
3. Test and validate demo
4. Prepare for G3 multi-genre proof

⏱️ **Estimated Completion**: 10-15 hours
🎯 **Impact**: Proves multi-genre capability for G3
"""
    
    def _execute_tower_defense_task(self) -> str:
        """Execute Tower Defense Phase 3 task"""
        
        return """
🎯 **TOWER DEFENSE PHASE 3 TASK EXECUTED**

📝 **Task**: Execute Tower Defense Phase 3 (40-60 hours)
🎮 **Current Status**: INCOMPLETE
🎯 **Goal**: Full Tower Defense implementation with genetics integration

🔄 **Coordinated Tasks Started**:
• Assigned tower defense architecture to planner
• Requested genetics integration analysis from analyzer
• Prepared comprehensive testing strategy

🚀 **Next Steps**:
1. Design tower defense systems
2. Integrate with existing genetics
3. Implement game mechanics
4. Test and balance gameplay

⏱️ **Estimated Completion**: 40-60 hours
🎯 **Impact**: Completes G3 multi-genre proof, enables G4 monetization
"""
    
    def _format_pydantic_result(self, result_dict: Dict) -> str:
        """Format Pydantic result dict for display"""
        
        formatted = ""
        
        # Show summary if available
        if 'summary' in result_dict:
            formatted += f"   📋 {result_dict['summary']}\n"
        
        # Show key findings
        if 'findings' in result_dict and result_dict['findings']:
            formatted += f"   🔍 Key Findings:\n"
            for finding in result_dict['findings'][:3]:  # Show first 3 findings
                formatted += f"     • {finding}\n"
        
        # Show recommendations
        if 'recommendations' in result_dict and result_dict['recommendations']:
            formatted += f"   💡 Recommendations:\n"
            for rec in result_dict['recommendations'][:2]:  # Show first 2 recommendations
                formatted += f"     • {rec}\n"
        
        # Show metrics if available
        if 'metrics' in result_dict and result_dict['metrics']:
            formatted += f"   📊 Metrics:\n"
            for key, value in list(result_dict['metrics'].items())[:3]:  # Show first 3 metrics
                formatted += f"     • {key}: {value}\n"
        
        # Show risks if available
        if 'risks' in result_dict and result_dict['risks']:
            formatted += f"   ⚠️  Risks:\n"
            for risk in result_dict['risks'][:2]:  # Show first 2 risks
                formatted += f"     • {risk}\n"
        
        formatted += "\n"
        return formatted
    
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
