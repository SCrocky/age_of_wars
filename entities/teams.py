"""
Team palette — single source of truth for the 5 player colours shipped with
the Tiny Swords asset pack.

The team string itself is the asset folder name (capitalised at lookup time),
so renderers don't need a separate mapping for sprite paths.
"""
from __future__ import annotations

TEAM_COLORS: tuple[str, ...] = ("blue", "red", "yellow", "purple", "black")

# UI accent colour (used for HUD headers, victory popup, minimap labels, etc.)
BANNER_COLORS: dict[str, tuple[int, int, int]] = {
    "blue":   (80,  140, 255),
    "red":    (220, 80,  80),
    "yellow": (230, 200, 60),
    "purple": (180, 100, 200),
    "black":  (60,  60,  60),
}

# Row offset into the 5×5 Avatars sheet (1-indexed PNG names: Avatars_01..25).
# Add a per-unit-type column index (1..5) to get the avatar number.
AVATAR_ROW_OFFSET: dict[str, int] = {
    "blue":   0,   # Avatars_01..05
    "red":    5,   # Avatars_06..10
    "yellow": 10,  # Avatars_11..15
    "purple": 15,  # Avatars_16..20
    "black":  20,  # Avatars_21..25
}


def teams_from_scene(scene: dict) -> list[str]:
    """Extract the ordered list of teams from a scene's spawns."""
    seen: list[str] = []
    for sp in scene.get("spawns", []):
        t = sp.get("team")
        if t and t not in seen:
            seen.append(t)
    return seen
