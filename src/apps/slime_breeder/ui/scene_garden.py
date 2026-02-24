import pygame
import random
from typing import Optional, List
from src.shared.ui.scene_base import SceneBase
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.apps.slime_breeder.garden.garden_state import GardenState
from src.apps.slime_breeder.entities.slime import Slime
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.genetics import generate_random, breed

NAMES = ["Mochi", "Pip", "Glimmer", "Bloop", "Sage", "Dew", "Ember", "Fizz", "Lumen", "Nook"]

class GardenScene(SceneBase):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        self.garden_state = GardenState()
        self.renderer = SlimeRenderer()
        
        # UI Layout Constants
        self.width, self.height = surface.get_size()
        self.panel_width = 240
        self.bottom_bar_height = 80
        
        self.garden_rect = pygame.Rect(0, 0, self.width - self.panel_width, self.height - self.bottom_bar_height)
        
        # Setup UI
        self._setup_ui()
        
        # Add first slime
        self._add_new_slime()

    def _setup_ui(self):
        # Right Panel (Details)
        detail_rect = pygame.Rect(self.width - self.panel_width, 0, self.panel_width, self.height - self.bottom_bar_height)
        self.detail_panel = Panel(detail_rect, title="Slime Details", bg_color=(40, 60, 40))
        self.add_component(self.detail_panel)
        
        # Detail Labels
        self.name_label = Label(pygame.Rect(10, 40, self.panel_width-20, 30), text="Name: ---")
        self.detail_panel.add_child(self.name_label)
        
        self.mood_label = Label(pygame.Rect(10, 70, self.panel_width-20, 30), text="Mood: ---")
        self.detail_panel.add_child(self.mood_label)
        
        # Bottom Bar (Actions)
        bar_rect = pygame.Rect(0, self.height - self.bottom_bar_height, self.width, self.bottom_bar_height)
        self.action_bar = Panel(bar_rect, bg_color=(30, 40, 30))
        self.add_component(self.action_bar)
        
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
        # Logic for breeding (requires 2 selected, but currently we only track 1 selection in simpler POC)
        # For now, if we have a selection and at least one other slime, breed with random? 
        # Or let's implement multi-selection.
        pass

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check for slime selection in garden
            if self.garden_rect.collidepoint(event.pos):
                found = None
                for slime in reversed(self.garden_state.slimes):
                    dist = (slime.kinematics.position - pygame.Vector2(*event.pos)).magnitude()
                    if dist < 40: # Approximation based on max radius
                       found = slime
                       break
                
                self.garden_state.selected = found
                self._update_details()
                return True
        return False

    def _update_details(self):
        s = self.garden_state.selected
        if s:
            self.name_label.text = f"Name: {s.name}"
            self.mood_label.text = f"Mood: {s.get_mood()}"
        else:
            self.name_label.text = "Name: ---"
            self.mood_label.text = "Mood: ---"

    def update(self, dt_ms: int) -> None:
        dt = dt_ms / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        self.garden_state.update(dt, mouse_pos if self.garden_rect.collidepoint(mouse_pos) else None)
        super().update(dt_ms)
        self._update_details()

    def render(self) -> None:
        # 1. Background (Soft garden green)
        self.surface.fill((20, 30, 20))
        
        # 2. Render Slimes
        for slime in self.garden_state.slimes:
            is_selected = (slime == self.garden_state.selected)
            self.renderer.render(self.surface, slime, is_selected)
            
        # 3. Render UI components
        super().render()
