"""
Unit tests for Territorial Grid Prototype — Spec-001, Session 001

Tests are scoped to logic units that can be verified without a pygame display:
  1. TileState ownership cycle
  2. screen_pos_to_tile coordinate mapping
  3. Grid initialisation

Run with:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_territorial_grid.py -v
"""

import pytest
import sys
from pathlib import Path

# Make src importable without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from apps.slime_clan.territorial_grid import (
    TileState,
    screen_pos_to_tile,
    GRID_COLS,
    GRID_ROWS,
    TILE_SIZE,
    GRID_OFFSET_X,
    GRID_OFFSET_Y,
)


# ---------------------------------------------------------------------------
# 1. Ownership cycle
# ---------------------------------------------------------------------------
class TestTileStateCycle:
    """TileState must cycle NEUTRAL → BLUE → RED → NEUTRAL using % 3."""

    def test_neutral_to_blue(self) -> None:
        state = TileState.NEUTRAL
        assert TileState((state + 1) % 3) == TileState.BLUE

    def test_blue_to_red(self) -> None:
        state = TileState.BLUE
        assert TileState((state + 1) % 3) == TileState.RED

    def test_red_wraps_to_neutral(self) -> None:
        """Red must wrap back to Neutral — not overflow."""
        state = TileState.RED
        assert TileState((state + 1) % 3) == TileState.NEUTRAL

    def test_full_cycle(self) -> None:
        """Three successive cycles must return to the starting state."""
        state = TileState.NEUTRAL
        for _ in range(3):
            state = TileState((state + 1) % 3)
        assert state == TileState.NEUTRAL


# ---------------------------------------------------------------------------
# 2. Coordinate mapping
# ---------------------------------------------------------------------------
class TestScreenPosToTile:
    """screen_pos_to_tile must map pixel positions to (col, row) correctly."""

    def test_top_left_tile(self) -> None:
        # Pixel at GRID_OFFSET_X, GRID_OFFSET_Y → tile (0, 0)
        result = screen_pos_to_tile(GRID_OFFSET_X, GRID_OFFSET_Y)
        assert result == (0, 0)

    def test_second_column_tile(self) -> None:
        # One TILE_SIZE to the right of the first tile → col 1
        x = GRID_OFFSET_X + TILE_SIZE
        y = GRID_OFFSET_Y
        result = screen_pos_to_tile(x, y)
        assert result == (1, 0)

    def test_bottom_right_tile(self) -> None:
        # Pixel just inside the last tile
        x = GRID_OFFSET_X + (GRID_COLS - 1) * TILE_SIZE + 1
        y = GRID_OFFSET_Y + (GRID_ROWS - 1) * TILE_SIZE + 1
        result = screen_pos_to_tile(x, y)
        assert result == (GRID_COLS - 1, GRID_ROWS - 1)

    def test_click_in_sidebar_returns_none(self) -> None:
        # Pixel in the left sidebar (x < GRID_OFFSET_X) → None
        result = screen_pos_to_tile(0, 0)
        assert result is None

    def test_click_beyond_right_edge_returns_none(self) -> None:
        # Pixel one tile past the right edge
        x = GRID_OFFSET_X + GRID_COLS * TILE_SIZE + 1
        result = screen_pos_to_tile(x, GRID_OFFSET_Y)
        assert result is None

    def test_click_below_grid_returns_none(self) -> None:
        # Pixel below the bottom row
        y = GRID_OFFSET_Y + GRID_ROWS * TILE_SIZE + 1
        result = screen_pos_to_tile(GRID_OFFSET_X, y)
        assert result is None

    def test_negative_position_returns_none(self) -> None:
        result = screen_pos_to_tile(-1, -1)
        assert result is None


# ---------------------------------------------------------------------------
# 3. Grid initialisation
# ---------------------------------------------------------------------------
class TestGridInitialisation:
    """Grid must be 10×10 and all NEUTRAL at startup — no pygame required."""

    def test_all_tiles_neutral(self) -> None:
        grid = [[TileState.NEUTRAL] * GRID_COLS for _ in range(GRID_ROWS)]
        for row in grid:
            for tile in row:
                assert tile == TileState.NEUTRAL

    def test_grid_dimensions(self) -> None:
        grid = [[TileState.NEUTRAL] * GRID_COLS for _ in range(GRID_ROWS)]
        assert len(grid) == GRID_ROWS
        assert all(len(row) == GRID_COLS for row in grid)
