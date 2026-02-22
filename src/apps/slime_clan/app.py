"""
SlimeClanApp — Single-Window Application (Session 019B)

Zero subprocesses. Three scenes running in one pygame window.
Each scene wraps its existing logic class and delegates rendering.
"""

import sys
import enum
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import pygame
from loguru import logger

from src.shared.engine.scene_manager import Scene, SceneManager

# Import existing domain logic (unchanged)
from src.apps.slime_clan.territorial_grid import (
    draw_slime, SLIME_COLORS, TileState, generate_obstacles
)
from src.apps.slime_clan.auto_battle import (
    Shape, Hat, SlimeUnit, create_slime, execute_action
)

# Session 024: Faction System Integration
from src.shared.world.faction import FactionManager, FactionRelation
from src.apps.slime_clan.factions import get_slime_factions
from src.apps.slime_clan.colony import Colony, ColonyManager

# ---------------------------------------------------------------------------
# Shared Constants
# ---------------------------------------------------------------------------
WINDOW_WIDTH: int = 640
WINDOW_HEIGHT: int = 480
FPS: int = 60

# ===================================================================
# OVERWORLD
# ===================================================================
OVERWORLD_BG = (15, 15, 20)
LINE_COLOR = (80, 80, 100)
TEXT_COLOR = (200, 200, 200)
NODE_RADIUS = 25


class NodeState(enum.Enum):
    HOME = "HOME"
    BLUE = "BLUE"
    RED = "RED"
    CONTESTED = "CONTESTED"


class NodeType(enum.Enum):
    RESOURCE = "RESOURCE"
    RECRUITMENT = "RECRUITMENT"
    STRONGHOLD = "STRONGHOLD"
    SHIP_PARTS = "SHIP_PARTS"


NODE_TYPE_LABELS = {
    NodeType.RESOURCE: "Resource Node",
    NodeType.RECRUITMENT: "Recruitment Site",
    NodeType.STRONGHOLD: "Stronghold",
    NodeType.SHIP_PARTS: "Ship Parts Cache",
}


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
    coord: tuple[int, int] # Grid coordinate for Faction simulation
    node_type: NodeType
    connections: List[str] = field(default_factory=list)


class OverworldScene(Scene):
    """Strategic node map. Click RED/CONTESTED nodes to launch battles."""

    def on_enter(self, **kwargs) -> None:
        self.colony_manager = kwargs.get("colony_manager")
        if self.colony_manager is None:
            self.colony_manager = ColonyManager(NodeType)
            # Migrate nodes to colonies
            self.colony_manager.create_colony("home", "Crash Site", 100, 240, (0, 2), NodeType.SHIP_PARTS, ["node_1"], faction="CLAN_BLUE")
            self.colony_manager.create_colony("node_1", "Scrap Yard", 250, 150, (1, 2), NodeType.RESOURCE, ["home", "node_2", "node_3"])
            self.colony_manager.create_colony("node_2", "Northern Wastes", 400, 100, (2, 1), NodeType.STRONGHOLD, ["node_1", "ashfen", "node_4"])
            self.colony_manager.create_colony("node_3", "Eastern Front", 400, 300, (2, 3), NodeType.RECRUITMENT, ["node_1", "rootward", "node_4"])
            self.colony_manager.create_colony("node_4", "Deep Red Core", 550, 200, (3, 2), NodeType.RESOURCE, ["node_2", "node_3"])
            self.colony_manager.create_colony("ashfen", "The Ashfen Tribe", 325, 100, (1, 1), NodeType.RECRUITMENT, ["node_2"], faction="CLAN_YELLOW")
            self.colony_manager.create_colony("rootward", "The Rootward Tribe", 325, 300, (1, 3), NodeType.RECRUITMENT, ["node_3"], faction="CLAN_YELLOW")
        
        # Compatibility layer: many methods still look for self.nodes
        self.nodes = self.colony_manager 

        # Session 025/026: Day/Action & Resource State
        self.day = kwargs.get("day", 1)
        self.actions_remaining = kwargs.get("actions_remaining", 3)
        self.actions_per_day = 3
        self.resources = kwargs.get("resources", 0)
        self.ship_parts = kwargs.get("ship_parts", 0)
        self.secured_part_nodes = set(kwargs.get("secured_part_nodes", []))
        self.stronghold_bonus = kwargs.get("stronghold_bonus", False)
        self.player_units = kwargs.get("player_units", []) # Session 028 roster
        
        # Session 027: Unbound Tribal State
        self.tribe_state = kwargs.get("tribe_state", {
            "ashfen": {"approaches": 0, "dispersed": False},
            "rootward": {"approaches": 0, "dispersed": False}
        })
        self.selected_unbound_node: Optional[MapNode] = None

        # Session 024: Faction Manager Setup
        self.faction_manager = kwargs.get("faction_manager")
        if self.faction_manager is None:
            factions = get_slime_factions()
            self.faction_manager = FactionManager()
            for f in factions:
                self.faction_manager.register_faction(f)
            # Synchronize FactionManager with ColonyManager ownership
            for colony in self.colony_manager.values():
                if colony.faction:
                    self.faction_manager.claim_territory(colony.faction, colony.coord, 1.0, 0)

            # Initial setup: RED owns the core, BLUE owns the yard
            self.faction_manager.claim_territory("CLAN_RED", (3, 2), 1.0, 0) # Core
            self.faction_manager.claim_territory("CLAN_RED", (2, 3), 0.8, 0) # Eastern Front
            self.faction_manager.claim_territory("CLAN_BLUE", (1, 2), 0.8, 0) # Scrap Yard

        # Initial setup removed from here if manager exists
        # Sim params (Session 024 real-time timer removed)
        # self.sim_timer = 0.0
        # self.sim_interval = 5000.0 # 5 seconds

        # Build connection graph for FactionManager
        self.connection_graph = {}
        for node in self.nodes.values():
            self.connection_graph[node.coord] = [self.nodes[conn_id].coord for conn_id in node.connections]

        # Apply battle result from returning scenes
        battle_node_id = kwargs.get("battle_node_id")
        battle_won = kwargs.get("battle_won")
        if battle_node_id and battle_node_id in self.nodes:
            node = self.nodes[battle_node_id]
            if battle_won:
                logger.info(f"🏆 Blue secured {node.name}!")
                self.faction_manager.claim_territory("CLAN_BLUE", node.coord, 1.0, 0)
                # Session 026: Award ship parts immediately on win
                if node.node_type == NodeType.SHIP_PARTS and node.id not in self.secured_part_nodes:
                    self.ship_parts += 2
                    self.secured_part_nodes.add(node.id)
                    logger.info(f"📦 Found ship parts! (+2, total: {self.ship_parts})")
            else:
                logger.info(f"💀 Red held {node.name}.")
                self.faction_manager.claim_territory("CLAN_RED", node.coord, 1.0, 0)

        self.game_over = kwargs.get("game_over", None)
        self.font = pygame.font.Font(None, 24)
        logger.info("🗺️  Overworld scene entered")

    def on_exit(self) -> None:
        pass

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_over:
                    self.request_quit() # Back to title technically
                else:
                    self.request_quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Session 027: Interaction Panel check
                if self.selected_unbound_node:
                    if self._check_interaction_click(event.pos):
                        return
                    else:
                        self.selected_unbound_node = None # Close panel on miss

                # Session 026: Survivor Launch
                if self.ship_parts >= 5 and not self.game_over:
                    logger.info("🚀 Launching ship... Departure initiated.")
                    self.game_over = "SURVIVOR"
                    return

                # Check End Day button first
                if self._check_end_day_click(event.pos):
                    return
                self._handle_click(event.pos)

    def _check_end_day_click(self, pos: tuple[int, int]) -> bool:
        bx, by, bw, bh = WINDOW_WIDTH - 140, WINDOW_HEIGHT - 60, 120, 40
        if bx <= pos[0] <= bx + bw and by <= pos[1] <= by + bh:
            self._end_day()
            return True
        return False

    def _end_day(self) -> None:
        logger.info(f"⏳ Day {self.day} ends. Factions advance...")
        self.faction_manager.simulate_step(self.day, connection_graph=self.connection_graph)
        
        # Session 027: Tribal Encroachment & Dispersal
        for tid in ["ashfen", "rootward"]:
            if self.tribe_state[tid]["dispersed"]: continue
            node = self.nodes[tid]
            hostile_adj = 0
            total_adj = len(node.connections)
            for conn_id in node.connections:
                conn_node = self.nodes[conn_id]
                owner = self.faction_manager.get_owner(conn_node.coord)
                if owner in ["CLAN_RED", "CLAN_BLUE"]: # Hostile to tribes
                    hostile_adj += 1
            
            if hostile_adj > 0 and not self.tribe_state[tid]["dispersed"]:
                logger.warning(f"⚠️  Pressure building on {node.name}. Factions encroaching...")
            
            if hostile_adj >= total_adj:
                self.tribe_state[tid]["dispersed"] = True
                self.faction_manager.claim_territory(None, node.coord, 0.0, 0) # Tribe flees
                logger.error(f"💨 {node.name} has dispersed. They will not return.")

        # Session 026: Resource Generation
        bonus = 0
        for node in self.nodes.values():
            if self.faction_manager.get_owner(node.coord) == "CLAN_BLUE":
                if node.node_type == NodeType.RESOURCE:
                    bonus += 1
        
        if bonus > 0:
            self.resources += bonus
            logger.info(f"⚙️  Resource nodes generated +{bonus} (Total: {self.resources})")
            
        self.day += 1
        self.actions_remaining = self.actions_per_day
        logger.info(f"☀️ Day {self.day} begins!")

    def _handle_click(self, pos: tuple[int, int]) -> None:
        mx, my = pos
        for node in self.nodes.values():
            dist = math.hypot(mx - node.x, my - node.y)
            if dist <= NODE_RADIUS:
                owner = self.faction_manager.get_owner(node.coord)
                status = owner if owner else "NEUTRAL"
                logger.info(f"📍 Clicked node: {node.name} ({status})")
                
                if self.actions_remaining <= 0:
                    logger.warning("🚫 No actions remaining! Click 'End Day' to continue.")
                    return

                if owner == "CLAN_RED" or (not owner and node.id != "home"):
                    logger.info(f"⚔️  Deploying forces to {node.name}...")
                    self.actions_remaining -= 1
                    
                    # Session 026: Stronghold check
                    stronghold_bonus = (node.node_type == NodeType.STRONGHOLD)
                    if stronghold_bonus:
                        logger.info(f"🛡️  Launching from Stronghold: {node.name}! (+1 Defense Bonus)")

                    self.request_scene("battle_field",
                        region=node.name,
                        difficulty="NORMAL",
                        node_id=node.id,
                        nodes=self.nodes,
                        faction_manager=self.faction_manager,
                        day=self.day,
                        actions_remaining=self.actions_remaining,
                        resources=self.resources,
                        ship_parts=self.ship_parts,
                        secured_part_nodes=list(self.secured_part_nodes),
                        stronghold_bonus=stronghold_bonus,
                        tribe_state=self.tribe_state
                    )
                return

                if owner == "CLAN_YELLOW":
                    logger.info(f"🤝 Approaching {node.name}...")
                    if self.tribe_state.get(node.id, {}).get("dispersed", False):
                        logger.info("The campsite is empty.")
                    else:
                        self.selected_unbound_node = node
                    return

    def _check_interaction_click(self, pos: tuple[int, int]) -> bool:
        mx, my = pos
        # Panel pos: center of screen 
        pw, ph = 300, 180
        px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
        
        nid = self.selected_unbound_node.id
        approaches = self.tribe_state[nid]["approaches"]
        colony = self.colony_manager.get_colony(nid)
        
        # Determine buttons
        btns = [
            ("Observe", (px + 20, py + 110, 120, 30)),
            ("Approach", (px + 160, py + 110, 120, 30))
        ]
        if approaches >= 3:
            btns.append(("Wait", (px + 20, py + 145, 120, 30)))
            if colony and colony.units:
                btns.append(("Recruit...", (px + 160, py + 145, 120, 30)))
            
        for label, rect in btns:
            r = pygame.Rect(rect)
            if r.collidepoint(mx, my):
                if self.actions_remaining <= 0 and label not in ["Wait", "Recruit..."]:
                    logger.warning("🚫 No actions remaining for this!")
                    return True
                
                if label == "Observe":
                    self.actions_remaining -= 1
                    logger.info(f"🔭 You watch the {self.selected_unbound_node.name} from a distance. They notice.")
                elif label == "Approach":
                    self.actions_remaining -= 1
                    self.tribe_state[nid]["approaches"] += 1
                    logger.info(f"🚶 You approach unarmed. They do not flee. Progress: {self.tribe_state[nid]['approaches']}/3")
                elif label == "Wait":
                    logger.info("🧘 You wait. The silence is profound.")
                elif label == "Recruit...":
                    # Part 2: First Recruitment
                    if colony and colony.units:
                        # Pick unit with highest sympathy
                        selected_unit = max(colony.units, key=lambda u: getattr(u, "sympathy", 0))
                        colony.units.remove(selected_unit)
                        self.player_units.append(selected_unit)
                        logger.success(f"🤝 {selected_unit.name} steps forward from {colony.name}. They have chosen you.")
                    else:
                        logger.info("The tribe has no one left to send.")
                
                self.selected_unbound_node = None # Close panel
                return True
        return False

    def update(self, dt_ms: float) -> None:
        if self.game_over:
            return

        # Session 025: Real-time simulation tick removed.
        # Factions now only simulate in _end_day()

        red_count = sum(1 for n in self.nodes.values() if n.id != "home" and self.faction_manager.get_owner(n.coord) == "CLAN_RED")
        blue_count = sum(1 for n in self.nodes.values() if n.id != "home" and self.faction_manager.get_owner(n.coord) == "CLAN_BLUE")
        if blue_count >= 4:
            self.game_over = "WIN"
            logger.info("🎉 Planet Secured!")
        elif red_count >= 3:
            self.game_over = "LOSS"
            logger.info("💀 Colony Lost!")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(OVERWORLD_BG)

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

        for node in self.nodes.values():
            owner = self.faction_manager.get_owner(node.coord)
            
            # Base color selection
            color = NODE_COLORS.get(owner, (150, 150, 150))
            if node.id == "home":
                color = (200, 200, 200) # White for home

            # Actions depleted effect (Session 025/026)
            if self.actions_remaining <= 0 and owner == "CLAN_BLUE" and node.id != "home":
                color = (130, 130, 130) # Grey out player nodes

            pygame.draw.circle(surface, color, (node.x, node.y), NODE_RADIUS)
            
            # Session 027: Unbound Tribal Marker
            if owner == "CLAN_YELLOW":
                # Draw a small white diamond inside
                pts = [
                    (node.x, node.y - 8), (node.x + 8, node.y),
                    (node.x, node.y + 8), (node.x - 8, node.y)
                ]
                pygame.draw.polygon(surface, (255, 255, 255), pts)

            # Highlight (Session 024)
            if owner == "CLAN_RED":
                pygame.draw.circle(surface, (255, 255, 255), (node.x, node.y), NODE_RADIUS, 2)
            
            # Labels
            label_surf = self.font.render(node.name, True, TEXT_COLOR)
            lx = node.x - label_surf.get_width() // 2
            ly = node.y + NODE_RADIUS + 5
            surface.blit(label_surf, (lx, ly))
            
            # Node Type Label (Session 025)
            type_label = NODE_TYPE_LABELS[node.node_type]
            type_color = (120, 120, 120)
            
            # Session 026/027: Flavor Text
            if node.node_type == NodeType.RECRUITMENT and owner == "CLAN_BLUE":
                type_label = "Unbound tribe nearby"
                type_color = (100, 200, 100)
            elif owner == "CLAN_YELLOW":
                nid = node.id
                approaches = self.tribe_state.get(nid, {}).get("approaches", 0)
                if approaches >= 3:
                    type_label = "The tribe is considering you. Return tomorrow."
                    type_color = (255, 255, 150)
                else:
                    type_label = "They watch you from the treeline."
                    type_color = (200, 200, 100)

            type_surf = self.font.render(type_label, True, type_color)
            ty = ly + 18
            surface.blit(type_surf, (node.x - type_surf.get_width() // 2, ty))

        # HUD (Session 025/026)
        hud_text = f"Day {self.day}  —  Actions: {self.actions_remaining}/{self.actions_per_day}"
        hud_surf = self.font.render(hud_text, True, (255, 255, 255))
        surface.blit(hud_surf, (20, 20))
        
        res_text = f"Resources: {self.resources}  |  Ship Parts: {self.ship_parts}/5"
        res_surf = self.font.render(res_text, True, (150, 200, 255))
        surface.blit(res_surf, (20, 45))

        roster_text = f"Roster: {len(self.player_units)}"
        roster_surf = self.font.render(roster_text, True, (200, 255, 200))
        surface.blit(roster_surf, (20, 70))

        if self.actions_remaining == 0:
            prompt_surf = self.font.render("No actions remaining — End Day to continue", True, (255, 100, 100))
            surface.blit(prompt_surf, (20, 95))

        # End Day Button
        btn_x, btn_y, btn_w, btn_h = WINDOW_WIDTH - 140, WINDOW_HEIGHT - 60, 120, 40
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(surface, (40, 60, 100), btn_rect) # Blue-ish button
        pygame.draw.rect(surface, (100, 150, 255), btn_rect, 2) # Border
        btn_label = self.font.render("END DAY", True, (255, 255, 255))
        surface.blit(btn_label, (btn_x + (btn_w - btn_label.get_width()) // 2, btn_y + (btn_h - btn_label.get_height()) // 2))

        # Session 026: Survivor Ending Check
        if self.ship_parts >= 5 and not self.game_over:
            banner_w, banner_h = 500, 100
            bx = (WINDOW_WIDTH - banner_w) // 2
            by = 100
            pygame.draw.rect(surface, (20, 40, 20), (bx, by, banner_w, banner_h))
            pygame.draw.rect(surface, (100, 255, 100), (bx, by, banner_w, banner_h), 2)
            
            win_txt = self.font.render("SHIP REPAIRED: Survivor Ending Available", True, (150, 255, 150))
            surface.blit(win_txt, (bx + (banner_w - win_txt.get_width()) // 2, by + 20))
            
            launch_hint = self.font.render("Click anywhere to LAUNCH and depart", True, (200, 255, 200))
            surface.blit(launch_hint, (bx + (banner_w - launch_hint.get_width()) // 2, by + 60))

        if self.game_over:
            # Game Over / Survivor Banner (Session 026 Minimalist)
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 230))
            surface.blit(overlay, (0, 0))
            
            msg = ""
            if self.game_over == "WIN": msg = "🎉 Planet Secured!"
            elif self.game_over == "LOSS": msg = "💀 Colony Lost!"
            elif self.game_over == "SURVIVOR":
                msg = "The ship shudders to life. You don't look back."
            
            big_font = pygame.font.Font(None, 36)
            txt = big_font.render(msg, True, (255, 255, 255))
            surface.blit(txt, ((WINDOW_WIDTH - txt.get_width()) // 2, WINDOW_HEIGHT // 2 - 20))
            
            sub = self.font.render("Press ESC to return to title", True, (150, 150, 150))
            surface.blit(sub, ((WINDOW_WIDTH - sub.get_width()) // 2, WINDOW_HEIGHT // 2 + 30))

        # Session 027: Tribal Interaction Panel
        if self.selected_unbound_node:
            pw, ph = 300, 180
            px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
            pygame.draw.rect(surface, (20, 20, 30), (px, py, pw, ph))
            pygame.draw.rect(surface, (245, 197, 66), (px, py, pw, ph), 2)
            
            title = self.font.render(self.selected_unbound_node.name, True, (245, 197, 66))
            surface.blit(title, (px + (pw - title.get_width()) // 2, py + 15))
            
            nid = self.selected_unbound_node.id
            approaches = self.tribe_state[nid]["approaches"]
            
            flavor = "They watch you silently."
            if approaches >= 1: flavor = "They acknowledge your presence."
            if approaches >= 3: flavor = "They are considering you. Return tomorrow."
            
            flav_surf = self.font.render(flavor, True, (200, 200, 200))
            surface.blit(flav_surf, (px + (pw - flav_surf.get_width()) // 2, py + 50))
            
            prog_surf = self.font.render(f"Approach Progress: {approaches}/3", True, (150, 150, 150))
            surface.blit(prog_surf, (px + (pw - prog_surf.get_width()) // 2, py + 75))
            
            # Buttons
            btns = [
                ("Observe", (px + 20, py + 110, 120, 30)),
                ("Approach", (px + 160, py + 110, 120, 30))
            ]
            if approaches >= 3:
                btns.append(("Wait", (px + 20, py + 145, 120, 30)))
                # Show recruitment option if colony has units
                colony = self.colony_manager.get_colony(nid)
                if colony and colony.units:
                    btns.append(("Recruit", (px + 160, py + 145, 120, 30)))
                
            for label, rect in btns:
                pygame.draw.rect(surface, (40, 40, 60), rect)
                pygame.draw.rect(surface, (100, 100, 150), rect, 1)
                l_surf = self.font.render(label, True, (255, 255, 255))
                surface.blit(l_surf, (rect[0] + (rect[2] - l_surf.get_width()) // 2, rect[1] + (rect[3] - l_surf.get_height()) // 2))


# ===================================================================
# BATTLE FIELD
# ===================================================================
BF_GRID_COLS = 10
BF_GRID_ROWS = 10
BF_TILE_SIZE = 48
BF_GRID_OFFSET_X = 80
BF_GRID_OFFSET_Y = 0
BF_BG = (15, 15, 20)
BF_BORDER_COLOR = (20, 20, 20)
BF_TILE_NEUTRAL = (70, 70, 70)
BF_TILE_BLOCKED = (42, 40, 46)
BF_TILE_HIGHLIGHT = (100, 100, 100)
BF_BLOCKED_X = (210, 165, 20)
BF_SIDEBAR_TEXT = (200, 200, 200)


@dataclass
class SquadToken:
    col: int
    row: int
    team: TileState
    active: bool = True


class BattleFieldScene(Scene):
    """Operational grid — move Blue token, collide with Red to trigger auto-battle."""

    def on_enter(self, **kwargs) -> None:
        self.region_name = kwargs.get("region", "Test Grid")
        self.difficulty = kwargs.get("difficulty", "NORMAL")
        self.node_id = kwargs.get("node_id", "")
        self.nodes = kwargs.get("nodes", {})  # Overworld nodes to pass back
        self.faction_manager = kwargs.get("faction_manager")
        self.day = kwargs.get("day", 1)
        self.actions_remaining = kwargs.get("actions_remaining", 3)
        self.resources = kwargs.get("resources", 0)
        self.ship_parts = kwargs.get("ship_parts", 0)
        self.secured_part_nodes = kwargs.get("secured_part_nodes", [])
        self.tribe_state = kwargs.get("tribe_state", {})
        self.stronghold_bonus = kwargs.get("stronghold_bonus", False)
        self.game_over = False
        self.exit_code = 1

        self.font_ui = pygame.font.Font(None, 24)
        self.font_token = pygame.font.Font(None, 28)
        self.font_banner = pygame.font.Font(None, 52)

        # Grid
        self.grid = [[TileState.NEUTRAL for _ in range(BF_GRID_COLS)] for _ in range(BF_GRID_ROWS)]
        generate_obstacles(self.grid)

        # Tokens
        self.blue_token = SquadToken(0, 0, TileState.BLUE)
        self.red_token = SquadToken(BF_GRID_COLS - 1, BF_GRID_ROWS - 1, TileState.RED)

        # Auto-battle result pending from returning AutoBattleScene
        auto_battle_result = kwargs.get("auto_battle_result")
        if auto_battle_result is not None:
            if auto_battle_result == "blue_win":
                logger.info("🏆 Blue squad won the tactical skirmish! Red token eliminated.")
                self.red_token.active = False
                logger.info("🎉 Field Secured! Returning to Overworld.")
                self.exit_code = 0
                self.game_over = True
            else:
                logger.info("💀 Red squad repelled the attack! Blue token eliminated.")
                self.blue_token.active = False
                self.exit_code = 1
                self.game_over = True

        logger.info(f"🗺️  BattleField scene entered for {self.region_name} ({self.difficulty})")

    def on_exit(self) -> None:
        pass

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Return to overworld with loss
                    self._return_to_overworld(won=self.exit_code == 0)
                elif not self.game_over and self.blue_token.active:
                    self._handle_player_move(event.key)

    def _handle_player_move(self, key) -> None:
        dc, dr = 0, 0
        if key == pygame.K_UP: dr = -1
        elif key == pygame.K_DOWN: dr = 1
        elif key == pygame.K_LEFT: dc = -1
        elif key == pygame.K_RIGHT: dc = 1
        else:
            return

        new_c = self.blue_token.col + dc
        new_r = self.blue_token.row + dr
        if not (0 <= new_c < BF_GRID_COLS and 0 <= new_r < BF_GRID_ROWS):
            return
        if self.grid[new_r][new_c] == TileState.BLOCKED:
            return

        self.blue_token.col, self.blue_token.row = new_c, new_r

        if self._check_collision():
            return

        self._take_red_turn()
        self._check_collision()

    def _take_red_turn(self) -> None:
        if not self.red_token.active:
            return
        target_c, target_r = self.blue_token.col, self.blue_token.row
        best_dist = float('inf')
        best_step = (self.red_token.col, self.red_token.row)
        for dc, dr in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nc, nr = self.red_token.col + dc, self.red_token.row + dr
            if 0 <= nc < BF_GRID_COLS and 0 <= nr < BF_GRID_ROWS:
                if self.grid[nr][nc] != TileState.BLOCKED:
                    dist = abs(nc - target_c) + abs(nr - target_r)
                    if dist < best_dist:
                        best_dist = dist
                        best_step = (nc, nr)
        self.red_token.col, self.red_token.row = best_step

    def _check_collision(self) -> bool:
        if not self.red_token.active or not self.blue_token.active:
            return False
        dist = abs(self.blue_token.col - self.red_token.col) + abs(self.blue_token.row - self.red_token.row)
        if dist <= 1:
            logger.info("⚔️ SQUAD COLLISION DETECTED! Launching tactical auto-battle...")
            self._launch_auto_battle()
            return True
        return False

    def _launch_auto_battle(self) -> None:
        """Transition to AutoBattleScene (zero subprocess)."""
        self.request_scene("auto_battle",
            region=f"{self.region_name}_Skirmish",
            difficulty=self.difficulty,
            # Pass context for the return trip
            bf_region=self.region_name,
            bf_difficulty=self.difficulty,
            bf_node_id=self.node_id,
            faction_manager=self.faction_manager,
            day=self.day,
            actions_remaining=self.actions_remaining,
            resources=self.resources,
            ship_parts=self.ship_parts,
            secured_part_nodes=self.secured_part_nodes,
            tribe_state=self.tribe_state,
            stronghold_bonus=self.stronghold_bonus # Pass stronghold_bonus
        )

    def _return_to_overworld(self, won: bool) -> None:
        self.request_scene("overworld",
            nodes=self.nodes,
            battle_node_id=self.node_id,
            battle_won=won,
            faction_manager=self.faction_manager,
            day=self.day,
            actions_remaining=self.actions_remaining,
            resources=self.resources,
            ship_parts=self.ship_parts,
            secured_part_nodes=self.secured_part_nodes,
            tribe_state=self.tribe_state,
            stronghold_bonus=self.stronghold_bonus # Pass stronghold_bonus
        )

    def update(self, dt_ms: float) -> None:
        if self.game_over:
            return
        # Win condition: Blue reaches Red base corner
        if (self.blue_token.active
            and self.blue_token.col >= BF_GRID_COLS - 2
            and self.blue_token.row >= BF_GRID_ROWS - 2):
            logger.info("🎉 BLUE REACHED ENEMY BASE! Field Secured!")
            self.exit_code = 0
            self.game_over = True

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(BF_BG)

        # Sidebar
        panel_rect = pygame.Rect(0, 0, BF_GRID_OFFSET_X, WINDOW_HEIGHT)
        pygame.draw.rect(surface, (18, 18, 26), panel_rect)
        pygame.draw.rect(surface, (55, 55, 80), panel_rect, 1)
        title = self.font_ui.render("REGION", True, (120, 120, 148))
        surface.blit(title, (5, 20))
        region_label = self.font_ui.render(self.region_name[:10], True, BF_SIDEBAR_TEXT)
        surface.blit(region_label, (5, 40))

        # Grid
        for row in range(BF_GRID_ROWS):
            for col in range(BF_GRID_COLS):
                state = self.grid[row][col]
                x = BF_GRID_OFFSET_X + col * BF_TILE_SIZE
                y = BF_GRID_OFFSET_Y + row * BF_TILE_SIZE
                tile_rect = pygame.Rect(x, y, BF_TILE_SIZE, BF_TILE_SIZE)
                if state == TileState.BLOCKED:
                    pygame.draw.rect(surface, BF_TILE_BLOCKED, tile_rect)
                    m = 10
                    pygame.draw.line(surface, BF_BLOCKED_X, (x + m, y + m), (x + BF_TILE_SIZE - m, y + BF_TILE_SIZE - m), 2)
                    pygame.draw.line(surface, BF_BLOCKED_X, (x + BF_TILE_SIZE - m, y + m), (x + m, y + BF_TILE_SIZE - m), 2)
                else:
                    pygame.draw.rect(surface, BF_TILE_NEUTRAL, tile_rect)
                    hl = pygame.Rect(x + 2, y + 2, BF_TILE_SIZE - 4, BF_TILE_SIZE - 4)
                    pygame.draw.rect(surface, BF_TILE_HIGHLIGHT, hl, 2)
                pygame.draw.rect(surface, BF_BORDER_COLOR, tile_rect, 1)

        # Blue token
        if self.blue_token.active:
            x = BF_GRID_OFFSET_X + self.blue_token.col * BF_TILE_SIZE
            y = BF_GRID_OFFSET_Y + self.blue_token.row * BF_TILE_SIZE
            cx, cy = x + BF_TILE_SIZE // 2, y + BF_TILE_SIZE // 2
            draw_slime(surface, cx, cy, BF_TILE_SIZE, SLIME_COLORS[TileState.BLUE])
            lbl = self.font_token.render("3", True, (255, 255, 255))
            surface.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2 - 2))

        # Red token
        if self.red_token.active:
            x = BF_GRID_OFFSET_X + self.red_token.col * BF_TILE_SIZE
            y = BF_GRID_OFFSET_Y + self.red_token.row * BF_TILE_SIZE
            cx, cy = x + BF_TILE_SIZE // 2, y + BF_TILE_SIZE // 2
            draw_slime(surface, cx, cy, BF_TILE_SIZE, SLIME_COLORS[TileState.RED])
            lbl = self.font_token.render("3", True, (255, 255, 255))
            surface.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2 - 2))

        # Win/Loss banner
        if self.game_over:
            banner_w, banner_h = 320, 80
            bx = BF_GRID_OFFSET_X + (BF_GRID_COLS * BF_TILE_SIZE - banner_w) // 2
            by = BF_GRID_OFFSET_Y + (BF_GRID_ROWS * BF_TILE_SIZE - banner_h) // 2
            overlay = pygame.Surface((banner_w, banner_h))
            overlay.set_alpha(220)
            overlay.fill((10, 10, 15))
            surface.blit(overlay, (bx, by))
            color = (100, 200, 255) if self.exit_code == 0 else (255, 100, 100)
            msg = "FIELD SECURED!" if self.exit_code == 0 else "SQUAD WIPED!"
            surf = self.font_banner.render(msg, True, color)
            surface.blit(surf, (bx + (banner_w - surf.get_width()) // 2, by + 10))
            esc = self.font_ui.render("ESC to Return", True, (150, 150, 150))
            surface.blit(esc, (bx + (banner_w - esc.get_width()) // 2, by + 55))


# ===================================================================
# AUTO BATTLE
# ===================================================================
AB_BG = (20, 25, 30)
AB_TEXT = (220, 220, 220)
TICK_RATE_MS = 800


class AutoBattleScene(Scene):
    """3v3 auto-battler. Returns win/loss via scene transition."""

    def on_enter(self, **kwargs) -> None:
        self.region_name = kwargs.get("region", "Unknown Region")
        self.difficulty = kwargs.get("difficulty", "NORMAL")

        # Context for return trip to BattleFieldScene
        self.bf_region = kwargs.get("bf_region", "")
        self.bf_difficulty = kwargs.get("bf_difficulty", "NORMAL")
        self.bf_node_id = kwargs.get("bf_node_id", "")
        self.bf_nodes = kwargs.get("bf_nodes", {})
        self.faction_manager = kwargs.get("faction_manager")
        self.day = kwargs.get("day", 1)
        self.actions_remaining = kwargs.get("actions_remaining", 3)
        self.resources = kwargs.get("resources", 0)
        self.ship_parts = kwargs.get("ship_parts", 0)
        self.secured_part_nodes = kwargs.get("secured_part_nodes", [])
        self.tribe_state = kwargs.get("tribe_state", {})
        self.stronghold_bonus = kwargs.get("stronghold_bonus", False)

        self.turn_count = 0
        self.timer_ms = 0.0
        self.winner: Optional[str] = None
        self.win_close_timer = 0.0

        self.font_name = pygame.font.Font(None, 20)
        self.font_log = pygame.font.Font(None, 24)
        self.font_banner = pygame.font.Font(None, 52)

        # Difficulty multiplier
        mult = 1.0
        if self.difficulty == "EASY": mult = 0.8
        elif self.difficulty == "HARD": mult = 1.2

        self.blue_squad = [
            self._create_buffed_slime("b1", "Rex", Shape.CIRCLE, Hat.SWORD),
            self._create_buffed_slime("b2", "Brom", Shape.SQUARE, Hat.SHIELD),
            self._create_buffed_slime("b3", "Pip", Shape.TRIANGLE, Hat.STAFF),
        ]
        self.red_squad = [
            create_slime("r1", "R-Brute", TileState.RED, Shape.SQUARE, Hat.SWORD, difficulty_mult=mult),
            create_slime("r2", "R-Scout", TileState.RED, Shape.TRIANGLE, Hat.SWORD, difficulty_mult=mult),
            create_slime("r3", "R-Cleric", TileState.RED, Shape.CIRCLE, Hat.STAFF, difficulty_mult=mult),
        ]

        self.turn_queue: List[SlimeUnit] = []
        self._build_turn_queue()
        self.battle_logs: List[str] = [f"Battle Started in {self.region_name}!"]

        logger.info(f"⚔️ Auto-Battle scene entered for {self.region_name}")

    def on_exit(self) -> None:
        pass

    def _build_turn_queue(self) -> None:
        alive = [u for u in self.blue_squad + self.red_squad if u.hp > 0]
        self.turn_queue = sorted(alive, key=lambda x: x.speed, reverse=True)
        self.turn_count += 1

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ESC during battle = loss, return to battle field
                self._return_result("red_win")

    def update(self, dt_ms: float) -> None:
        if self.winner:
            self.win_close_timer += dt_ms
            if self.win_close_timer >= 2000:
                result = "blue_win" if "BLUE" in self.winner else "red_win"
                self._return_result(result)
            return

        self.timer_ms += dt_ms
        if self.timer_ms >= TICK_RATE_MS:
            self.timer_ms -= TICK_RATE_MS
            self._process_next_turn()

    def _process_next_turn(self) -> None:
        self.turn_queue = [u for u in self.turn_queue if u.hp > 0]
        if not self.turn_queue:
            self._build_turn_queue()
            if not self.turn_queue:
                return

        actor = self.turn_queue.pop(0)
        if actor.team == TileState.BLUE:
            allies, enemies = self.blue_squad, self.red_squad
        else:
            allies, enemies = self.red_squad, self.blue_squad

        log_msg = execute_action(actor, allies, enemies)
        logger.info(log_msg)
        self.battle_logs.append(log_msg)
        if len(self.battle_logs) > 5:
            self.battle_logs.pop(0)
        self._check_win_condition()

    def _check_win_condition(self) -> None:
        blue_alive = any(u.hp > 0 for u in self.blue_squad)
        red_alive = any(u.hp > 0 for u in self.red_squad)

        if blue_alive and not red_alive:
            self.winner = "BLUE WINS!"
            logger.info("🏆 Blue Squad Victory")
        elif red_alive and not blue_alive:
            self.winner = "RED WINS!"
            logger.info("🏆 Red Squad Victory")
        elif not blue_alive and not red_alive:
            self.winner = "DRAW!"
        elif self.turn_count >= 50:
            b_pct = sum(u.hp for u in self.blue_squad) / sum(u.max_hp for u in self.blue_squad)
            r_pct = sum(u.hp for u in self.red_squad) / sum(u.max_hp for u in self.red_squad)
            if b_pct > r_pct:
                self.winner = "BLUE WINS (TIMEOUT)!"
                logger.info(f"⌛ Turn Limit. Blue wins: {b_pct:.0%} vs {r_pct:.0%}")
            else:
                self.winner = "RED WINS (TIMEOUT)!"
                logger.info(f"⌛ Turn Limit. Red wins: {r_pct:.0%} vs {b_pct:.0%}")

    def _create_buffed_slime(self, id: str, name: str, shape: Shape, hat: Hat) -> SlimeUnit:
        unit = create_slime(id, name, TileState.BLUE, shape, hat, is_player=True)
        if self.stronghold_bonus:
            unit.defense += 1 # Tacit bonus from stronghold
        return unit

    def _return_result(self, result: str) -> None:
        """Transition back to BattleFieldScene with the result."""
        self.request_scene("battle_field",
            region=self.bf_region,
            difficulty=self.bf_difficulty,
            node_id=self.bf_node_id,
            nodes=self.bf_nodes,
            auto_battle_result=result,
            faction_manager=self.faction_manager,
            day=self.day,
            actions_remaining=self.actions_remaining,
            resources=self.resources,
            ship_parts=self.ship_parts,
            secured_part_nodes=self.secured_part_nodes,
            tribe_state=self.tribe_state,
            stronghold_bonus=self.stronghold_bonus
        )

    def _get_shape_str(self, shape: Shape) -> str:
        return {"CIRCLE": "C", "SQUARE": "S", "TRIANGLE": "T"}.get(shape.value, "?")

    def _get_hat_str(self, hat: Hat) -> str:
        return {"SWORD": "⚔", "SHIELD": "🛡", "STAFF": "✨"}.get(hat.value, "?")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(AB_BG)
        center_y = WINDOW_HEIGHT // 2
        spacing = 80

        # Blue squad (left)
        bx = WINDOW_WIDTH // 6
        for i, unit in enumerate(self.blue_squad):
            self._draw_unit(surface, unit, bx, center_y + (i - 1) * spacing)

        # Red squad (right)
        rx = WINDOW_WIDTH - WINDOW_WIDTH // 6
        for i, unit in enumerate(self.red_squad):
            self._draw_unit(surface, unit, rx, center_y + (i - 1) * spacing)

        # Battle logs
        log_y = WINDOW_HEIGHT - 120
        for i, log_str in enumerate(self.battle_logs):
            surf = self.font_log.render(log_str, True, (180, 180, 180))
            surface.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, log_y + i * 20))

        # Winner banner
        if self.winner:
            banner_w, banner_h = 320, 80
            bx = (WINDOW_WIDTH - banner_w) // 2
            by = (WINDOW_HEIGHT - banner_h) // 2
            overlay = pygame.Surface((banner_w, banner_h))
            overlay.set_alpha(220)
            overlay.fill((10, 10, 15))
            surface.blit(overlay, (bx, by))
            color = (100, 200, 255) if "BLUE" in self.winner else (255, 100, 100)
            surf = self.font_banner.render(self.winner, True, color)
            surface.blit(surf, (bx + (banner_w - surf.get_width()) // 2, by + 15))
            wait_surf = self.font_name.render("Returning...", True, (150, 150, 150))
            surface.blit(wait_surf, (bx + (banner_w - wait_surf.get_width()) // 2, by + 60))

    def _draw_unit(self, surface: pygame.Surface, unit: SlimeUnit, x: int, y: int) -> None:
        if unit.hp <= 0:
            pygame.draw.circle(surface, (50, 50, 50), (x, y), 20, 1)
            return

        name_surf = self.font_name.render(unit.name, True, AB_TEXT)
        surface.blit(name_surf, (x - name_surf.get_width() // 2, y - 35))

        draw_slime(surface, x, y, 48, SLIME_COLORS[unit.team])

        # HP bar
        bar_w, bar_h = 40, 6
        bx, by = x - bar_w // 2, y + 25
        pygame.draw.rect(surface, (50, 50, 50), (bx, by, bar_w, bar_h))
        fill_w = max(0, int((unit.hp / unit.max_hp) * bar_w))
        hp_color = (50, 255, 50) if unit.hp > unit.max_hp * 0.3 else (255, 50, 50)
        pygame.draw.rect(surface, hp_color, (bx, by, fill_w, bar_h))

        ind_str = f"[{self._get_shape_str(unit.shape)}] {self._get_hat_str(unit.hat)}"
        ind_surf = self.font_name.render(ind_str, True, (150, 150, 150))
        surface.blit(ind_surf, (x - ind_surf.get_width() // 2, by + 8))

        if unit.taunt_active:
            pygame.draw.circle(surface, (255, 200, 50), (x, y), 24, 1)


# ===================================================================
# Application Entry Point
# ===================================================================
def create_app() -> SceneManager:
    """Create and configure the SlimeClanApp with all three scenes."""
    manager = SceneManager(
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        title="rpgCore — Slime Clan",
        fps=FPS,
    )
    manager.register("overworld", OverworldScene)
    manager.register("battle_field", BattleFieldScene)
    manager.register("auto_battle", AutoBattleScene)
    return manager


if __name__ == "__main__":
    logger.info("🚀 Launching Slime Clan (Session 019B — Zero Subprocesses)...")
    app = create_app()
    app.run("overworld")
