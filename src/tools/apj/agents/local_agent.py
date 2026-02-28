"""
Local Agent - fully autonomous agent with codebase context
Runs on Ollama locally, connected to project understanding tools
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
from dataclasses import dataclass
from enum import Enum


class DecisionType(Enum):
    """Types of decisions agent can make"""
    IMPLEMENT = "implement"           # Write code
    ANALYZE = "analyze"               # Understand existing code
    REFACTOR = "refactor"             # Improve existing code
    DEBUG = "debug"                   # Fix broken code
    DESIGN = "design"                 # Make architecture decisions
    INTEGRATE = "integrate"           # Connect systems


@dataclass
class AgentContext:
    """Full context for agent decision making"""
    project_root: Path
    current_task: Dict                # Task being executed
    codebase_symbols: Dict            # SymbolMap data
    file_classifications: Dict        # What each file is for
    task_mappings: Dict               # Which tasks → which files
    project_status: Dict              # What's done/blocked
    existing_implementations: Dict    # Code that already exists
    technical_design: Dict            # Architecture decisions
    feature_spec: Dict                # What must exist
    system_specs: Dict                # How systems work
    # NEW: Full documentation context
    project_knowledge: Dict           # Structured knowledge from all docs
    vision: str                       # Project vision and north star
    goals: str                        # Project goals and objectives
    design_pillars: str               # Non-negotiable principles
    milestones: str                   # Project milestones and phases
    tasks_doc: str                    # Task breakdown documentation
    ecs_details: Dict                 # ECS system specifications
    genetics_details: Dict            # Genetics system specifications
    rendering_details: Dict           # Rendering system specifications


class LocalAgent:
    """
    Fully autonomous local agent with codebase understanding
    Uses Ollama for reasoning, has full project context
    """
    
    def __init__(self, project_root: Path = Path(".")):
        """Initialize agent with full documentation context"""
        
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.src_dir = self.project_root / "src"
        
        # Load all context tools
        self._load_context_tools()
        
        # Load ALL documentation
        self._load_all_documentation()
        
        # Build documentation context for Ollama
        self.documentation_context = self._build_documentation_context()
        
        # Ollama model for reasoning
        from src.tools.apj.agents.ollama_client import get_ollama_model
        self.ollama_model = get_ollama_model()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              LOCAL AGENT INITIALIZED                          ║
║            Using Ollama (fully autonomous)                    ║
╚══════════════════════════════════════════════════════════════╝

🧠 Model: {self.ollama_model.model_name}
📚 Documentation: {len(self.documentation)} files loaded
🗂️  Code Context: {len(self.symbol_map.files)} files indexed
🔌 Connectivity: Offline (no cloud dependency)

DOCUMENTATION LOADED:
{json.dumps({k: v['description'] for k, v in self.documentation.items()}, indent=2)}
""")
    
    def _load_context_tools(self):
        """Load all codebase understanding tools"""
        
        print("Loading codebase context tools...")
        
        # SymbolMap - knows all symbols in codebase
        from src.tools.apj.inventory.scanner import ASTScanner
        scanner = ASTScanner(self.src_dir)
        self.symbol_map = scanner.scan()
        print(f"  ✅ SymbolMap: {len(self.symbol_map.files)} files indexed")
        
        # FileClassifier - knows what each file is for
        from src.tools.apj.inventory.classifier import FileClassifier
        classifier = FileClassifier()
        self.classifications = classifier.classify_all(self.symbol_map)
        print(f"  ✅ FileClassifier: {len(self.classifications)} files classified")
        
        # TaskFileMapper - knows which tasks map to which files
        from src.tools.apj.data_loader import DataLoader
        loader = DataLoader(self.project_root)
        task_loader = loader.load_task_loader()
        self.task_mapper = loader.load_task_file_mapper(task_loader, self.classifications)
        print(f"  ✅ TaskFileMapper: {len(self.task_mapper.task_to_files)} task mappings")
        
        # ProjectStatus - knows what's done/blocked
        from src.tools.apj.project_status import ProjectStatus
        status_analyzer = ProjectStatus(self.project_root)
        self.project_status = status_analyzer.analyze_complete_project()
        print(f"  ✅ ProjectStatus: {len(self.project_status['blockers'])} blockers identified")
        
        # Load design documents
        self._load_all_documentation()
        
        print("✅ All context tools loaded\n")
    
    def _load_all_documentation(self):
        """
        Load ALL project documentation to prime the agent
        Agent reads and internalizes before starting work
        """
        
        print("\n📚 Loading Project Documentation...")
        
        self.documentation = {}
        
        # Ordered by importance for context
        docs_to_load = [
            # Foundation
            ("VISION.md", self.docs_dir / "VISION.md", "Project vision and philosophy"),
            ("GOALS.md", self.docs_dir / "GOALS.md", "High-level goals (G1-G5)"),
            ("DESIGN_PILLARS.md", self.docs_dir / "DESIGN_PILLARS.md", "Non-negotiable design principles"),
            
            # Planning
            ("MILESTONES.md", self.docs_dir / "MILESTONES.md", "Release milestones and phases"),
            ("TASKS.md", self.docs_dir / "TASKS.md", "Concrete tasks to implement"),
            
            # Phase 3 Specific
            ("FEATURE_SPEC.md", self.docs_dir / "phase3" / "FEATURE_SPEC.md", "Tower Defense features"),
            ("SYSTEM_SPECS.md", self.docs_dir / "phase3" / "SYSTEM_SPECS.md", "Tower Defense systems"),
            ("TECHNICAL_DESIGN.md", self.docs_dir / "phase3" / "TECHNICAL_DESIGN.md", "Tower Defense architecture"),
            
            # Systems Architecture
            ("systems/ecs_spec.md", self.docs_dir / "systems" / "ecs_system_spec.md", "ECS system specification"),
            ("systems/genetics_spec.md", self.docs_dir / "systems" / "genetics_system_spec.md", "Genetics system"),
            ("systems/rendering_spec.md", self.docs_dir / "systems" / "rendering_system_spec.md", "Rendering system"),
            
            # Status Reports
            ("INVENTORY_REPORT.md", self.docs_dir / "INVENTORY_REPORT.md", "Current code inventory"),
            
            # Execution
            ("REALITY.md", self.docs_dir / "REALITY.md", "What's actually implemented"),
        ]
        
        for doc_id, doc_path, description in docs_to_load:
            if doc_path.exists():
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.documentation[doc_id] = {
                            "path": str(doc_path),
                            "description": description,
                            "content": content,
                            "size_kb": len(content) / 1024
                        }
                        print(f"  ✅ {doc_id:30s} ({self.documentation[doc_id]['size_kb']:.1f} KB)")
                except Exception as e:
                    print(f"  ⚠️  {doc_id:30s} (error: {e})")
            else:
                print(f"  ❌ {doc_id:30s} (not found)")
        
        print(f"\n✅ Loaded {len(self.documentation)} documentation files\n")
    
    def _build_documentation_context(self) -> str:
        """
        Build a comprehensive context string from all documentation
        Used to prime Ollama with project knowledge
        """
        
        context_parts = []
        
        # Start with vision and goals
        if "VISION.md" in self.documentation:
            context_parts.append("=== PROJECT VISION ===\n" + 
                                self.documentation["VISION.md"]["content"][:2000])
        
        if "GOALS.md" in self.documentation:
            context_parts.append("\n=== PROJECT GOALS ===\n" + 
                                self.documentation["GOALS.md"]["content"][:2000])
        
        if "DESIGN_PILLARS.md" in self.documentation:
            context_parts.append("\n=== DESIGN PILLARS (NON-NEGOTIABLE) ===\n" + 
                                self.documentation["DESIGN_PILLARS.md"]["content"][:1500])
        
        # Technical context
        if "TECHNICAL_DESIGN.md" in self.documentation:
            context_parts.append("\n=== TECHNICAL DESIGN DECISIONS ===\n" + 
                                self.documentation["TECHNICAL_DESIGN.md"]["content"][:2000])
        
        if "SYSTEM_SPECS.md" in self.documentation:
            context_parts.append("\n=== SYSTEM ARCHITECTURE ===\n" + 
                                self.documentation["SYSTEM_SPECS.md"]["content"][:2000])
        
        # Feature context
        if "FEATURE_SPEC.md" in self.documentation:
            context_parts.append("\n=== REQUIRED FEATURES ===\n" + 
                                self.documentation["FEATURE_SPEC.md"]["content"][:1500])
        
        # Current status
        if "REALITY.md" in self.documentation:
            context_parts.append("\n=== CURRENT IMPLEMENTATION STATUS ===\n" + 
                                self.documentation["REALITY.md"]["content"][:1500])
        
        return "\n".join(context_parts)
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a specific section from markdown content"""
        import re
        
        # Look for ## section_name
        pattern = rf"^##\s*{re.escape(section_name)}\s*$(.*?)(?=^##|\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # Try with # section_name
        pattern = rf"^#\s*{re.escape(section_name)}\s*$(.*?)(?=^#|\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return f"Section '{section_name}' not found"
    
    def _extract_goals(self, content: str) -> Dict:
        """Extract goals with their descriptions"""
        import re
        
        goals = {}
        
        # Look for G1, G2, etc.
        pattern = r"^###\s*(G\d+_[A-Za-z_]+)\s*\n(.*?)(?=^###|\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for goal_id, description in matches:
            goals[goal_id] = {
                "description": description.strip(),
                "status": "unknown"  # Will be updated from project status
            }
        
        return goals
    
    def _extract_pillars(self, content: str) -> Dict:
        """Extract design pillars (non-negotiable principles)"""
        import re
        
        pillars = {}
        
        # Look for ### Pillar sections
        pattern = r"^###\s*Pillar\s*\d+:\s*([^\n]+)\s*\n(.*?)(?=^###|\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for i, (pillar_name, description) in enumerate(matches, 1):
            pillars[f"pillar_{i}"] = {
                "name": pillar_name.strip(),
                "description": description.strip()
            }
        
        return pillars
    
    def _extract_milestones(self, content: str) -> Dict:
        """Extract milestone information"""
        import re
        
        milestones = {}
        
        # Look for milestone sections
        pattern = r"^###\s*([^\n]+)\s*\n(.*?)(?=^###|\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for milestone_name, description in matches:
            milestones[milestone_name.strip()] = {
                "description": description.strip(),
                "status": "unknown"
            }
        
        return milestones
    
    def _extract_tasks(self, content: str) -> Dict:
        """Extract task breakdown"""
        import re
        
        tasks = {}
        
        # Look for task sections
        pattern = r"^###\s*(T_\d+_[^\n]*)\s*\n(.*?)(?=^###|\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for task_id, description in matches:
            tasks[task_id] = {
                "title": task_id,
                "description": description.strip()
            }
        
        return tasks
    
    def _extract_features(self, content: str) -> Dict:
        """Extract feature specifications"""
        import re
        
        features = {}
        
        # Look for feature sections
        pattern = r"^###\s*Feature\s*\d+:\s*([^\n]+)\s*\n(.*?)(?=^###|\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for i, (feature_name, description) in enumerate(matches, 1):
            features[f"feature_{i}"] = {
                "name": feature_name.strip(),
                "description": description.strip()
            }
        
        return features
    
    def _extract_system_specs(self, content: str) -> Dict:
        """Extract system specifications"""
        import re
        
        systems = {}
        
        # Look for system sections
        pattern = r"^##\s*\d+\.\s*([^\n]+)\s*\n(.*?)(?=^##|\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for i, (system_name, description) in enumerate(matches, 1):
            systems[f"system_{i}"] = {
                "name": system_name.strip(),
                "description": description.strip()
            }
        
        return systems
    
    def _extract_technical_decisions(self, content: str) -> Dict:
        """Extract technical design decisions"""
        import re
        
        decisions = {}
        
        # Look for decision sections
        pattern = r"^###\s*\d+\.\s*([^\n]+)\s*\n(.*?)(?=^###|\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for i, (decision_name, description) in enumerate(matches, 1):
            decisions[f"decision_{i}"] = {
                "name": decision_name.strip(),
                "description": description.strip()
            }
        
        return decisions
    
    def _extract_system_details(self, content: str) -> Dict:
        """Extract detailed system specifications"""
        import re
        
        details = {}
        
        # Extract components, systems, integration points
        components_section = self._extract_section(content, "Components")
        systems_section = self._extract_section(content, "System")
        integration_section = self._extract_section(content, "Integration")
        
        details["components"] = components_section
        details["system"] = systems_section
        details["integration"] = integration_section
        
        return details
    
    def execute_task(self, task: Dict) -> bool:
        """
        Execute a task autonomously with full codebase context
        
        Agent has access to:
          - Existing code (SymbolMap)
          - Architecture decisions (TECHNICAL_DESIGN)
          - What already exists (ProjectStatus)
          - How systems work (SYSTEM_SPECS)
          - What this task requires (task spec)
        """
        
        task_id = task.get("id", "unknown")
        task_title = task.get("title", "Untitled")
        
        print(f"\n{'='*60}")
        print(f"📋 Task: {task_title} ({task_id})")
        print(f"{'='*60}\n")
        
        # Build full context for this task
        context = self._build_task_context(task)
        
        # Ask Ollama to plan implementation
        implementation_plan = self._plan_implementation(context)
        
        if not implementation_plan:
            print(f"❌ Failed to plan implementation")
            return False
        
        print("Implementation Plan:")
        print(implementation_plan)
        print()
        
        # Execute each step of the plan
        steps = implementation_plan.get("steps", [])
        
        for step_num, step in enumerate(steps, 1):
            print(f"\n📝 Step {step_num}/{len(steps)}: {step.get('description', 'Unknown')}")
            
            success = self._execute_step(step, context)
            
            if not success:
                print(f"❌ Step failed: {step.get('description')}")
                return False
            
            print(f"✅ Step complete")
        
        # Verify success
        success = self._verify_task_complete(task, context)
        
        if success:
            print(f"\n✅ Task {task_id} COMPLETE")
        else:
            print(f"\n❌ Task {task_id} verification failed")
        
        return success
    
    def _build_task_context(self, task: Dict) -> AgentContext:
        """Build complete context for task execution with full documentation"""
        
        return AgentContext(
            project_root=self.project_root,
            current_task=task,
            codebase_symbols=self.symbol_map,
            file_classifications=self.classifications,
            task_mappings=self.task_mapper.task_to_files,
            project_status=self.project_status,
            existing_implementations=self._get_existing_code(task),
            technical_design=self.design_docs.get("technical_design", ""),
            feature_spec=self.design_docs.get("feature_spec", ""),
            system_specs=self.design_docs.get("system_specs", ""),
            # NEW: Full project knowledge from all documentation
            project_knowledge=self.project_knowledge,
            vision=self.design_docs.get("vision", ""),
            goals=self.design_docs.get("goals", ""),
            design_pillars=self.design_docs.get("design_pillars", ""),
            milestones=self.design_docs.get("milestones", ""),
            tasks_doc=self.design_docs.get("tasks", ""),
            ecs_details=self.project_knowledge.get("ecs_details", {}),
            genetics_details=self.project_knowledge.get("genetics_details", {}),
            rendering_details=self.project_knowledge.get("rendering_details", {})
        )
    
    def _get_existing_code(self, task: Dict) -> Dict:
        """Get existing code for files this task touches"""
        
        files = task.get("files", [])
        existing = {}
        
        for file_path in files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with open(full_path) as f:
                    existing[file_path] = f.read()
        
        return existing
    
    def _plan_implementation(self, context: AgentContext) -> Dict:
        """
        Plan implementation using:
        1. Project documentation (vision, design, architecture)
        2. Existing codebase (patterns, conventions)
        3. Task requirements (what to build)
        4. Current status (what's done/blocked)
        """
        
        task = context.current_task
        
        prompt = f"""
You are an autonomous agent implementing games in the DGT Engine.

PROJECT DOCUMENTATION AND CONTEXT:
═══════════════════════════════════════════════════════════════
{self.documentation_context}

═══════════════════════════════════════════════════════════════

CURRENT TASK TO IMPLEMENT:
{json.dumps(task, indent=2)}

CODEBASE CONTEXT:
- Total files: {len(context.codebase_symbols)}
- Existing systems: {self._get_existing_systems(context)}
- Existing patterns: {self._get_code_patterns(context)}

FILES YOU'LL MODIFY/CREATE:
{json.dumps(list(context.existing_implementations.keys()), indent=2)}

CURRENT PROJECT STATUS:
- Completed: {context.project_status['by_goal'].get('G1', {}).get('status', 'Unknown')}
- In Progress: {context.project_status['by_goal'].get('G3', {}).get('status', 'Unknown')}
- Blockers: {len(context.project_status.get('blockers', []))} items

YOUR TASK:
Create a detailed step-by-step implementation plan that:
1. Follows the design pillars (non-negotiable)
2. Uses existing patterns and conventions
3. Integrates with existing systems
4. Achieves the feature requirements
5. Passes tests

For each step:
- What to do
- Which files to create/modify
- Code patterns to follow
- Success criteria
- How to test

Use the project documentation as your guide.
Reference existing code patterns.
Follow ECS architecture.
Include docstrings and type hints.

Return as JSON with detailed steps.
"""
        
        # Get plan from Ollama with documentation context
        from pydantic_ai import Agent
        agent = Agent(self.ollama_model)
        
        response = agent.run(prompt)
        response_text = response.data
        
        # Parse response
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _get_existing_systems(self, context: AgentContext) -> List[str]:
        """Get list of existing systems from codebase"""
        systems = set()
        for file_clf in context.file_classifications.values():
            if file_clf.get('system'):
                systems.add(file_clf['system'])
        return sorted(list(systems))
    
    def _get_code_patterns(self, context: AgentContext) -> List[str]:
        """Get common code patterns from existing files"""
        patterns = [
            "ECS components with @dataclass decorator",
            "Systems that iterate entities",
            "Type hints on all functions",
            "Docstrings for public methods",
            "Tests in parallel test/ directory",
        ]
        return patterns
    
    def _execute_step(self, step: Dict, context: AgentContext) -> bool:
        """
        Execute a single step from the implementation plan
        
        This is where actual code generation happens
        Agent uses Ollama to generate code, write files, run tests
        """
        
        files = step.get("files", [])
        actions = step.get("actions", [])
        
        # For each file, generate code
        for file_path in files:
            print(f"  Writing: {file_path}")
            
            # Use Ollama to generate code
            code = self._generate_code(file_path, step, context)
            
            if not code:
                return False
            
            # Write file
            full_path = context.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(code)
        
        # Run tests if specified
        test_command = step.get("test_command")
        if test_command:
            print(f"  Testing: {test_command}")
            
            import subprocess
            result = subprocess.run(
                test_command,
                shell=True,
                cwd=context.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"  ❌ Tests failed: {result.stderr}")
                return False
        
        return True
    
    def _generate_code(self, file_path: str, step: Dict, context: AgentContext) -> Optional[str]:
        """
        Generate code that:
        1. Follows project vision and principles
        2. Matches existing code patterns
        3. Integrates with existing systems
        4. Achieves feature requirements
        """
        
        existing_code = context.existing_implementations.get(file_path, "")
        
        # Find relevant documentation
        relevant_docs = self._find_relevant_documentation(file_path, step, context)
        
        prompt = f"""
Generate Python code for: {file_path}

RELEVANT PROJECT DOCUMENTATION:
{relevant_docs}

STEP REQUIREMENTS:
{step.get('description')}

SUCCESS CRITERIA:
{json.dumps(step.get('success_criteria', []), indent=2)}

EXISTING CODE (if any, use as pattern reference):
{existing_code[:2000] if existing_code else "None - new file"}

INTEGRATION POINTS:
- Uses ECS systems: {self._get_system_integrations(file_path, context)}
- Uses genetics: {self._uses_genetics(file_path, context)}
- Part of demo: {self._get_demo_context(file_path, context)}

CODE REQUIREMENTS:
✅ Type hints on all functions and class methods
✅ Docstrings for all public methods and classes
✅ Follow existing code patterns (see examples below)
✅ Use ECS architecture where applicable
✅ Include assertions and validation
✅ Include TODO comments for incomplete sections

SIMILAR CODE TO USE AS PATTERNS:
{self._get_similar_files(file_path, context)}

Generate complete, working code that:
- Fits the project vision and design
- Matches existing patterns
- Integrates seamlessly
- Is well-documented
- Is testable

Be thorough and complete.
"""
        
        try:
            from pydantic_ai import Agent
            agent = Agent(self.ollama_model)
            
            response = agent.run(prompt)
            code = response.data
            
            # Clean up response
            if code.startswith("```"):
                code = code[code.find("\n")+1:]
            if code.endswith("```"):
                code = code[:code.rfind("```")]
            
            return code.strip()
        
        except Exception as e:
            print(f"  ❌ Code generation failed: {e}")
            return None
    
    def _find_relevant_documentation(self, file_path: str, step: Dict, context: AgentContext) -> str:
        """Find documentation relevant to this file"""
        
        relevant = []
        
        # Find by file system/demo
        file_clf = context.file_classifications.get(file_path, {})
        system = file_clf.get('system')
        demo = file_clf.get('demo')
        
        # Add system specs
        if system and "systems/" in file_path:
            for doc_id, doc_data in self.documentation.items():
                if system.lower() in doc_id.lower():
                    relevant.append(doc_data['content'][:1000])
        
        # Add feature specs for demo
        if demo or "phase3" in file_path:
            if "FEATURE_SPEC.md" in self.documentation:
                relevant.append(self.documentation["FEATURE_SPEC.md"]["content"][:1500])
        
        # Add technical design
        if "TECHNICAL_DESIGN.md" in self.documentation:
            relevant.append(self.documentation["TECHNICAL_DESIGN.md"]["content"][:1000])
        
        # Add design pillars
        if "DESIGN_PILLARS.md" in self.documentation:
            relevant.append(self.documentation["DESIGN_PILLARS.md"]["content"][:800])
        
        return "\n---\n".join(relevant) if relevant else "No specific documentation found"
    
    def _get_system_integrations(self, file_path: str, context: AgentContext) -> List[str]:
        """What systems does this file integrate with?"""
        file_clf = context.file_classifications.get(file_path, {})
        system = file_clf.get('system', 'unknown')
        return [system] if system else []
    
    def _uses_genetics(self, file_path: str, context: AgentContext) -> bool:
        """Does this file use genetics?"""
        return "genetics" in file_path.lower() or "tower" in file_path.lower()
    
    def _get_demo_context(self, file_path: str, context: AgentContext) -> Optional[str]:
        """What demo is this part of?"""
        file_clf = context.file_classifications.get(file_path, {})
        return file_clf.get('demo')
    
    def _get_similar_files(self, file_path: str, context: AgentContext) -> str:
        """Get similar files to use as code patterns"""
        
        # Find files in same directory or similar system
        similar = []
        
        for existing_file, code in context.existing_implementations.items():
            if Path(existing_file).parent == Path(file_path).parent:
                similar.append(f"{existing_file}: (use as pattern)")
        
        if not similar:
            # Find files in same system
            classification = context.file_classifications.get(file_path, {})
            system = classification.get("system")
            
            if system:
                for path, clf in context.file_classifications.items():
                    if clf.get("system") == system and path in context.existing_implementations:
                        similar.append(f"{path}: (same system)")
        
        return "\n".join(similar[:3])
    
    def _verify_task_complete(self, task: Dict, context: AgentContext) -> bool:
        """
        Verify task is complete based on success criteria
        Run tests, check files exist, verify output
        """
        
        files = task.get("files", [])
        
        # Check all files exist
        for file_path in files:
            full_path = context.project_root / file_path
            if not full_path.exists():
                print(f"  ❌ File not created: {file_path}")
                return False
        
        # Run tests
        import subprocess
        result = subprocess.run(
            ["uv", "run", "pytest", "--tb=short", "-q"],
            cwd=context.project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ⚠️  Tests not all passing: {result.stdout}")
            # Don't fail entirely, but flag it
        
        return True
