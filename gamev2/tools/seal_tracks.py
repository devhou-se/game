#!/usr/bin/env python3
"""seal_tracks.py — make train tracks unwalkable.

Adds gk_blank colliders on every train-track tile cell. In station rooms the
`board` cells from config `stations` stay open — that's where the player walks
up into the train's doorway to board.

Run from gamev2/:  python3 tools/seal_tracks.py [Room ...]
Then config_to_tiled, then play.js lint, for the printed rooms.

Pass room names to seal only those rooms (e.g. a freshly generated town);
with no arguments every room is sealed. A track cell whose Floor tile is a
road (`road-*`) is a level crossing and stays open, like Palace's road over
the tracks at 0,5 / 1,5.
"""
import sys
import roomgen as rg

cfg = rg.load_config()

changed = []
for room_key, room in cfg['rooms'].items():
    if sys.argv[1:] and room_key not in sys.argv[1:]:
        continue
    keep_open = {tuple(c) for c in (cfg.get('stations', {}).get(room_key, {}).get('board', []))}
    track_cells = set()
    for layer in room.get('layers', []):
        for xy, idx in layer.get('tiles', {}).items():
            cell = tuple(map(int, xy.split(',')))
            if rg._pal[idx].startswith('train-track'):
                track_cells.add(cell)
            elif layer['name'] == 'Floor' and rg._pal[idx].startswith('road-'):
                keep_open.add(cell)                 # a road over the track is a level crossing
    if not track_cells:
        continue
    colliders = next(l for l in room['layers'] if l['name'] == 'Colliders')
    added = 0
    for (x, y) in sorted(track_cells - keep_open):
        key = f'{x},{y}'
        if key not in colliders['tiles']:
            colliders['tiles'][key] = rg.pidx('gk_blank')
            added += 1
    if added:
        changed.append(room_key)
        print(f'{room_key}: sealed {added} track cells'
              + (f' (kept {len(keep_open)} board cells open)' if keep_open else ''))

rg.save_config(cfg)
print('rooms changed:', ' '.join(changed))
