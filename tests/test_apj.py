import os
import pytest
from src.tools.apj.journal import Journal

@pytest.fixture
def temp_journal(tmp_path):
    journal_dir = tmp_path / "docs"
    journal_dir.mkdir()
    journal_file = journal_dir / "PROJECT_JOURNAL.md"
    content = """# rpgCore — Project Journal

## Current State
Initial state.

## In Flight
Nothing.

## Next Priority
Testing.
"""
    journal_file.write_text(content, encoding="utf-8")
    return Journal(root_dir=str(tmp_path))

def test_journal_loads(temp_journal):
    content = temp_journal.load()
    assert "# rpgCore — Project Journal" in content
    assert "## Current State" in content

def test_get_section_returns_content(temp_journal):
    section = temp_journal.get_section("Current State")
    assert section == "Initial state."
    
    section = temp_journal.get_section("Next Priority")
    assert section == "Testing."

def test_get_handoff_contains_date(temp_journal):
    from datetime import datetime
    handoff = temp_journal.get_handoff()
    date_str = datetime.now().strftime("%Y-%m-%d")
    assert date_str in handoff

def test_get_handoff_contains_all_sections(temp_journal):
    handoff = temp_journal.get_handoff()
    assert "Initial state." in handoff
    assert "Nothing." in handoff
    assert "Testing." in handoff

def test_update_section_persists(temp_journal):
    temp_journal.update_section("In Flight", "Building APJ.")
    assert temp_journal.get_section("In Flight") == "Building APJ."
    
    # Reload to verify file write
    new_journal = Journal(root_dir=temp_journal.root_dir)
    assert new_journal.get_section("In Flight") == "Building APJ."
def test_get_handoff_contains_environment(temp_journal):
    handoff = temp_journal.get_handoff()
    assert "ENVIRONMENT: Windows (PowerShell/CMD)" in handoff
    assert "Do NOT use: cp, mv, rm, touch, grep, ls" in handoff

def test_get_boot_block_contains_environment(temp_journal):
    boot = temp_journal.get_boot_block()
    assert "rpgCore — Agent Boot Sequence" in boot
    assert "ENVIRONMENT: Windows PowerShell" in boot
    assert "STEP 0 — Verify orientation" in boot

def test_update_current_flag_via_cli_simulation(temp_journal):
    # Simulating the CLI update with flag
    new_content = "327 passing tests. Shared physics, input, spawner base established. APJ boot command live."
    temp_journal.update_section("Current State", new_content)
    assert temp_journal.get_section("Current State") == new_content
@pytest.fixture
def temp_journal_with_tasks(tmp_path):
    journal_dir = tmp_path / "docs"
    journal_dir.mkdir(exist_ok=True)
    
    # Journal file
    journal_file = journal_dir / "PROJECT_JOURNAL.md"
    journal_file.write_text("# rpgCore — Project Journal\n\n## Current State\nState.\n\n## In Flight\nFlight.\n\n## Next Priority\nPriority.\n", encoding="utf-8")
    
    # Tasks file
    tasks_file = journal_dir / "TASKS.md"
    tasks_content = "# rpgCore — Task Backlog\n\n## Active\n- [TOOL] APJ\n\n## Queued\n- [FEAT] Task 1\n- [FEAT] Task 2\n- [FEAT] Task 3\n- [FEAT] Task 4\n\n## Backlog\n\n## Completed\n"
    tasks_file.write_text(tasks_content, encoding="utf-8")
    
    return Journal(root_dir=str(tmp_path))

def test_tasks_file_loads(temp_journal_with_tasks):
    content = temp_journal_with_tasks.load(temp_journal_with_tasks.tasks_path)
    assert "# rpgCore — Task Backlog" in content

def test_tasks_add_appends_to_queued(temp_journal_with_tasks):
    temp_journal_with_tasks.add_task("[FEAT] Task 5")
    queued = temp_journal_with_tasks.get_section("Queued", temp_journal_with_tasks.tasks_path)
    assert "- [FEAT] Task 5" in queued

def test_tasks_done_moves_to_completed(temp_journal_with_tasks):
    # Setup: ensure Task 1 is there
    queued = temp_journal_with_tasks.get_section("Queued", temp_journal_with_tasks.tasks_path)
    assert "Task 1" in queued
    
    temp_journal_with_tasks.complete_task("Task 1")
    
    # Check it's gone from Queued
    queued_after = temp_journal_with_tasks.get_section("Queued", temp_journal_with_tasks.tasks_path)
    assert "Task 1" not in queued_after
    
    # Check it's in Completed
    completed = temp_journal_with_tasks.get_section("Completed", temp_journal_with_tasks.tasks_path)
    assert "Task 1" in completed

def test_get_next_tasks_returns_top_three(temp_journal_with_tasks):
    next_tasks = temp_journal_with_tasks.get_next_tasks(3)
    assert "1. [FEAT] Task 1" in next_tasks
    assert "2. [FEAT] Task 2" in next_tasks
    assert "3. [FEAT] Task 3" in next_tasks
    assert "4. [FEAT] Task 4" not in next_tasks

def test_handoff_contains_queued_tasks(temp_journal_with_tasks):
    handoff = temp_journal_with_tasks.get_handoff()
    assert "QUEUED TASKS (top 3):" in handoff
    assert "1. [FEAT] Task 1" in handoff

def test_get_handoff_protected_floor_updated(temp_journal_with_tasks):
    handoff = temp_journal_with_tasks.get_handoff()
    assert "PROTECTED FLOOR: 332 passing tests" in handoff
