"""
Body Systems - Entity Component System (ECS)

Entity management and component-based architecture for game objects.
Includes collision, physics, projectiles, effects, and spawning systems.

Provides:
- EntityManager: Entity lifecycle and component storage
- CollisionSystem: Collision detection and response
- PhysicsSystem: Physics simulation and movement
- ProjectileSystem: Projectile lifetime and impact
- FractureSystem: Object destruction and debris
- WaveSpawner: Enemy/entity wave generation
- StatusManager: Effect and status tracking
- TerrainEngine: Environment interaction
- FXSystem: Particle effects and visual effects
"""

from game_engine.systems.body.entity_manager import (
    EntityManager,
    Entity,
    EntityComponent,
    ObjectPool,
    SpaceEntity,
    RPGEntity,
    TycoonEntity,
)

__all__ = [
    # Core ECS
    "EntityManager",
    "Entity",
    "EntityComponent",
    "ObjectPool",
    # Specialized Entities
    "SpaceEntity",
    "RPGEntity",
    "TycoonEntity",
]
