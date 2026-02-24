import pygame
import math
from typing import List, Optional
from loguru import logger

from src.shared.engine.scene_templates.combat_scene import CombatSceneBase
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession
from src.shared.combat.d20_resolver import D20Resolver
from src.shared.combat.turn_order import TurnOrderManager

class DungeonUnit:
    """Wrapper for combatants in the 5v5 grid."""
    def __init__(self, id: str, name: str, stats: dict, side: str):
        self.id = id
        self.name = name
        self.stats = stats # hp, max_hp, attack, defense, speed
        self.side = side

class DungeonCombatScene(CombatSceneBase):
    def on_combat_enter(self, **kwargs):
        self.session = kwargs.get("session")
        # 1. Setup Units
        hero = self.session.hero
        self.party[0] = DungeonUnit("hero", hero.name, hero.stats, "party")
        
        enemy_data = kwargs.get("enemy_entity")
        enemy_name = getattr(enemy_data, "name", "Slime")
        self.enemies[0] = DungeonUnit("slime_0", enemy_name, {"hp": 15, "max_hp": 15, "attack": 4, "defense": 2, "speed": 5}, "enemy")
        
        # 2. Setup Turn Order
        self.session.turn_manager.reset()
        self.session.turn_manager.add_combatant("hero", hero.stats["speed"])
        self.session.turn_manager.add_combatant("slime_0", 5)
        
        self.add_log("Combat started!")
        self._next_turn()

    def _setup_action_buttons(self):
        w, h = self.width, self.height
        btn_w, btn_h = 120, 40
        y = 30
        
        self.btn_attack = Button(pygame.Rect(50, y, btn_w, btn_h), text="Attack", on_click=self._handle_player_attack)
        self.btn_flee = Button(pygame.Rect(180, y, btn_w, btn_h), text="Flee", on_click=self._handle_flee)
        
        self.action_panel.add_child(self.btn_attack)
        self.action_panel.add_child(self.btn_flee)

    def _next_turn(self):
        self.active_actor_id = self.session.turn_manager.next_turn()
        
        # Update Turn Order Bar
        order_str = " → ".join(self.session.turn_manager.order)
        self.turn_label.text = f"Turn Sequence: {order_str}"
        
        # Enable/Disable buttons
        can_act = (self.active_actor_id == "hero")
        self.btn_attack.enabled = can_act
        self.btn_flee.enabled = can_act
        
        if self.active_actor_id == "slime_0":
            # Small artificial delay would be nice, but for now instant
            self._enemy_turn()

    def _handle_player_attack(self):
        if self.active_actor_id != "hero": return
        
        hero = self.party[0]
        target = self.enemies[0]
        if not target or target.stats["hp"] <= 0: return
        
        atk_mod = hero.stats["attack"]
        resolver = D20Resolver()
        roll_res = resolver.ability_check(modifier=atk_mod, difficulty_class=10 + target.stats["defense"])
        
        if roll_res.success:
            damage = atk_mod + 2
            target.stats["hp"] -= damage
            self.add_log(f"Hero HITS Slime for {damage}!")
            self.trigger_flash((255, 100, 100)) # Red flash
        else:
            self.add_log(f"Hero MISSES Slime!")
            self.trigger_flash((255, 255, 255)) # White flash
            
        if target.stats["hp"] <= 0:
            target.stats["hp"] = 0
            self._handle_victory()
        else:
            self._next_turn()

    def _enemy_turn(self):
        hero = self.party[0]
        slime = self.enemies[0]
        
        resolver = D20Resolver()
        roll_res = resolver.ability_check(modifier=3, difficulty_class=10 + hero.stats["defense"])
        
        if roll_res.success:
            damage = 4
            hero.stats["hp"] -= damage
            self.add_log(f"Slime HITS Hero for {damage}!")
            self.trigger_flash((200, 0, 0))
        else:
            self.add_log("Slime MISSES!")
            self.trigger_flash((200, 200, 200))
            
        if hero.stats["hp"] <= 0:
            hero.stats["hp"] = 0
            self._handle_defeat()
        else:
            self._next_turn()

    def _handle_victory(self):
        self.add_log("Victory!")
        # Pause briefly? No, just return for now
        self.request_scene("dungeon_room", session=self.session, combat_result="victory")

    def _handle_defeat(self):
        self.add_log("Hero has fallen...")
        self.session.end_run(cause="Killed by Slime")
        self.request_scene("the_room", session=self.session)

    def _handle_flee(self):
        self.add_log("Fleeing...")
        self.request_scene("dungeon_room", session=self.session)
