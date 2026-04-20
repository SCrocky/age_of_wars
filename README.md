# Age of Wars

A medieval top-down 2D real-time strategy game built with Python and Pygame.

---

## Getting Started

```bash
pip install pygame
python main.py
```

The game auto-generates a procedural map on startup. Blue faction is player-controlled; Black is the opponent.

---

## Design

| Aspect | Decision |
|---|---|
| Perspective | Top-down 2D pixel art (chibi style) |
| Scope | Player vs AI, full RTS economy + combat |
| Theme | Medieval |
| Factions | Black, Blue, Purple color variants |
| Resources | Gold, Wood, Meat |

---

## Units

| Unit | Role |
|---|---|
| Pawn | Worker — gathers Gold, Wood, Meat; constructs buildings |
| Archer | Ranged attacker |
| Lancer | Fast melee attacker with 8-directional attacks |
| Warrior | Melee tank with a guard mechanic that reduces incoming damage |

---

## Buildings

| Building | Purpose |
|---|---|
| Castle | Main base, spawns Pawns, resource depot, increases population cap |
| Archery | Trains Archers |
| Barracks | Trains Lancers and Warriors |
| House | Extra resource depot, increases population cap (3 variants) |

**Construction**: Select a Pawn, choose a building from the HUD, then right-click to place a blueprint. Multiple Pawns can build simultaneously; the building activates when complete.

---

## Resources

| Resource | Source | Tool |
|---|---|---|
| Gold | Gold stone nodes (multiple size variants) | Pickaxe |
| Wood | Trees (→ Stump when depleted) | Axe |
| Meat | Sheep (autonomous wander/flee AI) | Knife |

---

## Controls

| Input | Action |
|---|---|
| Left-click | Select unit or building |
| Shift + Left-click | Toggle selection |
| Left-click drag | Box-select multiple units |
| Right-click (empty) | Move selected units |
| Right-click (enemy) | Attack |
| Right-click (resource) | Gather (Pawns only) |
| Arrow keys / edge scroll | Pan camera |
| Mouse wheel | Zoom |
| HUD buttons | Train units / construct buildings |

---

## Core Systems

**Game Loop**
- Fixed timestep update; entities advance by elapsed time each frame.

**Map & Camera**
- Tile-based grid with GRASS and WATER terrain types and per-tile walkability.
- Camera supports keyboard pan, edge scrolling, and mouse-wheel zoom (zoom is anchored to the cursor's world position).
- Tile render cache — only visible tiles are drawn, scaled to the current zoom level.

**Entities**
- `Entity` → `Unit` (moving/fighting) / `Building` (static/production) / `Resource` (gatherable)
- Sprite surfaces are cached by transform (scale + flip) to avoid redundant scaling.

**Pathfinding**
- A* on the 8-directional tile grid with an octile heuristic.
- Diagonal movement through blocked corners is prevented.
- Units re-path periodically while chasing a moving target.
- Soft-repulsion separation keeps units from stacking on top of each other.

**Selection & Commands**
- Click to select; drag to box-select multiple units.
- Right-click dispatch: attack / gather / move based on what was clicked.
- Group movement fans units in concentric rings around the destination.

**Economy**
- Per-team Gold / Wood / Meat counters.
- Population cap is the sum of all living Castles and Houses.
- Pawns cycle through gather → carry → deposit; any living Castle or House acts as a depot.

**Combat**
- Archer: fires a homing Arrow projectile.
- Lancer: 8-directional attack animations; plays a directional defence animation when hit.
- Warrior: alternates two attack animations; guard mechanic halves damage on the first hit within each attack cooldown.

**Production**
- Buildings hold a single production queue slot.
- Trained units spawn in an arc around the building entrance.

**Blueprint System**
- Blueprints render with increasing opacity as construction progresses.
- Multiple Pawns can contribute simultaneously; the building activates at full health.

---

## Procedural Map Generation

`map_editor/create_map.py` generates maps using a Wave Function Collapse zone algorithm:

1. Divides the interior into a grid of zones.
2. Two diagonal spawn zones (Blue top-left, Black bottom-right) seed the collapse.
3. Adjacency rules bias resource-rich zones near spawns and prevent same-type blobs.
4. Resources are placed in clumps (wood clusters; gold and meat scattered).
5. Outputs a JSON map file and a PNG preview.

`map_editor/populate_map.py` adds starting buildings and Pawns to a generated map, producing the scene JSON that the game loads.

---

## File Structure

```
age_of_wars/
├── main.py               # Entry point, game loop
├── game.py               # Central state: entities, input, update, render pipeline
├── map.py                # Tile map, terrain, walkability, render cache
├── camera.py             # Viewport pan/zoom, world↔screen coordinate conversion
├── hud.py                # Resource bar, unit/building info panel, production buttons
├── render_cache.py       # Scaled/flipped surface cache
├── entities/
│   ├── entity.py         # Base class: position, HP, team, health bar
│   ├── unit.py           # Base mover: A* pathfinding, attack targeting, animation
│   ├── pawn.py           # Worker: gather→carry→deposit state machine, build
│   ├── archer.py         # Ranged: fires Arrow projectiles
│   ├── lancer.py         # Melee: 8-directional attack/defence animations
│   ├── warrior.py        # Tank: guard mechanic, high HP
│   ├── building.py       # Castle, Archery, Barracks, House + production logic
│   ├── resource.py       # GoldNode, WoodNode, MeatNode (sheep AI)
│   ├── projectile.py     # Arrow: homing, snap-to-hit
│   └── blueprint.py      # Building under construction, alpha-blended render
├── systems/
│   └── pathfinding.py    # A* with octile heuristic, corner-cut prevention
├── map_editor/
│   ├── create_map.py     # Procedural WFC map generator → JSON + PNG
│   ├── populate_map.py   # Adds starting buildings/units to a map
│   └── maps/             # Generated map files
└── assets/               # Sprites (Buildings/, Units/, Terrain/, UI_Elements/)
```

---

## Asset Structure

```
assets/
├── Buildings/
│   ├── Black Buildings/    # Castle, Barracks, Archery, House1-3
│   ├── Blue Buildings/
│   └── Purple Buildings/
├── Units/
│   ├── Black Units/
│   │   ├── Archer/         # Idle, Run, Shoot, Arrow
│   │   ├── Lancer/         # Idle, Run, Attack×8dirs, Defence×8dirs
│   │   ├── Warrior/        # Idle, Run, Attack1, Attack2
│   │   └── Pawn/           # Idle, Run, Interact per tool (Axe/Pickaxe/Knife/Hammer)
│   ├── Blue Units/
│   └── Purple Units/
├── Terrain/
│   ├── Tileset/            # Tilemap color variants, Water Background, Water Foam
│   └── Resources/
│       ├── Gold/           # Gold_Resource, Gold Stones variants (+ Highlight variants)
│       ├── Wood/           # Tree variants, Stump variants
│       └── Meat/           # Sheep_Idle, Sheep_Move, Sheep_Grass
└── UI_Elements/
```

---

## Milestones

| # | Milestone | Status |
|---|---|---|
| 1 | Foundation: game loop, tile map, camera, sprites on screen | ✅ Done |
| 2 | Units: animated units, A* pathfinding, click-to-move | ✅ Done |
| 3 | Combat: selection box, attack commands, health bars, death | ✅ Done |
| 4 | Economy: Pawn gathering, resource counters, Castle drop-off | ✅ Done |
| 5 | Buildings: place/train from buildings, population cap | ✅ Done |
| 6 | AI: opponent gathers, trains units, and attacks player | 🔲 Planned |
| 7 | Polish: minimap, sounds, win/lose conditions | 🔲 Planned |
