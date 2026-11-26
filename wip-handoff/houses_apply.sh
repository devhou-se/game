#!/bin/bash
# houses_apply.sh — give the houses of the named towns their generic interiors (issue #208).
#
#     .agent-queue/items/houses_apply.sh [--root <checkout root>] <Town> [<Town> ...]
#     .agent-queue/items/houses_apply.sh Asahikawa
#     .agent-queue/items/houses_apply.sh Sapporo Sendai Machi Market      # the rollout
#
# Run it in a checkout that has the #208 SOURCE files (tools/generate_houses.py,
# tools/generate_house_art.py, tools/extract_house_interior.py, the house-door keeping in
# tools/roomgen.py, check_generators.py, src/utils/Interactions.js, src/GameScene.js,
# tools/world-model.js, tools/tests/houses.test.js, docs) and whatever config.json, tiled/
# and assets/ master has at the time. <Town> is a room key (Asahikawa, Sapporo, Market ...).
#
# For each town it opens every house generate_houses.py accepts (see its docstring for what
# counts as a house and what makes one stay sealed) into a `House<Town><n>` room, and prints
# the houses it skipped and why. Towns that already have houses are rebuilt too, so the
# whole set stays in step. Nothing outdoors changes to the eye - a doorway is a hidden
# transporter and one collider fewer - so the world map is left alone. A town generator
# needs no edit: roomgen.save_config puts the house doors back after a rebuild.
#
# It is idempotent: a second run changes nothing. It ends with the five gates and exits
# non-zero if a step, a lint or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT=""
if [ "${1:-}" = "--root" ]; then ROOT="$2"; shift 2; fi
[ $# -ge 1 ] || { echo 'usage: houses_apply.sh [--root <checkout root>] <Town> [<Town> ...]'; exit 2; }
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'houses_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }
houses() {      # "<room> ..." of every house interior in config.json, with the towns they open off
    python3 - <<'PY'
import json
cfg = json.load(open('config.json'))
rooms = sorted(k for k, r in cfg['rooms'].items() if r.get('house'))
towns = sorted({cfg['rooms'][k]['house']['host'] for k in rooms})
print(' '.join(rooms + towns))
PY
}

step 'art: the two pack crops, then the furniture of a home'
"$PIL_PY" tools/extract_house_interior.py
"$PIL_PY" tools/generate_house_art.py

step "house interiors: $* (and every town that already has them)"
BEFORE=$(houses)
# shellcheck disable=SC2046
python3 tools/generate_houses.py $(python3 - "$@" <<'PY'
import json, sys
cfg = json.load(open('config.json'))
have = {r['house']['host'] for r in cfg['rooms'].values() if r.get('house')}
print(' '.join(sorted(have | set(sys.argv[1:]))))
PY
)

step 'Tiled maps: every house interior and every town with a house door'
ROOMS=$(houses)
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py $ROOMS
for room in $BEFORE; do     # a house that is sealed again (someone stands at its door now) loses its map
    case " $ROOMS " in *" $room "*) ;; *) rm -f "tiled/$(echo "$room" | tr '[:upper:]' '[:lower:]').tmj"; echo "removed the map of $room";; esac
done

step 'lint every house interior and its town'
for room in $ROOMS; do
    out=$(node tools/play.js lint "$room" | tail -1); echo "$out"
    case "$out" in *' 0 errors'*) ;; *) echo "houses_apply: lint errors in $room"; exit 1;; esac
done

step 'the five gates'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py 2>&1 | tail -1
node tools/play.js check | tail -1
GEN=$("$PIL_PY" tools/check_generators.py) || { echo "$GEN" | grep -v '^ok'; echo 'houses_apply: check_generators failed'; exit 1; }
echo "check_generators: $(echo "$GEN" | grep -c '^ok') ok, $(echo "$GEN" | grep -c '^skip' || true) skipped"
python3 tools/sync_cities.py --check | tail -1
echo
echo "houses_apply: done - $(echo "$ROOMS" | tr ' ' '\n' | grep -c "^House") house interior(s), all five gates pass"
