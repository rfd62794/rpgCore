#!/usr/bin/env python3
"""
Launcher for Session 012 - Overworld Stub
-----------------------------------------
Execute this file from the repository root to start the Slime Clan Overworld map.
"""
from src.apps.slime_clan.overworld import Overworld

if __name__ == "__main__":
    app = Overworld()
    app.run()
