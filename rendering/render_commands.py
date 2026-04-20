from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class RenderCommand:
    """One sprite blit request. World coordinates; renderer applies camera transform."""
    sprite_key: str       # SpriteRegistry lookup key, e.g. "unit/archer/blue/run/3"
    world_x:    float
    world_y:    float
    world_w:    int
    world_h:    int
    flip_x:     bool  = False
    angle:      float = 0.0   # degrees, for projectiles
    alpha:      int   = 255   # 0-255, for blueprints
    sort_y:     float = 0.0   # painter's algorithm depth


@dataclass
class RectCommand:
    """One filled or outlined rectangle. World coordinates."""
    world_x: float
    world_y: float
    world_w: float
    world_h: float
    color:   tuple[int, int, int]
    thickness: int  = 0       # 0 = filled
    sort_y:  float  = 0.0


# Type alias for anything the renderer can process
DrawCommand = RenderCommand | RectCommand
