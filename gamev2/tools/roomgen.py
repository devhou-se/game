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

Then: qa_port --room MyRoom; config_to_tiled.py MyRoom (and any room whose
transporters you touched — the game reads transporters from the .tmj!).
"""
import json, os
import prefab as _prefab

LAYER_NAMES = ['Floor', 'Over Floor', 'Water', 'Non-Collidables', 'Collidables', 'Other', 'Tops', 'Colliders']
FULL9 = {'center', 'edge-n', 'edge-e', 'edge-s', 'edge-w', 'corner-nw', 'corner-ne', 'corner-sw', 'corner-se'}

_cfg = None
_pal = None
_idx = None
_PF = {}


def load_config(path='config.json'):
    global _cfg, _pal, _idx
    _cfg = json.load(open(path))
    _pal = _cfg['tilePalette']
    _idx = {k: i for i, k in enumerate(_pal)}
    return _cfg


def save_config(cfg=None, path='config.json'):
    open(path, 'w').write(json.dumps(cfg or _cfg, indent=2, sort_keys=True))


def pidx(key):
    if key not in _idx:
        _pal.append(key); _idx[key] = len(_pal) - 1
    return _idx[key]


def rect(x0, y0, x1, y1):
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


class Builder:
    def __init__(self, w, h):
        assert w >= 20 and h >= 15, 'room must be at least 20x15 cells (1280x960 camera viewport)'
        self.W, self.H = w, h
        self.L = {n: {} for n in LAYER_NAMES}

    def put(self, layer, x, y, key):
        assert 0 <= x < self.W and 0 <= y < self.H, (layer, x, y, key)
        self.L[layer][f'{x},{y}'] = pidx(key)

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

    def pond(self, x0, y0, x1):
        """A pond exactly two rows tall (the pond set has no edge-w piece).
        Solid water, rock-rimmed."""
        top = [('corner-nw', x0)] + [('edge-n', x) for x in range(x0+1, x1)] + [('corner-ne', x1)]
        bot = [('corner-sw', x0)] + [('edge-s', x) for x in range(x0+1, x1)] + [('corner-se', x1)]
        for role, x in top: self.put('Water', x, y0, f'pond-autotile_{role}'); self.solid(x, y0)
        for role, x in bot: self.put('Water', x, y0+1, f'pond-autotile_{role}'); self.solid(x, y0+1)

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

    def fence(self, x, y, v=0):
        self.put('Collidables', x, y, ['fence-barriers_2_0','fence-barriers_0_2','fence-barriers_1_2','fence-barriers_0_3'][v % 4])
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
