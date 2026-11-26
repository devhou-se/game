#!/bin/bash
# shrines_apply.sh <Room> [<Room> ...] — give the shrine halls of the named towns their worship hall
# interior (issue #212), on a checkout that has tools/generate_shrines.py and its art tools.
#
#   cd <checkout>/gamev2 && bash /Users/bbutler/bb/game/.agent-queue/items/shrines_apply.sh Asahikawa Fukuoka
#   (or GV2=<checkout>/gamev2 bash shrines_apply.sh Asahikawa)
#
# Idempotent: a second run changes no file. It draws the art, runs the generator for the named towns
# (the halls already wired are rebuilt with them), re-seeds the Tiled maps of every interior and host,
# lints them, and ends with the five gates. Exit 0 only if everything passed.
# Nothing is committed. A town whose map changed visibly needs no new world map: only a door opens.
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: shrines_apply.sh <Room> [<Room> ...]" >&2; exit 2; }
cd "${GV2:-.}"
[ -f tools/generate_shrines.py ] && [ -f tools/generate_shrine_art.py ] && [ -f config.json ] || {
    echo "run from gamev2/ of a checkout that has tools/generate_shrines.py (or set GV2)" >&2; exit 2; }
export OPENSSL_CONF=/dev/null
PY="${PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"     # a python3 with Pillow
"$PY" -c 'import PIL' 2>/dev/null || { echo "$PY has no Pillow (set PY)" >&2; exit 2; }

echo "== art"
"$PY" tools/extract_shrine.py >/dev/null
"$PY" tools/generate_shrine_art.py >/dev/null

echo "== generator: $*"
# the towns named now, plus the ones wired before (the generator's default), in one run
WIRED=$(python3 - <<'PYEOF'
import json
c = json.load(open('config.json'))
print(' '.join(k for k, r in c['rooms'].items()
               if any(t['targetRoom'].startswith('Shrine') for t in r.get('transporters', []))))
PYEOF
)
HOSTS=$(printf '%s\n' "$@" $WIRED | awk 'NF && !seen[$0]++' | tr '\n' ' ')
# shellcheck disable=SC2086
OUT=$(python3 tools/generate_shrines.py $HOSTS)
echo "$OUT"
ROOMS=$(echo "$OUT" | tail -1)

echo "== maps and lint: $ROOMS"
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py $ROOMS >/dev/null
# shellcheck disable=SC2086
node tools/play.js lint $ROOMS

echo "== no dated NPC on a shrine door or the cell in front of it"
python3 - <<'PYEOF'
import json, sys
c = json.load(open('config.json'))
bad = []
for key, room in c['rooms'].items():
    for t in room.get('transporters', []):
        if not t['targetRoom'].startswith('Shrine'):
            continue
        cells = {(t['gridX'], t['gridY']), (t['gridX'], t['gridY'] + 1)}
        for n in room.get('npcs', []):
            for date, s in [('base', n)] + sorted((n.get('states') or {}).items()):
                if (s.get('gridX'), s.get('gridY')) in cells:
                    bad.append(f"{key}: {n['name']} {date} at {s['gridX']},{s['gridY']} (door {t['gridX']},{t['gridY']})")
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
echo "shrines_apply: done ($ROOMS)"
