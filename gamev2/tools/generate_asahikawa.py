#!/usr/bin/env python3
"""generate_asahikawa.py — "Asahikawa", a day trip up the line from Sapporo (issue #43).

A small generated town (the generate_yukimura.py recipe), reachable ONLY by
train through the AsahikawaStation interior (built by generate_stations.py).
Snowier and quieter than Sapporo, and not Yukimura again - it has a frozen
RIVER rather than a pond, and it is a ramen town:

  north   the rail line, the platform and the station house; west of the
          forecourt RAMEN ALLEY - three machiya shopfronts under red ラーメン
          banners, snow trees behind them
  middle  the frozen river, running bank to bank across the whole town, and
          the timber BRIDGE that is the only way over
  south   through the red torii at the bridgehead to a lane with the blue
          SHRINE hall, its fox statues, and a few cottages

The river is laid by hand (ice edge-n / center / edge-s rows) because
Builder.pond is two rows tall and rock-rimmed at both ends; the bridge is a
flat sprite over the ice whose cells are left open (see 'asahikawa-bridge' in
tools/make_prefabs.py). Bridge and banner art come from generate_hokkaido.py.
Deterministic and idempotent: rebuilds rooms.Asahikawa from scratch each run,
keeping any NPCs the blog pipeline has placed there.

Run from gamev2/:
    python3 tools/generate_hokkaido.py            # sprites (needs Pillow)
    python3 tools/make_prefabs.py
    python3 tools/generate_asahikawa.py
    python3 tools/generate_stations.py            # builds AsahikawaStation + registry
    python3 tools/fix_fences.py Asahikawa         # MANDATORY (b.fence)
    python3 tools/seal_tracks.py Asahikawa        # MANDATORY (rail line)
    node tools/play.js lint Asahikawa          (and AsahikawaStation)
    python3 tools/config_to_tiled.py Asahikawa AsahikawaStation
"""
import roomgen as rg
from roomgen import rect

cfg = rg.load_config()

W, H = 42, 32
b = rg.Builder(W, H)

b.fill('snow-autotile')

# ---- rail corridor across the north (ambient trains run along the track) ------
b.autotile('gravel-snow-autotile', rect(0, 3, W - 1, 5))   # gravel with a snow bank, not a grass fringe
for x in range(W):
    b.put('Over Floor', x, 4, 'train-track_0_0')
for x in range(1, W - 1):
    b.fence(x, 2, x)                                  # north fence line
for x in list(range(1, 18)) + list(range(35, W - 1)):
    b.fence(x, 6, x)                                  # south fence, gap at the platform
for y in (3, 4, 5):                                   # snowy caps at the corridor ends
    b.stamp('shrub-small-snow', 0, y); b.stamp('shrub-small-snow', W - 1, y)

# ---- station platform, station house, forecourt --------------------------------
b.autotile('light-concrete-autotile', rect(18, 6, 30, 8))
b.stamp('lamp-blue', 19, 7); b.stamp('lamp-blue', 29, 7)
b.stamp('vending-white', 23, 6); b.stamp('vending-red', 25, 6)
for i, px in enumerate((20, 24, 27)):
    b.paver(px, 8, i)
station_door = b.stamp('house-blue', 31, 4, seal=False)[0]   # door -> AsahikawaStation
b.autotile('light-concrete-autotile', rect(18, 9, 34, 10))

# ---- trodden paths: forecourt -> ramen alley / bridge, bridge -> shrine lane
#      (dirt-snow: the dirt path with a snow bank instead of a grass fringe) ------
BRIDGE = (20, 16)
b.autotile('dirt-snow-autotile', rect(2, 14, 21, 15) + rect(20, 11, 21, 13))
b.autotile('dirt-snow-autotile', rect(4, 28, 37, 29) + rect(20, 21, 21, 27))

# ---- ramen alley: three shopfronts, feet on row 13, facing the lane ------------
for x, colour in ((2, 'black'), (7, 'red'), (12, 'blue')):
    b.stamp(f'machiya-{colour}', x, 9)
    b.stamp('ramen-banner', x + 4, 13)                # beside each shop door
# snow trees behind the alley, and a hedge so nobody wanders in under its roofs
for x in (3, 8, 13):
    b.stamp('tree-snow', x, 6)
for y in (7, 8, 9, 10):
    b.stamp('shrub-small-snow', 17, y)
b.stamp('vending-red', 18, 12)
b.stamp('lantern-red', 22, 12)

# ---- the frozen river, bank to bank, and the bridge ------------------------------
for x in range(W):
    for y, role in ((17, 'edge-n'), (18, 'center'), (19, 'edge-s')):
        b.put('Water', x, y, f'ice-pond-autotile_{role}')
        if x not in (BRIDGE[0], BRIDGE[0] + 1):
            b.solid(x, y)
b.stamp('asahikawa-bridge', *BRIDGE)
b.stamp('lantern-red', 19, 15); b.stamp('lantern-red', 22, 15)   # the north bridgehead
for x in (5, 11, 15, 27, 33, 38):                                # bare shrubs on the banks
    b.stamp('shrub-small-snow', x, 16)
for x in (3, 9, 14, 25, 28, 35):
    b.stamp('shrub-small-snow', x, 20)

# ---- south bank: the torii astride the path at the bridgehead ------------------
b.stamp('torii-red', 18, 21)
b.stamp('lantern-red', 18, 26); b.stamp('lantern-red', 23, 26)

# ---- the shrine: hall facing the lane, foxes either side of its steps ----------
SHRINE = (29, 20)
b.stamp('shrine', *SHRINE)
b.stamp('fox-statue', 29, 26); b.stamp('fox-statue', 33, 26)
b.stamp('lantern-red', 27, 26); b.stamp('lantern-red', 35, 26)

# ---- cottages -----------------------------------------------------------------
b.stamp('house-red', 4, 21)
b.stamp('house-black', 9, 21)
b.stamp('vending-white', 7, 25)
b.stamp('tree-snow', 13, 22)
b.stamp('house-blue', 36, 20)
b.stamp('tree-snow', 25, 22)
b.stamp('sakura-small', 15, 26)

# ---- borders: snowy hedges west / east (the river itself closes rows 17-19),
#      a fence along the south --------------------------------------------------
for y in list(range(7, 17, 2)) + list(range(20, 30, 2)):
    b.stamp('shrub-large-snow', 0, y); b.stamp('shrub-large-snow', W - 2, y)
for x in (0, 1, W - 2, W - 1):
    b.stamp('shrub-small-snow', x, 30)
for x in (0, W - 1):
    b.stamp('shrub-small-snow', x, 6); b.stamp('shrub-small-snow', x, 31)
for i, x in enumerate(range(1, W - 1)):
    b.fence(x, 31, i)

# ---- keep the player off the ballast: the south fence has a gap at the
#      platform, so a platform-edge fence closes the gravel row behind it -------
for x in range(18, 35):
    if f'{x},5' not in b.L['Colliders']:
        b.fence(x, 5, x)

# isolated: the ONLY way out is the station house door into AsahikawaStation.
# NPCs are placed here by the blog pipeline (tools/blog_to_npc.py) - keep them.
prev = cfg['rooms'].get('Asahikawa', {})
cfg['rooms']['Asahikawa'] = b.room('Asahikawa', npcs=prev.get('npcs', []), transporters=[
    rg.transporter(station_door[0], station_door[1], 'AsahikawaStation', 11, 11, hidden=True),
])

rg.save_config(cfg)
print(f'Asahikawa {W}x{H}; station house door at {station_door} -> AsahikawaStation; '
      f'bridge at {BRIDGE}, shrine at {SHRINE}')
