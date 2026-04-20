from __future__ import annotations
import pygame


class SpriteRegistry:
    """Central store for all game Surfaces, keyed by stable string identifiers.

    Key conventions:
      Buildings : "building/{type}/{team}"
                  e.g. "building/castle/blue"
      Units     : "unit/{type}/{team}/{anim}/{frame}"
                  e.g. "unit/archer/blue/run/3"
      Lancer    : "unit/lancer/{team}/{anim}/{dir}/{frame}"
                  e.g. "unit/lancer/black/attack/downright/0"
      Pawn      : "unit/pawn/{team}/{anim}/{tool}/{frame}"
                  e.g. "unit/pawn/blue/interact/axe/2"
      Arrow     : "projectile/arrow/{team}"
      Resources :
        Gold    : "resource/gold/{variant}/frame/{n}"
        Wood    : "resource/wood/{variant}/frame/{n}"
                  "resource/wood/{variant}/stump"
        Meat    : "resource/meat/{state}/{n}"
                  e.g. "resource/meat/idle/0"
      Tiles     : "tile/{name}"
                  e.g. "tile/grass1", "tile/water_bg"
    """

    def __init__(self) -> None:
        self._surfaces: dict[str, pygame.Surface] = {}
        self._frame_counts: dict[str, int] = {}  # prefix → frame count

    # ------------------------------------------------------------------
    # Registration (called by renderer initialisation code)
    # ------------------------------------------------------------------

    def register(self, key: str, surface: pygame.Surface) -> None:
        self._surfaces[key] = surface

    def register_strip(self, prefix: str, frames: list[pygame.Surface]) -> None:
        """Register a list of frames and record the count under *prefix*."""
        for i, surf in enumerate(frames):
            self._surfaces[f"{prefix}/{i}"] = surf
        self._frame_counts[prefix] = len(frames)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, key: str) -> pygame.Surface:
        surf = self._surfaces.get(key)
        if surf is None:
            raise KeyError(f"SpriteRegistry: unknown key {key!r}")
        return surf

    def frame_count(self, prefix: str) -> int:
        """Return the number of frames registered under *prefix*."""
        count = self._frame_counts.get(prefix)
        if count is None:
            raise KeyError(f"SpriteRegistry: no frame strip for prefix {prefix!r}")
        return count

    def __contains__(self, key: str) -> bool:
        return key in self._surfaces
