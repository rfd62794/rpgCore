# Implementation Plan: Session 012 - Overworld Stub

## Technical Approach

### 1. Data Structures & State Management
- Define `NodeState` enum in `src/apps/slime_clan/overworld.py` for possible node ownerships (`HOME`, `RED`, `BLUE`, `CONTESTED`).
- Create a `MapNode` dataclass containing `id`, `name`, `x`, `y`, `state`, and `connections`.
- Initialize the graph with 1 Home node and 4 contestable nodes (e.g., "Crash Site", "Northern Wastes", "Scrap Yard", "Eastern Front", "Deep Red Core").

### 2. Overworld Engine (`overworld.py`)
- Initialize a Pygame window at 640x480.
- `handle_events()`: Detect clicks within node radii.
- `update()`: Handle logic and transitions. If a Red/Contested node is clicked, execute the battle transition.
- `render()`: Draw connection lines between nodes, then draw nodes (distinct shapes/colors based on `NodeState`).

### 3. Transition Logic
- When triggering a battle, use `subprocess.run([sys.executable, "-m", "src.apps.slime_clan.territorial_grid"])` to launch the grid battle, simulating a scene transition without complex engine coupling.
- Upon completion of the subprocess (simulated win), update the node state to `BLUE`.

### 4. Root Launcher (`run_overworld.py`)
- Very simple 3-line file to import and launch the `Overworld` class game loop.

### 5. Tests
- Create `tests/unit/test_overworld_state.py`.
- Write tests for initializing `MapNode` relationships and verifying `NodeState` transitions.
- Verify existing tests still pass with `pytest`.

### 6. Known Limitations
- **Future: Scene Manager**: The subprocess launch of `territorial_grid.py` is intentional for this stub session, which results in two separate pygame windows. This is acceptable for the stub and will be addressed in a future session when a proper scene transition architecture is wired up.
- **Battle Results**: The ownership update on return simulates a Blue win regardless of the actual battle outcome. We will wire real result passing in a future session.

## Verification Plan
1. Run `pytest` to ensure test count is >= 79 and all pass.
2. Execute `python run_overworld.py`.
3. Verify map renders correctly.
4. Click a Red node -> see the `territorial_grid` window open.
5. Close the grid window -> verify the Red node turned Blue on the map.
