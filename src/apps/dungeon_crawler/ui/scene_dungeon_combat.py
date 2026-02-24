import pygame
import math
from typing import List, Optional
from loguru import logger

from src.shared.engine.scene_templates.combat_scene import CombatSceneBase
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.progress_bar import ProgressBar
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession
from src.shared.combat.d20_resolver import D20Resolver, DifficultyClass
from src.shared.combat.turn_order import TurnOrderManager
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer

class DungeonCombatScene(CombatSceneBase):
    def __init__(self, manager, session: DungeonSession, **kwargs):
        super().__init__(manager, **kwargs)
        self.session = session
        self.resolver = D20Resolver()
        self.log_messages: List[str] = []
        
        # Renderer for enemy
        self.slime_renderer = SlimeRenderer()
        # The enemy entity is passed in kwargs
        self.enemy = kwargs.get("enemy_entity")
        
        # Layout metrics
        self.hero_x = 150
        self.enemy_x = manager.width - 250
        self.center_y = manager.height // 2 - 50

    def on_combat_enter(self, **kwargs):
        logger.info("⚔️ Combat Mode Started")
        self.log_messages.append("An enemy appears!")
        
        # Setup Turn Order
        self.session.turn_manager.reset()
        self.session.turn_manager.add_combatant("hero", self.session.hero.stats["speed"])
        self.session.turn_manager.add_combatant("enemy", 5) # Default slime speed
        
        self._next_turn()

    def _next_turn(self):
        self.current_turn_id = self.session.turn_manager.next_turn()
        self.turn_label.text = f"Turn: {self.current_turn_id.upper()}"
        
        if self.current_turn_id == "enemy":
            self._enemy_ai_turn()

    def _enemy_ai_turn(self):
        # Enemy attacks hero
        roll_res = self.resolver.ability_check(modifier=2, difficulty_class=10 + self.session.hero.stats["defense"])
        damage = 0
        if roll_res.success:
            damage = 3
            self.session.hero.stats["hp"] -= damage
            self.log_messages.append(f"Slime attacks: {roll_res.roll} (HIT) for {damage} dmg")
        else:
            self.log_messages.append(f"Slime attacks: {roll_res.roll} (MISS)")
            
        if self.session.hero.stats["hp"] <= 0:
            self.session.hero.stats["hp"] = 0
            self._handle_defeat()
        else:
            # Small delay? For now just instant
            self._next_turn()

    def _handle_attack(self):
        if self.current_turn_id != "hero": return
        
        # Hero attacks enemy
        atk_mod = self.session.hero.stats["attack"]
        roll_res = self.resolver.ability_check(modifier=atk_mod, difficulty_class=12)
        
        if roll_res.success:
            damage = atk_mod + 2
            # Slime in RoomScene is just a visual, but we track its "HP" locally or in kwargs
            # For this pass, we just simulate a single enemy defeat
            self.log_messages.append(f"You attack: {roll_res.roll} (HIT) for {damage} dmg")
            self._handle_victory()
        else:
            self.log_messages.append(f"You attack: {roll_res.roll} (MISS)")
            self._next_turn()

    def _handle_victory(self):
        self.log_messages.append("Victory!")
        # Return to room, passing victory signal
        self.request_scene("dungeon_room", session=self.session, combat_result="victory")

    def _handle_defeat(self):
        self.log_messages.append("Defeat...")
        self.session.end_run(cause="Killed in combat")
        self.request_scene("the_room", session=self.session) # Return to hub

    def _setup_combat_ui(self):
        super()._setup_combat_ui()
        w, h = self.width, self.height
        
        # Action Buttons
        btn_w, btn_h = 120, 40
        self.btn_attack = Button(pygame.Rect(50, h - 100, btn_w, btn_h), text="Attack", on_click=self._handle_attack)
        self.btn_flee = Button(pygame.Rect(180, h - 100, btn_w, btn_h), text="Flee", on_click=lambda: self.request_scene("dungeon_room", session=self.session))
        self.action_panel.add_child(self.btn_attack)
        self.action_panel.add_child(self.btn_flee)
        
        # Log Panel (Center)
        self.log_panel = Panel(pygame.Rect(w//2 - 200, h//2 + 50, 400, 100), bg_color=(20, 20, 25))
        self.ui_components.append(self.log_panel)

    def render_combatants(self, surface: pygame.Surface):
        # 1. Hero (Left)
        hx, hy = self.hero_x, self.center_y
        pygame.draw.rect(surface, (100, 255, 100), (hx - 25, hy - 40, 50, 80))
        # Hero HP Bar
        hp = self.session.hero.stats["hp"]
        max_hp = self.session.hero.stats["max_hp"]
        pygame.draw.rect(surface, (200, 50, 50), (hx - 40, hy + 50, 80, 10))
        pygame.draw.rect(surface, (50, 200, 50), (hx - 40, hy + 50, int(80 * (hp/max_hp)), 10))
        
        # 2. Enemy (Right)
        if self.enemy:
            # Enemy position for renderer
            self.enemy.kinematics.position = pygame.Vector2(self.enemy_x, hy)
            self.slime_renderer.render(surface, self.enemy)
            # Enemy HP Bar (Stubbed)
            pygame.draw.rect(surface, (200, 50, 50), (self.enemy_x - 40, hy + 50, 80, 10))

    def render(self, surface: pygame.Surface) -> None:
        super().render(surface)
        # Render Log
        for i, msg in enumerate(self.log_messages[-3:]):
            label = Label(pygame.Rect(10, 10 + i * 25, 380, 20), text=msg, font_size=18, color=(200, 200, 200))
            label.render(surface.subsurface(self.log_panel.rect))
