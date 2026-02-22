import os
import re
from datetime import datetime

class Journal:
    JOURNAL_PATH = "docs/PROJECT_JOURNAL.md"
    TASKS_PATH = "docs/TASKS.md"

    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.full_path = os.path.join(self.root_dir, self.JOURNAL_PATH)
        self.tasks_path = os.path.join(self.root_dir, self.TASKS_PATH)

    def load(self, path: str = None) -> str:
        """Reads and returns full content of a file."""
        target = path or self.full_path
        if not os.path.exists(target):
            return ""
        with open(target, "r", encoding="utf-8") as f:
            return f.read()

    def get_section(self, name: str, path: str = None) -> str:
        """Extracts a named ## Section and its content."""
        content = self.load(path)
        # Regex to find ## Name until the next ## or end of file
        pattern = rf"## {name}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def update_section(self, name: str, new_content: str, path: str = None):
        """Replaces a section's content in the file."""
        target = path or self.full_path
        content = self.load(target)
        pattern = rf"## {name}\n(.*?)(?=\n## |\Z)"
        
        # Check if section exists
        if re.search(pattern, content, re.DOTALL):
            new_section = rf"## {name}\n{new_content.strip()}\n"
            updated_content = re.sub(pattern, new_section, content, flags=re.DOTALL)
        else:
            # Append if it doesn't exist
            updated_content = content.rstrip() + f"\n\n## {name}\n{new_content.strip()}\n"
            
        with open(target, "w", encoding="utf-8") as f:
            f.write(updated_content)

    def get_next_tasks(self, n: int = 3) -> str:
        """Reads top n items from Queued tier in TASKS.md."""
        queued = self.get_section("Queued", self.tasks_path)
        if not queued:
            return "No queued tasks."
        lines = [line.strip("- ").strip() for line in queued.split("\n") if line.strip().startswith("-")]
        top_n = lines[:n]
        return "\n".join([f"  {i+1}. {task}" for i, task in enumerate(top_n)])

    def add_task(self, text: str):
        """Appends a task to the Queued section in TASKS.md."""
        queued = self.get_section("Queued", self.tasks_path)
        new_queued = queued + f"\n- {text}"
        self.update_section("Queued", new_queued, self.tasks_path)

    def complete_task(self, pattern: str):
        """Moves matching task to Completed section in TASKS.md."""
        content = self.load(self.tasks_path)
        
        # Find the line
        lines = content.split("\n")
        task_line = None
        new_lines = []
        for line in lines:
            if pattern.lower() in line.lower() and line.strip().startswith("-"):
                task_line = line
            else:
                new_lines.append(line)
        
        if task_line:
            updated_content = "\n".join(new_lines)
            with open(self.tasks_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            
            # Append to completed
            completed = self.get_section("Completed", self.tasks_path)
            date_str = datetime.now().strftime("%Y-%m-%d")
            completed_entry = f"- [x] {task_line.strip('- ').strip()} ({date_str})"
            new_completed = completed + f"\n{completed_entry}"
            self.update_section("Completed", new_completed, self.tasks_path)

    def get_handoff(self, test_floor: int = 338) -> str:
        """Builds a formatted handoff string."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        curr_state = self.get_section("Current State")
        in_flight = self.get_section("In Flight")
        next_priority = self.get_section("Next Priority")
        queued_tasks = self.get_next_tasks(3)

        handoff = f"""═══════════════════════════════════════
rpgCore Agent Handoff — {date_str}
═══════════════════════════════════════
ENVIRONMENT: Windows (PowerShell/CMD)
  All commands use: python, uv run pytest, copy, move
  Do NOT use: cp, mv, rm, touch, grep, ls
  Path separator: backslash
  Line endings: CRLF

READ FIRST:
  docs/RPGCORE_CONSTITUTION.md
  docs/SESSION_PROTOCOL.md

CURRENT STATE:
  {curr_state}

IN FLIGHT:
  {in_flight}

QUEUED TASKS (top 3):
{queued_tasks}

NEXT PRIORITY:
  {next_priority}

PROTECTED FLOOR: {test_floor} passing tests
  Verify with: uv run pytest
═══════════════════════════════════════"""
        return handoff

    def get_boot_block(self, test_floor: int = 338) -> str:
        """Prints a complete agent onboarding block."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        cwd = os.getcwd()
        queued_tasks = self.get_next_tasks(3)
        
        boot = f"""═══════════════════════════════════════
rpgCore — Agent Boot Sequence
═══════════════════════════════════════
ENVIRONMENT: Windows PowerShell
REPO: {cwd}

STEP 0 — Verify orientation:
  python -m src.tools.apj handoff

STEP 1 — Read these documents in order:
  docs/RPGCORE_CONSTITUTION.md
  docs/SESSION_PROTOCOL.md
  docs/PROJECT_JOURNAL.md
  docs/TASKS.md

STEP 2 — Verify test floor:
  uv run pytest

STEP 3 — Confirm understanding before acting:
  State current floor, what is in flight, next priority.
  Wait for Overseer confirmation before writing any code.

QUEUED TASKS (top 3):
{queued_tasks}

AGENT STANDARDS:
  Use: uv run pytest, uv run python
  No print() in src/ — use logging
  Spec before code — confirm plan with Overseer first
  Present options as: Headlong / Divert / Alt
  Final step: python -m src.tools.apj update --current "..." --inflight "..." --next "..."

PROTECTED FLOOR: {test_floor} passing tests
SESSION DATE: {date_str}
═══════════════════════════════════════"""
        return boot
