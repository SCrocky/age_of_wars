"""
HUD rendering entry point.

hud.py is a self-contained renderer module — all surface loading, drawing,
and click-hit-testing lives there with no game-logic dependencies.
This module re-exports HUD so callers can import from the rendering package.
"""
from hud import HUD

__all__ = ["HUD"]
