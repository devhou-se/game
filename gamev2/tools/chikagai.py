"""chikagai.py — the towns that have an underground arcade (a chikagai), as data.

Read by tools/generate_chikagai_art.py (an exit's sign is drawn from its
names), tools/generate_chikagai.py (the room, and the doors into it) and the
town's own generator (which stamps the street entrances where this says).
Importing it runs nothing.

A town's arcade is a cross of corridors on one floor grid:
  hall     (w, h)                 the east-west arcade, shopfronts along its north wall
  north    (x, w, h) or None      a stem running north from the hall's cell x
  south    (x, w, h) or None      a stem running south from it
  shops    [(x, kind)]            3-cell shopfronts in the hall's north wall (SHOPS in the art tool)
  exits    {slug: {...}}          the stairs up to the street:
             ja, en               the names on its sign
             at  ('north', x) / ('hall', x) / ('south', x)
                                  the wall it is in (a stem's end wall, or the hall's north
                                  wall) and the first of its two cells
             street (x, y)        top-left cell of its entrance in the town (2x3, doors on the bottom row)
"""
ENTRANCE = 'chikagai-entrance-snow'           # the street entrance prefab (snow on its roof)
ENTRANCE_DOORS = [(0, 2), (1, 2)]             # its door cells, relative to its top-left cell

TOWNS = {
    'Sapporo': {
        'name': 'Aurora Town',
        'hall': (40, 6),
        'north': (2, 6, 5),
        'south': (26, 6, 4),
        'shops': [(13, 'bakery'), (17, 'kissa'), (21, 'books'), (25, 'shutter'), (29, 'bar'), (33, 'flowers')],
        'exits': {
            'sapporo-station': {'ja': '札幌駅', 'en': 'JR SAPPORO', 'at': ('north', 4), 'street': (28, 13)},
            'odori-park': {'ja': '大通公園', 'en': 'ODORI PARK', 'at': ('hall', 9), 'street': (33, 23)},
            'tv-tower': {'ja': 'テレビ塔', 'en': 'TV TOWER', 'at': ('hall', 37), 'street': (52, 24)},
            'tanukikoji': {'ja': '狸小路', 'en': 'TANUKIKOJI', 'at': ('south', 28), 'street': (47, 37)},
        },
    },
}
