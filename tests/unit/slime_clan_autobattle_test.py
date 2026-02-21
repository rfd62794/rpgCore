import pytest
from src.apps.slime_clan.auto_battle import (
    Shape, Hat, SlimeUnit, create_slime, execute_action
)
from src.apps.slime_clan.territorial_grid import TileState

def test_slime_stat_generation():
    # Square gets +Defense -Speed +HP
    square_shield = create_slime("1", "Tank", TileState.BLUE, Shape.SQUARE, Hat.SHIELD)
    assert square_shield.shape == Shape.SQUARE
    assert square_shield.hat == Hat.SHIELD
    assert square_shield.speed == 7   # base 10 - 3 (shape)
    assert square_shield.defense == 7 # base 2 + 3 (shape) + 2 (hat)
    assert square_shield.max_hp == 30 # base 20 + 5 (shape) + 5 (hat)

    # Triangle gets +Speed -Defense -HP
    tri_sword = create_slime("2", "Attacker", TileState.BLUE, Shape.TRIANGLE, Hat.SWORD)
    assert tri_sword.speed == 14      # base 10 + 4
    assert tri_sword.defense == 1     # base 2 - 1
    assert tri_sword.max_hp == 17     # base 20 - 3
    assert tri_sword.attack == 8      # base 5 + 3 (hat)

    # Circle gets Balanced stats
    circle_staff = create_slime("3", "Healer", TileState.BLUE, Shape.CIRCLE, Hat.STAFF)
    assert circle_staff.speed == 12   # base 10 + 2 (hat)
    assert circle_staff.defense == 2  # base 2
    assert circle_staff.max_hp == 20  # base 20
    assert circle_staff.attack == 3   # base 5 - 2 (hat)


def test_sword_targets_lowest_hp_enemy():
    actor = create_slime("1", "A", TileState.BLUE, Shape.TRIANGLE, Hat.SWORD)
    actor.attack = 10
    
    e1 = create_slime("e1", "E1", TileState.RED, Shape.CIRCLE, Hat.SWORD)
    e1.hp = 15
    e1.defense = 0
    
    e2 = create_slime("e2", "E2", TileState.RED, Shape.CIRCLE, Hat.SWORD)
    e2.hp = 5
    e2.defense = 0
    
    e3 = create_slime("e3", "E3", TileState.RED, Shape.CIRCLE, Hat.SWORD)
    e3.hp = 25
    e3.defense = 0
    
    enemies = [e1, e2, e3]
    allies = [actor]
    
    log = execute_action(actor, allies, enemies)
    
    # E2 should be attacked and killed (5 - 10 < 0, floored to 0)
    assert e2.hp == 0
    assert e1.hp == 15
    assert e3.hp == 25
    assert "attacks E2" in log


def test_staff_heals_lowest_hp_ally():
    actor = create_slime("1", "H", TileState.BLUE, Shape.CIRCLE, Hat.STAFF)
    actor.attack = 5  # Staff uses attack for heal power
    
    a1 = create_slime("a1", "A1", TileState.BLUE, Shape.CIRCLE, Hat.SWORD)
    a1.max_hp = 20
    a1.hp = 10 # 50%
    
    a2 = create_slime("a2", "A2", TileState.BLUE, Shape.CIRCLE, Hat.SWORD)
    a2.max_hp = 20
    a2.hp = 18 # 90%
    
    allies = [actor, a1, a2]
    enemies = []
    
    log = execute_action(actor, allies, enemies)
    
    # A1 should be healed (10 + 5 = 15)
    assert a1.hp == 15
    assert a2.hp == 18
    assert "heals A1" in log


def test_shield_taunts_and_clears_taunt():
    actor = create_slime("1", "T", TileState.BLUE, Shape.CIRCLE, Hat.SHIELD)
    start_defense = actor.defense
    
    allies = [actor]
    enemies = []
    
    assert not actor.taunt_active
    
    # Turn 1: Taunt
    execute_action(actor, allies, enemies)
    assert actor.taunt_active
    assert actor.defense == start_defense + 2
    
    # Turn 2: Clears old taunt, then taunts again (adds +2 again as it stacks indefinitely in this stub version)
    execute_action(actor, allies, enemies)
    assert actor.taunt_active
    assert actor.defense == start_defense + 4
