import pytest
from src.shared.racing.race_engine import RaceEngine
from src.shared.racing.race_track import generate_track, get_terrain_at
from src.shared.teams.roster import RosterSlime
from src.shared.genetics.genome import SlimeGenome
from src.shared.genetics.cultural_base import CulturalBase

def test_race_track_terrain():
    track = ["grass", "water", "rock"]
    # SEGMENT_LENGTH = 10
    assert get_terrain_at(track, 5) == "grass"
    assert get_terrain_at(track, 15) == "water"
    assert get_terrain_at(track, 25) == "rock"
    assert get_terrain_at(track, 100) == "rock" # clamp

def test_race_engine_simulation():
    # Setup test slimes
    s1 = RosterSlime("s1", "Light", SlimeGenome(
        shape="round", size="small", base_color=(100, 100, 100),
        pattern="solid", pattern_color=(0,0,0), accessory="none",
        curiosity=0.5, energy=1.0, affection=0.5, shyness=0.1,
        cultural_base=CulturalBase.MOSS # Moss has speed modifier 1.3
    ), level=1)
    
    s2 = RosterSlime("s2", "Heavy", SlimeGenome(
        shape="cubic", size="massive", base_color=(100, 100, 100),
        pattern="solid", pattern_color=(0,0,0), accessory="none",
        curiosity=0.5, energy=0.1, affection=0.5, shyness=0.1,
        cultural_base=CulturalBase.CRYSTAL # Crystal has speed modifier 0.7
    ), level=1)
    
    track = ["grass"] * 100
    engine = RaceEngine([s1, s2], track, length=100)
    
    # Tick simulation
    for _ in range(100):
        engine.tick(0.1)
    
    # With new mass mechanics, light slime should be faster due to rapid jumping
    # Heavy slime jumps further but much slower
    assert engine.participants[0].distance >= engine.participants[1].distance
    
    # Run until finish
    for _ in range(1000):
        engine.tick(0.1)
        if engine.is_finished(): break
        
    assert engine.is_finished()
    assert engine.participants[0].finished  # Light slime wins
    assert engine.participants[0].rank == 1

def test_terrain_influence():
    s = RosterSlime("s", "Racer", SlimeGenome(
        shape="round", size="medium", base_color=(100, 100, 100),
        pattern="solid", pattern_color=(0,0,0), accessory="none",
        curiosity=0.5, energy=0.5, affection=0.5, shyness=0.5
    ), level=1)
    
    # Grass track
    engine_g = RaceEngine([s], ["grass"] * 10, length=50)
    engine_g.tick(1.0)
    dist_grass = engine_g.participants[0].distance
    
    # Water track
    engine_w = RaceEngine([s], ["water"] * 10, length=50)
    engine_w.tick(1.0)
    dist_water = engine_w.participants[0].distance
    
    assert dist_grass > dist_water
