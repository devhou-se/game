#!/usr/bin/env python3
"""stamp_prefab.py — surgically add (or lift) prefabs in an EXISTING room.

Generated rooms get their buildings from `b.stamp()` in their generator. The
ported rooms (Tokyo, Market, Park, Palace) have no such step: their map lives in
config.json. This is the same stamp for those rooms, with the checks the
adjust-game skill asks for done up front, so a placement cannot silently eat a
door, bury an NPC or wall off part of the map:

  * the prefab lies inside the room;
  * its sprites do not overlap another standing sprite (trees, buildings,
    lamps...) — `--allow-overlap` to permit it when the overlap is intended;
  * none of its solid cells is already solid;
  * no cell its sprites cover - solid OR walk-behind - is a transporter or a
    cell an NPC stands on in any of its dated states (a door or a character
    under a roof would be drawn hidden behind the building);
  * flood-fill: every walkable cell that could be reached from the room's
    transporters before can still be reached after (except the cells the
    prefab itself makes solid).

Nothing is written unless every check passes (or with --dry-run, ever).

    python3 tools/stamp_prefab.py Market --add discount-store 46 22
    python3 tools/stamp_prefab.py Park --remove sakura-small 5 20 --add machiya-black 4 17
    python3 tools/stamp_prefab.py Palace --add highrise-yellow 48 6 --dry-run

`--remove <prefab> x y` is the inverse of a stamp at that cell (the prefab's
sprites must be there, and it lifts the colliders of the prefab AS IT IS NOW -
if you are changing a prefab's collision, remove the old one from the rooms
before re-running make_prefabs.py). A collider cell that another standing
sprite still covers is kept. Removals run before additions. Doors are sealed
(a wired interior needs a transporter — do that in a script).

Then, as for any map edit:  config_to_tiled.py <Room>;  play.js lint <Room>.
Run from gamev2/.
"""
import json, struct, sys
from collections import deque
import prefab as _prefab

STANDING = ('Non-Collidables', 'Collidables', 'Other', 'Tops')
Z = {'Floor': 0, 'Over Floor': 1, 'Water': 1, 'Non-Collidables': 4, 'Collidables': 5, 'Other': 6, 'Tops': 7}


def png_cells(key):
    with open(f'assets/sprites/{key}.png', 'rb') as f:
        f.read(16); w, h = struct.unpack('>II', f.read(8))
    return max(1, round(w / 64)), max(1, round(h / 64))


class Room:
    def __init__(self, cfg, name):
        self.cfg, self.name, self.room = cfg, name, cfg['rooms'][name]
        self.pal = cfg['tilePalette']
        self.W, self.H = self.room['worldWidth'] // 64, self.room['worldHeight'] // 64
        self.layers = {L['name']: L for L in self.room['layers']}

    def layer(self, name):
        """The named layer, created (in z order) if the room never had one."""
        if name not in self.layers:
            L = {'name': name, 'z': Z[name], 'collision': False, 'tiles': {}}
            at = next((i for i, o in enumerate(self.room['layers']) if o['z'] > L['z'] or o['collision']),
                      len(self.room['layers']))
            self.room['layers'].insert(at, L)
            self.layers[name] = L
        return self.layers[name]

    def pidx(self, key):
        if key not in self.pal:
            self.pal.append(key)
        return self.pal.index(key)

    def solid(self):
        return {tuple(map(int, xy.split(','))) for L in self.room['layers'] if L['collision'] for xy in L['tiles']}

    def collider_layer(self):
        return self.layers.get('Colliders') or next(L for L in self.room['layers'] if L['collision'])

    def standing(self):
        """cell -> sprite key, for every cell covered by a standing sprite."""
        out = {}
        for n in STANDING:
            for xy, i in self.layers.get(n, {'tiles': {}})['tiles'].items():
                x, y = map(int, xy.split(','))
                w, h = png_cells(self.pal[i])
                for a in range(w):
                    for b in range(h):
                        out.setdefault((x + a, y + b), self.pal[i])
        return out

    def npc_cells(self):
        out = {}
        for n in self.room.get('npcs', []):
            for s in [n] + list(n.get('states', {}).values()):
                if 'gridX' in s and 'gridY' in s:
                    out[(s['gridX'], s['gridY'])] = n.get('name', '?')
        return out

    def portals(self):
        return {(t['gridX'], t['gridY']): t['targetRoom'] for t in self.room.get('transporters', [])}

    def reachable(self):
        """Walkable cells reachable (4-way) from any transporter."""
        solid = self.solid()
        floor = {tuple(map(int, xy.split(','))) for xy in self.layers['Floor']['tiles']}
        ok = lambda c: c in floor and c not in solid and 0 <= c[0] < self.W and 0 <= c[1] < self.H
        seen, todo = set(), deque(c for c in self.portals() if ok(c))
        seen.update(todo)
        while todo:
            x, y = todo.popleft()
            for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if c not in seen and ok(c):
                    seen.add(c); todo.append(c)
        return seen


def footprint(pf, x, y):
    cells = set()
    for (_layer, dx, dy, key) in pf['sprites']:
        w, h = png_cells(key)
        cells |= {(x + dx + a, y + dy + b) for a in range(w) for b in range(h)}
    return cells


def remove(room, pf, x, y, errors):
    for (layer, dx, dy, key) in pf['sprites']:
        tiles = room.layer(layer)['tiles']
        xy = f'{x + dx},{y + dy}'
        if room.pal[tiles.get(xy, 0)] != key or xy not in tiles:
            errors.append(f'remove {pf["name"]} @{x},{y}: no {key} on {layer} at {xy}')
            return
    for (layer, dx, dy, _key) in pf['sprites']:
        del room.layer(layer)['tiles'][f'{x + dx},{y + dy}']
    # lift the colliders too - except under a neighbour: a cell another standing
    # sprite still covers keeps its collider (it may be that object's own)
    coll, still = room.collider_layer()['tiles'], room.standing()
    for (dx, dy) in sorted(set(pf['colliders']) | set(pf['doors'])):
        c = (x + dx, y + dy)
        if c in still:
            print(f'{room.name}: kept the collider at {c} (under {still[c]})')
        else:
            coll.pop(f'{c[0]},{c[1]}', None)


def add(room, pf, x, y, errors, allow_overlap=False):
    tag = f'add {pf["name"]} @{x},{y}'
    if not (0 <= x and 0 <= y and x + pf['w'] <= room.W and y + pf['h'] <= room.H):
        errors.append(f'{tag}: outside the {room.W}x{room.H} room'); return
    solid_new = {(x + dx, y + dy) for (dx, dy) in set(pf['colliders']) | set(pf['doors'])}
    standing = room.standing()
    hits = sorted({standing[c] for c in footprint(pf, x, y) if c in standing})
    if hits and not allow_overlap:
        errors.append(f'{tag}: overlaps {", ".join(hits)}')
    already = sorted(solid_new & room.solid())
    if already:
        errors.append(f'{tag}: cells already solid {already[:6]}')
    covered = footprint(pf, x, y) | solid_new               # solid cells and the walk-behind rows
    for cells, what in ((room.portals(), 'transporter to'), (room.npc_cells(), 'NPC')):
        for c in sorted(covered & set(cells)):
            how = 'bury' if c in solid_new else 'hide (behind the sprite)'
            errors.append(f'{tag}: would {how} {what} {cells[c]} at {c}')
    put = lambda layer, cx, cy, key: room.layer(layer)['tiles'].__setitem__(f'{cx},{cy}', room.pidx(key))
    solid = lambda cx, cy: room.collider_layer()['tiles'].__setitem__(f'{cx},{cy}', room.pidx('gk_blank'))
    _prefab.stamp(pf, x, y, put, solid, seal_doors=True)
    return solid_new


def main(argv):
    if len(argv) < 2 or argv[1].startswith('-'):
        sys.exit(__doc__)
    name, args = argv[1], argv[2:]
    dry = '--dry-run' in args
    allow = '--allow-overlap' in args
    ops, i = [], 0
    while i < len(args):
        if args[i] in ('--add', '--remove'):
            ops.append((args[i][2:], args[i + 1], int(args[i + 2]), int(args[i + 3]))); i += 4
        else:
            i += 1
    raw = open('config.json').read()
    cfg = json.loads(raw)
    room = Room(cfg, name)
    before, errors, made_solid = room.reachable(), [], set()
    for kind, pfname, x, y in sorted(ops, key=lambda o: o[0] != 'remove'):
        pf = _prefab.load_prefab(pfname)
        if kind == 'remove':
            remove(room, pf, x, y, errors)
        else:
            made_solid |= add(room, pf, x, y, errors, allow) or set()
    after = room.reachable()
    lost = sorted(before - after - made_solid)
    if lost:
        errors.append(f'{len(lost)} walkable cells cut off from the transporters, e.g. {lost[:8]}')
    for kind, pfname, x, y in ops:
        print(f'{name}: {kind} {pfname} @{x},{y}')
    print(f'{name}: reachable walkable cells {len(before)} -> {len(after)} '
          f'({len(made_solid)} made solid, {len(after - before)} opened up)')
    if errors:
        sys.exit('NOT WRITTEN:\n  ' + '\n  '.join(errors))
    if dry:
        print('dry run - config.json not written'); return
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    print(f'wrote config.json - now: config_to_tiled.py {name}; play.js lint {name}')


if __name__ == '__main__':
    main(sys.argv)
