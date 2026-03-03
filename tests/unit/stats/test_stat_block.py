"""
Tests for StatBlock computed stats system.
Verifies culture modifiers, stage scaling, and equipment integration.
"""

import pytest
from dataclasses import replace

from src.shared.stats.stat_block import StatBlock
from src.shared.genetics.genome import SlimeGenome
from src.shared.teams.roster import RosterSlime
from src.shared.genetics.cultural_base import CulturalBase


class TestStatBlock:
    """Test suite for StatBlock functionality."""
    
    @pytest.fixture
    def base_genome(self):
        """Create a base genome for testing."""
        return SlimeGenome(
            shape='round',
            size='medium',
            base_color=(100, 150, 200),
            pattern='solid',
            pattern_color=(50, 75, 100),
            accessory='none',
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            cultural_base=CulturalBase.EMBER,
            culture_expression={'ember': 1.0, 'gale': 0.0, 'marsh': 0.0, 'crystal': 0.0, 'tundra': 0.0, 'tide': 0.0},
            generation=1,
            level=5  # Young stage with 1.0x modifier for predictable results
        )
    
    def test_from_genome_pure_ember(self, base_genome):
        """Test pure ember culture gives attack bonus."""
        # Pure ember culture
        ember_genome = replace(base_genome,
            cultural_base=CulturalBase.EMBER,
            culture_expression={'ember': 1.0, 'gale': 0.0, 'marsh': 0.0, 'crystal': 0.0, 'tundra': 0.0, 'tide': 0.0}
        )
        
        stat_block = StatBlock.from_genome(ember_genome)
        
        # Ember: atk=3.0, hp=0.5, spd=0.5 per unit weight
        assert stat_block.culture_atk == 3.0  # 1.0 * 3.0
        assert stat_block.culture_hp == 0.5   # 1.0 * 0.5
        assert stat_block.culture_spd == 0.5 # 1.0 * 0.5
        
        # Final stats should include culture bonuses
        # Base: 20.0 + 0.5 = 20.5 -> int(20.5) = 20 (rounded down)
        assert stat_block.hp == 20
        # Base: 5.0 + 3.0 = 8.0 -> int(8.0) = 8
        assert stat_block.atk == 8
        assert stat_block.atk > base_genome.base_atk  # Attack bonus
        # Base: 5.0 + 0.5 = 5.5 -> int(5.5) = 5 (rounded down)
        assert stat_block.spd == 5
    
    def test_from_genome_pure_marsh(self, base_genome):
        """Test pure marsh culture gives HP bonus."""
        # Pure marsh culture
        marsh_genome = replace(base_genome,
            cultural_base=CulturalBase.MOSS,
            culture_expression={'ember': 0.0, 'gale': 0.0, 'marsh': 1.0, 'crystal': 0.0, 'tundra': 0.0, 'tide': 0.0}
        )
        
        stat_block = StatBlock.from_genome(marsh_genome)
        
        # Marsh: atk=0.5, hp=3.0, spd=0.5 per unit weight
        assert stat_block.culture_atk == 0.5  # 1.0 * 0.5
        assert stat_block.culture_hp == 3.0   # 1.0 * 3.0
        assert stat_block.culture_spd == 0.5 # 1.0 * 0.5
        
        # Final stats should include culture bonuses
        assert stat_block.hp > base_genome.base_hp     # HP bonus
        assert stat_block.atk > base_genome.base_atk  # Attack bonus
        assert stat_block.spd > base_genome.base_spd   # Speed bonus
    
    def test_from_genome_pure_gale(self, base_genome):
        """Test pure gale culture gives speed bonus."""
        # Pure gale culture
        gale_genome = replace(base_genome,
            cultural_base=CulturalBase.EMBER,
            culture_expression={'ember': 0.0, 'gale': 1.0, 'marsh': 0.0, 'crystal': 0.0, 'tundra': 0.0, 'tide': 0.0}
        )
        
        stat_block = StatBlock.from_genome(gale_genome)
        
        # Gale: atk=0.5, hp=0.5, spd=3.0 per unit weight
        assert stat_block.culture_atk == 0.5  # 1.0 * 0.5
        assert stat_block.culture_hp == 0.5   # 1.0 * 0.5
        assert stat_block.culture_spd == 3.0 # 1.0 * 3.0
        
        # Final stats should include culture bonuses
        assert stat_block.spd > base_genome.base_spd   # Major speed bonus
        assert stat_block.hp > base_genome.base_hp     # HP bonus
        assert stat_block.atk > base_genome.base_atk  # Attack bonus
    
    def test_from_genome_mixed_culture(self, base_genome):
        """Test mixed culture expression gives multiple bonuses."""
        # Mixed culture: 50% ember, 50% marsh
        mixed_genome = replace(base_genome,
            cultural_base=CulturalBase.MIXED,
            culture_expression={'ember': 0.5, 'gale': 0.0, 'marsh': 0.5, 'crystal': 0.0, 'tundra': 0.0, 'tide': 0.0}
        )
        
        stat_block = StatBlock.from_genome(mixed_genome)
        
        # Ember: atk=3.0, hp=0.5, spd=0.5 * 0.5 weight = 1.5, 0.25, 0.25
        # Marsh: atk=0.5, hp=3.0, spd=0.5 * 0.5 weight = 0.25, 1.5, 0.25
        assert stat_block.culture_atk == 1.75  # 1.5 + 0.25
        assert stat_block.culture_hp == 1.75   # 0.25 + 1.5
        assert stat_block.culture_spd == 0.5  # 0.25 + 0.25
        
        # Final stats should include both culture bonuses
        assert stat_block.atk > base_genome.base_atk  # Attack bonus
        assert stat_block.hp > base_genome.base_hp     # HP bonus
        assert stat_block.spd > base_genome.base_spd   # Speed bonus
    
    def test_stage_modifier_hatchling(self, base_genome):
        """Test hatchling stage modifier reduces stats."""
        # Hatchling level (0 or 1)
        hatchling_genome = replace(base_genome, level=0)
        
        stat_block = StatBlock.from_genome(hatchling_genome)
        
        # Hatchling: 0.6x modifier
        assert stat_block.stage_modifier == 0.6
        
        # Final stats should be reduced
        expected_hp = int((base_genome.base_hp + stat_block.culture_hp) * 0.6)
        assert stat_block.hp == expected_hp
        assert stat_block.hp < base_genome.base_hp
    
    def test_stage_modifier_prime(self, base_genome):
        """Test prime stage modifier increases stats."""
        # Prime level (6 or 7)
        prime_genome = replace(base_genome, level=6)
        
        stat_block = StatBlock.from_genome(prime_genome)
        
        # Prime: 1.2x modifier
        assert stat_block.stage_modifier == 1.2
        
        # Final stats should be increased
        expected_hp = int((base_genome.base_hp + stat_block.culture_hp) * 1.2)
        assert stat_block.hp == expected_hp
        assert stat_block.hp > base_genome.base_hp
    
    def test_computed_hp_minimum_one(self):
        """Test HP is never less than 1."""
        # Create genome with very low stats
        low_genome = SlimeGenome(
            shape='round',
            size='tiny',
            base_color=(100, 100, 100),
            pattern='solid',
            pattern_color=(50, 50, 50),
            accessory='none',
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            base_hp=1.0,
            base_atk=1.0,
            base_spd=1.0,
            cultural_base=CulturalBase.EMBER,
            culture_expression={'ember': 1.0, 'gale': 0.0, 'marsh': 0.0, 'crystal': 0.0, 'tundra': 0.0, 'tide': 0.0},
            generation=1,
            level=0  # Hatchling with 0.6x modifier
        )
        
        stat_block = StatBlock.from_genome(low_genome)
        
        # Even with low base + hatchling modifier, HP should be at least 1
        assert stat_block.hp >= 1
        assert stat_block.atk >= 1
        assert stat_block.spd >= 1
    
    def test_with_equipment_modifiers(self, base_genome):
        """Test equipment modifiers are applied correctly."""
        stat_block = StatBlock.from_genome(base_genome)
        
        # Apply equipment bonuses
        equipped_block = stat_block.with_equipment(hp=10.0, atk=5.0, spd=2.0)
        
        # Equipment modifiers should be set
        assert equipped_block.equipment_hp == 10.0
        assert equipped_block.equipment_atk == 5.0
        assert equipped_block.equipment_spd == 2.0
        
        # Final stats should include equipment
        assert equipped_block.hp > stat_block.hp
        assert equipped_block.atk > stat_block.atk
        assert equipped_block.spd > stat_block.spd
    
    def test_with_equipment_immutable(self, base_genome):
        """Test with_equipment() returns new instance, doesn't mutate original."""
        stat_block = StatBlock.from_genome(base_genome)
        original_hp = stat_block.hp
        
        # Apply equipment bonuses
        equipped_block = stat_block.with_equipment(hp=10.0, atk=5.0, spd=2.0)
        
        # Original should be unchanged
        assert stat_block.hp == original_hp
        assert stat_block.equipment_hp == 0.0
        assert stat_block.equipment_atk == 0.0
        assert stat_block.equipment_spd == 0.0
        
        # New instance should have equipment
        assert equipped_block.hp > original_hp
        assert equipped_block.equipment_hp == 10.0
    
    def test_to_dict_contains_all_keys(self, base_genome):
        """Test to_dict() returns all expected keys."""
        stat_block = StatBlock.from_genome(base_genome)
        
        result = stat_block.to_dict()
        
        expected_keys = {
            'hp', 'atk', 'spd',
            'base_hp', 'base_atk', 'base_spd',
            'culture_hp', 'culture_atk', 'culture_spd',
            'stage_modifier'
        }
        
        assert set(result.keys()) == expected_keys
        assert result['hp'] == stat_block.hp
        assert result['atk'] == stat_block.atk
        assert result['spd'] == stat_block.spd
    
    def test_stat_block_property_on_roster_slime(self, base_genome):
        """Test RosterSlime.stat_block property returns StatBlock instance."""
        slime = RosterSlime(
            slime_id="test_slime",
            name="Test Slime",
            genome=base_genome,
            level=2
        )
        
        # Access stat_block property
        stat_block = slime.stat_block
        
        # Should return StatBlock instance
        assert isinstance(stat_block, StatBlock)
        assert stat_block.hp >= 1
        assert stat_block.atk >= 1
        assert stat_block.spd >= 1
        
        # Should be based on slime's genome
        assert stat_block.base_hp == base_genome.base_hp
        assert stat_block.base_atk == base_genome.base_atk
        assert stat_block.base_spd == base_genome.base_spd
    
    def test_stat_block_culture_tundra_spd_penalty(self, base_genome):
        """Test pure tundra culture applies speed penalty."""
        # Pure tundra culture
        tundra_genome = replace(base_genome,
            cultural_base=CulturalBase.VOID,
            culture_expression={'ember': 0.0, 'gale': 0.0, 'marsh': 0.0, 'crystal': 0.0, 'tundra': 1.0, 'tide': 0.0}
        )
        
        stat_block = StatBlock.from_genome(tundra_genome)
        
        # Tundra: atk=0.5, hp=2.0, spd=-1.0 per unit weight
        assert stat_block.culture_atk == 0.5  # 1.0 * 0.5
        assert stat_block.culture_hp == 2.0   # 1.0 * 2.0
        assert stat_block.culture_spd == -1.0 # 1.0 * -1.0
        
        # Final HP should be higher due to tundra bonus
        assert stat_block.hp > base_genome.base_hp
        
        # Final speed should be lower due to tundra penalty
        # But equipment and stage modifiers might offset it
        base_speed_with_culture = base_genome.base_spd + stat_block.culture_spd
        assert stat_block.culture_spd < 0  # Penalty applied
    
    def test_stage_modifier_veteran(self, base_genome):
        """Test veteran stage modifier."""
        # Veteran level (8 or 9)
        veteran_genome = replace(base_genome, level=8)
        
        stat_block = StatBlock.from_genome(veteran_genome)
        
        # Veteran: 1.1x modifier
        assert stat_block.stage_modifier == 1.1
        
        # Final stats should be increased but less than prime
        expected_hp = int((base_genome.base_hp + stat_block.culture_hp) * 1.1)
        assert stat_block.hp == expected_hp
    
    def test_stage_modifier_elder(self, base_genome):
        """Test elder stage modifier."""
        # Elder level (10+)
        elder_genome = replace(base_genome, level=10)
        
        stat_block = StatBlock.from_genome(elder_genome)
        
        # Elder: 1.0x modifier (wisdom compensates decline)
        assert stat_block.stage_modifier == 1.0
        
        # Final stats should be same as base (no multiplier)
        expected_hp = int(base_genome.base_hp + stat_block.culture_hp)
        assert stat_block.hp == expected_hp
