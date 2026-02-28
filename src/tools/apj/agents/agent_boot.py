"""
Agent Boot Sequence - Initializes and connects all agents in the ecosystem
Wakes up agents, establishes communication, and sets up initial conversations
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import uuid

from .agent_registry import AGENT_REGISTRY, AgentType, AgentCapability
from .swarm_agent import SwarmCoordinator
from .base_agent import AgentConfig
from .a2a_communication import A2A_MANAGER, MessageType, MessagePriority, A2AMessage
from .child_agent import CHILD_AGENT_MANAGER
from .tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)


class AgentBootManager:
    """Manages the complete agent ecosystem boot sequence"""
    
    def __init__(self):
        self.swarm_coordinator = None
        self.boot_time = datetime.now()
        self.initialized_agents = {}
        self.communication_links = []
    
    def boot_ecosystem(self, project_status: Dict[str, Any]) -> Dict[str, Any]:
        """Complete boot sequence for all agents"""
        
        logger.info("🚀 Starting Agent Ecosystem Boot Sequence")
        
        boot_results = {
            "start_time": self.boot_time.isoformat(),
            "phases": {},
            "agents": {},
            "communication": {},
            "errors": []
        }
        
        try:
            # Phase 1: Initialize Swarm Coordinator
            boot_results["phases"]["swarm_init"] = self._boot_swarm_coordinator()
            
            # Phase 2: Initialize Existing Agents
            boot_results["phases"]["existing_agents"] = self._boot_existing_agents()
            
            # Phase 3: Establish Communication Links
            boot_results["phases"]["communication"] = self._establish_communication_links()
            
            # Phase 4: Initial Agent Conversations
            boot_results["phases"]["conversations"] = self._start_initial_conversations(project_status)
            
            # Phase 5: Create Specialized Child Agents
            boot_results["phases"]["child_agents"] = self._create_specialized_children(project_status)
            
            # Phase 6: Final Status Report
            boot_results["phases"]["status"] = self._generate_boot_status()
            
            boot_results["success"] = True
            logger.info("✅ Agent Ecosystem Boot Complete")
            
        except Exception as e:
            boot_results["success"] = False
            boot_results["errors"].append(str(e))
            logger.error(f"❌ Agent Ecosystem Boot Failed: {e}")
        
        return boot_results
    
    def _boot_swarm_coordinator(self) -> Dict[str, Any]:
        """Initialize the swarm coordinator"""
        logger.info("🐝 Initializing Swarm Coordinator")
        
        try:
            # Create swarm coordinator config
            swarm_config = AgentConfig(
                name="swarm_coordinator",
                role="Master coordinator for agent ecosystem",
                department="coordination",
                model_preference="local",
                prompts={
                    "system": "docs/agents/prompts/coordinator_system.md",
                    "fewshot": "docs/agents/prompts/generic_system.md"
                },
                schema_name="SwarmTaskAssignment",
                fallback={
                    "recommended": {
                        "label": "FALLBACK",
                        "title": "Use individual agents",
                        "rationale": "Swarm coordination failed",
                        "risk": "medium"
                    },
                    "alternatives": []
                },
                open_questions=[],
                archivist_risks_addressed=[],
                corpus_hash=""
            )
            
            # Initialize swarm coordinator
            self.swarm_coordinator = SwarmCoordinator(swarm_config, force_reinit=True)
            self.initialized_agents["swarm_coordinator"] = self.swarm_coordinator
            
            return {
                "success": True,
                "agent_count": len(self.swarm_coordinator.swarm_agents),
                "available_agents": list(self.swarm_coordinator.swarm_agents.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to boot swarm coordinator: {e}")
            return {"success": False, "error": str(e)}
    
    def _boot_existing_agents(self) -> Dict[str, Any]:
        """Initialize existing specialist agents"""
        logger.info("🤖 Initializing Existing Specialist Agents")
        
        results = {
            "success": True,
            "agents": {},
            "failed": []
        }
        
        existing_agents = AGENT_REGISTRY.get_agents_by_type(AgentType.SPECIALIST)
        
        for agent_metadata in existing_agents:
            try:
                agent = AGENT_REGISTRY.create_agent_instance(agent_metadata.name)
                if agent:
                    self.initialized_agents[agent_metadata.name] = agent
                    results["agents"][agent_metadata.name] = {
                        "capabilities": [cap.value for cap in agent_metadata.capabilities],
                        "department": agent_metadata.department,
                        "supports_a2a": agent_metadata.supports_a2a
                    }
                    logger.info(f"✅ Initialized agent: {agent_metadata.name}")
                else:
                    results["failed"].append(agent_metadata.name)
                    logger.warning(f"❌ Failed to initialize: {agent_metadata.name}")
                    
            except Exception as e:
                results["failed"].append(agent_metadata.name)
                results["success"] = False
                logger.error(f"❌ Error initializing {agent_metadata.name}: {e}")
        
        return results
    
    def _establish_communication_links(self) -> Dict[str, Any]:
        """Establish communication links between agents"""
        logger.info("🔗 Establishing Agent Communication Links")
        
        results = {
            "success": True,
            "links": [],
            "failed": []
        }
        
        # Register all agents for A2A communication
        for agent_name, agent in self.initialized_agents.items():
            if AGENT_REGISTRY.supports_a2a(agent_name):
                try:
                    # Create message handler for agent
                    from .a2a_communication import MessageHandler
                    handler = MessageHandler(agent_name)
                    
                    # Register basic handlers
                    handler.register_handler(MessageType.REQUEST, self._create_request_handler(agent))
                    handler.register_handler(MessageType.NOTIFICATION, self._create_notification_handler(agent))
                    
                    # Register with A2A manager
                    A2A_MANAGER.register_agent(agent_name, handler)
                    results["links"].append(agent_name)
                    logger.info(f"🔗 Connected {agent_name} to A2A network")
                    
                except Exception as e:
                    results["failed"].append(agent_name)
                    results["success"] = False
                    logger.error(f"❌ Failed to connect {agent_name}: {e}")
        
        # Ensure swarm coordinator is registered for A2A
        if self.swarm_coordinator and "swarm_coordinator" not in results["links"]:
            try:
                # Create message handler for swarm coordinator
                from .a2a_communication import MessageHandler
                handler = MessageHandler("swarm_coordinator")
                
                # Register handlers
                handler.register_handler(MessageType.REQUEST, self._create_request_handler(self.swarm_coordinator))
                handler.register_handler(MessageType.NOTIFICATION, self._create_notification_handler(self.swarm_coordinator))
                
                # Register with A2A manager
                A2A_MANAGER.register_agent("swarm_coordinator", handler)
                results["links"].append("swarm_coordinator")
                logger.info(f"🔗 Connected swarm_coordinator to A2A network")
                
            except Exception as e:
                results["failed"].append("swarm_coordinator")
                results["success"] = False
                logger.error(f"❌ Failed to connect swarm_coordinator: {e}")
        
        return results
    
    def _create_request_handler(self, agent):
        """Create request handler for agent"""
        def handler(message: A2AMessage) -> A2AMessage:
            try:
                # Process request with agent
                task = message.content.get("task", "")
                result = agent.run(task)
                
                return A2AMessage(
                    id=str(uuid.uuid4()),
                    sender=agent.config.name,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    priority=MessagePriority.NORMAL,
                    content={"result": result, "request_id": message.id},
                    timestamp=datetime.now(),
                    reply_to=message.id
                )
            except Exception as e:
                return A2AMessage(
                    id=str(uuid.uuid4()),
                    sender=agent.config.name,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    priority=MessagePriority.NORMAL,
                    content={"error": str(e), "request_id": message.id},
                    timestamp=datetime.now(),
                    reply_to=message.id
                )
        return handler
    
    def _create_notification_handler(self, agent):
        """Create notification handler for agent"""
        def handler(message: A2AMessage) -> None:
            logger.info(f"📢 {agent.config.name} received notification: {message.content}")
        return handler
    
    def _start_initial_conversations(self, project_status: Dict[str, Any]) -> Dict[str, Any]:
        """Start initial conversations based on project status"""
        logger.info("💬 Starting Initial Agent Conversations")
        
        results = {
            "success": True,
            "conversations": [],
            "failed": []
        }
        
        try:
            # Wait a moment for A2A registration to complete
            import time
            time.sleep(0.1)
            
            # Conversation 1: Coordinator asks strategist about current blockers
            if "strategist" in self.initialized_agents:
                try:
                    message_id = self.swarm_coordinator.send_a2a_message(
                        recipient="strategist",
                        message_type=MessageType.REQUEST,
                        content={
                            "task": "Analyze current project blockers and recommend strategy",
                            "context": {
                                "blockers": project_status.get("blockers", []),
                                "goals": project_status.get("goals", {}),
                                "next_actions": project_status.get("next_actions", [])
                            }
                        },
                        priority=MessagePriority.HIGH
                    )
                    results["conversations"].append({
                        "type": "coordinator_to_strategist",
                        "message_id": message_id,
                        "topic": "Blocker analysis and strategy"
                    })
                except Exception as e:
                    results["failed"].append(f"coordinator_to_strategist: {e}")
            
            # Conversation 2: Coordinator asks archivist to document current state
            if "archivist" in self.initialized_agents:
                try:
                    message_id = self.swarm_coordinator.send_a2a_message(
                        recipient="archivist",
                        message_type=MessageType.REQUEST,
                        content={
                            "task": "Document current project state and progress",
                            "context": {
                                "project_status": project_status,
                                "timestamp": datetime.now().isoformat()
                            }
                        },
                        priority=MessagePriority.NORMAL
                    )
                    results["conversations"].append({
                        "type": "coordinator_to_archivist",
                        "message_id": message_id,
                        "topic": "Project state documentation"
                    })
                except Exception as e:
                    results["failed"].append(f"coordinator_to_archivist: {e}")
            
            # Conversation 3: Coordinator broadcasts project status to all agents
            try:
                broadcast_id = self.swarm_coordinator.broadcast_to_all_agents({
                    "type": "project_status_update",
                    "status": project_status,
                    "timestamp": datetime.now().isoformat(),
                    "action_required": True
                })
                results["conversations"].append({
                    "type": "broadcast",
                    "message_id": broadcast_id,
                    "topic": "Project status broadcast"
                })
            except Exception as e:
                results["failed"].append(f"broadcast: {e}")
            
            logger.info(f"🗣️ Started {len(results['conversations'])} initial conversations")
            
        except Exception as e:
            results["success"] = False
            results["failed"].append(str(e))
            logger.error(f"❌ Failed to start conversations: {e}")
        
        return results
    
    def _create_specialized_children(self, project_status: Dict[str, Any]) -> Dict[str, Any]:
        """Create specialized child agents based on project needs"""
        logger.info("👶 Creating Specialized Child Agents")
        
        results = {
            "success": True,
            "children": [],
            "failed": []
        }
        
        try:
            # Extract blockers and demos from project status
            blockers = project_status.get("blockers", [])
            demos = project_status.get("demos", {})
            
            # Child agent 1: ECS Rendering Specialist
            if any("ECS RenderingSystem missing" in str(blocker) for blocker in blockers):
                child_id = self.swarm_coordinator.create_child_agent(
                    purpose="Implement ECS Rendering System",
                    capabilities=["coding", "testing", "analysis"],
                    tools=["file_ops", "code_ops", "test_ops", "system_ops"],
                    lifespan=100
                )
                if child_id:
                    results["children"].append({
                        "id": child_id,
                        "purpose": "ECS Rendering System implementation",
                        "capabilities": ["coding", "testing", "analysis"]
                    })
            
            # Child agent 2: Dungeon Demo Polisher
            if "dungeon" in demos:
                if demos.get("dungeon") == "INCOMPLETE":
                    child_id = self.swarm_coordinator.create_child_agent(
                        purpose="Complete and polish dungeon demo",
                        capabilities=["coding", "testing", "review"],
                        tools=["file_ops", "code_ops", "test_ops"],
                        lifespan=150
                    )
                    if child_id:
                        results["children"].append({
                            "id": child_id,
                            "purpose": "Dungeon demo completion",
                            "capabilities": ["coding", "testing", "review"]
                        })
            
            # Child agent 3: Tower Defense Architect
            if "tower_defense" in demos:
                if demos.get("tower_defense") == "INCOMPLETE":
                    child_id = self.swarm_coordinator.create_child_agent(
                        purpose="Design and implement Tower Defense demo",
                        capabilities=["planning", "coding", "testing"],
                        tools=["file_ops", "code_ops", "test_ops", "system_ops"],
                        lifespan=200
                    )
                    if child_id:
                        results["children"].append({
                            "id": child_id,
                            "purpose": "Tower Defense implementation",
                            "capabilities": ["planning", "coding", "testing"]
                        })
            
            logger.info(f"👶 Created {len(results['children'])} specialized child agents")
            
        except Exception as e:
            results["success"] = False
            results["failed"].append(str(e))
            logger.error(f"❌ Failed to create child agents: {e}")
        
        return results
    
    def _generate_boot_status(self) -> Dict[str, Any]:
        """Generate final boot status report"""
        
        # Process any pending messages
        processed_messages = A2A_MANAGER.process_messages()
        
        # Get comprehensive status
        swarm_status = self.swarm_coordinator.get_swarm_status() if self.swarm_coordinator else {}
        
        status = {
            "boot_time": self.boot_time.isoformat(),
            "duration_seconds": (datetime.now() - self.boot_time).total_seconds(),
            "initialized_agents": len(self.initialized_agents),
            "swarm_status": swarm_status,
            "communication_links": len(A2A_MANAGER._message_handlers),
            "child_agents": len(CHILD_AGENT_MANAGER.get_all_children()),
            "processed_messages": len(processed_messages),
            "available_tools": len(TOOL_REGISTRY.get_all_tools()),
            "ecosystem_health": self._calculate_ecosystem_health()
        }
        
        return status
    
    def _calculate_ecosystem_health(self) -> Dict[str, Any]:
        """Calculate overall ecosystem health metrics"""
        
        health = {
            "overall": "healthy",
            "metrics": {},
            "issues": []
        }
        
        # Agent health
        total_expected = 11  # 7 swarm + 4 existing
        initialized_count = len(self.initialized_agents)
        health["metrics"]["agent_coverage"] = f"{initialized_count}/{total_expected}"
        
        if initialized_count < total_expected * 0.8:
            health["overall"] = "degraded"
            health["issues"].append("Low agent coverage")
        
        # Communication health
        a2a_agents = len([name for name in AGENT_REGISTRY.get_all_agents() 
                           if AGENT_REGISTRY.supports_a2a(name)])
        health["metrics"]["a2a_coverage"] = f"{a2a_agents}/{total_expected}"
        
        # Tool availability
        tool_count = len(TOOL_REGISTRY.get_all_tools())
        health["metrics"]["available_tools"] = tool_count
        
        # Message processing
        pending = len(A2A_MANAGER._message_queue)
        health["metrics"]["pending_messages"] = pending
        
        if pending > 10:
            health["overall"] = "stressed"
            health["issues"].append("High message queue")
        
        return health

# Global boot manager
AGENT_BOOT_MANAGER = AgentBootManager()
