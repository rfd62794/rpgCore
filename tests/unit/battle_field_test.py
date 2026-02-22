import pytest
from src.apps.slime_clan.scenes.battle_field_scene import BattleFieldScene as BattleField, SquadToken
from src.apps.slime_clan.territorial_grid import TileState
import pygame

def test_battle_field_initialization():
    bf = BattleField("TestRegion", "NORMAL")
    assert bf.region_name == "TestRegion"
    assert bf.difficulty == "NORMAL"
    assert bf.blue_token.team == TileState.BLUE
    assert bf.red_token.team == TileState.RED
    assert bf.blue_token.col == 0
    assert bf.blue_token.row == 0
    assert bf.red_token.col == 9
    assert bf.red_token.row == 9
    
    # Needs to quit pygame after test initialize
    pygame.quit()

def test_collision_detection_adjacent():
    bf = BattleField("TestRegion", "NORMAL")
    bf.blue_token.col = 5
    bf.blue_token.row = 5
    
    # Top Adjacent
    bf.red_token.col = 5
    bf.red_token.row = 4
    # We mock _launch_auto_battle so it doesn't spin up a subprocess
    bf._launch_auto_battle = lambda: setattr(bf, 'mock_launched', True)
    assert bf._check_collision() is True
    assert bf.mock_launched is True
    
    # Left Adjacent
    bf.red_token.col = 4
    bf.red_token.row = 5
    assert bf._check_collision() is True
    
    # Diagonal (Not adjacent)
    bf.red_token.col = 6
    bf.red_token.row = 6
    assert bf._check_collision() is False
    
    pygame.quit()

def test_red_pathfinding_step():
    bf = BattleField("TestRegion", "NORMAL")
    bf.blue_token.col = 2
    bf.blue_token.row = 2
    
    bf.red_token.col = 5
    bf.red_token.row = 5
    
    # Red should step towards blue (Manhattan distance calculation favors vertical then horizontal in our simple grid, but either 4,5 or 5,4 is valid)
    bf._take_red_turn()
    
    dist_after = abs(bf.blue_token.col - bf.red_token.col) + abs(bf.blue_token.row - bf.red_token.row)
    assert dist_after < 6 # Initial dist was 3 + 3 = 6. After step it should be 5.
    
    pygame.quit()

def test_win_condition_reaches_base():
    bf = BattleField("TestRegion", "NORMAL")
    
    # Move blue to bottom right
    bf.blue_token.col = 8
    bf.blue_token.row = 8
    
    bf.update(16)
    
    assert bf.game_over is True
    assert bf.exit_code == 0
    
    pygame.quit()
