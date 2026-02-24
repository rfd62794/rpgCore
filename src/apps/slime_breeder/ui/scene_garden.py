import pygame
import random
from typing import Optional, List, Tuple
from src.shared.engine.scene_templates.garden_scene import GardenSceneBase
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.apps.slime_breeder.garden.garden_state import GardenState
from src.apps.slime_breeder.entities.slime import Slime
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.genetics import generate_random, breed

NAMES = ["Mochi", "Pip", "Glimmer", "Bloop", "Sage", "Dew", "Ember", "Fizz", "Lumen", "Nook"]

class GardenScene(GardenSceneBase):
    def on_garden_enter(self, **kwargs) -> None:
        self.garden_state = GardenState()
        self.renderer = SlimeRenderer()
        
        # 1. Custom Details UI
        self.name_label = Label(pygame.Rect(10, 40, self.panel_width-20, 30), text="Name: ---")
        self.detail_panel.add_child(self.name_label)
        
        self.mood_label = Label(pygame.Rect(10, 70, self.panel_width-20, 30), text="Mood: ---")
        self.detail_panel.add_child(self.mood_label)
        
        # 2. Custom Action Bar Buttons
        btn_y = 15
        btn_w, btn_h = 120, 50
        
        self.new_btn = Button(pygame.Rect(20, btn_y, btn_w, btn_h), text="New Slime", on_click=self._add_new_slime)
        self.action_bar.add_child(self.new_btn)
        
        self.breed_btn = Button(pygame.Rect(150, btn_y, btn_w, btn_h), text="Breed", on_click=self._breed_selected)
        self.breed_btn.set_enabled(False)
        self.action_bar.add_child(self.breed_btn)

        self.release_btn = Button(pygame.Rect(280, btn_y, btn_w, btn_h), text="Release", on_click=self._release_selected)
        self.release_btn.set_enabled(False)
        self.action_bar.add_child(self.release_btn)

        # Start with a slime
        self._add_new_slime()

    def _add_new_slime(self):
        name = random.choice(NAMES) + " " + str(len(self.garden_state.slimes) + 1)
        genome = generate_random()
        pos = (random.randint(50, self.garden_rect.width - 50), random.randint(50, self.garden_rect.height - 50))
        slime = Slime(name, genome, pos)
        self.garden_state.add_slime(slime)

    def _breed_selected(self):
        if len(self.selected_entities) == 2:
            s1, s2 = self.selected_entities
            child_name = f"{s1.name[:3]}{s2.name[3:]} Jr"
            child_genome = breed(s1.genome, s2.genome)
            # Spawn near parents
            pos = (s1.kinematics.position.x + 20, s1.kinematics.position.y + 20)
            child = Slime(child_name, child_genome, pos)
            self.garden_state.add_slime(child)
            # Select the child
            self.selected_entities = [child]
            self.on_selection_changed()

    def _release_selected(self):
        if self.selected_entities:
            for s in self.selected_entities:
                print(f"DEBUG: Releasing {s.name} into the wild...")
                self.garden_state.remove_slime(s.name)
            self.selected_entities = []
            self.on_selection_changed()

    def pick_entity(self, pos: Tuple[int, int]) -> Optional[Slime]:
        # Return the top-most slime at pos
        for slime in reversed(self.garden_state.slimes):
            dist = (slime.kinematics.position - pygame.Vector2(*pos)).magnitude()
            if dist < 40: # Hit radius
                return slime
        return None

    def on_selection_changed(self):
        num_selected = len(self.selected_entities)
        self.breed_btn.set_enabled(num_selected == 2)
        self.release_btn.set_enabled(num_selected > 0)
        
        # Update details for the primary selection
        if num_selected > 0:
            s = self.selected_entities[0]
            self.name_label.text = f"Name: {s.name}"
            self.mood_label.text = f"Mood: {s.get_mood()}"
        else:
            self.name_label.text = "Name: ---"
            self.mood_label.text = "Mood: ---"

    def update_garden(self, dt_ms: float):
        dt = dt_ms / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        # Only pass cursor if in garden area
        cursor = mouse_pos if self.garden_rect.collidepoint(mouse_pos) else None
        self.garden_state.update(dt, cursor)

    def render_garden(self, surface: pygame.Surface):
        # Background color is handled by base
        # Render Slimes
        for slime in self.garden_state.slimes:
            is_selected = (slime in self.selected_entities)
            self.renderer.render(surface, slime, is_selected)
