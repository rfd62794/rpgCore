# Implementation Plan: Session 013 - Auto-Battle Scene

## Technical Approach

### 1. Data Structures & State Management
- Create `src/apps/slime_clan/auto_battle.py`.
- Define `Shape` (`CIRCLE`, `SQUARE`, `TRIANGLE`) and `Hat` (`SWORD`, `SHIELD`, `STAFF`) Enums.
- Implement `SlimeUnit` dataclass.
  - Implement a factory method or pure function `create_slime(name, shape, hat)` to generate units with shape-adjusted stats.
- Define `Action` and `TurnOrder` semantics to handle combat.

### 2. Auto-Battle Engine (`auto_battle.py`)
- Define `Squad` list containing surviving `SlimeUnit`s.
- `handle_events()`: only checks for Window Quit or ESC.
- `update()`:
  - Timer mechanism triggers every 800ms.
  - Sort all surviving units by speed (fastest first).
  - Let one unit execute its action.
  - Advance the pointer; reset pointer if sequence complete.
  - Check for squad wipe conditions.
- `render()`:
  - Draw Blue squad on `x = WINDOW_WIDTH // 6`.
  - Draw Red squad on `x = WINDOW_WIDTH - WINDOW_WIDTH // 6`.
  - Utilize `draw_slime` for the core body.
  - Render the unit's name above the slime sprite.
  - Draw HP bars below each survivor.
  - Render a small shape indicator (`C`/`S`/`T`) and hat indicator (`⚔`/`🛡`/`✨`) beneath the HP bar for quick readability.

### 3. Combat Logic Functions (Pure functions)
- `execute_action(actor, allies, enemies)`: Handles the logic where `SWORD` finds enemy min HP to attack, `SHIELD` buffs defense, `STAFF` heals ally min HP.

### 4. Root Launcher (`run_auto_battle.py`)
- Python script to launch the auto-combat visualization.

### 5. Tests
- Create `tests/unit/slime_clan_autobattle_test.py`.
- Write tests:
  - `test_slime_stat_generation`
  - `test_turn_order_sorting`
  - `test_sword_targets_lowest_hp_enemy`
  - `test_staff_heals_lowest_hp_ally`

### 6. Known Limitations
- **Animation Fidelity**: Visualizing actions (like a projectile or sword swing) may be rudimentary (e.g., text popups or simple flashes) to keep within the fast development pace of the stub.
- **Subprocesses**: Still lacking a unified Scene Manager, so isolated tests run decoupled.

## Verification Plan
1. Run `pytest` to ensure test count is >= 79 and all pass.
2. Execute `python run_auto_battle.py`.
3. Verify battle loop runs cleanly and autonomously.
