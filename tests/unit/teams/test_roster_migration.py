"""
Tests for culture_expression migration in Roster loading.
"""

import pytest
from src.shared.teams.roster import Roster
from src.shared.genetics.cultural_base import CulturalBase


class TestCultureExpressionMigration:
    """Test suite for culture_expression migration functionality."""
    
    def test_migrate_genome_missing_expression(self):
        """Test migration when culture_expression is missing."""
        genome_data = {
            'cultural_base': CulturalBase.EMBER,
            'shape': 'round',
            'size': 'medium',
            'base_color': [255, 100, 100],
            'pattern': 'solid',
            'pattern_color': [200, 50, 50],
            'accessory': 'none',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should have culture_expression added
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'ember': 1.0}
    
    def test_migrate_genome_empty_expression(self):
        """Test migration when culture_expression is empty."""
        genome_data = {
            'cultural_base': CulturalBase.MOSS,
            'culture_expression': {},
            'shape': 'round',
            'size': 'medium',
            'base_color': [100, 255, 100],
            'pattern': 'solid',
            'pattern_color': [50, 200, 50],
            'accessory': 'none',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should have culture_expression populated
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'marsh': 1.0}
    
    def test_migrate_genome_existing_expression_unchanged(self):
        """Test that existing culture_expression is not modified."""
        existing_expr = {'ember': 0.7, 'marsh': 0.3}
        genome_data = {
            'cultural_base': CulturalBase.EMBER,
            'culture_expression': existing_expr.copy(),
            'shape': 'round',
            'size': 'medium',
            'base_color': [255, 100, 100],
            'pattern': 'solid',
            'pattern_color': [200, 50, 50],
            'accessory': 'none',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should preserve existing expression
        assert result['culture_expression'] == existing_expr
    
    def test_migrate_genome_string_cultural_base(self):
        """Test migration with string cultural_base (old format)."""
        genome_data = {
            'cultural_base': 'void',
            'shape': 'amorphous',
            'size': 'large',
            'base_color': [150, 150, 150],
            'pattern': 'iridescent',
            'pattern_color': [100, 100, 100],
            'accessory': 'glow',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should have culture_expression for void
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'void': 1.0}
    
    def test_migrate_genome_moss_alias(self):
        """Test moss -> marsh alias mapping."""
        genome_data = {
            'cultural_base': CulturalBase.MOSS,
            'shape': 'round',
            'size': 'medium',
            'base_color': [100, 255, 100],
            'pattern': 'spotted',
            'pattern_color': [50, 200, 50],
            'accessory': 'none',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should map moss to marsh
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'marsh': 1.0}
    
    def test_migrate_genome_coastal_alias(self):
        """Test coastal -> tide alias mapping."""
        genome_data = {
            'cultural_base': CulturalBase.COASTAL,
            'shape': 'elongated',
            'size': 'small',
            'base_color': [100, 150, 255],
            'pattern': 'striped',
            'pattern_color': [50, 100, 200],
            'accessory': 'shell',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should map coastal to tide
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'tide': 1.0}
    
    def test_migrate_genome_mixed_alias(self):
        """Test mixed -> marsh alias mapping."""
        genome_data = {
            'cultural_base': CulturalBase.MIXED,
            'shape': 'cubic',
            'size': 'tiny',
            'base_color': [200, 200, 200],
            'pattern': 'marbled',
            'pattern_color': [150, 150, 150],
            'accessory': 'crystals',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should map mixed to marsh
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'marsh': 1.0}
    
    def test_migrate_genome_unknown_culture_fallback(self):
        """Test fallback for unknown culture names."""
        genome_data = {
            'cultural_base': 'unknown_culture',
            'shape': 'round',
            'size': 'medium',
            'base_color': [255, 255, 255],
            'pattern': 'solid',
            'pattern_color': [200, 200, 200],
            'accessory': 'none',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should use the unknown culture name as-is
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'unknown_culture': 1.0}
    
    def test_migrate_genome_enum_handling(self):
        """Test handling of enum cultural_base values."""
        genome_data = {
            'cultural_base': CulturalBase.CRYSTAL,
            'shape': 'crystalline',
            'size': 'medium',
            'base_color': [200, 200, 255],
            'pattern': 'iridescent',
            'pattern_color': [150, 150, 200],
            'accessory': 'crystals',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should handle enum correctly
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'crystal': 1.0}
    
    def test_migrate_genome_culturalbase_prefix_cleanup(self):
        """Test cleanup of CulturalBase. prefix in string values."""
        genome_data = {
            'cultural_base': 'CulturalBase.EMBER',
            'shape': 'round',
            'size': 'medium',
            'base_color': [255, 100, 100],
            'pattern': 'solid',
            'pattern_color': [200, 50, 50],
            'accessory': 'none',
            'curiosity': 0.5,
            'energy': 0.5,
            'affection': 0.5,
            'shyness': 0.5,
            'base_hp': 20.0,
            'base_atk': 5.0,
            'base_spd': 5.0,
        }
        
        result = Roster._migrate_genome(genome_data)
        
        # Should clean up prefix and map correctly
        assert 'culture_expression' in result
        assert result['culture_expression'] == {'ember': 1.0}
