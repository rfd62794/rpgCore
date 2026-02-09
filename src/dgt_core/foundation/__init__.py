"""
DGT Foundation - Tier 1 System Foundation

ADR 198: Foundation Import Strategy

This module provides the foundational types and base classes
that the entire DGT Platform depends on. All imports from
this module are safe and will not cause circular dependencies.
"""

from .types import Result, ValidationResult, TypeVar
from .base import BaseEngine, BaseRenderer, BaseStateManager

__all__ = [
    'Result',
    'ValidationResult', 
    'TypeVar',
    'BaseEngine',
    'BaseRenderer', 
    'BaseStateManager'
]
