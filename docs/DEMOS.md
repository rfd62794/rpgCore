# RPGCore Demos

This document outlines the design pillars, core loops, current status, and engine proofs for the four target games sharing the RPGCore engine.

## 1. Slime Clan
**Status:** Playable
**Genre:** Turn-based faction strategy

- **Core Loop:** Claim territory → Gather resources → End Day → Auto-resolve conflicts → Expand.
- **Design Pillars:** Deterministic conflict resolution, clear strategic trade-offs, intuitive visual map logic.
- **Engine Proofs:** 
  - Validates `src/shared/` Grid map management.
  - Proves deterministic "Auto-Battle" engines without real-time action intervention.
  - Scene modularity (Overworld vs Battle Field).

## 2. Last Appointment
**Status:** Playable
**Genre:** Narrative dialogue

- **Core Loop:** Read NPC text → Evaluate dialogue options → Select response via UI Cards → Update scene state and room atmosphere.
- **Design Pillars:** Heavy atmospheric tension, branching narrative consequences, seamless UI transitions.
- **Engine Proofs:**
  - Validates `src/shared/` Text rendering and UI layout managers.
  - Proves complex dialogue state machines and script parsing.
  - Showcases environmental visual effects (Radial Vignette).

## 3. TurboShells
**Status:** In Development (Stubbed)
**Genre:** Breeding/management sim

- **Core Loop:** Analyze turtle genetics → Pair and Breed → Train stats → Race for capital → Re-invest in facilities.
- **Design Pillars:** Endless genetic depth, statistically driven emergent outcomes, satisfying progression arcs.
- **Engine Proofs:**
  - Will validate complex data mutations and large object registries.
  - Proves out long-term save-state persistence and background simulation processing.

## 4. Asteroids Roguelike
**Status:** In Development (Stubbed)
**Genre:** Action roguelike

- **Core Loop:** Spawn → Navigate asteroid field → Shoot hazards/enemies → Collect power-ups → Die → Upgrade → Repeat.
- **Design Pillars:** High-stakes twitch gameplay, immediate feedback loops, diverse run-altering upgrades (roguelike elements).
- **Engine Proofs:**
  - Will stress-test real-time physics and collision layers.
  - Proves high-framerate rendering pipelines and particle systems.
  - Validates the `EntityTemplateRegistry` for rapid enemy/projectile spawning and despawning.
