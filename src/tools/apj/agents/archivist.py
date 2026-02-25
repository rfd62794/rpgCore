"""
archivist.py — APJ Archivist Agent

Single responsibility: read the APJ corpus and produce a Coherence Report
before every session. The report surfaces drift, risks, and constitutional
violations so the developer starts each session oriented.

Constitutional Four Laws (what the Archivist watches for):
  1. Demo-specific logic creeping into src/shared/
  2. Content gating between demos
  3. New scenes not inheriting from scene templates
  4. Test count below the current floor (402)

Offline fallback: if Ollama is unreachable, produces a deterministic stub
from raw markdown content. Sessions NEVER fail to start.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.tools.apj.agents.ollama_client import get_ollama_model

# ---------------------------------------------------------------------------
# Project root — two levels up from src/tools/apj/agents/
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[4]

# APJ corpus paths (relative to project root)
_CORPUS_PATHS: dict[str, Path] = {
    "journal":    _PROJECT_ROOT / "docs" / "JOURNAL.md",
    "tasks":      _PROJECT_ROOT / "docs" / "TASKS.md",
    "goals":      _PROJECT_ROOT / "docs" / "GOALS.md",
    "milestones": _PROJECT_ROOT / "docs" / "MILESTONES.md",
}

# Where session reports are saved
_SESSION_LOGS_DIR = _PROJECT_ROOT / "docs" / "session_logs"

# Constitutional laws (injected into the Archivist's system prompt)
_FOUR_LAWS = """
The Four Constitutional Laws of rpgCore:
  LAW 1 — No demo-specific logic in src/shared/. Shared code must be generic.
  LAW 2 — No content gating between demos. Each demo is self-contained.
  LAW 3 — Every new scene must inherit from a scene template in src/shared/engine/scene_templates/.
  LAW 4 — The test floor is 402 passing tests. Do not regress below this.
"""


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class CoherenceReport(BaseModel):
    """Structured output from the Archivist agent."""

    session_primer: str = Field(
        description="2-sentence summary of current project state and momentum."
    )
    open_risks: list[str] = Field(
        default_factory=list,
        description="Detected blockers, spec drift, broken references, or orphaned goals."
    )
    queued_focus: str = Field(
        description="Single top-priority task recommendation for this session."
    )
    constitutional_flags: list[str] = Field(
        default_factory=list,
        description=(
            "Any patterns in the corpus that violate the Four Constitutional Laws: "
            "demo logic in shared, content gating, scenes not using templates, "
            "or test count at risk."
        )
    )
    corpus_hash: str = Field(
        description="SHA256 of the combined corpus content for change detection."
    )


# ---------------------------------------------------------------------------
# Archivist
# ---------------------------------------------------------------------------
class Archivist:
    """
    The APJ Archivist: reads the project corpus and generates a Coherence Report.

    Design:
    - Uses llama3.2:3b via Ollama (quality over speed for coherence reasoning)
    - Falls back to a deterministic stub if Ollama is unreachable
    - Always saves the report to docs/session_logs/
    - Never raises — sessions must always be able to start
    """

    def __init__(self, model_name: str = "llama3.2:3b") -> None:
        self.model_name = model_name
        self._agent: Optional[Agent] = None
        logger.info(f"Archivist initialized (model={model_name})")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> CoherenceReport:
        """
        Synchronous entry point. Reads corpus, calls Ollama, saves report.

        Returns:
            CoherenceReport — always, even if Ollama is down.
        """
        corpus = self._load_corpus()
        corpus_hash = self._hash_corpus(corpus)

        try:
            report = asyncio.run(self._run_async(corpus, corpus_hash))
        except Exception as exc:
            logger.warning(f"Archivist: Ollama unreachable or agent failed ({exc}). Using fallback.")
            report = self._fallback_report(corpus, corpus_hash)

        self._save_report(report)
        return report

    # ------------------------------------------------------------------
    # Internal: corpus handling
    # ------------------------------------------------------------------

    def _load_corpus(self) -> dict[str, str]:
        """Read all APJ markdown files. Missing files return empty string."""
        corpus: dict[str, str] = {}
        for key, path in _CORPUS_PATHS.items():
            if path.exists():
                try:
                    corpus[key] = path.read_text(encoding="utf-8")
                    logger.debug(f"Archivist: loaded {key} ({len(corpus[key])} chars)")
                except OSError as e:
                    logger.warning(f"Archivist: could not read {key}: {e}")
                    corpus[key] = ""
            else:
                logger.debug(f"Archivist: {key} not found at {path}")
                corpus[key] = ""
        return corpus

    @staticmethod
    def _hash_corpus(corpus: dict[str, str]) -> str:
        """SHA256 of all corpus values concatenated."""
        combined = "\n".join(corpus.values()).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @staticmethod
    def _build_prompt(corpus: dict[str, str]) -> str:
        """Assemble the Archivist's user prompt from corpus content."""
        sections = []
        for key, content in corpus.items():
            if content.strip():
                sections.append(f"=== {key.upper()} ===\n{content[:3000]}")
            else:
                sections.append(f"=== {key.upper()} ===\n(empty)")
        return (
            "Analyze the following APJ project corpus and produce a CoherenceReport.\n\n"
            + "\n\n".join(sections)
        )

    # ------------------------------------------------------------------
    # Internal: agent
    # ------------------------------------------------------------------

    def _get_agent(self) -> Agent:
        """Lazy-init the pydantic_ai Agent."""
        if self._agent is None:
            model = get_ollama_model(model_name=self.model_name, temperature=0.3)
            system_prompt = (
                "You are the ARCHIVIST for rpgCore, a Python/Pygame game engine project. "
                "Your job is to read the Automated Project Journal (APJ) corpus and produce "
                "a structured CoherenceReport that orients the developer at the START of a session.\n\n"
                f"{_FOUR_LAWS}\n\n"
                "Rules:\n"
                "- session_primer: Exactly 2 sentences. State WHERE the project is and what MOMENTUM exists.\n"
                "- open_risks: List concrete risks you see (drift, broken refs, orphaned goals). "
                "  Empty list if none detected.\n"
                "- queued_focus: ONE clear task. Be specific (file, feature, test count).\n"
                "- constitutional_flags: List ONLY actual violations of the Four Laws. "
                "  Empty list if the corpus shows no violations.\n"
                "- corpus_hash: Leave blank — it will be filled programmatically.\n"
                "Be concise. No filler. The report is for a developer starting work."
            )
            self._agent = Agent(
                model=model,
                output_type=CoherenceReport,
                system_prompt=system_prompt,
            )
            logger.debug("Archivist: Agent initialized")
        return self._agent

    async def _run_async(self, corpus: dict[str, str], corpus_hash: str) -> CoherenceReport:
        """Run the pydantic_ai Agent asynchronously."""
        agent = self._get_agent()
        prompt = self._build_prompt(corpus)
        logger.info("Archivist: querying Ollama...")
        result = await agent.run(prompt)
        report: CoherenceReport = result.output
        # Overwrite corpus_hash with the computed value (model may leave it blank)
        report.corpus_hash = corpus_hash
        logger.info(
            f"Archivist: report complete — "
            f"{len(report.open_risks)} risks, "
            f"{len(report.constitutional_flags)} constitutional flags"
        )
        return report

    # ------------------------------------------------------------------
    # Internal: fallback
    # ------------------------------------------------------------------

    def _fallback_report(self, corpus: dict[str, str], corpus_hash: str) -> CoherenceReport:
        """
        Deterministic stub report built from raw corpus text.
        Used when Ollama is unreachable — never fails.
        """
        logger.warning("Archivist: generating fallback report from raw corpus (Ollama offline)")

        # Extract a rough session primer from JOURNAL.md first ~200 chars
        journal_excerpt = corpus.get("journal", "")[:200].strip()
        primer = (
            f"{journal_excerpt[:120]}..."
            if len(journal_excerpt) > 120
            else journal_excerpt or "Project corpus loaded. Ollama was offline — review corpus manually."
        )

        return CoherenceReport(
            session_primer=(
                f"{primer} "
                "[FALLBACK — Ollama unreachable. No AI analysis performed.]"
            ),
            open_risks=["Ollama was unreachable at session start — AI analysis skipped."],
            queued_focus="Verify Ollama is running (ollama list) then re-run session start.",
            constitutional_flags=[],
            corpus_hash=corpus_hash,
        )

    # ------------------------------------------------------------------
    # Internal: persistence
    # ------------------------------------------------------------------

    def _save_report(self, report: CoherenceReport) -> None:
        """Write the Coherence Report to docs/session_logs/."""
        _SESSION_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = _SESSION_LOGS_DIR / f"{timestamp}_archivist.md"

        lines = [
            f"# Archivist Coherence Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**Model:** {self.model_name}  ",
            f"**Corpus Hash:** `{report.corpus_hash}`\n",
            "## Session Primer",
            report.session_primer,
            "\n## Queued Focus",
            f"> {report.queued_focus}",
            "\n## Open Risks",
        ]

        if report.open_risks:
            lines += [f"- {r}" for r in report.open_risks]
        else:
            lines.append("_None detected._")

        lines.append("\n## Constitutional Flags")
        if report.constitutional_flags:
            lines += [f"- ⚠️ {f}" for f in report.constitutional_flags]
        else:
            lines.append("_No violations detected._")

        report_path.write_text("\n".join(lines), encoding="utf-8")
        try:
            display_path = report_path.relative_to(_PROJECT_ROOT)
        except ValueError:
            display_path = report_path
        logger.info(f"Archivist: report saved → {display_path}")

