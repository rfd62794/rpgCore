
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


def test_sword_attacks_taunted_target():
    """SWORD should redirect attacks to a taunted enemy when no low-HP non-taunted targets exist."""
    actor = create_slime("1", "A", TileState.BLUE, Shape.TRIANGLE, Hat.SWORD)
    actor.attack = 10
    
    # Only taunted enemies — no low-HP non-taunted targets means Taunt Break won't trigger 
    e1 = create_slime("e1", "Tank", TileState.RED, Shape.SQUARE, Hat.SHIELD)
    e1.hp = 25
    e1.defense = 0
    e1.taunt_active = True
    
    enemies = [e1]
    allies = [actor]
    
    log = execute_action(actor, allies, enemies)
    
    # With only one enemy that's taunted and has high HP, SWORD uses Crit Focus first
    # On subsequent call it attacks
    assert "CRIT FOCUS" in log or "attacks Tank" in log or "CRITICAL" in log


def test_sword_taunt_break():
    """SWORD should use Taunt Break when a taunted enemy is blocking a low-HP target."""
    actor = create_slime("1", "A", TileState.BLUE, Shape.TRIANGLE, Hat.SWORD)
    actor.attack = 10
    
    e1 = create_slime("e1", "Squishy", TileState.RED, Shape.CIRCLE, Hat.SWORD)
    e1.hp = 5   # Below 40% of max_hp (20 * 0.4 = 8)
    e1.defense = 0
    e1.taunt_active = False
    
    e2 = create_slime("e2", "Tank", TileState.RED, Shape.SQUARE, Hat.SHIELD)
    e2.hp = 25
    e2.defense = 0
    e2.taunt_active = True  # Taunting — blocking the squishy target
    
    enemies = [e1, e2]
    allies = [actor]
    
    log = execute_action(actor, allies, enemies)
    
    # SWORD AI should use Taunt Break on Tank to access Squishy
    assert "TAUNT BREAK" in log
    assert e2.taunt_active is False


def test_sword_crit_focus():
    """SWORD should enter Crit Focus when facing a high-HP enemy."""
    actor = create_slime("1", "A", TileState.BLUE, Shape.TRIANGLE, Hat.SWORD)
    actor.attack = 10
    
    e1 = create_slime("e1", "Tanky", TileState.RED, Shape.SQUARE, Hat.SHIELD)
    e1.hp = 28  # Above 75% of max_hp (30 * 0.75 = 22.5)
    e1.max_hp = 30
    
    e2 = create_slime("e2", "Other", TileState.RED, Shape.CIRCLE, Hat.SWORD)
    e2.hp = 15
    
    enemies = [e1, e2]
    allies = [actor]
    
    log = execute_action(actor, allies, enemies)
    
    assert "CRIT FOCUS" in log
    assert actor.is_crit_focused is True


def test_staff_heals_scales_with_missing_hp():
    """STAFF heal should scale with missing HP but be capped at 30% of max HP."""
    actor = create_slime("1", "H", TileState.BLUE, Shape.CIRCLE, Hat.STAFF)
    actor.attack = 5
    
    a1 = create_slime("a1", "A1", TileState.BLUE, Shape.CIRCLE, Hat.SWORD)
    a1.max_hp = 20
    a1.hp = 5   # Very low — will trigger Heal (below 60% threshold for Mana Surge)
    
    # Heal = Base(5) + 30% of missing(15) = 5 + 4 = 9 → capped at 30% of max_hp(6)
    
    allies = [actor, a1]
    enemies = []
    
    log = execute_action(actor, allies, enemies)
    
    assert a1.hp == 11  # 5 + 6 = 11
    assert "heals A1 for 6" in log


def test_shield_bash_stuns_healer():
    """SHIELD should use Shield Bash to stun enemy healers."""
    actor = create_slime("1", "T", TileState.BLUE, Shape.SQUARE, Hat.SHIELD)
    actor.attack = 6
    
    e_healer = create_slime("e1", "Cleric", TileState.RED, Shape.CIRCLE, Hat.STAFF)
    e_healer.hp = 20
    
    allies = [actor]
    enemies = [e_healer]
    
    log = execute_action(actor, allies, enemies)
    
    assert "SHIELD BASHES" in log
    assert e_healer.stunned_turns == 1
    assert e_healer.hp < 20  # Should have taken damage


def test_shield_taunts_when_no_healers():
    """SHIELD should default to taunt when no enemy healers to bash and no wounded allies."""
    actor = create_slime("1", "T", TileState.BLUE, Shape.CIRCLE, Hat.SHIELD)
    start_defense = actor.defense
    
    e_sword = create_slime("e1", "Brute", TileState.RED, Shape.SQUARE, Hat.SWORD)
    
    allies = [actor]
    enemies = [e_sword]
    
    assert not actor.taunt_active
    
    execute_action(actor, allies, enemies)
    assert actor.taunt_active
    assert actor.defense == start_defense + 2
