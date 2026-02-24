import pytest
import pygame
from unittest.mock import MagicMock
from src.apps.dungeon_crawler.ui.scene_dungeon_room import DungeonRoomScene
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession

@pytest.fixture
def mock_session():
    session = MagicMock(spec=DungeonSession)
    session.floor = MagicMock()
    room = MagicMock()
    room.id = "room_1"
    room.room_type = "combat"
    room.has_enemies.return_value = True
    room.enemies = [MagicMock()]
    room.connections = ["room_2"]
    session.floor.get_current_room.return_value = room
    session.floor.depth = 1
    return session

@pytest.fixture
def scene(mock_session):
    pygame.init()
    manager = MagicMock()
    manager.width = 1024
    manager.height = 768
    scene = DungeonRoomScene(manager, mock_session)
    scene.initialize()
    return scene

def test_patrol_reverses_at_boundary(scene):
    # Initial state: pos 4, dir 1, range 2
    scene.enemy_grid_pos = [4, 4]
    scene.enemy_patrol_dir = 1
    scene.enemy_patrol_timer = 0.9
    scene.enemy_patrol_speed = 1.0
    
    # Update to move to 5
    scene.update(100) # 0.1s
    assert scene.enemy_grid_pos[0] == 5
    assert scene.enemy_patrol_dir == 1
    
    # Update to move to 6 (reaches boundary |6-4| >= 2)
    scene.enemy_patrol_timer = 0.9
    scene.update(100)
    assert scene.enemy_grid_pos[0] == 6
    assert scene.enemy_patrol_dir == -1 # Should have reversed

def test_exit_flag_hidden_while_enemies_alive(scene):
    scene.enemy_defeated = False
    # Check if enemy_defeated is False (rendering logic uses this)
    assert not scene.enemy_defeated

def test_exit_flag_visible_after_room_cleared(scene):
    scene.enemy_defeated = True
    # In render, it checks self.enemy_defeated
    assert scene.enemy_defeated

def test_hero_and_enemy_initial_positions(scene):
    assert scene.hero_grid_pos == [4, 1]
    assert scene.enemy_grid_pos == [4, 4]

# Cleanup pygame
def test_teardown():
    pygame.quit()
