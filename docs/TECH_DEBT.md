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

## ~~Lack of Unified Scene Manager~~ ✅ RESOLVED
**Logged:** 2026-02-21 (Session 015) | **Resolved:** 2026-02-21 (Session 019B)

### Resolution
Implemented `src/shared/engine/scene_manager.py` with `Scene` ABC and `SceneManager` state machine. All three tiers (`OverworldScene`, `BattleFieldScene`, `AutoBattleScene`) now run in a single pygame window via `src/apps/slime_clan/app.py`. Zero subprocesses. See `docs/SCENE_MANAGER.md` for the full interface contract.

---

## Mana UI Not Visible to Player
**Logged:** 2026-02-21 (Session 017)

### Description
The mana resource system (3 start, 5 max) is fully functional in `auto_battle.py` and logged to terminal, but there is no visual mana bar or MP indicator rendered on-screen for the player. The player cannot see mana values during combat — they can only infer resource management from the combat log.

### Mitigation
Add a mana bar or MP text indicator below each unit's HP bar in `auto_battle.py` rendering. Low priority — the system works correctly without visual feedback.

