# Agent Memory

## Architectural Decisions
- SceneBase is in src/shared/ui/scene_base.py (not BaseScene)
- D20Resolver is stable — do not refactor without explicit request
- Mathematical renderer — slimes are drawn not sprited
- All demos must inherit shared infrastructure from src/shared/
- Herald routes to remote (execution department)
- Archivist and Strategist now route to remote (Ollama unstable)

## Patterns That Work
- Two-pass Herald with ContextBuilder produces real file paths
- Remote routing via DeepSeek R1 produces complete valid JSON
- Brace-depth extraction handles partial model output
- YAML configs per agent — schema and prompt in same config

## Patterns That Failed
- :free suffix on OpenRouter models returns 404 — never use
- Strategist on 1b truncates at ~512 tokens — always use 3b or remote
- Herald example absorption — copies example verbatim on 1b
- Herald with invented file paths — ContextBuilder fixes this
- model_name kwarg on Herald.__init__ — removed, use AgentConfig

## Constitutional Rules
- Test floor: 494 passing
- All new features require tests
- src/shared/ is shared infrastructure — never app-specific
- Demos in src/apps/ — shared systems in src/shared/

## Never Do
- Do not invent file paths not in SymbolMap
- Do not use :free suffix on OpenRouter model names
- Do not skip risk field in SessionPlan alternatives
- Do not refactor existing agents mid-session
- Do not recommend non-vision-aligned work when VISION.md exists

## Planned: ThreadAgent Suite
- **ThreadAuditor** — Audits VISION -> Goal -> Milestone -> Task -> Step chain.
- **ThreadBuilder** — Generates missing chain links with real file paths.
- **ThreadValidator** — Verifies steps against chain after completion.
- Build after **M_BROWSER** ships.
- **Priority**: HIGH — fixes Strategist drift permanently.
