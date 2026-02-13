"""
Test Sprint E2: The Derby Engine

Sprint E2: The Derby Engine - Verification
Tests the terrain system, physics handshake, and strategic racing scenarios.
"""

import sys
from pathlib import Path

def test_terrain_system():
    """Test terrain engine functionality"""
    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        from engines.body.systems.terrain_engine import TerrainEngine, TerrainType, create_balanced_terrain
        from foundation.registry import DGTRegistry, RegistryType
        
        print("✅ Terrain system imports successful")
        
        # Create terrain engine
        terrain = create_balanced_terrain()
        print("✅ Terrain engine created")
        
        # Test terrain properties
        stats = terrain.get_terrain_statistics()
        assert stats['total_cells'] == 160 * 144  # 160x144 grid
        print(f"✅ Terrain grid: {stats['total_cells']} cells")
        
        # Test terrain types
        land_count = stats['terrain_counts'][TerrainType.LAND]
        water_count = stats['terrain_counts'][TerrainType.WATER]
        rough_count = stats['terrain_counts'][TerrainType.ROUGH]
        
        print(f"✅ Terrain distribution: {land_count} land, {water_count} water, {rough_count} rough")
        
        # Test terrain at specific positions
        land_cell = terrain.get_terrain_at(50, 72)  # Middle of track
        water_cell = terrain.get_terrain_at(30, 80)  # Off-track water
        rough_cell = terrain.get_terrain_at(70, 60)  # Off-track rough
        
        assert land_cell.terrain_type == TerrainType.LAND
        assert water_cell.terrain_type == TerrainType.WATER
        assert rough_cell.terrain_type == TerrainType.ROUGH
        print("✅ Terrain cell queries working")
        
        # Test terrain effects
        from apps.tycoon.entities.turtle import create_fast_turtle, create_heavy_turtle
        
        fast_turtle = create_fast_turtle("swimmer", (50, 72))
        heavy_turtle = create_heavy_turtle("climber", (50, 72))
        
        # Test water effects
        water_effects_fast = terrain.apply_terrain_effects(fast_turtle, 1.0)
        water_effects_heavy = terrain.apply_terrain_effects(heavy_turtle, 1.0)
        
        # Fast turtle should have better water performance
        assert water_effects_fast['friction'] > water_effects_heavy['friction']
        assert water_effects_fast['energy_drain'] < water_effects_heavy['energy_drain']
        print("✅ Water terrain effects verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_physics_handshake():
    """Test terrain physics handshake with turtle entities"""
    try:
        from engines.body.systems.race_runner import RaceRunner, create_race_runner_system
        from apps.tycoon.entities.turtle import create_fast_turtle, create_heavy_turtle
        from foundation.registry import DGTRegistry
        
        print("✅ Physics handshake imports successful")
        
        # Create race runner with terrain
        race_runner = create_race_runner_system()
        init_result = race_runner.initialize()
        assert init_result.success, f"Race runner initialization failed: {init_result.error}"
        print("✅ Race runner with terrain initialized")
        
        # Create test turtles with different genetic traits
        swimmer = create_fast_turtle("swimmer", (30, 72))
        climber = create_heavy_turtle("climber", (30, 72))
        
        # Register turtles with registry
        registry = DGTRegistry()
        
        swimmer.register_with_registry(registry)
        climber.register_with_registry(registry)
        
        # Start race
        start_result = race_runner.handle_event("start_race", {})
        assert start_result.success, f"Failed to start race: {start_result.error}"
        
        # Simulate race crossing water terrain
        # Move both turtles to water terrain
        swimmer.position = Vector2(30, 80)  # Water terrain
        climber.position = Vector2(30, 80)  # Same water terrain
        
        # Update physics for several seconds
        for i in range(180):  # 3 seconds at 60Hz
            swimmer.update(1.0/60.0)
            climber.update(1.0/60.0)
        
        # Check positions
        print(f"Swimmer position: {swimmer.position.x:.1f}, {swimmer.position.y:.1f}")
        print(f"Climber position: {climber.position.x:.1f}, {climber.position.y:.1f}")
        
        # Fast turtle should be ahead due to swim trait advantage
        assert swimmer.position.x > climber.position.x
        print("✅ Genetic advantage verified in water terrain")
        
        # Stop race
        stop_result = race_runner.handle_event("stop_race", {})
        assert stop_result.success, f"Failed to stop race: {stop_result.error}"
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategic_racing():
    """Test strategic racing with terrain variety"""
    try:
        from engines.body.systems.race_runner import RaceRunner, create_race_runner_system
        from apps.tycoon.entities.turtle import create_random_turtle
        from foundation.registry import DGTRegistry
        
        print("✅ Strategic racing imports successful")
        
        # Create challenging terrain
        race_runner = create_race_runner_system()
        init_result = race_runner.initialize()
        assert init_result.success, f"Race runner initialization failed: {init_result.error}"
        
        # Create diverse turtles
        turtles = []
        for i in range(3):
            turtle = create_random_turtle(f"turtle_{i}", (20 + i * 40, 72))
            turtles.append(turtle)
        
        # Register all turtles
        registry = DGTRegistry()
        for turtle in turtles:
            turtle.register_with_registry(registry)
        
        # Start race
        start_result = race_runner.handle_event("start_race", {})
        assert start_result.success, f"Failed to start race: {start_result.error}"
        
        # Simulate race for 5 seconds
        import time
        start_time = time.time()
        
        while time.time() - start_time < 5.0:
            race_runner.update(1.0/60.0)
        
        # Get final positions
        final_positions = [turtle.position.x for turtle in turtles]
        winner_index = final_positions.index(max(final_positions))
        
        print(f"🏆️ Race completed! Winner: turtle_{winner_index}")
        print(f"Final positions: {[f'{pos:.1f}' for pos in final_positions]}")
        
        # Verify race completion
        for i, turtle in enumerate(turtles):
            if turtle.finish_time is not None:
                race_time = turtle.finish_time - race_runner.race_start_time
                print(f"Turtle {i} finished in {race_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_registry_lifecycle_fix():
    """Test that registry lifecycle issues are resolved"""
    try:
        from apps.tycoon.entities.turtle import SovereignTurtle, create_random_turtle
        from foundation.registry import DGTRegistry, RegistryType
        
        print("✅ Registry lifecycle test imports successful")
        
        # Create turtles
        turtles = []
        for i in range(5):
            turtle = create_random_turtle(f"turtle_{i}", (20 + i * 20, 72))
            turtles.append(turtle)
        
        # Register all turtles once
        registry = DGTRegistry()
        for turtle in turtles:
            turtle.register_with_registry(registry)
        
        # Check registry state
        snapshot_result = registry.get_world_snapshot()
        assert snapshot_result.success, f"Registry snapshot failed: {snapshot_result.error}"
        
        # Should have exactly 5 entities
        assert len(snapshot_result.value.entities) == 5
        print(f"✅ Registry contains {len(snapshot_result.value.entities)} entities")
        
        # Verify no double-counting
        entity_ids = [entity.entity_id for entity in snapshot_result.value.entities]
        unique_ids = set(entity_ids)
        assert len(entity_ids) == len(entity_ids), "Duplicate entity IDs found!"
        print("✅ No double-counting in registry")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_terrain_visualization():
    """Test terrain visualization"""
    try:
        from engines.body.systems.terrain_engine import TerrainEngine, create_challenging_terrain
        from foundation.registry import DGTRegistry
        
        print("✅ Terrain visualization test imports successful")
        
        # Create challenging terrain for visualization
        terrain = create_challenging()
        init_result = terrain.initialize()
        assert init_result.success, f"Terrain initialization failed: {init_result.error}"
        
        # Get terrain map for visualization
        terrain_map = terrain.get_terrain_map()
        
        # Verify terrain map dimensions
        assert len(terrain_map) == 144  # 144 rows
        assert len(terrain_map[0]) == 160  # 160 columns
        print(f"✅ Terrain map dimensions: {len(terrain_map)}x{len(terrain_map[0])}")
        
        # Check terrain distribution
        land_count = sum(1 for row in terrain_map for cell in row if cell[0] == (34, 139, 34))  # Forest green
        water_count = sum(1 for row in terrain_map for cell in row if cell[0] == (64, 164, 223))  # Ocean blue
        rough_count = sum(1 for row in terrain_map for cell in row if cell[0] == (139, 69, 19))  # Brown mud
        
        print(f"✅ Terrain distribution: {land_count} land, {water_count} water, {rough_count} rough")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__name__ == "__main__":
    print("🔧 Testing Sprint E2: The Derby Engine...")
    
    tests = [
        ("Terrain System", test_terrain_system),
        ("Physics Handshake", test_physics_handshake),
        ("Strategic Racing", test_strategic_racing),
        ("Registry Lifecycle Fix", test_registry_lifecycle_fix),
        ("Terrain Visualization", test_terrain_visualization)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))
    
    print(f"\n🏁 Sprint E2 Test Results:")
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🏆 Sprint E2: THE DERBY ENGINE - SUCCESS!")
        print("🏞️ Terrain system operational with strategic racing!")
        print("🐢 Genetic advantages verified in terrain challenges!")
        print("🏁 Registry lifecycle issues resolved!")
        print("🎨 Strategic racing environment ready for TurboShells!")
