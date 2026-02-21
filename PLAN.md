# Implementation Plan: Session 015 - Balance and Tier Integration

## Technical Approach

### 1. Three-Tier War System Architecture
The game loop consists of three interconnected simulation tiers:
1. **Strategic Tier (`overworld.py`)**: A static node map where the player plots their macro-campaign. Each node (Region) is contested, red, or blue. Clicking a node initiates an invasion. Features global win/loss tracking.
2. **Operational Tier (`territorial_grid.py`)**: A mid-level skirmish that determines the spatial momentum of the invasion. A grid-based simulation where blue and red abstract slimes collide for dominance over tiles.
3. **Tactical Tier (`auto_battle.py`)**: The final 3v3 auto-battler resolving the conflict using specific player squad characters (`Rex`, `Brom`, `Pip`) against a specialized red squad.

### 2. Session 015 Objectives

**A. Battle Balance (`auto_battle.py`)**
- **Player Bias**: The core trio (`Rex`, `Brom`, `Pip`) receives a permanent +25% base stat multiplier (HP, Attack, Defense, Speed) so the player acts as a durable, elite underdog.
- **SHIELD Taunt Redirection**: `SWORD` logic must explicitly check if any enemy has `taunt_active=True`. If so, those enemies must be prioritized over the standard "lowest HP" fallback.
- **STAFF Heal Scaling**: Change the heal function from standard flat scaling to a percentage-missing based heal (e.g., target missing HP / max HP factor).

**B. Difficulty Scaling (`overworld.py`)**
- Implement an Easy/Normal/Hard scaling configuration.
- Pass `--difficulty` from the overworld down to the tactical `auto_battle.py` layer.
- Enemy squads scale -20% / 0% / +20% based on difficulty.

**C. Tier Integration (`overworld.py` -> `territorial_grid.py` -> `auto_battle.py`)**
- Revise the `_launch_battle()` function in `overworld.py`.
- First, launch `territorial_grid.py` via subprocess.
- Wait for the result object (exit code 0 = Blue Win, 1 = Red Win/Cancel).
- Launch `auto_battle.py` with an argument like `--grid-advantage=PLAYER` or `--grid-advantage=ENEMY`.
- Parse the result to determine final node ownership.

### 3. Tests
- Update `tests/unit/slime_clan_autobattle_test.py` to cover taunt logic and scaled healing logic.
- Maintain the 7 tests in the `slime_clan_*.py` suite.

## Verification Plan
1. Run `uv run pytest` to ensure all 7 unit tests pass.
2. Run `python run_overworld.py`.
3. Verify clicking a node first opens the grid, then upon completion, opens the auto battler with the correct stat buffs applied.
4. Verify the overworld correctly handles the final result.
