"""
Territorial Grid Prototype — Spec-001, Session 003
===================================================
A 10x10 tile-based territorial map rendered inside the rpgCore game loop.
Each tile tracks ownership: Neutral, Blue Clan, or Red Clan.

Session 003 — Seed Initial State:
  On launch the board starts in a war footing:
    Blue clan owns a 2×2 cluster in the top-left corner.
    Red clan owns a 2×2 cluster in the bottom-right corner.
    All other tiles remain Neutral (contested space).

Session 002 — Contested Tile Logic (intent-aware interaction):
  NEUTRAL tile  → instant Blue claim (free land, no fight needed)
  BLUE tile     → no action (already owned)
  RED tile      → resolve_battle() stub; winner applied to tile

Architecture: Flat module, mirroring simple_visual_asteroids.py loop contract.
  handle_events → update → render → clock.tick(60)
"""

import sys
import enum
import random
from pathlib import Path
from typing import List

import pygame
from loguru import logger

# ---------------------------------------------------------------------------
# Rendering Constants — 640×480 native surface (no pixel scaling)
# ---------------------------------------------------------------------------
WINDOW_WIDTH: int = 640
WINDOW_HEIGHT: int = 480
WINDOW_TITLE: str = "rpgCore — Slime Clan Territorial Prototype [Session 001]"
FPS: int = 60

# Grid layout — 10×10 tiles of 48px each = 480px fills full window height.
# 80px left margin centres the 480px grid in a 640px wide window.
GRID_COLS: int = 10
GRID_ROWS: int = 10
TILE_SIZE: int = 48           # px per tile
GRID_OFFSET_X: int = 80      # (640 - 480) // 2  — horizontal centre
GRID_OFFSET_Y: int = 0       # grid fills full height, no vertical offset
BORDER_PX: int = 1           # px border drawn around each tile


# ---------------------------------------------------------------------------
# Ownership State
# ---------------------------------------------------------------------------
class TileState(enum.IntEnum):
    NEUTRAL = 0
    BLUE = 1
    RED = 2


# Visually distinct colours for each ownership state
TILE_COLORS: dict[TileState, tuple[int, int, int]] = {
    TileState.NEUTRAL: (70, 70, 70),    # dark slate — unclaimed territory
    TileState.BLUE:    (30, 110, 220),  # bold blue  — Blue Clan
    TileState.RED:     (210, 50,  50),  # bold red   — Red Clan
}

# Lighter shade drawn as an inner highlight to add visual depth
TILE_HIGHLIGHT: dict[TileState, tuple[int, int, int]] = {
    TileState.NEUTRAL: (100, 100, 100),
    TileState.BLUE:    (70,  150, 255),
    TileState.RED:     (255, 90,   90),
}

BORDER_COLOR: tuple[int, int, int] = (20, 20, 20)
BACKGROUND_COLOR: tuple[int, int, int] = (15, 15, 20)
SIDEBAR_TEXT_COLOR: tuple[int, int, int] = (200, 200, 200)


# ---------------------------------------------------------------------------
# Battle resolution stub (Session 002)
# ---------------------------------------------------------------------------
def resolve_battle(attacker: str, defender: str) -> str:
    """
    Stub battle resolver — returns winner name at random.

    This is the seam for real battle logic in Session 003+.
    Signature is intentionally simple: plain strings for easy testing.

    Args:
        attacker: Clan name initiating the attack (e.g. 'BLUE')
        defender: Clan name defending the tile (e.g. 'RED')

    Returns:
        The winning clan name — either attacker or defender.
    """
    winner = random.choice([attacker, defender])
    logger.info("⚔️  Battle: {} attacks {} → {} wins", attacker, defender, winner)
    return winner


# ---------------------------------------------------------------------------
# Initial board seeding (Session 003)
# ---------------------------------------------------------------------------
def seed_initial_state(grid: list[list[TileState]]) -> None:
    """
    Set the starting board configuration in-place.

    Blue clan: 2×2 cluster in the top-left corner     — cols 0-1, rows 0-1
    Red clan:  2×2 cluster in the bottom-right corner — cols 8-9, rows 8-9
    All other tiles remain NEUTRAL.

    Pure function over the grid list — no pygame, no side effects beyond
    mutating the passed grid. Easy to test and easy to swap in Session 004+.
    """
    # Blue home territory — top-left 2×2
    for row in range(2):
        for col in range(2):
            grid[row][col] = TileState.BLUE

    # Red rival territory — bottom-right 2×2
    for row in range(8, 10):
        for col in range(8, 10):
            grid[row][col] = TileState.RED

    logger.info(
        "🌱 Board seeded — Blue top-left 2×2, Red bottom-right 2×2, {} neutral tiles",
        GRID_COLS * GRID_ROWS - 4 - 4,
    )


# ---------------------------------------------------------------------------
# Pure helper — coordinate mapping (tested independently of pygame)
# ---------------------------------------------------------------------------
def screen_pos_to_tile(
    mouse_x: int,
    mouse_y: int,
    offset_x: int = GRID_OFFSET_X,
    offset_y: int = GRID_OFFSET_Y,
    tile_size: int = TILE_SIZE,
    cols: int = GRID_COLS,
    rows: int = GRID_ROWS,
) -> tuple[int, int] | None:
    """
    Convert a screen pixel position to a (col, row) tile coordinate.

    Returns None if the position is outside the grid bounds.
    No SCALE_FACTOR division is needed — surface is native 640×480.
    """
    col = (mouse_x - offset_x) // tile_size
    row = (mouse_y - offset_y) // tile_size
    if 0 <= col < cols and 0 <= row < rows:
        return col, row
    return None


# ---------------------------------------------------------------------------
# Prototype game object
# ---------------------------------------------------------------------------
class TerritorialGrid:
    """
    Territorial map prototype.

    Owns the pygame window and the 10×10 ownership grid.
    Follows the rpgCore loop contract:
        handle_events() → update() → render() → clock.tick(60)
    """

    def __init__(self) -> None:
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        pygame.display.set_caption(WINDOW_TITLE)

        # 10×10 grid — seeded with starting state (Session 003)
        self.grid: List[List[TileState]] = [
            [TileState.NEUTRAL] * GRID_COLS for _ in range(GRID_ROWS)
        ]
        seed_initial_state(self.grid)

        self.running: bool = True
        self.click_count: int = 0       # total clicks on the grid
        self.battles_fought: int = 0    # RED tile attacks attempted
        self.last_battle_result: str = "—"  # shown in sidebar HUD

        # Font for sidebar HUD — fall back gracefully
        try:
            self.font_large = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 20)
        except Exception:
            self.font_large = pygame.font.SysFont("monospace", 22)
            self.font_small = pygame.font.SysFont("monospace", 16)

        logger.info(
            "🗺️  TerritorialGrid initialised — {}×{} window, {}×{} grid",
            WINDOW_WIDTH, WINDOW_HEIGHT, GRID_COLS, GRID_ROWS,
        )

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        """Process pygame events — quit and tile-click."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        """
        Intent-aware tile interaction (Session 002).

        NEUTRAL → instant Blue claim (free land)
        BLUE    → no action (already owned by player)
        RED     → resolve_battle(); apply winner to tile
        """
        result = screen_pos_to_tile(pos[0], pos[1])
        if result is None:
            return  # click in sidebar — ignore

        col, row = result
        state = self.grid[row][col]
        self.click_count += 1

        if state == TileState.NEUTRAL:
            # Free land — instant claim, no battle needed
            self.grid[row][col] = TileState.BLUE
            logger.info("🏴 Tile ({},{}) claimed: NEUTRAL → BLUE", col, row)

        elif state == TileState.BLUE:
            # Already owned — do nothing
            logger.debug("🔵 Tile ({},{}) already owned by Blue — no action", col, row)

        elif state == TileState.RED:
            # Enemy tile — fight for it
            self.battles_fought += 1
            winner = resolve_battle(attacker="BLUE", defender="RED")
            self.grid[row][col] = TileState.BLUE if winner == "BLUE" else TileState.RED
            self.last_battle_result = (
                f"({col},{row}) → {winner} wins"
            )

    # ------------------------------------------------------------------
    # Update (reserved — no logic yet for Session 001)
    # ------------------------------------------------------------------
    def update(self) -> None:
        """Reserved for future battle resolution stub (Session 002+)."""
        pass

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def render(self) -> None:
        """Draw the full frame: background, grid tiles, borders, HUD."""
        self.screen.fill(BACKGROUND_COLOR)
        self._draw_grid()
        self._draw_sidebar()
        pygame.display.flip()

    def _draw_grid(self) -> None:
        """Draw all 10×10 tiles with fill, inner highlight, and border."""
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                state = self.grid[row][col]
                x = GRID_OFFSET_X + col * TILE_SIZE
                y = GRID_OFFSET_Y + row * TILE_SIZE

                # Filled tile background
                tile_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, TILE_COLORS[state], tile_rect)

                # Inner highlight stripe (top-left corner, 3px)
                highlight_rect = pygame.Rect(
                    x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4
                )
                pygame.draw.rect(
                    self.screen, TILE_HIGHLIGHT[state], highlight_rect, 2
                )

                # Tile border
                pygame.draw.rect(
                    self.screen, BORDER_COLOR, tile_rect, BORDER_PX
                )

    def _draw_sidebar(self) -> None:
        """Render ownership counts and instructions in the left sidebar."""
        blue_count = sum(
            self.grid[r][c] == TileState.BLUE
            for r in range(GRID_ROWS)
            for c in range(GRID_COLS)
        )
        red_count = sum(
            self.grid[r][c] == TileState.RED
            for r in range(GRID_ROWS)
            for c in range(GRID_COLS)
        )
        neutral_count = GRID_COLS * GRID_ROWS - blue_count - red_count

        sidebar_x = 6
        lines = [
            ("SLIME CLAN", (180, 180, 120), self.font_large),
            ("Session 003", (130, 130, 130), self.font_small),
            ("", SIDEBAR_TEXT_COLOR, self.font_small),
            ("TERRITORY", (180, 180, 120), self.font_small),
            (f"  Blue  {blue_count:>3}", TILE_HIGHLIGHT[TileState.BLUE], self.font_small),
            (f"  Red   {red_count:>3}", TILE_HIGHLIGHT[TileState.RED], self.font_small),
            (f"  Neutral{neutral_count:>2}", TILE_HIGHLIGHT[TileState.NEUTRAL], self.font_small),
            ("", SIDEBAR_TEXT_COLOR, self.font_small),
            (f"Battles: {self.battles_fought}", SIDEBAR_TEXT_COLOR, self.font_small),
            (f"Last:", SIDEBAR_TEXT_COLOR, self.font_small),
            (f" {self.last_battle_result}", (220, 200, 100), self.font_small),
            ("", SIDEBAR_TEXT_COLOR, self.font_small),
            ("CONTROLS", (180, 180, 120), self.font_small),
            ("Neutral: claim", SIDEBAR_TEXT_COLOR, self.font_small),
            ("Red: battle", SIDEBAR_TEXT_COLOR, self.font_small),
            ("Blue: owned", SIDEBAR_TEXT_COLOR, self.font_small),
            ("ESC: quit", SIDEBAR_TEXT_COLOR, self.font_small),
        ]

        y = 12
        for text, color, font in lines:
            if text:
                surf = font.render(text, True, color)
                self.screen.blit(surf, (sidebar_x, y))
            y += font.size("A")[1] + 3

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> int:
        """
        Main game loop.

        Returns 0 on clean exit, 1 on unhandled exception.
        """
        clock = pygame.time.Clock()
        logger.info("▶️  Game loop started — press ESC or close window to exit")

        try:
            while self.running:
                self.handle_events()
                self.update()
                self.render()
                clock.tick(FPS)

            logger.info("🛑 Game loop exited cleanly")
            return 0

        except Exception as exc:
            logger.exception("💥 Unhandled exception in game loop: {}", exc)
            return 1

    def cleanup(self) -> None:
        """Release pygame resources."""
        pygame.quit()
        logger.info("🧹 TerritorialGrid cleanup complete")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
def main() -> int:
    """Configure logging and launch the territorial grid prototype."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:HH:mm:ss} | {level:<7} | {message}",
        colorize=True,
    )

    logger.info("🗺️  rpgCore — Slime Clan Territorial Prototype launching…")
    game = TerritorialGrid()
    try:
        return game.run()
    finally:
        game.cleanup()


if __name__ == "__main__":
    sys.exit(main())
