#!/bin/bash
# sapporo4_apply.sh — Sapporo rebuild, stage 4 of 4: Susukino and the streetcar (issue #219).
#
#     .agent-queue/items/sapporo4_apply.sh [--root <checkout root>]
#
# Run it in a checkout that has the stage 4 SOURCE files (tools/generate_sapporo.py at 56x51 with
# Susukino, the tramway and the two moved cast; the ramen counters and susukino-asphalt-autotile in
# tools/generate_sapporo_art.py; the Susukino prefabs in tools/make_prefabs.py; the neon corner in
# roomgen.TOWER_DOORS and the karaoke bar in roomgen.SHOP_DOORS / generate_houses.SHOP_TYPES; the
# LANDMARKS rows and `tram-rail` in NOT_PLAIN in tools/blog_to_npc.py; the Susukino row of
# tools/districts.py; src/Shop.js with the `bar` and `ramen` venues, the Interactions rule, the
# Glows rows; the tests, docs) and whatever config.json, devhouse.world, tiled/ and assets/ master
# has at the time. It rebuilds the DATA from them:
#
#   art        generate_sapporo_art.py    the two ramen counters and Susukino's wet asphalt (PNGs and
#                                         their spriteMetadata / tileNames)
#   prefabs    make_prefabs.py            the neon corner, the karaoke bar, the ramen gate and counters,
#                                         the two lantern poles, the tram pole
#   town       generate_sapporo.py        the room grown from 56x43 to 56x51; the three north-south
#                                         streets run on to the tram street; Susukino; the rails; the
#                                         `tramways` row; Dylan and Khoi moved to Susukino spots (only
#                                         from the cells they had before stage 4)
#   shops      generate_houses.py --shops Sapporo     ShopSapporo4, the karaoke bar (1..3 keep their keys)
#   lobbies    generate_houses.py --lobbies Sapporo   LobbySapporo3, the neon corner (1..2 keep theirs)
#   town       generate_sapporo.py        once more: a rebuild keeps every door the others wired
#   world      devhouse.world             Sapporo's slot takes the room's new height, grown NORTHWARD:
#                                         its south edge and its columns stay, so it clears every map
#   districts  districts.py               the Susukino district and the spots inside each
#   maps       config_to_tiled.py         Sapporo and every interior generate_houses.py owns there
#   world map  make_worldmap.py
#   baseline   check_distinct.py --update   (only after the check itself passes: nothing got worse)
#
# No blog placement had to be re-homed (no dated state stands in Sapporo). It is idempotent: a
# second run changes nothing. It ends with the five gates and the blog rehearsal and exits non-zero
# if a step, a lint or a gate fails. Nothing here needs the network.
set -euo pipefail

ROOT=""
if [ "${1:-}" = "--root" ]; then ROOT="$2"; shift 2; fi
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
cd "$ROOT/gamev2"
export OPENSSL_CONF=/dev/null

# an interpreter with Pillow for the imaging tools (plain python3 has none on this machine)
PIL_PY="${PIL_PY:-/Library/Developer/CommandLineTools/usr/bin/python3}"
"$PIL_PY" -c 'import PIL' 2>/dev/null || PIL_PY=python3
"$PIL_PY" -c 'import PIL' || { echo 'sapporo4_apply: no python3 with Pillow (set PIL_PY)'; exit 1; }

step() { printf '\n== %s\n' "$*"; }
owned() {       # "<room> ..." of every Sapporo interior generate_houses.py owns
    python3 - <<'PY'
import json
cfg = json.load(open('config.json'))
print(' '.join(sorted(k for k, r in cfg['rooms'].items()
                      if any((r.get(m) or {}).get('host') == 'Sapporo' for m in ('house', 'lobby', 'shop')))))
PY
}
grep -q "'susukino-neon-corner'" tools/make_prefabs.py && grep -q "'susukino-karaoke_0_0'" tools/roomgen.py \
    && grep -q "'susukino-neon-corner_0_0'" tools/roomgen.py && grep -q "'susukino-karaoke':" tools/generate_houses.py \
    && grep -q 'WET_ASPHALT' tools/generate_sapporo.py && grep -q "room\['tramways'\]" tools/generate_sapporo.py \
    && grep -q 'def ramen_stall' tools/generate_sapporo_art.py && grep -q 'def wet_asphalt' tools/generate_sapporo_art.py \
    && grep -q "'Susukino crossing'" tools/blog_to_npc.py && grep -q "'susukino'" tools/districts.py \
    && grep -q 'ramen: ' src/Shop.js && grep -q 'susukino-ramen-stall' src/utils/Interactions.js \
    || { echo 'sapporo4_apply: the stage 4 source files are not in this checkout'; exit 1; }

step 'art and prefabs'
"$PIL_PY" tools/generate_sapporo_art.py | grep -E 'susukino-ramen-stall|autotile'
python3 tools/make_prefabs.py | tail -1

step 'the town, then the karaoke bar and the neon corner'
python3 tools/generate_sapporo.py
python3 tools/generate_houses.py --shops Sapporo | grep -v '^$' | grep -E '^(built|skipped|not)'
python3 tools/generate_houses.py --lobbies Sapporo | grep -v '^$' | grep -E '^(built|skipped|not)'
python3 tools/generate_sapporo.py >/dev/null      # a rebuild keeps every door the others wired

step 'devhouse.world: the slot grows northward (south edge and columns stay), clear of every other map'
python3 - <<'PY'
import json
path = '../devhouse.world'
world = json.load(open(path))
room = json.load(open('config.json'))['rooms']['Sapporo']
me = next(m for m in world['maps'] if m['fileName'].endswith('/sapporo.tmj'))
south = me['y'] + me['height']
me['width'], me['height'] = room['worldWidth'], room['worldHeight']
me['y'] = south - me['height']
for m in world['maps']:
    if m is me:
        continue
    apart = (me['x'] + me['width'] <= m['x'] or m['x'] + m['width'] <= me['x']
             or me['y'] + me['height'] <= m['y'] or m['y'] + m['height'] <= me['y'])
    assert apart, f"Sapporo would overlap {m['fileName']} in devhouse.world - move it"
text = json.dumps(world, indent=2)
if open(path).read() != text:
    open(path, 'w').write(text)
print('devhouse.world:', me)
PY
python3 tools/districts.py | tail -1

step 'Tiled maps: Sapporo and its shops and lobbies'
AFTER=$(owned)
for want in ShopSapporo1 ShopSapporo2 ShopSapporo3 ShopSapporo4 LobbySapporo1 LobbySapporo2 LobbySapporo3; do
    case " $AFTER " in *" $want "*) ;; *) echo "sapporo4_apply: $want was not built (have: $AFTER)"; exit 1;; esac
done
[ "$(echo $AFTER | wc -w | tr -d ' ')" = 7 ] || { echo "sapporo4_apply: expected seven interiors, got: $AFTER"; exit 1; }
# shellcheck disable=SC2086
python3 tools/config_to_tiled.py Sapporo $AFTER | tail -1

step 'world map (the room grew)'
"$PIL_PY" tools/make_worldmap.py | tail -1

step 'lint'
# shellcheck disable=SC2086
for room in Sapporo $AFTER; do
    out=$(node tools/play.js lint "$room" | head -1); echo "$out"
    case "$out" in *' 0 errors'*) ;; *) echo "sapporo4_apply: lint errors in $room"; exit 1;; esac
done

step 'distinctness: not worse than the baseline, then record it'
python3 tools/check_distinct.py | grep -E '^(city|target|Sapporo|no city)' || { echo 'sapporo4_apply: a city is worse than the baseline'; exit 1; }
python3 tools/check_distinct.py >/dev/null || { echo 'sapporo4_apply: a city is worse than the baseline'; exit 1; }
python3 tools/check_distinct.py --update | tail -1

step 'the five gates and the blog rehearsal'
node tools/test_game.js | tail -1
python3 tools/test_blog_to_npc.py 2>&1 | tail -1
node tools/play.js check | tail -1
GEN=$("$PIL_PY" tools/check_generators.py) || { echo "$GEN" | grep -v '^ok'; echo 'sapporo4_apply: check_generators failed'; exit 1; }
echo "check_generators: $(echo "$GEN" | grep -c '^ok') ok, $(echo "$GEN" | grep -c '^skip' || true) skipped"
python3 tools/sync_cities.py --check | tail -1
python3 tools/rehearse_blog.py 2>&1 | grep 'rehearsal' | tail -1
echo
echo 'sapporo4_apply: done - Sapporo stage 4 (Susukino and the streetcar) is built, all gates pass'
