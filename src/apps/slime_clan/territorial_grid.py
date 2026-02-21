"""
Territorial Grid Prototype — Spec-001, Session 005
===================================================
A 10x10 tile-based territorial map rendered inside the rpgCore game loop.
Each tile tracks ownership: Neutral, Blue Clan, or Red Clan.

Session 005 — Turn Clarity & AI Intent:
  TurnState machine: PLAYER_TURN | AI_BLINKING.
  Player input blocked during AI blink. HUD shows whose turn it is.
  AI blink: 3 steps × 300 ms (white → original → white) then resolves.
  AI targeting: adjacency-weighted selection (adjacent to Red = ×5 priority).

Session 004 — Reactive AI: ai_take_turn() fires after every player action.
Session 003 — Seed Initial State: Blue top-left 2×2, Red bottom-right 2×2.
Session 002 — Contested Tile Logic: NEUTRAL→claim | BLUE→no-op | RED→battle.

Architecture: Flat module, mirroring simple_visual_asteroids.py loop contract.
  handle_events → update(dt_ms) → render → clock.tick(FPS)
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
# Ownership State & Turn State
# ---------------------------------------------------------------------------
class TileState(enum.IntEnum):
    NEUTRAL = 0
    BLUE = 1
    RED = 2


class TurnState(enum.Enum):
    PLAYER_TURN = "player"
    AI_BLINKING = "ai_blinking"


# Blink sequence: white(300ms) → original(300ms) → white(300ms) → resolve
BLINK_STEP_MS: int = 300
BLINK_STEPS: int = 3  # total steps in the sequence
FLASH_COLOR: tuple[int, int, int] = (255, 255, 255)


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
# AI Logic (Session 004/005)
# ---------------------------------------------------------------------------
AI_NEUTRAL_BIAS: float = 0.70


def get_tiles_adjacent_to_red(
    grid: list[list[TileState]],
) -> set[tuple[int, int]]:
    """
    Return the set of (col, row) coordinates that are orthogonally adjacent
    to at least one RED tile. Used to apply adjacency weighting in AI targeting.
    """
    adjacent: set[tuple[int, int]] = set()
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if grid[r][c] == TileState.RED:
                for dc, dr in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nc, nr = c + dc, r + dr
                    if 0 <= nc < GRID_COLS and 0 <= nr < GRID_ROWS:
                        adjacent.add((nc, nr))
    return adjacent


def _weighted_choice(
    tiles: list[tuple[int, int]],
    weights: list[float],
) -> tuple[int, int]:
    """Pick one tile using weighted random selection."""
    total = sum(weights)
    r = random.uniform(0, total)
    for tile, w in zip(tiles, weights):
        r -= w
        if r <= 0:
            return tile
    return tiles[-1]  # fallback (floating-point safety)


def ai_choose_action(
    grid: list[list[TileState]],
) -> tuple[int, int, TileState] | None:
    """
    Session 005: Decide the AI's next action WITHOUT modifying the grid.

    Returns (col, row, new_state) or None if no valid targets exist.
    Tiles adjacent to Red territory are weighted 5×; others weight 1.
    Battle resolution uses resolve_battle() — same seam as player.
    """
    adjacent_red = get_tiles_adjacent_to_red(grid)

    neutral = [
        (c, r)
        for r in range(GRID_ROWS)
        for c in range(GRID_COLS)
        if grid[r][c] == TileState.NEUTRAL
    ]
    blue = [
        (c, r)
        for r in range(GRID_ROWS)
        for c in range(GRID_COLS)
        if grid[r][c] == TileState.BLUE
    ]

    if not neutral and not blue:
        logger.info("🤖 AI has no valid targets — map fully Red")
        return None

    take_neutral = neutral and (not blue or random.random() < AI_NEUTRAL_BIAS)

    if take_neutral:
        weights = [5.0 if t in adjacent_red else 1.0 for t in neutral]
        col, row = _weighted_choice(neutral, weights)
        logger.info("🤖 AI chooses neutral ({},{}) [adj={}]", col, row, (col, row) in adjacent_red)
        return (col, row, TileState.RED)
    else:
        weights = [5.0 if t in adjacent_red else 1.0 for t in blue]
        col, row = _weighted_choice(blue, weights)
        winner = resolve_battle(attacker="RED", defender="BLUE")
        new_state = TileState.RED if winner == "RED" else TileState.BLUE
        logger.info("🤖 AI attacks Blue ({},{}) → {} wins", col, row, winner)
        return (col, row, new_state)


def ai_take_turn(
    grid: list[list[TileState]],
) -> tuple[int, int] | None:
    """
    Backward-compatible wrapper: decide + apply immediately.
    Used by tests from Sessions 001-004; Session 005 uses ai_choose_action().
    """
    result = ai_choose_action(grid)
    if result is None:
        return None
    col, row, new_state = result
    grid[row][col] = new_state
    return (col, row)


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
        self.click_count: int = 0
        self.battles_fought: int = 0
        self.last_battle_result: str = "—"
        # Session 005 turn state
        self.turn: TurnState = TurnState.PLAYER_TURN
        self.flash_tiles: set[tuple[int, int]] = set()  # player immediate flash
        self._player_acted: bool = False
        # Blink animation state (AI turn)
        self._blink_tile: tuple[int, int] | None = None
        self._blink_pre_state: TileState = TileState.NEUTRAL  # color before change
        self._blink_pending: TileState = TileState.RED        # color to apply after
        self._blink_step: int = 0      # 0=white 1=original 2=white
        self._blink_timer_ms: float = 0.0

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
        Intent-aware tile interaction. Blocked during AI blink (Session 005).

        NEUTRAL → instant Blue claim
        BLUE    → no action
        RED     → resolve_battle(); apply winner
        """
        if self.turn != TurnState.PLAYER_TURN:
            return  # input locked during AI blink sequence

        result = screen_pos_to_tile(pos[0], pos[1])
        if result is None:
            return

        col, row = result
        state = self.grid[row][col]
        self.click_count += 1

        if state == TileState.NEUTRAL:
            self.grid[row][col] = TileState.BLUE
            self.flash_tiles.add((col, row))
            self._player_acted = True
            logger.info("🏴 Tile ({},{}) claimed: NEUTRAL → BLUE", col, row)

        elif state == TileState.BLUE:
            logger.debug("🔵 Tile ({},{}) already owned by Blue — no action", col, row)

        elif state == TileState.RED:
            self.battles_fought += 1
            winner = resolve_battle(attacker="BLUE", defender="RED")
            self.grid[row][col] = TileState.BLUE if winner == "BLUE" else TileState.RED
            self.last_battle_result = f"({col},{row}) → {winner} wins"
            self.flash_tiles.add((col, row))
            self._player_acted = True

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt_ms: float = 0.0) -> None:
        """
        Session 005 turn state machine.

        PLAYER_TURN: if player acted, ask AI to choose (no grid change yet),
                     store blink state, switch to AI_BLINKING.
        AI_BLINKING: advance blink timer; on step completion advance step;
                     after BLINK_STEPS apply pending grid change, return to PLAYER.
        """
        if self.turn == TurnState.PLAYER_TURN:
            if self._player_acted:
                action = ai_choose_action(self.grid)
                if action is not None:
                    col, row, new_state = action
                    self._blink_tile = (col, row)
                    self._blink_pre_state = self.grid[row][col]  # color before change
                    self._blink_pending = new_state
                    self._blink_step = 0
                    self._blink_timer_ms = 0.0
                    self.turn = TurnState.AI_BLINKING
                    logger.info("🤖 AI blink started on ({},{})", col, row)
                self._player_acted = False

        elif self.turn == TurnState.AI_BLINKING:
            self._blink_timer_ms += dt_ms
            if self._blink_timer_ms >= BLINK_STEP_MS:
                self._blink_timer_ms -= BLINK_STEP_MS
                self._blink_step += 1
                if self._blink_step >= BLINK_STEPS:
                    # Blink complete — apply ownership change
                    col, row = self._blink_tile  # type: ignore[misc]
                    self.grid[row][col] = self._blink_pending
                    self._blink_tile = None
                    self.turn = TurnState.PLAYER_TURN
                    logger.info("🤖 AI blink resolved — turn returns to player")

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
        """
        Draw all 10×10 tiles.

        Special rendering paths (in priority order):
          1. AI blink tile: color driven by _blink_step (white/original/white)
          2. Player flash tiles: white for one frame
          3. Normal tiles: TILE_COLORS fill + TILE_HIGHLIGHT inner ring
        """
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                state = self.grid[row][col]
                x = GRID_OFFSET_X + col * TILE_SIZE
                y = GRID_OFFSET_Y + row * TILE_SIZE
                tile_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

                if self._blink_tile == (col, row):
                    # AI blink: step 0=white, step 1=pre-change color, step 2=white
                    if self._blink_step == 1:
                        blink_color = TILE_COLORS[self._blink_pre_state]
                    else:
                        blink_color = FLASH_COLOR
                    pygame.draw.rect(self.screen, blink_color, tile_rect)
                elif (col, row) in self.flash_tiles:
                    pygame.draw.rect(self.screen, FLASH_COLOR, tile_rect)
                else:
                    pygame.draw.rect(self.screen, TILE_COLORS[state], tile_rect)
                    highlight_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(self.screen, TILE_HIGHLIGHT[state], highlight_rect, 2)

                pygame.draw.rect(self.screen, BORDER_COLOR, tile_rect, BORDER_PX)

        self.flash_tiles.clear()


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
        # Turn indicator
        if self.turn == TurnState.PLAYER_TURN:
            turn_text  = "YOUR TURN"
            turn_color = TILE_HIGHLIGHT[TileState.BLUE]
        else:
            turn_text  = "RED MOVING"
            turn_color = TILE_HIGHLIGHT[TileState.RED]

        lines = [
            ("SLIME CLAN", (180, 180, 120), self.font_large),
            ("Session 005", (130, 130, 130), self.font_small),
            ("", SIDEBAR_TEXT_COLOR, self.font_small),
            (turn_text, turn_color, self.font_small),
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
                dt_ms = clock.tick(FPS)  # returns ms elapsed; drive blink timer
                self.handle_events()
                self.update(dt_ms)
                self.render()

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
