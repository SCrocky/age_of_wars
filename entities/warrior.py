import rendering.entity_renderer as entity_renderer
from entities.unit import Unit

ANIM_FPS        = 8
ATTACK_DAMAGE   = 25
ATTACK_COOLDOWN = 2.0
HIT_DELAY       = 0.5
GUARD_DURATION  = 0.5   # how long the guard animation stays visible

_WARRIOR_FRAME_COUNTS: dict[str, int] = {
    "idle":    8,
    "run":     6,
    "attack1": 4,
    "attack2": 4,
    "guard":   6,
}


class Warrior(Unit):
    """
    Slow melee unit that guards against the first hit received during
    its attack cooldown, taking only half damage from that hit.

    States
    ------
    idle    – standing still
    run     – following a path
    attack  – in melee range of target (alternates Attack1 / Attack2)
    guard   – brief visual played when a block lands
    """

    FRAME_SIZE    = 192
    DISPLAY_SIZE  = 128
    SELECT_RADIUS = 22
    MOVE_SPEED    = 80.0
    ATTACK_RANGE  = 55.0

    def __init__(self, x: float, y: float, team: str = "blue"):
        super().__init__(x, y, team, max_hp=150)

        self._state:       str   = "idle"
        self._anim_key:    str   = "idle"
        self._frame_idx:   int   = 0
        self._anim_timer:  float = 0.0
        self._attack_set:  int   = 0    # alternates 0 / 1

        self.attack_range: float = self.ATTACK_RANGE
        self._hit_timer:   float = 0.0

        self._guard_ready: bool  = True    # one block available per attack cycle
        self._guard_timer: float = 0.0     # drives guard anim display

    # ------------------------------------------------------------------
    # Damage interception
    # ------------------------------------------------------------------

    def receive_melee_hit(self, attacker):
        dx = attacker.x - self.x
        if abs(dx) > 1:
            self._facing_right = dx > 0

    def take_damage(self, amount: int, is_melee: bool = False):
        if is_melee and self._guard_ready:
            amount = max(1, amount // 2)
            self._guard_ready = False
            self._guard_timer = GUARD_DURATION
            self._frame_idx   = 0
        super().take_damage(amount)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float, tile_map=None) -> list:
        self._time       += dt
        self._guard_timer = max(0.0, self._guard_timer - dt)

        if self.attack_target is not None:
            if not self.attack_target.alive:
                self.attack_target = None
            else:
                if self._dist_to_target() <= self.attack_range:
                    self.path   = []
                    self._state = "attack"
                    self._tick_melee(dt)
                else:
                    self._state     = "run"
                    self._hit_timer = 0.0
                    self._chase(dt, tile_map)

        elif self.path:
            self._state = "run"
            self._move_along_path(dt)
        else:
            self._state = "idle"

        self._tick_animation(dt)
        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tick_melee(self, dt: float):
        if self._time - self._last_shot_time < ATTACK_COOLDOWN:
            return

        if self._hit_timer == 0.0:
            self._frame_idx = 0

        dx = self.attack_target.x - self.x
        if abs(dx) > 1:
            self._facing_right = dx > 0

        self._hit_timer += dt
        if self._hit_timer >= HIT_DELAY:
            self.attack_target.take_damage(ATTACK_DAMAGE, is_melee=True)
            self.attack_target.receive_melee_hit(self)
            self._last_shot_time = self._time
            self._hit_timer      = 0.0
            self._guard_ready    = True
            self._attack_set     = 1 - self._attack_set
            self._frame_idx      = 0

    def _current_anim_key(self) -> str:
        if self._guard_timer > 0:
            return "guard"
        if self._state == "attack":
            if self._time - self._last_shot_time < ATTACK_COOLDOWN:
                return "idle"
            return f"attack{self._attack_set + 1}"
        if self._state == "run":
            return "run"
        return "idle"

    def _tick_animation(self, dt: float):
        self._anim_key    = self._current_anim_key()
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / ANIM_FPS:
            self._anim_timer -= 1.0 / ANIM_FPS
            count = _WARRIOR_FRAME_COUNTS[self._anim_key]
            if self._state == "attack" and self._frame_idx >= count - 1:
                pass  # hold last frame until next swing resets to 0
            else:
                self._frame_idx = (self._frame_idx + 1) % count

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, surface, camera):
        entity_renderer.render_warrior(self, surface, camera)
