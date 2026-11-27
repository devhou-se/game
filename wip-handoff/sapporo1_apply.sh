#!/bin/bash
# sapporo1_apply.sh — Sapporo rebuild, stage 1 of 4: the north of the town (issue #219).
#
#     .agent-queue/items/sapporo1_apply.sh [--root <checkout root>]
#
# Run it in a checkout that has the stage 1 SOURCE files (tools/generate_sapporo.py,
# tools/generate_sapporo_art.py with its register(), the four sapporo-* prefabs in
# tools/make_prefabs.py, the two office rows in roomgen.TOWER_DOORS, SapporoStation's row in
# generate_stations.py TOWN_DOORS, check_generators.py, tools/tests/sapporo.test.js and the
# edited lobbies / houses tests, docs) and whatever config.json, tiled/ and assets/ master has
# at the time. It rebuilds the DATA from them:
#
#   art       generate_sapporo_art.py   sprites (unchanged) + spriteMetadata / tileNames
#   prefabs   make_prefabs.py           sapporo-station-front / -akarenga / -office-brick / -office-glass
#   town      generate_sapporo.py       the station front, the government hall, the two office
#                                       blocks, the two districts' ground; no house in the north
#   station   generate_stations.py      the way out of SapporoStation lands in front of the new doors
#   houses    generate_houses.py Sapporo            the north-east house is gone: HouseSapporo1..6
#   lobbies   generate_houses.py --lobbies ...      LobbySapporo1 (brick block), LobbySapporo2 (glass)
#   maps      config_to_tiled.py, and the map of a house / lobby room that no longer exists is removed
#   world map make_worldmap.py          buildings moved
#
# It is idempotent: a second run changes nothing. It ends with the five gates and the blog
# rehearsal and exits non-zero if a step, a lint or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT=""
if [ "${1:-}" = "--root" ]; then ROOT="$2"; shift 2; fi
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'sapporo1_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }
owned() {       # "<room> ..." of every house and lobby interior in config.json
    python3 - <<'PY'
import json
cfg = json.load(open('config.json'))
print(' '.join(sorted(k for k, r in cfg['rooms'].items() if r.get('house') or r.get('lobby'))))
PY
}
grep -q "'sapporo-station-front'" tools/make_prefabs.py && grep -q 'def register' tools/generate_sapporo_art.py \
    && grep -q "sapporo-office-brick_0_0" tools/roomgen.py \
    || { echo 'sapporo1_apply: the stage 1 source files are not in this checkout'; exit 1; }

step 'art: Sapporo sprites and their spriteMetadata / tileNames; prefabs'
"$PIL_PY" tools/generate_sapporo_art.py | tail -1
python3 tools/make_prefabs.py | tail -1

step 'the town, then the station (its way out), the houses and the lobbies'
BEFORE=$(owned)
python3 tools/generate_sapporo.py
python3 tools/generate_stations.py | tail -1
python3 tools/generate_houses.py Sapporo | grep -v '^$' | tail -9
# shellcheck disable=SC2046
python3 tools/generate_houses.py --lobbies $(python3 - <<'PY'
import json
cfg = json.load(open('config.json'))
print(' '.join(sorted({r['lobby']['host'] for r in cfg['rooms'].values() if r.get('lobby')} | {'Sapporo'})))
PY
) | grep -v '^$' | tail -9
python3 tools/generate_sapporo.py >/dev/null      # a rebuild keeps every door the others wired

step 'Tiled maps: Sapporo, its station, its houses and lobbies'
AFTER=$(owned)
ROOMS="Sapporo SapporoStation $(echo "$AFTER" | tr ' ' '\n' | grep -E '^(House|Lobby)Sapporo' | tr '\n' ' ')"
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py $ROOMS | tail -1
for room in $BEFORE HouseSapporo7; do       # an interior that is gone (HouseSapporo7 after the renumbering) loses its map
    case " $AFTER " in *" $room "*) ;; *) f="tiled/$(echo "$room" | tr '[:upper:]' '[:lower:]').tmj"
        if [ -e "$f" ]; then rm -f "$f"; echo "removed the map of $room"; fi;; esac
done

step 'world map (buildings moved)'
"$PIL_PY" tools/make_worldmap.py | tail -1

step 'lint'
for room in $ROOMS; do
    out=$(node tools/play.js lint "$room" | tail -1); echo "$out"
    case "$out" in *' 0 errors'*) ;; *) echo "sapporo1_apply: lint errors in $room"; exit 1;; esac
done

step 'the five gates and the blog rehearsal'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py 2>&1 | tail -1
node tools/play.js check | tail -1
GEN=$("$PIL_PY" tools/check_generators.py) || { echo "$GEN" | grep -v '^ok'; echo 'sapporo1_apply: check_generators failed'; exit 1; }
echo "check_generators: $(echo "$GEN" | grep -c '^ok') ok, $(echo "$GEN" | grep -c '^skip' || true) skipped"
python3 tools/sync_cities.py --check | tail -1
python3 tools/rehearse_blog.py 2>&1 | grep 'rehearsal' | tail -1
echo
echo 'sapporo1_apply: done - Sapporo stage 1 (the north) is built, all gates pass'
