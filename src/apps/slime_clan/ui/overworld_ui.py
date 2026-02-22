import pygame
import math
from typing import List, Dict, Any, Optional, Set
from src.apps.slime_clan.constants import *

def draw_overworld_hud(surface: pygame.Surface, font: pygame.font.Font, day: int, actions: int, actions_max: int, resources: int, ship_parts: int, roster_count: int):
    """Pure render for Overworld HUD."""
    hud_text = f"Day {day}  —  Actions: {actions}/{actions_max}"
    hud_surf = font.render(hud_text, True, (255, 255, 255))
    surface.blit(hud_surf, (20, 20))
    
    res_text = f"Resources: {resources}  |  Ship Parts: {ship_parts}/5"
    res_surf = font.render(res_text, True, (150, 200, 255))
    surface.blit(res_surf, (20, 45))

    roster_text = f"Roster: {roster_count}"
    roster_surf = font.render(roster_text, True, (200, 255, 200))
    surface.blit(roster_surf, (20, 70))

    if actions == 0:
        prompt_surf = font.render("No actions remaining — End Day to continue", True, (255, 100, 100))
        surface.blit(prompt_surf, (20, 95))

def draw_nodes_and_connections(surface: pygame.Surface, font: pygame.font.Font, colonies: list, faction_manager: Any, actions_remaining: int):
    """Pure render for Map Nodes and Connections."""
    # Connections first
    drawn_pairs = set()
    for col in colonies:
        for conn_id in col.connections:
            # Note: We need a way to look up target pos. 
            # Passing colonies as a list might be tricky if connections refer to IDs.
            # Let's pass a dict of {id: col_obj} instead.
            pass

def render_overworld_map(surface: pygame.Surface, font: pygame.font.Font, colonies_dict: Dict[str, Any], faction_manager: Any, actions_remaining: int, tribe_state: Dict[str, Any]):
    """Pure render for the entire map layer."""
    surface.fill(OVERWORLD_BG)
    
    # Connections
    drawn_pairs = set()
    for col in colonies_dict.values():
        for conn_id in col.connections:
            conn_node = colonies_dict.get(conn_id)
            if not conn_node: continue
            pair = tuple(sorted([col.id, conn_id]))
            if pair not in drawn_pairs:
                pygame.draw.line(surface, LINE_COLOR, (col.x, col.y), (conn_node.x, conn_node.y), 3)
                drawn_pairs.add(pair)

    # Nodes
    for node in colonies_dict.values():
        owner = faction_manager.get_owner(node.coord)
        color = NODE_COLORS.get(owner, (150, 150, 150))
        if node.id == "home": color = (200, 200, 200)
        
        if actions_remaining <= 0 and owner == "CLAN_BLUE" and node.id != "home":
            color = (130, 130, 130)

        pygame.draw.circle(surface, color, (node.x, node.y), NODE_RADIUS)
        
        if owner == "CLAN_YELLOW":
            pts = [(node.x, node.y - 8), (node.x + 8, node.y), (node.x, node.y + 8), (node.x - 8, node.y)]
            pygame.draw.polygon(surface, (255, 255, 255), pts)

        if owner == "CLAN_RED":
            pygame.draw.circle(surface, (255, 255, 255), (node.x, node.y), NODE_RADIUS, 2)
            
        # Labels
        label_surf = font.render(node.name, True, TEXT_COLOR)
        lx = node.x - label_surf.get_width() // 2
        ly = node.y + NODE_RADIUS + 5
        surface.blit(label_surf, (lx, ly))

        # Type/State Label (The logic for label text should probably be passed in to keep this pure)
        # But for now we'll pass the specific label text list or dict to maps.
        pass

def draw_node_labels(surface: pygame.Surface, font: pygame.font.Font, node: Any, label_text: str, label_color: tuple):
    lx = node.x - font.size(label_text)[0] // 2
    ly = node.y + NODE_RADIUS + 23
    surf = font.render(label_text, True, label_color)
    surface.blit(surf, (lx, ly))

def draw_end_day_button(surface: pygame.Surface, font: pygame.font.Font):
    btn_x, btn_y, btn_w, btn_h = WINDOW_WIDTH - 140, WINDOW_HEIGHT - 60, 120, 40
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(surface, (40, 60, 100), btn_rect)
    pygame.draw.rect(surface, (100, 150, 255), btn_rect, 2)
    btn_label = font.render("END DAY", True, (255, 255, 255))
    surface.blit(btn_label, (btn_x + (btn_w - btn_label.get_width()) // 2, btn_y + (btn_h - btn_label.get_height()) // 2))

def draw_interaction_panel(surface: pygame.Surface, font: pygame.font.Font, node_name: str, approaches: int, btns: List[tuple]):
    pw, ph = 300, 180
    px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
    pygame.draw.rect(surface, (20, 20, 30), (px, py, pw, ph))
    pygame.draw.rect(surface, (245, 197, 66), (px, py, pw, ph), 2)
    
    title = font.render(node_name, True, (245, 197, 66))
    surface.blit(title, (px + (pw - title.get_width()) // 2, py + 15))
    
    flavor = "They watch you silently."
    if approaches >= 1: flavor = "They acknowledge your presence."
    if approaches >= 3: flavor = "They are considering you. Return tomorrow."
    
    flav_surf = font.render(flavor, True, (200, 200, 200))
    surface.blit(flav_surf, (px + (pw - flav_surf.get_width()) // 2, py + 50))
    
    prog_surf = font.render(f"Approach Progress: {approaches}/3", True, (150, 150, 150))
    surface.blit(prog_surf, (px + (pw - prog_surf.get_width()) // 2, py + 75))
    
    for label, rect in btns:
        pygame.draw.rect(surface, (40, 40, 60), rect)
        pygame.draw.rect(surface, (100, 100, 150), rect, 1)
        l_surf = font.render(label, True, (255, 255, 255))
        surface.blit(l_surf, (rect[0] + (rect[2] - l_surf.get_width()) // 2, rect[1] + (rect[3] - l_surf.get_height()) // 2))

def render_defection_moment(surface: pygame.Surface, font: pygame.font.Font, unit_name: str, colony_name: str):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.fill((10, 10, 20))
    overlay.set_alpha(230)
    surface.blit(overlay, (0, 0))
    
    big_f = pygame.font.Font(None, 48)
    name_surf = big_f.render(unit_name, True, (255, 255, 255))
    surface.blit(name_surf, ((WINDOW_WIDTH - name_surf.get_width()) // 2, WINDOW_HEIGHT // 2 - 50))
    
    flavor1 = f"{unit_name} slips away from {colony_name} in the darkness."
    flavor2 = "By morning they are standing at your fire."
    
    f1_surf = font.render(flavor1, True, (200, 200, 200))
    f2_surf = font.render(flavor2, True, (200, 200, 200))
    
    surface.blit(f1_surf, ((WINDOW_WIDTH - f1_surf.get_width()) // 2, WINDOW_HEIGHT // 2 + 10))
    surface.blit(f2_surf, ((WINDOW_WIDTH - f2_surf.get_width()) // 2, WINDOW_HEIGHT // 2 + 40))

def draw_game_over_overlay(surface: pygame.Surface, font: pygame.font.Font, game_over_type: str):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    surface.blit(overlay, (0, 0))
    
    msg = ""
    if game_over_type == "WIN": msg = "🎉 Planet Secured!"
    elif game_over_type == "LOSS": msg = "💀 Colony Lost!"
    elif game_over_type == "SURVIVOR": msg = "The ship shudders to life. You don't look back."
    
    big_font = pygame.font.Font(None, 36)
    txt = big_font.render(msg, True, (255, 255, 255))
    surface.blit(txt, ((WINDOW_WIDTH - txt.get_width()) // 2, WINDOW_HEIGHT // 2 - 20))
    
    sub = font.render("Press ESC to return to title", True, (150, 150, 150))
    surface.blit(sub, ((WINDOW_WIDTH - sub.get_width()) // 2, WINDOW_HEIGHT // 2 + 30))

def draw_launch_banner(surface: pygame.Surface, font: pygame.font.Font):
    banner_w, banner_h = 500, 100
    bx = (WINDOW_WIDTH - banner_w) // 2
    by = 100
    pygame.draw.rect(surface, (20, 40, 20), (bx, by, banner_w, banner_h))
    pygame.draw.rect(surface, (100, 255, 100), (bx, by, banner_w, banner_h), 2)
    
    win_txt = font.render("SHIP REPAIRED: Survivor Ending Available", True, (150, 255, 150))
    surface.blit(win_txt, (bx + (banner_w - win_txt.get_width()) // 2, by + 20))
    
    launch_hint = font.render("Click anywhere to LAUNCH and depart", True, (200, 255, 200))
    surface.blit(launch_hint, (bx + (banner_w - launch_hint.get_width()) // 2, by + 60))
