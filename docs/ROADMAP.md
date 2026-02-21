# Slime Clan — Development Roadmap

## Session 018 — Combat Polish
- **Floating Combat Symbols**: Animate action icons from attacker to target (⚔️ slash, 🛡️ pulse, ✨ heal glow, 💥 crit burst). 400ms fade-out.
- **Optional Player Control**: SPACE pauses the turn queue and displays the current unit's available actions with mana costs. SPACE again resumes AI execution. Gives the player agency without breaking the auto-battler rhythm.
- **AI Randomness**: Introduce 20% action randomness to prevent perfectly predictable behavior. Units occasionally pick suboptimal actions to feel more organic.

---

## Session 019 — Battle Queue Visualization
- **Turn Order Strip**: Visual bar showing upcoming unit portraits/icons in sequence.
- **Active Unit Highlight**: The currently acting unit is highlighted with a glow or border pulse.
- **Queue Depth**: Show the next 3–5 units in the queue.
- **Dynamic Updates**: Queue reorders visually when speed buffs, stuns, or deaths modify turn order.

---

## Session 020 — Squad Loadout
- **Pre-Battle Screen**: New screen shown before deploying to `battle_field.py`.
- **Composition Selection**: Player selects 3 slimes from a roster to form their squad.
- **Starter Roster**: Begins with Rex, Brom, and Pip. Expandable through future unlocks or recruitment mechanics.

---

## Future — rpgCore Integration
- **Entity Migration**: Refactor `SlimeUnit` toward the rpgCore entity/component system.
- **Rendering Adapters**: Replace direct pygame drawing primitives with rpgCore rendering adapters for portability.
- **Faction System**: Wire `faction_system.py` to Overworld node ownership, replacing the current hardcoded `NodeState` enum with faction-driven territory control.
