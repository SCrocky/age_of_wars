import pygame

# surface id → {(w, h, flip_x, flip_y): scaled_surface}
_cache: dict[int, dict[tuple, pygame.Surface]] = {}


def get_scaled(surf: pygame.Surface, w: int, h: int,
               flip_x: bool = False, flip_y: bool = False) -> pygame.Surface:
    sid = id(surf)
    key = (w, h, flip_x, flip_y)
    entry = _cache.get(sid)
    if entry is None:
        _cache[sid] = entry = {}
    cached = entry.get(key)
    if cached is None:
        s = pygame.transform.scale(surf, (w, h))
        if flip_x or flip_y:
            s = pygame.transform.flip(s, flip_x, flip_y)
        entry[key] = cached = s
    return cached
