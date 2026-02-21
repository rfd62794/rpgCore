# Implementation Plan: Inventory Directive

## Technical Approach

1. **Information Gathering**:
   - Use `list_dir` to map the root directory.
   - Use `find_by_name` to locate all Python files (`*.py`) inside `src`, `tools`, `scripts`, and `tests`.
   - Read the relevant core files (`src/core`, `src/engine`, `src/ui`, etc.) using `view_file` to determine their purpose and identify reusable systems.
   - Analyze `slime_clan/territorial_grid.py` to summarize its reusable pieces.

2. **Generate `INVENTORY.md`**:
   - Create a markdown file at `docs/INVENTORY.md`.
   - Section 1: Directory structure (high-level tree).
   - Section 2: Component inventory (1-line summaries of non-Slime Clan Python files).
   - Section 3: System inventory (reusable game loops, entities, UI).
   - Section 4: Slime Clan summary (what `territorial_grid.py` provides).
   - Section 5: Gaps for an Overworld screen.

3. **Commit**:
   - Use `run_command` with `git add docs/INVENTORY.md` and `git commit -m "docs: Add rpgCore repository and system INVENTORY.md"`.

## Verification Plan
- Ensure `docs/INVENTORY.md` exists and contains all 5 required sections accurately reflecting the codebase.
- Ensure the commit is present on the `main` branch.
