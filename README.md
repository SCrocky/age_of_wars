# Age of Wars

A medieval top-down 2D real-time strategy game built with Python and Pygame.

---

## Design Decisions

| Aspect | Decision |
|---|---|
| Perspective | Top-down 2D pixel art (chibi style) |
| Scope | Start with combat + basic economy; expand to full RTS |
| Opponents | Player vs AI |
| Theme | Medieval |
| Factions | Multiple color variants (Black, Blue, Purple, …) |
| Resources | Gold, Wood, Meat |

---

## Units

| Unit | Role | Animations |
|---|---|---|
| Pawn | Worker — gathers Gold, Wood, Meat | Idle, Run, Interact (per tool) |
| Archer | Ranged attacker | Idle, Run, Shoot |
| Lancer | Melee attacker (directional) | Idle, Run, Attack, Defence (8 dirs) |
| Monk | Healer | Idle, Run, Heal |

---

## Buildings

| Building | Purpose |
|---|---|
| Castle | Main base / spawn point |
| Barracks | Train Lancers |
| Archery | Train Archers |
| Monastery | Train Monks |
| House | Increase population cap |
| Tower | Defensive structure |

---

## Resources

| Resource | Source | Gathered by |
|---|---|---|
| Gold | Gold stones / Gold resource nodes | Pawn (Pickaxe) |
| Wood | Trees (→ Stump when depleted) | Pawn (Axe) |
| Meat | Sheep | Pawn (Knife) |

---

## Core Systems

**1. Game Loop**
- Fixed-timestep update (logic) + variable render
- State management: Menu → Playing → Paused / Game Over

**2. Map / World**
- Tile-based grid (top-down)
- Terrain types and walkability
- Resource nodes placed on the map
- Camera with pan and zoom

**3. Entities**
- Base `Entity` class: position, health, team/faction color
- `Unit` subclass: movement, pathfinding, commands, animation
- `Building` subclass: production queues, garrison
- `Resource` subclass: current amount, depletion state

**4. Pathfinding**
- A* on the tile grid
- 8-directional movement (matching Lancer sprite dirs)
- Unit steering to avoid clumping

**5. Selection & Commands**
- Click or drag-box to select units
- Right-click to move / attack / gather
- Command queue per unit

**6. Economy**
- Pawns carry resources back to the Castle
- Spending resources to train units or construct buildings
- Population cap enforced by Houses

**7. Combat**
- Attack range, damage, cooldown per unit type
- Archer projectile (Arrow sprite)
- Monk healing aura (Heal_Effect sprite)

**8. AI Opponent**
- Gather resources, train units, attack player base
- Simple priority: economy first, then military

**9. UI**
- Resource counters (Gold / Wood / Meat) — top bar
- Selected unit / building info panel — bottom bar
- Minimap — bottom-right corner

---

## Asset Structure

```
assets/
├── Buildings/
│   ├── Black Buildings/    # Castle, Barracks, Archery, Monastery, Tower, House1-3
│   ├── Blue Buildings/
│   └── Purple Buildings/
├── Units/
│   ├── Black Units/
│   │   ├── Archer/         # Archer_Idle.png, Archer_Run.png, Archer_Shoot.png, Arrow.png
│   │   ├── Lancer/         # Directional: Up/Down/Right/UpRight/DownRight × Attack/Defence + Idle/Run
│   │   ├── Monk/           # Idle.png, Run.png, Heal.png, Heal_Effect.png
│   │   └── Pawn/           # Idle/Run/Interact per tool (Axe, Pickaxe, Knife, Hammer, Gold, Wood, Meat)
│   ├── Blue Units/
│   └── Purple Units/
├── Terrain/
│   ├── Tileset/            # Tilemap_color1-5.png, Water Background, Water Foam
│   ├── Resources/
│   │   ├── Gold/           # Gold_Resource.png, Gold Stones 1-6 (+ Highlight variants)
│   │   ├── Wood/           # Tree1-4.png, Stump 1-4.png
│   │   └── Meat/           # Sheep_Idle.png, Sheep_Move.png, Sheep_Grass.png
│   └── Decorations/        # Bushes, Rocks, Clouds, Water Rocks, Rubber Duck
├── Particle_FX/
└── UI_Elements/
```

---

## Planned File Structure

```
age_of_wars/
├── main.py               # Entry point, game loop
├── game.py               # Game state manager
├── map.py                # Tile map, terrain, resource placement
├── camera.py             # Viewport, pan/zoom
├── entities/
│   ├── entity.py         # Base class
│   ├── unit.py           # Moving, fighting, animated units
│   ├── building.py       # Structures, production queues
│   └── resource.py       # Resource nodes (gold, trees, sheep)
├── systems/
│   ├── pathfinding.py    # A* on tile grid
│   ├── combat.py         # Attack/heal resolution
│   ├── economy.py        # Resource tracking, population cap
│   └── selection.py      # Mouse selection (click + drag-box)
├── ai/
│   └── opponent.py       # Simple AI: gather → build → attack
├── ui/
│   ├── hud.py            # Resource bar, unit info panel
│   └── minimap.py        # Minimap renderer
├── assets/               # Sprites, sounds (see above)
└── README.md
```

---

## Milestones

1. **Milestone 1 — Foundation**: Game loop, tile map, camera, placeholder sprites on screen
2. **Milestone 2 — Units**: Render animated units, A* pathfinding, click-to-move
3. **Milestone 3 — Combat**: Selection box, attack commands, health bars, death
4. **Milestone 4 — Economy**: Pawn gathering, resource counters, drop-off at Castle
5. **Milestone 5 — Buildings**: Place/train from buildings, population cap
6. **Milestone 6 — AI**: Opponent gathers, trains, and attacks
7. **Milestone 7 — Polish**: UI panels, minimap, sounds, win/lose condition
