# Implementation Plan: Session 010 — Slime Sprites

## Technical Approach
1. **Import `math`**: Add `import math` to `territorial_grid.py` for drawing the arc (mouth).
2. **Define Colors**: Add `SLIME_COLORS: dict[TileState, tuple[int, int, int]]` containing base colors for `BLUE` and `RED` slimes.
3. **Implement `draw_slime`**:
   - Signature: `def draw_slime(surface: pygame.Surface, cx: int, cy: int, tile_size: int, color: tuple[int, int, int]) -> None:`
   - Scale geometries dynamically based on `tile_size`.
   - Body: `pygame.draw.circle`
   - Eye: `pygame.draw.ellipse`
   - Pupil: `pygame.draw.circle`
   - Mouth: `pygame.draw.arc` using `math.pi` to `2 * math.pi` in standard PyGame coordinates or adjusted appropriately to ensure it curves downwards like a smile (SVG `M26 48 Q32 52 38 48`).
4. **Integrate into `_draw_grid`**:
   - Inside `TerritorialGrid._draw_grid()`, immediately after drawing the highlight ring and before drawing the border, call `draw_slime` if state is `BLUE` or `RED`.
5. **Unit Tests**:
   - In `test_territorial_grid.py`, add `test_draw_slime_valid_inputs` and `test_draw_slime_small_size` targeting the new function. Check that `pygame.Surface` operations do not throw an error. Run via `uv run pytest`.

## Verification Steps
- `uv run pytest tests/unit/test_territorial_grid.py -v` ensures tests pass.
- `uv run python run_territorial_grid.py` ensures the game runs without crashing and visuals are correct.
