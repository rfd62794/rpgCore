"""
Scene Manager — Lightweight State Machine for pygame Applications

Provides a Scene base class and SceneManager that runs a single pygame
event loop, delegating to the active scene's handle_events/update/render.

Extracted from the dgt_engine heartbeat pattern, stripped to essentials.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from typing import Dict, Any


class Scene(ABC):
    """
    Abstract base class for all game scenes.

    Every scene implements four lifecycle methods:
    - on_enter(**kwargs): called when scene becomes active
    - on_exit(): called when scene is deactivated  
    - handle_events(events): process pygame events
    - update(dt_ms): update game state
    - render(surface): draw to the shared surface

    Scenes signal transitions by setting self.next_scene.
    """

    def __init__(self, manager: SceneManager) -> None:
        self.manager = manager
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

    @abstractmethod
    def on_enter(self, **kwargs) -> None:
        """Called when this scene becomes active. Use kwargs for data passing."""
        pass

    @abstractmethod
    def on_exit(self) -> None:
        """Called when this scene is deactivated. Clean up resources."""
        pass

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Process pygame events for this scene."""
        pass

    @abstractmethod
    def update(self, dt_ms: float) -> None:
        """Update scene state. dt_ms is milliseconds since last frame."""
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

    def register(self, name: str, scene_class: type) -> None:
        """Register a scene class by name."""
        self._scenes[name] = scene_class

    def switch_to(self, name: str, **kwargs) -> None:
        """Switch to a registered scene. Calls on_exit/on_enter."""
        if name not in self._scenes:
            raise ValueError(f"Unknown scene: {name}. Registered: {list(self._scenes.keys())}")

        if self._active_scene:
            self._active_scene.on_exit()

        scene_class = self._scenes[name]
        self._active_scene = scene_class(self)
        self._active_scene.on_enter(**kwargs)

    def run(self, initial_scene: str, **kwargs) -> None:
        """Main loop. Initialize pygame, enter initial scene, and loop."""
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        clock = pygame.time.Clock()

        self.switch_to(initial_scene, **kwargs)
        self._running = True

        while self._running:
            dt_ms = clock.tick(self.fps)
            events = pygame.event.get()

            # Let the active scene process
            self._active_scene.handle_events(events)
            self._active_scene.update(dt_ms)
            self._active_scene.render(screen)
            pygame.display.flip()

            # Check for scene transition or quit
            if self._active_scene.quit_requested:
                self._running = False
            elif self._active_scene.next_scene:
                next_name = self._active_scene.next_scene
                next_kwargs = self._active_scene.next_scene_kwargs
                self.switch_to(next_name, **next_kwargs)

        if self._active_scene:
            self._active_scene.on_exit()
        pygame.quit()
