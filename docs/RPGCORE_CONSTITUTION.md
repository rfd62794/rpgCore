# rpgCore — Constitution
## What rpgCore Is
rpgCore is a shared game engine and collection of demos built by one developer across multiple creative directions. It is not a single game. It is a platform that supports multiple games sharing a common technical and creative foundation.
## The Three Laws
1. src/shared/ is the engine. If a system is useful to more than one demo it lives in shared. It does not live in the demo.
2. Demos live in src/apps/. Each demo is self-contained above the shared layer. Demos consume shared systems. They do not reimplement them.
3. Nothing gets built twice. If it exists in shared you use it. If it doesn't exist in shared and two demos need it, you extract it into shared before building it again.
## The Engine Layer Decision
src/shared/ is the canonical engine layer. It was built deliberately, extracted cleanly, and proven by a working demo.
src/dgt_engine/ and src/game_engine/ are donor archives. They contain valuable components that have not yet been harvested. They are not active engine layers. No new code should be added to either. Components worth keeping get extracted into src/shared/ properly then the source is archived.
## The Shared Layer Structure
```
src/shared/

combat/          # D20Resolver, damage resolution, status effects*
engine/          # BaseSystem, SystemClock, SceneManager*
entities/        # Entity base, EntityManager*
world/           # FactionManager, ColonyManager*
narrative/       # ConversationGraph, StateTracker, KeywordRegistry (planned)*
rendering/       # RenderAdapter contract, pygame bridge*
genetics/        # GeneticInheritance, TraitSystem (planned)*
persistence/     # SaveLoad, SQLite adapter (planned)*
```

## The Demos
Each demo proves a different expression of the shared engine:
- Slime Clan — strategy/tactics. Civ meets FFT meets DQM. The deep game.
- TurboShells — management/breeding. Genetic inheritance, racing, nurture loop.
- Last Appointment — dialogue/narrative. Conversation graph, stance system, single scene.
- Asteroids Roguelike — action/progression. Run-based, procedural, reflex plus strategy.
These four demos share entity management, relationship tracking, scene management, and resource economy. Their genres differ. Their foundation does not.
## What Gets Archived
- src/demos/ — empty skeletons, no implementation
- src/apps/tycoon/ — domain mismatch, reference only
- src/apps/space/ — experimental testbed, harvest useful AI/evolution concepts first
- godot_project/ — out of scope for Python/Pygame/WASM target
- rust/ — premature optimization, revisit if performance requires it
- Fragmented docs: PHASE_.md, README_.md shards, INVENTORY.md, ASTEROIDS_CSHARP_PORT_PLAN.md, GODOT_.md*
## The Active Docs
These documents are canonical and maintained:
- RPGCORE_CONSTITUTION.md — this document
- SESSION_PROTOCOL.md — how to start a new agent session
- VISION.md — Slime Clan north star
- ROADMAP.md — Slime Clan session plan
- MILESTONES.md — Slime Clan milestone tracking
- COLONY_SYSTEM.md — colony architecture
- SCENE_MANAGER.md — scene contract
- TECH_DEBT.md — known issues
- REPO_AUDIT.md — current repository state
- ENGINE_AUDIT.md — component integration status
## The Platform Vision
rpgCore is one developer's Orange Box. Four games, one engine, one creative voice. Different genres, different tones, different audiences. The shared foundation makes each game stronger by what the others built.
The engine does not belong to any one demo. The demos are expressions of the engine.
## Scope Boundary
If a feature does not serve at least one active demo it does not get built. If a system cannot be shared across at least two demos it lives in the demo not the engine. If a document does not help a future agent session or a future design decision it gets archived.
