#!/usr/bin/env python3
"""generate_stations.py — train station interiors + the rail network registry.

Each town with a station gets an interior room (one template): a track at the
top with the train parked at the platform, a concrete platform with lamps /
vending / a ticket counter, and a door at the bottom back out to the town.
Walking up to the train (the board cells on the platform edge) opens the
destination picker (src/StationPicker.js); the ride itself is animated by
src/TrainTravel.js using the config `stations` registry written here.

Stations:
  TokyoStation — behind the Tokyo Station facade in the Palace room
  InakaStation — inside Inaka's station house

Also carves the Palace facade door and removes the old direct platform
portals (superseded by the train). Idempotent. Run from gamev2/ AFTER
generate_inaka.py. Then: qa_port + config_to_tiled for TokyoStation,
InakaStation, Palace (and Inaka if regenerated).
"""
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

W, H = 24, 15
# You board only at the train's actual doors: the two columns that line up with
# a door on BOTH liveries (orange + green), so boarding — and stepping back off
# at the same X — always lands on a door and never a window. See
# tools/extract_train.py for the sprite geometry.
DOOR_COLS = [8, 15]
# The door cells sit on the train's bottom row (row 3): you walk *into* the train
# to board, and step off *from* the train. So those two cells are carved out of
# the otherwise-solid track bed (below), and the board cells live there.
BOARD = [[c, 3] for c in DOOR_COLS]
ARRIVE = [11, 8]                           # (legacy) platform reference cell
DOOR_MATS = [[11, 14], [12, 14]]           # exit door at the bottom


def station_interior(train_sprite):
    b = rg.Builder(W, H)
    b.autotile('light-concrete-autotile', rect(0, 0, W - 1, H - 1))
    # back wall + double track bed (solid — the train parks over it), except the
    # door cells on the bottom track row, which you walk through to board
    for x in range(W):
        b.wall_stone(x, 0)
    b.autotile('gravel-autotile', rect(0, 2, W - 1, 3))
    for x in range(W):
        b.put('Over Floor', x, 2, 'train-track_0_0')
        b.put('Over Floor', x, 3, 'train-track_0_0')
        b.solid(x, 2)
        if x not in DOOR_COLS:
            b.solid(x, 3)
    # platform furniture
    b.stamp('lamp-blue', 4, 4); b.stamp('lamp-blue', 19, 4)
    b.stamp('vending-white', 2, 6); b.stamp('vending-red', 21, 6)
    b.counter(2, 9)                        # ticket counter
    b.stamp('lantern-red', 6, 10); b.stamp('lantern-red', 17, 10)
    for i, (px, py) in enumerate([(7, 7), (16, 7), (10, 10), (13, 10), (5, 12), (18, 12), (9, 12), (14, 12)]):
        b.paver(px, py, i)
    # front wall with the exit door gap
    for x in range(W):
        if x in (11, 12): continue
        b.wall_stone(x, 13)
    b.paver(11, 14, 0); b.paver(12, 14, 1)  # door mats
    return b


STATIONS = {
    'TokyoStation': {'label': 'Tokyo Station', 'town': 'Palace', 'train': 'train-orange'},
    'InakaStation': {'label': 'Inaka',         'town': 'Inaka',  'train': 'train-green'},
}
TOWN_DOORS = {          # townRoom: (hidden door cell into the station, exit cell outside)
    'TokyoStation': {'door': [27, 9], 'exit': [27, 10]},
    'InakaStation': {'door': [29, 9], 'exit': [29, 10]},
}

for key, st in STATIONS.items():
    b = station_interior(st['train'])
    exit_cell = TOWN_DOORS[key]['exit']
    cfg['rooms'][key] = b.room(key, transporters=[
        rg.transporter(mx, my, st['town'], exit_cell[0], exit_cell[1], hidden=True)
        for (mx, my) in DOOR_MATS
    ])

# registry the game reads (StationPicker + TrainTravel)
cfg['stations'] = {
    key: {'label': st['label'], 'town': st['town'], 'train': st['train'],
          'board': BOARD, 'arrive': ARRIVE,
          'trainCell': [7, 4]}             # train's left edge; feet on the platform edge row
    for key, st in STATIONS.items()
}

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
         'targetX': 11, 'targetY': 11, 'hidden': True})

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
