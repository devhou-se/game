"""kansai.py — what the Kansai district generators share (issues #255, #267, #268, #68).

Osaka, Himeji, Okayama and Nara are four rooms the game stitches into ONE walkable room,
`KansaiCity` (config `cities`, src/systems/CityStitcher.js — the mechanism
Tokyo's and Hokuriku's districts use). Each has its own generator; this module
holds the one thing they must agree on, where the districts meet. The building
helpers are Hokuriku's (`Kit`, tools/hokuriku.py). It builds nothing itself.

Kansai is planned as five districts, one ticket each. `AT` and `SIZE` hold all
five, in the city's own cells (the union's top-left is 0,0), which is also how
they sit in ../devhouse.world relative to each other — so that a later ticket
moves nothing; `BUILT` names the ones that exist:

    Okayama   44x40 at (0, 36)     the black keep and Korakuen, west of Himeji. Its
                                   own west edge has no join: nothing is planned beyond it
    Himeji    44x40 at (44, 36)    the castle and Koko-en, west of Osaka
    Osaka     50x46 at (88, 30)    the town: the station, the canal, Dotonbori
    Nara      52x40 at (138, 36)   the Great Buddha Hall, the deer and Kasuga Taisha,
                                   east of Osaka. Its north edge opens with Lake Biwa
    LakeBiwa  46x36 at (152, 0)    not built

    Osaka's west edge meets Himeji's east edge: Canal-side Avenue (Osaka rows
    24-28) is Himeji rows 18-22, and Osaka's canal (rows 20-22) runs on as the
    castle moat (Himeji rows 14-16).
    Himeji's west edge meets Okayama's east edge: the avenue carries on, on the
    same rows (Okayama rows 18-22), and ends in Okayama's plaza.
    Osaka's east edge meets Nara's west edge: the avenue carries on (Nara rows
    18-22) to the plaza below the Nandaimon, and the canal runs on as a river
    (Nara rows 14-16) that bends north up columns 20-22 with a towpath beside
    it (23-24). The towpath's top is where Lake Biwa will join (`LakeBiwa`,
    columns 9-10 of its south edge); until then Nara's north edge is closed.

A join (`JOINS`) is open only when both its districts are in `BUILT`; a
generator asks `is_open(district, side)` and closes its edge otherwise. Every
seam cell of an open join carries a hidden transporter to the cell three in
from the neighbour's edge, which is what `?stitch=0` (and `play.js --stitch=0`)
plays; stitched, the transporters are dropped and you just walk.
"""
import roomgen as rg
from hokuriku import Kit       # noqa: F401 — the generators build with ks.Kit

AT = {'Okayama': (0, 36), 'Himeji': (44, 36), 'Osaka': (88, 30), 'Nara': (138, 36), 'LakeBiwa': (152, 0)}
SIZE = {'Okayama': (44, 40), 'Himeji': (44, 40), 'Osaka': (50, 46), 'Nara': (52, 40), 'LakeBiwa': (46, 36)}
CITY, IN = 'KansaiCity', 3               # a seam transporter lands IN cells inside the neighbour
BUILT = ('Himeji', 'Nara', 'Okayama', 'Osaka')   # each later ticket adds its district

O_AVENUE = (24, 25, 26, 27, 28)          # Osaka: the rows of Canal-side Avenue, at x = 0
H_AVENUE = tuple(y + AT['Osaka'][1] - AT['Himeji'][1] for y in O_AVENUE)          # Himeji: 18-22, at x = 43
O_CANAL = (20, 22)                       # Osaka: the canal's first and last row
H_MOAT = tuple(y + AT['Osaka'][1] - AT['Himeji'][1] for y in O_CANAL)             # Himeji: 14-16, the moat
OK_AVENUE = tuple(y + AT['Himeji'][1] - AT['Okayama'][1] for y in H_AVENUE)       # Okayama: 18-22, at x = 43
N_AVENUE = tuple(y + AT['Osaka'][1] - AT['Nara'][1] for y in O_AVENUE)            # Nara: 18-22, at x = 0
N_RIVER = tuple(y + AT['Osaka'][1] - AT['Nara'][1] for y in O_CANAL)              # Nara: 14-16, the river in from Osaka
N_BEND = (20, 22)                        # Nara: the columns the river turns north up
N_TOWPATH = (23, 24)                     # Nara: the towpath's columns, at y = 0
L_TOWPATH = tuple(x + AT['Nara'][0] - AT['LakeBiwa'][0] for x in N_TOWPATH)       # Lake Biwa: 9-10, at y = 35
# Osaka's seams are written in this order (west, then east): keep its west row first
JOINS = [('Osaka', 'w', O_AVENUE, 'Himeji', H_AVENUE),      # (district, side, its cells, neighbour, its cells)
         ('Himeji', 'w', H_AVENUE, 'Okayama', OK_AVENUE),
         ('Osaka', 'e', O_AVENUE, 'Nara', N_AVENUE),
         ('Nara', 'n', N_TOWPATH, 'LakeBiwa', L_TOWPATH)]  # inert until Lake Biwa is built (#269)

OPPOSITE = {'w': 'e', 'e': 'w', 'n': 's', 's': 'n'}


def joins(district):
    """The joins of `district` whose both ends are built, from its own end:
    [(side, its cells, neighbour, the neighbour's cells)]."""
    out = []
    for a, side, a_cells, b, b_cells in JOINS:
        if a in BUILT and b in BUILT:
            if a == district:
                out.append((side, a_cells, b, b_cells))
            elif b == district:
                out.append((OPPOSITE[side], b_cells, a, a_cells))
    return out


def is_open(district, side):
    """Whether `district` is walked out of on `side` ('n', 'e', 's', 'w'): a
    join touches that side and the district at its other end is built."""
    return any(s == side for s, _, _, _ in joins(district))


def seams(district):
    """The hidden seam transporters of a district (for ?stitch=0)."""
    w, h = SIZE[district]
    out = []
    for side, cells, other, other_cells in joins(district):
        ow, oh = SIZE[other]
        for c, oc in zip(cells, other_cells):
            here = {'w': (0, c), 'e': (w - 1, c), 'n': (c, 0), 's': (c, h - 1)}[side]
            there = {'w': (ow - 1 - IN, oc), 'e': (IN, oc), 'n': (oc, oh - 1 - IN), 's': (oc, IN)}[side]
            out.append(rg.transporter(*here, other, *there, hidden=True))
    return out
