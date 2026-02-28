import pygame
import random
import math
from enum import Enum, auto
from typing import Optional, List, Tuple

from src.shared.engine.scene_manager import Scene
from src.shared.ui.base import UIComponent
from src.shared.ui.panel import Panel
from src.shared.ui.button import Button
from src.shared.ui.label import Label
from src.shared.ui.spec import UISpec
from src.shared.ui.layouts import SelectionLayout, OverlayLayout
from src.shared.teams.roster import Roster, RosterSlime, TeamRole
from src.shared.genetics.inheritance import breed, generate_random
from src.shared.genetics.genome import SlimeGenome, CulturalBase
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
    def __init__(self, manager, spec: UISpec, **kwargs):
        super().__init__(manager, spec, **kwargs)
        self.layout = SelectionLayout(spec)
        self.roster = kwargs.get("roster")
        if not self.roster:
            from src.shared.teams.roster_save import load_roster
            self.roster = load_roster()
            
        self.state = BreedingState.SELECT_A
        
        # Selection state
        self.parent_a: Optional[RosterSlime] = None
        self.parent_b: Optional[RosterSlime] = None
        self.offspring_genome: Optional[SlimeGenome] = None
        self.offspring_name: str = ""
        self.offspring_slime: Optional[RosterSlime] = None
        
        # UI Setup
        self.ui_components: List[UIComponent] = []
        self.cards: List[ProfileCard] = []
        self._setup_ui()
        
        # Rendering
        self.renderer = SlimeRenderer()
        
        # Animation timer
        self.anim_timer = 0.0
        self._complete_timer = 0.0
        # Input for naming
        self.name_font = pygame.font.Font(None, int(48 * spec.scale_factor))

    def _setup_ui(self):
        self.ui_components = []
        
        # 1. Base Layout Panels
        Panel(self.layout.header, self.spec, variant="surface").add_to(self.ui_components)
        Panel(self.layout.action_bar, self.spec, variant="surface").add_to(self.ui_components)
        
        # 2. Title and Status
        Label("BREEDING CHAMBER", (self.layout.header.centerx, 20), self.spec, size="xl", bold=True, centered=True).add_to(self.ui_components)
        
        status_text = self.get_status_text()
        status_color = self.spec.color_text_dim
        if self.state == BreedingState.PREVIEW: status_color = self.spec.color_warning
        
        Label(status_text, (self.layout.header.centerx, 50), self.spec, size="md", color=status_color, centered=True).add_to(self.ui_components)

        # 3. Global Navigation
        Button("BACK", pygame.Rect(20, 10, 100, 44), self._handle_back, self.spec, variant="secondary").add_to(self.ui_components)

        # 4. State-Specific Content
        if self.state in [BreedingState.SELECT_A, BreedingState.SELECT_B]:
            self._setup_selection_view()
        elif self.state == BreedingState.PREVIEW:
            self._setup_preview_view()
        elif self.state == BreedingState.COMPLETE:
            self._setup_complete_view()

    def _setup_selection_view(self):
        # Left Panel: Parent Slots
        Panel(self.layout.left_panel, self.spec, variant="surface").add_to(self.ui_components)
        Label("PARENT A", (self.layout.left_panel.x + 20, self.layout.left_panel.y + 10), self.spec, bold=True).add_to(self.ui_components)
        
        if self.parent_a:
            ProfileCard(self.parent_a, (self.layout.left_panel.x + 20, self.layout.left_panel.y + 40), self.spec).add_to(self.ui_components)
        else:
            p_rect = pygame.Rect(self.layout.left_panel.x + 20, self.layout.left_panel.y + 40, self.spec.card_width, self.spec.card_height)
            Panel(p_rect, self.spec, variant="surface", border=True).add_to(self.ui_components)
            Label("NONE SELECTED", (p_rect.centerx, p_rect.centery), self.spec, centered=True).add_to(self.ui_components)

        # Right Panel: Selection Grid
        Panel(self.layout.right_panel, self.spec, variant="surface").add_to(self.ui_components)
        Label("AVAILABLE PARTNERS", (self.layout.right_panel.x + 20, self.layout.right_panel.y + 10), self.spec, bold=True).add_to(self.ui_components)
        
        slimes = [s for s in self.roster.slimes if s.alive and s != self.parent_a]
        self.cards = []
        for i, slime in enumerate(slimes):
            if i >= 6: break
            row_y = self.layout.right_panel.y + 40 + (i * 90)
            card = ProfileCard(slime, (self.layout.right_panel.x + 20, row_y), self.spec).add_to(self.ui_components)
            self.cards.append(card)
            
            if not slime.can_breed:
                # Ghost button to show why can't select
                Label("(Need Lv.3)", (card.rect.right - 80, card.rect.y + 10), self.spec, size="sm", color=self.spec.color_danger).add_to(self.ui_components)
            else:
                Button("Select", pygame.Rect(card.rect.right - 70, card.rect.y + 10, 60, 30),
                       lambda s=slime: self.handle_card_click(s), self.spec, variant="primary").add_to(self.ui_components)

    def _setup_preview_view(self):
        # Show both parents in side panels, preview in center
        Panel(self.layout.left_panel, self.spec, variant="surface").add_to(self.ui_components)
        ProfileCard(self.parent_a, (self.layout.left_panel.x + 20, self.layout.left_panel.y + 40), self.spec).add_to(self.ui_components)
        
        Panel(self.layout.right_panel, self.spec, variant="surface").add_to(self.ui_components)
        ProfileCard(self.parent_b, (self.layout.right_panel.x + 20, self.layout.right_panel.y + 40), self.spec).add_to(self.ui_components)
        
        # Center Preview Table
        center_rect = self.layout.center_area.inflate(-40, -40)
        preview_panel = Panel(center_rect, self.spec, variant="card").add_to(self.ui_components)
        
        Label("POTENTIAL OFFSPRING", (center_rect.centerx, center_rect.y + 20), self.spec, size="lg", bold=True, centered=True).add_to(self.ui_components)
        
        y_off = center_rect.y + 60
        stats = [
            ("HP", self.offspring_genome.base_hp),
            ("ATK", self.offspring_genome.base_atk),
            ("SPD", self.offspring_genome.base_spd)
        ]
        for label, val in stats:
            Label(f"{label}: {int(val*0.95)}-{int(val*1.05)}", (center_rect.centerx, y_off), self.spec, centered=True).add_to(self.ui_components)
            y_off += 30
            
        Label(f"Culture: {self.offspring_genome.cultural_base.value.upper()}", (center_rect.centerx, y_off + 20), self.spec, color=self.spec.color_accent, centered=True).add_to(self.ui_components)
        
        Button("BEGIN RITUAL", pygame.Rect(center_rect.centerx - 100, center_rect.bottom - 60, 200, 44),
               self.start_breeding, self.spec, variant="primary").add_to(self.ui_components)

    def _setup_complete_view(self):
        # Show Offspring in center
        center_rect = self.layout.center_area.inflate(-20, -100)
        Panel(center_rect, self.spec, variant="card").add_to(self.ui_components)
        
        Label("BREEDING COMPLETE", (center_rect.centerx, center_rect.y + 20), self.spec, size="lg", bold=True, centered=True).add_to(self.ui_components)
        
        if self.offspring_slime:
            ProfileCard(self.offspring_slime, (center_rect.centerx - self.spec.card_width//2, center_rect.y + 60), self.spec).add_to(self.ui_components)
            
        Button("RETURN TO GARDEN", pygame.Rect(center_rect.centerx - 100, center_rect.bottom - 60, 200, 44),
               lambda: self.manager.switch_to("garden"), self.spec, variant="primary").add_to(self.ui_components)

    def get_status_text(self) -> str:
        if self.state == BreedingState.SELECT_A:
            return "CHOOSE PARENT A (LEVEL 3+)"
        elif self.state == BreedingState.SELECT_B:
            return f"CHOOSE PARTNER FOR {self.parent_a.name.upper()}"
        elif self.state == BreedingState.PREVIEW:
            return "WARNING: BOTH PARENTS WILL LOSE 1 LEVEL"
        elif self.state == BreedingState.ANIMATION:
            return "STIRRING THE PRISM..."
        elif self.state == BreedingState.NAMING:
            return "A NEW SLIME ARRIVES"
        elif self.state == BreedingState.COMPLETE:
            return "SUCCESSFUL LEGACY"
        return ""

    def _handle_back(self):
        if self.state in [BreedingState.SELECT_A, BreedingState.COMPLETE]:
            self.manager.switch_to("garden")
        elif self.state == BreedingState.SELECT_B:
            self.state = BreedingState.SELECT_A
            self.parent_a = None
            self._setup_ui()
        elif self.state == BreedingState.PREVIEW:
            self.state = BreedingState.SELECT_B
            self.parent_b = None
            self._setup_ui()

    def handle_event(self, event: pygame.event.Event):
        # Pass to UI components
        for comp in reversed(self.ui_components):
            if hasattr(comp, "handle_event") and comp.handle_event(event):
                return

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
            return
        
        if self.state == BreedingState.SELECT_A:
            self.parent_a = slime
            self.state = BreedingState.SELECT_B
            self._setup_ui()
        elif self.state == BreedingState.SELECT_B:
            if slime != self.parent_a:
                self.parent_b = slime
                self.state = BreedingState.PREVIEW
                has_elder = self.parent_a.is_elder or self.parent_b.is_elder
                self.offspring_genome = breed(self.parent_a.genome, self.parent_b.genome, elder_bonus=has_elder)
                self._setup_ui()

    def start_breeding(self):
        self.state = BreedingState.ANIMATION
        self.anim_timer = 0.0
        self._setup_ui()

    def finalize_breeding(self):
        if not self.parent_a.is_elder:
            self.parent_a.level = max(1, self.parent_a.level - 1)
        if not self.parent_b.is_elder:
            self.parent_b.level = max(1, self.parent_b.level - 1)
        
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
        from src.shared.teams.roster_save import save_roster
        save_roster(self.roster)
        
        self.state = BreedingState.COMPLETE
        self._complete_timer = 3.0
        self._setup_ui()

    def update(self, dt: float):
        dt_ms = int(dt * 1000)
        for comp in self.ui_components:
            comp.update(dt_ms)

        if self.state == BreedingState.ANIMATION:
            self.anim_timer += dt
            if self.anim_timer > 2.0:
                self.state = BreedingState.NAMING
                self.offspring_name = f"Slug-{random.randint(10, 99)}"
                self._setup_ui()
                
        if self.state == BreedingState.COMPLETE:
            if self._complete_timer > 0:
                self._complete_timer -= dt
                if self._complete_timer <= 0:
                    self.manager.switch_to("garden")

    def render(self, surface: pygame.Surface):
        surface.fill(self.spec.color_bg)
        
        for comp in self.ui_components:
            comp.render(surface)
            
        if self.state == BreedingState.ANIMATION:
            progress = min(1.0, self.anim_timer / 2.0)
            center = (self.spec.screen_width // 2, self.spec.screen_height // 2)
            for i in range(12):
                angle = math.radians(i * 30 + progress * 360)
                dist = 150 * (1.0 - progress)
                px = center[0] + dist * math.cos(angle)
                py = center[1] + dist * math.sin(angle)
                pygame.draw.circle(surface, self.spec.color_accent, (int(px), int(py)), 10)

        elif self.state == BreedingState.NAMING:
            overlay_rect = self.layout.center_area.inflate(-100, -200)
            pygame.draw.rect(surface, (0,0,0,180), self.spec.screen_rect if hasattr(self.spec, "screen_rect") else surface.get_rect(), )
            # Simple naming input render
            txt_surf = self.name_font.render(self.offspring_name + "_", True, (255, 255, 255))
            txt_rect = txt_surf.get_rect(center=(self.spec.screen_width // 2, self.spec.screen_height // 2))
            surface.blit(txt_surf, txt_rect)
            Label("NAME YOUR NEW ARRIVAL", (txt_rect.centerx, txt_rect.top - 40), self.spec, centered=True, bold=True).render(surface)
