import pygame
import math
import random
from typing import List, Optional, Any
from loguru import logger

from src.shared.engine.scene_templates.combat_scene import CombatSceneBase
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.spec import UISpec
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession
from src.shared.combat.d20_resolver import D20Resolver
from src.shared.combat.turn_order import TurnOrderManager
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.teams.stat_calculator import calculate_hp, calculate_attack, calculate_speed

class DungeonUnit:
    """Wrapper for combatants."""
    def __init__(self, id: str, name: str, stats: dict, side: str, entity: Optional[Any] = None):
        self.id = id
        self.name = name
        self.stats = stats # hp, max_hp, attack, defense, speed, stance
        self.side = side
        self.entity = entity # Original Slime or Hero entity

class DungeonCombatScene(CombatSceneBase):
    def on_combat_enter(self, **kwargs):
        self.session = kwargs.get("session")
        if not self.session:
            # Fallback for direct testing
            self.session = DungeonSession()
            self.session.start_run()
            
        self.slime_renderer = SlimeRenderer()
        
        # 1. Setup Units
        hero = self.session.hero
        self.party[0] = DungeonUnit("hero", hero.name, hero.stats, "party", hero)
        
        enemy_data = kwargs.get("enemy_entity")
        enemy_name = getattr(enemy_data, "name", "Giant Slime")
        enemy_stats = {"hp": 20, "max_hp": 20, "attack": 4, "defense": 2, "speed": 5, "stance": "Aggressive"}
        self.enemies[0] = DungeonUnit("slime_0", enemy_name, enemy_stats, "enemy", enemy_data)
        
        # 2. Setup Party Slimes
        for i, slime in enumerate(self.session.party_slimes):
            if i >= 4: break
            slot_idx = i + 1
            stats = {
                "hp": calculate_hp(slime.genome),
                "max_hp": calculate_hp(slime.genome),
                "attack": calculate_attack(slime.genome),
                "defense": 2,
                "speed": calculate_speed(slime.genome),
                "stance": "Aggressive"
            }
            # Mocking slime entity for renderer
            class MockSlime:
                def __init__(self, genome):
                    self.genome = genome
                    class Kinematics:
                        def __init__(self): self.position = pygame.Vector2(0,0)
                    self.kinematics = Kinematics()
            
            mock_slime = MockSlime(slime.genome)
            self.party[slot_idx] = DungeonUnit(f"party_{slot_idx}", slime.name, stats, "party", mock_slime)
        
        # 3. Setup Turn Order
        self.session.turn_manager.reset()
        self.session.turn_manager.add_combatant("hero", hero.stats["speed"])
        for unit in self.party:
            if unit and unit.id != "hero":
                self.session.turn_manager.add_combatant(unit.id, unit.stats["speed"])
        self.session.turn_manager.add_combatant("slime_0", 5)
        
        self.add_log("Combat started!")
        self._next_turn()

    def _setup_action_buttons(self):
        # Evenly space 4 buttons in bottom bar
        p = self.spec.padding_md
        bw, bh = self.bottom_rect.width, self.bottom_rect.height
        btn_w = (bw - (5 * p)) // 4
        btn_h = bh - 24
        btn_y = self.bottom_rect.y + 12
        
        self.btn_attack = Button("Attack", pygame.Rect(p, btn_y, btn_w, btn_h), self._handle_player_attack, self.spec, variant="primary")
        self.action_panel.add_child(self.btn_attack)
        
        self.btn_ability = Button("Ability", pygame.Rect(2*p + btn_w, btn_y, btn_w, btn_h), lambda: self.add_log("Locked"), self.spec, variant="secondary", enabled=False)
        self.action_panel.add_child(self.btn_ability)
        
        self.btn_item = Button("Item", pygame.Rect(3*p + 2*btn_w, btn_y, btn_w, btn_h), lambda: self.add_log("Empty"), self.spec, variant="secondary", enabled=False)
        self.action_panel.add_child(self.btn_item)
        
        self.btn_flee = Button("Flee", pygame.Rect(4*p + 3*btn_w, btn_y, btn_w, btn_h), self._handle_flee, self.spec, variant="danger")
        self.action_panel.add_child(self.btn_flee)

    def _next_turn(self):
        self.active_actor_id = self.session.turn_manager.next_turn()
        order = self.session.turn_manager.get_order()
        
        def get_name(eid):
            for unit in (self.party + self.enemies):
                if unit and unit.id == eid: return unit.name
            return eid

        if order:
            self.turn_label_active.set_text(f"Turn: {get_name(order[0])}")
            if len(order) > 1:
                self.turn_label_next.set_text(f"Next: {get_name(order[1])}")
        
        can_act = (self.active_actor_id == "hero" or (self.active_actor_id and self.active_actor_id.startswith("party_")))
        self.btn_attack.enabled = can_act
        self.btn_flee.enabled = can_act
        
        if self.active_actor_id and self.active_actor_id.startswith("slime"):
            self._enemy_turn()

    def _draw_unit_slot(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, entity: Optional[DungeonUnit], side: str):
        super()._draw_unit_slot(surface, x, y, w, h, entity, side)
        
        if entity and entity.entity:
            if hasattr(entity.entity, "kinematics"):
                old_pos = entity.entity.kinematics.position.copy()
                entity.entity.kinematics.position.x = x + w // 2
                entity.entity.kinematics.position.y = y + h // 3 + 4
                self.slime_renderer.render(surface, entity.entity)
                entity.entity.kinematics.position = old_pos

    def _handle_player_attack(self):
        attacker = next((u for u in self.party if u and u.id == self.active_actor_id), None)
        if not attacker: return

        target = self.enemies[0]
        if not target or target.stats["hp"] <= 0: return
        
        atk_mod = attacker.stats["attack"]
        resolver = D20Resolver()
        roll_res = resolver.ability_check(modifier=atk_mod, difficulty_class=10 + target.stats["defense"])
        
        if roll_res.success:
            damage = atk_mod + 2
            target.stats["hp"] -= damage
            self.add_log(f"{attacker.name} HITS for {damage}!")
            self.trigger_flash((255, 100, 100))
        else:
            self.add_log(f"{attacker.name} MISSES!")
            self.trigger_flash((255, 255, 255))
            
        if target.stats["hp"] <= 0:
            target.stats["hp"] = 0
            self._handle_victory()
        else:
            self._next_turn()

    def _enemy_turn(self):
        valid_targets = [u for u in self.party if u and u.stats["hp"] > 0]
        if not valid_targets: return
        
        hero_unit = next((u for u in valid_targets if u.id == "hero"), None)
        target = hero_unit if hero_unit else random.choice(valid_targets)
        
        resolver = D20Resolver()
        roll_res = resolver.ability_check(modifier=3, difficulty_class=10 + target.stats["defense"])
        
        if roll_res.success:
            damage = 4
            target.stats["hp"] -= damage
            self.add_log(f"Slime HITS {target.name} for {damage}!")
            self.trigger_flash((200, 0, 0))
        else:
            self.add_log("Slime MISSES!")
            self.trigger_flash((200, 200, 200))
            
        if target.id == "hero" and target.stats["hp"] <= 0:
            target.stats["hp"] = 0
            self._handle_defeat()
        elif target.stats["hp"] <= 0:
            target.stats["hp"] = 0
            self.add_log(f"{target.name} has fallen!")
            rs = next((s for s in self.session.party_slimes if s.name == target.name), None)
            if rs: rs.alive = False
            self._next_turn()
        else:
            self._next_turn()

    def _handle_victory(self):
        self.add_log("Victory!")
        self.request_scene("dungeon_room", session=self.session, combat_result="victory")

    def _handle_defeat(self):
        self.add_log("Hero has fallen...")
        self.session.end_run(cause="Killed in combat")
        self.request_scene("the_room", session=self.session)

    def _handle_flee(self):
        self.add_log("Fleeing...")
        self.request_scene("dungeon_room", session=self.session)
