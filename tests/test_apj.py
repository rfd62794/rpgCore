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
