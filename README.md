# DGT Platform

**A High-Concurrency Neuro-Evolutionary SDK for Cross-Engine Simulation**

[![CI/CD](https://github.com/ConsumrBuzzy/rpgCore/workflows/ci/badge.svg)](https://github.com/ConsumrBuzzy/rpgCore/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code Coverage](https://codecov.io/gh/ConsumrBuzzy/rpgCore/branch/main/graph/badge.svg)](https://codecov.io/gh/ConsumrBuzzy/rpgCore/branch/main)

---

## 🎯 Value Proposition

The DGT Platform is a **production-ready SDK** that combines genetic algorithms, physics engines, and permadeath mechanics into a unified system. It demonstrates advanced software architecture, thread-safe concurrent processing, and enterprise-grade data management—perfect for showcasing IT Management and Data Administration expertise.

### 🚀 Key Features

- **Neuro-Evolutionary AI**: NEAT-based genetic algorithm system
- **Cross-Engine Physics**: Newtonian space combat + D20 RPG mechanics
- **Permadeath System**: Resource depletion with legacy preservation
- **Industrial Tools**: Professional asset pipeline and utilities
- **60 FPS Performance**: High-concurrency rendering with hardware burn effects
- **Thread-Safe Design**: Concurrent batch processing with SQLite
- **Python 3.12 Standard**: Enterprise-grade stability and performance

## Architecture

**Two-Pipeline Design:**
1. **Fast Path (Semantic)**: MiniLM embeddings → Intent ID (~50ms)
2. **Narrative Path (LLM)**: Ollama + Pydantic AI → Rich storytelling (~200-500ms)

**Core Components:**
- `semantic_engine.py`: Vector-based intent resolution
- `narrative_engine.py`: LLM-driven outcome generation with Pydantic validation
- `game_state.py`: Deterministic state machine (player, NPCs, rooms)
- `game_loop.py`: Rich UI REPL orchestrating the game cycle

## Installation

```bash
# Clone repository
git clone https://github.com/ConsumrBuzzy/rpgCore.git
cd rpgCore

# Install in development mode (Python 3.12+ required)
pip install -e .

# Run validation
python scripts/run_tests.py
```

## Quick Start

### Test Semantic Resolver (No LLM Required)
```bash
python demo_semantic_resolver.py
```

This lets you verify that inputs like **"I throw my beer at him"** correctly map to the **`distract`** intent.

### Play the Full Game
```bash
cd src
python game_loop.py
```

**Example gameplay:**
```
> I kick the table to distract the guard

🎲 Intent: distract (confidence: 0.87)
🧠 Generating outcome...

The guard spins around as your boot connects with the table leg,
sending mugs clattering to the floor. "What in the—?" he shouts.

[Guard: distracted] [HP: 100] [Turn: 2]
```

## Project Structure

```
rpgCore/
├── src/
│   ├── semantic_engine.py    # Intent library + vector matching
│   ├── narrative_engine.py   # Pydantic AI narrator
│   ├── game_state.py          # State machine + persistence
│   └── game_loop.py           # Main REPL
├── tests/
│   └── test_semantic_resolver.py
├── demo_semantic_resolver.py  # Standalone intent tester
├── requirements.txt
└── README.md
```

## Extending the Game

### Add New Intents
Edit `semantic_engine.py`:
```python
library.add_intent(
    "climb",
    "Scale walls, climb objects, or ascend to higher ground"
)
```

### Customize Narrative Tone
In `game_loop.py`:
```python
self.narrator = SyncNarrativeEngine(
    model_name='ollama:llama3.2',
    tone='serious'  # Options: humorous, serious, gritty
)
```

### Create New Scenarios
See `game_state.py → create_tavern_scenario()` for examples.

## Performance Specs

| Component | Latency | VRAM/RAM |
|-----------|---------|----------|
| MiniLM (semantic) | <50ms | 80MB (CPU) |
| Llama 3.2 3B (narrative) | 200-500ms | ~2GB |
| **Total turn time** | ~300-600ms | ~2GB VRAM |

## Testing

```bash
# Run unit tests
pytest tests/ -v

# Check intent matching accuracy
pytest tests/test_semantic_resolver.py::test_paraphrased_distract -v
```

## Troubleshooting

**"Model not found" error:**
```bash
ollama pull llama3.2:3b
```

**Slow first turn:**
- Normal! Models pre-warm on first inference (~2-3 seconds)

**Intent matching poor quality:**
- Adjust `confidence_threshold` in `game_loop.py` (default: 0.5)
- Add more specific intent descriptions in `create_default_intent_library()`

## Design Philosophy

- **SOLID Principles**: Intent resolution, narrative generation, and state management are fully decoupled
- **Fail-Safe Design**: If LLM fails, system falls back to deterministic outcomes
- **Offline-First**: Zero network dependencies after initial setup
- **Extensibility**: Add new intents without modifying core resolver code

## License

MIT (or your preferred license)
