"""
Tests for Garden Assignment Indicators
"""

import pytest
import pygame
from src.shared.ui.theme import DEFAULT_THEME
from src.apps.slime_breeder.entities.slime import Slime
from src.shared.genetics.genome import SlimeGenome, CulturalBase


class TestGardenIndicators:
    
    @classmethod
    def setup_class(cls):
        """Initialize pygame for rendering tests"""
        pygame.init()
        pygame.font.init()
    
    @classmethod
    def teardown_class(cls):
        """Clean up pygame"""
        pygame.quit()
    
    def test_slime_team_property(self):
        """Test that slime has team property"""
        genome = SlimeGenome(
            cultural_base=CulturalBase.EMBER,
            base_color=(255, 100, 50),
            pattern_color=(200, 50, 25),
            shape="round",
            size="medium",
            pattern="spotted",
            accessory="none"
        )
        
        slime = Slime("Test Slime", genome, (100, 100))
        
        # Should have team property initialized to None
        assert hasattr(slime, 'team')
        assert slime.team is None
        
        # Can assign team
        slime.team = 'dungeon'
        assert slime.team == 'dungeon'
    
    def test_team_colors_in_theme(self):
        """Test that theme has team colors"""
        assert hasattr(DEFAULT_THEME, 'team_colors')
        
        expected_teams = ['dungeon', 'racing', 'garden', 'conquest']
        for team in expected_teams:
            assert team in DEFAULT_THEME.team_colors
            assert isinstance(DEFAULT_THEME.team_colors[team], tuple)
            assert len(DEFAULT_THEME.team_colors[team]) == 3  # RGB tuple
    
    def test_team_color_helper_method(self):
        """Test team_color helper method"""
        # Test existing team colors
        assert DEFAULT_THEME.team_color('dungeon') == (180, 60, 60)
        assert DEFAULT_THEME.team_color('racing') == (60, 140, 220)
        assert DEFAULT_THEME.team_color('garden') == (80, 160, 80)
        
        # Test fallback
        assert DEFAULT_THEME.team_color('nonexistent') == (150, 150, 150)
        assert DEFAULT_THEME.team_color('nonexistent', (100, 100, 100)) == (100, 100, 100)
    
    def test_stage_colors_in_theme(self):
        """Test that theme has stage colors"""
        assert hasattr(DEFAULT_THEME, 'stage_colors')
        
        expected_stages = ['Hatchling', 'Juvenile', 'Young', 'Prime', 'Veteran', 'Elder']
        for stage in expected_stages:
            assert stage in DEFAULT_THEME.stage_colors
            assert isinstance(DEFAULT_THEME.stage_colors[stage], tuple)
            assert len(DEFAULT_THEME.stage_colors[stage]) == 3  # RGB tuple
    
    def test_stage_color_helper_method(self):
        """Test stage_color helper method"""
        # Test existing stage colors
        assert DEFAULT_THEME.stage_color('Young') == (144, 238, 144)
        assert DEFAULT_THEME.stage_color('Elder') == (147, 112, 219)
        
        # Test fallback
        assert DEFAULT_THEME.stage_color('Unknown') == (150, 150, 150)
        assert DEFAULT_THEME.stage_color('Unknown', (100, 100, 100)) == (100, 100, 100)
    
    def test_hover_tooltip_delay(self):
        """Test hover tooltip delay configuration"""
        from src.apps.slime_breeder.ui.scene_garden import GardenScene
        from src.shared.ui.spec import UISpec
        from src.shared.engine.scene_manager import SceneManager
        
        # Create garden scene
        spec = UISpec()
        manager = SceneManager(spec)
        scene = GardenScene(manager, spec)
        
        # Should have hover tooltip properties
        assert hasattr(scene, 'hover_timer')
        assert hasattr(scene, 'hovered_slime')
        assert hasattr(scene, 'tooltip_delay')
        
        # Should have reasonable delay
        assert scene.tooltip_delay == 0.5
        assert scene.hover_timer == 0.0
        assert scene.hovered_slime is None
    
    def test_slime_renderer_team_ring_rendering(self):
        """Test that slime renderer can handle team ring rendering"""
        from src.shared.rendering.slime_renderer import SlimeRenderer
        
        genome = SlimeGenome(
            cultural_base=CulturalBase.EMBER,
            base_color=(255, 100, 50),
            pattern_color=(200, 50, 25),
            shape="round",
            size="medium",
            pattern="spotted",
            accessory="none"
        )
        
        slime = Slime("Test Slime", genome, (100, 100))
        slime.team = 'dungeon'  # Assign team
        
        renderer = SlimeRenderer()
        surface = pygame.Surface((200, 200))
        
        # Should render without crashing
        renderer.render(surface, slime, selected=False)
        
        # Should also render with selection
        renderer.render(surface, slime, selected=True)
    
    def test_slime_renderer_dispatched_state(self):
        """Test that slime renderer can handle dispatched state"""
        from src.shared.rendering.slime_renderer import SlimeRenderer
        
        genome = SlimeGenome(
            cultural_base=CulturalBase.EMBER,
            base_color=(255, 100, 50),
            pattern_color=(200, 50, 25),
            shape="round",
            size="medium",
            pattern="spotted",
            accessory="none"
        )
        
        slime = Slime("Test Slime", genome, (100, 100))
        slime.is_dispatched = True  # Set dispatched state
        
        renderer = SlimeRenderer()
        surface = pygame.Surface((200, 200))
        
        # Should render without crashing
        renderer.render(surface, slime, selected=False)
    
    def test_slime_renderer_stage_dot_rendering(self):
        """Test that slime renderer can handle stage dot rendering"""
        from src.shared.rendering.slime_renderer import SlimeRenderer
        
        genome = SlimeGenome(
            cultural_base=CulturalBase.EMBER,
            base_color=(255, 100, 50),
            pattern_color=(200, 50, 25),
            shape="round",
            size="medium",
            pattern="spotted",
            accessory="none"
        )
        
        slime = Slime("Test Slime", genome, (100, 100))
        
        renderer = SlimeRenderer()
        surface = pygame.Surface((200, 200))
        
        # Should render without crashing
        renderer.render(surface, slime, selected=False)
