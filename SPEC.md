# Project Specification: Session 011 — Tile Intelligence HUD

## Directive Summary
Initialize Session 011 — Tile Intelligence HUD. Add hover-state feedback to tiles to provide context-aware text in the HUD and visually highlight the hovered tile.

## Technical Requirements
1. **Core Function:** Track `hovered_tile` as `(col, row)` or `None`, updated in `handle_events` on `MOUSEMOTION`.
2. **HUD Updates:** Render a tooltip-style info line in the battle log strip at the bottom of the sidebar showing context-aware text based on the hovered tile:
   - Hovering **NEUTRAL**: `Claim: Free → yours instantly`
   - Hovering **RED**: `Battle: B:X vs R:X → Y% win chance` (using `compute_battle_strength()` or calculating the probability dynamically as done in `resolve_battle_weighted`)
   - Hovering **BLUE**: `Owned — X adjacent Blue tiles` (compute adjacency)
   - Hovering **BLOCKED**: `Impassable`
   - No hover: show last battle result as before
3. **Visuals:** Highlight the hovered tile with a subtle 1px white border so it's clear which tile is being read.
4. **Testing:** 
   - All 75 existing tests must still pass. 
   - Add tests for hover state tracking and strength display logic.

## Future Parking Lot
- Cell expansion / energy nodes. Parked for now to maintain focus on the core interaction feedback loop. Will evaluate for future sessions.

