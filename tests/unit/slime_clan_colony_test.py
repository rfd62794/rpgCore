import pytest
from src.apps.slime_clan.colony import Colony, ColonyManager
from src.apps.slime_clan.auto_battle import SlimeUnit, TileState, Shape, Hat
from enum import Enum

class MockNodeType(Enum):
    TEST = "TEST"

def test_colony_initialization():
    colony = Colony(
        id="test_colony",
        name="Test Colony",
        x=100,
        y=100,
        coord=(1, 1),
        node_type=MockNodeType.TEST,
        connections=[]
    )
    assert colony.id == "test_colony"
    assert colony.population == 100
    assert colony.units == []

def test_colony_manager_tribal_generation():
    manager = ColonyManager(MockNodeType)
    manager.create_colony("ashfen", "Ashfen", 0, 0, (0, 0), MockNodeType.TEST, [], faction="CLAN_YELLOW")
    
    colony = manager.get_colony("ashfen")
    assert colony is not None
    assert len(colony.units) == 3
    for unit in colony.units:
        assert isinstance(unit, SlimeUnit)
        assert hasattr(unit, "sympathy")
        assert unit.sympathy == 20

def test_recruitment_logic_transfer():
    # Simulate the logic in app.py
    manager = ColonyManager(MockNodeType)
    manager.create_colony("ashfen", "Ashfen", 0, 0, (0, 0), MockNodeType.TEST, [], faction="CLAN_YELLOW")
    colony = manager.get_colony("ashfen")
    
    # Mock sympathy scores
    colony.units[0].sympathy = 30
    colony.units[1].sympathy = 50 # Highest
    colony.units[2].sympathy = 10
    
    target_unit = colony.units[1]
    name = target_unit.name
    
    # Logic from app.py
    selected_unit = max(colony.units, key=lambda u: getattr(u, "sympathy", 0))
    colony.units.remove(selected_unit)
    
    assert selected_unit == target_unit
    assert len(colony.units) == 2
    assert selected_unit.name == name

def test_colony_manager_iter():
    manager = ColonyManager(MockNodeType)
    manager.create_colony("c1", "C1", 0, 0, (0, 0), MockNodeType.TEST, [])
    manager.create_colony("c2", "C2", 1, 1, (1, 1), MockNodeType.TEST, [])
    
    ids = [cid for cid in manager]
    assert "c1" in ids
    assert "c2" in ids
    assert len(list(manager.values())) == 2
