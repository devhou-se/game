#!/usr/bin/env python3
"""fix_fences.py — swap the broken fence art for real picket fence runs.

The fence-barriers_* tiles are crowd-barrier/bench pieces; cycling them
(roomgen's fence()) produces disconnected junk. This rewrites every
horizontal run of fence-barriers tiles into the fence-garden-outside picket
set: left end, middle pieces, right end. Colliders are untouched (the cells
were already solid). MANDATORY post-pass for any generated room that calls
b.fence() (see the /generate-room skill).

Run from gamev2/ (defaults to the pre-existing generated rooms; pass room
names to fix others, e.g. a freshly generated one):
    python3 tools/fix_fences.py                # Inaka Machi
    python3 tools/fix_fences.py Yukimura       # a specific room
Then qa_port + config_to_tiled for the printed rooms.
"""
import sys
import roomgen as rg

cfg = rg.load_config()

LEFT, MID, RIGHT = ('fence-garden-outside_2_5',
                    'fence-garden-outside_3_5',
                    'fence-garden-outside_4_5')

# Default to the rooms whose fences came from roomgen's broken fence() cycle.
# Tokyo/Market/Park use fence-barriers as ported road barriers — intentional,
# so they are NOT defaulted. CLI args override (any generated room can be fixed).
ROOMS = sys.argv[1:] or ['Inaka', 'Machi']

changed = []
for room_key in ROOMS:
    room = cfg['rooms'][room_key]
    for layer in room.get('layers', []):
        cells = sorted(
            tuple(map(int, xy.split(',')))
            for xy, idx in layer.get('tiles', {}).items()
            if rg._pal[idx].startswith('fence-barriers')
        )
        if not cells:
            continue
        cellset = set(cells)
        for (x, y) in cells:
            has_l = (x - 1, y) in cellset
            has_r = (x + 1, y) in cellset
            piece = MID if (has_l and has_r) else LEFT if not has_l else RIGHT
            layer['tiles'][f'{x},{y}'] = rg.pidx(piece)
        if room_key not in changed:
            changed.append(room_key)
        print(f'{room_key}/{layer["name"]}: re-fenced {len(cells)} cells')

rg.save_config(cfg)
print('rooms changed:', ' '.join(changed))
