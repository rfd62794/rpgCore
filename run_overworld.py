#!/usr/bin/env python3
"""
Launcher for Session 014 - Playable Demo Slice
-----------------------------------------
Execute this file from the repository root to start the Slime Clan Overworld loop.
"""

import sys
from pathlib import Path
from loguru import logger

# Add src to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from apps.slime_clan.overworld import Overworld
except ImportError as e:
    logger.error(f"❌ Failed to import Overworld: {e}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("🚀 Launching Slime Clan Overworld (Session 014)...")
    app = Overworld()
    app.run()
