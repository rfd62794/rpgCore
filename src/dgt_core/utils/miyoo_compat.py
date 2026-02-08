"""
DGT Platform Miyoo Mini Plus Compatibility Layer
Handles 90-degree screen rotation and hardware-specific optimizations
"""

import os
import sys
from typing import Tuple, Optional
from loguru import logger


class MiyooCompat:
    """Miyoo Mini Plus hardware compatibility layer"""
    
    # Miyoo Mini Plus specifications
    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 480
    ROTATION = 90  # Miyoo Mini Plus rotates screen 90 degrees
    
    # Memory constraints
    MAX_MEMORY_MB = 256  # Miyoo Mini Plus max memory
    TARGET_MEMORY_MB = 128  # Target memory usage
    
    def __init__(self):
        self.is_miyoo = self._detect_miyoo_hardware()
        self.rotation_offset = self.ROTATION if self.is_miyoo else 0
        
    def _detect_miyoo_hardware(self) -> bool:
        """Detect if running on Miyoo Mini Plus hardware"""
        try:
            # Check for Miyoo-specific environment variables
            if os.environ.get('MIYOO_MODEL'):
                return True
            
            # Check for Miyoo-specific file paths
            miyoo_paths = [
                '/opt/miyoo',
                '/etc/miyoo-release',
                '/usr/miyoo'
            ]
            
            for path in miyoo_paths:
                if os.path.exists(path):
                    return True
            
            # Check for ARM architecture (Miyoo uses ARM)
            if sys.platform.startswith('linux') and 'arm' in os.uname().get('machine', '').lower():
                return True
                
        except Exception:
            pass
            
        return False
    
    def get_screen_dimensions(self) -> Tuple[int, int]:
        """Get effective screen dimensions accounting for rotation"""
        if self.rotation_offset == 90:
            return self.SCREEN_HEIGHT, self.SCREEN_WIDTH
        else:
            return self.SCREEN_WIDTH, self.SCREEN_HEIGHT
    
    def get_memory_constraints(self) -> dict:
        """Get memory constraints for current hardware"""
        if self.is_miyoo:
            return {
                'max_memory_mb': self.MAX_MEMORY_MB,
                'target_memory_mb': self.TARGET_MEMORY_MB,
                'hardware': 'Miyoo Mini Plus'
            }
        else:
            return {
                'max_memory_mb': 8192,  # 8GB typical desktop
                'target_memory_mb': 1024,  # 1GB target
                'hardware': 'Desktop'
            }
    
    def adjust_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Adjust coordinates for screen rotation"""
        if self.rotation_offset == 90:
            # Rotate 90 degrees clockwise: (x, y) -> (y, width - x)
            width, height = self.get_screen_dimensions()
            return y, width - x
        else:
            return x, y
    
    def get_optimal_settings(self) -> dict:
        """Get optimal settings for Miyoo Mini Plus"""
        if self.is_miyoo:
            return {
                'resolution': (self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
                'fps_target': 30,  # Lower FPS for handheld
                'particle_count': 50,  # Reduced particles
                'max_ships': 4,  # Smaller fleet sizes
                'enable_shadows': False,  # Disable shadows for performance
                'enable_post_processing': False,  # Disable post-processing
                'texture_quality': 'low',
                'enable_vsync': True,
                'memory_limit_mb': self.TARGET_MEMORY_MB
            }
        else:
            return {
                'resolution': (1280, 720),  # Desktop resolution
                'fps_target': 60,  # Desktop FPS
                'particle_count': 200,  # More particles
                'max_ships': 8,  # Larger fleet sizes
                'enable_shadows': True,  # Enable shadows
                'enable_post_processing': True,  # Enable post-processing
                'texture_quality': 'high',
                'enable_vsync': True,
                'memory_limit_mb': 1024
            }
    
    def log_hardware_info(self) -> None:
        """Log hardware detection information"""
        if self.is_miyoo:
            logger.info("🎮 Miyoo Mini Plus hardware detected")
            logger.info(f"📱 Screen: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT} (rotated {self.rotation_offset}°)")
            logger.info(f"💾 Memory: {self.TARGET_MEMORY_MB}MB target / {self.MAX_MEMORY_MB}MB max")
        else:
            logger.info("🖥️ Desktop hardware detected")
            logger.info("📱 Using desktop settings")
    
    def validate_environment(self) -> bool:
        """Validate environment for Miyoo compatibility"""
        if self.is_miyoo:
            # Check Python version
            if sys.version_info < (3, 12):
                logger.error("❌ Miyoo Mini Plus requires Python 3.12+")
                return False
            
            # Check available memory
            try:
                import psutil
                available_memory = psutil.virtual_memory().available // (1024 * 1024)
                if available_memory < self.TARGET_MEMORY_MB:
                    logger.warning(f"⚠️ Low memory available: {available_memory}MB")
                    logger.warning(f"⚠️ Target: {self.TARGET_MEMORY_MB}MB")
            except ImportError:
                logger.warning("⚠️ psutil not available, cannot check memory")
            
            # Check screen resolution
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()
                
                if (screen_width, screen_height) != (self.SCREEN_WIDTH, self.SCREEN_HEIGHT):
                    logger.warning(f"⚠️ Unexpected resolution: {screen_width}x{screen_height}")
                    logger.warning(f"⚠️ Expected: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT}")
                root.destroy()
            except Exception as e:
                logger.warning(f"⚠️ Cannot check screen resolution: {e}")
        
        return True


# Global compatibility instance
miyoo_compat = MiyooCompat()


def get_hardware_settings() -> dict:
    """Get hardware-specific settings"""
    return miyoo_compat.get_optimal_settings()


def adjust_for_miyoo(x: int, y: int) -> Tuple[int, int]:
    """Adjust coordinates for Miyoo Mini Plus rotation"""
    return miyoo_compat.adjust_coordinates(x, y)


def is_miyoo_hardware() -> bool:
    """Check if running on Miyoo Mini Plus"""
    return miyoo_compat.is_miyoo


def validate_miyoo_environment() -> bool:
    """Validate Miyoo Mini Plus environment"""
    return miyoo_compat.validate_environment()


if __name__ == "__main__":
    # Test Miyoo compatibility
    miyoo_compat.log_hardware_info()
    
    print("🎮 Miyoo Mini Plus Compatibility Test")
    print(f"Hardware detected: {'Miyoo Mini Plus' if miyoo_compat.is_miyoo else 'Desktop'}")
    print(f"Screen dimensions: {miyoo_compat.get_screen_dimensions()}")
    print(f"Memory constraints: {miyoo_compat.get_memory_constraints()}")
    print(f"Environment valid: {miyoo_compat.validate_environment()}")
