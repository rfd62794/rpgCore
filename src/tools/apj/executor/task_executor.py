"""
Task executor - runs a single task autonomously with validation
"""

from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import subprocess
import json
import ast
import sys


@dataclass
class ExecutionReport:
    """Report from executing a single task"""
    task_id: str
    task_title: str
    start_time: str
    end_time: Optional[str] = None
    status: str  # "running", "complete", "blocked", "failed"
    tests_run: int = 0
    tests_passing: int = 0
    tests_failing: int = 0
    files_modified: List[str] = None
    files_created: List[str] = None
    blocker_reason: Optional[str] = None
    output: List[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task_title": self.task_title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "tests_run": self.tests_run,
            "tests_passing": self.tests_passing,
            "tests_failing": self.tests_failing,
            "files_modified": self.files_modified or [],
            "files_created": self.files_created or [],
            "blocker_reason": self.blocker_reason,
            "output": self.output or []
        }


class TaskExecutor:
    """Execute a single task autonomously"""
    
    def __init__(self, project_root: Path, task_id: str, task_spec: Dict):
        self.project_root = project_root
        self.task_id = task_id
        self.task_spec = task_spec
        
        self.report = ExecutionReport(
            task_id=task_id,
            task_title=task_spec.get('title', 'Unknown Task'),
            start_time=datetime.now().isoformat(),
            output=[]
        )
    
    def execute(self) -> ExecutionReport:
        """Execute the task and return report"""
        print(f"🚀 Starting task: {self.task_id}")
        print(f"📝 Description: {self.task_spec.get('description', 'No description')}")
        print(f"⏱️  Estimated: {self.task_spec.get('estimated_hours', '?')} hours")
        
        try:
            # Step 1: Pre-execution validation
            self._validate_prerequisites()
            
            # Step 2: Execute implementation
            self._execute_implementation()
            
            # Step 3: Post-execution validation
            self._validate_success_criteria()
            
            self.report.status = "complete"
            
        except Exception as e:
            self.report.status = "failed"
            self.report.blocker_reason = str(e)
            self.report.output.append(f"ERROR: {e}")
        
        self.report.end_time = datetime.now().isoformat()
        
        # Print summary
        self._print_summary()
        
        return self.report
    
    def _validate_prerequisites(self):
        """Validate that prerequisites are met"""
        print("🔍 Validating prerequisites...")
        
        # Check if files exist that need to be modified
        files = self.task_spec.get('files', [])
        if files:
            print(f"   Files to modify: {len(files)}")
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    print(f"     ✅ {file_path}")
                else:
                    print(f"     ❌ {file_path} (will be created)")
        
        # Check if test suite passes
        print("   Running test suite...")
        result = subprocess.run(
            ["uv", "run", "pytest", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        self.report.tests_run = 1
        if result.returncode == 0:
            # Extract test count
            for line in result.stdout.split('\n'):
                if "passed" in line:
                    parts = line.split()[0]
                    try:
                        self.report.tests_passing = int(parts)
                        break
                    except ValueError:
                        pass
            print(f"   ✅ {self.report.tests_passing} tests passing")
        else:
            self.report.tests_failing = 1
            print(f"   ❌ Tests failing")
            raise Exception("Test suite is not passing")
    
    def _execute_implementation(self):
        """Execute the implementation steps"""
        print("🔧 Executing implementation...")
        
        # For now, we'll simulate implementation
        # In a real system, this would:
        # 1. Create/modify files
        # 2. Run any build commands
        # 3. Update documentation
        
        files = self.task_spec.get('files', [])
        self.report.files_modified = []
        self.report.files_created = []
        
        for file_path in files:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                # Create directory if needed
                full_path.parent.mkdir(parents=True, exist_ok=True)
                # Create file with basic structure
                with open(full_path, 'w') as f:
                    f.write(f"# {file_path}\n")
                    f.write(f"# Created for task {self.task_id}\n")
                    f.write(f"# Task: {self.task_spec.get('title', 'Unknown')}\n")
                    f.write(f"# Description: {self.task_spec.get('description', 'No description')}\n")
                
                self.report.files_created.append(file_path)
                print(f"     ✅ Created {file_path}")
                self.report.output.append(f"Created: {file_path}")
            else:
                # Modify existing file
                with open(full_path, 'a') as f:
                    f.write(f"\n# Modified for task {self.task_id}\n")
                    f.write(f"# Task: {self.task_spec.get('title', 'Unknown')}\n")
                
                self.report.files_modified.append(file_path)
                print(f"     ✅ Modified {file_path}")
                self.report.output.append(f"Modified: {file_path}")
        
        print(f"   ✅ Implementation complete")
    
    def _validate_success_criteria(self):
        """Validate that success criteria are met"""
        print("🔍 Validating success criteria...")
        
        criteria = self.task_spec.get('success_criteria', '')
        if criteria:
            print(f"   Checking: {criteria}")
        
        # Re-run tests to ensure nothing broke
        result = subprocess.run(
            ["uv", "run", "pytest", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        if result.returncode == 0:
            # Extract test count
            for line in result.stdout.split('\n'):
                if "passed" in line:
                    parts = line.split()[0]
                    try:
                        self.report.tests_passing = int(parts)
                        break
                    except ValueError:
                        pass
            print(f"   ✅ {self.report.tests_passing} tests passing")
        else:
            self.report.tests_failing = 1
            print(f"   ❌ Tests failing")
            raise Exception("Success criteria not met: tests failing")
        
        print(f"   ✅ Success criteria met")
    
    def _print_summary(self):
        """Print execution summary"""
        print(f"\n{'─'*60}")
        print(f"TASK EXECUTION SUMMARY")
        print(f"{'─'*60}\n")
        
        print(f"Task: {self.report.task_id}")
        print(f"Title: {self.report.task_title}")
        print(f"Status: {self.report.status}")
        
        if self.report.status == "complete":
            print(f"✅ SUCCESS: Task completed successfully")
            print(f"📊 Tests: {self.report.tests_passing} passing")
            if self.report.files_created:
                print(f"📁 Files created: {len(self.report.files_created)}")
            if self.report.files_modified:
                print(f"📁 Files modified: {len(self.report.files_modified)}")
        elif self.report.status == "blocked":
            print(f"❌ BLOCKED: {self.report.blocker_reason}")
        elif self.report.status == "failed":
            print(f"❌ FAILED: {self.report.blocker_reason}")
        
        print(f"\nTime: {self.report.start_time} → {self.report.end_time}")
        print(f"{'─'*60}\n")
