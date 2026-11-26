"""roomgen.py — the room-building toolkit behind generate_machi.py and the
/generate-room skill. Compose a room from autotiled floor terrains + prefabs
(tiled/prefabs/*.tmj, authored in the Tiled app), with the engine's collision
and depth conventions baked in.

Typical script:

    import roomgen as rg
    cfg = rg.load_config()
    b = rg.Builder(30, 22)                       # min 20x15 (camera viewport)
    b.fill('grass-autotile')                     # base ground everywhere
    b.autotile('gravel-autotile', rg.rect(3, 10, 26, 11))   # a path
    b.pond(5, 4, 10)                             # water, 2 rows tall
    b.stamp('house-blue', 8, 6)                  # prefab (door sealed)
    door = b.stamp('seven-eleven', 20, 6, seal=False)[0]    # open door cell
    cfg['rooms']['MyRoom'] = b.room('MyRoom', npcs=[], transporters=[...])
    rg.save_config(cfg)

Then: config_to_tiled.py MyRoom (and any room whose transporters you touched —
the game reads the .tmj!), then play.js lint MyRoom.
"""
import json, os
import prefab as _prefab

LAYER_NAMES = ['Floor', 'Over Floor', 'Water', 'Non-Collidables', 'Collidables', 'Other', 'Tops', 'Colliders']
FULL9 = {'center', 'edge-n', 'edge-e', 'edge-s', 'edge-w', 'corner-nw', 'corner-ne', 'corner-sw', 'corner-se'}

_cfg = None
_pal = None
_idx = None
_PF = {}


# The houses tools/generate_houses.py can open (issue #208): the sprite on
# Collidables that carries a house's front door -> the door cell, relative to
# that sprite's own top-left cell. The three townhouse prefabs (house-blue /
# -red / -black) end in a 3x1 `building-entrance`; a machiya is one 5x5 sprite.
HOUSE_DOORS = {
    'building-entrance-1_0_0': (1, 0), 'building-entrance-2_0_0': (1, 0), 'building-entrance-3_0_0': (1, 0),
    'machiya-black_0_0': (2, 4), 'machiya-red_0_0': (2, 4), 'machiya-blue_0_0': (2, 4),
}
HOUSE_PREFIX = 'House'      # rooms.House<Town><n>, the interiors generate_houses.py owns
# The towers the same generator gives a lobby (issue #216): the one sprite a
# high-rise, an office tower or a block of flats is -> its door cells, relative
# to the sprite's top-left cell (the bottom row, as building() in
# make_prefabs.py puts them; the glass tower's doors are a pair). A landmark
# tower (Tokyo Tower, the TV tower, Fukuoka Tower, a castle) is not in here.
TOWER_DOORS = {
    'highrise-yellow_0_0': [(1, 7)], 'highrise-blue_0_0': [(2, 10)], 'highrise-glass_0_0': [(1, 9), (2, 9)],
    'highrise-apartment_0_0': [(2, 7)], 'midrise-apartment_0_0': [(2, 5)],
}
LOBBY_PREFIX = 'Lobby'      # rooms.Lobby<Town><n>
# The shrine halls tools/generate_shrines.py can open (issue #212): the hall's
# sprite on Collidables -> its door cells, relative to the sprite's top-left
# cell (the top step of the `shrine` / `shrine-red` prefab; Dazaifu's own hall).
SHRINE_DOORS = {'shrine-building_0_0': [(1, 4)], 'dazaifu-hall_0_0': [(3, 4)]}
SHRINE_PREFIX = 'Shrine'    # rooms.Shrine<Town><n>, the worship halls generate_shrines.py owns
# Every kind of interior whose door a town generator neither builds nor knows
# about, and save_config therefore keeps through a town rebuild (keep_house_doors):
# room-key prefix -> (the key on the interior that says its generator owns it, its door sprites).
# A new kind is one more row here, and a `{host, door}` marker on its rooms.
OWNED_DOORS = {HOUSE_PREFIX: ('house', {k: [v] for k, v in HOUSE_DOORS.items()}),
               LOBBY_PREFIX: ('lobby', TOWER_DOORS),
               SHRINE_PREFIX: ('shrine', SHRINE_DOORS)}
_house_doors = {}           # room -> its transporters as loaded, when any leads into an OWNED_DOORS interior


def owned_door(cfg, t):
    """The door sprites of the kind of interior transporter `t` leads into, if
    its generator owns that interior (a house, a lobby or a worship hall that exists)."""
    for prefix, (marker, sprites) in OWNED_DOORS.items():
        owner = cfg['rooms'].get(t['targetRoom'], {}).get(marker) if t['targetRoom'].startswith(prefix) else None
        # ...and still counts this cell among its doors (one of a tower's pair may have been shut)
        if owner and [t['gridX'], t['gridY']] in (owner.get('doors') or [owner.get('door')]):
            return sprites
    return None


def house_door_at(room, x, y, sprites=None):
    """Whether (x, y) of `room` is the front door of a house that stands there
    (or, given another kind's `sprites` - a lobby's, a shrine's - a door of one of those)."""
    sprites = sprites or OWNED_DOORS[HOUSE_PREFIX][1]
    for layer in room.get('layers', []):
        if layer['name'] != 'Collidables':
            continue
        for key, cells in sprites.items():
            for dx, dy in cells:
                idx = layer['tiles'].get(f'{x - dx},{y - dy}')
                if idx is not None and _pal[idx] == key:
                    return True
    return False


def load_config(path='config.json'):
    global _cfg, _pal, _idx
    _cfg = json.load(open(path))
    _pal = _cfg['tilePalette']
    _idx = {k: i for i, k in enumerate(_pal)}
    _house_doors.clear()
    for key, room in _cfg['rooms'].items():
        ts = room.get('transporters', [])
        if any(owned_door(_cfg, t) for t in ts):
            _house_doors[key] = json.loads(json.dumps(ts))
    return _cfg


def keep_house_doors(cfg):
    """Put back the house doors a rebuild dropped (issue #208).

    A town generator rebuilds its room from scratch and stamps every house
    sealed; the doors into the house interiors are wired afterwards by
    generate_houses.py, which is run per town and long after the town's own
    generator was written. Rather than have every town generator know about
    them (the way each keeps its 7-Eleven door with kept_door), save_config
    restores them: a transporter the room had on load that led into a
    `House...` room which still exists is put back, with its doorway
    unsealed, when the rebuilt room has no transporter on that cell and the
    house still stands there (house_door_at - a house the generator moved or
    removed stays sealed until generate_houses.py is run for the town). The
    list keeps the order it was loaded in (kept_order), so a town generator
    re-run on an unchanged world still leaves config.json byte-identical.
    The doors into a tower's lobby (issue #216) and into a shrine's worship
    hall (issue #212, generate_shrines.py) are kept the same way, and so is
    every kind of interior in OWNED_DOORS."""
    for key, before in _house_doors.items():
        room = cfg['rooms'].get(key)
        if room is None:
            continue
        ts = room.setdefault('transporters', [])
        taken = {(t['gridX'], t['gridY']) for t in ts}
        back = [t for t in before
                if owned_door(cfg, t) and (t['gridX'], t['gridY']) not in taken
                and house_door_at(room, t['gridX'], t['gridY'], owned_door(cfg, t))]
        if not back:
            continue
        for layer in room['layers']:
            if layer['name'] == 'Colliders':
                for t in back:
                    layer['tiles'].pop(f"{t['gridX']},{t['gridY']}", None)
        room['transporters'] = kept_order({'transporters': before}, ts + back)


def save_config(cfg=None, path='config.json'):
    cfg = cfg or _cfg
    keep_house_doors(cfg)
    open(path, 'w').write(json.dumps(cfg, indent=2, sort_keys=True))


def pidx(key):
    if key not in _idx:
        _pal.append(key); _idx[key] = len(_pal) - 1
    return _idx[key]


def rect(x0, y0, x1, y1):
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


PICKET_LEFT, PICKET_MID, PICKET_RIGHT = ('fence-garden-outside_2_5',
                                         'fence-garden-outside_3_5',
                                         'fence-garden-outside_4_5')


def picket_fences(layers):
    """Rewrite every horizontal run of fence-barriers_* tiles (what
    Builder.fence() lays: crowd-barrier pieces that read as junk when cycled)
    into the fence-garden-outside picket set - left end, middle pieces, right
    end. Colliders are untouched (the cells are already solid).

    layers is {layer name: {'x,y': palette index}}. Returns {layer name: cells
    re-fenced}. Shared by Builder.finish() and tools/fix_fences.py."""
    done = {}
    for name, tiles in layers.items():
        cells = sorted(tuple(map(int, xy.split(','))) for xy, idx in tiles.items()
                       if _pal[idx].startswith('fence-barriers'))
        if not cells:
            continue
        cellset = set(cells)
        for (x, y) in cells:
            has_l, has_r = (x - 1, y) in cellset, (x + 1, y) in cellset
            piece = PICKET_MID if (has_l and has_r) else PICKET_LEFT if not has_l else PICKET_RIGHT
            tiles[f'{x},{y}'] = pidx(piece)
        done[name] = len(cells)
    return done


def seal_tracks(layers, keep_open=()):
    """Put a gk_blank collider on every train-track cell. keep_open cells (a
    station room's `board` cells) stay walkable, and so does a track cell whose
    Floor tile is a road (`road-*`): that is a level crossing.

    layers is {layer name: {'x,y': palette index}} and must hold 'Colliders'.
    Returns (cells sealed, cells kept open). Shared by Builder.finish() and
    tools/seal_tracks.py."""
    keep_open = {tuple(c) for c in keep_open}
    track_cells = set()
    for name, tiles in layers.items():
        for xy, idx in tiles.items():
            cell = tuple(map(int, xy.split(',')))
            if _pal[idx].startswith('train-track'):
                track_cells.add(cell)
            elif name == 'Floor' and _pal[idx].startswith('road-'):
                keep_open.add(cell)                 # a road over the track is a level crossing
    added = 0
    for (x, y) in sorted(track_cells - keep_open):
        key = f'{x},{y}'
        if key not in layers['Colliders']:
            layers['Colliders'][key] = pidx('gk_blank')
            added += 1
    return added, len(keep_open)


def kept_door(prev, cell, prefix):
    """The transporter a previous build of a room has on `cell`, if it leads
    into an interior another generator owns (a room named `prefix`...,
    e.g. 'Konbini' for generate_konbinis.py) that still exists - else None.

    A town generator rebuilds its room from scratch, so without this a re-run
    would drop the shop door that the interior's generator wired afterwards.
    prev is the room as it is in config.json before the rebuild ({} if new)."""
    for t in prev.get('transporters', []):
        if (t['gridX'], t['gridY']) == tuple(cell) and t['targetRoom'].startswith(prefix) \
                and t['targetRoom'] in _cfg['rooms']:
            return t
    return None


def kept_order(prev, transporters):
    """`transporters` in the order the previous build of the room lists them
    (anything new goes last, in the order given). The same doors in another
    order are the same room, but not the same bytes: generate_konbinis.py
    appends the door it wires, so a generator that put a kept door anywhere
    else would reorder the list on its next run (issue #107)."""
    where = {(t['gridX'], t['gridY'], t['targetRoom']): i
             for i, t in enumerate(prev.get('transporters', []))}
    return sorted(transporters,
                  key=lambda t: where.get((t['gridX'], t['gridY'], t['targetRoom']), len(where)))


class Builder:
    def __init__(self, w, h):
        assert w >= 20 and h >= 15, 'room must be at least 20x15 cells (1280x960 camera viewport)'
        self.W, self.H = w, h
        self.L = {n: {} for n in LAYER_NAMES}

    def put(self, layer, x, y, key, replace=False):
        """One tile per cell per layer. A big sprite lives only on its top-left
        cell, so putting a second prop there would drop the first and leave its
        colliders behind: off the Floor that is an error unless replace=True."""
        assert 0 <= x < self.W and 0 <= y < self.H, (layer, x, y, key)
        cell, new = f'{x},{y}', pidx(key)
        old = self.L[layer].get(cell)
        if old is not None and old != new and layer != 'Floor' and not replace:
            raise ValueError(f'{layer} {cell}: {key} would replace {_pal[old]} '
                             f'(move one of them, or pass replace=True)')
        self.L[layer][cell] = new

    def solid(self, x, y):
        self.put('Colliders', x, y, 'gk_blank')

    def stamp(self, name, x, y, seal=True):
        """Place a prefab (tiled/prefabs/<name>.tmj) with its top-left at (x,y).
        Returns the prefab's door cells in world coords. seal=False keeps
        doorways open so a hidden transporter can be wired onto them."""
        if name not in _PF:
            _PF[name] = _prefab.load_prefab(name)
        return _prefab.stamp(_PF[name], x, y, self.put, self.solid, seal_doors=seal)

    def fill(self, fam):
        for x in range(self.W):
            for y in range(self.H):
                self.put('Floor', x, y, f'{fam}_center')

    def autotile(self, fam, cells, roles=FULL9):
        """Paint a terrain region with correct edge/corner pieces (9-piece sets;
        inner corners fall back to center, so keep regions chunky)."""
        cells = set(cells)
        for (x, y) in cells:
            n, e, s, w = (x, y-1) in cells, (x+1, y) in cells, (x, y+1) in cells, (x-1, y) in cells
            role = 'center'
            if not n and not w and e and s: role = 'corner-nw'
            elif not n and not e and w and s: role = 'corner-ne'
            elif not s and not w and e and n: role = 'corner-sw'
            elif not s and not e and w and n: role = 'corner-se'
            elif not n and e and w and s: role = 'edge-n'
            elif not s and e and w and n: role = 'edge-s'
            elif not w and n and s and e: role = 'edge-w'
            elif not e and n and s and w: role = 'edge-e'
            if role not in roles: role = 'center'
            self.put('Floor', x, y, f'{fam}_{role}')

    def pond(self, x0, y0, x1, fam='pond-autotile'):
        """A pond exactly two rows tall (the pond set has no edge-w piece).
        Solid water, rock-rimmed. Pass fam='ice-pond-autotile' for a frozen
        pond (same geometry, recoloured — see tools/make_snow_tiles.py)."""
        top = [('corner-nw', x0)] + [('edge-n', x) for x in range(x0+1, x1)] + [('corner-ne', x1)]
        bot = [('corner-sw', x0)] + [('edge-s', x) for x in range(x0+1, x1)] + [('corner-se', x1)]
        for role, x in top: self.put('Water', x, y0, f'{fam}_{role}'); self.solid(x, y0)
        for role, x in bot: self.put('Water', x, y0+1, f'{fam}_{role}'); self.solid(x, y0+1)

    def flowers(self, x, y):
        """2x2 flowering-grass patch (only the 4 corner pieces exist)."""
        self.put('Floor', x, y, 'flowering-grass-autotile_corner-nw')
        self.put('Floor', x+1, y, 'flowering-grass-autotile_corner-ne')
        self.put('Floor', x, y+1, 'flowering-grass-autotile_corner-sw')
        self.put('Floor', x+1, y+1, 'flowering-grass-autotile_corner-se')

    def plants(self, x, y, v=0):
        self.put('Over Floor', x, y, f'ground-plants-1_{["0_0","0_1","1_0","1_1"][v % 4]}')

    def paver(self, x, y, v=0):
        self.put('Over Floor', x, y, ['pavers_1_0','pavers_2_0','pavers_1_2','pavers_2_1','pavers_0_2','pavers_2_2'][v % 6])

    def fence(self, x, y, v=0, replace=False):
        self.put('Collidables', x, y, ['fence-barriers_2_0','fence-barriers_0_2','fence-barriers_1_2','fence-barriers_0_3'][v % 4], replace)
        self.solid(x, y)

    def stairs(self, x, y):
        self.put('Over Floor', x, y, 'castle-stairs_0_0')

    def wall_stone(self, x, y):
        """Stone wall segment, 1x2 tall, solid (castle-wall-siding)."""
        self.put('Collidables', x, y, 'castle-wall-siding_0_0'); self.solid(x, y); self.solid(x, y + 1)

    def wall_panel(self, x, y):
        """Blue panelled wall segment, 1x2 tall, solid (blue-wall-short)."""
        self.put('Collidables', x, y, 'blue-wall-short_0_0'); self.solid(x, y); self.solid(x, y + 1)

    def counter(self, x, y):
        """2x2 solid display cabinet / counter (blue-shrine-platform-base)."""
        self.put('Collidables', x, y, 'blue-shrine-platform-base_0_0')
        for dx in (0, 1):
            for dy in (0, 1): self.solid(x + dx, y + dy)

    def finish(self):
        """The two passes every outdoor generated room needs before room():
        real picket fences for the fence() runs and solid train tracks - the
        same code tools/fix_fences.py and tools/seal_tracks.py run on a named
        room. Call it last, once everything is placed; a town generator that
        does is complete on its own and a re-run of it on an unchanged world
        leaves config.json byte-identical (tools/check_generators.py)."""
        picket_fences(self.L)
        seal_tracks(self.L)

    def validate(self):
        missing = [_pal[i] for lay in self.L.values() for i in lay.values()
                   if not os.path.exists(f'assets/sprites/{_pal[i]}.png')]
        assert not missing, f'missing sprites: {sorted(set(missing))[:8]}'

    def room(self, name, npcs=None, transporters=None):
        self.validate()
        return {'name': name, 'worldWidth': self.W * 64, 'worldHeight': self.H * 64,
                'boundary': [[0, 0], [self.W, 0], [self.W, self.H], [0, self.H]],
                'layers': [
                    {'name': 'Floor', 'z': 0, 'collision': False, 'tiles': self.L['Floor']},
                    {'name': 'Over Floor', 'z': 1, 'collision': False, 'tiles': self.L['Over Floor']},
                    {'name': 'Water', 'z': 1, 'collision': False, 'tiles': self.L['Water']},
                    {'name': 'Non-Collidables', 'z': 4, 'collision': False, 'tiles': self.L['Non-Collidables']},
                    {'name': 'Collidables', 'z': 5, 'collision': False, 'tiles': self.L['Collidables']},
                    {'name': 'Other', 'z': 6, 'collision': False, 'tiles': self.L['Other']},
                    {'name': 'Tops', 'z': 7, 'collision': False, 'tiles': self.L['Tops']},
                    {'name': 'Colliders', 'z': 5, 'collision': True, 'tiles': self.L['Colliders']},
                ],
                'npcs': npcs or [], 'objects': [], 'transporters': transporters or []}


def make_npc(name, sprite_base, x, y, dialogue, states=None):
    """NPC dict for Builder.room(); sprite_base e.g. 'dylan' (needs
    <base>_front/_back/_side sprites in spriteMetadata). states is an optional
    {'YYYY-MM-DD': {field updates...}} history — the game applies every state
    dated on-or-before the current game date, in order (tools/npc_state.py
    manages these from the CLI)."""
    npc = {'name': name, 'sprite': f'{sprite_base}_front', 'gridX': x, 'gridY': y,
           'gridOffsetX': 0, 'gridOffsetY': 0, 'dialogue': dialogue,
           'directionalSprites': {'up': f'{sprite_base}_back', 'down': f'{sprite_base}_front',
                                  'left': '', 'right': f'{sprite_base}_side'},
           'autoFlip': {'horizontal': True, 'vertical': False}}
    if states: npc['states'] = states
    return npc


def transporter(x, y, target_room, tx, ty, hidden=False):
    return {'gridX': x, 'gridY': y, 'targetRoom': target_room,
            'targetX': tx, 'targetY': ty, 'hidden': hidden}
