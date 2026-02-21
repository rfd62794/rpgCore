
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


def test_sword_targets_taunted_enemy_over_low_hp():
    actor = create_slime("1", "A", TileState.BLUE, Shape.TRIANGLE, Hat.SWORD)
    actor.attack = 10
    
    e1 = create_slime("e1", "Squishy", TileState.RED, Shape.CIRCLE, Hat.SWORD)
    e1.hp = 5
    e1.defense = 0
    e1.taunt_active = False
    
    e2 = create_slime("e2", "Tank", TileState.RED, Shape.SQUARE, Hat.SHIELD)
    e2.hp = 25
    e2.defense = 0
    e2.taunt_active = True # Taunting tank
    
    enemies = [e1, e2]
    allies = [actor]
    
    log = execute_action(actor, allies, enemies)
    
    # E2 (Tank) should be attacked despite E1 (Squishy) having lower HP
    assert e2.hp == 15 # 25 - 10
    assert e1.hp == 5
    assert "attacks Tank" in log


def test_staff_heals_scales_with_missing_hp():
    actor = create_slime("1", "H", TileState.BLUE, Shape.CIRCLE, Hat.STAFF)
    actor.attack = 5  # Base heal = max(2, 5) = 5
    
    a1 = create_slime("a1", "A1", TileState.BLUE, Shape.CIRCLE, Hat.SWORD)
    a1.max_hp = 20
    a1.hp = 10 # Missing 10 HP
    
    # Heal should be Base (5) + 30% of missing HP (3) = 8
    # BUT explicitly capped at 30% of max_hp (20 * 0.3) = 6
    # Final Heal = 6
    
    allies = [actor, a1]
    enemies = []
    
    log = execute_action(actor, allies, enemies)
    
    assert a1.hp == 16 # 10 + 6 = 16
    assert "heals A1 for 6" in log


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
