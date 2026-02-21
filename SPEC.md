# Project Specification: Session 010 — Slime Sprites

## Directive Summary
Initialize Session 010 — Slime Sprites. Draw a slime sprite on each owned tile using `pygame.draw` primitives. No image files, no new dependencies.

## Technical Requirements
1. **Core Function:** Create `draw_slime(surface, cx, cy, tile_size, color)` as a pure drawing function.
2. **Geometry:**
   - Body: filled circle at 80% of tile size (diameter)
   - Eye: ellipse centered upper-middle
   - Pupil: smaller filled circle offset left and down
   - Mouth: quadratic curve using `pygame.draw.arc`
3. **Integration:** 
   - Blue tiles render a blue-tinted slime. Red tiles render a red-tinted slime.
   - Neutral and BLOCKED tiles remain unchanged (no slime).
   - Slimes are drawn centered within the tile, after the tile fill, before the border.
4. **Testing:** 
   - All 73 existing tests must still pass. 
   - Add 2 tests confirming `draw_slime` accepts valid color and size inputs without error.
