import pygame
import random
from typing import Optional, List
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.base import UIComponent
from src.apps.slime_breeder.garden.garden_state import GardenState
from src.apps.slime_breeder.entities.slime import Slime
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.genetics import generate_random, breed

NAMES = ["Mochi", "Pip", "Glimmer", "Bloop", "Sage", "Dew", "Ember", "Fizz", "Lumen", "Nook"]

class GardenScene(Scene):
    def on_enter(self, **kwargs) -> None:
        self.garden_state = GardenState()
        self.renderer = SlimeRenderer()
        
        # UI Components list (mimicking SceneBase logic)
        self.ui_components: List[UIComponent] = []
        
        # UI Layout Constants
        # Assume 1024x768 based on run_slime_breeder.py
        self.width, self.height = 1024, 768
        self.panel_width = 240
        self.bottom_bar_height = 80
        
        self.garden_rect = pygame.Rect(0, 0, self.width - self.panel_width, self.height - self.bottom_bar_height)
        
        # Setup UI
        self._setup_ui()
        
        # Add first slime
        self._add_new_slime()

    def on_exit(self) -> None:
        pass

    def _setup_ui(self):
        # Right Panel (Details)
        detail_rect = pygame.Rect(self.width - self.panel_width, 0, self.panel_width, self.height - self.bottom_bar_height)
        self.detail_panel = Panel(detail_rect, title="Slime Details", bg_color=(40, 60, 40))
        self.ui_components.append(self.detail_panel)
        
        # Detail Labels
        self.name_label = Label(pygame.Rect(10, 40, self.panel_width-20, 30), text="Name: ---")
        self.detail_panel.add_child(self.name_label)
        
        self.mood_label = Label(pygame.Rect(10, 70, self.panel_width-20, 30), text="Mood: ---")
        self.detail_panel.add_child(self.mood_label)
        
        # Bottom Bar (Actions)
        bar_rect = pygame.Rect(0, self.height - self.bottom_bar_height, self.width, self.bottom_bar_height)
        self.action_bar = Panel(bar_rect, bg_color=(30, 40, 30))
        self.ui_components.append(self.action_bar)
        
        btn_y = 15
        btn_w, btn_h = 120, 50
        
        self.new_btn = Button(pygame.Rect(20, btn_y, btn_w, btn_h), text="New Slime", on_click=self._add_new_slime)
        self.action_bar.add_child(self.new_btn)
        
        self.breed_btn = Button(pygame.Rect(150, btn_y, btn_w, btn_h), text="Breed", on_click=self._breed_selected)
        self.breed_btn.set_enabled(False)
        self.action_bar.add_child(self.breed_btn)

    def _add_new_slime(self):
        name = random.choice(NAMES) + " " + str(len(self.garden_state.slimes) + 1)
        genome = generate_random()
        pos = (random.randint(50, self.garden_rect.width - 50), random.randint(50, self.garden_rect.height - 50))
        slime = Slime(name, genome, pos)
        self.garden_state.add_slime(slime)

    def _breed_selected(self):
        pass

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            
            # 1. UI components handle event first
            consumed = False
            for comp in reversed(self.ui_components):
                if hasattr(comp, 'handle_event') and comp.handle_event(event):
                    consumed = True
                    break
            
            if consumed:
                continue

            # 2. Handle garden clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.garden_rect.collidepoint(event.pos):
                    found = None
                    for slime in reversed(self.garden_state.slimes):
                        dist = (slime.kinematics.position - pygame.Vector2(*event.pos)).magnitude()
                        if dist < 40:
                           found = slime
                           break
                    
                    self.garden_state.selected = found

    def update(self, dt_ms: float) -> None:
        dt = dt_ms / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        self.garden_state.update(dt, mouse_pos if self.garden_rect.collidepoint(mouse_pos) else None)
        
        for comp in self.ui_components:
            comp.update(int(dt_ms))
        
        self._update_details()

    def _update_details(self):
        s = self.garden_state.selected
        if s:
            self.name_label.text = f"Name: {s.name}"
            self.mood_label.text = f"Mood: {s.get_mood()}"
        else:
            self.name_label.text = "Name: ---"
            self.mood_label.text = "Mood: ---"

    def render(self, surface: pygame.Surface) -> None:
        # 1. Background (Soft garden green)
        surface.fill((20, 30, 20))
        
        # 2. Render Slimes
        for slime in self.garden_state.slimes:
            is_selected = (slime == self.garden_state.selected)
            self.renderer.render(surface, slime, is_selected)
            
        # 3. Render UI components
        for comp in self.ui_components:
            comp.render(surface)
