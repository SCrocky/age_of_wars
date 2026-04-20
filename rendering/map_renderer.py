from __future__ import annotations
import math
import pygame
from map import TILE_SIZE, WATER, GRASS


class MapRenderer:
    """Owns the tile Surface cache and renders a TileMap to the screen."""

    _SHEET_COLS  = 9
    _SHEET_ROWS  = 6
    _GRASS_COLOR = (106, 153, 56)
    _WATER_COLOR = (56, 120, 153)

    def __init__(self) -> None:
        self._tile_cache:  pygame.Surface | None   = None
        self._water_tile:  pygame.Surface | None   = None
        self._sheet_tiles: list[pygame.Surface]    = []
        self._loaded = False

    # ------------------------------------------------------------------

    def _load_sprites(self) -> None:
        self._water_tile = pygame.image.load(
            "assets/Terrain/Tileset/Water Background color.png"
        ).convert_alpha()

        sheet = pygame.image.load(
            "assets/Terrain/Tileset/Tilemap_color1.png"
        ).convert_alpha()
        self._sheet_tiles = []
        for row in range(self._SHEET_ROWS):
            for col in range(self._SHEET_COLS):
                tile = sheet.subsurface(
                    pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
                self._sheet_tiles.append(tile)

        self._loaded = True

    def _build_tile_cache(self, tile_map) -> None:
        """Pre-render all tiles into a full-resolution Surface (zoom=1.0)."""
        surf = pygame.Surface((tile_map.pixel_width, tile_map.pixel_height))
        for row in range(tile_map.rows):
            for col in range(tile_map.cols):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                if tile_map.tiles[row][col] == WATER:
                    surf.blit(self._water_tile, (x, y))
                else:
                    # +1 to eliminate sub-pixel gaps when scaled
                    pygame.draw.rect(surf, self._GRASS_COLOR,
                                     (x, y, TILE_SIZE + 1, TILE_SIZE + 1))
        self._tile_cache       = surf
        tile_map._tiles_dirty  = False

    # ------------------------------------------------------------------

    def render(self, tile_map, surface: pygame.Surface, camera) -> None:
        if not self._loaded:
            self._load_sprites()

        if self._tile_cache is None or tile_map._tiles_dirty:
            self._build_tile_cache(tile_map)

        zoom = camera.zoom
        sw   = surface.get_width()
        sh   = surface.get_height()

        src_x  = max(0, int(camera.x))
        src_y  = max(0, int(camera.y))
        src_x2 = min(tile_map.pixel_width,  int(math.ceil(camera.x + sw / zoom)) + 1)
        src_y2 = min(tile_map.pixel_height, int(math.ceil(camera.y + sh / zoom)) + 1)
        src_w  = max(1, src_x2 - src_x)
        src_h  = max(1, src_y2 - src_y)

        dst_x = int((src_x - camera.x) * zoom)
        dst_y = int((src_y - camera.y) * zoom)
        dst_w = max(1, int(src_w * zoom))
        dst_h = max(1, int(src_h * zoom))

        sub = self._tile_cache.subsurface((src_x, src_y, src_w, src_h))
        surface.blit(pygame.transform.scale(sub, (dst_w, dst_h)), (dst_x, dst_y))
