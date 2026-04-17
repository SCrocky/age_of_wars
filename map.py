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

        self._load_sprites()
        self._generate()

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
        rng = random.Random(42)
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
        return self.tile_at(col, row) == GRASS

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface, camera):
        zoom = camera.zoom
        scaled_tile = int(TILE_SIZE * zoom)
        if scaled_tile < 1:
            scaled_tile = 1

        # Visible tile range (add 1 tile padding to avoid edge gaps)
        start_col = max(0, int(camera.x // TILE_SIZE))
        start_row = max(0, int(camera.y // TILE_SIZE))
        end_col = min(
            self.cols,
            int((camera.x + surface.get_width() / zoom) // TILE_SIZE) + 2,
        )
        end_row = min(
            self.rows,
            int((camera.y + surface.get_height() / zoom) // TILE_SIZE) + 2,
        )

        scaled_water = pygame.transform.scale(self._water_tile, (scaled_tile, scaled_tile))

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                wx = col * TILE_SIZE
                wy = row * TILE_SIZE
                sx, sy = camera.world_to_screen(wx, wy)
                dest = pygame.Rect(int(sx), int(sy), scaled_tile, scaled_tile)

                tile_type = self.tiles[row][col]
                if tile_type == WATER:
                    surface.blit(scaled_water, dest)
                else:
                    # Expand by 1px to eliminate sub-pixel gaps between tiles
                    gapless = pygame.Rect(dest.x, dest.y, dest.w + 1, dest.h + 1)
                    pygame.draw.rect(surface, self._grass_colour, gapless)
