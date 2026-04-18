import pygame
from entities.building import Archery, Barracks, House

BUILD_RATE = 30.0  # HP-equivalent progress per second per builder

# name → (class, cost_dict)
BUILDABLE: dict[str, tuple[type, dict[str, int]]] = {
    "Archery":  (Archery,  {"wood": 30, "gold": 20}),
    "Barracks": (Barracks, {"wood": 50, "gold": 30}),
    "House":    (House,    {"wood": 20}),
}


class Blueprint:
    """A building site under construction. Wraps a pre-created building instance."""

    def __init__(self, building):
        self._building  = building
        self.x          = building.x
        self.y          = building.y
        self.team       = building.team
        self.selected   = False
        self.alive      = True
        self.progress   = 0.0
        self.COLLISION_W = building.COLLISION_W
        self.COLLISION_H = building.COLLISION_H

    @property
    def hp(self) -> int:
        return int(self.progress)

    @property
    def max_hp(self) -> int:
        return self._building.max_hp

    @property
    def sort_y(self) -> float:
        return self._building.sort_y

    def closest_point(self, x: float, y: float) -> tuple[float, float]:
        return self._building.closest_point(x, y)

    def hit_test(self, sx: float, sy: float, camera) -> bool:
        return self._building.hit_test(sx, sy, camera)

    def add_progress(self, amount: float) -> bool:
        """Returns True when construction completes."""
        self.progress = min(self._building.max_hp, self.progress + amount)
        return self.progress >= self._building.max_hp

    def complete(self):
        """Mark done and return the finished building."""
        self.alive = False
        return self._building

    def render(self, surface: pygame.Surface, camera):
        b     = self._building
        ratio = self.progress / b.max_hp

        w = max(1, int(b.DISPLAY_W * camera.zoom))
        h = max(1, int(b.DISPLAY_H * camera.zoom))
        scaled = pygame.transform.scale(b._surf, (w, h)).copy()
        scaled.set_alpha(int(60 + ratio * 180))
        sx, sy = camera.world_to_screen(b.x, b.y)
        surface.blit(scaled, (int(sx - w / 2), int(sy - h / 2)))

        # Construction progress bar
        bar_w = max(20, int(w * 0.6))
        bar_h = max(4, int(6 * camera.zoom))
        bx    = int(sx - bar_w / 2)
        by    = int(sy - h / 2 - bar_h - 4)
        pygame.draw.rect(surface, (40, 40, 40),    (bx, by, bar_w, bar_h))
        fill = int(bar_w * ratio)
        if fill > 0:
            pygame.draw.rect(surface, (255, 200, 50), (bx, by, fill,  bar_h))
        pygame.draw.rect(surface, (0, 0, 0),       (bx, by, bar_w, bar_h), 1)
