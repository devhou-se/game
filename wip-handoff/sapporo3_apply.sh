#!/bin/bash
# sapporo3_apply.sh — Sapporo rebuild, stage 3 of 4: Tanukikoji (issue #219).
#
#     .agent-queue/items/sapporo3_apply.sh [--root <checkout root>]
#
# Run it in a checkout that has the stage 3 SOURCE files (tools/generate_sapporo.py with the
# arcade and the two moved cast, the Tanukikoji prefabs in tools/make_prefabs.py, SHOP_DOORS in
# tools/roomgen.py, the shop kind of tools/generate_houses.py, the LANDMARKS rows in
# tools/blog_to_npc.py, the Tanukikoji row of tools/districts.py, src/Shop.js with the three
# shop venues, the tests, docs) and whatever config.json, tiled/ and assets/ master has at the
# time. It rebuilds the DATA from them:
#
#   prefabs    make_prefabs.py            the three shopfronts, the gate, the end sign, the south row
#   town       generate_sapporo.py        Tanukikoji on arcade-brick south of Minami-Odori; the six
#                                         townhouses gone; the station plaza repaved in stone slabs;
#                                         the 7-Eleven moved from the Clock Tower block to the arcade;
#                                         Xander and Khoi moved to arcade spots (only from the cells
#                                         they had before stage 3)
#   konbini    generate_konbinis.py Sapporo   KonbiniSapporo1 re-wired to its new door (same key and name)
#   houses     generate_houses.py Sapporo     HouseSapporo1..6 removed (no townhouse is left)
#   shops      generate_houses.py --shops Sapporo   ShopSapporo1..3 behind the three shopfronts
#   town       generate_sapporo.py        once more: a rebuild keeps every door the others wired
#   districts  districts.py               the Tanukikoji district, the Clock Tower block's and the
#                                         station front's descriptions, the spots inside each
#   maps       config_to_tiled.py         Sapporo, KonbiniSapporo1, ShopSapporo1..3; the House maps removed
#   world map  make_worldmap.py
#   baseline   check_distinct.py --update   (only after the check itself passes: nothing got worse)
#
# No blog placement had to be re-homed (no dated state stood south of Minami-Odori or at the
# konbini). It is idempotent: a second run changes nothing. It ends with the five gates and the
# blog rehearsal and exits non-zero if a step, a lint or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT=""
if [ "${1:-}" = "--root" ]; then ROOT="$2"; shift 2; fi
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'sapporo3_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }
owned() {       # "<room> ..." of every Sapporo interior generate_houses.py owns
    python3 - <<'PY'
import json
cfg = json.load(open('config.json'))
print(' '.join(sorted(k for k, r in cfg['rooms'].items()
                      if any((r.get(m) or {}).get('host') == 'Sapporo' for m in ('house', 'lobby', 'shop')))))
PY
}
grep -q "'tanukikoji-gate'" tools/make_prefabs.py && grep -q 'SHOP_DOORS' tools/roomgen.py \
    && grep -q 'def build_shop' tools/generate_houses.py && grep -q 'ARCADE_BRICK' tools/generate_sapporo.py \
    && grep -q "'Tanukikoji arcade'" tools/blog_to_npc.py && grep -q "'tanukikoji'" tools/districts.py \
    && grep -q 'souvenirs:' src/Shop.js \
    || { echo 'sapporo3_apply: the stage 3 source files are not in this checkout'; exit 1; }

step 'prefabs'
python3 tools/make_prefabs.py | tail -1

step 'the town, then the konbini (moved), the houses (gone) and the shops'
BEFORE=$(owned)
python3 tools/generate_sapporo.py
python3 tools/generate_konbinis.py Sapporo | grep '^built'
python3 tools/generate_houses.py Sapporo | grep -v '^$' | tail -3
python3 tools/generate_houses.py --shops Sapporo | grep -v '^$' | grep -E '^(built|skipped|not)'
python3 tools/generate_sapporo.py >/dev/null      # a rebuild keeps every door the others wired
python3 tools/districts.py | tail -1

step 'Tiled maps: Sapporo, its konbini and its shops; the House maps go'
AFTER=$(owned)
SHOPS=$(echo "$AFTER" | tr ' ' '\n' | grep -E '^ShopSapporo' | tr '\n' ' ')
[ "$(echo $SHOPS | wc -w | tr -d ' ')" = 3 ] || { echo "sapporo3_apply: expected three shops, got: $SHOPS"; exit 1; }
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py Sapporo KonbiniSapporo1 $SHOPS | tail -1
for room in $BEFORE HouseSapporo1 HouseSapporo2 HouseSapporo3 HouseSapporo4 HouseSapporo5 HouseSapporo6; do
    case " $AFTER " in *" $room "*) ;; *) f="tiled/$(echo "$room" | tr '[:upper:]' '[:lower:]').tmj"
        if [ -e "$f" ]; then rm -f "$f"; echo "removed the map of $room"; fi;; esac
done

step 'world map (the south changed)'
"$PIL_PY" tools/make_worldmap.py | tail -1

step 'lint'
# shellcheck disable=SC2086
for room in Sapporo KonbiniSapporo1 $SHOPS; do
    out=$(node tools/play.js lint "$room" | tail -1); echo "$out"
    case "$out" in *' 0 errors'*) ;; *) echo "sapporo3_apply: lint errors in $room"; exit 1;; esac
done

step 'distinctness: not worse than the baseline, then record it'
python3 tools/check_distinct.py | grep -E '^(city|target|Sapporo|no city)' || { echo 'sapporo3_apply: a city is worse than the baseline'; exit 1; }
python3 tools/check_distinct.py >/dev/null || { echo 'sapporo3_apply: a city is worse than the baseline'; exit 1; }
python3 tools/check_distinct.py --update | tail -1

step 'the five gates and the blog rehearsal'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py 2>&1 | tail -1
node tools/play.js check | tail -1
GEN=$("$PIL_PY" tools/check_generators.py) || { echo "$GEN" | grep -v '^ok'; echo 'sapporo3_apply: check_generators failed'; exit 1; }
echo "check_generators: $(echo "$GEN" | grep -c '^ok') ok, $(echo "$GEN" | grep -c '^skip' || true) skipped"
python3 tools/sync_cities.py --check | tail -1
python3 tools/rehearse_blog.py 2>&1 | grep 'rehearsal' | tail -1
echo
echo 'sapporo3_apply: done - Sapporo stage 3 (Tanukikoji) is built, all gates pass'
