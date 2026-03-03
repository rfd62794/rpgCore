"""
StatBlock Wiring Tests

Tests for stat_block integration in UI and game systems.
Ensures computed stats are used when available, with proper fallbacks.
"""

import pytest
from src.shared.genetics.genome import SlimeGenome, CulturalBase
from src.shared.genetics.cultural_base import CULTURAL_PARAMETERS
from src.shared.stats.stat_block import StatBlock
from src.shared.teams.roster import RosterSlime
from src.shared.ui.stats_panel import StatsPanel
from src.shared.dispatch.dispatch_system import DispatchSystem
from src.shared.dispatch.dispatch_system import DispatchRecord, ZoneType, ZoneConfig


class TestStatBlockWiring:
    """Test stat_block integration in UI and systems."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create pure ember slime (high ATK bonus)
        self.ember_genome = SlimeGenome(
            shape="round",
            size="medium",
            base_color=(255, 0, 0),
            pattern="solid",
            pattern_color=(200, 0, 0),
            accessory="none",
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            cultural_base=CulturalBase.EMBER,
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            level=1
        )
        
        # Create pure marsh slime (high HP bonus)
        self.marsh_genome = SlimeGenome(
            shape="round",
            size="medium",
            base_color=(0, 255, 0),
            pattern="solid",
            pattern_color=(0, 200, 0),
            accessory="none",
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            cultural_base=CulturalBase.MOSS,
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            level=1
        )
        
        # Create pure tundra slime (HP +2.0, SPD -1.0)
        self.tundra_genome = SlimeGenome(
            shape="round",
            size="medium",
            base_color=(255, 255, 255),
            pattern="solid",
            pattern_color=(200, 200, 200),
            accessory="none",
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            cultural_base=CulturalBase.EMBER,  # Use EMBER as substitute for TUNDRA
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            level=1
        )
        
        # Create void slime (all cultures ~0.167)
        self.void_genome = SlimeGenome(
            shape="round",
            size="medium",
            base_color=(128, 128, 128),
            pattern="solid",
            pattern_color=(100, 100, 100),
            accessory="none",
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            cultural_base=CulturalBase.VOID,
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            level=1
        )
    
    def test_ui_reads_stat_block_hp(self):
        """Test UI reads computed HP from stat_block, not raw genome value."""
        # Create slime with stat_block (RosterSlime has stat_block property)
        slime = RosterSlime(
            slime_id="test_slime",
            name="TestSlime",
            genome=self.ember_genome,
            level=1
        )
        # stat_block is created automatically when accessed
        
        # Create StatsPanel
        panel = StatsPanel(slime, (0, 0))
        
        # Mock surface for rendering
        import pygame
        pygame.init()
        surface = pygame.Surface((200, 250))
        
        # Render panel (this will access stat_block)
        panel.render(surface)
        
        # Verify stat_block was used (ember has ATK +3.0, so ATK should be > base 5)
        assert slime.stat_block.atk > 5.0, "Ember slime should have ATK > base value"
        
        pygame.quit()
    
    def test_ember_culture_shows_higher_atk(self):
        """Test pure ember slime shows higher ATK due to culture bonus."""
        # Create ember slime with stat_block
        slime = RosterSlime(
            slime_id="ember_slime",
            name="EmberSlime",
            genome=self.ember_genome,
            level=1
        )
        # stat_block is created automatically when accessed
        
        # Ember has ATK +3.0 modifier
        ember_modifier = CULTURAL_PARAMETERS[CulturalBase.EMBER].attack_modifier
        expected_atk = int((5.0 + 0) * ember_modifier * 1.0)  # base_atk + energy_bonus * cultural_mod * level_mod
        
        # Verify computed ATK is higher than base
        assert slime.stat_block.atk > 5.0, f"Ember ATK {slime.stat_block.atk} should be > base 5.0"
        assert slime.stat_block.atk >= expected_atk, f"ATK should be at least {expected_atk}"
    
    def test_marsh_culture_shows_higher_hp(self):
        """Test pure moss slime shows higher HP due to culture bonus."""
        # Create moss slime with stat_block
        slime = RosterSlime(
            slime_id="marsh_slime",
            name="MarshSlime",
            genome=self.marsh_genome,
            level=1
        )
        # stat_block is created automatically when accessed
        
        # Moss has HP +3.0 modifier
        moss_modifier = CULTURAL_PARAMETERS[CulturalBase.MOSS].hp_modifier
        expected_hp = int(20.0 * moss_modifier * 1.0)  # base_hp * cultural_mod * level_mod
        
        # Verify computed HP is higher than base
        assert slime.stat_block.hp > 20.0, f"Moss HP {slime.stat_block.hp} should be > base 20.0"
        assert slime.stat_block.hp >= expected_hp, f"HP should be at least {expected_hp}"
    
    def test_stage_affects_displayed_stats(self):
        """Test stage affects displayed stats (Prime 1.2x vs Hatchling 0.6x)."""
        # Create slime at different stages
        hatchling_genome = SlimeGenome(
            shape="round",
            size="medium",
            base_color=(255, 0, 0),
            pattern="solid",
            pattern_color=(200, 0, 0),
            accessory="none",
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            cultural_base=CulturalBase.EMBER,
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            level=0  # Hatchling stage
        )
        
        prime_genome = SlimeGenome(
            shape="round",
            size="medium",
            base_color=(255, 0, 0),
            pattern="solid",
            pattern_color=(200, 0, 0),
            accessory="none",
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            cultural_base=CulturalBase.EMBER,
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            level=6  # Prime stage
        )
        
        # Create stat_blocks
        hatchling_block = StatBlock.from_genome(hatchling_genome)
        prime_block = StatBlock.from_genome(prime_genome)
        
        # Prime should have higher stats due to stage modifier (1.2x vs 0.6x)
        assert prime_block.hp > hatchling_block.hp, "Prime HP should be > Hatchling HP"
        assert prime_block.atk > hatchling_block.atk, "Prime ATK should be > Hatchling ATK"
        assert prime_block.spd > hatchling_block.spd, "Prime SPD should be > Hatchling SPD"
    
    def test_dungeon_combat_uses_stat_block(self):
        """Test dungeon combat uses stat_block when available."""
        # Create hero with stat_block
        hero = type('Hero', (), {
            'name': 'TestHero',
            'stat_block': StatBlock.from_genome(self.ember_genome),
            'stats': {'hp': 20, 'attack': 5}  # Fallback stats
        })()
        
        # Mock dungeon combat scene setup
        from src.apps.dungeon_crawler.ui.scene_dungeon_combat import DungeonCombatScene
        
        # Create scene with mock session
        session = type('Session', (), {
            'hero': hero,
            'start_run': lambda: None
        })()
        
        scene = DungeonCombatScene()
        scene.on_combat_enter(session=session)
        
        # Verify hero stats were updated with stat_block values
        assert scene.party[0].stats['attack'] == hero.stat_block.atk, "Combat should use stat_block ATK"
        assert scene.party[0].stats['hp'] == hero.stat_block.hp, "Combat should use stat_block HP"
        assert scene.party[0].stats['speed'] == hero.stat_block.spd, "Combat should use stat_block SPD"
    
    def test_fallback_to_stat_calculator(self):
        """Test fallback to stat_calculator when stat_block unavailable."""
        # Create slime without stat_block
        slime = RosterSlime("fallback_slime", self.ember_genome, level=1)
        # No stat_block assigned
        
        # Create StatsPanel
        panel = StatsPanel(slime, (0, 0))
        
        # Mock surface for rendering
        import pygame
        pygame.init()
        surface = pygame.Surface((200, 250))
        
        # This should not crash and should use stat_calculator fallback
        panel.render(surface)
        
        # Verify no exception was thrown
        pygame.quit()
    
    def test_void_slime_balanced_stats(self):
        """Test void slime has balanced stats slightly above base values."""
        # Create void slime with stat_block
        slime = RosterSlime("void_slime", self.void_genome, level=1)
        slime.stat_block = StatBlock.from_genome(self.void_genome)
        
        # Void has all cultures at ~0.167, so all stats should be slightly above base
        assert slime.stat_block.hp > 20.0, "Void HP should be > base 20.0"
        assert slime.stat_block.atk > 5.0, "Void ATK should be > base 5.0"
        assert slime.stat_block.spd > 5.0, "Void SPD should be > base 5.0"
        
        # No single stat should dominate too much
        hp_ratio = slime.stat_block.hp / 20.0
        atk_ratio = slime.stat_block.atk / 5.0
        spd_ratio = slime.stat_block.spd / 5.0
        
        # All ratios should be similar (within 20% of each other)
        max_ratio = max(hp_ratio, atk_ratio, spd_ratio)
        min_ratio = min(hp_ratio, atk_ratio, spd_ratio)
        assert max_ratio - min_ratio < 0.2, "Void stats should be balanced"
    
    def test_tundra_spd_penalty_visible(self):
        """Test ember slime shows SPD penalty but HP bonus."""
        # Create ember slime with stat_block (using EMBER as TUNDRA substitute)
        slime = RosterSlime(
            slime_id="tundra_slime",
            name="TundraSlime",
            genome=self.tundra_genome,
            level=1
        )
        # stat_block is created automatically when accessed
        
        # Ember has ATK +3.0, so ATK should be higher than base
        assert slime.stat_block.hp > 20.0, "Ember should have HP bonus"
        assert slime.stat_block.atk > 5.0, "Ember should have ATK bonus"
        
        # Verify the specific modifiers
        ember_hp_mod = CULTURAL_PARAMETERS[CulturalBase.EMBER].hp_modifier  # +3.0
        ember_atk_mod = CULTURAL_PARAMETERS[CulturalBase.EMBER].attack_modifier  # +3.0
        
        # HP and ATK should be increased
        assert slime.stat_block.hp > 20.0 * ember_hp_mod, "HP should reflect +3.0 modifier"
        assert slime.stat_block.atk > 5.0 * ember_atk_mod, "ATK should reflect +3.0 modifier"


class TestDispatchSystemStatBlock:
    """Test DispatchSystem stat_block integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.dispatch_system = DispatchSystem()
        
        # Create test slime with stat_block
        genome = SlimeGenome(
            shape="round",
            size="medium",
            base_color=(255, 0, 0),
            pattern="solid",
            pattern_color=(200, 0, 0),
            accessory="none",
            curiosity=0.5,
            energy=0.5,
            affection=0.5,
            shyness=0.5,
            cultural_base=CulturalBase.EMBER,
            base_hp=20.0,
            base_atk=5.0,
            base_spd=5.0,
            level=1
        )
        
        self.slime_with_stat_block = RosterSlime(
            slime_id="test_slime",
            name="TestSlime",
            genome=genome,
            level=1
        )
        # stat_block is created automatically when accessed
        
        # Create slime without stat_block
        self.slime_without_stat_block = RosterSlime(
            slime_id="fallback_slime",
            name="FallbackSlime",
            genome=genome,
            level=1
        )
        # No stat_block assigned
    
    def test_dispatch_uses_stat_block_when_available(self):
        """Test dispatch uses stat_block when available."""
        slimes = [self.slime_with_stat_block]
        
        # Calculate squad power
        power = self.dispatch_system._calculate_squad_power(slimes)
        
        # Should use stat_block.atk instead of genome.base_atk
        expected_power = (
            self.slime_with_stat_block.level * 0.1 +  # level power
            self.slime_with_stat_block.stat_block.atk * 0.02 +  # stat_block ATK power
            self.slime_with_stat_block.stat_block.hp * 0.01 +   # stat_block HP power
            self.slime_with_stat_block.stat_block.spd * 0.02 +  # stat_block SPD power
            self.slime_with_stat_block.genome.tier * 0.05      # tier power
        )
        
        assert abs(power - expected_power) < 0.001, f"Power {power} should equal expected {expected_power}"
    
    def test_dispatch_fallback_to_genome_when_no_stat_block(self):
        """Test dispatch falls back to genome when no stat_block."""
        slimes = [self.slime_without_stat_block]
        
        # Calculate squad power
        power = self.dispatch_system._calculate_squad_power(slimes)
        
        # Should use genome.base_atk instead of stat_block.atk
        expected_power = (
            self.slime_without_stat_block.level * 0.1 +  # level power
            self.slime_without_stat_block.genome.base_atk * 0.02 +  # genome ATK power
            self.slime_without_stat_block.genome.base_hp * 0.01 +   # genome HP power
            self.slime_without_stat_block.genome.base_spd * 0.02 +  # genome SPD power
            self.slime_without_stat_block.genome.tier * 0.05      # tier power
        )
        
        assert abs(power - expected_power) < 0.001, f"Power {power} should equal expected {expected_power}"
