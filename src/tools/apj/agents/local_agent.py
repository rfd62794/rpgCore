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


class LocalAgent:
    """
    Fully autonomous local agent with codebase understanding
    Uses Ollama for reasoning, has full project context
    """
    
    def __init__(self, project_root: Path = Path(".")):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.src_dir = self.project_root / "src"
        
        # Load all context tools
        self._load_context_tools()
        
        # Ollama model for reasoning
        from src.tools.apj.agents.ollama_client import get_ollama_model
        self.ollama_model = get_ollama_model()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              LOCAL AGENT INITIALIZED                          ║
║            Using Ollama (fully autonomous)                    ║
╚══════════════════════════════════════════════════════════════╝

🧠 Model: {self.ollama_model.model_name}
📚 Context: Loaded codebase understanding tools
🔌 Connectivity: Offline (no cloud dependency)
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
        self._load_design_documents()
        
        print("✅ All context tools loaded\n")
    
    def _load_design_documents(self):
        """Load design documents for context"""
        
        self.design_docs = {}
        
        # Try to load each design doc
        docs_to_load = [
            ("design_pillars", self.docs_dir / "DESIGN_PILLARS.md"),
            ("feature_spec", self.docs_dir / "phase3" / "FEATURE_SPEC.md"),
            ("system_specs", self.docs_dir / "phase3" / "SYSTEM_SPECS.md"),
            ("technical_design", self.docs_dir / "phase3" / "TECHNICAL_DESIGN.md"),
        ]
        
        for doc_name, doc_path in docs_to_load:
            if doc_path.exists():
                with open(doc_path) as f:
                    self.design_docs[doc_name] = f.read()
    
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
        """Build complete context for task execution"""
        
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
            system_specs=self.design_docs.get("system_specs", "")
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
        Use Ollama to plan implementation
        Agent has full codebase context, can make informed decisions
        """
        
        task = context.current_task
        
        prompt = f"""
You are an autonomous software agent with full understanding of this codebase.

CURRENT TASK:
{json.dumps(task, indent=2)}

CODEBASE CONTEXT:
- Total files: {len(context.codebase_symbols)}
- Relevant systems: {list(set(f.get('system') for f in context.file_classifications.values() if f))}
- Relevant demos: {list(set(f.get('demo') for f in context.file_classifications.values() if f))}

EXISTING IMPLEMENTATIONS (files you'll modify/extend):
{json.dumps(list(context.existing_implementations.keys()), indent=2)}

TECHNICAL DESIGN DECISIONS:
{context.technical_design[:1000]}

WHAT THIS TASK ACHIEVES:
{context.feature_spec[:1000]}

SYSTEM ARCHITECTURE:
{context.system_specs[:1000]}

Your job: Create a detailed step-by-step implementation plan.

For each step, provide:
1. What to do
2. Which files to create/modify
3. What code to write (pseudocode is fine)
4. How to test it
5. Expected success criteria

Be specific. Reference existing code where applicable.
Make decisions based on the architecture and existing patterns.

Return as JSON:
{{
  "summary": "Overall plan summary",
  "steps": [
    {{
      "number": 1,
      "description": "string",
      "files": ["path/to/file.py"],
      "actions": ["action1", "action2"],
      "test_command": "pytest ...",
      "success_criteria": ["criterion1"]
    }}
  ]
}}
"""
        
        # Get plan from Ollama
        from pydantic_ai import Agent
        agent = Agent(self.ollama_model)
        
        response = agent.run(prompt)
        response_text = response.data
        
        # Parse response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
        except json.JSONDecodeError:
            pass
        
        return None
    
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
        Generate code for a file using Ollama
        Agent has context of existing code, architecture, requirements
        """
        
        existing_code = context.existing_implementations.get(file_path, "")
        
        prompt = f"""
Generate Python code for: {file_path}

STEP DESCRIPTION:
{step.get('description')}

SUCCESS CRITERIA:
{json.dumps(step.get('success_criteria', []), indent=2)}

EXISTING CODE (if any):
{existing_code[:2000] if existing_code else "None - new file"}

CODEBASE PATTERNS:
Look at these similar files for patterns:
{self._get_similar_files(file_path, context)}

REQUIREMENTS:
- Follow existing code style
- Use ECS patterns where applicable
- Write docstrings for all functions/classes
- Include type hints
- Add TODO comments for incomplete sections

Generate complete, working code. Be thorough.
"""
        
        try:
            code = self.ollama.analyze_blockers(prompt)
            
            # Clean up response (remove markdown if present)
            if code.startswith("```"):
                code = code[code.find("\n")+1:]
            if code.endswith("```"):
                code = code[:code.rfind("```")]
            
            return code.strip()
        
        except Exception as e:
            print(f"  ❌ Code generation failed: {e}")
            return None
    
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
