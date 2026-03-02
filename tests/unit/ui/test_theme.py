"""
Tests for UITheme design token system
"""

import pytest
from src.shared.ui.theme import UITheme


class TestUITheme:
    """Test UITheme design token system"""
    
    def test_theme_defaults(self):
        """Test that default theme has all required properties"""
        theme = UITheme()
        
        # Typography
        assert theme.font_large == 18
        assert theme.font_medium == 14
        assert theme.font_small == 11
        assert theme.font_tiny == 10
        
        # Base colors
        assert theme.background == (20, 20, 30)
        assert theme.surface == (30, 30, 45)
        assert theme.surface_raised == (40, 40, 58)
        assert theme.border == (60, 60, 80)
        assert theme.border_active == (100, 100, 140)
        
        # Text colors
        assert theme.text_primary == (220, 220, 235)
        assert theme.text_secondary == (160, 160, 180)
        assert theme.text_dim == (100, 100, 120)
        assert theme.text_accent == (255, 215, 0)
        
        # Status colors
        assert theme.success == (80, 180, 80)
        assert theme.warning == (220, 160, 40)
        assert theme.danger == (200, 60, 60)
        assert theme.info == (80, 140, 220)
    
    def test_culture_colors_complete(self):
        """Test that all expected culture colors are defined"""
        theme = UITheme()
        
        expected_cultures = [
            'ember', 'gale', 'marsh', 'crystal', 'tundra', 'tide', 'void', 'coastal', 'mixed'
        ]
        
        for culture in expected_cultures:
            assert culture in theme.culture_colors
            assert isinstance(theme.culture_colors[culture], tuple)
            assert len(theme.culture_colors[culture]) == 3  # RGB tuple
            assert all(0 <= c <= 255 for c in theme.culture_colors[culture])  # Valid RGB values
    
    def test_stage_colors_complete(self):
        """Test that all expected stage colors are defined"""
        theme = UITheme()
        
        expected_stages = [
            'Hatchling', 'Juvenile', 'Young', 'Prime', 'Veteran', 'Elder'
        ]
        
        for stage in expected_stages:
            assert stage in theme.stage_colors
            assert isinstance(theme.stage_colors[stage], tuple)
            assert len(theme.stage_colors[stage]) == 3  # RGB tuple
            assert all(0 <= c <= 255 for c in theme.stage_colors[stage])  # Valid RGB values
    
    def test_tier_colors_complete(self):
        """Test that all expected tier colors are defined"""
        theme = UITheme()
        
        expected_tiers = [1, 2, 3, 4, 5, 6, 7, 8]
        
        for tier in expected_tiers:
            assert tier in theme.tier_colors
            assert isinstance(theme.tier_colors[tier], tuple)
            assert len(theme.tier_colors[tier]) == 3  # RGB tuple
            assert all(0 <= c <= 255 for c in theme.tier_colors[tier])  # Valid RGB values
    
    def test_button_colors_complete(self):
        """Test that all expected button colors are defined"""
        theme = UITheme()
        
        expected_variants = ['primary', 'secondary', 'danger', 'ghost', 'warning']
        
        for variant in expected_variants:
            assert variant in theme.button_colors
            assert 'bg' in theme.button_colors[variant]
            assert 'text' in theme.button_colors[variant]
            assert 'border' in theme.button_colors[variant]
            
            # Check that all colors are valid RGB/RGBA tuples
            for color_type in ['bg', 'text', 'border']:
                color = theme.button_colors[variant][color_type]
                assert isinstance(color, tuple)
                assert len(color) in [3, 4]  # RGB or RGBA
                assert all(0 <= c <= 255 for c in color[:3])  # Check RGB values
    
    def test_panel_colors_complete(self):
        """Test that all expected panel colors are defined"""
        theme = UITheme()
        
        expected_variants = ['surface', 'card', 'overlay', 'raised']
        
        for variant in expected_variants:
            assert variant in theme.panel_colors
            assert 'bg' in theme.panel_colors[variant]
            assert 'border' in theme.panel_colors[variant]
            
            # Check that all colors are valid RGB tuples
            for color_type in ['bg', 'border']:
                color = theme.panel_colors[variant][color_type]
                if isinstance(color, tuple):  # Skip alpha tuples
                    assert len(color) == 3
                    assert all(0 <= c <= 255 for c in color)
    
    def test_theme_default_instance(self):
        """Test that UITheme.DEFAULT is properly set"""
        assert UITheme.DEFAULT is not None
        assert isinstance(UITheme.DEFAULT, UITheme)
        assert UITheme.DEFAULT.font_large == 18  # Check it's a valid theme
    
    def test_theme_customization(self):
        """Test that theme can be customized"""
        custom_theme = UITheme(
            font_large=20,
            background=(10, 10, 20),
            success=(100, 200, 100)
        )
        
        assert custom_theme.font_large == 20
        assert custom_theme.background == (10, 10, 20)
        assert custom_theme.success == (100, 200, 100)
        # Other defaults should remain
        assert custom_theme.font_medium == 14
        assert custom_theme.surface == (30, 30, 45)
