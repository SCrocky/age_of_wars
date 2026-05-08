import json
import math
import random
from map import TileMap, TILE_SIZE
from entities.archer import Archer
from entities.lancer import Lancer
from entities.warrior import Warrior
from entities.monk import Monk
from entities.pawn import Pawn
from entities.building import Building, Castle, Archery, Barracks, House, Tower, Monastery
from entities.resource import GoldNode, WoodNode, MeatNode
from entities.projectile import Arrow
from entities.blueprint import Blueprint
from entities.teams import teams_from_scene

_BUILDING_CLS = {
    "Castle":    Castle,
    "Archery":   Archery,
    "Barracks":  Barracks,
    "House":     House,
    "Tower":     Tower,
    "Monastery": Monastery,
}
_UNIT_CLS = {
    "Archer":  Archer,
    "Lancer":  Lancer,
    "Warrior": Warrior,
    "Monk":    Monk,
}


class Game:
    def __init__(self, scene_path: str):
        self.units:      list            = []
        self.pawns:      list[Pawn]      = []
        self.arrows:     list[Arrow]     = []
        self.buildings:  list[Building]  = []
        self.blueprints: list[Blueprint] = []
        self.resources:  list            = []

        self.teams: list[str] = []
        self.economy: dict[str, dict[str, int]] = {}

        self._next_entity_id: int = 1
        self._load_scene(scene_path)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _assign_id(self, entity):
        entity.entity_id = self._next_entity_id
        self._next_entity_id += 1
        return entity

    def save(self, path: str) -> None:
        """Serialize current game state to a JSON save file."""
        import json, os
        from datetime import datetime, timezone
        from entities.building import House, Tower

        buildings_out = []
        for b in self.buildings:
            if not b.alive:
                continue
            entry = {"id": b.entity_id, "type": type(b).__name__, "x": b.x, "y": b.y,
                     "team": b.team, "hp": b.hp}
            if isinstance(b, House):
                entry["variant"] = int(b.sprite_key.split("/")[1][-1])
            if isinstance(b, Tower) and b.garrisoned_archer is not None:
                entry["garrisoned_archer"] = {"hp": b.garrisoned_archer.hp}
            buildings_out.append(entry)

        blueprints_out = []
        for bp in self.blueprints:
            if not bp.alive:
                continue
            b = bp._building
            entry = {"id": bp.entity_id, "type": type(b).__name__, "x": b.x, "y": b.y,
                     "team": b.team, "progress": bp.progress}
            if isinstance(b, House):
                entry["variant"] = int(b.sprite_key.split("/")[1][-1])
            blueprints_out.append(entry)

        units_out = []
        for u in self.units:
            if not u.alive:
                continue
            entry = {"id": u.entity_id, "type": type(u).__name__, "x": u.x, "y": u.y,
                     "team": u.team, "hp": u.hp}
            if u.attack_target is not None and getattr(u.attack_target, "alive", False):
                entry["attack_target_id"] = u.attack_target.entity_id
            units_out.append(entry)
        for p in self.pawns:
            if not p.alive:
                continue
            entry = {"id": p.entity_id, "type": "Pawn", "x": p.x, "y": p.y,
                     "team": p.team, "hp": p.hp,
                     "task": p._task.value,
                     "resource_type": p._resource_type,
                     "carried": p._carried}
            if p._resource_node is not None:
                entry["resource_node_id"] = p._resource_node.entity_id
            if p._blueprint is not None:
                entry["blueprint_id"] = p._blueprint.entity_id
            units_out.append(entry)

        resources_out = []
        for r in self.resources:
            entry = {"id": r.entity_id, "type": r.resource_type, "x": r.x, "y": r.y,
                     "amount": r.amount}
            if hasattr(r, "sprite_key"):
                n = int(r.sprite_key.split("/")[2])
                # Invert constructor formulas to recover original variant arg:
                #   WoodNode: n = (variant % 4) + 1  →  variant = n - 1
                #   GoldNode: n = max(1, min(6, variant))  →  variant = n
                entry["variant"] = n - 1 if r.resource_type == "wood" else n
            else:
                entry["variant"] = 0
            resources_out.append(entry)

        teams = list(self.economy.keys())
        data = {
            "save_version": 1,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "rows":         self.map.rows,
            "cols":         self.map.cols,
            "tile_px":      TILE_SIZE,
            "tileset":      "Tilemap_color1",
            "tiles":        self.map.tiles,
            # Stub spawns so teams_from_scene() and server seat-validation keep working.
            "spawns":       [{"team": t, "x": 0.0, "y": 0.0} for t in teams],
            "economy":      {t: dict(eco) for t, eco in self.economy.items()},
            "buildings":    buildings_out,
            "blueprints":   blueprints_out,
            "units":        units_out,
            "resources":    resources_out,
        }

        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, separators=(",", ":"))
        print(f"[game] saved → {path}")

    def _load_scene(self, path: str):
        with open(path) as f:
            scene = json.load(f)

        self.map = TileMap.from_data(scene["cols"], scene["rows"], scene["tiles"])

        self.teams = teams_from_scene(scene)
        self.economy = {
            t: {"gold": 60, "wood": 60, "meat": 60, "pop": 0, "pop_cap": 0}
            for t in self.teams
        }
        if "economy" in scene:
            for team, saved in scene["economy"].items():
                if team in self.economy:
                    for k in ("gold", "wood", "meat"):
                        if k in saved:
                            self.economy[team][k] = saved[k]

        # Maps saved entity_id → newly created entity for cross-reference resolution.
        _saved_id_map: dict[int, object] = {}

        for b_data in scene.get("buildings", []):
            cls = _BUILDING_CLS.get(b_data["type"])
            if cls is None:
                continue
            kw = {}
            if b_data["type"] == "House":
                kw["variant"] = b_data.get("variant", 1)
            building = self._assign_id(cls(b_data["x"], b_data["y"], team=b_data["team"], **kw))
            self.map.clear_area(building.x, building.y, tile_radius=4)
            building.on_place(self.map)
            if "hp" in b_data:
                building.hp = b_data["hp"]
            if isinstance(building, Tower) and "garrisoned_archer" in b_data:
                archer_data = b_data["garrisoned_archer"]
                archer = self._assign_id(Archer(building.x, building.y, team=building.team))
                archer.hp = archer_data.get("hp", archer.max_hp)
                building.garrison(archer)
            if "id" in b_data:
                _saved_id_map[b_data["id"]] = building
            self.buildings.append(building)

        for bp_data in scene.get("blueprints", []):
            cls = _BUILDING_CLS.get(bp_data["type"])
            if cls is None:
                continue
            kw = {}
            if bp_data["type"] == "House":
                kw["variant"] = bp_data.get("variant", 1)
            b = cls(bp_data["x"], bp_data["y"], team=bp_data["team"], **kw)
            self.map.clear_area(b.x, b.y, tile_radius=4)
            bp = self._assign_id(Blueprint(b))
            bp.progress = float(bp_data.get("progress", 0.0))
            if "id" in bp_data:
                _saved_id_map[bp_data["id"]] = bp
            self.blueprints.append(bp)

        # Collect (entity, data) pairs for cross-reference resolution after all entities loaded.
        _unit_data_pairs: list[tuple] = []
        _pawn_data_pairs: list[tuple] = []

        for u_data in scene.get("units", []):
            x, y, team = u_data["x"], u_data["y"], u_data["team"]
            if u_data["type"] == "Pawn":
                p = self._assign_id(Pawn(x, y, team=team))
                if "hp" in u_data:
                    p.hp = u_data["hp"]
                if "id" in u_data:
                    _saved_id_map[u_data["id"]] = p
                _pawn_data_pairs.append((p, u_data))
                self.pawns.append(p)
            else:
                cls = _UNIT_CLS.get(u_data["type"])
                if cls:
                    u = self._assign_id(cls(x, y, team=team))
                    if "hp" in u_data:
                        u.hp = u_data["hp"]
                    if "id" in u_data:
                        _saved_id_map[u_data["id"]] = u
                    _unit_data_pairs.append((u, u_data))
                    self.units.append(u)

        for r_data in scene.get("resources", []):
            x, y, variant = r_data["x"], r_data["y"], r_data.get("variant", 0)
            rtype = r_data["type"]
            if rtype == "wood":
                node = self._assign_id(WoodNode(x, y, variant=variant))
            elif rtype == "gold":
                node = self._assign_id(GoldNode(x, y, variant=variant))
            elif rtype == "meat":
                node = self._assign_id(MeatNode(x, y))
            else:
                continue
            if "amount" in r_data:
                node.amount = r_data["amount"]
            if "id" in r_data:
                _saved_id_map[r_data["id"]] = node
            self.resources.append(node)

        # --- Second pass: resolve cross-references ---

        from entities.pawn import Task as PawnTask
        _valid_task_values = {t.value for t in PawnTask}

        for p, p_data in _pawn_data_pairs:
            task_str = p_data.get("task", "idle")
            task = PawnTask(task_str) if task_str in _valid_task_values else PawnTask.IDLE
            p._task          = task
            p._resource_type = p_data.get("resource_type", "")
            p._carried       = float(p_data.get("carried", 0.0))
            p._buildings     = tuple(self.buildings)

            if task in (PawnTask.TO_RESOURCE, PawnTask.GATHER, PawnTask.TO_DEPOT):
                p._resource_pool = self.resources
                node = _saved_id_map.get(p_data.get("resource_node_id"))
                if node is not None and not node.depleted:
                    p._resource_node = node
                elif task != PawnTask.TO_DEPOT:
                    # No valid node; pawn will idle (TO_DEPOT can proceed without a node)
                    p._task = PawnTask.IDLE

            if task in (PawnTask.TO_BUILD, PawnTask.BUILD):
                p._blueprint_pool = self.blueprints
                bp = _saved_id_map.get(p_data.get("blueprint_id"))
                if bp is not None and bp.alive:
                    p._blueprint = bp
                else:
                    p._task = PawnTask.IDLE

        for u, u_data in _unit_data_pairs:
            target_id = u_data.get("attack_target_id")
            if target_id is not None:
                target = _saved_id_map.get(target_id)
                if target is not None and getattr(target, "alive", False):
                    u.attack_target = target

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _recalc_pop(self):
        for team in self.teams:
            eco = self.economy[team]
            eco["pop"] = sum(1 for u in self.units + self.pawns if u.team == team)
            eco["pop_cap"] = sum(
                b.pop_bonus
                for b in self.buildings
                if b.team == team and b.alive and b.pop_bonus > 0
            )

    def update(self, dt: float):
        _combatants = [e for e in self.units + self.pawns + self.buildings if getattr(e, "alive", True)]
        _enemy_pool: dict[str, list] = {}
        _ally_pool:  dict[str, list] = {}
        for unit in self.units:
            if unit.team not in _enemy_pool:
                _enemy_pool[unit.team] = [e for e in _combatants if e.team != unit.team]
            if unit.team not in _ally_pool:
                _ally_pool[unit.team] = [u for u in self.units + self.pawns if u.team == unit.team]

        for unit in self.units:
            if isinstance(unit, Monk):
                unit.update(dt, self.map, _ally_pool.get(unit.team, []))
            else:
                new_arrows = unit.update(dt, self.map, _enemy_pool.get(unit.team, []))
                for arrow in new_arrows:
                    self._assign_id(arrow)
                self.arrows.extend(new_arrows)

        for building in self.buildings:
            if isinstance(building, Tower) and building.garrisoned_archer is not None:
                enemies = [e for e in self.units + self.pawns + self.buildings
                           if e.team != building.team and getattr(e, "alive", True)]
                new_arrows = building.update_garrison(dt, enemies, self.map)
                for arrow in new_arrows:
                    self._assign_id(arrow)
                self.arrows.extend(new_arrows)

        for pawn in self.pawns:
            deposit = pawn.update(dt, self.map)
            for resource_type, amount in deposit.items():
                self.economy[pawn.team][resource_type] += amount

        for arrow in self.arrows:
            arrow.update(dt)

        for res in self.resources:
            res.update(dt)

        self._apply_separation(dt)
        self._apply_building_collision()
        self._apply_tree_collision()

        next_buildings  = []
        next_blueprints = []
        for bp in self.blueprints:
            if bp.alive and bp.progress >= bp.max_hp:
                building = self._assign_id(bp.complete())
                building.on_place(self.map)
                next_buildings.append(building)
            elif bp.alive:
                next_blueprints.append(bp)
        for b in self.buildings:
            if b.alive:
                next_buildings.append(b)
            else:
                b.on_destroy(self.map)
        self.buildings  = next_buildings
        self.blueprints = next_blueprints

        self.units  = [u for u in self.units  if u.alive]
        self.pawns  = [p for p in self.pawns  if p.alive]
        self.arrows = [a for a in self.arrows if a.alive]
        self._recalc_pop()

    def _apply_building_collision(self):
        for unit in self.units + self.pawns:
            r = unit.DISPLAY_SIZE / 4
            for building in self.buildings + self.blueprints:
                hw = building.COLLISION_W / 2 + r
                hh = building.COLLISION_H / 2 + r
                dx = unit.x - building.x
                dy = unit.y - building.y
                ox = hw - abs(dx)
                oy = hh - abs(dy)
                if ox > 0 and oy > 0:
                    if ox <= oy:
                        unit.x += ox * (1 if dx >= 0 else -1)
                    else:
                        unit.y += oy * (1 if dy >= 0 else -1)

    def _apply_tree_collision(self):
        from entities.pawn import Task as PawnTask
        for unit in self.units + self.pawns:
            if getattr(unit, "_task", None) is PawnTask.GATHER:
                continue
            unit_r = unit.DISPLAY_SIZE / 4
            for res in self.resources:
                if not isinstance(res, WoodNode) or res.depleted:
                    continue
                combined_r = unit_r + WoodNode.COLLISION_RADIUS
                dx = unit.x - res.x
                dy = unit.y - (res.y + WoodNode.COLLISION_Y_OFFSET)
                dist_sq = dx * dx + dy * dy
                if 0 < dist_sq < combined_r * combined_r:
                    dist = math.sqrt(dist_sq)
                    overlap = combined_r - dist
                    unit.x += dx / dist * overlap
                    unit.y += dy / dist * overlap

    def _apply_separation(self, dt: float):
        RADIUS        = 52.0
        REPEL_FORCE   = 240.0
        ATTRACT_FORCE = 80.0
        all_units = self.units + self.pawns
        for i, a in enumerate(all_units):
            fx = fy = 0.0
            for j, b in enumerate(all_units):
                if i == j:
                    continue
                dx = a.x - b.x
                dy = a.y - b.y
                dist = math.hypot(dx, dy)
                if 0 < dist < RADIUS:
                    # Quadratic falloff: weak at the edge, strong near contact.
                    s = (RADIUS - dist) / RADIUS
                    s *= s
                    fx += dx / dist * s
                    fy += dy / dist * s
            fx *= REPEL_FORCE
            fy *= REPEL_FORCE

            target = self._unit_attract_point(a)
            if target is not None:
                tx, ty = target
                tdx = tx - a.x
                tdy = ty - a.y
                tdist = math.hypot(tdx, tdy)
                if tdist > 0:
                    fx += tdx / tdist * ATTRACT_FORCE
                    fy += tdy / tdist * ATTRACT_FORCE

            new_x = a.x + fx * dt
            new_y = a.y + fy * dt
            if self.map.is_walkable(int(new_x // TILE_SIZE), int(a.y // TILE_SIZE)):
                a.x = new_x
            if self.map.is_walkable(int(a.x // TILE_SIZE), int(new_y // TILE_SIZE)):
                a.y = new_y

    @staticmethod
    def _unit_attract_point(unit):
        if unit.path:
            col, row = unit.path[0]
            return (col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2)
        target = getattr(unit, "attack_target", None)
        if target is not None and getattr(target, "alive", True):
            return target.closest_point(unit.x, unit.y)
        return None

    # ------------------------------------------------------------------
    # Server-facing helpers
    # ------------------------------------------------------------------

    _SPAWN_TABLE = {
        "Pawn":    (Pawn,    {"meat": 20},             None),
        "Archer":  (Archer,  {"wood": 15, "meat": 30}, Archery),
        "Lancer":  (Lancer,  {"wood": 45, "meat": 10}, Barracks),
        "Warrior": (Warrior, {"gold": 35, "meat": 40}, Barracks),
        "Monk":    (Monk,    {"gold": 20, "meat": 30}, Monastery),
    }

    def _spawn_unit(self, unit_type: str, team: str = "blue", building=None):
        unit_cls, costs, building_cls = self._SPAWN_TABLE[unit_type]
        eco = self.economy[team]
        if eco["pop"] >= eco["pop_cap"]:
            return
        if any(eco.get(r, 0) < amt for r, amt in costs.items()):
            return
        spawn_building = building or next(
            (b for b in self.buildings
             if b.team == team and b.selected and b.alive
             and (building_cls is None or isinstance(b, building_cls))),
            None,
        )
        if spawn_building is None:
            return
        for r, amt in costs.items():
            eco[r] -= amt
        angle = random.uniform(0, 2 * math.pi)
        unit = self._assign_id(unit_cls(
            spawn_building.x + math.cos(angle) * 120,
            spawn_building.y + math.sin(angle) * 120,
            team=team,
        ))
        (self.pawns if unit_cls is Pawn else self.units).append(unit)

    @staticmethod
    def _formation_offsets(count: int) -> list[tuple[int, int]]:
        offsets = [(0, 0)]
        ring = 1
        while len(offsets) < count:
            for dc in range(-ring, ring + 1):
                for dr in range(-ring, ring + 1):
                    if max(abs(dc), abs(dr)) == ring:
                        offsets.append((dc, dr))
                        if len(offsets) == count:
                            return offsets
            ring += 1
        return offsets[:count]
