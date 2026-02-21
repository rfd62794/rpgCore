# Scene Manager — Architecture Reference

## Overview

The Scene Manager provides a single-window state machine for the Slime Clan application. Instead of spawning separate pygame processes per game tier, all scenes share one `pygame.display` surface and transition via `request_scene()`.

## Scene Interface Contract

Every scene must implement these methods:

```python
class MyScene(Scene):
    def on_enter(self, **kwargs) -> None:
        """Initialize state. Receive data from the previous scene via kwargs."""

    def on_exit(self) -> None:
        """Clean up. Called before the next scene's on_enter."""

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Process input events for this frame."""

    def update(self, dt_ms: float) -> None:
        """Advance game logic. dt_ms = milliseconds since last frame."""

    def render(self, surface: pygame.Surface) -> None:
        """Draw to the shared surface. Do NOT call pygame.display.flip()."""
```

## Scene Transitions

| Method | Effect |
|---|---|
| `self.request_scene("name", **kwargs)` | Transition to another scene after this frame |
| `self.request_quit()` | Exit the application after this frame |

Data flows between scenes via `kwargs`. For example, returning from a battle:
```python
self.request_scene("overworld", nodes=self.nodes, game_over=None)
```

## Registered Scenes

| Name | Class | Status | Purpose |
|---|---|---|---|
| `overworld` | `OverworldScene` | ✅ Migrated | Strategic node map, battle launches |
| `battle_field` | `BattleFieldScene` | 🔲 019B | Tactical grid movement, squad collision |
| `auto_battle` | `AutoBattleScene` | 🔲 019B | Turn-based combat resolution |

## Future Scenes

| Name | Purpose | Session |
|---|---|---|
| `squad_loadout` | Pre-battle composition selection | 020 |
| `recruitment` | Slime recruitment / roster management | Future |
| `ship_status` | Ship repair progress / departure readiness | Future |

## Source Files

- **Scene Manager:** `src/shared/engine/scene_manager.py`
- **Application:** `src/apps/slime_clan/app.py`
- **Launcher:** `run_overworld.py`
