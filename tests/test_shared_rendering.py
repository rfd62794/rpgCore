import os

def test_pygame_renderer_initialization():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    from src.shared.rendering.pygame_renderer import PyGameRenderer
    
    renderer = PyGameRenderer(width=100, height=100)
    assert renderer.initialize() is True
    assert renderer.screen is not None
    renderer.shutdown()

def test_render_entities():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    from src.shared.rendering.pygame_renderer import PyGameRenderer
    
    renderer = PyGameRenderer(width=100, height=100)
    renderer.initialize()
    
    entities = [
        {"type": "circle", "x": 50, "y": 50, "radius": 5, "color": (255, 255, 255)}
    ]
    
    renderer.clear((0, 0, 0))
    renderer.render_entities(entities)
    renderer.present()
    
    renderer.shutdown()
    assert True
