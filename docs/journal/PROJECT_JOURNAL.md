# rpgCore — Project Journal

## Current State
422 passing tests. APJ schema layer shipped: Pydantic corpus models (Goal, Milestone, Task, JournalEntry, Corpus), all enums, LAW 1+4 validators, CorpusValidator. Docs restructured into core/planning/journal/reference/agents subdirs. pydantic-ai installed into system Python.

## In Flight
Phase 2 — APJ corpus parser: read GOALS.md, TASKS.md, MILESTONES.md, PROJECT_JOURNAL.md into Corpus model.

## Next Priority
Build corpus parser that ingests the restructured markdown docs into validated Corpus instances using the Phase 1 schema.
