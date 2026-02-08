"""
DGT View Package - Unified UI/UX Layer
ADR 163: Unified View Layer Architecture
"""

from .cli import dashboard, logger_config
from .graphics import legacy_adapter
from .terminal import inspector

__all__ = [
    # CLI components
    'dashboard',
    'logger_config',
    
    # Graphics components
    'legacy_adapter',
    
    # Terminal components
    'inspector'
]
