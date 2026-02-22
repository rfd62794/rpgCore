import os
import json
import pygame
from loguru import logger
from typing import List

from src.shared.engine.scene_manager import Scene, SceneManager
from src.shared.narrative.conversation_graph import ConversationGraph, Node, Edge
from src.shared.narrative.state_tracker import StateTracker
from src.shared.narrative.keyword_registry import KeywordRegistry
from src.shared.rendering.font_manager import FontManager

from src.apps.last_appointment.ui.text_window import TextWindow

STANCE_COLORS = {
    "PROFESSIONAL": (200, 200, 212), # #C8C8D4
    "WEARY": (136, 153, 170),        # #8899AA
    "CURIOUS": (136, 187, 204),      # #88BBCC
    "RELUCTANT": (204, 153, 68),     # #CC9944
    "MOVED": (170, 136, 187)         # #AA88BB
}
NUMBER_COLOR = (102, 102, 128)       # #666680

class AppointmentScene(Scene):
    def __init__(self, manager: SceneManager, **kwargs):
        super().__init__(manager, **kwargs)
        self.state_tracker = StateTracker()
        self.keyword_registry = KeywordRegistry()
        self.graph = ConversationGraph(self.state_tracker, self.keyword_registry)
        self.current_node = None
        self.available_edges: List[Edge] = []
        
        self.phase = "PROMPT" # PROMPT or NPC_RESPONSE
        self.pending_node = None
        self.npc_response_text = ""
        
        # Initialize text window
        self.text_window = TextWindow(0, 0, manager.width, slow_reveal=True, reveal_speed=40.0)
        
        # UI rendering needs FontManager
        FontManager().initialize()
        
    def _load_graph(self):
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "appointment.json")
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for beat in data.get("beats", []):
                edges = []
                for resp in beat.get("responses", []):
                    stance = resp.get("stance", "PROFESSIONAL")
                    npc_res = resp.get("npc_response", "")
                    edge = Edge(
                        target_node=resp["leads_to"],
                        text=resp["text"]
                    )
                    edge.stance = stance
                    edge.npc_response = npc_res
                    edges.append(edge)
                    
                node = Node(
                    node_id=beat["id"],
                    text=beat["prompt"],
                    edges=edges
                )
                self.graph.add_node(node)
                
            self.current_node = self.graph.start("beat_1")
            if self.current_node:
                self.available_edges = self.graph.get_available_choices()
                self.text_window.set_text(self.current_node.text)
        except Exception as e:
            logger.error(f"Failed to load appointment.json: {e}")

    def on_enter(self, **kwargs) -> None:
        logger.info("Entering AppointmentScene")
        self._load_graph()

    def on_exit(self) -> None:
        logger.info("Exiting AppointmentScene")

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.request_quit()
                
                if self.phase == "PROMPT":
                    # Handling choices 1-5
                    if pygame.K_1 <= event.key <= pygame.K_5:
                        idx = event.key - pygame.K_1
                        if idx < len(self.available_edges):
                            selected = self.available_edges[idx]
                            stance = getattr(selected, "stance", "PROFESSIONAL")
                            npc_response = getattr(selected, "npc_response", "")
                            
                            self.state_tracker.set_flag("current_stance", stance)
                            
                            self.pending_node = self.graph.make_choice(selected)
                            
                            if npc_response:
                                self.phase = "NPC_RESPONSE"
                                self.npc_response_text = npc_response
                                self.text_window.set_text(self.npc_response_text)
                            else:
                                # Advance immediately if no pending response
                                self._advance_to_pending()
                elif self.phase == "NPC_RESPONSE":
                    if self.text_window.is_finished:
                        # Advance to next prompt
                        self._advance_to_pending()
                    else:
                        # Skip reveal
                        self.text_window.skip_reveal()

    def _advance_to_pending(self):
        self.current_node = self.pending_node
        if self.current_node:
            self.available_edges = self.graph.get_available_choices()
            self.text_window.set_text(self.current_node.text)
        self.phase = "PROMPT"

    def update(self, dt_ms: float) -> None:
        self.text_window.update(dt_ms)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 18))  # Dark room: #0A0A12
        
        if not self.current_node:
            text_sur = FontManager().render_text("No conversation loaded.", "Arial", 24, (255, 0, 0))
            surface.blit(text_sur, (50, 50))
            return
            
        # Draw the main text window (prompt or npc response)
        self.text_window.render(surface)
        
        # Draw stances (bottom right corner, muted italic style)
        stance = self.state_tracker.get_flag("current_stance", "")
        if stance:
            # We mock italics if font manager doesn't natively support it by using a distinct font or just color
            # Since PyGame sysfonts can be italicized, but FontManager currently doesn't expose it,
            # we draw it minimal and muted. Let's just use Arial 16, very dark grey.
            stance_text = stance.capitalize()
            stance_sur = FontManager().render_text(stance_text, "Arial", 16, (80, 80, 95))
            sw = stance_sur.get_width()
            sh = stance_sur.get_height()
            surface.blit(stance_sur, (self.manager.width - sw - 20, self.manager.height - sh - 20))
        
        if self.phase == "PROMPT":
            # Draw responses at bottom third
            start_y = (self.manager.height // 3) * 2
            for i, edge in enumerate(self.available_edges):
                stance = getattr(edge, "stance", "PROFESSIONAL")
                color = STANCE_COLORS.get(stance, (200, 200, 200))
                
                # Render number in grey
                num_text = f"[{i+1}] "
                num_sur = FontManager().render_text(num_text, "Arial", 20, NUMBER_COLOR)
                
                # Render response in stance color
                resp_sur = FontManager().render_text(edge.text, "Arial", 20, color)
                
                # Assume mouse isn't currently tracked, so no hover highlight yet, unless we query it.
                # To query mouse for hover highlight:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                resp_rect = pygame.Rect(80, start_y + i * 40, num_sur.get_width() + resp_sur.get_width(), max(num_sur.get_height(), resp_sur.get_height()))
                
                if resp_rect.collidepoint(mouse_x, mouse_y):
                    # Brighten color
                    bright_color = tuple(min(255, int(c * 1.2)) for c in color)
                    resp_sur = FontManager().render_text(edge.text, "Arial", 20, bright_color)
                
                surface.blit(num_sur, (80, start_y + i * 40))
                surface.blit(resp_sur, (80 + num_sur.get_width(), start_y + i * 40))
        elif self.phase == "NPC_RESPONSE":
            if self.text_window.is_finished:
                cont_sur = FontManager().render_text("[Press Any Key to Continue]", "Arial", 16, (100, 100, 100))
                surface.blit(cont_sur, (80, (self.manager.height // 3) * 2))
