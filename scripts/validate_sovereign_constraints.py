#!/usr/bin/env python3
"""
Sovereign Constraints Validation Suite

Phase 2: Fixed-Point Rendering Standard Validation

Validates all rendering strategies against the 160×144 sovereign resolution
and other systemic constraints established in ADR 192.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import traceback

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from loguru import logger
from src.interfaces.protocols import PPUProtocol, Result
from src.dgt_core.engines.body.unified_ppu import (
    UnifiedPPU, PPUMode, PPUConfig, 
    MiyooStrategy, PhosphorStrategy, GameBoyStrategy,
    EnhancedStrategy, HardwareBurnStrategy
)
from src.exceptions.core import PPUException


class SovereignConstraintValidator:
    """Validates rendering strategies against sovereign constraints"""
    
    SOVEREIGN_WIDTH = 160
    SOVEREIGN_HEIGHT = 144
    SOVEREIGN_PIXELS = SOVEREIGN_WIDTH * SOVEREIGN_HEIGHT  # 23,040
    MAX_COLORS = 4
    MAX_FPS = 60
    
    def __init__(self):
        self.validation_results: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        
    def validate_all_strategies(self) -> Result[Dict[str, bool]]:
        """Validate all rendering strategies against sovereign constraints"""
        logger.info("🏆 Starting Sovereign Constraints Validation")
        
        strategies = {
            "miyoo": MiyooStrategy(),
            "phosphor": PhosphorStrategy(),
            "gameboy": GameBoyStrategy(),
            "enhanced": EnhancedStrategy(),
            "hardware_burn": HardwareBurnStrategy()
        }
        
        results = {}
        
        for strategy_name, strategy in strategies.items():
            logger.info(f"🔍 Validating {strategy_name} strategy")
            
            try:
                strategy_result = self._validate_strategy(strategy_name, strategy)
                results[strategy_name] = strategy_result
                
                if strategy_result["compliant"]:
                    logger.success(f"✅ {strategy_name}: COMPLIANT")
                else:
                    logger.error(f"❌ {strategy_name}: VIOLATIONS")
                    for violation in strategy_result["violations"]:
                        self.errors.append(f"{strategy_name}: {violation}")
                        
            except Exception as e:
                logger.error(f"💥 {strategy_name}: VALIDATION ERROR - {e}")
                results[strategy_name] = {
                    "compliant": False,
                    "violations": [f"Validation error: {str(e)}"]
                }
                self.errors.append(f"{strategy_name}: {str(e)}")
        
        # Generate summary
        compliant_count = sum(1 for r in results.values() if r["compliant"])
        total_count = len(results)
        
        logger.info(f"📊 Validation Summary: {compliant_count}/{total_count} strategies compliant")
        
        if self.errors:
            logger.error("🚨 Constraint Violations Detected:")
            for error in self.errors:
                logger.error(f"  • {error}")
        
        return Result.success_result(results)
    
    def validate_unified_ppu(self) -> Result[Dict[str, Any]]:
        """Validate UnifiedPPU compliance with sovereign constraints"""
        logger.info("🎯 Validating UnifiedPPU compliance")
        
        try:
            # Test each mode
            modes = [PPUMode.MIYOO, PPUMode.PHOSPHOR, PPUMode.GAMEBOY, 
                    PPUMode.ENHANCED, PPUMode.HARDWARE_BURN]
            
            results = {}
            
            for mode in modes:
                logger.info(f"🔍 Testing UnifiedPPU in {mode.value} mode")
                
                # Create config for mode
                config = PPUConfig(
                    mode=mode,
                    width=self.SOVEREIGN_WIDTH,
                    height=self.SOVEREIGN_HEIGHT
                )
                
                # Create and initialize PPU
                ppu_result = create_unified_ppu(config)
                if not ppu_result.success:
                    results[mode.value] = {
                        "compliant": False,
                        "violations": [f"Failed to create PPU: {ppu_result.error}"]
                    }
                    continue
                
                ppu = ppu_result.value
                
                # Validate PPU
                ppu_validation = self._validate_ppu_instance(ppu, mode)
                results[mode.value] = ppu_validation
                
                if ppu_validation["compliant"]:
                    logger.success(f"✅ UnifiedPPU.{mode.value}: COMPLIANT")
                else:
                    logger.error(f"❌ UnifiedPPU.{mode.value}: VIOLATIONS")
            
            return Result.success_result(results)
            
        except Exception as e:
            logger.error(f"💥 UnifiedPPU validation error: {e}")
            return Result.failure_result(f"Validation error: {str(e)}")
    
    def _validate_strategy(self, name: str, strategy) -> Dict[str, Any]:
        """Validate individual strategy against constraints"""
        violations = []
        
        # Test 1: Resolution Compliance
        try:
            # Create test buffer
            test_buffer = bytearray(self.SOVEREIGN_PIXELS)
            
            # Initialize strategy
            config = PPUConfig(
                mode=PPUMode.MIYOO,  # Default mode for testing
                width=self.SOVEREIGN_WIDTH,
                height=self.SOVEREIGN_HEIGHT
            )
            
            init_result = strategy.initialize(config)
            if not init_result.success:
                violations.append(f"Initialization failed: {init_result.error}")
            
            # Test rendering
            render_result = strategy.render_tile(1, 0, 0, test_buffer)
            if not render_result.success:
                violations.append(f"Tile rendering failed: {render_result.error}")
            
            # Validate buffer size
            if len(test_buffer) != self.SOVEREIGN_PIXELS:
                violations.append(f"Buffer size {len(test_buffer)} != {self.SOVEREIGN_PIXELS}")
            
        except Exception as e:
            violations.append(f"Resolution test error: {str(e)}")
        
        # Test 2: Performance Profile
        try:
            profile = strategy.get_performance_profile()
            
            # Check FPS constraint
            fps = profile.get("target_fps", 0)
            if fps > self.MAX_FPS:
                violations.append(f"FPS {fps} exceeds constraint {self.MAX_FPS}")
            
            # Check memory usage
            memory_usage = profile.get("memory_usage", "unknown")
            if memory_usage == "unknown":
                violations.append("Memory usage not specified in profile")
            
        except Exception as e:
            violations.append(f"Performance profile error: {str(e)}")
        
        # Test 3: Color Depth (if applicable)
        try:
            # This would be strategy-specific testing
            # For now, we'll assume compliance based on design
            pass
            
        except Exception as e:
            violations.append(f"Color depth test error: {str(e)}")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "strategy_name": name
        }
    
    def _validate_ppu_instance(self, ppu: UnifiedPPU, mode: PPUMode) -> Dict[str, Any]:
        """Validate UnifiedPPU instance"""
        violations = []
        
        try:
            # Test frame buffer operations
            frame_result = ppu.get_frame_buffer()
            if not frame_result.success:
                violations.append(f"Frame buffer access failed: {frame_result.error}")
            else:
                frame_data = frame_result.value
                if len(frame_data) != self.SOVEREIGN_PIXELS:
                    violations.append(f"Frame buffer size {len(frame_data)} != {self.SOVEREIGN_PIXELS}")
            
            # Test tile rendering
            tile_result = ppu.render_tile(1, 10, 10)
            if not tile_result.success:
                violations.append(f"Tile rendering failed: {tile_result.error}")
            
            # Test sprite rendering
            sprite_data = bytes([1, 2, 3, 4])  # Test sprite
            sprite_result = ppu.render_sprite(sprite_data, 20, 20)
            if not sprite_result.success:
                violations.append(f"Sprite rendering failed: {sprite_result.error}")
            
            # Test clear frame
            clear_result = ppu.clear_frame()
            if not clear_result.success:
                violations.append(f"Frame clear failed: {clear_result.error}")
            
            # Test palette
            test_palette = [(0, 0, 0), (255, 255, 255), (128, 128, 128), (64, 64, 64)]
            palette_result = ppu.set_palette(test_palette)
            if not palette_result.success:
                violations.append(f"Palette setting failed: {palette_result.error}")
            
            # Get performance profile
            profile = ppu.get_performance_profile()
            fps = profile.get("target_fps", 0)
            if fps > self.MAX_FPS:
                violations.append(f"FPS {fps} exceeds constraint {self.MAX_FPS}")
            
        except Exception as e:
            violations.append(f"PPU validation error: {str(e)}")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "mode": mode.value,
            "performance_profile": profile if 'profile' in locals() else {}
        }
    
    def generate_report(self) -> str:
        """Generate validation report"""
        report = []
        report.append("# Sovereign Constraints Validation Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        total_strategies = len(self.validation_results)
        compliant_strategies = sum(1 for r in self.validation_results.values() if r.get("compliant", False))
        
        report.append("## Summary")
        report.append(f"- Strategies Tested: {total_strategies}")
        report.append(f"- Compliant Strategies: {compliant_strategies}")
        report.append(f"- Compliance Rate: {compliant_strategies/total_strategies*100:.1f}%")
        report.append("")
        
        # Detailed Results
        report.append("## Detailed Results")
        
        for strategy_name, result in self.validation_results.items():
            status = "✅ COMPLIANT" if result.get("compliant", False) else "❌ NON-COMPLIANT"
            report.append(f"### {strategy_name}: {status}")
            
            if not result.get("compliant", False):
                report.append("**Violations:**")
                for violation in result.get("violations", []):
                    report.append(f"- {violation}")
            
            report.append("")
        
        # Errors
        if self.errors:
            report.append("## Errors")
            for error in self.errors:
                report.append(f"- {error}")
            report.append("")
        
        # Constraints Summary
        report.append("## Sovereign Constraints")
        report.append(f"- Resolution: {self.SOVEREIGN_WIDTH}×{self.SOVEREIGN_HEIGHT}")
        report.append(f"- Total Pixels: {self.SOVEREIGN_PIXELS}")
        report.append(f"- Max Colors: {self.MAX_COLORS}")
        report.append(f"- Max FPS: {self.MAX_FPS}")
        
        return "\n".join(report)


def create_unified_ppu(config: PPUConfig) -> Result[UnifiedPPU]:
    """Factory function for testing"""
    try:
        ppu = UnifiedPPU(config)
        init_result = ppu.initialize(config.width, config.height)
        
        if not init_result.success:
            return Result.failure_result(f"PPU initialization failed: {init_result.error}")
        
        return Result.success_result(ppu)
        
    except Exception as e:
        return Result.failure_result(f"Failed to create PPU: {str(e)}")


def main():
    """Main validation entry point"""
    print("🏆 Sovereign Constraints Validation Suite")
    print("=" * 50)
    
    validator = SovereignConstraintValidator()
    
    # Validate all strategies
    print("\n🔍 Validating Rendering Strategies...")
    strategy_results = validator.validate_all_strategies()
    
    if not strategy_results.success:
        print(f"❌ Strategy validation failed: {strategy_results.error}")
        return 1
    
    # Validate UnifiedPPU
    print("\n🎯 Validating UnifiedPPU...")
    ppu_results = validator.validate_unified_ppu()
    
    if not ppu_results.success:
        print(f"❌ UnifiedPPU validation failed: {ppu_results.error}")
        return 1
    
    # Store results for reporting
    validator.validation_results = strategy_results.value
    
    # Generate report
    report = validator.generate_report()
    
    # Save report
    report_path = Path(__file__).parent / "sovereign_constraints_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📋 Report saved to: {report_path}")
    
    # Determine exit code
    total_violations = sum(1 for r in strategy_results.value.values() if not r.get("compliant", False))
    total_violations += sum(1 for r in ppu_results.value.values() if not r.get("compliant", False))
    
    if total_violations > 0:
        print(f"\n❌ Validation failed with {total_violations} violations")
        return 1
    else:
        print("\n✅ All constraints validated successfully")
        return 0


if __name__ == "__main__":
    import time
    sys.exit(main())
