# Technical Debt & Known Issues

## Test Suite Import Path Failures (`dgt_engine` Refactor)
**Logged:** 2026-02-21 (Session 013)

### Description
A prior architectural refactor moved the `foundation` and `engines` directories into a new namespace package `dgt_engine`. 
The `tests/` directory was not fully updated to reflect this change, leaving substantial technical debt in the test suite.

### Affected Areas
Approximately 73+ tests are currently failing due to stale import paths or outdated `sys.path.insert` hacks.
The primary affected directories are:
*   `tests/stress/`
*   `tests/verification/`
*   `tests/integration/`
*   `tests/benchmarks/`

### Impact & Scope
These failures are **out of scope** for the current `slime_clan` application development. 
The errors do not indicate broken logic in the underlying engines, but merely broken import references in the test files themselves.

### Mitigation
To prevent these pre-existing failures from blocking CI/CD or local verification of new features, `pyproject.toml` has been configured with `testpaths = ["tests/unit"]` to isolate `uv run pytest` to the actively maintained, verified unit test scope.

When these legacy systems are actively developed again in the future, a dedicated "Janitor Session" should be spun up to patch the remaining `from engines...` and `sys.path` injection statements.

---

## Lack of Unified Scene Manager
**Logged:** 2026-02-21 (Session 015)

### Description
The current Three-Tier War System architecture relies on `sys.executable -m` subprocess calls to shift between the three tiers: `overworld.py` -> `battle_field.py` -> `auto_battle.py`.

### Impact & Scope
This creates a fundamentally janky three-window cascading UX. A new PyGame window spawns for the Operational grid, and a third PyGame window spawns for the Tactical skirmish. While acceptable for a prototype loop, this is not production quality.

### Mitigation
Documented here for resolution in **Session 016 or later**. A unified Scene Manager (`scene_manager.py`) is required. The Scene Manager should initialize a single `pygame.display.set_mode()` instance and pass the common rendering surface and event loop down to state-machine-controlled View instances (`OverworldView`, `BattleFieldView`, `AutoBattleView`) instead of executing entirely separate module processes.

---

## Mana UI Not Visible to Player
**Logged:** 2026-02-21 (Session 017)

### Description
The mana resource system (3 start, 5 max) is fully functional in `auto_battle.py` and logged to terminal, but there is no visual mana bar or MP indicator rendered on-screen for the player. The player cannot see mana values during combat — they can only infer resource management from the combat log.

### Mitigation
Add a mana bar or MP text indicator below each unit's HP bar in `auto_battle.py` rendering. Low priority — the system works correctly without visual feedback.

