#!/bin/bash
# sapporo2_apply.sh — Sapporo rebuild, stage 2 of 4: Odori Park (issue #219).
#
#     .agent-queue/items/sapporo2_apply.sh [--root <checkout root>]
#
# Run it in a checkout that has the stage 2 SOURCE files (tools/generate_sapporo.py with the
# park and PARK_CAST, tools/generate_sapporo_art.py with odori-lamp-post / odori-bench, the
# Odori prefabs in tools/make_prefabs.py, the LANDMARKS rows in tools/blog_to_npc.py, the Odori
# row of tools/districts.py, src/utils/Interactions.js and src/Shop.js with the stall rules,
# tools/tests/sapporo.test.js, tools/rehearse_blog.py, docs) and whatever config.json, tiled/
# and assets/ master has at the time. It rebuilds the DATA from them:
#
#   art        generate_sapporo_art.py  the two new sprites (lamp, bench) + spriteMetadata / tileNames
#   prefabs    make_prefabs.py          the sculptures, the tents, the fountain, lamp, bench, snowbanks
#   town       generate_sapporo.py      Odori Park's three blocks on the packed-snow path; the frozen
#                                       pond and its sakura gone; Sam and Julia moved to park spots
#                                       (only from the cells they had before stage 2), Julia's
#                                       line naming the snow castle instead of the Clock Tower
#   districts  districts.py             Odori Park's description, stand cell and the spots inside it
#   map        config_to_tiled.py Sapporo
#   world map  make_worldmap.py         the park changed
#   baseline   check_distinct.py --update   (only after the check itself passes: nothing got worse)
#
# No interior is added or removed by this stage and no blog placement had to be re-homed (no
# dated state and no base NPC stood by the pond). It is idempotent: a second run changes
# nothing. It ends with the five gates and the blog rehearsal and exits non-zero if a step, a
# lint or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT=""
if [ "${1:-}" = "--root" ]; then ROOT="$2"; shift 2; fi
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'sapporo2_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }
grep -q "'snow-sculpture-castle'" tools/make_prefabs.py && grep -q 'def odori_lamp' tools/generate_sapporo_art.py \
    && grep -q 'PARK_CAST' tools/generate_sapporo.py && grep -q "'the snow castle'" tools/blog_to_npc.py \
    && grep -q "snowfest-stall-drinks" src/utils/Interactions.js \
    || { echo 'sapporo2_apply: the stage 2 source files are not in this checkout'; exit 1; }

step 'art: the lamp and the bench, spriteMetadata / tileNames; prefabs'
"$PIL_PY" tools/generate_sapporo_art.py | tail -1
python3 tools/make_prefabs.py | tail -1

step 'the town (Odori Park; the pond goes; Sam and Julia to the park), then the districts'
python3 tools/generate_sapporo.py
python3 tools/districts.py | tail -1

step 'Tiled map'
python3 tools/config_to_tiled.py Sapporo | tail -1

step 'world map (the park changed)'
"$PIL_PY" tools/make_worldmap.py | tail -1

step 'lint'
out=$(node tools/play.js lint Sapporo | tail -1); echo "$out"
case "$out" in *' 0 errors'*) ;; *) echo 'sapporo2_apply: lint errors in Sapporo'; exit 1;; esac

step 'distinctness: not worse than the baseline, then record it'
python3 tools/check_distinct.py | grep -E '^(city|target|Sapporo|no city)' || { echo 'sapporo2_apply: a city is worse than the baseline'; exit 1; }
python3 tools/check_distinct.py >/dev/null || { echo 'sapporo2_apply: a city is worse than the baseline'; exit 1; }
python3 tools/check_distinct.py --update | tail -1

step 'the five gates and the blog rehearsal'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py 2>&1 | tail -1
node tools/play.js check | tail -1
GEN=$("$PIL_PY" tools/check_generators.py) || { echo "$GEN" | grep -v '^ok'; echo 'sapporo2_apply: check_generators failed'; exit 1; }
echo "check_generators: $(echo "$GEN" | grep -c '^ok') ok, $(echo "$GEN" | grep -c '^skip' || true) skipped"
python3 tools/sync_cities.py --check | tail -1
python3 tools/rehearse_blog.py 2>&1 | grep 'rehearsal' | tail -1
echo
echo 'sapporo2_apply: done - Sapporo stage 2 (Odori Park) is built, all gates pass'
