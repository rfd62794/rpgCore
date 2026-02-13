"""
PyGame Compatibility Shim Verification Test
Tests that legacy UI logic works correctly with the Sovereign Layout System
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from dgt_core.engines.viewport.logical_viewport import LogicalViewport
from dgt_core.compat.pygame_shim import SovereignRect, SovereignColor, DGTDrawProxy, LegacyUIContext, create_legacy_context


def test_sovereign_rect_scaling():
    """Test that SovereignRect correctly scales legacy coordinates"""
    print("🔧 Testing SovereignRect Scaling")
    print("=" * 50)
    
    # Create viewport for different resolutions
    resolutions = [(160, 144), (800, 600), (1920, 1080)]
    
    # Test legacy coordinates (from breeding_panel.py)
    legacy_coords = [
        (50, 100, 200, 150),  # Parent slot 1
        (270, 100, 200, 150), # Parent slot 2  
        (10, 50, 120, 30),   # Breed button
        (20, 15, 200, 30),   # Money label
    ]
    
    for width, height in resolutions:
        print(f"\nResolution: {width}x{height}")
        viewport = LogicalViewport()
        viewport.set_physical_resolution((width, height))
        
        for x, y, w, h in legacy_coords:
            # Create SovereignRect with legacy coordinates
            sovereign_rect = SovereignRect(x, y, w, h, viewport)
            
            # Get physical rectangle
            physical_rect = sovereign_rect.get_physical_rect((width, height))
            
            print(f"  Legacy ({x:3},{y:3},{w:3},{h:3}) → Physical {physical_rect}")
            
            # Verify scaling is proportional
            expected_x = int((x / 800.0) * width)
            expected_y = int((y / 600.0) * height)
            expected_w = int((w / 800.0) * width)
            expected_h = int((h / 600.0) * height)
            
            tolerance = 2  # Allow small rounding differences
            assert abs(physical_rect[0] - expected_x) <= tolerance
            assert abs(physical_rect[1] - expected_y) <= tolerance
            assert abs(physical_rect[2] - expected_w) <= tolerance
            assert abs(physical_rect[3] - expected_h) <= tolerance
    
    print("✅ SovereignRect scaling verified")
    return True


def test_legacy_ui_context():
    """Test LegacyUIContext provides pygame-like interface"""
    print("\n🎮 Testing Legacy UI Context")
    print("=" * 50)
    
    # Create legacy context
    context = create_legacy_context((800, 600))
    
    # Test pygame.Rect creation
    rect1 = context.Rect(50, 100, 200, 150)
    print(f"Created rect: {rect1}")
    
    # Test pygame.Rect properties
    assert rect1.left == rect1.x
    assert rect1.right == rect1.x + rect1.width
    assert rect1.top == rect1.y
    assert rect1.bottom == rect1.y + rect1.height
    assert rect1.centerx == rect1.x + rect1.width / 2
    assert rect1.centery == rect1.y + rect1.height / 2
    print("✅ pygame.Rect properties working")
    
    # Test pygame.Rect methods
    moved_rect = rect1.move(10, 20)
    # Note: move operates on legacy coordinates, then converts to logical
    # So the logical position will be different from original + dx
    assert moved_rect.legacy_x == rect1.legacy_x + 10
    assert moved_rect.legacy_y == rect1.legacy_y + 20
    
    inflated_rect = rect1.inflate(20, 10)
    assert inflated_rect.width == rect1.width + 20
    assert inflated_rect.height == rect1.height + 10
    
    # Test collision detection
    assert rect1.collidepoint((100, 150))  # Point inside
    assert not rect1.collidepoint((0, 0))     # Point outside
    
    rect2 = context.Rect(60, 110, 200, 150)
    assert rect1.colliderect(rect2)  # Overlapping rectangles
    
    print("✅ pygame.Rect methods working")
    
    # Test pygame.Color creation
    color1 = context.Color(255, 0, 0)
    assert color1.r == 255
    assert color1.g == 0
    assert color1.b == 0
    assert tuple(color1) == (255, 0, 0, 255)
    print("✅ pygame.Color working")
    
    # Test theme access
    assert 'SELECTION_GLOW' in context.theme_colors
    assert 'PARENT_SLOT_OFFSET_X' in context.layout
    print("✅ Theme constants accessible")
    
    return True


def test_drawing_proxy():
    """Test that drawing proxy creates correct render packets"""
    print("\n🎨 Testing Drawing Proxy")
    print("=" * 50)
    
    # Create context for 160x144 (retro mode)
    context = create_legacy_context((160, 144))
    
    # Create some rectangles using legacy coordinates
    rect1 = context.Rect(10, 10, 50, 30)
    rect2 = context.Rect(70, 50, 80, 40)
    
    # Draw using legacy-style calls
    context.draw.rect(None, context.theme_colors['BREEDING_PANEL_BG'], rect1)
    context.draw.rect(None, context.theme_colors['SELECTION_GLOW'], rect2, 3)  # Border
    
    # Draw text
    context.draw.text(None, "BREED", context.theme_colors['BUTTON_TEXT_COLOR'], (20, 20), 12)
    
    # Draw circle
    context.draw.circle(None, context.theme_colors['BUTTON_NORMAL'], (100, 100), 10)
    
    # Get render packets
    frame_data = context.get_frame_data()
    render_packets = frame_data['render_packets']
    
    print(f"Generated {len(render_packets)} render packets")
    
    # Verify packet types and content
    packet_types = [packet['type'] for packet in render_packets]
    assert 'rectangle' in packet_types
    assert 'text' in packet_types
    assert 'circle' in packet_types
    
    # Check rectangle packets
    rect_packets = [p for p in render_packets if p['type'] == 'rectangle']
    assert len(rect_packets) >= 2
    
    for packet in rect_packets:
        assert 'rect' in packet
        assert 'color' in packet
        assert 'filled' in packet
    
    print("✅ Drawing proxy working correctly")
    return True


def test_legacy_logic_integration():
    """Test that extracted legacy logic works with shim"""
    print("\n🧬 Testing Legacy Logic Integration")
    print("=" * 50)
    
    # Import extracted logic
    from legacy_logic_extraction.breeding_logic import BreedingLogicExtractor, BreedingUIConstants
    
    # Create legacy context
    context = create_legacy_context((800, 600))
    
    # Create logic extractor
    extractor = BreedingLogicExtractor()
    
    # Test slot layout calculation with SovereignRect
    container_rect = context.Rect(20, 100, 760, 400)
    slots = extractor.calculate_slot_layout((container_rect.left, container_rect.top, 
                                           container_rect.width, container_rect.height))
    
    print(f"Calculated {len(slots)} breeding slots")
    
    # Verify slots are positioned correctly
    for i, slot_rect in enumerate(slots[:4]):  # Check first 4 slots
        x, y, w, h = slot_rect
        
        # Create SovereignRect to verify positioning
        sovereign_rect = context.Rect(x, y, w, h)
        physical_rect = sovereign_rect.get_physical_rect((800, 600))
        
        print(f"  Slot {i}: Legacy {slot_rect} → Physical {physical_rect}")
        
        # Verify slot is within container bounds
        assert x >= container_rect.left
        assert y >= container_rect.top
        assert x + w <= container_rect.right
        assert y + h <= container_rect.bottom
    
    # Test parent selection logic
    test_turtle = {'id': 'test_turtle_1', 'name': 'Test Turtle'}
    success = extractor.process_parent_selection(0, test_turtle)
    assert success
    assert len(extractor.selected_parents) == 1
    
    print("✅ Legacy logic integration working")
    return True


def test_cross_resolution_consistency():
    """Test that same legacy coordinates work across resolutions"""
    print("\n📱 Testing Cross-Resolution Consistency")
    print("=" * 50)
    
    # Test coordinates from breeding_panel.py
    test_coords = [
        (50, 100, 200, 150),  # Parent slot
        (10, 50, 120, 30),    # Breed button
        (20, 15, 200, 30),    # Money label
    ]
    
    resolutions = [(160, 144), (800, 600), (1920, 1080)]
    
    for x, y, w, h in test_coords:
        print(f"\nTesting coordinates ({x}, {y}, {w}, {h}):")
        
        # Store logical positions for comparison
        logical_positions = []
        
        for width, height in resolutions:
            context = create_legacy_context((width, height))
            rect = context.Rect(x, y, w, h)
            
            # Get logical position (should be same across resolutions)
            logical_x = rect.x
            logical_y = rect.y
            logical_w = rect.width
            logical_h = rect.height
            
            logical_positions.append((logical_x, logical_y, logical_w, logical_h))
            
            # Get physical position
            physical_rect = rect.get_physical_rect((width, height))
            print(f"  {width:4}x{height:<4} → Physical {physical_rect}")
        
        # Verify logical positions are consistent
        first_pos = logical_positions[0]
        for i, pos in enumerate(logical_positions[1:], 1):
            tolerance = 0.1
            assert abs(pos[0] - first_pos[0]) <= tolerance
            assert abs(pos[1] - first_pos[1]) <= tolerance
            assert abs(pos[2] - first_pos[2]) <= tolerance
            assert abs(pos[3] - first_pos[3]) <= tolerance
        
        print(f"  ✅ Logical positions consistent across resolutions")
    
    return True


def test_theme_export():
    """Test theme export functionality"""
    print("\n🎨 Testing Theme Export")
    print("=" * 50)
    
    # Create context and export theme
    context = create_legacy_context((800, 600))
    
    # Export to file
    theme_file = "test_theme.json"
    context.export_theme_to_json(theme_file)
    
    # Verify file was created and has content
    import json
    with open(theme_file, 'r') as f:
        theme_data = json.load(f)
    
    # Verify structure
    assert 'colors' in theme_data
    assert 'fonts' in theme_data
    assert 'layout' in theme_data
    
    # Verify key colors are present
    colors = theme_data['colors']
    assert 'SELECTION_GLOW' in colors
    assert 'BREEDING_PANEL_BG' in colors
    assert colors['SELECTION_GLOW'] == [255, 255, 0]
    
    # Verify layout constants
    layout = theme_data['layout']
    assert 'PARENT_SLOT_OFFSET_X' in layout
    assert layout['PARENT_SLOT_OFFSET_X'] == 50
    
    print(f"✅ Theme exported to {theme_file}")
    print(f"  Colors: {len(colors)}")
    print(f"  Fonts: {len(theme_data['fonts'])}")
    print(f"  Layout: {len(layout)}")
    
    # Cleanup
    import os
    os.remove(theme_file)
    
    return True


def main():
    """Run all PyGame shim verification tests"""
    print("🏆 PyGame Compatibility Shim Verification Suite")
    print("=" * 60)
    print("Testing Legacy UI Logic Bridge for DGT Platform")
    print()
    
    tests = [
        ("SovereignRect Scaling", test_sovereign_rect_scaling),
        ("Legacy UI Context", test_legacy_ui_context),
        ("Drawing Proxy", test_drawing_proxy),
        ("Legacy Logic Integration", test_legacy_logic_integration),
        ("Cross-Resolution Consistency", test_cross_resolution_consistency),
        ("Theme Export", test_theme_export),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"PyGame Shim Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PYGAME SHIM TESTS PASSED!")
        print("✅ Legacy UI Logic Bridge is FULLY OPERATIONAL")
        print("✅ pygame.Rect compatibility verified")
        print("✅ pygame.Color compatibility verified")
        print("✅ Drawing proxy working correctly")
        print("✅ Cross-resolution scaling perfect")
        print("✅ Legacy logic integration successful")
        print("\n🚀 READY FOR LEGACY UI MIGRATION! 🚀")
        print("\n📱 Legacy coordinates now work on:")
        print("   • Miyoo Mini (160x144)")
        print("   • Desktop (1920x1080)")
        print("   • Any resolution (adaptive)")
        print("\n🔧 The 'Ship of Theseus' problem is SOLVED!")
        return True
    else:
        print("❌ Some PyGame shim tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
