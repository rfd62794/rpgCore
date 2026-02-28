"""
Swarm Agent - Integration of swarm coordination with existing BaseAgent system
Uses the robust BaseAgent framework while providing swarm coordination
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger

from src.tools.apj.agents.base_agent import BaseAgent, AgentConfig
from src.tools.apj.agents.model_router import ModelRouter, RoutingDecision
from src.tools.apj.agents.registry import SchemaRegistry
from pydantic_ai import Agent


class SwarmCoordinator(BaseAgent):
    """
    Swarm Coordinator that uses BaseAgent framework
    Coordinates multiple specialized agents using existing infrastructure
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.model_router = ModelRouter()
        self.swarm_agents = {}
        self._initialize_swarm_agents()
    
    def _initialize_swarm_agents(self) -> None:
        """Initialize swarm agents using existing BaseAgent system"""
        
        # Define swarm agent configurations
        swarm_configs = {
            "coordinator": {
                "name": "swarm_coordinator",
                "role": "Coordinate swarm tasks and manage agent orchestration",
                "department": "planning",
                "model_preference": "local",
                "prompts": {
                    "system": "docs/agents/prompts/coordinator_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                "schema_name": "SwarmTaskAssignment",
                "fallback": {
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Use single agent analysis",
                        "rationale": "Swarm coordination failed",
                        "risk": "low"
                    }
                }
            },
            "analyzer": {
                "name": "swarm_analyzer",
                "role": "Analyze codebase and project state",
                "department": "analysis",
                "model_preference": "local",
                "prompts": {
                    "system": "docs/agents/prompts/analyzer_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                "schema_name": "AnalysisReport",
                "fallback": {
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Manual analysis",
                        "rationale": "Agent analysis failed",
                        "risk": "low"
                    }
                }
            },
            "planner": {
                "name": "swarm_planner",
                "role": "Create detailed implementation plans",
                "department": "planning",
                "model_preference": "local",
                "prompts": {
                    "system": "docs/agents/prompts/generic_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                "schema_name": "ImplementationPlan",
                "fallback": {
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Manual task assignment",
                        "rationale": "Swarm coordination failed - use manual analysis",
                        "risk": "low"
                    },
                    "alternatives": []
                },
                "open_questions": ["Can you provide more specific details?"],
                "archivist_risks_addressed": [],
                "corpus_hash": ""
            },
            "coder": {
                "name": "swarm_coder",
                "role": "Generate and modify code following patterns",
                "department": "execution",
                "model_preference": "local",
                "prompts": {
                    "system": "docs/agents/prompts/generic_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                "schema_name": "CodeChanges",
                "fallback": {
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Manual task assignment",
                        "rationale": "Swarm coordination failed - use manual analysis",
                        "risk": "low"
                    },
                    "alternatives": []
                }
            },
            "tester": {
                "name": "swarm_tester",
                "role": "Run tests and validate implementation",
                "department": "execution",
                "model_preference": "local",
                "prompts": {
                    "system": "docs/agents/prompts/generic_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                "schema_name": "TestResults",
                "fallback": {
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Manual task assignment",
                        "rationale": "Swarm coordination failed - use manual analysis",
                        "risk": "low"
                    },
                    "alternatives": []
                },
                "open_questions": ["Can you provide more specific details?"],
                "archivist_risks_addressed": [],
                "corpus_hash": ""
            },
            "reviewer": {
                "name": "swarm_reviewer",
                "role": "Review code and decisions for quality",
                "department": "analysis",
                "model_preference": "local",
                "prompts": {
                    "system": "docs/agents/prompts/generic_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                "schema_name": "ReviewReport",
                "fallback": {
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Manual task assignment",
                        "rationale": "Swarm coordination failed - use manual analysis",
                        "risk": "low"
                    },
                    "alternatives": []
                },
                "open_questions": ["Can you provide more specific details?"],
                "archivist_risks_addressed": [],
                "corpus_hash": ""
            },
            "executor": {
                "name": "swarm_executor",
                "role": "Execute actions and commands",
                "department": "execution",
                "model_preference": "local",
                "prompts": {
                    "system": "docs/agents/prompts/generic_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                "schema_name": "ExecutionReport",
                "fallback": {
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Manual task assignment",
                        "rationale": "Swarm coordination failed - use manual analysis",
                        "risk": "low"
                    },
                    "alternatives": []
                },
                "open_questions": ["Can you provide more specific details?"],
                "archivist_risks_addressed": [],
                "corpus_hash": ""
            }
        }
        
        # Initialize each swarm agent
        for agent_type, config_data in swarm_configs.items():
            try:
                # Create AgentConfig from dict
                config = AgentConfig(**config_data)
                
                # Create BaseAgent instance
                agent = BaseAgent(config)
                self.swarm_agents[agent_type] = agent
                
                logger.info(f"Initialized swarm agent: {agent_type}")
                
            except Exception as e:
                logger.error(f"Failed to initialize {agent_type}: {e}")
                # Create fallback agent
                self.swarm_agents[agent_type] = self._create_fallback_agent(agent_type)
    
    def _create_fallback_agent(self, agent_type: str) -> BaseAgent:
        """Create a fallback agent using existing LocalAgent"""
        
        fallback_config = AgentConfig(
            name=f"fallback_{agent_type}",
            role=f"Fallback {agent_type} agent",
            department="execution",
            model_preference="local",
            prompts={
                "system": "docs/agents/prompts/generic_system.md",
                "fewshot": "docs/agents/prompts/generic_system.md"
            },
            schema_name="GenericResponse",
            fallback={
                "recommended": {
                    "label": "FALLBACK",
                    "title": "Manual fallback",
                    "rationale": "Agent system failed",
                    "risk": "low"
                },
                "alternatives": []
            },
            open_questions=["Can you provide more specific details?"],
            archivist_risks_addressed=[],
            corpus_hash=""
        )
        
        return BaseAgent(fallback_config)
    
    def process_request(self, user_request: str, context: Dict) -> Dict:
        """
        Process user request through swarm coordination
        Uses existing BaseAgent framework for each agent
        """
        
        logger.info(f"Processing swarm request: {user_request}")
        
        # Step 1: Use coordinator to analyze and plan
        coordinator_result = self._call_agent(
            "coordinator",
            f"""
User request: "{user_request}"

Available swarm agents: {list(self.swarm_agents.keys())}

Project context:
{json.dumps(context.get('project_status', {}), indent=2)}

Analyze this request and create a task assignment plan.
Use the SwarmTaskAssignment schema for structured output.
"""
        )
        
        # Step 2: Execute task assignments
        if hasattr(coordinator_result, 'tasks'):
            # Pydantic object format
            return self._execute_swarm_tasks(coordinator_result.tasks, context)
        elif isinstance(coordinator_result, dict) and 'tasks' in coordinator_result:
            # Dict format
            return self._execute_swarm_tasks(coordinator_result['tasks'], context)
        else:
            # Fallback: single agent execution
            return self._fallback_execution(user_request, context)
    
    def _call_agent(self, agent_type: str, prompt: str) -> Any:
        """Call a specific swarm agent using BaseAgent framework"""
        
        if agent_type not in self.swarm_agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent = self.swarm_agents[agent_type]
        
        try:
            # Use BaseAgent.run() method with the prompt
            result = agent.run(prompt)
            return result
                
        except Exception as e:
            logger.error(f"Error calling {agent_type}: {e}")
            return {"error": f"Agent {agent_type} failed: {e}"}
    
    def _execute_swarm_tasks(self, tasks: List[Dict], context: Dict) -> Dict:
        """Execute swarm tasks using existing BaseAgent system"""
        
        results = {}
        
        for task in tasks:
            # Handle both dict and Pydantic object formats
            if hasattr(task, 'task_id'):
                # Pydantic object format
                task_id = task.task_id
                agent_type = task.agent
                description = task.description
                focus = getattr(task, 'focus', None)
            else:
                # Dict format
                task_id = task.get("task_id", f"task_{len(results)}")
                agent_type = task.get("agent", "analyzer")
                description = task.get("description", "")
                focus = task.get("focus", None)
            
            print(f" Executing task: {task_id}")
            
            # Normalize agent type
            agent_type = self._normalize_agent_type(agent_type)
            
            if agent_type not in self.swarm_agents:
                results[task_id] = {"error": f"Agent {agent_type} not available"}
                continue
            
            # Execute task using BaseAgent
            task_prompt = f"""
Task: {description}

Context:
{json.dumps(context, indent=2)}

Execute this task and provide detailed results.
Focus: {focus if focus else 'general analysis'}
"""
            
            try:
                result = self._call_agent(agent_type, task_prompt)
                
                results[task_id] = {
                    "agent": agent_type,
                    "result": result,
                    "status": "completed"
                }
                
            except Exception as e:
                results[task_id] = {
                    "agent": agent_type,
                    "error": str(e),
                    "status": "failed"
                }
        
        return results
    
    def _normalize_agent_type(self, agent_type: str) -> str:
        """Normalize agent type names"""
        
        agent_type = agent_type.lower().strip()
        
        # Handle various formats
        if "coordinator" in agent_type:
            return "coordinator"
        elif "analyzer" in agent_type or "analyze" in agent_type:
            return "analyzer"
        elif "planner" in agent_type or "plan" in agent_type:
            return "planner"
        elif "coder" in agent_type or "code" in agent_type:
            return "coder"
        elif "tester" in agent_type or "test" in agent_type:
            return "tester"
        elif "reviewer" in agent_type or "review" in agent_type:
            return "reviewer"
        elif "executor" in agent_type or "execute" in agent_type:
            return "executor"
        else:
            return "analyzer"  # Default fallback
    
    def _fallback_execution(self, user_request: str, context: Dict) -> Dict:
        """Fallback execution using analyzer agent"""
        
        fallback_prompt = f"""
User request: "{user_request}"

Context:
{json.dumps(context, indent=2)}

Please analyze this request and provide a helpful response.
"""
        
        try:
            result = self._call_agent("analyzer", fallback_prompt)
            
            return {
                "fallback_analysis": {
                    "agent": "analyzer",
                    "result": result,
                    "status": "completed"
                }
            }
            
        except Exception as e:
            return {
                "fallback_error": {
                    "error": f"Fallback execution failed: {e}",
                    "status": "failed"
                }
            }
    
    def get_swarm_status(self) -> Dict:
        """Get status of swarm agents"""
        
        return {
            "total_agents": len(self.swarm_agents),
            "available_agents": list(self.swarm_agents.keys()),
            "agent_details": {
                agent_type: {
                    "name": agent.config.name if hasattr(agent, 'config') else agent_type,
                    "role": agent.config.role if hasattr(agent, 'config') else "Unknown",
                    "department": agent.config.department if hasattr(agent, 'config') else "Unknown",
                    "model": agent.config.model_preference if hasattr(agent, 'config') else "Unknown"
                }
                for agent_type, agent in self.swarm_agents.items()
            }
        }
