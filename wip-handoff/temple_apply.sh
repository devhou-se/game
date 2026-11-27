#!/bin/bash
# temple_apply.sh — give Senso-ji, the great hall at the head of the stall street in the Tokyo district
# `Market` (display name Asakusa), its main hall (issue #213), on a checkout that has
# tools/generate_temple.py and tools/generate_temple_art.py.
#
#   cd <checkout>/gamev2 && bash /Users/bbutler/bb/game/.agent-queue/items/temple_apply.sh
#   (or GV2=<checkout>/gamev2 bash temple_apply.sh)
#
# For replaying the change onto a master whose tilePalette has moved on: take the lane's source files
# (tools/, src/, docs/, index.html, tools/tests/temple.test.js) and master's config.json, tiled/ and
# assets/, then run this. It draws the art (appending its sprites to the palette where master's ends),
# runs the generator (the room TempleMarket1, and in Market only the hall's two door leaves: a collider
# off and a transporter on each), re-seeds the two Tiled maps, lints them, checks that nobody stands in
# the doorway on any date, and ends with the five gates. Exit 0 only if everything passed.
# Idempotent: a second run changes no file. Nothing is committed. No new world map is needed: outdoors
# only two door cells open.
set -euo pipefail
cd "${GV2:-.}"
[ -f tools/generate_temple.py ] && [ -f tools/generate_temple_art.py ] && [ -f config.json ] || {
    echo "run from gamev2/ of a checkout that has tools/generate_temple.py (or set GV2)" >&2; exit 2; }
export OPENSSL_CONF=/dev/null
PY="${PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"     # a python3 with Pillow
"$PY" -c 'import PIL' 2>/dev/null || { echo "$PY has no Pillow (set PY)" >&2; exit 2; }

echo "== art"
"$PY" tools/generate_temple_art.py >/dev/null

echo "== generator"
OUT=$(python3 tools/generate_temple.py)
echo "$OUT"
ROOMS=$(echo "$OUT" | tail -1)

echo "== maps and lint: $ROOMS"
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py $ROOMS >/dev/null
# shellcheck disable=SC2086
node tools/play.js lint $ROOMS

echo "== no dated NPC and no district stand cell on the temple door or the cell in front of it"
python3 - <<'PYEOF'
import json, sys
c = json.load(open('config.json'))
bad = []
for key, room in c['rooms'].items():
    for t in room.get('transporters', []):
        if not t['targetRoom'].startswith('Temple'):
            continue
        cells = {(t['gridX'], t['gridY']), (t['gridX'], t['gridY'] + 1)}
        for n in room.get('npcs', []):
            for date, s in [('base', n)] + sorted((n.get('states') or {}).items()):
                if (s.get('gridX'), s.get('gridY')) in cells:
                    bad.append(f"{key}: {n['name']} {date} at {s['gridX']},{s['gridY']} (door {t['gridX']},{t['gridY']})")
        for d in (c.get('districts') or {}).get(key, []):
            if tuple(d.get('stand') or ()) in cells:
                bad.append(f"{key}: district {d['name']} stands its visitor at {d['stand']} (door {t['gridX']},{t['gridY']})")
print('\n'.join(bad) or 'none')
if bad:
    print('move the placement with: python3 tools/blog_to_npc.py --rehome <NPC> <date> "<Room> · <label>"', file=sys.stderr)
    sys.exit(1)
PYEOF

echo "== gates"
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py | tail -1
node tools/play.js check | tail -1
"$PY" tools/check_generators.py | grep -v '^ok ' || true
"$PY" tools/check_generators.py >/dev/null
python3 tools/sync_cities.py --check | tail -1
echo "temple_apply: done ($ROOMS)"
