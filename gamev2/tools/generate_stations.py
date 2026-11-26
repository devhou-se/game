#!/usr/bin/env python3
"""generate_stations.py — train station interiors + the rail network registry.

Each town with a station gets an interior room built from ONE template
(station_interior, issue #206), top to bottom:

  the back wall      in the line's colour, with the station's name boards
  the track          two rows of rail on ballast; the train parks on it
  the platform       coping, white line and yellow tactile strip along the edge,
                     door marks where the train's doors stop, lamps, benches,
                     the timetable, vending machines
  the gate line      a row of ticket gates you walk through, tube railing, the
                     ticket machines and the 7-Eleven kiosk (bump it to shop)
  the concourse      tactile path from the gates to the exit, benches, planters,
                     the post box; pillars, lockers and the route map in a city
  the front wall     with the stairs down to the town door

A station's `size` ('small' by default, 'large' for a city terminus — SIZES)
decides how wide and deep the room is, how many gates it has and where the
train stops; everything else follows from it. Walking onto the train's door
cells (`board`) opens the departures board (src/StationPicker.js); the ride is
animated by src/TrainTravel.js from the config `stations` registry written here.

Art: tools/extract_station.py (GuttyKreum Train Station pack) and
tools/generate_station_art.py (walls, gates, kiosk, signs, one name board per
station) — run both first; a new station needs the second for its name board.

Also carves the Palace facade door, removes the old direct platform portals
(superseded by the train) and points every town door that leads into a station
at that station's `entry` cell. Idempotent, and safe to re-run on the live
config: a station room that already exists keeps its NPCs (the blog pipeline
parks dated NPC states in station rooms, at the west end of the platform — the
template keeps those cells and the white vending machine beside them where they
have always been). Run from gamev2/ AFTER the town generators (generate_inaka.py /
generate_yukimura.py / generate_osaka.py / generate_sendai.py / generate_sapporo.py /
generate_asahikawa.py / generate_fukuoka.py).
Then: config_to_tiled, then play.js lint, for every *Station room and every town
(the town's door is a transporter in the town's map).

Stations:
  TokyoStation    — behind the Tokyo Station facade in the Palace room
  InakaStation    — inside Inaka's station house
  YukimuraStation — inside Yukimura's station house
  OsakaStation    — inside Osaka's station house
  SendaiStation   — inside Sendai's station house
  SapporoStation / AsahikawaStation — inside the Hokkaido station houses
  FukuokaStation  — "Hakata", inside Fukuoka's station house
  HanedaStation   — "Haneda Airport": its stairs lead into the HanedaAirport hall
                    (tools/generate_airports.py), not out to a town
"""
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

# How big a station is. `w` x `h` cells; `train` is the column of the train's left
# edge (it is ten cells long); `gates` how many ticket gates stand in the row.
# The small station is the size every station used to be, so a town door written
# for it (arriving at 11,11) is still right; a large one is a city terminus.
SIZES = {
    'small': dict(w=24, h=15, train=7, gates=2),
    'large': dict(w=36, h=20, train=13, gates=4),
}
TRACK_ROWS = (2, 3)         # the train's bottom row is row 3: you walk INTO it to board
EDGE_ROW = 4                # platform edge (tactile strip); you step off the train onto it
GATE_ROW = 9                # the ticket gates; the platform is rows 4-8, the concourse below
# You board only at the train's actual doors: the two columns that line up with
# a door on BOTH liveries (orange + green), so boarding — and stepping back off
# at the same X — always lands on a door and never a window. See
# tools/extract_train.py for the sprite geometry.
DOOR_OFFSETS = (1, 8)
# The blog pipeline's platform spot (tools/blog_to_npc.py LANDMARKS: 'the platform')
# is the first white vending machine, and shipped history stands at (1..2, 5..7)
# beside it. Both stay put in every station, whatever its size.
PLATFORM_VENDING = (2, 6)


def layout(size='small'):
    """Where everything in a station of this size is (cells)."""
    s = SIZES[size]
    w, h = s['w'], s['h']
    cx = w // 2 - 1                                     # the exit is cells cx, cx+1
    g0 = cx - (s['gates'] - 2) // 2                     # first gate column
    doors = [s['train'] + d for d in DOOR_OFFSETS]
    return dict(size=size, w=w, h=h, train=s['train'], doors=doors,
                board=[[c, TRACK_ROWS[1]] for c in doors],      # the door cells, on the track
                arrive=[cx, GATE_ROW - 1],                      # platform reference cell (tools)
                gates=list(range(g0, g0 + s['gates'])),
                wall_row=h - 2,                                 # front wall (two rows)
                mats=[[cx, h - 1], [cx + 1, h - 1]],            # the exit to the town
                entry=[cx, h - 4])                              # where a town door puts you


def name_board_key(key):
    """Sprite of a station's name board (drawn by tools/generate_station_art.py)."""
    town = key[:-len('Station')] if key.endswith('Station') else key
    return f'station-name-{town.lower()}_0_0'


def station_interior(key, st):
    L = layout(st.get('size', 'small'))
    w, h, cx = L['w'], L['h'], L['mats'][0][0]
    large = L['size'] == 'large'
    b = rg.Builder(w, h)

    def stand(layer, x, y, sprite, solid=()):
        b.put(layer, x, y, f'{sprite}_0_0')
        for dx, dy in solid:
            b.solid(x + dx, y + dy)

    # ---- floors: ballast under the track, slate platform, pale concourse
    for x in range(w):
        for y in range(h):
            fam = ('station-ballast' if y <= TRACK_ROWS[1] else
                   'station-platform-edge' if y == EDGE_ROW else
                   'station-floor' if y <= GATE_ROW else 'station-concourse')
            b.put('Floor', x, y, f'{fam}_0_0')

    # ---- back wall in the line's colour, then the track (solid — the train
    # parks over it), except the door cells, which you walk through to board
    line = 'green' if st['train'] == 'train-green' else 'orange'
    for x in range(w):
        stand('Collidables', x, 0, f'station-wall-{line}', [(0, 0), (0, 1)])
        b.put('Over Floor', x, TRACK_ROWS[0], 'station-track-n_0_0')
        b.put('Over Floor', x, TRACK_ROWS[1], 'station-track-s_0_0')
        b.solid(x, TRACK_ROWS[0])
        if x not in L['doors']:
            b.solid(x, TRACK_ROWS[1])
    # name boards on the wall, clear of the parked train (3 cells each)
    west, east = (1, L['train'] - 3), (L['train'] + 11, w - 4)
    spots = [west[0], east[1]] + ([west[1] - 1, east[0] + 1] if large else [])
    for x in spots:
        b.put('Other', x, 1, name_board_key(key))

    # ---- the platform (rows 4-8)
    for x in L['doors']:
        b.put('Over Floor', x, EDGE_ROW + 1, 'station-door-mark_0_0')
    b.stamp('vending-white', *PLATFORM_VENDING)
    b.stamp('vending-red', w - 3, 6)
    lamps = [5, w - 6] + ([10, w - 11] if large else [])
    for x in lamps:
        stand('Collidables', x, 5, 'station-lamp-post', [(0, 1)])
    for x in ([6, w - 9] if not large else [7, w - 9]):         # benches facing the train
        stand('Collidables', x, GATE_ROW - 2, 'station-bench-back', [(0, 1), (1, 1)])
    stand('Collidables', w - 5, 6, 'station-board-times', [(0, 2), (1, 2)])
    b.put('Tops', cx, 6, 'station-platform-sign_0_0')
    b.put('Tops', cx + 2, 6, 'station-clock_0_0')
    if st.get('parent'):                                        # a village stop has a station cat
        stand('Collidables', w - 7, GATE_ROW - 1, 'station-cat', [(0, 0), (1, 0)])

    # ---- the gate line (row 9): gates in the middle, machines, kiosk, railing
    taken = {}
    for x in L['gates']:
        b.put('Other', x, GATE_ROW - 1, 'station-gate_0_0')     # walk-through: no collider
        taken[x] = 'gate'
    for x, side in ((L['gates'][0] - 1, 'w'), (L['gates'][-1] + 1, 'e')):
        stand('Collidables', x, GATE_ROW - 1, f'station-gate-end-{side}', [(0, 1)])
        taken[x] = 'end'
    for x in ([3, 7] if large else [3]):                        # ticket machines, fare map above
        stand('Collidables', x, GATE_ROW, 'station-ticket-machines',
              [(dx, dy) for dx in range(3) for dy in range(2)])
        taken.update({x + dx: 'machines' for dx in range(3)})
    kiosk_x = w - 9 if large else w - 7                         # the 7-Eleven kiosk (4x3)
    stand('Collidables', kiosk_x, GATE_ROW, 'station-kiosk',
          [(dx, dy) for dx in range(4) for dy in range(3)])
    taken.update({kiosk_x + dx: 'kiosk' for dx in range(4)})
    if large:
        stand('Collidables', w - 4, GATE_ROW, 'station-lockers',
              [(dx, dy) for dx in range(2) for dy in range(2)])
        taken.update({w - 4: 'lockers', w - 3: 'lockers'})
    x = 0
    while x < w:                                                # railing in every gap
        if x in taken:
            x += 1
            continue
        run = [x]
        while run[-1] + 1 < w and run[-1] + 1 not in taken:
            run.append(run[-1] + 1)
        for i, rx in enumerate(run):
            piece = 'end' if i == len(run) - 1 else 'post' if i % 2 == 0 else 'mid'
            stand('Collidables', rx, GATE_ROW, f'station-railing-{piece}', [(0, 0)])
        x = run[-1] + 1
    b.put('Tops', L['gates'][0] - (4 - len(L['gates'])) // 2, GATE_ROW - 1, 'station-departures_0_0')

    # ---- the concourse: tactile path from the gates to the exit
    last = L['wall_row'] - 1
    branch = GATE_ROW + 2                                       # ...with a branch past the machines to the kiosk
    for y in range(GATE_ROW + 1, last + 1):
        b.put('Over Floor', cx, y, f"station-tactile-{'stop' if y in (GATE_ROW + 1, last) or (large and y == branch) else 'v'}_0_0")
    for x in (range(4, kiosk_x) if large else ()):              # (a small concourse is three rows: no room)
        if x != cx:
            b.put('Over Floor', x, branch, f"station-tactile-{'stop' if x in (4, kiosk_x - 1) else 'h'}_0_0")
    b.put('Tops', cx, last, 'station-exit-sign_0_0')
    for x in (cx - 2, cx + 2):                                  # planters either side of the exit
        stand('Collidables', x, last - 1, 'station-planter-a' if x < cx else 'station-planter-b',
              [(0, 1), (1, 1)])
    stand('Collidables', 1, last - 2, 'station-postbox', [(0, 2), (1, 2)])
    stand('Collidables', 5, last - 1, 'station-bench', [(0, 1), (1, 1)])
    if large:
        stand('Collidables', w - 7, last - 1, 'station-bench', [(0, 1), (1, 1)])
        stand('Collidables', w - 3, last - 2, 'station-board-map', [(0, 2), (1, 2)])
        for x in (6, 12, w - 13, w - 7):
            stand('Collidables', x, 12, 'station-pillar', [(0, 1)])
        for x in (9, w - 11):
            stand('Collidables', x, 14, 'station-bench', [(0, 1), (1, 1)])

    # ---- front wall with the exit: stairs down to the town door
    for x in range(w):
        if x in (cx, cx + 1):
            continue
        stand('Collidables', x, L['wall_row'], 'station-wall-front', [(0, 0), (0, 1)])
    b.put('Over Floor', cx, L['wall_row'], 'station-stairs_0_0')
    return b, L


# The departures board (src/StationPicker.js) lists stations in THIS order - the
# dict order is written to the registry as `order`, because save_config sorts
# keys. `parent` marks a day trip: it is listed indented under its parent city.
# Put a new city where it belongs along the line, and its day trips after it.
# `size` (optional, SIZES): 'large' for a city terminus, else the small station.
STATIONS = {
    'TokyoStation':    {'label': 'Tokyo Station', 'town': 'Palace',   'train': 'train-orange', 'size': 'large'},
    # Tokyo's day trips, both up the branch line (green).
    'InakaStation':    {'label': 'Inaka',         'town': 'Inaka',    'train': 'train-green',
                        'parent': 'TokyoStation'},
    # Yukimura — the snowy village, on the same branch line as Inaka.
    'YukimuraStation': {'label': 'Yukimura',      'town': 'Yukimura', 'train': 'train-green',
                        'parent': 'TokyoStation'},
    # Haneda Airport (issue #218): the airport line's one stop. Its `town` is the
    # airport hall itself (HanedaAirport, tools/generate_airports.py) - the stairs
    # lead straight into it. `blog: False`: the blog pipeline never offers it.
    'HanedaStation':   {'label': 'Haneda Airport', 'town': 'HanedaAirport', 'train': 'train-orange',
                        'blog': False},
    # Osaka — the second city, a main-line stop like Tokyo (orange).
    'OsakaStation':    {'label': 'Osaka',         'town': 'Osaka',    'train': 'train-orange', 'size': 'large'},
    # Sendai (issue #66) - a main-line city stop (orange), up the line from Tokyo
    # on the way to Hokkaido.
    'SendaiStation':   {'label': 'Sendai',        'town': 'Sendai',   'train': 'train-orange', 'size': 'large'},
    # Hokkaido (issue #43): Sapporo is a main-line city stop (orange), Asahikawa
    # the day trip up the branch line from it (green).
    'SapporoStation':   {'label': 'Sapporo',   'town': 'Sapporo',   'train': 'train-orange', 'size': 'large'},
    'AsahikawaStation': {'label': 'Asahikawa', 'town': 'Asahikawa', 'train': 'train-green',
                         'parent': 'SapporoStation'},
    # Fukuoka (issue #67): a main-line city stop (orange). The station is Hakata.
    'FukuokaStation':   {'label': 'Hakata',    'town': 'Fukuoka',   'train': 'train-orange', 'size': 'large'},
}
# The Japanese name on a station's name board (tools/generate_station_art.py draws
# one board per row of STATIONS). A station without one gets a romaji-only board;
# a row may also carry its own 'ja'.
STATION_JA = {
    'TokyoStation': '東京', 'InakaStation': 'いなか', 'YukimuraStation': '雪村',
    'OsakaStation': '大阪', 'SapporoStation': '札幌', 'AsahikawaStation': '旭川',
    'SendaiStation': '仙台', 'FukuokaStation': '博多', 'HanedaStation': '羽田空港',
}
assert all(st.get('parent', 'TokyoStation') in STATIONS for st in STATIONS.values()), 'unknown parent station'


def station_name(st):
    """The room's display name (the HUD shows it): 'Sapporo Station'."""
    return st['label'] if st['label'].endswith('Station') else f"{st['label']} Station"


TOWN_DOORS = {          # townRoom: (hidden door cell into the station, exit cell outside)
    'TokyoStation':    {'door': [27, 9], 'exit': [27, 10]},
    'InakaStation':    {'door': [29, 9], 'exit': [29, 10]},
    'YukimuraStation': {'door': [29, 9], 'exit': [29, 10]},
    'OsakaStation':    {'door': [24, 9], 'exit': [24, 10]},
    'SendaiStation':   {'door': [35, 9], 'exit': [35, 10]},
    'SapporoStation':   {'door': [34, 9], 'exit': [34, 10]},
    'AsahikawaStation': {'door': [32, 9], 'exit': [32, 10]},
    'FukuokaStation':   {'door': [30, 9], 'exit': [30, 10]},
    # the airport hall's own entry cell (generate_airports.layout()['entry']); there is no town door
    'HanedaStation':    {'door': [17, 21], 'exit': [17, 18]},
}

layouts = {}
for key, st in STATIONS.items():
    b, L = station_interior(key, st)
    layouts[key] = L
    exit_cell = TOWN_DOORS[key]['exit']
    prev = cfg['rooms'].get(key, {})
    cfg['rooms'][key] = b.room(station_name(st), npcs=prev.get('npcs', []), transporters=[
        rg.transporter(mx, my, st['town'], exit_cell[0], exit_cell[1], hidden=True)
        for (mx, my) in L['mats']
    ])
    if st.get('blog') is False:         # off the blog pipeline's list of rooms (blog_to_npc.overworld_rooms)
        cfg['rooms'][key]['blog'] = False

# registry the game reads (StationPicker + TrainTravel)
cfg['stations'] = {
    key: {'label': st['label'], 'town': st['town'], 'train': st['train'],
          'order': order,                  # position on the departures board
          **({'parent': st['parent']} if st.get('parent') else {}),
          **({'ja': st.get('ja') or STATION_JA[key]} if st.get('ja') or key in STATION_JA else {}),
          'size': layouts[key]['size'],
          'board': layouts[key]['board'], 'arrive': layouts[key]['arrive'],
          'entry': layouts[key]['entry'],  # where the town's door puts you
          'trainCell': [layouts[key]['train'], EDGE_ROW]}   # train's left edge; feet on the platform edge row
    for order, (key, st) in enumerate(STATIONS.items())
}

# every door into a station lands on its entry cell, whatever the town's
# generator wrote (a town generator reads it back: stations.<key>.entry)
for room in cfg['rooms'].values():
    for t in room.get('transporters', []):
        if t.get('targetRoom') in layouts:
            t['targetX'], t['targetY'] = layouts[t['targetRoom']]['entry']

# ---- Palace: carve the facade door, remove the old direct portals -------------
palace = cfg['rooms']['Palace']
for L in palace['layers']:
    if L.get('collision'):
        L['tiles'].pop('27,9', None)       # the station doorway
palace['transporters'] = [t for t in palace['transporters']
                          if t.get('targetRoom') not in ('Inaka',)]
if not any(t.get('targetRoom') == 'TokyoStation' for t in palace['transporters']):
    palace['transporters'].append(
        {'gridX': 27, 'gridY': 9, 'targetRoom': 'TokyoStation',
         'targetX': layouts['TokyoStation']['entry'][0], 'targetY': layouts['TokyoStation']['entry'][1],
         'hidden': True})

# train sprites are dynamic (not tiles) but load via spriteMetadata
import os, struct
for spr in ('train-orange', 'train-green'):
    with open(f'assets/sprites/{spr}.png', 'rb') as f:
        f.read(16); w, h = struct.unpack('>II', f.read(8))
    cfg['spriteMetadata'][spr] = {'frameCount': 1,
                                  'anchorX': round(32 / w, 4), 'anchorY': round(32 / h, 4)}
    cfg['tileNames'][spr] = spr

rg.save_config(cfg)
print('stations:', {k: v['town'] for k, v in cfg['stations'].items()})
