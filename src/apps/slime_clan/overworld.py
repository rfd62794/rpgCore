#!/usr/bin/env python3
"""
Session 012 — Overworld Stub
============================
A 640x480 static node map for the Slime Clan game.
Manages 5 nodes, their state (Ownership), and launches battles via subprocess.
"""

import sys
import enum
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import pygame
from loguru import logger

# ---------------------------------------------------------------------------
# Rendering Constants
# ---------------------------------------------------------------------------
WINDOW_WIDTH: int = 640
WINDOW_HEIGHT: int = 480
WINDOW_TITLE: str = "rpgCore — Slime Clan Overworld"
FPS: int = 60

BACKGROUND_COLOR: tuple[int, int, int] = (15, 15, 20)
LINE_COLOR: tuple[int, int, int] = (80, 80, 100)
TEXT_COLOR: tuple[int, int, int] = (200, 200, 200)

class NodeState(enum.Enum):
    HOME = "HOME"
    BLUE = "BLUE"
    RED = "RED"
    CONTESTED = "CONTESTED"

NODE_COLORS = {
    NodeState.HOME: (50, 220, 100),       # Distinct Green
    NodeState.BLUE: (30, 110, 220),       # Blue Clan
    NodeState.RED: (210, 50, 50),         # Red Clan
    NodeState.CONTESTED: (200, 180, 50),  # Yellow/Gold
}

NODE_RADIUS: int = 25

@dataclass
class MapNode:
    id: str
    name: str
    x: int
    y: int
    state: NodeState
    connections: List[str] = field(default_factory=list)

class Overworld:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        
        try:
            self.font = pygame.font.Font(None, 24)
        except Exception:
            self.font = pygame.font.SysFont("monospace", 16)
            
        self.running = True
        
        # Initialize nodes
        self.nodes = {
            "home": MapNode("home", "Crash Site", 100, 240, NodeState.HOME, ["node_1"]),
            "node_1": MapNode("node_1", "Scrap Yard", 250, 150, NodeState.BLUE, ["home", "node_2", "node_3"]),
            "node_2": MapNode("node_2", "Northern Wastes", 400, 100, NodeState.CONTESTED, ["node_1", "node_4"]),
            "node_3": MapNode("node_3", "Eastern Front", 400, 300, NodeState.RED, ["node_1", "node_4"]),
            "node_4": MapNode("node_4", "Deep Red Core", 550, 200, NodeState.RED, ["node_2", "node_3"])
        }
        
        logger.info("🗺️  Overworld initialized with 5 nodes")

    def handle_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        """Check if any node is clicked and launch battle if applicable."""
        mx, my = pos
        for node in self.nodes.values():
            dist = math.hypot(mx - node.x, my - node.y)
            if dist <= NODE_RADIUS:
                logger.info(f"📍 Clicked node: {node.name} ({node.state.value})")
                if node.state in (NodeState.RED, NodeState.CONTESTED):
                    self._launch_battle(node)
                return

    def _launch_battle(self, node: MapNode) -> None:
        """Launch the auto_battle scene for the node."""
        logger.info(f"⚔️  Launching battle for {node.name}...")
        
        # Subprocess launch
        try:
            # We assume we are running from the repository root
            base_cmd = [
                sys.executable, 
                "-m", "src.apps.slime_clan.auto_battle",
                "--region", node.name
            ]
            
            # Run the battle, wait for it to finish
            result = subprocess.run(base_cmd, check=False)
            
            # auto_battle.py will return 0 for Blue win, 1 for Red win/Draw/Cancel
            if result.returncode == 0:
                logger.info(f"🏆 Blue secured {node.name}!")
                node.state = NodeState.BLUE
            else:
                logger.info(f"💀 Red held {node.name}.")
                # If it was contested, it becomes red if we lose
                if node.state == NodeState.CONTESTED:
                    node.state = NodeState.RED
        except Exception as e:
            logger.error(f"❌ Battle subprocess failed: {e}")
            
    def update(self, dt_ms: float = 0.0) -> None:
        pass
        
    def render(self) -> None:
        """Draw the map: lines, nodes, and labels."""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw lines (connections)
        drawn_pairs = set()
        for node in self.nodes.values():
            for conn_id in node.connections:
                conn_node = self.nodes.get(conn_id)
                if not conn_node:
                    continue
                pair = tuple(sorted([node.id, conn_id]))
                if pair not in drawn_pairs:
                    pygame.draw.line(self.screen, LINE_COLOR, (node.x, node.y), (conn_node.x, conn_node.y), 3)
                    drawn_pairs.add(pair)
        
        # Draw nodes
        for node in self.nodes.values():
            color = NODE_COLORS[node.state]
            pygame.draw.circle(self.screen, color, (node.x, node.y), NODE_RADIUS)
            pygame.draw.circle(self.screen, (255, 255, 255), (node.x, node.y), NODE_RADIUS, 2)
            
            # Draw node label
            label_surf = self.font.render(node.name, True, TEXT_COLOR)
            lx = node.x - label_surf.get_width() // 2
            ly = node.y + NODE_RADIUS + 10
            self.screen.blit(label_surf, (lx, ly))
            
        pygame.display.flip()

    def run(self) -> None:
        """Main Pygame Loop."""
        clock = pygame.time.Clock()
        while self.running:
            dt_ms = clock.tick(FPS)
            self.handle_events()
            self.update(dt_ms)
            self.render()
        pygame.quit()

if __name__ == "__main__":
    app = Overworld()
    app.run()
