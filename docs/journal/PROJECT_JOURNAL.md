# rpgCore — Project Journal

## Current State
434 passing tests. APJ parser layer shipped: doc_parser.py (frontmatter extraction, typed dispatch, build_corpus), validator.py (ValidationResult, validate_corpus). pyyaml added. G10 frontmatter in GOALS.md — smoke test confirmed.

## In Flight
Phase 3 — wire parser into Archivist: replace raw markdown reads with build_corpus(), surface ValidationResult in CoherenceReport.

## Next Priority
Update Archivist._load_corpus() to call build_corpus() and pass structured Corpus to prompt builder.
