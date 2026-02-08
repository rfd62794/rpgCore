#!/usr/bin/env python3
"""
Launch Asset Ingestor SOLID - ADR 104: Production-Ready Asset Pipeline
Test the refactored DGT Asset Ingestor with SOLID architecture
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from tools.asset_ingestor_refactored import create_asset_ingestor_solid
from tools.optimized_image_processor import OptimizedImageProcessor


def create_sample_spritesheet_optimized():
    """Create a sample spritesheet using optimized processor"""
    processor = OptimizedImageProcessor(enable_profiling=True)
    
    # Create a larger, more complex spritesheet for testing
    spritesheet = processor.create_sample_spritesheet_vectorized(
        width=128, 
        height=128, 
        tile_size=16
    )
    
    return spritesheet, processor


def main():
    """Main entry point for SOLID asset ingestor"""
    print("=== DGT Asset Ingestor SOLID Architecture ===")
    print("🏗️  Initializing SOLID components...")
    
    # Create optimized sample spritesheet
    print("🎨 Creating optimized sample spritesheet...")
    spritesheet, processor = create_sample_spritesheet_optimized()
    
    # Save sample spritesheet
    sample_path = Path("sample_spritesheet_solid.png")
    spritesheet.save(sample_path)
    
    print(f"✅ Created optimized sample spritesheet: {sample_path}")
    
    # Show performance summary
    if processor.enable_profiling:
        summary = processor.get_performance_summary()
        print(f"📊 Performance Summary:")
        print(f"   Total operations: {summary['total_operations']}")
        for op_name, stats in summary['operations'].items():
            print(f"   {op_name}: {stats['count']} ops, "
                  f"{stats['avg_duration_ms']:.2f}ms avg")
    
    print("🚀 Starting SOLID Asset Ingestor...")
    
    # Launch SOLID ingestor
    ingestor = create_asset_ingestor_solid()
    
    # Auto-load the sample spritesheet
    ingestor.controller.spritesheet_path = sample_path
    ingestor.controller.spritesheet_image = spritesheet
    ingestor.controller.tile_size = 16
    
    # Update UI
    ingestor.ui.update_file_label(f"Loaded: {sample_path.name}")
    ingestor.ui.update_status("SOLID spritesheet loaded successfully")
    
    # Display spritesheet
    ingestor.controller._display_spritesheet()
    
    print("🏗️  SOLID Asset Ingestor ready!")
    print("📋 SOLID Architecture Features:")
    print("  ✅ Separation of Concerns (UI, Controller, Processor, Exporter)")
    print("  ✅ Pydantic v2 Data Validation")
    print("  ✅ Comprehensive Error Handling & Recovery")
    print("  ✅ Type-Safe Asset Models")
    print("  ✅ Vectorized Image Processing (numpy)")
    print("  ✅ Performance Profiling & Metrics")
    print("  ✅ SOLID Design Principles")
    print("")
    print("🎮 Instructions:")
    print("  1. Click '✂️ Slice Grid' to harvest all sprites with vectorization")
    print("  2. Select individual sprites with mouse drag")
    print("  3. Click '🎯 Bake Selection' to process with validation")
    print("  4. Click '📝 Generate Meta' to see validated YAML structure")
    print("  5. Click '💾 Export All' to save with error recovery")
    print("  6. Toggle '⚫ Grayscale Mode' for optimized conversion")
    print("  7. Use '🔍 Zoom In/Out' with vectorized resizing")
    print("")
    print("🔧 Architecture Benefits:")
    print("  • Single Responsibility Principle")
    print("  • Open/Closed Principle")
    print("  • Liskov Substitution Principle")
    print("  • Interface Segregation Principle")
    print("  • Dependency Inversion Principle")
    print("  • Type Safety & Validation")
    print("  • Error Resilience & Recovery")
    print("  • Performance Optimization")
    
    # Run the ingestor
    ingestor.run()


if __name__ == "__main__":
    main()
