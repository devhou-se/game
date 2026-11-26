#!/bin/bash
# kanazawa_apply.sh — rebuild every DATA change of issue #68 stage 3 (Hokuriku: Kanazawa,
# Shirakawa-go, Toyama) from scratch.
#
# Run it in a checkout that has the Hokuriku SOURCE files (tools/generate_hokuriku_art.py,
# tools/hokuriku.py, tools/generate_kanazawa.py / _shirakawago.py / _toyama.py, the Hokuriku
# entries in make_prefabs.py / generate_stations.py / generate_konbinis.py / check_generators.py /
# blog_to_npc.py, src/utils/Places.js (arrival: a town with no station), tools/tests/kanazawa.test.js,
# docs) but whatever config.json, devhouse.world, tiled/ and assets/ master has at the time - e.g.
# after another town landed first and config.json's positional tilePalette no longer rebases:
#
#     git checkout <master> -- gamev2/config.json devhouse.world gamev2/tiled gamev2/assets/map
#     .agent-queue/items/kanazawa_apply.sh [<checkout root>]      # default: the git toplevel of $PWD
#
# It is idempotent: a second run changes nothing. It ends with the five gates and exits non-zero
# if a step or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'kanazawa_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }

step 'art: sprites, spriteMetadata, tileNames, game.lookUp.sprites["toyama-port-tower"]'
"$PIL_PY" tools/generate_hokuriku_art.py
step 'station art: the name board of every STATIONS row (station-name-kanazawa: 金沢 / KANAZAWA)'
"$PIL_PY" tools/generate_station_art.py
step 'prefabs (tiled/prefabs/*.tmj)'
python3 tools/make_prefabs.py

step 'the three districts, the konbini, the station'
python3 tools/generate_kanazawa.py             # first build: konbini door sealed
python3 tools/generate_shirakawago.py
python3 tools/generate_toyama.py
python3 tools/generate_konbinis.py Kanazawa    # KonbiniKanazawa1 + the door into it
python3 tools/generate_stations.py             # KanazawaStation + the registry order
python3 tools/generate_kanazawa.py             # a re-run keeps the door: must change nothing

step 'devhouse.world: the three maps north-west of Tokyo, north of Yukimura, laid out as tools/hokuriku.py has them'
python3 - <<'PY'
import json, sys
sys.path.insert(0, 'tools')
import hokuriku as hk
# the region's top-left corner, in world cells: its box is x -112..-2, y -100..-34 - east of Fukuoka's
# east edge (-113; Fukuoka is west of every map, tools/tests/fukuoka.test.js), above Yukimura (top -32),
# west of Sapporo (4), and still overlapping Sendai's band of latitude (-50..-2)
ORIGIN = (-112, -100)
path = '../devhouse.world'
world = json.load(open(path))
entries = [{'fileName': f'gamev2/tiled/{room.lower()}.tmj',
            'x': (ORIGIN[0] + hk.AT[room][0]) * 64, 'y': (ORIGIN[1] + hk.AT[room][1]) * 64,
            'width': hk.SIZE[room][0] * 64, 'height': hk.SIZE[room][1] * 64} for room in ('Kanazawa', 'Shirakawago', 'Toyama')]
names = {e['fileName'] for e in entries}
maps = [m for m in world['maps'] if m['fileName'] not in names]
# the Map draws the city over its whole bounding box, woods included: refuse to sit on anything that landed meanwhile
box = (min(e['x'] for e in entries), min(e['y'] for e in entries),
       max(e['x'] + e['width'] for e in entries), max(e['y'] + e['height'] for e in entries))
for m in maps:
    apart = (box[2] <= m['x'] or m['x'] + m['width'] <= box[0] or box[3] <= m['y'] or m['y'] + m['height'] <= box[1])
    assert apart, f"Hokuriku would overlap {m['fileName']} in devhouse.world - move ORIGIN"
world['maps'] = maps + entries
open(path, 'w').write(json.dumps(world, indent=2))
print('devhouse.world:', [(e['fileName'], e['x'], e['y']) for e in entries])
PY

step 'config cities.HokurikuCity (the second stitched city), offsets from devhouse.world'
python3 - <<'PY'
import json
cfg = json.load(open('config.json'))
city = cfg['cities'].setdefault('HokurikuCity', {})
city['name'] = 'Hokuriku'
old = {m['room']: m for m in city.get('rooms', [])}
city['rooms'] = [old.get(room, {'room': room, 'x': 0, 'y': 0}) for room in ('Kanazawa', 'Shirakawago', 'Toyama')]
# the woodland in the gaps of the union: the same spec Tokyo's woods are grown from
city['backdrop'] = json.loads(json.dumps(cfg['cities']['TokyoCity']['backdrop']))
open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
PY
python3 tools/sync_cities.py

step 're-home the fourteen Toyama / Shirakawa-go / Kanazawa posts (no LLM call; a repeat is a no-op)'
python3 tools/blog_to_npc.py \
    --rehome Damian 2025-11-02 'Toyama · the Glass Art Museum' \
    --rehome Julia  2025-11-03 'Toyama · the tram stop' \
    --rehome Damian 2025-11-03 'Shirakawago · the suspension bridge' \
    --rehome Julia  2025-11-04 'Toyama · the port observation tower' \
    --rehome Julia  2025-11-05 'Shirakawago · the Shirakawa-go viewpoint' \
    --rehome Damian 2025-11-05 'Kanazawa · the whisky bar' \
    --rehome Bailey 2025-11-05 'KanazawaStation · the platform' \
    --rehome Julia  2025-11-06 'Kanazawa · the whisky bar' \
    --rehome Damian 2025-11-06 'Kanazawa · the Nagamachi samurai lane' \
    --rehome Bailey 2025-11-06 "Kanazawa · Kanazawa Castle's Ishikawa gate" \
    --rehome Julia  2025-11-07 'Kanazawa · Kenrokuen garden' \
    --rehome Damian 2025-11-07 'Kanazawa · the Higashi Chaya teahouse row' \
    --rehome Julia  2025-11-08 'Kanazawa · the 7-Eleven' \
    --rehome Bailey 2025-11-09 'Kanazawa · the shrine' | grep -E '^(Damian|Julia|Bailey|config)' || true

step 'Tiled maps: the new rooms, and every room a re-homed state left or passed through'
python3 tools/config_to_tiled.py $(python3 -c "
import sys; sys.path.insert(0, 'tools')
import check_generators as c
print(' '.join(sorted(set(c.tiled_rooms()) | {'Kanazawa', 'Shirakawago', 'Toyama', 'KanazawaStation', 'KonbiniKanazawa1'})))") | tail -1

step 'world map (assets/map/world-map.png + .json)'
"$PIL_PY" tools/make_worldmap.py

step 'lint the new rooms and the stitched region'
node tools/play.js lint Kanazawa Shirakawago Toyama HokurikuCity KanazawaStation KonbiniKanazawa1

step 'gates'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py
node tools/play.js check
"$PIL_PY" tools/check_generators.py
python3 tools/sync_cities.py --check
echo
echo 'kanazawa_apply: done - all five gates pass'
