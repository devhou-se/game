"""hokuriku.py — what the three Hokuriku district generators share (issue #68).

Kanazawa, Shirakawa-go and Toyama are three rooms the game stitches into ONE
walkable room, `HokurikuCity` (config `cities`, src/systems/CityStitcher.js —
the mechanism Tokyo's districts use). Each has its own generator; this module
holds the one thing they must agree on, where the districts meet, and the
helpers all three build with. It builds nothing itself.

The districts in the city's own cells (the union's top-left is 0,0), which is
also how they sit in ../devhouse.world relative to each other:

    Toyama        44x34 at (66, 0)    the coast, top right
    Kanazawa      60x52 at (0, 14)    the town, on the left
    Shirakawa-go  36x32 at (60, 34)   the mountain village, below Toyama

    Kanazawa's east edge meets Shirakawa-go's west edge: the road out of town
    (Kanazawa rows 30-32) is Shirakawa-go rows 10-12.
    Shirakawa-go's north edge meets Toyama's south edge: the mountain path
    (Shirakawa-go columns 24-25) is Toyama columns 18-19, and the Sho river
    (Shirakawa-go columns 10-15) runs on as Toyama columns 4-9, down to the sea.
    Toyama and Kanazawa do not touch: six columns of wood lie between them.

Every seam cell carries a hidden transporter to the cell three in from the
neighbour's edge, which is what `?stitch=0` (and `play.js --stitch=0`) plays;
stitched, the transporters are dropped and you just walk.
"""
import roomgen as rg
from roomgen import rect

AT = {'Kanazawa': (0, 14), 'Shirakawago': (60, 34), 'Toyama': (66, 0)}
SIZE = {'Kanazawa': (60, 52), 'Shirakawago': (36, 32), 'Toyama': (44, 34)}
CITY = 'HokurikuCity'

K_ROAD = (30, 31, 32)                    # Kanazawa: the rows of the road east, at x = 59
S_ROAD = tuple(y + AT['Kanazawa'][1] - AT['Shirakawago'][1] for y in K_ROAD)      # Shirakawa-go: 10-12, at x = 0
S_PATH = (24, 25)                        # Shirakawa-go: the columns of the path north, at y = 0
T_PATH = tuple(x + AT['Shirakawago'][0] - AT['Toyama'][0] for x in S_PATH)        # Toyama: 18-19, at y = 33
S_RIVER = (10, 15)                       # Shirakawa-go: the Sho river's columns (bank to bank)
T_RIVER = tuple(x + AT['Shirakawago'][0] - AT['Toyama'][0] for x in S_RIVER)      # Toyama: 4-9
IN = 3                                   # a seam transporter lands this many cells inside the neighbour


def seams(district):
    """The hidden seam transporters of a district (for ?stitch=0)."""
    kw, kh = SIZE['Kanazawa']
    sw, sh = SIZE['Shirakawago']
    tw, th = SIZE['Toyama']
    t = rg.transporter
    if district == 'Kanazawa':
        return [t(kw - 1, ky, 'Shirakawago', IN, sy, hidden=True) for ky, sy in zip(K_ROAD, S_ROAD)]
    if district == 'Shirakawago':
        return [t(0, sy, 'Kanazawa', kw - 1 - IN, ky, hidden=True) for ky, sy in zip(K_ROAD, S_ROAD)] + \
               [t(sx, 0, 'Toyama', tx, th - 1 - IN, hidden=True) for sx, tx in zip(S_PATH, T_PATH)]
    return [t(tx, th - 1, 'Shirakawago', sx, IN, hidden=True) for sx, tx in zip(S_PATH, T_PATH)]


class Kit:
    """The building helpers, bound to one Builder."""

    def __init__(self, b):
        self.b = b

    def solid_rect(self, x0, y0, x1, y1):
        self.b.solid(x0, y0, x1 - x0 + 1, y1 - y0 + 1)

    def building(self, name, x, y, w, roof=2):
        """A street building, solid over its roof rows too: nobody walks in behind it."""
        doors = self.b.stamp(name, x, y)
        self.solid_rect(x, y, x + w - 1, y + roof - 1)
        return doors

    def house(self, colour, x, y):
        """A townhouse (3x6: three roof rows on Tops), solid over the roof."""
        self.b.stamp(f'house-{colour}', x, y)
        self.solid_rect(x, y, x + 2, y + 2)

    TALL = {'sendai-pine': 3, 'sendai-cedar': 4, 'sendai-maple': 3, 'hokuriku-ginkgo': 3, 'tree-green': 3,
            'karuizawa-larch': 3, 'karuizawa-larch-tall': 4}

    def trees(self, name, cells):
        """Stamp `name` (2 wide) with its trunk on each (x, y)."""
        for x, y in cells:
            self.b.stamp(name, x, y - self.TALL[name] + 1)

    def wall(self, x0, x1, y):
        """An earthen wall along rows y..y+1."""
        for x in range(x0, x1 + 1):
            self.b.stamp('sendai-earthen-wall', x, y)

    def paved(self, cells, fam='flat-grey-brick-autotile'):
        for x, y in cells:
            self.b.put('Floor', x, y, f'{fam}_center')

    def taken(self, x, y):
        return any(f'{x},{y}' in self.b.L[n] for n in ('Collidables', 'Colliders', 'Other', 'Water', 'Tops', 'Non-Collidables'))

    def woods(self, x0, y0, x1, y1, kinds, rng, over=1, clear=()):
        """A wood nobody enters: trees of `kinds` planted in staggered bands over
        the rectangle wherever their trunk cells are free, shrubs in the gaps,
        and every cell solid. A canopy may hang `over` rows above the rectangle.
        The free cells in `clear` stay out of it (the steps of a hall that reach
        into the wood): open, no shrub, no tree with its trunk on one. They are
        planted and cleared again, not skipped, so that opening a cell does not
        reshuffle the rest of the seeded scatter."""
        b = self.b
        clear = {c for c in clear if not self.taken(*c)}
        felled = []
        for band, y in enumerate(range(y1, y0 - 1, -2)):
            for x in range(x0 + band % 2, x1, 2 + (band + x0) % 2):
                name = kinds[rng.randrange(len(kinds))]
                top = y - self.TALL[name] + 1
                if top < max(0, y0 - over) or x + 1 > x1 or x + 1 >= b.W:
                    continue
                if self.taken(x, y) or self.taken(x + 1, y) or f'{x},{top}' in b.L['Collidables']:
                    continue
                b.stamp(name, x, top)
                if (x, y) in clear or (x + 1, y) in clear:
                    felled.append((x, top))
        for x, y in rect(x0, y0, x1, y1):
            if not self.taken(x, y) and rng.random() < 0.3 and (x, y) not in clear:
                b.put('Collidables', x, y, 'shrub-small-circle_0_0')
            if (x, y) not in clear:
                b.solid(x, y)
        for x, top in felled:
            del b.L['Collidables'][f'{x},{top}']
        for x, y in clear:
            b.L['Colliders'].pop(f'{x},{y}', None)        # a felled trunk

    def dress(self):
        """Give every bare collider a walker can touch a shrub to be (the last pass
        before Builder.finish): a cell made solid to keep people out from behind
        something, with no art on it, is an invisible wall - `play.js lint`
        reports it as stray-collision."""
        b, sizes = self.b, {}
        covered = set()
        for name in ('Collidables', 'Other', 'Tops', 'Non-Collidables', 'Water'):
            for xy, idx in b.L[name].items():
                key = rg._pal[idx]
                if key not in sizes:
                    w, h = rg.png_size(key)
                    sizes[key] = (max(1, w // 64), max(1, h // 64))     # rounded down: not sprite_cells
                x, y = map(int, xy.split(','))
                w, h = sizes[key]
                covered.update((x + i, y + j) for i in range(w) for j in range(-1, h))
        solid = {tuple(map(int, xy.split(','))) for xy in b.L['Colliders']}
        n = 0
        for x, y in sorted(solid - covered):
            near = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            if any(0 <= nx < b.W and 0 <= ny < b.H and (nx, ny) not in solid for nx, ny in near):
                b.put('Collidables', x, y, 'shrub-small-circle_0_0')
                n += 1
        return n

    def road_h(self, x0, x1, y, cap_w=False, cap_e=False):
        """A three-cell asphalt road along rows y..y+2, x0..x1 inclusive."""
        b = self.b
        for x in range(x0, x1 + 1):
            b.put('Floor', x, y, 'road-edge-top_0_0')
            b.put('Floor', x, y + 1, 'road-div-horizontal_0_0')
            b.put('Floor', x, y + 2, 'road-edge-bottom_0_0')
        for on, x, (top, mid, bottom) in ((cap_w, x0, ('road-corner-nw', 'road-edge-left', 'road-corner-sw')),
                                          (cap_e, x1, ('road-corner-ne', 'road-edge-right', 'road-corner-se'))):
            if on:
                b.put('Floor', x, y, f'{top}_0_0')
                b.put('Floor', x, y + 1, f'{mid}_0_0')
                b.put('Floor', x, y + 2, f'{bottom}_0_0')

    def plants(self, rng, n, x0, y0, x1, y1):
        """Ground plants scattered on the open grass of a rectangle."""
        b = self.b
        for i in range(n):
            x, y = rng.randrange(x0, x1 + 1), rng.randrange(y0, y1 + 1)
            if all(f'{x},{y}' not in b.L[k] for k in ('Collidables', 'Colliders', 'Over Floor', 'Other', 'Water', 'Tops',
                                                     'Non-Collidables')) \
               and rg._pal[b.L['Floor'][f'{x},{y}']].startswith('grass'):
                b.plants(x, y, i)
