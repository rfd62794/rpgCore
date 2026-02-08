"""
Core Constants - System Configuration and Magic Numbers
LEGACY SHIM - Delegates to src.dgt_core.kernel.constants

All system constants, configuration values, and magic numbers
centralized for maintainability and consistency.
"""
import warnings

# Shim to the new DGT Kernel
from src.dgt_core.kernel.constants import *

# Optional: Add a subtle warning if needed for debugging, but silent for now to keep logs clean
# warnings.warn("Using legacy core.constants shim", DeprecationWarning, stacklevel=2)
