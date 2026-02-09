"""
Core Constants - System Configuration and Magic Numbers
LEGACY SHIM - Delegates to src.dgt_core.kernel.constants

All system constants, configuration values, and magic numbers
centralized for maintainability and consistency.
"""
import warnings
import sys

# Ensure the source module is available
try:
    # Shim to the new DGT Kernel
    from src.dgt_core.kernel.constants import *
    
    # Verify critical constants are available
    required_constants = [
        'EMERGENCY_SAVE_PREFIX',
        'LOG_LEVEL_DEFAULT', 
        'SOVEREIGN_WIDTH',
        'SOVEREIGN_HEIGHT'
    ]
    
    for const in required_constants:
        if const not in globals():
            raise ImportError(f"Missing required constant: {const}")
    
except ImportError as e:
    # Fallback - provide minimal constants to prevent system failure
    warnings.warn(f"Core constants shim failed: {e}", RuntimeWarning)
    
    # Minimal fallback constants
    EMERGENCY_SAVE_PREFIX = "emergency_save"
    LOG_LEVEL_DEFAULT = "INFO"
    SOVEREIGN_WIDTH = 160
    SOVEREIGN_HEIGHT = 144
