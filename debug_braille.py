import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

import time
from unittest.mock import Mock
from ui.render_passes import RenderPassRegistry, RenderContext, RenderPassType
from ui.render_passes.braille_radar import BrailleRadarPass

# Test just the Braille radar
registry = RenderPassRegistry()
radar = BrailleRadarPass()
registry.register_pass(radar)

# Simple mock
mock_game_state = Mock()
mock_position = Mock()
mock_position.x = 10.0
mock_position.y = 10.0
mock_game_state.position = mock_position

mock_ledger = Mock()
mock_ledger.get_chunk.return_value = Mock(tags=[])

context = RenderContext(
    game_state=mock_game_state,
    world_ledger=mock_ledger,
    viewport_bounds=(0, 0, 100, 100),
    current_time=time.time(),
    frame_count=1
)

try:
    result = radar.render(context)
    print('SUCCESS: Braille radar rendered')
    print(f'Result type: {type(result)}')
    print(f'Content length: {len(result.content)}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
