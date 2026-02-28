import pytest
import pygame
from unittest.mock import MagicMock
from src.apps.slime_breeder.scenes.team_scene import TeamScene
from src.shared.teams.roster import RosterSlime, TeamRole, Team
from src.shared.genetics.genome import SlimeGenome
from src.shared.ui.spec import SPEC_720

@pytest.fixture
def mock_manager():
    manager = MagicMock()
    manager.width = 1024
    manager.height = 768
    return manager

@pytest.fixture
def sample_roster():
    from src.shared.teams.roster import Roster
    roster = Roster()
    genome = SlimeGenome(
        shape="round", size="medium", base_color=(100, 200, 100),
        pattern="spotted", pattern_color=(50, 50, 50), accessory="none",
        curiosity=0.8, energy=0.2, affection=0.1, shyness=0.1
    )
    for i in range(5):
        rs = RosterSlime(slime_id=f"s{i}", name=f"Slime {i}", genome=genome)
        roster.add_slime(rs)
    return roster

def test_team_scene_initialization(mock_manager, sample_roster, monkeypatch):
    # Mock load_roster
    monkeypatch.setattr("src.apps.slime_breeder.scenes.team_scene.load_roster", lambda: sample_roster)
    monkeypatch.setattr("src.apps.slime_breeder.scenes.team_scene.save_roster", lambda r: None)
    
    scene = TeamScene(mock_manager, SPEC_720)
    scene.on_enter()
    
    assert scene.roster == sample_roster
    assert len(scene.dungeon_team.members) == 0
    assert len(scene.racing_team.members) == 0
    assert len(scene.ui_components) > 0 # Back button + panels + labels

def test_team_scene_assign_slime(mock_manager, sample_roster, monkeypatch):
    monkeypatch.setattr("src.apps.slime_breeder.scenes.team_scene.load_roster", lambda: sample_roster)
    monkeypatch.setattr("src.apps.slime_breeder.scenes.team_scene.save_roster", MagicMock())
    
    scene = TeamScene(mock_manager, SPEC_720)
    scene.on_enter()
    
    slime = sample_roster.slimes[0]
    scene._assign_to_dungeon(slime)
    
    assert len(scene.dungeon_team.members) == 1
    assert scene.dungeon_team.members[0] == slime

def test_team_scene_remove_slime(mock_manager, sample_roster, monkeypatch):
    monkeypatch.setattr("src.apps.slime_breeder.scenes.team_scene.load_roster", lambda: sample_roster)
    monkeypatch.setattr("src.apps.slime_breeder.scenes.team_scene.save_roster", MagicMock())
    
    scene = TeamScene(mock_manager, SPEC_720)
    scene.on_enter()
    
    # First assign a slime to dungeon team
    slime = sample_roster.slimes[0]
    scene._assign_to_dungeon(slime)
    
    # Then remove it
    scene._remove_from_dungeon(slime)
    
    assert len(scene.dungeon_team.members) == 0

def test_team_scene_back_to_garden(mock_manager, monkeypatch):
    monkeypatch.setattr("src.apps.slime_breeder.scenes.team_scene.load_roster", MagicMock())
    
    scene = TeamScene(mock_manager, SPEC_720)
    scene.on_enter()
    
    # Mock the request_scene method
    scene.request_scene = MagicMock()
    scene._back_to_garden()
    
    scene.request_scene.assert_called_once_with("garden")
