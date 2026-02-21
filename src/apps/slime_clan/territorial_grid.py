"""
Territorial Grid Prototype — Spec-001, Session 008
===================================================
A 10x10 tile-based territorial map rendered inside the rpgCore game loop.
Each tile tracks ownership: Neutral, Blue Clan, Red Clan, or Blocked.

Session 008 — Procedural Obstacle Generation:
  TileState.BLOCKED added. generate_obstacles() places 8 impassable tiles
  in the neutral zone only, never in either clan's 3×3 corner protection area.
  Blocked tiles render as dark gray + yellow X. Win threshold adjusts to
  (claimable_tiles × WIN_FRACTION) so obstacles don't inflate win cost.

Session 007 — UI Formalization: panel bg, progress bars, battle log strip.
Session 006 — Universal Blink, Win Condition & Reset.
Session 005 — Turn Clarity & AI Intent: TurnState, adjacency AI, blink.
Sessions 001–004 — Grid | Click logic | Seed | Reactive AI.

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
WINDOW_TITLE: str = "rpgCore — Slime Clan"
FPS: int = 60

# Grid layout — 10×10 tiles of 48px each = 480px fills full window height.
# 80px left sidebar + 480px grid = 560px; 80px right margin.
GRID_COLS: int = 10
GRID_ROWS: int = 10
TILE_SIZE: int = 48
GRID_OFFSET_X: int = 80
GRID_OFFSET_Y: int = 0
BORDER_PX: int = 1


# ---------------------------------------------------------------------------
# Ownership State & Turn State
# ---------------------------------------------------------------------------
class TileState(enum.IntEnum):
    NEUTRAL = 0
    BLUE    = 1
    RED     = 2
    BLOCKED = 3  # Session 008: impassable terrain


class TurnState(enum.Enum):
    PLAYER_TURN    = "player"
    PLAYER_BLINKING = "player_blinking"
    AI_BLINKING    = "ai_blinking"


# Blink sequence (shared for both player and AI moves)
BLINK_STEP_MS: int = 300
BLINK_STEPS: int = 3
FLASH_COLOR: tuple[int, int, int] = (255, 255, 255)

# Win condition (Session 006/008)
WIN_THRESHOLD: int  = 60    # baseline (no obstacles); kept for test compat
WIN_FRACTION: float = 0.60  # fraction of claimable tiles each clan needs

# Obstacle generation (Session 008)
OBSTACLE_COUNT: int = 8  # obstacles placed per game


# ---------------------------------------------------------------------------
# Win detection (pure function — Session 006)
# ---------------------------------------------------------------------------
def check_win(
    grid: list[list[TileState]],
    threshold: int | None = None,
) -> TileState | None:
    """
    Return the winning TileState if any clan holds >= threshold tiles, else None.

    If threshold is None (default), computes dynamically:
        claimable = total tiles − BLOCKED tiles
        threshold  = int(claimable × WIN_FRACTION)
    If threshold is provided explicitly, uses that value directly
    (backward-compat for tests using check_win(grid, threshold=N)).
    """
    if threshold is None:
        blocked   = sum(grid[r][c] == TileState.BLOCKED for r in range(GRID_ROWS) for c in range(GRID_COLS))
        claimable = GRID_COLS * GRID_ROWS - blocked
        threshold = max(1, int(claimable * WIN_FRACTION))
    blue = sum(grid[r][c] == TileState.BLUE for r in range(GRID_ROWS) for c in range(GRID_COLS))
    red  = sum(grid[r][c] == TileState.RED  for r in range(GRID_ROWS) for c in range(GRID_COLS))
    if blue >= threshold:
        return TileState.BLUE
    if red >= threshold:
        return TileState.RED
    return None


# Visually distinct colours for each ownership state
TILE_COLORS: dict[TileState, tuple[int, int, int]] = {
    TileState.NEUTRAL: (70,  70,  70),
    TileState.BLUE:    (30,  110, 220),
    TileState.RED:     (210, 50,  50),
    TileState.BLOCKED: (42,  40,  46),  # dead zone — darker than neutral
}

TILE_HIGHLIGHT: dict[TileState, tuple[int, int, int]] = {
    TileState.NEUTRAL: (100, 100, 100),
    TileState.BLUE:    (70,  150, 255),
    TileState.RED:     (255, 90,   90),
    TileState.BLOCKED: (60,  58,  66),  # subtle
}

# Session 008 — obstacle visual constants
BLOCKED_X_COLOR: tuple[int, int, int] = (210, 165, 20)  # amber / yellow X

BORDER_COLOR: tuple[int, int, int]     = (20,  20,  20)
BACKGROUND_COLOR: tuple[int, int, int] = (15,  15,  20)

# ---------------------------------------------------------------------------
# Session 007 — HUD visual palette
# ---------------------------------------------------------------------------
SIDEBAR_TEXT_COLOR: tuple[int, int, int] = (200, 200, 200)
PANEL_BG: tuple[int, int, int]           = (18,  18,  26)   # sidebar background
PANEL_BORDER: tuple[int, int, int]       = (55,  55,  80)   # grid separator line
LABEL_COLOR: tuple[int, int, int]        = (120, 120, 148)  # muted section labels
BAR_TRACK: tuple[int, int, int]          = (38,  38,  55)   # progress bar track
BAR_HEIGHT: int = 7                                          # progress bar px height
BATTLE_LOG_BG: tuple[int, int, int]      = (25,  18,  38)   # battle log strip bg


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
    Set the starting board configuration in-place (Session 003).
    Session 008: also calls generate_obstacles() after seeding clans.

    Blue clan: 2×2 cluster in the top-left corner     — cols 0-1, rows 0-1
    Red clan:  2×2 cluster in the bottom-right corner — cols 8-9, rows 8-9
    """
    # Blue home territory
    for row in range(2):
        for col in range(2):
            grid[row][col] = TileState.BLUE

    # Red rival territory
    for row in range(8, 10):
        for col in range(8, 10):
            grid[row][col] = TileState.RED

    # Procedural obstacles in neutral zone (Session 008)
    generate_obstacles(grid)

    logger.info(
        "🌱 Board seeded — Blue top-left 2×2, Red bottom-right 2×2, "
        "{} obstacle(s) placed",
        OBSTACLE_COUNT,
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
        # Turn / blink state (Sessions 005-006)
        self.turn: TurnState = TurnState.PLAYER_TURN
        self.winner: TileState | None = None       # set when a clan hits WIN_THRESHOLD
        self._blink_tile: tuple[int, int] | None = None
        self._blink_pre_state: TileState = TileState.NEUTRAL
        self._blink_pending: TileState = TileState.BLUE
        self._blink_step: int = 0
        self._blink_timer_ms: float = 0.0
        # Legacy flash set kept for potential future use (Session 004)
        self.flash_tiles: set[tuple[int, int]] = set()

        # Font hierarchy — Session 007 typography
        try:
            self.font_title  = pygame.font.Font(None, 22)  # SLIME CLAN header
            self.font_label  = pygame.font.Font(None, 16)  # section labels
            self.font_small  = pygame.font.Font(None, 16)  # stat values (compat alias)
            self.font_large  = pygame.font.Font(None, 22)  # banner font (compat alias)
        except Exception:
            self.font_title  = pygame.font.SysFont("monospace", 16)
            self.font_label  = pygame.font.SysFont("monospace", 13)
            self.font_small  = self.font_label
            self.font_large  = self.font_title

        logger.info(
            "🗺️  TerritorialGrid initialised — {}×{} window, {}×{} grid",
            WINDOW_WIDTH, WINDOW_HEIGHT, GRID_COLS, GRID_ROWS,
        )

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        """Process pygame events — quit, reset, and tile-click."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.winner is not None:
                        self._reset()   # game over → reset
                    else:
                        self.running = False  # in-play → quit

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        """
        Intent-aware tile interaction (Session 006: queues blink, no immediate grid write).

        Blocked if: turn != PLAYER_TURN, or game is over (winner set).
        NEUTRAL → queues BLUE claim + starts PLAYER_BLINKING
        BLUE    → no action
        RED     → resolve_battle(); queues result + starts PLAYER_BLINKING
        """
        if self.turn != TurnState.PLAYER_TURN or self.winner is not None:
            return

        result = screen_pos_to_tile(pos[0], pos[1])
        if result is None:
            return

        col, row = result
        state = self.grid[row][col]
        self.click_count += 1

        if state == TileState.NEUTRAL:
            pending = TileState.BLUE
            logger.info("🏴 Tile ({},{}) queued: NEUTRAL → BLUE", col, row)

        elif state == TileState.BLUE:
            logger.debug("🔵 Tile ({},{}) already owned by Blue — no action", col, row)
            return

        elif state == TileState.RED:
            self.battles_fought += 1
            winner = resolve_battle(attacker="BLUE", defender="RED")
            pending = TileState.BLUE if winner == "BLUE" else TileState.RED
            self.last_battle_result = f"({col},{row}) → {winner} wins"
            logger.info("⚔️ Player battles Red ({},{}) → {} wins", col, row, winner)

        else:
            return

        # Start player blink sequence
        self._blink_tile = (col, row)
        self._blink_pre_state = state
        self._blink_pending = pending
        self._blink_step = 0
        self._blink_timer_ms = 0.0
        self.turn = TurnState.PLAYER_BLINKING

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt_ms: float = 0.0) -> None:
        """
        Session 006 turn state machine (symmetric player + AI blink).

        PLAYER_TURN    : waiting for player input.
        PLAYER_BLINKING: player blink animates; on complete → apply grid change,
                         check win, then immediately trigger AI choice → AI_BLINKING.
        AI_BLINKING    : AI blink animates; on complete → apply grid change,
                         check win, return to PLAYER_TURN.
        """
        if self.winner is not None:
            return  # game frozen at winner screen

        if self.turn == TurnState.PLAYER_BLINKING:
            self._blink_timer_ms += dt_ms
            if self._blink_timer_ms >= BLINK_STEP_MS:
                self._blink_timer_ms -= BLINK_STEP_MS
                self._blink_step += 1
                if self._blink_step >= BLINK_STEPS:
                    # Player blink complete — apply change
                    col, row = self._blink_tile  # type: ignore[misc]
                    self.grid[row][col] = self._blink_pending
                    self._blink_tile = None
                    logger.info("🏴 Player blink resolved ({},{})", col, row)
                    # Check win
                    self.winner = check_win(self.grid)
                    if self.winner:
                        self.turn = TurnState.PLAYER_TURN
                        logger.info("🎉 {} wins!", self.winner.name)
                        return
                    # Trigger AI
                    action = ai_choose_action(self.grid)
                    if action is not None:
                        ac, ar, new_state = action
                        self._blink_tile = (ac, ar)
                        self._blink_pre_state = self.grid[ar][ac]
                        self._blink_pending = new_state
                        self._blink_step = 0
                        self._blink_timer_ms = 0.0
                        self.turn = TurnState.AI_BLINKING
                        logger.info("🤖 AI blink started on ({},{})", ac, ar)
                    else:
                        self.turn = TurnState.PLAYER_TURN

        elif self.turn == TurnState.AI_BLINKING:
            self._blink_timer_ms += dt_ms
            if self._blink_timer_ms >= BLINK_STEP_MS:
                self._blink_timer_ms -= BLINK_STEP_MS
                self._blink_step += 1
                if self._blink_step >= BLINK_STEPS:
                    # AI blink complete — apply change
                    col, row = self._blink_tile  # type: ignore[misc]
                    self.grid[row][col] = self._blink_pending
                    self._blink_tile = None
                    self.turn = TurnState.PLAYER_TURN
                    logger.info("🤖 AI blink resolved — turn returns to player")
                    # Check win
                    self.winner = check_win(self.grid)
                    if self.winner:
                        logger.info("🎉 {} wins!", self.winner.name)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def render(self) -> None:
        """Draw the full frame: background, grid tiles, borders, HUD, banner."""
        self.screen.fill(BACKGROUND_COLOR)
        self._draw_grid()
        self._draw_sidebar()
        if self.winner is not None:
            self._draw_winner_banner()
        pygame.display.flip()

    def _draw_winner_banner(self) -> None:
        """Render a semi-transparent winner overlay centered over the grid."""
        # Overlay background
        banner_w, banner_h = 320, 80
        banner_x = GRID_OFFSET_X + (GRID_COLS * TILE_SIZE - banner_w) // 2
        banner_y = GRID_OFFSET_Y + (GRID_ROWS * TILE_SIZE - banner_h) // 2
        overlay = pygame.Surface((banner_w, banner_h))
        overlay.set_alpha(210)
        overlay.fill((10, 10, 15))
        self.screen.blit(overlay, (banner_x, banner_y))

        # Winner text
        if self.winner == TileState.BLUE:
            text, color = "BLUE WINS!", TILE_HIGHLIGHT[TileState.BLUE]
        else:
            text, color = "RED WINS!", TILE_HIGHLIGHT[TileState.RED]

        font_banner = pygame.font.Font(None, 52)
        surf = font_banner.render(text, True, color)
        tx = banner_x + (banner_w - surf.get_width()) // 2
        ty = banner_y + 10
        self.screen.blit(surf, (tx, ty))

        # Reset prompt
        prompt = "ESC to reset"
        prompt_surf = self.font_small.render(prompt, True, (180, 180, 180))
        px = banner_x + (banner_w - prompt_surf.get_width()) // 2
        py = banner_y + banner_h - prompt_surf.get_height() - 8
        self.screen.blit(prompt_surf, (px, py))

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


    def _draw_progress_bar(
        self,
        x: int, y: int, width: int, height: int,
        count: int, total: int,
        color: tuple[int, int, int],
    ) -> None:
        """Pygame rect progress bar with a background track."""
        pygame.draw.rect(self.screen, BAR_TRACK, (x, y, width, height), border_radius=3)
        fill_w = max(2, min(int(count / total * width), width))
        pygame.draw.rect(self.screen, color,    (x, y, fill_w, height), border_radius=3)

    def _draw_sidebar(self) -> None:
        """
        Session 007 HUD panel \u2014 fully pygame-drawn.

        Layout top\u2192bottom:
          Panel bg + separator | Title | Turn pill | Progress bars | Controls | Battle log
        """
        # 1. Panel background + separator
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, GRID_OFFSET_X, WINDOW_HEIGHT))
        pygame.draw.rect(self.screen, PANEL_BORDER, (GRID_OFFSET_X - 1, 0, 1, WINDOW_HEIGHT))

        blue_count = sum(
            self.grid[r][c] == TileState.BLUE
            for r in range(GRID_ROWS) for c in range(GRID_COLS)
        )
        red_count = sum(
            self.grid[r][c] == TileState.RED
            for r in range(GRID_ROWS) for c in range(GRID_COLS)
        )
        neutral_count = GRID_COLS * GRID_ROWS - blue_count - red_count

        pad   = 7
        bar_w = GRID_OFFSET_X - pad * 2   # 66 px
        y     = 9

        def t(surf: pygame.Surface, x_off: int, y_off: int) -> None:
            self.screen.blit(surf, (x_off, y_off))

        # 2. Title block
        s = self.font_title.render("SLIME CLAN", True, (195, 190, 100))
        t(s, pad, y);  y += s.get_height() + 1
        s = self.font_label.render("Session 007", True, LABEL_COLOR)
        t(s, pad, y);  y += s.get_height() + 8

        # 3. Turn indicator pill
        if self.winner is not None:
            turn_text, turn_color = "GAME OVER", (195, 190, 100)
        elif self.turn == TurnState.PLAYER_TURN:
            turn_text, turn_color = "YOUR TURN", TILE_HIGHLIGHT[TileState.BLUE]
        else:
            turn_text, turn_color = "RED MOVING", TILE_HIGHLIGHT[TileState.RED]

        pill = pygame.Surface((bar_w, 14), pygame.SRCALPHA)
        pill.fill((42, 42, 62, 210))
        self.screen.blit(pill, (pad, y - 1))
        s = self.font_label.render(turn_text, True, turn_color)
        t(s, pad + 2, y);  y += 14 + 8

        # 4. TO WIN progress section
        s = self.font_label.render("TO WIN: 60", True, LABEL_COLOR)
        t(s, pad, y);  y += s.get_height() + 4

        s = self.font_label.render(f"B {blue_count:>2}/60", True, TILE_HIGHLIGHT[TileState.BLUE])
        t(s, pad, y);  y += s.get_height() + 2
        self._draw_progress_bar(pad, y, bar_w, BAR_HEIGHT,
                                blue_count, WIN_THRESHOLD, TILE_HIGHLIGHT[TileState.BLUE])
        y += BAR_HEIGHT + 6

        s = self.font_label.render(f"R {red_count:>2}/60", True, TILE_HIGHLIGHT[TileState.RED])
        t(s, pad, y);  y += s.get_height() + 2
        self._draw_progress_bar(pad, y, bar_w, BAR_HEIGHT,
                                red_count, WIN_THRESHOLD, TILE_HIGHLIGHT[TileState.RED])
        y += BAR_HEIGHT + 5

        s = self.font_label.render(f"N {neutral_count}", True, TILE_HIGHLIGHT[TileState.NEUTRAL])
        t(s, pad, y);  y += s.get_height() + 6

        s = self.font_label.render(f"Battles:{self.battles_fought}", True, LABEL_COLOR)
        t(s, pad, y)

        # 5. Controls (above battle log strip)
        ctrl = [
            ("CONTROLS", LABEL_COLOR),
            ("N: claim",       SIDEBAR_TEXT_COLOR),
            ("R: battle",      SIDEBAR_TEXT_COLOR),
            ("B: owned",       SIDEBAR_TEXT_COLOR),
            ("ESC: quit/rst",  SIDEBAR_TEXT_COLOR),
        ]
        BATTLE_LOG_H = 44
        line_h = 15
        ctrl_y = WINDOW_HEIGHT - BATTLE_LOG_H - 4 - len(ctrl) * line_h
        for label, color in ctrl:
            s = self.font_label.render(label, True, color)
            t(s, pad, ctrl_y);  ctrl_y += line_h

        # 6. Battle log strip (pinned at bottom)
        log_y = WINDOW_HEIGHT - BATTLE_LOG_H
        pygame.draw.rect(self.screen, BATTLE_LOG_BG, (0, log_y, GRID_OFFSET_X, BATTLE_LOG_H))
        pygame.draw.rect(self.screen, PANEL_BORDER,  (0, log_y, GRID_OFFSET_X, 1))

        s = self.font_label.render("Last:", True, LABEL_COLOR)
        t(s, pad, log_y + 4)
        result = self.last_battle_result
        # Split "coord \u2192 winner" onto two lines so it fits in 66px
        parts = result.split(" \u2192 ") if " \u2192 " in result else [result]
        s1 = self.font_label.render(parts[0], True, (220, 200, 100))
        t(s1, pad, log_y + 17)
        if len(parts) > 1:
            s2 = self.font_label.render("\u2192 " + parts[1], True, (220, 200, 100))
            t(s2, pad, log_y + 29)



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

    def _reset(self) -> None:
        """Reset board to seeded starting state. Called on ESC after game over."""
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                self.grid[r][c] = TileState.NEUTRAL
        seed_initial_state(self.grid)
        self.winner = None
        self.turn = TurnState.PLAYER_TURN
        self._blink_tile = None
        self._blink_step = 0
        self._blink_timer_ms = 0.0
        self.battles_fought = 0
        self.last_battle_result = "—"
        logger.info("🔄 Board reset to starting state")

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
