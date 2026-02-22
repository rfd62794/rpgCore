# Slime Clan — AI Session Protocol

*To be provided at the start of every new Coding Agent session to prevent context drift.*

## Step 0 — Orient
Run: `python -m src.tools.apj handoff`
This prints current project state, what is in flight, and next priority. 
Read the output before reading anything else.

## Agent Behavior Standards
- Always use `uv run` for execution. Never activate venv manually.
- Spec-first: No code written until plan is confirmed by Overseer in the IMPLEMENTATION PLAN artifact.
- Present significant architectural decisions as three options:
    - **Headlong**: Direct engineering, fastest path.
    - **Divert**: Side-step, different approach to the same goal.
    - **Alt**: The better way, may change the question.
- No `print()` statements in `src/`. Use `logging` or `Rich` for CLI output.
- All commands must be Windows PowerShell safe.
- Artifact first: update docs and journal before closing a session.

---

You are working on the Slime Clan game within the rpgCore repository (github.com/rfd62794/rpgCore). Before starting, read these docs:

- `docs/RPGCORE_CONSTITUTION.md` — engine law, demo structure, repository context (READ FIRST)
- `docs/VISION.md` — the north star
- `docs/ROADMAP.md` — session plan
- `docs/COLONY_SYSTEM.md` — colony architecture
- `docs/SCENE_MANAGER.md` — scene contract

## Key facts:

- This is a desktop pygame application on Windows
- Entry point: `uv run python run_overworld.py`
- Manual verification means running locally and describing what you see
- Do NOT use browser tools — this is not a web application
- Test command: `uv run pytest`
- Current passing tests: [UPDATE THIS NUMBER]
- Git identity: rfd62794

## Architecture: 
- `src/apps/slime_clan/scenes/` for scenes
- `src/apps/slime_clan/ui/` for rendering
- `src/shared/` for engine components
- `src/apps/slime_clan/app.py` is a 31-line launcher.
- Final step of every session:
  - Run `python -m src.tools.apj tasks --done "completed task"` for each finished item.
  - Run `python -m src.tools.apj tasks --add "[TAG] description"` for new discoveries.
  - Run `python -m src.tools.apj update` and update all three journal sections to reflect current state.
