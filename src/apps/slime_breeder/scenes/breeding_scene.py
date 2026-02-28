import pygame
import random
from enum import Enum, auto
from typing import Optional, List, Tuple

from src.shared.engine.scene_manager import Scene
from src.shared.ui.base import UIComponent
from src.shared.ui import Panel, Button, Label
from src.shared.teams.roster import Roster, RosterSlime, TeamRole
from src.shared.genetics.inheritance import breed, generate_random
from src.shared.genetics.genome import SlimeGenome
from src.shared.ui.profile_card import ProfileCard
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.apps.slime_breeder.entities.slime import Slime

class BreedingState(Enum):
    SELECT_A = auto()
    SELECT_B = auto()
    PREVIEW  = auto()
    ANIMATION = auto()
    NAMING   = auto()
    COMPLETE = auto()

class BreedingScene(Scene):
    def __init__(self, roster: Roster):
        super().__init__()
        self.roster = roster
        self.state = BreedingState.SELECT_A
        
        # Selection state
        self.parent_a: Optional[RosterSlime] = None
        self.parent_b: Optional[RosterSlime] = None
        self.offspring_genome: Optional[SlimeGenome] = None
        self.offspring_name: str = ""
        self.offspring_slime: Optional[RosterSlime] = None
        
        # UI Setup
        self.ui_components: List[UIComponent] = []
        self.setup_ui()
        
        # Rendering
        self.renderer = SlimeRenderer()
        self.cards: List[ProfileCard] = []
        
        # Animation timer
        self.anim_timer = 0.0
        
        # Input for naming
        self.name_font = pygame.font.Font(None, 48)

    def setup_ui(self):
        self.ui_components.clear()
        
        # Title Panel
        title_panel = Panel(pygame.Rect(0, 0, 800, 60), color=(40, 40, 60))
        self.ui_components.append(title_panel)
        
        title_label = Label("BREEDING CHAMBER", (400, 30), size=32, color=(200, 200, 255))
        self.ui_components.append(title_label)
        
        # Status Label
        status_text = self.get_status_text()
        self.status_label = Label(status_text, (400, 80), size=24, color=(180, 180, 200))
        self.ui_components.append(self.status_label)
        
        # Action Buttons
        self.back_btn = Button(pygame.Rect(20, 15, 100, 30), "BACK", color=(100, 60, 60))
        self.ui_components.append(self.back_btn)
        
        if self.state == BreedingState.PREVIEW:
            self.breed_btn = Button(pygame.Rect(350, 400, 100, 40), "BREED!", color=(60, 120, 60))
            self.ui_components.append(self.breed_btn)
            
        if self.state == BreedingState.COMPLETE:
            self.finish_btn = Button(pygame.Rect(350, 500, 100, 40), "GARDEN", color=(60, 80, 120))
            self.ui_components.append(self.finish_btn)

    def get_status_text(self) -> str:
        if self.state == BreedingState.SELECT_A:
            return "Choose Parent A (Requirement: Lv.3+)"
        elif self.state == BreedingState.SELECT_B:
            return f"Choose Partner for {self.parent_a.name}"
        elif self.state == BreedingState.PREVIEW:
            return "Previewing Legacy. Warning: Parents will lose 1 Level."
        elif self.state == BreedingState.ANIMATION:
            return "The ritual is underway..."
        elif self.state == BreedingState.NAMING:
            return "A new slime is born! Give it a name."
        elif self.state == BreedingState.COMPLETE:
            return "Breeding complete."
        return ""

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_btn.rect.collidepoint(event.pos):
                    if self.state in [BreedingState.SELECT_A, BreedingState.COMPLETE]:
                        self.manager.switch_to("garden")
                    elif self.state == BreedingState.SELECT_B:
                        self.state = BreedingState.SELECT_A
                        self.parent_a = None
                        self.setup_ui()
                    elif self.state == BreedingState.PREVIEW:
                        self.state = BreedingState.SELECT_B
                        self.parent_b = None
                        self.setup_ui()
                
                if self.state == BreedingState.PREVIEW and hasattr(self, 'breed_btn'):
                    if self.breed_btn.rect.collidepoint(event.pos):
                        self.start_breeding()
                
                if self.state == BreedingState.COMPLETE and hasattr(self, 'finish_btn'):
                    if self.finish_btn.rect.collidepoint(event.pos):
                        self.manager.switch_to("garden")

                # Selection clicks
                if self.state in [BreedingState.SELECT_A, BreedingState.SELECT_B]:
                    for card in self.cards:
                        if card.rect.collidepoint(event.pos):
                            self.handle_card_click(card.slime)

            if self.state == BreedingState.NAMING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.offspring_name:
                            self.finalize_breeding()
                    elif event.key == pygame.K_BACKSPACE:
                        self.offspring_name = self.offspring_name[:-1]
                    else:
                        if len(self.offspring_name) < 12:
                            self.offspring_name += event.unicode

    def handle_card_click(self, slime: RosterSlime):
        if not slime.can_breed:
            return # Level gate
        
        if self.state == BreedingState.SELECT_A:
            self.parent_a = slime
            self.state = BreedingState.SELECT_B
            self.setup_ui()
        elif self.state == BreedingState.SELECT_B:
            if slime != self.parent_a:
                self.parent_b = slime
                self.state = BreedingState.PREVIEW
                # Check for Elder bonus
                has_elder = self.parent_a.is_elder or self.parent_b.is_elder
                self.offspring_genome = breed(self.parent_a.genome, self.parent_b.genome, elder_bonus=has_elder)
                self.setup_ui()

    def start_breeding(self):
        self.state = BreedingState.ANIMATION
        self.anim_timer = 0.0
        self.setup_ui()

    def finalize_breeding(self):
        # 1. Apply Level Drain (Skip for Elders)
        if not self.parent_a.is_elder:
            self.parent_a.breeding_lock_level = self.parent_a.level
            self.parent_a.level -= 1
        
        if not self.parent_b.is_elder:
            self.parent_b.breeding_lock_level = self.parent_b.level
            self.parent_b.level -= 1
        
        # 2. Add Offspring (Level 2 if any parent is Elder)
        start_level = 2 if (self.parent_a.is_elder or self.parent_b.is_elder) else 1
        
        new_id = f"slime_{random.randint(10000, 99999)}"
        self.offspring_slime = RosterSlime(
            slime_id=new_id,
            name=self.offspring_name,
            genome=self.offspring_genome,
            team=TeamRole.UNASSIGNED,
            level=start_level,
            generation=self.offspring_genome.generation
        )
        self.roster.add_slime(self.offspring_slime)
        
        self.state = BreedingState.COMPLETE
        self.setup_ui()

    def update(self, dt_ms: int):
        if self.state == BreedingState.ANIMATION:
            self.anim_timer += dt_ms / 1000.0
            if self.anim_timer > 2.0:
                self.state = BreedingState.NAMING
                self.offspring_name = f"Slug-{random.randint(10, 99)}"
                self.setup_ui()

        # Update cards
        if self.state in [BreedingState.SELECT_A, BreedingState.SELECT_B]:
            # Show breedable slimes
            slimes = [s for s in self.roster.slimes if s.alive and s != self.parent_a]
            self.cards = []
            for i, slime in enumerate(slimes):
                col = i % 3
                row = i // 3
                pos = (50 + col * 240, 150 + row * 160)
                self.cards.append(ProfileCard(slime, pos))

    def render(self, surface: pygame.Surface):
        surface.fill((20, 20, 30))
        
        for comp in self.ui_components:
            comp.render(surface)
            
        if self.state in [BreedingState.SELECT_A, BreedingState.SELECT_B]:
            for card in self.cards:
                # Dim cards that can't breed
                card.render(surface)
                if not card.slime.can_breed:
                    overlay = pygame.Surface((card.WIDTH, card.HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 180))
                    surface.blit(overlay, card.position)
                    
        elif self.state == BreedingState.PREVIEW:
            # Show Parents
            ProfileCard(self.parent_a, (50, 150)).render(surface)
            ProfileCard(self.parent_b, (530, 150)).render(surface)
            
            # Preview Panel (Middle)
            preview_rect = pygame.Rect(280, 150, 240, 250)
            pygame.draw.rect(surface, (40, 45, 60), preview_rect, border_radius=8)
            pygame.draw.rect(surface, (100, 120, 180), preview_rect, width=1, border_radius=8)
            
            Label("POTENTIAL LEGACY", (400, 170), size=18, color=(200, 220, 255)).render(surface)
            
            # Show estimated ranges (+/- 5% of genome base)
            y_off = 200
            for label, base_val, p_pref in [("HP", self.offspring_genome.base_hp, max(self.parent_a.genome.base_hp, self.parent_b.genome.base_hp)), 
                                           ("ATK", self.offspring_genome.base_atk, (self.parent_a.genome.base_atk + self.parent_b.genome.base_atk)/2), 
                                           ("SPD", self.offspring_genome.base_spd, max(self.parent_a.genome.base_spd, self.parent_b.genome.base_spd)*0.95)]:
                msg = f"{label}: {int(base_val*0.95)}-{int(base_val*1.05)}"
                Label(msg, (400, y_off), size=16, color=(200, 200, 220)).render(surface)
                
                # Improvement indicator (Simplified comparison)
                if base_val > p_pref:
                     Label("(Up)", (480, y_off), size=12, color=(100, 255, 100)).render(surface)
                
                y_off += 25
            
            # Mutation / Culture
            mut_chance_val = 0.15 if (self.parent_a.cultural_base == CulturalBase.VOID or self.parent_b.cultural_base == CulturalBase.VOID) else 0.05
            mut_label = "HIGH" if mut_chance_val > 0.1 else "LOW"
            Label(f"Mutation Risk: {mut_label}", (400, 290), size=14, color=(180, 140, 200)).render(surface)
            Label(f"Culture: {self.offspring_genome.cultural_base.value.upper()}", (400, 310), size=14, color=(200, 200, 200)).render(surface)
            
            # Improvement note
            Label("Generational Gain: Diminishing", (400, 340), size=14, color=(100, 220, 100)).render(surface)
            Label(f"Target Gen: {self.offspring_genome.generation}", (400, 360), size=14, color=(150, 150, 255)).render(surface)

            if self.parent_a.is_elder or self.parent_b.is_elder:
                Label("ELDER BONUS: LEVEL 2 START", (400, 380), size=14, color=(255, 215, 0)).render(surface)
            
        elif self.state == BreedingState.ANIMATION:
            # Cool swirling effects
            progress = min(1.0, self.anim_timer / 2.0)
            center = (400, 300)
            for i in range(12):
                angle = math.radians(i * 30 + progress * 360)
                dist = 100 * (1.0 - progress)
                px = center[0] + dist * math.cos(angle)
                py = center[1] + dist * math.sin(angle)
                pygame.draw.circle(surface, (200, 200, 255), (int(px), int(py)), 10)

        elif self.state == BreedingState.NAMING:
            # Name Input
            center = (400, 300)
            txt_surf = self.name_font.render(self.offspring_name + "_", True, (255, 255, 255))
            txt_rect = txt_surf.get_rect(center=center)
            surface.blit(txt_surf, txt_rect)
            
        elif self.state == BreedingState.COMPLETE:
            # Show the new arrival
            ProfileCard(self.offspring_slime, (290, 200)).render(surface)
            Label("Welcome Home!", (400, 400), size=32, color=(100, 255, 100)).render(surface)
