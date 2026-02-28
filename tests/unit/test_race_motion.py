import pytest
from src.shared.racing.race_engine import RaceEngine, RaceParticipant
from src.shared.teams.roster import RosterSlime
from src.shared.genetics.inheritance import generate_random

def test_race_participant_acceleration():
    slime = RosterSlime(slime_id="test", name="Speedy", genome=generate_random(), level=1)
    p = RaceParticipant(slime)
    
    assert p.velocity == 0
    p.update(0.1, "grass")
    assert p.velocity > 0
    
    v1 = p.velocity
    p.update(0.1, "grass")
    assert p.velocity > v1 # Still accelerating

def test_terrain_impact_on_velocity():
    slime = RosterSlime(slime_id="test", name="Racer", genome=generate_random(), level=1)
    
    # Grass vs Water
    p_grass = RaceParticipant(slime)
    p_water = RaceParticipant(slime)
    
    p_grass.update(1.0, "grass")
    p_water.update(1.0, "water")
    
    assert p_grass.velocity > p_water.velocity
    assert p_grass.distance > p_water.distance

def test_drag_limits_terminal_velocity():
    slime = RosterSlime(slime_id="test", name="Racer", genome=generate_random(), level=1)
    p = RaceParticipant(slime)
    
    # Update for a long time
    for _ in range(500):
        p.update(0.016, "grass")
        
    last_v = p.velocity
    p.update(0.016, "grass")
    
    # Should be close to terminal velocity (accel balancing drag)
    assert abs(p.velocity - last_v) < 0.1
