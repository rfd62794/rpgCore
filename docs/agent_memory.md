# Agent Memory

## Scene Standardization — Planned Next Infrastructure Session

Current state:
  534 passing, 0 failures, 0 errors
  All scenes satisfy abstract contract via stubs
  
Problem remaining:
  Stubs are scattered across legacy scenes
  BaseScene does not exist yet
  Boilerplate duplicated in every scene
  
Planned:
  BaseScene — extract shared boilerplate
  BaseComponent — UI component contract
  SceneManager stack — clean navigation
  
When to build:
  After Racing track feels right
  After Dungeon auto-battle prototype
  One dedicated session
  
Payoff:
  Adding abstract method to BaseScene
  with default impl = 0 cascade errors
  New scenes = 20 lines not 80
  Navigation = manager.push/pop only
