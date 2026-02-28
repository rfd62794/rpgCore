import pytest
import pygame
from src.shared.ui.spec import SPEC_720
from src.shared.ui.button import Button
from src.shared.ui.label import Label
from src.shared.ui.panel import Panel

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    yield
    pygame.quit()

def test_button_variants():
    rect = pygame.Rect(0, 0, 100, 40)
    btn_p = Button("Primary", rect, lambda: None, SPEC_720, variant="primary")
    btn_d = Button("Danger", rect, lambda: None, SPEC_720, variant="danger")
    
    # Primary should have a background color from spec
    assert btn_p.bg_color == SPEC_720.color_primary
    assert btn_d.bg_color == SPEC_720.color_danger

def test_label_standardization():
    label = Label("Test", (10, 10), SPEC_720, size="lg", color=(255, 0, 0))
    assert label.font_size == SPEC_720.font_size_lg
    assert label.color == (255, 0, 0)

def test_panel_variants():
    rect = pygame.Rect(0, 0, 100, 100)
    panel = Panel(rect, SPEC_720, variant="card")
    assert panel.bg_color == SPEC_720.color_surface_alt
