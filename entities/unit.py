import math
import pygame
from entities.entity import Entity
from entities.projectile import Arrow, ARROW_DAMAGE
from map import TILE_SIZE

MOVE_SPEED      = 96.0   # world px / second
ANIM_FPS        = 8      # animation frames per second
DISPLAY_SIZE    = 96     # render size in world px (sprite frame is 192×192)
WAYPOINT_RADIUS = 4.0    # snap threshold in world px

ATTACK_RANGE    = 200.0  # world px (~3 tiles)
ATTACK_COOLDOWN = 1.5    # seconds between shots
SHOOT_DELAY     = 0.4    # seconds into shoot animation before arrow spawns
CHASE_INTERVAL  = 0.5    # seconds between re-paths when chasing


def _load_sheet(path: str, frame_size: int) -> list[pygame.Surface]:
    sheet = pygame.image.load(path).convert_alpha()
    count = sheet.get_width() // frame_size
    return [
        sheet.subsurface(pygame.Rect(i * frame_size, 0, frame_size, frame_size))
        for i in range(count)
    ]


class Archer(Entity):
    """
    Player- or AI-controlled archer unit.

    States
    ------
    idle    – standing still
    run     – following a path
    attack  – in range of target, playing shoot animation
    """

    FRAME_SIZE = 192

    def __init__(self, x: float, y: float, team: str = "blue"):
        super().__init__(x, y, team, max_hp=80)

        folder = f"assets/Units/{team.capitalize()} Units/Archer"
        self._frames = {
            "idle":   _load_sheet(f"{folder}/Archer_Idle.png",  self.FRAME_SIZE),
            "run":    _load_sheet(f"{folder}/Archer_Run.png",   self.FRAME_SIZE),
            "attack": _load_sheet(f"{folder}/Archer_Shoot.png", self.FRAME_SIZE),
        }

        self._state:        str   = "idle"
        self._frame_idx:    int   = 0
        self._anim_timer:   float = 0.0
        self._facing_right: bool  = True

        self.path: list[tuple[int, int]] = []

        # Combat
        self.attack_target          = None   # Entity | None
        self.attack_range: float    = ATTACK_RANGE
        self._attack_cooldown: float = 0.0   # time until next shot allowed
        self._shoot_timer:    float = 0.0   # time in current attack cycle
        self._arrow_spawned:  bool  = False  # have we fired this cycle?
        self._chase_timer:    float = 0.0   # time until next re-path

    # ------------------------------------------------------------------
    # Commands (called by game.py)
    # ------------------------------------------------------------------

    def set_path(self, path: list[tuple[int, int]]):
        self.path = list(path)
        self.attack_target = None   # move command cancels attack

    def set_attack_target(self, target):
        self.attack_target = target
        self.path = []

    # ------------------------------------------------------------------
    # Update  →  returns list of Arrow objects to be added to the world
    # ------------------------------------------------------------------

    def update(self, dt: float, tile_map=None) -> list[Arrow]:
        spawned: list[Arrow] = []

        self._attack_cooldown = max(0.0, self._attack_cooldown - dt)

        if self.attack_target is not None:
            if not self.attack_target.alive:
                self.attack_target = None
            else:
                dist = math.hypot(self.attack_target.x - self.x,
                                   self.attack_target.y - self.y)
                if dist <= self.attack_range:
                    self.path = []
                    self._state = "attack"
                    arrow = self._tick_attack(dt)
                    if arrow:
                        spawned.append(arrow)
                else:
                    self._state = "run"
                    self._shoot_timer = 0.0
                    self._arrow_spawned = False
                    if tile_map is not None:
                        self._chase_timer -= dt
                        if self._chase_timer <= 0:
                            self._chase_timer = CHASE_INTERVAL
                            self._repath_to_target(tile_map)
                    self._move_along_path(dt)

        elif self.path:
            self._state = "run"
            self._move_along_path(dt)
        else:
            self._state = "idle"

        self._tick_animation(dt)
        return spawned

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tick_attack(self, dt: float):
        """Advance attack cycle; returns an Arrow when it should fire."""
        if self._attack_cooldown > 0:
            return None

        # Orient toward target
        dx = self.attack_target.x - self.x
        if abs(dx) > 1:
            self._facing_right = dx > 0

        self._shoot_timer += dt

        # Spawn arrow once per cycle after SHOOT_DELAY
        if not self._arrow_spawned and self._shoot_timer >= SHOOT_DELAY:
            self._arrow_spawned = True
            self._attack_cooldown = ATTACK_COOLDOWN
            self._shoot_timer = 0.0
            self._arrow_spawned = False   # reset for next cycle
            self._frame_idx = 0           # restart shoot anim
            return Arrow(self.x, self.y, self.attack_target, ARROW_DAMAGE, self.team)

        return None

    def _repath_to_target(self, tile_map):
        from systems.pathfinding import astar
        sc = int(self.x // TILE_SIZE)
        sr = int(self.y // TILE_SIZE)
        gc = int(self.attack_target.x // TILE_SIZE)
        gr = int(self.attack_target.y // TILE_SIZE)
        self.path = astar(tile_map, (sc, sr), (gc, gr))

    def _move_along_path(self, dt: float):
        if not self.path:
            return
        col, row = self.path[0]
        target_x = col * TILE_SIZE + TILE_SIZE / 2
        target_y = row * TILE_SIZE + TILE_SIZE / 2
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist <= WAYPOINT_RADIUS:
            self.x, self.y = target_x, target_y
            self.path.pop(0)
            return
        speed = MOVE_SPEED * dt
        self.x += dx / dist * speed
        self.y += dy / dist * speed
        if abs(dx) > 1:
            self._facing_right = dx > 0

    def _tick_animation(self, dt: float):
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / ANIM_FPS:
            self._anim_timer -= 1.0 / ANIM_FPS
            frames = self._frames[self._state]
            self._frame_idx = (self._frame_idx + 1) % len(frames)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface, camera):
        frames = self._frames[self._state]
        frame  = frames[self._frame_idx % len(frames)]

        size   = max(1, int(DISPLAY_SIZE * camera.zoom))
        scaled = pygame.transform.scale(frame, (size, size))
        if not self._facing_right:
            scaled = pygame.transform.flip(scaled, True, False)

        sx, sy = camera.world_to_screen(self.x, self.y)
        surface.blit(scaled, (int(sx - size / 2), int(sy - size / 2)))

        if self.selected:
            r = max(2, int(20 * camera.zoom))
            pygame.draw.circle(surface, (255, 220, 0), (int(sx), int(sy)), r, 2)

        self.draw_health_bar(surface, camera)

    # ------------------------------------------------------------------
    # Hit-test
    # ------------------------------------------------------------------

    def hit_test(self, sx: float, sy: float, camera) -> bool:
        ux, uy = camera.world_to_screen(self.x, self.y)
        half = DISPLAY_SIZE * camera.zoom / 2
        return abs(sx - ux) <= half and abs(sy - uy) <= half
