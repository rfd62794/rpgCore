"""
tests/unit/test_apj_parser.py

Unit tests for the APJ corpus parser (Phase 2).
Uses tmp_path fixtures with real markdown frontmatter.
Target: 422 baseline + 12 new = 434 passing.
"""

from datetime import date, datetime
from pathlib import Path

import pytest

from src.tools.apj.parser import (
    ParseError,
    ValidationResult,
    build_corpus,
    parse_file,
    validate_corpus,
)
from src.tools.apj.parser.doc_parser import (
    _extract_frontmatter_blocks,
    _parse_record,
)
from src.tools.apj.schema import (
    Corpus,
    Goal,
    GoalStatus,
    Task,
    TaskScope,
    TaskStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


GOAL_BLOCK = """\
---
id: G1
type: goal
title: Ship the Parser
status: ACTIVE
owner: human
created: 2026-02-25
modified: 2026-02-25
tags: [parser, apl]
---

Prose description here.
"""

TASK_BLOCK = """\
---
id: T1
type: task
title: Write doc_parser.py
status: ACTIVE
scope: tooling
owner: human
created: 2026-02-25
modified: 2026-02-25
tags: []
---
"""

TASK_LAW1_BLOCK = """\
---
id: T2
type: task
title: Bad shared task
status: ACTIVE
scope: shared
demo: slime_breeder
owner: human
created: 2026-02-25
modified: 2026-02-25
tags: []
---
"""

UNKNOWN_TYPE_BLOCK = """\
---
id: X1
type: widget
title: Unknown
status: ACTIVE
owner: human
created: 2026-02-25
modified: 2026-02-25
---
"""

MULTI_BLOCK = GOAL_BLOCK + "\n" + TASK_BLOCK


# ---------------------------------------------------------------------------
# Frontmatter extraction
# ---------------------------------------------------------------------------

def test_extract_frontmatter_single_block():
    """One valid frontmatter block is extracted as a single dict."""
    blocks = _extract_frontmatter_blocks(GOAL_BLOCK)
    assert len(blocks) == 1
    assert blocks[0]["id"] == "G1"
    assert blocks[0]["type"] == "goal"


def test_extract_frontmatter_multiple_blocks():
    """Multiple frontmatter blocks in one file are all extracted."""
    blocks = _extract_frontmatter_blocks(MULTI_BLOCK)
    assert len(blocks) == 2
    ids = {b["id"] for b in blocks}
    assert ids == {"G1", "T1"}


# ---------------------------------------------------------------------------
# Record parsing
# ---------------------------------------------------------------------------

def test_parse_goal_record():
    """Valid goal frontmatter dict → Goal instance with correct fields."""
    data = {
        "id": "G2",
        "type": "goal",
        "title": "Test Goal",
        "status": "ACTIVE",
        "owner": "human",
        "created": date(2026, 2, 25),
        "modified": date(2026, 2, 25),
        "tags": [],
    }
    record = _parse_record(data)
    assert isinstance(record, Goal)
    assert record.id == "G2"
    assert record.status == GoalStatus.ACTIVE


def test_parse_task_record():
    """Valid task frontmatter dict → Task instance."""
    data = {
        "id": "T3",
        "type": "task",
        "title": "Parser task",
        "status": "ACTIVE",
        "scope": "tooling",
        "owner": "human",
        "created": date(2026, 2, 25),
        "modified": date(2026, 2, 25),
        "tags": [],
    }
    record = _parse_record(data)
    assert isinstance(record, Task)
    assert record.scope == TaskScope.TOOLING


def test_parse_task_law1_violation_raises():
    """scope=shared with demo field → ParseError (LAW 1 via model_validator)."""
    data = {
        "id": "T4",
        "type": "task",
        "title": "Bad task",
        "status": "ACTIVE",
        "scope": "shared",
        "demo": "slime_breeder",
        "owner": "human",
        "created": date(2026, 2, 25),
        "modified": date(2026, 2, 25),
        "tags": [],
    }
    with pytest.raises(ParseError, match="Validation failed"):
        _parse_record(data)


def test_parse_unknown_type_raises():
    """An unknown type string → ParseError."""
    data = {
        "id": "X1",
        "type": "widget",
        "title": "Unknown",
        "owner": "human",
        "created": date(2026, 2, 25),
        "modified": date(2026, 2, 25),
    }
    with pytest.raises(ParseError, match="Unknown record type"):
        _parse_record(data)


# ---------------------------------------------------------------------------
# parse_file
# ---------------------------------------------------------------------------

def test_parse_file_missing_returns_empty(tmp_path):
    """parse_file on a non-existent path returns empty list, never raises."""
    result = parse_file(tmp_path / "does_not_exist.md")
    assert result == []


def test_parse_file_skips_invalid_blocks(tmp_path):
    """A file with one bad block and one good block: bad is skipped, good parsed."""
    content = GOAL_BLOCK + "\n" + TASK_LAW1_BLOCK
    path = _write(tmp_path, "mixed.md", content)
    records = parse_file(path)
    # Only the valid GOAL block should survive
    assert len(records) == 1
    assert isinstance(records[0], Goal)


# ---------------------------------------------------------------------------
# build_corpus
# ---------------------------------------------------------------------------

def test_build_corpus_empty_docs(tmp_path, monkeypatch):
    """build_corpus with no real docs → empty Corpus, no raise."""
    import src.tools.apj.parser.doc_parser as dp

    # Point _DOC_PATHS to non-existent paths in tmp_path
    monkeypatch.setattr(dp, "_DOC_PATHS", {
        "goals":      tmp_path / "GOALS.md",
        "milestones": tmp_path / "MILESTONES.md",
        "tasks":      tmp_path / "TASKS.md",
        "journal":    tmp_path / "PROJECT_JOURNAL.md",
    })
    corpus = build_corpus()
    assert isinstance(corpus, Corpus)
    assert corpus.goals == []
    assert corpus.tasks == []


def test_build_corpus_with_goals(tmp_path, monkeypatch):
    """build_corpus with a goals file → Corpus.goals populated."""
    import src.tools.apj.parser.doc_parser as dp

    goals_file = _write(tmp_path, "GOALS.md", GOAL_BLOCK)
    monkeypatch.setattr(dp, "_DOC_PATHS", {
        "goals":      goals_file,
        "milestones": tmp_path / "MILESTONES.md",
        "tasks":      tmp_path / "TASKS.md",
        "journal":    tmp_path / "PROJECT_JOURNAL.md",
    })
    corpus = build_corpus()
    assert len(corpus.goals) == 1
    assert corpus.goals[0].id == "G1"
    assert corpus.corpus_hash  # non-empty SHA256


# ---------------------------------------------------------------------------
# validate_corpus
# ---------------------------------------------------------------------------

def test_validate_corpus_clean():
    """A self-consistent corpus → ValidationResult.passed is True."""
    from src.tools.apj.schema import Goal, Milestone, GoalStatus, MilestoneStatus, OwnerType

    g = Goal(
        id="G1", title="Ship it", status=GoalStatus.ACTIVE,
        milestone="M1", owner=OwnerType.HUMAN,
        created=date(2026, 2, 25), modified=date(2026, 2, 25),
    )
    m = Milestone(
        id="M1", title="Phase 1", status=MilestoneStatus.ACTIVE,
        goals=["G1"], owner=OwnerType.HUMAN,
        created=date(2026, 2, 25), modified=date(2026, 2, 25),
    )
    corpus = Corpus(
        goals=[g], milestones=[m], tasks=[], journal=[],
        parsed_at=datetime(2026, 2, 25, 6, 0, 0),
    )
    result = validate_corpus(corpus)
    assert result.passed is True
    assert result.errors == []
    assert "valid" in result.summary()


def test_validate_corpus_orphan():
    """Goal referencing unknown milestone → error in ValidationResult."""
    from src.tools.apj.schema import Goal, GoalStatus, OwnerType

    g = Goal(
        id="G99", title="Orphan", status=GoalStatus.ACTIVE,
        milestone="M_GHOST", owner=OwnerType.HUMAN,
        created=date(2026, 2, 25), modified=date(2026, 2, 25),
    )
    corpus = Corpus(
        goals=[g], milestones=[], tasks=[], journal=[],
        parsed_at=datetime(2026, 2, 25, 6, 0, 0),
    )
    result = validate_corpus(corpus)
    assert result.passed is False
    assert result.error_count == 1
    assert any("unknown milestone" in e for e in result.errors)
    assert "violation" in result.summary()
