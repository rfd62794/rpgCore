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

STANCE_COLORS = {
    "PROFESSIONAL": (200, 200, 200),
    "WEARY": (150, 150, 150),
    "CURIOUS": (100, 200, 255),
    "RELUCTANT": (200, 150, 100),
    "MOVED": (255, 200, 200)
}

class AppointmentScene(Scene):
    def __init__(self, manager: SceneManager, **kwargs):
        super().__init__(manager, **kwargs)
        self.state_tracker = StateTracker()
        self.keyword_registry = KeywordRegistry()
        self.graph = ConversationGraph(self.state_tracker, self.keyword_registry)
        self.current_node = None
        self.available_edges: List[Edge] = []
        
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
                    # Store stance required/set locally if we want, but for now just as flags
                    stance = resp.get("stance", "PROFESSIONAL")
                    edge = Edge(
                        target_node=resp["leads_to"],
                        text=resp["text"]
                    )
                    # We can use the edge text and stance down in render, but Edge class
                    # doesn't natively store stance. We can patch it later or just parse here.
                    # For simplicity, let's inject stance dynamically or just let it be.
                    # Let's add a custom attribute to edge for the demo
                    edge.stance = stance
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
                
                # Handling choices 1-5
                if pygame.K_1 <= event.key <= pygame.K_5:
                    idx = event.key - pygame.K_1
                    if idx < len(self.available_edges):
                        selected = self.available_edges[idx]
                        stance = getattr(selected, "stance", "PROFESSIONAL")
                        logger.info(f"Player selected '{selected.text}' with stance {stance}")
                        
                        # Set stance
                        self.state_tracker.set_flag("current_stance", stance)
                        
                        self.current_node = self.graph.make_choice(selected)
                        if self.current_node:
                            self.available_edges = self.graph.get_available_choices()

    def update(self, dt_ms: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 18))  # Dark room: #0A0A12
        
        if not self.current_node:
            text_sur = FontManager().render_text("No conversation loaded.", "Arial", 24, (255, 0, 0))
            surface.blit(text_sur, (50, 50))
            return
            
        # Draw prompt
        prompt_sur = FontManager().render_text(self.current_node.text, "Arial", 28, (230, 230, 230))
        prompt_x = (self.manager.width - prompt_sur.get_width()) // 2
        surface.blit(prompt_sur, (prompt_x, 150))
        
        # Draw stances (for debug/flavor)
        stance = self.state_tracker.get_flag("current_stance", "NONE")
        stance_sur = FontManager().render_text(f"Stance: {stance}", "Arial", 16, (100, 100, 100))
        surface.blit(stance_sur, (20, 20))
        
        # Draw responses
        start_y = 350
        for i, edge in enumerate(self.available_edges):
            stance = getattr(edge, "stance", "PROFESSIONAL")
            color = STANCE_COLORS.get(stance, (200, 200, 200))
            
            choice_text = f"[{i+1}] {edge.text} ({stance})"
            edge_sur = FontManager().render_text(choice_text, "Arial", 20, color)
            
            surface.blit(edge_sur, (80, start_y + i * 40))
