"""
Scene Manager — Lightweight State Machine for pygame Applications

Provides a Scene base class and SceneManager that runs a single pygame
event loop, delegating to the active scene's handle_events/update/render.

Extracted from the dgt_engine heartbeat pattern, stripped to essentials.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Dict, Any

import pygame
from loguru import logger

from src.shared.engine.base_system import BaseSystem, SystemStatus, SystemConfig
from src.shared.engine.system_clock import SystemClock, TimeMode

if TYPE_CHECKING:
    pass


class Scene(BaseSystem, ABC):
    """
    Abstract base class for all game scenes.
    Now inherits from BaseSystem for formalized lifecycle management.
    """

    def __init__(self, manager: SceneManager, **kwargs) -> None:
        # BaseSystem initialization
        super().__init__(SystemConfig(name=self.__class__.__name__))
        
        self.manager = manager
        self._kwargs = kwargs  # Stored for initialize -> on_enter
        self.next_scene: Optional[str] = None
        self.next_scene_kwargs: Dict[str, Any] = {}
        self.quit_requested: bool = False

    def request_scene(self, scene_name: str, **kwargs) -> None:
        """Request a transition to another scene after this frame."""
        self.next_scene = scene_name
        self.next_scene_kwargs = kwargs

    def request_quit(self) -> None:
        """Request application exit after this frame."""
        self.quit_requested = True

    # ---------------------------------------------------------------------------
    # BaseSystem Lifecycle Wrappers
    # ---------------------------------------------------------------------------
    def initialize(self) -> bool:
        """Formal initialization. Wraps legacy on_enter."""
        self.on_enter(**self._kwargs)
        return True

    def tick(self, delta_time: float) -> None:
        """Formal update. Wraps legacy update (converting seconds to ms)."""
        self.update(delta_time * 1000.0)

    def shutdown(self) -> None:
        """Formal cleanup. Wraps legacy on_exit."""
        self.on_exit()

    # ---------------------------------------------------------------------------
    # Legacy/Scene Interface (to be implemented by subclasses)
    # ---------------------------------------------------------------------------
    @abstractmethod
    def on_enter(self, **kwargs) -> None:
        """Called during initialize()."""
        pass

    @abstractmethod
    def on_exit(self) -> None:
        """Called during shutdown()."""
        pass

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Process pygame events for this scene."""
        pass

    @abstractmethod
    def update(self, dt_ms: float) -> None:
        """Update scene state. Called during tick()."""
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Render scene to the provided surface."""
        pass


class SceneManager:
    """
    Manages scene lifecycle and transitions in a single pygame window.

    Usage:
        manager = SceneManager(width=640, height=480, title="My Game")
        manager.register("overworld", OverworldScene)
        manager.register("battle", BattleScene)
        manager.run("overworld")  # Start with overworld
    """

    def __init__(self, width: int = 640, height: int = 480, title: str = "rpgCore", fps: int = 60):
        self.width = width
        self.height = height
        self.title = title
        self.fps = fps

        self._scenes: Dict[str, type] = {}
        self._active_scene: Optional[Scene] = None
        self._running = False
        
        # Session 021: Formal timing
        self.clock = SystemClock(target_fps=fps, mode=TimeMode.REAL_TIME)
        

    def register(self, name: str, scene_class: type) -> None:
        """Register a scene class by name."""
        self._scenes[name] = scene_class

    def switch_to(self, name: str, **kwargs) -> None:
        """Switch to a registered scene. Calls lifecycle methods."""
        if name not in self._scenes:
            raise ValueError(f"Unknown scene: {name}. Registered: {list(self._scenes.keys())}")

        if self._active_scene:
            self._active_scene.shutdown()
            self._active_scene.status = SystemStatus.STOPPED

        scene_class = self._scenes[name]
        self._active_scene = scene_class(self, **kwargs)
        
        if not self._active_scene.initialize():
            logger.error(f"Failed to initialize scene: {name}")
            self._running = False
        else:
            self._active_scene.status = SystemStatus.RUNNING

    def run(self, initial_scene: str, **kwargs) -> None:
        """Main loop. Initialize pygame, enter initial scene, and loop."""
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        
        # Internal raw clock for calculating elapsed time across frames
        raw_clock = pygame.time.Clock()

        self.switch_to(initial_scene, **kwargs)
        self._running = True

        while self._running:
            # 1. Update timing
            elapsed_ms = raw_clock.tick(self.fps)
            self.clock.update(elapsed_ms / 1000.0)
            dt = self.clock.delta_time

            events = pygame.event.get()

            # 2. Update active scene via tick() wrapper
            if self._active_scene and self._active_scene.is_running():
                self._active_scene.handle_events(events)
                self._active_scene.tick(dt)
                
                # 3. Render
                self._active_scene.render(screen)
                pygame.display.flip()

                # 4. Check for scene transition or quit
                if self._active_scene.quit_requested:
                    self._running = False
                elif self._active_scene.next_scene:
                    next_name = self._active_scene.next_scene
                    next_kwargs = self._active_scene.next_scene_kwargs
                    self.switch_to(next_name, **next_kwargs)

        if self._active_scene:
            self._active_scene.shutdown()
        pygame.quit()
