"""kansai.py — what the Kansai district generators share (issues #255, #68).

Osaka and Himeji are two rooms the game stitches into ONE walkable room,
`KansaiCity` (config `cities`, src/systems/CityStitcher.js — the mechanism
Tokyo's and Hokuriku's districts use). Each has its own generator; this module
holds the one thing they must agree on, where the districts meet. The building
helpers are Hokuriku's (`Kit`, tools/hokuriku.py). It builds nothing itself.

Kansai is planned as five districts, one ticket each. `AT` and `SIZE` hold all
five, in the city's own cells (the union's top-left is 0,0), which is also how
they sit in ../devhouse.world relative to each other — so that a later ticket
moves nothing; `BUILT` names the ones that exist:

    Okayama   44x40 at (0, 36)     not built: Himeji's west edge is closed until it is
    Himeji    44x40 at (44, 36)    the castle and Koko-en, west of Osaka
    Osaka     50x46 at (88, 30)    the town: the station, the canal, Dotonbori
    Nara      52x40 at (138, 36)   not built
    LakeBiwa  46x36 at (152, 0)    not built

    Osaka's west edge meets Himeji's east edge: Canal-side Avenue (Osaka rows
    24-28) is Himeji rows 18-22, and Osaka's canal (rows 20-22) runs on as the
    castle moat (Himeji rows 14-16).

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
BUILT = ('Himeji', 'Osaka')              # each later ticket adds its district

O_AVENUE = (24, 25, 26, 27, 28)          # Osaka: the rows of Canal-side Avenue, at x = 0
H_AVENUE = tuple(y + AT['Osaka'][1] - AT['Himeji'][1] for y in O_AVENUE)          # Himeji: 18-22, at x = 43
O_CANAL = (20, 22)                       # Osaka: the canal's first and last row
H_MOAT = tuple(y + AT['Osaka'][1] - AT['Himeji'][1] for y in O_CANAL)             # Himeji: 14-16, the moat
JOINS = [('Osaka', 'w', O_AVENUE, 'Himeji', H_AVENUE)]      # (district, side, its cells, neighbour, its cells)

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
