#!/usr/bin/env python3
"""fix_fences.py — swap the broken fence art for real picket fence runs.

The fence-barriers_* tiles are crowd-barrier/bench pieces; cycling them
(roomgen's fence()) produces disconnected junk. This rewrites every
horizontal run of fence-barriers tiles into the fence-garden-outside picket
set: left end, middle pieces, right end. Colliders are untouched (the cells
were already solid). The pass itself is roomgen.picket_fences; a generator
that ends with b.finish() has already run it, so this is for a room whose
generator does not (or that has none).

Run from gamev2/ (defaults to the pre-existing generated rooms; pass room
names to fix others, e.g. a freshly generated one):
    python3 tools/fix_fences.py                # Inaka Machi
    python3 tools/fix_fences.py Yukimura       # a specific room
Then config_to_tiled, then play.js lint, for the printed rooms.
"""
import sys
import roomgen as rg

cfg = rg.load_config()

# Default to the rooms whose fences came from roomgen's broken fence() cycle.
# Tokyo/Market/Park use fence-barriers as ported road barriers — intentional,
# so they are NOT defaulted. CLI args override (any generated room can be fixed).
ROOMS = sys.argv[1:] or ['Inaka', 'Machi']

changed = []
for room_key in ROOMS:
    room = cfg['rooms'][room_key]
    done = rg.picket_fences({layer['name']: layer['tiles'] for layer in room.get('layers', []) if 'tiles' in layer})
    for layer_name, n in done.items():
        print(f'{room_key}/{layer_name}: re-fenced {n} cells')
    if done:
        changed.append(room_key)

rg.save_config(cfg)
print('rooms changed:', ' '.join(changed))
