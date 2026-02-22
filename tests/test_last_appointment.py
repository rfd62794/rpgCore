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
    assert len(scene.graph.nodes) == 5

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
    
    # Should advance to beat_2
    assert scene.current_node.node_id == "beat_2"
    assert scene.phase == "PROMPT"
    
    # Moving back to beat 1 from beat 2 requires pressing K_1 again
    events = [MockEvent(pygame.K_1)]
    scene.handle_events(events)
    
    # Beat 2's option has NO npc_response, so it advances immediately
    assert scene.current_node.node_id == "beat_1"
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
