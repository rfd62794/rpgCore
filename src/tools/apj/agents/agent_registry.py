"""
Agent Registry - Central registry for all agents in the system
Manages agent discovery, capabilities, and swarm integration
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path

from .base_agent import BaseAgent, AgentConfig
from .registry import SCHEMA_REGISTRY

class AgentType(Enum):
    """Agent types in the system"""
    SWARM = "swarm"  # Swarm coordination agents
    SPECIALIST = "specialist"  # Domain-specific agents
    TOOL = "tool"  # Tool/utility agents
    CHILD = "child"  # Dynamically created child agents

class AgentCapability(Enum):
    """Agent capabilities"""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "review"
    EXECUTION = "execution"
    STRATEGY = "strategy"
    ARCHIVAL = "archival"
    COMMUNICATION = "communication"
    DOCUMENTATION = "documentation"
    COORDINATION = "coordination"

@dataclass
class AgentMetadata:
    """Metadata for registered agents"""
    name: str
    agent_type: AgentType
    capabilities: List[AgentCapability]
    department: str
    description: str
    config_file: Optional[str] = None
    tools: List[str] = None
    can_create_children: bool = False
    supports_a2a: bool = False  # Agent-to-Agent communication
    parent_agent: Optional[str] = None
    child_agents: List[str] = None

class AgentRegistry:
    """Central registry for all agents"""
    
    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}
        self._load_existing_agents()
    
    def _load_existing_agents(self):
        """Load existing agents from configs"""
        config_dir = Path("docs/agents/configs")
        
        # Load known existing agents
        existing_agents = {
            "strategist": AgentMetadata(
                name="strategist",
                agent_type=AgentType.SPECIALIST,
                capabilities=[AgentCapability.STRATEGY, AgentCapability.PLANNING],
                department="planning",
                description="Strategic planning and goal setting",
                config_file="strategist.yaml",
                can_create_children=True,
                supports_a2a=True
            ),
            "archivist": AgentMetadata(
                name="archivist", 
                agent_type=AgentType.SPECIALIST,
                capabilities=[AgentCapability.ARCHIVAL, AgentCapability.DOCUMENTATION],
                department="memory",
                description="Document management and archival",
                config_file="archivist.yaml",
                can_create_children=False,
                supports_a2a=True
            ),
            "herald": AgentMetadata(
                name="herald",
                agent_type=AgentType.SPECIALIST,
                capabilities=[AgentCapability.COMMUNICATION],
                department="persona",
                description="Communication and messaging",
                config_file="herald.yaml",
                can_create_children=False,
                supports_a2a=True
            ),
            "docstring": AgentMetadata(
                name="docstring",
                agent_type=AgentType.TOOL,
                capabilities=[AgentCapability.DOCUMENTATION],
                department="tools",
                description="Code documentation generation",
                config_file="docstring.yaml",
                can_create_children=False,
                supports_a2a=False
            )
        }
        
        # Add swarm agents
        swarm_agents = {
            "coordinator": AgentMetadata(
                name="coordinator",
                agent_type=AgentType.SWARM,
                capabilities=[AgentCapability.PLANNING, AgentCapability.COORDINATION],
                department="planning",
                description="Swarm task coordination",
                can_create_children=True,
                supports_a2a=True
            ),
            "analyzer": AgentMetadata(
                name="analyzer",
                agent_type=AgentType.SWARM,
                capabilities=[AgentCapability.ANALYSIS],
                department="analysis",
                description="Codebase analysis",
                can_create_children=False,
                supports_a2a=True
            ),
            "planner": AgentMetadata(
                name="planner",
                agent_type=AgentType.SWARM,
                capabilities=[AgentCapability.PLANNING],
                department="planning",
                description="Implementation planning",
                can_create_children=False,
                supports_a2a=True
            ),
            "coder": AgentMetadata(
                name="coder",
                agent_type=AgentType.SWARM,
                capabilities=[AgentCapability.CODING],
                department="execution",
                description="Code generation",
                can_create_children=False,
                supports_a2a=True
            ),
            "tester": AgentMetadata(
                name="tester",
                agent_type=AgentType.SWARM,
                capabilities=[AgentCapability.TESTING],
                department="execution",
                description="Testing and validation",
                can_create_children=False,
                supports_a2a=True
            ),
            "reviewer": AgentMetadata(
                name="reviewer",
                agent_type=AgentType.SWARM,
                capabilities=[AgentCapability.REVIEW],
                department="analysis",
                description="Code review",
                can_create_children=False,
                supports_a2a=True
            ),
            "executor": AgentMetadata(
                name="executor",
                agent_type=AgentType.SWARM,
                capabilities=[AgentCapability.EXECUTION],
                department="execution",
                description="Command execution",
                can_create_children=False,
                supports_a2a=True
            )
        }
        
        self._agents.update(existing_agents)
        self._agents.update(swarm_agents)
    
    def register_agent(self, metadata: AgentMetadata):
        """Register a new agent"""
        self._agents[metadata.name] = metadata
    
    def get_agent_metadata(self, name: str) -> Optional[AgentMetadata]:
        """Get agent metadata"""
        return self._agents.get(name)
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[AgentMetadata]:
        """Get agents with specific capability"""
        return [agent for agent in self._agents.values() 
                if capability in agent.capabilities]
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentMetadata]:
        """Get agents by type"""
        return [agent for agent in self._agents.values() 
                if agent.agent_type == agent_type]
    
    def can_create_children(self, agent_name: str) -> bool:
        """Check if agent can create children"""
        metadata = self.get_agent_metadata(agent_name)
        return metadata.can_create_children if metadata else False
    
    def supports_a2a(self, agent_name: str) -> bool:
        """Check if agent supports A2A communication"""
        metadata = self.get_agent_metadata(agent_name)
        return metadata.supports_a2a if metadata else False
    
    def get_all_agents(self) -> Dict[str, AgentMetadata]:
        """Get all registered agents"""
        return self._agents.copy()
    
    def create_agent_instance(self, name: str) -> Optional[BaseAgent]:
        """Create agent instance from config"""
        metadata = self.get_agent_metadata(name)
        if not metadata or not metadata.config_file:
            return None
        
        try:
            # Try to load config directly
            config_path = Path("docs/agents/configs") / f"{metadata.config_file}"
            if config_path.exists():
                config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                config = AgentConfig(**config_data)
                agent = BaseAgent(config)
                self._agent_instances[name] = agent
                return agent
            else:
                # Fallback to from_config method
                config = AgentConfig.from_config(name)
                agent = BaseAgent(config)
                self._agent_instances[name] = agent
                return agent
        except Exception as e:
            print(f"Failed to create agent {name}: {e}")
            return None
    
    def get_agent_instance(self, name: str) -> Optional[BaseAgent]:
        """Get existing agent instance or create new one"""
        if name in self._agent_instances:
            return self._agent_instances[name]
        return self.create_agent_instance(name)

# Global agent registry
AGENT_REGISTRY = AgentRegistry()
