# Implementation Plan: Session 011 — Tile Intelligence HUD

## Technical Approach

### 1. `TerritorialGrid` State
- Add `self.hovered_tile: tuple[int, int] | None = None` to the `__init__` constructor.

### 2. Event Handling
- Modify `handle_events` to listen for `pygame.MOUSEMOTION`.
- Use `screen_pos_to_tile(event.pos[0], event.pos[1])` to update `self.hovered_tile`. 

### 3. Rendering Updates
- **Grid Rendering** (`_draw_grid`): If `self.hovered_tile` is `(col, row)`, draw a 1px white outline `#FFFFFF` directly over the tile at the end of its drawing block (or right after the standard border).
- **HUD Rendering** (`_draw_sidebar`): 
  - Update the battle log strip section. 
  - If `self.hovered_tile` is `None`, show the legacy "Last Battle" logic.
  - If `self.hovered_tile` is set, read `state = self.grid[row][col]`.
    - `NEUTRAL`: "Claim: Free → yours instantly"
    - `RED`: Compute Blue/Red strengths using `compute_battle_strength`. Calculate win percentage as `blue / (blue + red)`. Display "Battle: B:{b} vs R:{r} → {pct}% win chance".
    - `BLUE`: Count orthogonal adjacent blue tiles. Display "Owned — {adj} adjacent Blue tiles".
    - `BLOCKED`: "Impassable"

### 4. Unit Tests
- Add `TestHoverLogic` to `tests/unit/test_territorial_grid.py`.
- Test that hovering over different states computes the correct HUD text data (we can extract this HUD string generation into a pure function `get_hover_tooltip(grid, col, row, hover_state)` to make it easily testable without pygame window mocking).

## Verification Plan

### Automated Tests
- Run `uv run pytest tests/unit/test_territorial_grid.py -v`.
- Ensure all 75 previous tests pass plus the new hover logic tests.

### Manual Verification
- Run `uv run python run_territorial_grid.py`.
- Move the mouse across different tile states and verify the HUD text updates correctly and the 1px white outline appears on the correct tile.

