"""
Task loader - loads and structures goals, milestones, tasks from documentation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import re


@dataclass
class Goal:
    """High-level project goal"""
    id: str                    # "G1", "G2", "G3"
    title: str
    description: str
    linked_milestones: List[str] = None  # ["M1", "M2"]


@dataclass
class Milestone:
    """Phase milestone"""
    id: str                    # "M1", "M2", "M_PHASE3"
    title: str
    description: str
    phase: Optional[str] = None           # "phase_1", "phase_2", "phase_3"
    status: str = "planning"   # "planning", "in_progress", "complete"
    linked_goals: List[str] = None        # ["G1", "G3"]
    linked_tasks: List[str] = None        # ["T001", "T002"]


@dataclass
class Task:
    """Implementation task"""
    id: str                    # "T001", "T002", "phase_3_0"
    title: str
    description: str
    status: str = "queued"     # "queued", "in_progress", "complete"
    priority: str = "P1"       # "P0", "P1", "P2", "P3"
    estimated_hours: float = 0
    linked_milestone: Optional[str] = None  # "M_PHASE3"
    linked_steps: List[str] = None          # ["S001", "S002"]
    file_references: List[str] = None       # ["src/shared/ecs/components/tower.py"]
    symbols_to_create: List[str] = None  # Classes/functions to implement


@dataclass
class Step:
    """Specific implementation step"""
    id: str                    # "S001", "S002"
    task_id: str
    title: str
    description: str
    file_references: List[str] = None  # Files to create/modify
    symbols_to_create: List[str] = None  # Classes/functions to implement


class TaskLoader:
    """Load goals, milestones, tasks from documentation"""
    
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.goals: Dict[str, Goal] = {}
        self.milestones: Dict[str, Milestone] = {}
        self.tasks: Dict[str, Task] = {}
        self.steps: Dict[str, Step] = {}
    
    def load_all(self) -> None:
        """Load all planning documents"""
        self.load_goals()
        self.load_milestones()
        self.load_tasks()
        self.load_steps()
        self._link_relationships()
    
    def load_goals(self) -> Dict[str, Goal]:
        """Load GOALS.md"""
        goals_file = self.docs_dir / "GOALS.md"
        if not goals_file.exists():
            return {}
        
        goals = {}
        # Parse GOALS.md for G1, G2, G3, etc
        # For now, return defaults
        
        self.goals = {
            "G1": Goal(
                id="G1",
                title="Prove Unified Creature System",
                description="Single entity type scales across all game genres",
                linked_milestones=["M1"]
            ),
            "G2": Goal(
                id="G2",
                title="Demonstrate ECS Architecture",
                description="Component-based system works in production",
                linked_milestones=["M2"]
            ),
            "G3": Goal(
                id="G3",
                title="Establish Multi-Genre Support",
                description="Prove any creature type works in any genre",
                linked_milestones=["M_PHASE3"]
            ),
            "G4": Goal(
                id="G4",
                title="Create Monetizable Platform",
                description="Engine supports commercial applications",
                linked_milestones=["M_PHASE3"]
            ),
            "G5": Goal(
                id="G5",
                title="Build Production Infrastructure",
                description="Scalable, maintainable codebase",
                linked_milestones=["M_PHASE3"]
            )
        }
        
        return self.goals
    
    def load_milestones(self) -> Dict[str, Milestone]:
        """Load MILESTONES.md"""
        milestones_file = self.docs_dir / "MILESTONES.md"
        if not milestones_file.exists():
            return {}
        
        # Parse MILESTONES.md for M1, M2, M_PHASE3, etc
        # For now, return defaults
        
        self.milestones = {
            "M1": Milestone(
                id="M1",
                title="Entity Unification",
                phase="phase_1",
                status="complete",
                linked_goals=["G1"],
                linked_tasks=[]
            ),
            "M2": Milestone(
                id="M2",
                title="ECS Foundation",
                phase="phase_2",
                status="complete",
                linked_goals=["G2"],
                linked_tasks=[]
            ),
            "M_PHASE3": Milestone(
                id="M_PHASE3",
                title="Tower Defense Integration",
                phase="phase_3",
                status="planning",
                linked_goals=["G3", "G4", "G5"],
                linked_tasks=["T_3_0", "T_3_1", "T_3_2", "T_3_3", "T_3_4", "T_3_5", "T_3_6"]
            )
        }
        
        return self.milestones
    
    def load_tasks(self) -> Dict[str, Task]:
        """Load TASKS.md"""
        tasks_file = self.docs_dir / "TASKS.md"
        if not tasks_file.exists():
            return {}
        
        # Parse TASKS.md for T001, T002, etc
        # For now, return Phase 3 tasks
        
        self.tasks = {
            "T_3_0": Task(
                id="T_3_0",
                title="ECS Rendering Refactor",
                description="Add RenderComponent, AnimationComponent, RenderingSystem",
                priority="P0",
                estimated_hours=4,
                linked_milestone="M_PHASE3",
                linked_steps=["S_3_0_1", "S_3_0_2", "S_3_0_3"],
                file_references=[
                    "src/shared/ecs/components/render.py",
                    "src/shared/ecs/systems/rendering_system.py"
                ]
            ),
            "T_3_1": Task(
                id="T_3_1",
                title="Grid System & Components",
                description="GridPositionComponent, TowerComponent, WaveComponent",
                priority="P0",
                estimated_hours=6,
                linked_milestone="M_PHASE3",
                file_references=[
                    "src/shared/ecs/components/grid.py",
                    "src/shared/ecs/components/tower.py",
                    "src/shared/ecs/components/wave.py"
                ]
            ),
            "T_3_2": Task(
                id="T_3_2",
                title="Tower Defense Systems",
                description="TowerDefenseBehaviorSystem, WaveSystem, UpgradeSystem, TargetingSystem",
                priority="P0",
                estimated_hours=8,
                linked_milestone="M_PHASE3",
                file_references=[
                    "src/shared/ecs/systems/behavior_system.py",
                    "src/shared/ecs/systems/wave_system.py",
                    "src/shared/ecs/systems/upgrade_system.py",
                    "src/shared/ecs/systems/targeting_system.py"
                ]
            ),
            "T_3_3": Task(
                id="T_3_3",
                title="TD Session & Persistence",
                description="TowerDefenseSession, save/load JSON, resource feedback",
                priority="P0",
                estimated_hours=6,
                linked_milestone="M_PHASE3",
                file_references=[
                    "src/apps/tower_defense/session.py",
                    "src/shared/persistence/session.py"
                ]
            ),
            "T_3_4": Task(
                id="T_3_4",
                title="TD Scene & Integration",
                description="TowerDefenseScene, UI, rendering, end-of-game results",
                priority="P0",
                estimated_hours=8,
                linked_milestone="M_PHASE3",
                file_references=[
                    "src/apps/tower_defense/ui/scene_td.py",
                    "src/shared/ui/components/tower_ui.py"
                ]
            ),
            "T_3_5": Task(
                id="T_3_5",
                title="Fantasy RPG Tenant",
                description="Multi-tenant proof-of-concept with free sprites",
                priority="P1",
                estimated_hours=6,
                linked_milestone="M_PHASE3",
                file_references=[
                    "src/apps/fantasy_rpg/run_fantasy_rpg.py",
                    "src/apps/fantasy_rpg/ui/scene_fr.py"
                ]
            ),
            "T_3_6": Task(
                id="T_3_6",
                title="Archive & Documentation",
                description="Move exploratory demos, document multi-tenant architecture",
                priority="P1",
                estimated_hours=4,
                linked_milestone="M_PHASE3",
                file_references=[
                    "docs/MULTI_TENANT_GUIDE.md",
                    "docs/PHASE_3_SUMMARY.md"
                ]
            )
        }
        
        return self.tasks
    
    def load_steps(self) -> Dict[str, Step]:
        """Load step-level details (can be in TASKS.md or separate)"""
        # For now, create steps from tasks
        self.steps = {
            "S_3_0_1": Step(
                id="S_3_0_1",
                task_id="T_3_0",
                title="Create RenderComponent",
                description="Add RenderComponent dataclass to ECS",
                file_references=["src/shared/ecs/components/render.py"],
                symbols_to_create=["RenderComponent"]
            ),
            "S_3_0_2": Step(
                id="S_3_0_2",
                task_id="T_3_0",
                title="Create AnimationComponent",
                description="Add AnimationComponent dataclass to ECS",
                file_references=["src/shared/ecs/components/render.py"],
                symbols_to_create=["AnimationComponent"]
            ),
            "S_3_0_3": Step(
                id="S_3_0_3",
                task_id="T_3_0",
                title="Create RenderingSystem",
                description="Add RenderingSystem for ECS pipeline",
                file_references=["src/shared/ecs/systems/rendering_system.py"],
                symbols_to_create=["RenderingSystem"]
            ),
            "S_3_1_1": Step(
                id="S_3_1_1",
                task_id="T_3_1",
                title="Create GridPositionComponent",
                description="Add GridPositionComponent for tower placement",
                file_references=["src/shared/ecs/components/grid.py"],
                symbols_to_create=["GridPositionComponent"]
            ),
            "S_3_1_2": Step(
                id="S_3_1_2",
                task_id="T_3_1",
                title="Create TowerComponent",
                description="Add TowerComponent for tower data",
                file_references=["src/shared/ecs/components/tower.py"],
                symbols_to_create=["TowerComponent"]
            ),
            "S_3_1_3": Step(
                id="S_3_1_3",
                task_id="T_3_1",
                title="Create WaveComponent",
                description="Add WaveComponent for wave data",
                file_references=["src/shared/ecs/components/wave.py"],
                symbols_to_create=["WaveComponent"]
            )
        }
        
        return self.steps
    
    def _link_relationships(self) -> None:
        """Link goals to milestones to tasks to steps"""
        # This happens naturally from the data structure
        # But we can add validation and cross-linking
        pass
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get goal and all linked milestones"""
        return self.goals.get(goal_id)
    
    def get_milestone_tasks(self, milestone_id: str) -> List[Task]:
        """Get all tasks for a milestone"""
        milestone = self.milestones.get(milestone_id)
        if not milestone:
            return []
        
        return [self.tasks[t_id] for t_id in (milestone.linked_tasks or [])
                if t_id in self.tasks]
    
    def get_task_steps(self, task_id: str) -> List[Step]:
        """Get all steps for a task"""
        task = self.tasks.get(task_id)
        if not task:
            return []
        
        return [self.steps[s_id] for s_id in (task.linked_steps or [])
                if s_id in self.steps]
    
    def get_task_files(self, task_id: str) -> List[str]:
        """Get all files referenced by a task"""
        task = self.tasks.get(task_id)
        if not task:
            return []
        
        # Collect from task and all steps
        files = set(task.file_references or [])
        
        for step in self.get_task_steps(task_id):
            files.update(step.file_references or [])
        
        return sorted(list(files))
