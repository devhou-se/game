#!/bin/bash
# sanfranbourne_apply.sh — rebuild every DATA change of issue #218 (San Franbourne, the two
# airports, the Haneda rail stop) from scratch.
#
# Run it in a checkout that has the #218 SOURCE files (tools/generate_sanfranbourne.py,
# generate_sanfranbourne_art.py, generate_airports.py, the Haneda row in generate_stations.py,
# the SanFranbourne host in generate_konbinis.py, check_generators.py, blog_to_npc.py,
# src/AirTravel.js and the src/ edits, tools/tests/airports.test.js, docs) but whatever
# config.json, devhouse.world, tiled/ and assets/ master has at the time - e.g. after another
# town or a batch of interiors landed first and config.json's positional tilePalette no
# longer rebases:
#
#     git checkout <master> -- gamev2/config.json devhouse.world gamev2/tiled gamev2/assets
#     .agent-queue/items/sanfranbourne_apply.sh [<checkout root>]   # default: the git toplevel of $PWD
#
# What it writes: assets/sprites/{sfb-*,airport-*,plane-*,station-name-haneda}*.png,
# config.json (spriteMetadata, tileNames, tilePalette appends, game.lookUp.sprites, rooms
# SanFranbourne / SanFranbourneAirport / HanedaAirport / HanedaStation / KonbiniSanFranbourne1,
# `airports`, `stations` (Haneda Airport is stop 3 on the board; the later stops' `order`
# moves up one), places.SanFranbourne), tiled/*.tmj for those five rooms, devhouse.world
# (the city far to the south-east) and assets/map/world-map.{png,json}.
#
# It is idempotent: a second run changes nothing. It ends with the five gates and the blog
# rehearsal and exits non-zero if a step, a lint or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'sanfranbourne_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }
ROOMS='SanFranbourne SanFranbourneAirport HanedaAirport HanedaStation KonbiniSanFranbourne1'

step 'art: the city, the airport furniture, the cabin and the sky; the Haneda name board'
"$PIL_PY" tools/generate_sanfranbourne_art.py
"$PIL_PY" tools/generate_station_art.py

step 'the airports, the city, its konbini, the Haneda rail stop'
python3 tools/generate_airports.py                  # first build: Haneda's way out assumes a small station (11,11)
python3 tools/generate_sanfranbourne.py             # first build: konbini door sealed
python3 tools/generate_konbinis.py SanFranbourne    # KonbiniSanFranbourne1 + the door into it
python3 tools/generate_stations.py                  # HanedaStation + the registry order
python3 tools/generate_airports.py                  # re-runs keep everything: must change nothing
python3 tools/generate_sanfranbourne.py

step 'devhouse.world: the home city far to the south-east, clear of every other map'
python3 - <<'PY'
import json
path = '../devhouse.world'
world = json.load(open(path))
name, size = 'gamev2/tiled/sanfranbourne.tmj', 60 * 64
maps = [m for m in world['maps'] if m['fileName'] != name]
# south and east of everything that is there now, by a clear margin, on the 64px grid
x = max(16000, (max(m['x'] + m['width'] for m in maps) + 3712) // 64 * 64)
y = max(12800, (max(m['y'] + m['height'] for m in maps) + 3392) // 64 * 64)
entry = {'fileName': name, 'x': x, 'y': y, 'width': size, 'height': size}
for m in maps:
    assert entry['x'] >= m['x'] + m['width'] + 1024 and entry['y'] >= m['y'] + m['height'] + 1024, \
        f"San Franbourne is not clear to the south-east of {m['fileName']}"
world['maps'] = maps + [entry]
open(path, 'w').write(json.dumps(world, indent=2))
print('devhouse.world:', entry)
PY

step 'Tiled maps for every room touched'
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py $ROOMS

step 'world map (assets/map/world-map.png + .json)'
"$PIL_PY" tools/make_worldmap.py

step 'lint the new rooms'
for room in $ROOMS; do
    out=$(node tools/play.js lint "$room" | tail -1); echo "$out"
    case "$out" in *' 0 errors'*) ;; *) echo "sanfranbourne_apply: lint errors in $room"; exit 1;; esac
done

step 'gates'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py 2>&1 | tail -1
node tools/play.js check | tail -1
GEN=$("$PIL_PY" tools/check_generators.py) || { echo "$GEN" | grep -v '^ok'; echo 'sanfranbourne_apply: check_generators failed'; exit 1; }
echo "check_generators: $(echo "$GEN" | grep -c '^ok') ok, $(echo "$GEN" | grep -c '^skip' || true) skipped"
python3 tools/sync_cities.py --check | tail -1
python3 tools/rehearse_blog.py 2>&1 | grep 'checks passed'
echo
echo 'sanfranbourne_apply: done - all five gates and the blog rehearsal pass'
