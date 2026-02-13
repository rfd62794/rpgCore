"""
Foundation Tier
Shared utilities, constants, and base classes.
"""

import sys
from pathlib import Path

# ADR 215: Python Version Check (Relaxed for 3.14 compatibility)
if sys.version_info < (3, 12, 0):
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    raise RuntimeError(
        f"DGT Platform requires Python 3.12.x or newer. Current version: {current_version}\n"
        "Please upgrade your Python environment."
    )
        "\n"
        "  # Linux/macOS\n"
        "  python3.12 -m venv .venv\n"
        "  source .venv/bin/activate"
    )

# Import version manager for advanced usage
from ..tools.python_version_manager import PythonVersionManager, enforce_python_312

# Export convenience function
__all__ = ["PythonVersionManager", "enforce_python_312"]
