# Project Specification: Session 012 - Overworld Stub

## Directive Summary
Initialize Session 012 — Overworld Stub. Create `src/apps/slime_clan/overworld.py` as a new standalone screen that manages the macro-map layer for the Slime Clan game. Do not modify `territorial_grid.py` or existing `dgt_engine` components.

## Technical Requirements
1. **Resolution**: Simple pygame screen, 640×480 resolution.
2. **Nodes**: Display a static map of 5 named regions as clickable nodes connected by lines (hand-coded positions).
3. **Home Base**: One node is marked as the crashed ship / home base — visually distinct and non-contestable.
4. **Ownership**: Remaining 4 nodes show ownership state: Blue, Red, or Contested.
5. **Transitions**: Clicking a Contested or Red node launches `territorial_grid.py` as a subprocess or scene transition, passing the region name as context.
6. **State Updates**: Returning from battle updates that node's ownership on the overworld.
7. **Launcher**: Create a new launcher `run_overworld.py` at the repo root.
8. **Testing**: All 79 existing tests must remain passing. Add basic tests for node state management.

## Constraints
- Do not modify `territorial_grid.py` or `dgt_engine` core logic.
- Standalone execution via `run_overworld.py`.
- No procedural map generation in this session (hand-coded node map only).
