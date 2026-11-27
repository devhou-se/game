#!/bin/bash
# lobbies_apply.sh — give the towers of the named towns their lobby (issue #216).
#
#     .agent-queue/items/lobbies_apply.sh [--root <checkout root>] <Town> [<Town> ...]
#     .agent-queue/items/lobbies_apply.sh Osaka
#     .agent-queue/items/lobbies_apply.sh Sapporo Sendai Fukuoka        # the rollout
#
# Run it in a checkout that has the #216 SOURCE files (tools/generate_houses.py with --lobbies,
# the lobby sprites in tools/generate_house_art.py, TOWER_DOORS and the door keeping in
# tools/roomgen.py, src/utils/Interactions.js, tools/world-model.js, tools/tests/lobbies.test.js,
# docs) and whatever config.json, tiled/ and assets/ master has at the time. <Town> is a room
# key (Osaka, Sapporo, Market ...).
#
# For each town it opens every high-rise, office tower and block of flats generate_houses.py
# accepts (roomgen.TOWER_DOORS; see the generator's docstring for what makes one stay sealed)
# into a `Lobby<Town><n>` room - one design, identical everywhere - and prints the towers it
# skipped and why. Towns that already have lobbies are rebuilt too, so the whole set stays in
# step. Houses are not touched (that is houses_apply.sh), in either direction. Nothing outdoors
# changes to the eye - a doorway is a hidden transporter and one collider fewer - so the world
# map is left alone. A town generator needs no edit: roomgen.save_config puts the lobby doors
# back after a rebuild.
#
# It is idempotent: a second run changes nothing. It ends with the five gates and exits
# non-zero if a step, a lint or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT=""
if [ "${1:-}" = "--root" ]; then ROOT="$2"; shift 2; fi
[ $# -ge 1 ] || { echo 'usage: lobbies_apply.sh [--root <checkout root>] <Town> [<Town> ...]'; exit 2; }
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'lobbies_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }
lobbies() {     # "<room> ..." of every tower lobby in config.json, with the towns they open off
    python3 - <<'PY'
import json
cfg = json.load(open('config.json'))
rooms = sorted(k for k, r in cfg['rooms'].items() if r.get('lobby'))
towns = sorted({cfg['rooms'][k]['lobby']['host'] for k in rooms})
print(' '.join(rooms + towns))
PY
}

step 'art: the lobby sprites (and the furniture of a home, unchanged)'
"$PIL_PY" tools/generate_house_art.py

step "tower lobbies: $* (and every town that already has them)"
BEFORE=$(lobbies)
# shellcheck disable=SC2046
python3 tools/generate_houses.py --lobbies $(python3 - "$@" <<'PY'
import json, sys
cfg = json.load(open('config.json'))
have = {r['lobby']['host'] for r in cfg['rooms'].values() if r.get('lobby')}
print(' '.join(sorted(have | set(sys.argv[1:]))))
PY
)

step 'Tiled maps: every lobby and every town with a lobby door'
ROOMS=$(lobbies)
# a named town whose towers were all skipped has no lobby, but a door of it may have been sealed
for town in "$@"; do case " $ROOMS " in *" $town "*) ;; *) ROOMS="$ROOMS $town";; esac; done
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py $ROOMS
for room in $BEFORE; do     # a tower that is sealed again (someone stands at its door now) loses its map
    case " $ROOMS " in *" $room "*) ;; *) rm -f "tiled/$(echo "$room" | tr '[:upper:]' '[:lower:]').tmj"; echo "removed the map of $room";; esac
done

step 'lint every lobby and its town'
for room in $ROOMS; do
    out=$(node tools/play.js lint "$room" | tail -1); echo "$out"
    case "$out" in *' 0 errors'*) ;; *) echo "lobbies_apply: lint errors in $room"; exit 1;; esac
done

step 'the five gates'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py 2>&1 | tail -1
node tools/play.js check | tail -1
GEN=$("$PIL_PY" tools/check_generators.py) || { echo "$GEN" | grep -v '^ok'; echo 'lobbies_apply: check_generators failed'; exit 1; }
echo "check_generators: $(echo "$GEN" | grep -c '^ok') ok, $(echo "$GEN" | grep -c '^skip' || true) skipped"
python3 tools/sync_cities.py --check | tail -1
echo
echo "lobbies_apply: done - $(echo "$ROOMS" | tr ' ' '\n' | grep -c "^Lobby") lobby interior(s), all five gates pass"
