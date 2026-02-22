import os
import pytest
from src.apps.last_appointment.scenes.appointment_scene import AppointmentScene
from src.shared.engine.scene_manager import SceneManager

class DummyManager:
    width = 800
    height = 600

@pytest.fixture
def scene():
    # Make sure we don't try to initialize pygame displays in tests
    os.environ["PYTEST_CURRENT_TEST"] = "1"
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    manager = DummyManager()
    return AppointmentScene(manager)

def test_graph_loading(scene):
    scene.on_enter()
    assert scene.current_node is not None
    assert scene.current_node.node_id == "beat_1"
    # Beat 1 should have 5 responses
    assert len(scene.available_edges) == 5
    assert len(scene.graph.nodes) == 21

def test_stance_tracking_and_advancement(scene):
    scene.on_enter()
    
    # We shouldn't need a real pygame object, just mock the choices.
    # We can invoke make_choice directly on the graph or simulate the keys if we want.
    # It's easier to simulate the choice directly on the graph or call handle_events with a mock event
    class MockEvent:
        def __init__(self, key):
            import pygame
            self.type = pygame.KEYDOWN
            self.key = key
            
    import pygame
    
    # Press '1', which corresponds to K_1 and "PROFESSIONAL"
    events = [MockEvent(pygame.K_1)]
    scene.handle_events(events)
    
    # Should flag the stance and move to NPC_RESPONSE phase
    assert scene.state_tracker.get_flag("current_stance", "") == "PROFESSIONAL"
    assert scene.phase == "NPC_RESPONSE"
    
    # Simulate text reveal finishing
    scene.text_window.is_finished = True
    
    # Press any key to advance
    scene.handle_events([MockEvent(pygame.K_SPACE)])
    
    # Should advance to beat_2_pro
    assert scene.current_node.node_id == "beat_2_pro"
    assert scene.phase == "PROMPT"
    
    # beat_2_pro has 5 options. Let's pick 1 again (PROFESSIONAL), which leads to beat_3_pro
    events = [MockEvent(pygame.K_1)]
    scene.handle_events(events)
    
    # Beat 2's options do NOT have npc_response in the current JSON, so they advance immediately
    assert scene.current_node.node_id == "beat_3_pro"
    assert scene.phase == "PROMPT"

def test_invalid_key_does_not_advance(scene):
    scene.on_enter()
    
    class MockEvent:
        def __init__(self, key):
            import pygame
            self.type = pygame.KEYDOWN
            self.key = key
            
    import pygame
    
    # Press an invalid key like '9'
    events = [MockEvent(pygame.K_9)]
    scene.handle_events(events)
    
    # Should remain on beat_1
    assert scene.current_node.node_id == "beat_1"


def test_beat_4_loading_and_wildcard_routing(scene):
    """Verify that Beat 4 loads correctly and wildcards route effectively"""
    scene.on_enter()
    
    # Check that Beat 4 nodes exist
    stances = ["pro", "weary", "curious", "reluctant", "moved"]
    for stance in stances:
        node_id = f"beat_4_{stance}"
        assert node_id in scene.graph.nodes
        node = scene.graph.nodes[node_id]
        
        # Verify prompt
        assert node.text == 'The Client states: "You\'ve been doing this alone for a very long time."'
        
        # Verify 5 responses exist
        assert len(node.edges) == 5
        
    # Verify Wildcard routing across rivers (Index 4 is the Wildcard)
    # Professional wildcard -> Curious closing
    assert scene.graph.nodes["beat_4_pro"].edges[4].target_node == "end_curious"
    
    # Weary wildcard -> Moved closing
    assert scene.graph.nodes["beat_4_weary"].edges[4].target_node == "end_moved"
    
    # Curious wildcard -> Moved closing
    assert scene.graph.nodes["beat_4_curious"].edges[4].target_node == "end_moved"
    
    # Reluctant wildcard -> Moved closing
    assert scene.graph.nodes["beat_4_reluctant"].edges[4].target_node == "end_moved"
    
    # Moved wildcard -> Moved closing
    assert scene.graph.nodes["beat_4_moved"].edges[4].target_node == "end_moved"
