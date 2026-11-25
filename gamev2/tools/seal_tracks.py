#!/usr/bin/env python3
"""seal_tracks.py — make train tracks unwalkable.

Adds gk_blank colliders on every train-track tile cell. In station rooms the
`board` cells from config `stations` stay open — that's where the player walks
up into the train's doorway to board.

The pass itself is roomgen.seal_tracks; a town generator that ends with
b.finish() has already run it on its room.

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
    board = cfg.get('stations', {}).get(room_key, {}).get('board', [])
    layers = {layer['name']: layer['tiles'] for layer in room.get('layers', []) if 'tiles' in layer}
    added, kept = rg.seal_tracks(layers, keep_open=board)
    if added:
        changed.append(room_key)
        print(f'{room_key}: sealed {added} track cells'
              + (f' (kept {kept} board cells open)' if kept else ''))

rg.save_config(cfg)
print('rooms changed:', ' '.join(changed))
