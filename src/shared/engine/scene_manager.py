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

from src.shared.ui.spec import UISpec, SPEC_720

class Scene(BaseSystem, ABC):
    """
    Abstract base class for all game scenes, driven by UISpec.
    """

    def __init__(self, manager: SceneManager, spec: UISpec, **kwargs) -> None:
        # BaseSystem initialization
        super().__init__(SystemConfig(name=self.__class__.__name__))
        
        self.manager = manager
        self.spec = spec
        self._kwargs = kwargs
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
        """Formal initialization."""
        self.on_enter()
        return True

    def tick(self, delta_time: float) -> None:
        """Formal update (delta_time in seconds)."""
        self.update(delta_time)

    def shutdown(self) -> None:
        """Formal cleanup."""
        self.on_exit()

    # ---------------------------------------------------------------------------
    # Standard Scene Interface
    # ---------------------------------------------------------------------------
    def on_enter(self) -> None:
        """Optional: Called when entering the scene."""
        pass

    def on_exit(self) -> None:
        """Optional: Called when exiting the scene."""
        pass

    def on_resume(self, **kwargs) -> None:
        """Optional: Called when resuming the scene after a pop."""
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update scene state (dt in seconds)."""
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Render scene to the provided surface."""
        pass


class SceneManager:
    """
    Manages scene lifecycle and transitions in a single pygame window.
    """

    def __init__(self, width: int = 1280, height: int = 720, title: str = "rpgCore", fps: int = 60, spec: Optional[UISpec] = None):
        self.width = width
        self.height = height
        self.title = title
        self.fps = fps
        self.spec = spec or SPEC_720

        self._scenes: Dict[str, type] = {}
        self._active_scene: Optional[Scene] = None
        self._scene_stack: List[Scene] = []
        self._running = False
        
        self.clock = SystemClock(target_fps=fps, mode=TimeMode.REAL_TIME)

    def register(self, name: str, scene_class: type) -> None:
        """Register a scene class by name."""
        self._scenes[name] = scene_class

    def switch_to(self, name: str, **kwargs) -> None:
        """Switch to a registered scene. Calls lifecycle methods."""
        if name not in self._scenes:
            raise ValueError(f"Unknown scene: {name}")

        if self._active_scene:
            self._active_scene.shutdown()
            self._active_scene.status = SystemStatus.STOPPED

        scene_class = self._scenes[name]
        logger.info(f"Switching to scene: {name}")
        logger.info(f"Scene class: {scene_class}")
        logger.info(f"Kwargs: {kwargs}")
        self._active_scene = scene_class(self, self.spec, **kwargs)
        
        if not self._active_scene.initialize():
            logger.error(f"Failed to initialize scene: {name}")
            self._running = False
        else:
            self._active_scene.status = SystemStatus.RUNNING

    def push(self, name: str, **kwargs) -> None:
        """Pause current scene and push a new one onto the stack."""
        if name not in self._scenes:
            raise ValueError(f"Unknown scene: {name}")

        if self._active_scene:
            logger.info(f"Pausing scene: {self._active_scene.config.name}")
            self._active_scene.status = SystemStatus.PAUSED
            self._scene_stack.append(self._active_scene)

        scene_class = self._scenes[name]
        logger.info(f"Pushing scene: {name}")
        self._active_scene = scene_class(self, self.spec, **kwargs)
        
        if not self._active_scene.initialize():
            logger.error(f"Failed to initialize pushed scene: {name}")
            self._running = False
        else:
            self._active_scene.status = SystemStatus.RUNNING

    def pop(self, **kwargs) -> None:
        """Shutdown current scene and resume the previous one from the stack."""
        if not self._scene_stack:
            logger.warning("Attempted to pop from empty scene stack")
            return

        if self._active_scene:
            logger.info(f"Popping scene: {self._active_scene.config.name}")
            self._active_scene.shutdown()
            self._active_scene.status = SystemStatus.STOPPED

        self._active_scene = self._scene_stack.pop()
        logger.info(f"Resuming scene: {self._active_scene.config.name}")
        self._active_scene.status = SystemStatus.RUNNING
        self._active_scene.on_resume(**kwargs)

    def run(self, initial_scene: str, **kwargs) -> None:
        """Main loop."""
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        
        raw_clock = pygame.time.Clock()

        self.switch_to(initial_scene, **kwargs)
        self._running = True

        while self._running:
            elapsed_ms = raw_clock.tick(self.fps)
            self.clock.update(elapsed_ms / 1000.0)
            dt = self.clock.delta_time

            events = pygame.event.get()

            if self._active_scene and self._active_scene.is_running():
                # Loop through events and pass individually
                for event in events:
                    if event.type == pygame.QUIT:
                        self._running = False
                    self._active_scene.handle_event(event)
                
                self._active_scene.tick(dt)
                self._active_scene.render(screen)
                pygame.display.flip()

                if self._active_scene.quit_requested:
                    self._running = False
                elif self._active_scene.next_scene:
                    next_name = self._active_scene.next_scene
                    next_kwargs = self._active_scene.next_scene_kwargs
                    self.switch_to(next_name, **next_kwargs)

        if self._active_scene:
            self._active_scene.shutdown()
        pygame.quit()
