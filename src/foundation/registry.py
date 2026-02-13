"""
DGT Foundation Registry - Centralized Asset & Entity Management

Sprint A: Foundation Hardening - Registry Pattern Implementation

Provides single source of truth for all loaded Assets, Genomes, and Active Entities.
Eliminates state leakage and provides centralized lifecycle management.
"""

from typing import Dict, List, Optional, Any, Set, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
from pathlib import Path

from ..types import Result, ValidationResult
from ..base import ComponentConfig

T = TypeVar('T')


class RegistryType(Enum):
    """Registry category types"""
    ASSET = "asset"
    GENOME = "genome"
    ENTITY = "entity"
    COMPONENT = "component"
    SYSTEM = "system"


@dataclass
class RegistryEntry(Generic[T]):
    """Registry entry with metadata"""
    item: T
    registry_type: RegistryType
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def touch(self) -> None:
        """Update last access time and count"""
        self.last_accessed = time.time()
        self.access_count += 1


class DGTRegistry:
    """
    Centralized registry for all DGT Platform assets and entities.
    
    Thread-safe singleton implementation with lifecycle management.
    Provides high-discoverability and prevents state leakage.
    """
    
    _instance: Optional['DGTRegistry'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'DGTRegistry':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        # Lazy logger initialization to prevent circular dependency
        self._logger = None
        
        # Type-specific registries
        self._registries: Dict[RegistryType, Dict[str, RegistryEntry[Any]]] = {
            registry_type: {} for registry_type in RegistryType
        }
        
        # Registry metadata
        self._creation_time = time.time()
        self._total_operations = 0
        self._lock = threading.RLock()
        
        self._get_logger().info("🔧 DGT Registry initialized")
    
    def _get_logger(self):
        """Lazy logger initialization"""
        if self._logger is None:
            try:
                from .utils.logger import get_logger_manager
                self._logger = get_logger_manager().get_component_logger("registry")
            except Exception:
                # Fallback to basic logging
                import logging
                self._logger = logging.getLogger("registry")
        return self._logger
    
    def register(self, item_id: str, item: Any, registry_type: RegistryType, 
                 metadata: Optional[Dict[str, Any]] = None) -> Result[None]:
        """
        Register an item in the appropriate registry.
        
        Args:
            item_id: Unique identifier for the item
            item: The item to register
            registry_type: Type of registry
            metadata: Additional metadata
            
        Returns:
            Result indicating success or failure
        """
        with self._lock:
            self._total_operations += 1
            
            # Validate input
            if not item_id or not isinstance(item_id, str):
                return Result.failure_result("Invalid item_id: must be non-empty string")
            
            if not isinstance(registry_type, RegistryType):
                return Result.failure_result("Invalid registry_type: must be RegistryType enum")
            
            # Check for existing registration
            registry = self._registries[registry_type]
            if item_id in registry:
                self._logger.warning(f"Overwriting existing registration: {item_id}")
            
            # Create entry
            entry = RegistryEntry(
                item=item,
                registry_type=registry_type,
                metadata=metadata or {}
            )
            
            # Register
            registry[item_id] = entry
            
            self._logger.debug(f"Registered {registry_type.value}: {item_id}")
            return Result.success_result(None)
    
    def get(self, item_id: str, registry_type: RegistryType) -> Result[Optional[Any]]:
        """
        Retrieve an item from the registry.
        
        Args:
            item_id: Unique identifier
            registry_type: Type of registry
            
        Returns:
            Result containing the item or None if not found
        """
        with self._lock:
            self._total_operations += 1
            
            registry = self._registries[registry_type]
            entry = registry.get(item_id)
            
            if entry is None:
                return Result.success_result(None)
            
            # Update access statistics
            entry.touch()
            self._logger.debug(f"Retrieved {registry_type.value}: {item_id}")
            
            return Result.success_result(entry.item)
    
    def unregister(self, item_id: str, registry_type: RegistryType) -> Result[bool]:
        """
        Remove an item from the registry.
        
        Args:
            item_id: Unique identifier
            registry_type: Type of registry
            
        Returns:
            Result indicating if item was removed
        """
        with self._lock:
            self._total_operations += 1
            
            registry = self._registries[registry_type]
            removed = registry.pop(item_id, None)
            
            if removed:
                self._logger.debug(f"Unregistered {registry_type.value}: {item_id}")
                return Result.success_result(True)
            
            return Result.success_result(False)
    
    def list_items(self, registry_type: RegistryType) -> Result[List[str]]:
        """
        List all item IDs in a registry.
        
        Args:
            registry_type: Type of registry
            
        Returns:
            Result containing list of item IDs
        """
        with self._lock:
            self._total_operations += 1
            
            registry = self._registries[registry_type]
            items = list(registry.keys())
            
            return Result.success_result(items)
    
    def get_registry_stats(self, registry_type: Optional[RegistryType] = None) -> Result[Dict[str, Any]]:
        """
        Get comprehensive registry statistics.
        
        Args:
            registry_type: Specific registry type or None for all
            
        Returns:
            Result containing statistics
        """
        with self._lock:
            self._total_operations += 1
            
            if registry_type:
                stats = self._get_single_registry_stats(registry_type)
            else:
                stats = {
                    "total_registrations": sum(len(reg) for reg in self._registries.values()),
                    "total_operations": self._total_operations,
                    "uptime_seconds": time.time() - self._creation_time,
                    "registry_breakdown": {}
                }
                
                for reg_type in RegistryType:
                    stats["registry_breakdown"][reg_type.value] = self._get_single_registry_stats(reg_type)
            
            return Result.success_result(stats)
    
    def _get_single_registry_stats(self, registry_type: RegistryType) -> Dict[str, Any]:
        """Get statistics for a single registry"""
        registry = self._registries[registry_type]
        
        if not registry:
            return {
                "count": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "most_accessed": None
            }
        
        entries = list(registry.values())
        
        # Find oldest and newest entries
        oldest = min(entries, key=lambda e: e.created_at)
        newest = max(entries, key=lambda e: e.created_at)
        most_accessed = max(entries, key=lambda e: e.access_count)
        
        return {
            "count": len(registry),
            "oldest_entry": {
                "id": next(k for k, v in registry.items() if v == oldest),
                "created_at": oldest.created_at
            },
            "newest_entry": {
                "id": next(k for k, v in registry.items() if v == newest),
                "created_at": newest.created_at
            },
            "most_accessed": {
                "id": next(k for k, v in registry.items() if v == most_accessed),
                "access_count": most_accessed.access_count
            }
        }
    
    def clear_registry(self, registry_type: RegistryType) -> Result[int]:
        """
        Clear all items from a registry.
        
        Args:
            registry_type: Type of registry to clear
            
        Returns:
            Result containing number of items cleared
        """
        with self._lock:
            self._total_operations += 1
            
            registry = self._registries[registry_type]
            count = len(registry)
            registry.clear()
            
            self._logger.info(f"Cleared {count} items from {registry_type.value} registry")
            return Result.success_result(count)
    
    def validate_registry_integrity(self) -> Result[ValidationResult]:
        """
        Validate registry integrity and consistency.
        
        Returns:
            Result containing validation outcome
        """
        with self._lock:
            self._total_operations += 1
            
            issues = []
            
            # Check for duplicate IDs across registries
            all_ids: Set[str] = set()
            duplicates: Set[str] = set()
            
            for registry_type, registry in self._registries.items():
                for item_id in registry.keys():
                    if item_id in all_ids:
                        duplicates.add(item_id)
                    all_ids.add(item_id)
            
            if duplicates:
                issues.append(f"Duplicate IDs found: {duplicates}")
            
            # Check for empty metadata where required
            for registry_type, registry in self._registries.items():
                for item_id, entry in registry.items():
                    if not entry.metadata and registry_type in [RegistryType.ASSET, RegistryType.GENOME]:
                        issues.append(f"Missing metadata for {registry_type.value}: {item_id}")
            
            if issues:
                return Result.failure_result(
                    f"Registry validation failed: {'; '.join(issues)}",
                    ValidationResult.SYSTEM_ERROR
                )
            
            return Result.success_result(ValidationResult.VALID)


# === GLOBAL REGISTRY ACCESS ===

def get_dgt_registry() -> DGTRegistry:
    """Get the global DGT Registry instance"""
    return DGTRegistry()


# === CONVENIENCE FUNCTIONS ===

def register_asset(asset_id: str, asset: Any, metadata: Optional[Dict[str, Any]] = None) -> Result[None]:
    """Register an asset in the global registry"""
    return get_dgt_registry().register(asset_id, asset, RegistryType.ASSET, metadata)


def register_genome(genome_id: str, genome: Any, metadata: Optional[Dict[str, Any]] = None) -> Result[None]:
    """Register a genome in the global registry"""
    return get_dgt_registry().register(genome_id, genome, RegistryType.GENOME, metadata)


def register_entity(entity_id: str, entity: Any, metadata: Optional[Dict[str, Any]] = None) -> Result[None]:
    """Register an entity in the global registry"""
    return get_dgt_registry().register(entity_id, entity, RegistryType.ENTITY, metadata)


def get_asset(asset_id: str) -> Result[Optional[Any]]:
    """Get an asset from the global registry"""
    return get_dgt_registry().get(asset_id, RegistryType.ASSET)


def get_genome(genome_id: str) -> Result[Optional[Any]]:
    """Get a genome from the global registry"""
    return get_dgt_registry().get(genome_id, RegistryType.GENOME)


def get_entity(entity_id: str) -> Result[Optional[Any]]:
    """Get an entity from the global registry"""
    return get_dgt_registry().get(entity_id, RegistryType.ENTITY)


# === EXPORTS ===

__all__ = [
    'RegistryType',
    'RegistryEntry',
    'DGTRegistry',
    'get_dgt_registry',
    'register_asset',
    'register_genome', 
    'register_entity',
    'get_asset',
    'get_genome',
    'get_entity'
]
