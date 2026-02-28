import pygame
import math
from typing import List, Optional, Any
from loguru import logger

from src.shared.engine.scene_templates.combat_scene import CombatSceneBase
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession
from src.shared.combat.d20_resolver import D20Resolver
from src.shared.combat.turn_order import TurnOrderManager
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.teams.stat_calculator import calculate_hp, calculate_attack, calculate_speed

class DungeonUnit:
    """Wrapper for combatants in the 5v5 grid."""
    def __init__(self, id: str, name: str, stats: dict, side: str, entity: Optional[Any] = None):
        self.id = id
        self.name = name
        self.stats = stats # hp, max_hp, attack, defense, speed, stance
        self.side = side
        self.entity = entity # Original Slime or Hero entity

class DungeonCombatScene(CombatSceneBase):
    def on_combat_enter(self, **kwargs):
        self.session = kwargs.get("session")
        self.slime_renderer = SlimeRenderer()
        
        # 1. Setup Units
        hero = self.session.hero
        self.party[0] = DungeonUnit("hero", hero.name, hero.stats, "party", hero)
        
        enemy_data = kwargs.get("enemy_entity")
        enemy_name = getattr(enemy_data, "name", "Slime")
        # Enforce stance in stats for UI
        enemy_stats = {"hp": 15, "max_hp": 15, "attack": 4, "defense": 2, "speed": 5, "stance": "Aggressive"}
        self.enemies[0] = DungeonUnit("slime_0", enemy_name, enemy_stats, "enemy", enemy_data)
        
        # 2. Setup Party Slimes (Slots 1-4)
        for i, slime in enumerate(self.session.party_slimes):
            if i >= 4: break # Max 4 slimes + 1 hero
            slot_idx = i + 1
            stats = {
                "hp": calculate_hp(slime.genome),
                "max_hp": calculate_hp(slime.genome),
                "attack": calculate_attack(slime.genome),
                "defense": 2,
                "speed": calculate_speed(slime.genome),
                "stance": "Aggressive"
            }
            # Mocking slime entity for renderer (it expects Slime entity with kinematics)
            # Create a minimal object that renderer can handle
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
        p = self.padding
        bw, bh = self.bottom_rect.width, self.bottom_rect.height
        btn_w = (bw - (5 * p)) // 4
        btn_h = int(bh * 0.8)
        # Calculate Y relative to screen bottom bar start
        btn_y = self.bottom_rect.y + (bh - btn_h) // 2
        
        button_font_size = 24
        
        self.btn_attack = Button(pygame.Rect(p, btn_y, btn_w, btn_h), text="Attack", on_click=self._handle_player_attack)
        self.btn_attack.bg_color = (40, 80, 40) # Greenish
        
        self.btn_ability = Button(pygame.Rect(2*p + btn_w, btn_y, btn_w, btn_h), text="Ability", on_click=lambda: self.add_log("No abilities yet!"))
        self.btn_ability.bg_color = (40, 40, 80) # Bluish
        self.btn_ability.enabled = False
        
        self.btn_item = Button(pygame.Rect(3*p + 2*btn_w, btn_y, btn_w, btn_h), text="Item", on_click=lambda: self.add_log("Inventory empty!"))
        self.btn_item.bg_color = (80, 80, 40) # Yellowish
        self.btn_item.enabled = False
        
        self.btn_flee = Button(pygame.Rect(4*p + 3*btn_w, btn_y, btn_w, btn_h), text="Flee", on_click=self._handle_flee)
        self.btn_flee.bg_color = (80, 40, 40) # Reddish
        
        for btn in [self.btn_attack, self.btn_ability, self.btn_item, self.btn_flee]:
            btn.font_size = button_font_size
            self.action_panel.add_child(btn)

    def _next_turn(self):
        self.active_actor_id = self.session.turn_manager.next_turn()
        order = self.session.turn_manager.get_order()
        
        # Update Turn Order Labels
        active_name = "—"
        next_name = "—"
        
        # Helper to find name from ID
        def get_name(eid):
            # Check all 10 slots
            for unit in (self.party + self.enemies):
                if unit and unit.id == eid:
                    return unit.name
            return eid

        if order:
            active_name = get_name(order[0])
            if len(order) > 1:
                next_name = get_name(order[1])
        
        self.turn_label_active.set_text(f"Turn: {active_name}")
        self.turn_label_next.set_text(f"Next: {next_name}")
        
        # Enable/Disable buttons
        can_act = (self.active_actor_id == "hero")
        # For this demo, we'll allow player to control all party slimes too
        if self.active_actor_id and self.active_actor_id.startswith("party_"):
            can_act = True
            
        self.btn_attack.enabled = can_act
        self.btn_flee.enabled = can_act
        
        if self.active_actor_id and self.active_actor_id.startswith("slime"):
            # Just enemy turn for now
            self._enemy_turn()

    def _draw_unit_slot(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, entity: Optional[DungeonUnit], side: str):
        # Call base to draw container, name, HP bar
        super()._draw_unit_slot(surface, x, y, w, h, entity, side)
        
        # Add SlimeRenderer visuals if it's an enemy or party slime
        if entity and entity.entity:
            # We need to temporarily set kinematics pos for the renderer
            # centered in the slot middle-upper area
            if hasattr(entity.entity, "kinematics"):
                old_x = entity.entity.kinematics.position.x
                old_y = entity.entity.kinematics.position.y
                
                # Render higher up in the slot to avoid overlapping stance text
                entity.entity.kinematics.position.x = x + w // 2
                entity.entity.kinematics.position.y = y + h // 3 + 4
                
                # Render (centered)
                self.slime_renderer.render(surface, entity.entity)
                
                # Restore
                entity.entity.kinematics.position.x = old_x
                entity.entity.kinematics.position.y = old_y

    def _handle_player_attack(self):
        if not self.active_actor_id or (self.active_actor_id != "hero" and not self.active_actor_id.startswith("party_")): 
            return
        
        # Get active unit
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
            self.add_log(f"{attacker.name} HITS Slime for {damage}!")
            self.trigger_flash((255, 100, 100)) # Red flash
        else:
            self.add_log(f"{attacker.name} MISSES Slime!")
            self.trigger_flash((255, 255, 255)) # White flash
            
        if target.stats["hp"] <= 0:
            target.stats["hp"] = 0
            self._handle_victory()
        else:
            self._next_turn()

    def _enemy_turn(self):
        # Target hero first, then random party slime
        valid_targets = [u for u in self.party if u and u.stats["hp"] > 0]
        if not valid_targets: return
        
        hero_unit = next((u for u in valid_targets if u.id == "hero"), None)
        target = hero_unit if hero_unit else random.choice(valid_targets)
        
        slime = self.enemies[0]
        
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
            # Mark as dead in roster context
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
        self.session.end_run(cause="Killed by Slime")
        self.request_scene("the_room", session=self.session)

    def _handle_flee(self):
        self.add_log("Fleeing...")
        self.request_scene("dungeon_room", session=self.session)
