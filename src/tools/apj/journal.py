import os
import re
from datetime import datetime

class Journal:
    JOURNAL_PATH = "docs/PROJECT_JOURNAL.md"

    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.full_path = os.path.join(self.root_dir, self.JOURNAL_PATH)

    def load(self) -> str:
        """Reads and returns full journal content."""
        if not os.path.exists(self.full_path):
            return ""
        with open(self.full_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_section(self, name: str) -> str:
        """Extracts a named ## Section and its content."""
        content = self.load()
        # Regex to find ## Name until the next ## or end of file
        pattern = rf"## {name}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def update_section(self, name: str, new_content: str):
        """Replaces a section's content in the file."""
        content = self.load()
        pattern = rf"## {name}\n(.*?)(?=\n## |\Z)"
        
        # Check if section exists
        if re.search(pattern, content, re.DOTALL):
            new_section = rf"## {name}\n{new_content.strip()}\n"
            updated_content = re.sub(pattern, new_section, content, flags=re.DOTALL)
        else:
            # Append if it doesn't exist
            updated_content = content.rstrip() + f"\n\n## {name}\n{new_content.strip()}\n"
            
        with open(self.full_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

    def get_handoff(self, test_floor: int = 307) -> str:
        """Builds a formatted handoff string."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        curr_state = self.get_section("Current State")
        in_flight = self.get_section("In Flight")
        next_priority = self.get_section("Next Priority")

        handoff = f"""═══════════════════════════════════════
rpgCore Agent Handoff — {date_str}
═══════════════════════════════════════
READ FIRST:
  docs/RPGCORE_CONSTITUTION.md
  docs/SESSION_PROTOCOL.md

CURRENT STATE:
  {curr_state}

IN FLIGHT:
  {in_flight}

NEXT PRIORITY:
  {next_priority}

PROTECTED FLOOR: {test_floor} passing tests
  Verify with: uv run pytest
═══════════════════════════════════════"""
        return handoff
