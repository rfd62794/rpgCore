"""
doc_parser.py — APJ Corpus Parser

Reads structured markdown documents with YAML frontmatter and
deserializes them into validated Pydantic schema objects.

Document format expected:
  ---
  id: G10
  type: goal
  title: The Living World
  status: ACTIVE
  milestone: M11
  owner: human
  created: 2026-02-20
  modified: 2026-02-24
  tags: [living-world, soul, aspects]
  ---
  
  Prose description here...

Parsing strategy:
  - Split document on --- delimiters
  - Parse YAML frontmatter blocks
  - Deserialize into typed Pydantic models
  - Collect all entries from a single file
  - Return typed list or raise ParseError with context
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Union

import yaml
from loguru import logger
from pydantic import ValidationError

from src.tools.apj.schema import (
    Goal, Milestone, Task, JournalEntry, Corpus,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[4]

DOCS_PLANNING = _PROJECT_ROOT / "docs" / "planning"
DOCS_JOURNAL  = _PROJECT_ROOT / "docs" / "journal"

_DOC_PATHS = {
    "goals":      DOCS_PLANNING / "GOALS.md",
    "milestones": DOCS_PLANNING / "MILESTONES.md",
    "tasks":      DOCS_PLANNING / "TASKS.md",
    "journal":    DOCS_JOURNAL  / "PROJECT_JOURNAL.md",
}

DocRecord = Union[Goal, Milestone, Task, JournalEntry]


class ParseError(Exception):
    """Raised when a document block cannot be parsed."""
    pass


def _extract_frontmatter_blocks(text: str) -> list[dict]:
    """
    Extract all YAML frontmatter blocks from a markdown document.
    Each block is delimited by --- lines.
    Returns list of parsed dicts. Skips blocks that fail YAML parse.
    """
    blocks = []
    parts = text.split("---")
    # parts[0] is before first ---, parts[1] is first block, etc.
    # Valid blocks are at odd indices if file starts with ---
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        try:
            data = yaml.safe_load(part)
            if isinstance(data, dict) and "id" in data:
                blocks.append(data)
        except yaml.YAMLError:
            continue
    return blocks


def _parse_record(data: dict) -> DocRecord:
    """
    Deserialize a frontmatter dict into the correct Pydantic model
    based on the 'type' field.
    """
    record_type = data.get("type", "").lower()

    try:
        if record_type == "goal":
            return Goal(**data)
        elif record_type == "milestone":
            return Milestone(**data)
        elif record_type == "task":
            return Task(**data)
        elif record_type == "journal":
            return JournalEntry(**data)
        else:
            raise ParseError(
                f"Unknown record type '{record_type}' in block: "
                f"{list(data.keys())}"
            )
    except ValidationError as e:
        raise ParseError(
            f"Validation failed for {record_type} '{data.get('id', '?')}': {e}"
        ) from e


def parse_file(path: Path) -> list[DocRecord]:
    """
    Parse all frontmatter records from a single markdown file.
    Returns list of typed Pydantic objects.
    Logs warnings for unparseable blocks, never raises.
    """
    if not path.exists():
        logger.debug(f"DocParser: {path.name} not found — skipping")
        return []

    text = path.read_text(encoding="utf-8")
    blocks = _extract_frontmatter_blocks(text)
    records = []

    for block in blocks:
        try:
            records.append(_parse_record(block))
        except ParseError as e:
            logger.warning(f"DocParser: skipped block in {path.name} — {e}")

    logger.debug(
        f"DocParser: {path.name} → {len(records)} records parsed"
    )
    return records


def build_corpus() -> Corpus:
    """
    Read all APJ planning documents and build a validated Corpus.
    Missing files produce empty collections — never raises.
    """
    goals: list[Goal] = []
    milestones: list[Milestone] = []
    tasks: list[Task] = []
    journal: list[JournalEntry] = []

    all_text: list[str] = []

    for key, path in _DOC_PATHS.items():
        records = parse_file(path)
        if path.exists():
            all_text.append(path.read_text(encoding="utf-8"))
        for record in records:
            if isinstance(record, Goal):
                goals.append(record)
            elif isinstance(record, Milestone):
                milestones.append(record)
            elif isinstance(record, Task):
                tasks.append(record)
            elif isinstance(record, JournalEntry):
                journal.append(record)

    corpus_hash = hashlib.sha256(
        "\n".join(all_text).encode("utf-8")
    ).hexdigest()

    corpus = Corpus(
        goals=goals,
        milestones=milestones,
        tasks=tasks,
        journal=journal,
        parsed_at=datetime.now(),
        corpus_hash=corpus_hash,
    )

    logger.info(
        f"DocParser: corpus built — "
        f"{len(goals)} goals, {len(milestones)} milestones, "
        f"{len(tasks)} tasks, {len(journal)} journal entries"
    )
    return corpus
