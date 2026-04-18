import math
import pygame

ARROW_SPEED  = 400.0   # world px / second
ARROW_DAMAGE = 15
ARROW_HIT_RADIUS = 12.0  # world px — snap-to-hit distance


def _load_arrow(team: str) -> pygame.Surface:
    folder = f"assets/Units/{team.capitalize()} Units/Archer"
    return pygame.image.load(f"{folder}/Arrow.png").convert_alpha()


# Cache one surface per team so we don't reload on every shot
_arrow_cache: dict[str, pygame.Surface] = {}


def _get_arrow_surf(team: str) -> pygame.Surface:
    if team not in _arrow_cache:
        _arrow_cache[team] = _load_arrow(team)
    return _arrow_cache[team]


class Arrow:
    """A projectile fired by an Archer at a target entity."""

    DISPLAY_SIZE = 32  # render size in world px (Arrow.png is 64×64)

    def __init__(self, x: float, y: float, target, damage: int, team: str):
        self.x = x
        self.y = y
        self.target = target   # Entity reference — we home on it
        self.damage = damage
        self.team = team
        self.alive = True
        self._surf = _get_arrow_surf(team)

        # Initial direction toward target
        dx = target.x - x
        dy = target.y - y
        dist = math.hypot(dx, dy) or 1
        self._angle = math.degrees(math.atan2(-dy, dx))  # for rotation

    # ------------------------------------------------------------------

    def update(self, dt: float):
        if not self.alive:
            return

        if not self.target.alive:
            self.alive = False
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist <= ARROW_HIT_RADIUS:
            self.target.take_damage(self.damage)
            self.alive = False
            return

        self._angle = math.degrees(math.atan2(-dy, dx))
        speed = ARROW_SPEED * dt
        self.x += dx / dist * speed
        self.y += dy / dist * speed

    def render(self, surface: pygame.Surface, camera):
        if not self.alive:
            return

        size = max(1, int(self.DISPLAY_SIZE * camera.zoom))
        scaled = pygame.transform.scale(self._surf, (size, size))
        rotated = pygame.transform.rotate(scaled, self._angle)
        sx, sy = camera.world_to_screen(self.x, self.y)
        rect = rotated.get_rect(center=(int(sx), int(sy)))
        surface.blit(rotated, rect)
