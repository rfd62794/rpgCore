#!/usr/bin/env python3
"""
Session 013 — Auto-Battle Scene
===============================
A 640x480 standalone auto-battler for Slime Clan squads.
3v3 deterministic battles with speed-based turn order.
"""

import sys
import enum
import math
import random
from dataclasses import dataclass
from typing import List, Optional

import pygame
from loguru import logger

# Import the procedural slime drawer from the strategic layer
try:
    from src.apps.slime_clan.territorial_grid import draw_slime, SLIME_COLORS, TileState
except ImportError:
    # Fallback for standalone/testing if path issues occur
    class TileState(enum.IntEnum):
        NEUTRAL = 0
        BLUE = 1
        RED = 2
        BLOCKED = 3
    SLIME_COLORS = {TileState.BLUE: (50, 160, 255), TileState.RED: (255, 80, 80)}
    def draw_slime(surface, cx, cy, tile_size, color):
        pygame.draw.circle(surface, color, (cx, cy), int(tile_size * 0.435))

# ---------------------------------------------------------------------------
# Enums & Data Models
# ---------------------------------------------------------------------------
class Shape(enum.Enum):
    CIRCLE = "CIRCLE"      # Balanced
    SQUARE = "SQUARE"      # +Defense, -Speed
    TRIANGLE = "TRIANGLE"  # +Speed, -Defense

class Hat(enum.Enum):
    SWORD = "SWORD"    # Attacker
    SHIELD = "SHIELD"  # Defender (Taunt)
    STAFF = "STAFF"    # Utility/Healer

@dataclass
class SlimeUnit:
    id: str
    name: str
    team: TileState
    shape: Shape
    hat: Hat
    hp: int
    max_hp: int
    attack: int
    defense: int
    speed: int
    taunt_active: bool = False

# ---------------------------------------------------------------------------
# Pure Functions: Stat Generation
# ---------------------------------------------------------------------------
def create_slime(unit_id: str, name: str, team: TileState, shape: Shape, hat: Hat, is_player: bool = False, difficulty_mult: float = 1.0) -> SlimeUnit:
    """Generate a SlimeUnit with stats modified by Shape and Hat."""
    # Base Stats
    hp = 20
    attack = 5
    defense = 2
    speed = 10

    # Shape Modifiers
    if shape == Shape.SQUARE:
        defense += 3
        speed -= 3
        hp += 5
    elif shape == Shape.TRIANGLE:
        speed += 4
        defense -= 1
        hp -= 3
    elif shape == Shape.CIRCLE:
        pass # Balanced

    # Hat Role specializations (minor stat bumps to fit role)
    if hat == Hat.SWORD:
        attack += 3
    elif hat == Hat.SHIELD:
        defense += 2
        hp += 5
    elif hat == Hat.STAFF:
        speed += 2
        attack -= 2 # Staff users hit weakly

    # Session 015 Player Bias: Elite Underdogs (+25% stats)
    if is_player:
        hp = int(hp * 1.25)
        attack = int(attack * 1.25)
        defense = int(defense * 1.25)
        speed = int(speed * 1.25)
    else:
        # Scale enemy stats based on difficulty (-20%, 0%, +20%)
        hp = max(1, int(hp * difficulty_mult))
        attack = max(1, int(attack * difficulty_mult))
        defense = max(1, int(defense * difficulty_mult))
        speed = max(1, int(speed * difficulty_mult))

    return SlimeUnit(
        id=unit_id,
        name=name,
        team=team,
        shape=shape,
        hat=hat,
        hp=hp,
        max_hp=hp,
        attack=attack,
        defense=defense,
        speed=speed
    )

# ---------------------------------------------------------------------------
# Pure Functions: Combat Logic
# ---------------------------------------------------------------------------
def execute_action(actor: SlimeUnit, allies: List[SlimeUnit], enemies: List[SlimeUnit]) -> str:
    """Execute one turn for the actor. Returns a combat log string."""
    if actor.hp <= 0:
        return f"{actor.name} is dead and cannot act."

    # Clear taunt at start of turn (if we had a duration, we'd decrement it here)
    # For now, taunt lasts until their next turn.
    actor.taunt_active = False

    if actor.hat == Hat.SWORD:
        # Attack lowest absolute HP enemy
        alive_enemies = [e for e in enemies if e.hp > 0]
        if not alive_enemies:
            return f"{actor.name} finds no enemies to attack."
            
        target = min(alive_enemies, key=lambda e: e.hp)
        damage = max(1, actor.attack - target.defense)
        target.hp = max(0, target.hp - damage)
        return f"⚔️ {actor.name} attacks {target.name} for {damage} dmg! ({target.hp}/{target.max_hp} HP)"

    elif actor.hat == Hat.SHIELD:
        # Taunt (Placeholder for Session 014 aggro logic)
        actor.taunt_active = True
        actor.defense += 2 # Temporary defense boost
        return f"🛡️ {actor.name} raises shield! (+2 Def, Taunting)"

    elif actor.hat == Hat.STAFF:
        # Heal lowest HP% ally
        alive_allies = [a for a in allies if a.hp > 0]
        if not alive_allies:
            return f"{actor.name} has no allies to heal."
            
        target = min(alive_allies, key=lambda a: a.hp / a.max_hp)
        heal_amt = max(2, actor.attack) # Use attack stat directly for heal power
        target.hp = min(target.max_hp, target.hp + heal_amt)
        return f"✨ {actor.name} heals {target.name} for {heal_amt} HP! ({target.hp}/{target.max_hp} HP)"
        
    return f"{actor.name} did nothing."

# ---------------------------------------------------------------------------
# Auto-Battler Engine (PyGame)
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
BACKGROUND_COLOR = (20, 25, 30)
TEXT_COLOR = (220, 220, 220)
FPS = 60
TICK_RATE_MS = 800

class AutoBattleScene:
    def __init__(self, region_name: str = "Unknown Region", difficulty: str = "NORMAL"):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("rpgCore — Auto-Battle")
        self.region_name = region_name
        self.difficulty = difficulty
        
        try:
            self.font_name = pygame.font.Font(None, 20)
            self.font_log = pygame.font.Font(None, 24)
            self.font_banner = pygame.font.Font(None, 52)
        except Exception:
            self.font_name = pygame.font.SysFont("monospace", 14)
            self.font_log = pygame.font.SysFont("monospace", 16)
            self.font_banner = pygame.font.SysFont("monospace", 36)

        self.running = True
        self.timer_ms = 0.0
        self.exit_code = 1 # Default to 1 (Loss/Cancel) if we exit early
        
        # Parse difficulty multiplier
        mult = 1.0
        if difficulty == "EASY": mult = 0.8
        elif difficulty == "HARD": mult = 1.2
        
        # Hard-coded Player Squad (Blue) per Session 014 Directive
        self.blue_squad = [
            create_slime("b1", "Rex", TileState.BLUE, Shape.CIRCLE, Hat.SWORD, is_player=True),
            create_slime("b2", "Brom", TileState.BLUE, Shape.SQUARE, Hat.SHIELD, is_player=True),
            create_slime("b3", "Pip", TileState.BLUE, Shape.TRIANGLE, Hat.STAFF, is_player=True),
        ]
        
        self.red_squad = [
            create_slime("r1", "R-Brute", TileState.RED, Shape.SQUARE, Hat.SWORD, difficulty_mult=mult),
            create_slime("r2", "R-Scout", TileState.RED, Shape.TRIANGLE, Hat.SWORD, difficulty_mult=mult),
            create_slime("r3", "R-Cleric", TileState.RED, Shape.CIRCLE, Hat.STAFF, difficulty_mult=mult),
        ]
        
        self.turn_queue: List[SlimeUnit] = []
        self._build_turn_queue()
        
        self.battle_logs: List[str] = [f"Battle Started in {self.region_name}!"]
        self.winner: Optional[str] = None
        
        logger.info(f"⚔️ Auto-Battle Initialized for {self.region_name}")

    def _build_turn_queue(self):
        alive = [u for u in self.blue_squad + self.red_squad if u.hp > 0]
        # Sort by speed descending
        self.turn_queue = sorted(alive, key=lambda x: x.speed, reverse=True)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self, dt_ms: float):
        if self.winner:
            return

        self.timer_ms += dt_ms
        if self.timer_ms >= TICK_RATE_MS:
            self.timer_ms -= TICK_RATE_MS
            self._process_next_turn()

    def _process_next_turn(self):
        # Filter queue to remove dead units before taking action
        self.turn_queue = [u for u in self.turn_queue if u.hp > 0]
        
        if not self.turn_queue:
            self._build_turn_queue()
            if not self.turn_queue:
                return # Everyone is dead?

        actor = self.turn_queue.pop(0)
        
        if actor.team == TileState.BLUE:
            allies = self.blue_squad
            enemies = self.red_squad
        else:
            allies = self.red_squad
            enemies = self.blue_squad
            
        log_msg = execute_action(actor, allies, enemies)
        logger.info(log_msg)
        self.battle_logs.append(log_msg)
        if len(self.battle_logs) > 5:
            self.battle_logs.pop(0)
            
        self._check_win_condition()

    def _check_win_condition(self):
        blue_alive = any(u.hp > 0 for u in self.blue_squad)
        red_alive = any(u.hp > 0 for u in self.red_squad)
        
        if blue_alive and not red_alive:
            self.winner = "BLUE WINS!"
            self.exit_code = 0
            logger.info("🏆 Blue Squad Victory")
        elif red_alive and not blue_alive:
            self.winner = "RED WINS!"
            self.exit_code = 1
            logger.info("🏆 Red Squad Victory")
        elif not blue_alive and not red_alive:
            self.winner = "DRAW!"
            self.exit_code = 1

    def _get_shape_str(self, shape: Shape) -> str:
        if shape == Shape.CIRCLE: return "C"
        if shape == Shape.SQUARE: return "S"
        if shape == Shape.TRIANGLE: return "T"
        return "?"

    def _get_hat_str(self, hat: Hat) -> str:
        if hat == Hat.SWORD: return "⚔"
        if hat == Hat.SHIELD: return "🛡"
        if hat == Hat.STAFF: return "✨"
        return "?"

    def render(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        center_y = WINDOW_HEIGHT // 2
        spacing = 80
        
        # Draw Blue Squad (Left)
        bx = WINDOW_WIDTH // 6
        for i, unit in enumerate(self.blue_squad):
            y = center_y + (i - 1) * spacing
            self._draw_unit(unit, bx, y)
            
        # Draw Red Squad (Right)
        rx = WINDOW_WIDTH - WINDOW_WIDTH // 6
        for i, unit in enumerate(self.red_squad):
            y = center_y + (i - 1) * spacing
            self._draw_unit(unit, rx, y)
            
        # Draw Battle Logs
        log_y = WINDOW_HEIGHT - 120
        for i, log_str in enumerate(self.battle_logs):
            surf = self.font_log.render(log_str, True, (180, 180, 180))
            self.screen.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, log_y + i * 20))

        # Draw Winner Banner
        if self.winner:
            banner_w, banner_h = 320, 80
            bx = (WINDOW_WIDTH - banner_w) // 2
            by = (WINDOW_HEIGHT - banner_h) // 2
            
            overlay = pygame.Surface((banner_w, banner_h))
            overlay.set_alpha(220)
            overlay.fill((10, 10, 15))
            self.screen.blit(overlay, (bx, by))
            
            color = (100, 200, 255) if "BLUE" in self.winner else (255, 100, 100)
            surf = self.font_banner.render(self.winner, True, color)
            self.screen.blit(surf, (bx + (banner_w - surf.get_width()) // 2, by + 15))
            
            esc_surf = self.font_name.render("ESC to Return", True, (150, 150, 150))
            self.screen.blit(esc_surf, (bx + (banner_w - esc_surf.get_width()) // 2, by + 60))

        pygame.display.flip()

    def _draw_unit(self, unit: SlimeUnit, x: int, y: int):
        if unit.hp <= 0:
            # Render faded gravestone or skip? For now, render faint outline
            pygame.draw.circle(self.screen, (50, 50, 50), (x, y), 20, 1)
            return

        # Name above
        name_surf = self.font_name.render(unit.name, True, TEXT_COLOR)
        self.screen.blit(name_surf, (x - name_surf.get_width() // 2, y - 35))
        
        # Slime body
        color = SLIME_COLORS[unit.team]
        draw_slime(self.screen, x, y, 48, color)
        
        # HP Bar below
        bar_w = 40
        bar_h = 6
        bx = x - bar_w // 2
        by = y + 25
        pygame.draw.rect(self.screen, (50, 50, 50), (bx, by, bar_w, bar_h))
        fill_w = max(0, int((unit.hp / unit.max_hp) * bar_w))
        hp_color = (50, 255, 50) if unit.hp > unit.max_hp * 0.3 else (255, 50, 50)
        pygame.draw.rect(self.screen, hp_color, (bx, by, fill_w, bar_h))
        
        # Indicators
        ind_str = f"[{self._get_shape_str(unit.shape)}] {self._get_hat_str(unit.hat)}"
        ind_surf = self.font_name.render(ind_str, True, (150, 150, 150))
        self.screen.blit(ind_surf, (x - ind_surf.get_width() // 2, by + 8))
        
        # Target/Taunt pulse (Optional polishing later)
        if unit.taunt_active:
            pygame.draw.circle(self.screen, (255, 200, 50), (x, y), 24, 1)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt_ms = clock.tick(FPS)
            self.handle_events()
            self.update(dt_ms)
            self.render()
        pygame.quit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="Unknown Region", help="Region name for the battle header")
    args = parser.parse_args()
    
    app = AutoBattleScene(region_name=args.region)
    app.run()
    sys.exit(app.exit_code)
