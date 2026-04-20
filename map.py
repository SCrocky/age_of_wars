import math
import pygame
import random

TILE_SIZE = 64  # world pixels per tile

# Tile type constants
WATER = 0
GRASS = 1


class TileMap:
    """
    A grid-based tile map.

    Tile types
    ----------
    WATER – rendered with the tiling water sprite
    GRASS – rendered with a grass terrain tile from the tileset sheet
    """

    # How many columns/rows are in the tileset sheet
    _SHEET_COLS = 9
    _SHEET_ROWS = 6

    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.tiles: list[list[int]] = []
        self.blocked: set[tuple[int, int]] = set()
        self._tile_cache: pygame.Surface | None = None

        self._load_sprites()
        self._generate()

    @classmethod
    def from_data(cls, cols: int, rows: int, tiles: list[list[int]]) -> "TileMap":
        """Create a TileMap from a pre-built tile grid (skips procedural generation)."""
        obj = object.__new__(cls)
        obj.cols = cols
        obj.rows = rows
        obj.tiles = [list(row) for row in tiles]
        obj.blocked = set()
        obj._tile_cache = None
        obj._load_sprites()
        return obj

    # ------------------------------------------------------------------
    # Asset loading
    # ------------------------------------------------------------------

    def _load_sprites(self):
        self._water_tile = pygame.image.load(
            "assets/Terrain/Tileset/Water Background color.png"
        ).convert_alpha()

        # The tileset sheet contains organic terrain CHUNKS (not solid square ground
        # tiles).  We use them as decorations drawn on top of solid colour fills.
        sheet = pygame.image.load(
            "assets/Terrain/Tileset/Tilemap_color1.png"
        ).convert_alpha()
        self._sheet_tiles: list[pygame.Surface] = []
        for row in range(self._SHEET_ROWS):
            for col in range(self._SHEET_COLS):
                tile = sheet.subsurface(
                    pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
                self._sheet_tiles.append(tile)

        # Solid base colours
        self._grass_colour = (106, 153, 56)   # muted green
        self._water_colour = (56, 120, 153)   # muted blue (matches water sprite)

    # ------------------------------------------------------------------
    # Map generation
    # ------------------------------------------------------------------

    def _generate(self):
        """Generate a simple island: grass in the interior, water on the border."""
        border = 3  # water border thickness in tiles

        self.tiles = []
        for row in range(self.rows):
            tile_row = []
            for col in range(self.cols):
                if (
                    col < border
                    or col >= self.cols - border
                    or row < border
                    or row >= self.rows - border
                ):
                    tile_row.append(WATER)
                else:
                    tile_row.append(GRASS)
            self.tiles.append(tile_row)

        # Scatter some water "lakes" inside the island for variety
        rng = random.Random()
        for _ in range(8):
            lx = rng.randint(border + 1, self.cols - border - 4)
            ly = rng.randint(border + 1, self.rows - border - 4)
            lw = rng.randint(2, 4)
            lh = rng.randint(2, 3)
            for r in range(ly, min(ly + lh, self.rows - border)):
                for c in range(lx, min(lx + lw, self.cols - border)):
                    self.tiles[r][c] = WATER

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pixel_width(self) -> int:
        return self.cols * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self.rows * TILE_SIZE

    def tile_at(self, col: int, row: int) -> int:
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.tiles[row][col]
        return WATER

    def world_to_tile(self, wx: float, wy: float) -> tuple[int, int]:
        return int(wx // TILE_SIZE), int(wy // TILE_SIZE)

    def is_walkable(self, col: int, row: int) -> bool:
        return self.tile_at(col, row) == GRASS and (col, row) not in self.blocked

    def clear_area(self, world_x: float, world_y: float, tile_radius: int):
        """Force all tiles within tile_radius of a world position to GRASS."""
        cx = int(world_x // TILE_SIZE)
        cy = int(world_y // TILE_SIZE)
        for dr in range(-tile_radius, tile_radius + 1):
            for dc in range(-tile_radius, tile_radius + 1):
                col, row = cx + dc, cy + dr
                if 0 <= col < self.cols and 0 <= row < self.rows:
                    self.tiles[row][col] = GRASS
        self._tile_cache = None

    def block_area(self, world_x: float, world_y: float, half_w: int, half_h: int):
        """Mark a rectangular tile area as unwalkable without changing its visual."""
        cx = int(world_x // TILE_SIZE)
        cy = int(world_y // TILE_SIZE)
        for dr in range(-half_h, half_h + 1):
            for dc in range(-half_w, half_w + 1):
                col, row = cx + dc, cy + dr
                if 0 <= col < self.cols and 0 <= row < self.rows:
                    self.blocked.add((col, row))

    def unblock_area(self, world_x: float, world_y: float, half_w: int, half_h: int):
        """Remove a rectangular tile area from the blocked set."""
        cx = int(world_x // TILE_SIZE)
        cy = int(world_y // TILE_SIZE)
        for dr in range(-half_h, half_h + 1):
            for dc in range(-half_w, half_w + 1):
                self.blocked.discard((cx + dc, cy + dr))

    def nearest_walkable(self, col: int, row: int) -> tuple[int, int]:
        """Return the walkable tile closest to (col, row) by Euclidean distance."""
        if self.is_walkable(col, row):
            return col, row
        for r in range(1, 8):
            candidates = [
                (math.hypot(dc, dr), col + dc, row + dr)
                for dc in range(-r, r + 1)
                for dr in range(-r, r + 1)
                if (abs(dc) == r or abs(dr) == r)
                and self.is_walkable(col + dc, row + dr)
            ]
            if candidates:
                _, c, ro = min(candidates)
                return c, ro
        return col, row

    def block_tiles(self, world_x: float, world_y: float, offsets: list[tuple[int, int]]):
        """Mark specific tile offsets (dc, dr) relative to a world position as unwalkable."""
        cx = int(world_x // TILE_SIZE)
        cy = int(world_y // TILE_SIZE)
        for dc, dr in offsets:
            col, row = cx + dc, cy + dr
            if 0 <= col < self.cols and 0 <= row < self.rows:
                self.blocked.add((col, row))

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _build_tile_cache(self):
        """Pre-render all tiles into a full-resolution Surface (zoom=1.0)."""
        surf = pygame.Surface((self.pixel_width, self.pixel_height))
        for row in range(self.rows):
            for col in range(self.cols):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                if self.tiles[row][col] == WATER:
                    surf.blit(self._water_tile, (x, y))
                else:
                    # +1 to eliminate sub-pixel gaps when scaled
                    pygame.draw.rect(surf, self._grass_colour,
                                     (x, y, TILE_SIZE + 1, TILE_SIZE + 1))
        self._tile_cache = surf

    def render(self, surface: pygame.Surface, camera):
        if self._tile_cache is None:
            self._build_tile_cache()

        zoom = camera.zoom
        sw = surface.get_width()
        sh = surface.get_height()

        # Visible world region (clamped to map bounds)
        src_x = max(0, int(camera.x))
        src_y = max(0, int(camera.y))
        src_x2 = min(self.pixel_width,  int(math.ceil(camera.x + sw / zoom)) + 1)
        src_y2 = min(self.pixel_height, int(math.ceil(camera.y + sh / zoom)) + 1)
        src_w = max(1, src_x2 - src_x)
        src_h = max(1, src_y2 - src_y)

        # Destination on screen (offset accounts for sub-pixel camera position)
        dst_x = int((src_x - camera.x) * zoom)
        dst_y = int((src_y - camera.y) * zoom)
        dst_w = max(1, int(src_w * zoom))
        dst_h = max(1, int(src_h * zoom))

        sub = self._tile_cache.subsurface((src_x, src_y, src_w, src_h))
        surface.blit(pygame.transform.scale(sub, (dst_w, dst_h)), (dst_x, dst_y))
