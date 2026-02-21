"""
SlimeClanApp — Single-Window Application (Session 019A)

Replaces the multi-subprocess architecture with a SceneManager-driven
state machine. One pygame window, three scenes.

Currently migrated:
  - OverworldScene (fully functional)
  - BattleFieldScene (stub — falls back to subprocess)  
  - AutoBattleScene (stub — falls back to subprocess)
"""

import sys
import enum
import math
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any

import pygame
from loguru import logger

from src.shared.engine.scene_manager import Scene, SceneManager

# ---------------------------------------------------------------------------
# Shared Constants
# ---------------------------------------------------------------------------
WINDOW_WIDTH: int = 640
WINDOW_HEIGHT: int = 480
FPS: int = 60

# Overworld rendering constants
BACKGROUND_COLOR = (15, 15, 20)
LINE_COLOR = (80, 80, 100)
TEXT_COLOR = (200, 200, 200)
NODE_RADIUS = 25


class NodeState(enum.Enum):
    HOME = "HOME"
    BLUE = "BLUE"
    RED = "RED"
    CONTESTED = "CONTESTED"


NODE_COLORS = {
    NodeState.HOME: (50, 220, 100),
    NodeState.BLUE: (30, 110, 220),
    NodeState.RED: (210, 50, 50),
    NodeState.CONTESTED: (200, 180, 50),
}


@dataclass
class MapNode:
    id: str
    name: str
    x: int
    y: int
    state: NodeState
    connections: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# OverworldScene — Fully Migrated
# ---------------------------------------------------------------------------
class OverworldScene(Scene):
    """
    Strategic node map. Click RED/CONTESTED nodes to launch battles.
    Win condition: capture all 4 non-home nodes.
    """

    def on_enter(self, **kwargs) -> None:
        # Restore node state if returning from a battle, otherwise init fresh
        self.nodes: Dict[str, MapNode] = kwargs.get("nodes", None)
        if self.nodes is None:
            self.nodes = {
                "home": MapNode("home", "Crash Site", 100, 240, NodeState.HOME, ["node_1"]),
                "node_1": MapNode("node_1", "Scrap Yard", 250, 150, NodeState.BLUE, ["home", "node_2", "node_3"]),
                "node_2": MapNode("node_2", "Northern Wastes", 400, 100, NodeState.CONTESTED, ["node_1", "node_4"]),
                "node_3": MapNode("node_3", "Eastern Front", 400, 300, NodeState.RED, ["node_1", "node_4"]),
                "node_4": MapNode("node_4", "Deep Red Core", 550, 200, NodeState.RED, ["node_2", "node_3"]),
            }
        self.game_over = kwargs.get("game_over", None)
        self.font = pygame.font.Font(None, 24)
        logger.info("🗺️  Overworld scene entered")

    def on_exit(self) -> None:
        logger.info("🗺️  Overworld scene exited")

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.request_quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        mx, my = pos
        for node in self.nodes.values():
            dist = math.hypot(mx - node.x, my - node.y)
            if dist <= NODE_RADIUS:
                logger.info(f"📍 Clicked node: {node.name} ({node.state.value})")
                if node.state in (NodeState.RED, NodeState.CONTESTED):
                    self._launch_battle(node)
                return

    def _launch_battle(self, node: MapNode) -> None:
        """Launch battle via subprocess (preserved from Session 015 until 019B)."""
        logger.info(f"⚔️  Deploying forces to {node.name}...")
        try:
            base_cmd = [
                sys.executable,
                "-m", "src.apps.slime_clan.battle_field",
                "--region", node.name,
                "--difficulty", "NORMAL",
            ]
            result = subprocess.run(base_cmd, check=False)

            if result.returncode == 0:
                logger.info(f"🏆 Blue secured {node.name}!")
                node.state = NodeState.BLUE
            else:
                logger.info(f"💀 Red held {node.name}.")
                if node.state == NodeState.CONTESTED:
                    node.state = NodeState.RED
        except Exception as e:
            logger.error(f"❌ Battle subprocess failed: {e}")

    def update(self, dt_ms: float) -> None:
        if self.game_over:
            return

        red_count = sum(1 for n in self.nodes.values() if n.id != "home" and n.state == NodeState.RED)
        blue_count = sum(1 for n in self.nodes.values() if n.id != "home" and n.state == NodeState.BLUE)

        if blue_count >= 4:
            self.game_over = "WIN"
            logger.info("🎉 Planet Secured!")
        elif red_count >= 3:
            self.game_over = "LOSS"
            logger.info("💀 Colony Lost!")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)

        # Draw connection lines
        drawn_pairs: set = set()
        for node in self.nodes.values():
            for conn_id in node.connections:
                conn_node = self.nodes.get(conn_id)
                if not conn_node:
                    continue
                pair = tuple(sorted([node.id, conn_id]))
                if pair not in drawn_pairs:
                    pygame.draw.line(surface, LINE_COLOR, (node.x, node.y), (conn_node.x, conn_node.y), 3)
                    drawn_pairs.add(pair)

        # Draw nodes
        for node in self.nodes.values():
            color = NODE_COLORS[node.state]
            pygame.draw.circle(surface, color, (node.x, node.y), NODE_RADIUS)
            pygame.draw.circle(surface, (255, 255, 255), (node.x, node.y), NODE_RADIUS, 2)

            label_surf = self.font.render(node.name, True, TEXT_COLOR)
            lx = node.x - label_surf.get_width() // 2
            ly = node.y + NODE_RADIUS + 10
            surface.blit(label_surf, (lx, ly))

        # Game over banner
        if self.game_over:
            banner_w, banner_h = 500, 100
            bx = (WINDOW_WIDTH - banner_w) // 2
            by = (WINDOW_HEIGHT - banner_h) // 2

            overlay = pygame.Surface((banner_w, banner_h))
            overlay.set_alpha(230)
            overlay.fill((10, 10, 15))
            surface.blit(overlay, (bx, by))

            msg = ("Planet Secured - The Slime Clans bow to the Astronaut"
                   if self.game_over == "WIN"
                   else "Colony Lost - The Clans have driven you out")
            color = (100, 200, 255) if self.game_over == "WIN" else (255, 100, 100)

            surf = self.font.render(msg, True, color)
            surface.blit(surf, (bx + (banner_w - surf.get_width()) // 2, by + 25))

            esc_surf = self.font.render("ESC to Exit", True, (150, 150, 150))
            surface.blit(esc_surf, (bx + (banner_w - esc_surf.get_width()) // 2, by + 60))


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------
def create_app() -> SceneManager:
    """Create and configure the SlimeClanApp."""
    manager = SceneManager(
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        title="rpgCore — Slime Clan",
        fps=FPS,
    )
    manager.register("overworld", OverworldScene)
    return manager


if __name__ == "__main__":
    logger.info("🚀 Launching Slime Clan (Session 019A — Single Window)...")
    app = create_app()
    app.run("overworld")
