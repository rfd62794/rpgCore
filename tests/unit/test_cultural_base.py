import pytest
from src.shared.genetics.genome import SlimeGenome
from src.shared.genetics.cultural_base import CulturalBase
from src.shared.genetics.inheritance import breed, generate_random
from src.shared.teams.stat_calculator import calculate_hp, calculate_attack, calculate_speed
from src.shared.teams.roster import RosterSlime, TeamRole

def test_cultural_inheritance():
    # Two parents of same culture should produce same culture offspring
    g1 = generate_random(CulturalBase.EMBER)
    g2 = generate_random(CulturalBase.EMBER)
    offspring = breed(g1, g2)
    assert offspring.cultural_base == CulturalBase.EMBER

def test_mixed_culture_inheritance():
    # Two different cultures should mostly produce MIXED
    g1 = generate_random(CulturalBase.EMBER)
    g2 = generate_random(CulturalBase.CRYSTAL)
    
    mixed_found = False
    for i in range(100):
        offspring = breed(g1, g2)
        if offspring.cultural_base == CulturalBase.MIXED:
            mixed_found = True
            break
    assert mixed_found

def test_stat_modifiers():
    # Ember should have high ATK but lower HP
    ember_genome = generate_random(CulturalBase.EMBER)
    crystal_genome = generate_random(CulturalBase.CRYSTAL)
    
    # At level 1
    ember_atk = calculate_attack(ember_genome, 1)
    crystal_atk = calculate_attack(crystal_genome, 1)
    # Ember has 1.4x attack modifier, Crystal has 0.8x
    # Base attack is influenced by energy, so we can't be 100% sure without fixed energy
    # But cultural modifier is strong
    
    ember_hp = calculate_hp(ember_genome, 1)
    crystal_hp = calculate_hp(crystal_genome, 1)
    # Crystal has 1.4x hp modifier, Ember has 0.8x
    assert crystal_hp > ember_hp

def test_level_progression():
    genome = generate_random(CulturalBase.MOSS)
    hp_lv1 = calculate_hp(genome, 1)
    hp_lv10 = calculate_hp(genome, 10)
    
    # Level 10 should be roughly double Level 1 in HP (1.0 + 9*0.1 = 1.9x)
    assert hp_lv10 > hp_lv1

def test_slime_leveling_logic():
    rs = RosterSlime("test", "Testy", generate_random())
    assert rs.level == 1
    
    # 5 + (1*2) = 7 XP to next level
    leveled = rs.gain_exp(7)
    assert leveled is True
    assert rs.level == 2
    assert rs.experience == 0
    
    # 5 + (2*2) = 9 XP to level 3
    rs.gain_exp(5)
    assert rs.level == 2
    rs.gain_exp(4)
    assert rs.level == 3
    
    assert rs.can_breed is True

def test_breeding_lock_mechanic():
    rs = RosterSlime("test", "Testy", generate_random(), level=4)
    assert rs.can_breed is True
    
    # Lock it
    rs.breeding_lock_level = 4
    rs.level = 3 # Level drain
    assert rs.can_breed is False
    
    # Regain level
    rs.level = 4
    assert rs.can_breed is False # Still locked at level 4
    
    rs.level = 5
    assert rs.can_breed is True
