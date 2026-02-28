"""
Autonomous Swarm - Self-sufficient round-robin task execution
Continuously works through tasks until completion without human intervention
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import uuid

from .a2a_communication import A2A_MANAGER, MessageType, MessagePriority
from .agent_registry import AGENT_REGISTRY
from .child_agent import CHILD_AGENT_MANAGER
from .agent_boot import AGENT_BOOT_MANAGER

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class SwarmState(Enum):
    """Swarm operational state"""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SwarmTask:
    """Individual task for swarm execution"""
    id: str
    title: str
    description: str
    agent_type: str  # Which agent type should handle this
    priority: int  # 1-10, lower is higher priority
    estimated_hours: float
    dependencies: List[str]  # Task IDs that must complete first
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class AgentWorkload:
    """Track agent workload and availability"""
    agent_name: str
    current_task: Optional[str] = None
    tasks_completed: int = 0
    total_work_time: float = 0.0  # Hours
    last_activity: Optional[datetime] = None
    efficiency_score: float = 1.0  # Tasks completed per hour
    is_available: bool = True


class AutonomousSwarm:
    """Self-sufficient swarm that executes tasks round-robin"""
    
    def __init__(self):
        self.state = SwarmState.IDLE
        self.tasks: Dict[str, SwarmTask] = {}
        self.agent_workloads: Dict[str, AgentWorkload] = {}
        self.current_task_index = 0
        self.round_robin_cycle = 0
        self.swarm_start_time: Optional[datetime] = None
        self.last_activity: Optional[datetime] = None
        self.task_queue: List[str] = []  # Ordered task IDs
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.blocked_tasks: List[str] = []
        
        # Swarm configuration
        self.max_concurrent_tasks = 3
        self.task_timeout_minutes = 30
        self.round_robin_interval_seconds = 5
        self.auto_retry_enabled = True
        self.progress_reporting_enabled = True
        
        # Initialize agent workloads
        self._initialize_agent_workloads()
    
    def _initialize_agent_workloads(self):
        """Initialize workload tracking for all available agents"""
        
        # Get all swarm agents
        swarm_agents = ["coordinator", "analyzer", "planner", "coder", "tester", "reviewer", "executor"]
        existing_agents = ["strategist", "archivist", "herald"]
        
        all_agents = swarm_agents + existing_agents
        
        for agent_name in all_agents:
            self.agent_workloads[agent_name] = AgentWorkload(
                agent_name=agent_name,
                is_available=True
            )
    
    def define_task_workflow(self, workflow_name: str, tasks: List[Dict[str, Any]]) -> bool:
        """Define a complete workflow of tasks for autonomous execution"""
        
        try:
            logger.info(f"📋 Defining workflow: {workflow_name}")
            
            # Clear existing tasks for this workflow
            workflow_prefix = f"{workflow_name}_"
            self.tasks = {k: v for k, v in self.tasks.items() if not k.startswith(workflow_prefix)}
            
            # Create tasks from workflow definition
            created_tasks = []
            for task_def in tasks:
                task_id = f"{workflow_prefix}_{task_def['title'].lower().replace(' ', '_')}"
                
                task = SwarmTask(
                    id=task_id,
                    title=task_def['title'],
                    description=task_def['description'],
                    agent_type=task_def['agent_type'],
                    priority=task_def.get('priority', 5),
                    estimated_hours=task_def.get('estimated_hours', 1.0),
                    dependencies=task_def.get('dependencies', [])
                )
                
                self.tasks[task_id] = task
                created_tasks.append(task_id)
            
            # Build task queue based on dependencies and priority
            self._build_task_queue()
            
            logger.info(f"✅ Created {len(created_tasks)} tasks for workflow: {workflow_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to define workflow {workflow_name}: {e}")
            return False
    
    def _build_task_queue(self):
        """Build ordered task queue based on dependencies and priority"""
        
        # Simple topological sort with priority ordering
        remaining_tasks = list(self.tasks.values())
        self.task_queue = []
        
        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = []
            for task in remaining_tasks:
                deps_met = all(dep_id in self.completed_tasks for dep_id in task.dependencies)
                if deps_met:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Circular dependency or missing dependency
                logger.warning("⚠️ Circular dependency detected or missing dependencies")
                break
            
            # Sort by priority (lower number = higher priority)
            ready_tasks.sort(key=lambda t: t.priority)
            
            # Add highest priority task to queue
            next_task = ready_tasks[0]
            self.task_queue.append(next_task.id)
            remaining_tasks.remove(next_task)
    
    def start_autonomous_execution(self) -> bool:
        """Start autonomous round-robin execution"""
        
        if self.state == SwarmState.ACTIVE:
            logger.warning("⚠️ Swarm is already active")
            return False
        
        if not self.task_queue:
            logger.warning("⚠️ No tasks in queue to execute")
            return False
        
        logger.info("🚀 Starting Autonomous Swarm Execution")
        self.state = SwarmState.ACTIVE
        self.swarm_start_time = datetime.now()
        self.last_activity = datetime.now()
        
        # Start the autonomous execution loop
        try:
            self._autonomous_execution_loop()
        except KeyboardInterrupt:
            logger.info("⏸️ Swarm execution paused by user")
            self.state = SwarmState.PAUSED
        except Exception as e:
            logger.error(f"❌ Swarm execution error: {e}")
            self.state = SwarmState.ERROR
        
        return True
    
    def _autonomous_execution_loop(self):
        """Main autonomous execution loop - round-robin task assignment"""
        
        logger.info("🔄 Starting round-robin execution loop")
        
        while self.state == SwarmState.ACTIVE:
            try:
                # Check if all tasks are completed
                if self._are_all_tasks_completed():
                    logger.info("✅ All tasks completed!")
                    self.state = SwarmState.COMPLETED
                    break
                
                # Get next available task
                next_task_id = self._get_next_available_task()
                if not next_task_id:
                    # No available tasks - wait for current ones to complete
                    time.sleep(self.round_robin_interval_seconds)
                    continue
                
                # Get best available agent for this task
                task = self.tasks[next_task_id]
                best_agent = self._get_best_available_agent(task.agent_type)
                
                if not best_agent:
                    logger.warning(f"⚠️ No available agents for task: {task.title}")
                    time.sleep(self.round_robin_interval_seconds)
                    continue
                
                # Assign task to agent
                self._assign_task_to_agent(next_task_id, best_agent)
                
                # Execute task
                self._execute_task(next_task_id, best_agent)
                
                # Wait before next assignment
                time.sleep(self.round_robin_interval_seconds)
                
                # Report progress periodically
                if self.progress_reporting_enabled:
                    self._report_progress()
                
            except Exception as e:
                logger.error(f"❌ Error in execution loop: {e}")
                time.sleep(self.round_robin_interval_seconds)
    
    def _get_next_available_task(self) -> Optional[str]:
        """Get next available task from queue"""
        
        for task_id in self.task_queue:
            task = self.tasks[task_id]
            
            # Skip if task is already completed, failed, or in progress
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.IN_PROGRESS]:
                continue
            
            # Check if dependencies are met
            deps_met = all(dep_id in self.completed_tasks for dep_id in task.dependencies)
            if not deps_met:
                continue
            
            return task_id
        
        return None
    
    def _get_best_available_agent(self, required_agent_type: str) -> Optional[str]:
        """Get best available agent for task type"""
        
        # Map task types to agent names
        agent_mapping = {
            "coordinator": ["coordinator", "swarm_coordinator"],
            "analyzer": ["analyzer", "swarm_analyzer"],
            "planner": ["planner", "swarm_planner"],
            "coder": ["coder", "swarm_coder"],
            "tester": ["tester", "swarm_tester"],
            "reviewer": ["reviewer", "swarm_reviewer"],
            "executor": ["executor", "swarm_executor"],
            "strategist": ["strategist"],
            "archivist": ["archivist"],
            "herald": ["herald"]
        }
        
        candidate_agents = agent_mapping.get(required_agent_type, [required_agent_type])
        
        # Find available agents with best efficiency
        available_agents = []
        for agent_name in candidate_agents:
            if agent_name in self.agent_workloads:
                workload = self.agent_workloads[agent_name]
                if workload.is_available and workload.current_task is None:
                    available_agents.append((agent_name, workload.efficiency_score))
        
        if not available_agents:
            return None
        
        # Sort by efficiency score (highest first)
        available_agents.sort(key=lambda x: x[1], reverse=True)
        return available_agents[0][0]
    
    def _assign_task_to_agent(self, task_id: str, agent_name: str):
        """Assign task to specific agent"""
        
        task = self.tasks[task_id]
        workload = self.agent_workloads[agent_name]
        
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_to = agent_name
        task.started_at = datetime.now()
        
        workload.current_task = task_id
        workload.is_available = False
        workload.last_activity = datetime.now()
        
        logger.info(f"📋 Assigned task '{task.title}' to {agent_name}")
    
    def _execute_task(self, task_id: str, agent_name: str) -> bool:
        """Execute task through agent"""
        
        task = self.tasks[task_id]
        workload = self.agent_workloads[agent_name]
        
        try:
            logger.info(f"🔧 Executing task: {task.title} ({agent_name})")
            
            # Send task to agent via A2A communication
            if agent_name.startswith("swarm_"):
                recipient = agent_name.replace("swarm_", "") + "_agent"
            else:
                recipient = agent_name
            
            message_content = {
                "task": task.title,
                "description": task.description,
                "context": {
                    "task_id": task_id,
                    "priority": task.priority,
                    "estimated_hours": task.estimated_hours,
                    "autonomous_execution": True
                }
            }
            
            # Send task message
            message_id = A2A_MANAGER.send_message(
                sender="swarm_coordinator",
                recipient=recipient,
                message_type=MessageType.REQUEST,
                content=message_content,
                priority=MessagePriority.HIGH if task.priority <= 3 else MessagePriority.NORMAL
            )
            
            # Simulate task execution (in real implementation, this would wait for actual completion)
            # For now, we'll simulate based on estimated hours
            execution_time = min(task.estimated_hours * 0.1, 2.0)  # Simulate faster for demo
            time.sleep(execution_time)
            
            # Mark task as completed (simulated)
            self._complete_task(task_id, agent_name, {"message_id": message_id, "simulated": True})
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            self._fail_task(task_id, agent_name, str(e))
            return False
    
    def _complete_task(self, task_id: str, agent_name: str, result: Dict[str, Any]):
        """Mark task as completed"""
        
        task = self.tasks[task_id]
        workload = self.agent_workloads[agent_name]
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result
        
        workload.current_task = None
        workload.is_available = True
        workload.tasks_completed += 1
        workload.total_work_time += task.estimated_hours
        workload.efficiency_score = workload.tasks_completed / max(workload.total_work_time, 0.1)
        
        self.completed_tasks.append(task_id)
        self.last_activity = datetime.now()
        
        logger.info(f"✅ Task completed: {task.title} by {agent_name}")
    
    def _fail_task(self, task_id: str, agent_name: str, error_message: str):
        """Mark task as failed"""
        
        task = self.tasks[task_id]
        workload = self.agent_workloads[agent_name]
        
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        task.retry_count += 1
        
        workload.current_task = None
        workload.is_available = True
        
        if task.retry_count < task.max_retries and self.auto_retry_enabled:
            # Retry task
            task.status = TaskStatus.PENDING
            logger.warning(f"🔄 Retrying task: {task.title} (attempt {task.retry_count + 1})")
        else:
            self.failed_tasks.append(task_id)
            logger.error(f"❌ Task failed permanently: {task.title}")
    
    def _are_all_tasks_completed(self) -> bool:
        """Check if all tasks are completed"""
        
        total_tasks = len(self.tasks)
        completed_tasks = len(self.completed_tasks)
        failed_tasks = len(self.failed_tasks)
        
        return (completed_tasks + failed_tasks) >= total_tasks
    
    def _report_progress(self):
        """Report current swarm progress"""
        
        total_tasks = len(self.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        
        progress_pct = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate swarm efficiency
        total_completed = sum(w.tasks_completed for w in self.agent_workloads.values())
        total_work_time = sum(w.total_work_time for w in self.agent_workloads.values())
        swarm_efficiency = total_completed / max(total_work_time, 0.1)
        
        # Calculate runtime
        if self.swarm_start_time:
            runtime = datetime.now() - self.swarm_start_time
            runtime_str = str(runtime).split('.')[0]  # Remove microseconds
        else:
            runtime_str = "00:00:00"
        
        logger.info(f"📊 Swarm Progress: {progress_pct:.1f}% ({completed}/{total_tasks}) | "
                   f"Active: {in_progress} | Pending: {pending} | Failed: {failed} | "
                   f"Efficiency: {swarm_efficiency:.1f} tasks/hr | Runtime: {runtime_str}")
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive swarm status"""
        
        total_tasks = len(self.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        
        progress_pct = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Agent status
        agent_status = {}
        for agent_name, workload in self.agent_workloads.items():
            agent_status[agent_name] = {
                "available": workload.is_available,
                "current_task": workload.current_task,
                "tasks_completed": workload.tasks_completed,
                "efficiency": f"{workload.efficiency_score:.2f} tasks/hr"
            }
        
        return {
            "state": self.state.value,
            "progress": {
                "total_tasks": total_tasks,
                "completed": completed,
                "failed": failed,
                "in_progress": in_progress,
                "pending": pending,
                "progress_percentage": f"{progress_pct:.1f}%"
            },
            "agents": agent_status,
            "runtime": str(datetime.now() - self.swarm_start_time) if self.swarm_start_time else "00:00:00",
            "round_robin_cycle": self.round_robin_cycle,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }
    
    def pause_execution(self):
        """Pause autonomous execution"""
        if self.state == SwarmState.ACTIVE:
            self.state = SwarmState.PAUSED
            logger.info("⏸️ Swarm execution paused")
    
    def resume_execution(self):
        """Resume autonomous execution"""
        if self.state == SwarmState.PAUSED:
            self.state = SwarmState.ACTIVE
            logger.info("▶️ Swarm execution resumed")
            self._autonomous_execution_loop()
    
    def stop_execution(self):
        """Stop autonomous execution"""
        self.state = SwarmState.IDLE
        logger.info("⏹️ Swarm execution stopped")


# Global autonomous swarm instance
AUTONOMOUS_SWARM = AutonomousSwarm()
