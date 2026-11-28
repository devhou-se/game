#!/usr/bin/env python3
"""blog_to_npc.py — the blog → game pipeline.

A new devhou.se blog post moves its author's NPC somewhere in the game world
and gives them fresh dialogue, both derived from the post's content by Claude
(Sonnet). The result is written as dated NPC states in config.json (see
src/utils/NpcStates.js): the author appears at the chosen spot with the new
dialogue from the post's date, and disappears from wherever they were before.
Time travel (the in-game date picker) replays history faithfully.

If the post embeds a photo, the first one is imported as a 160×144 pixel-art
print (tools/post_photos.py) and the dated state carries "photo": <post_id>,
which the dialogue box hangs in a frame next to the author. Photo import is
best-effort — a failed photo never blocks the placement.

The dialogue can also be spoken: when ELEVENLABS_API_KEY and a voice id for
the author (ELEVENLABS_VOICE_<NPC>, e.g. ELEVENLABS_VOICE_BAILEY) are set,
each line is sent to ElevenLabs text-to-speech (tools/post_voice.py — see its
docstring for every env var), saved to assets/voice/<voice id>/<line>.mp3,
and the dated state carries "voice": <voice id>, which the dialogue box plays
line by line. The LLM also says whether the post reads as drunk; a drunk post
is recorded as "drunk": true and spoken in ELEVENLABS_VOICE_<NPC>_DRUNK when
that optional second voice is set. Voice is best-effort too — unconfigured or
failing, it logs a line and the placement lands silent.
Clip directories that no state references any more are deleted after each
config write, so whoever runs this must commit gamev2/assets/voice (additions
AND deletions) together with config.json — a recorded "voice" whose clips were
not deployed 404s on every line.

Two posts by the same author on the same day share one dated state (states
are keyed by date): the later post's spot wins and its lines are appended to
the earlier post's, capped at MAX_DAY_LINES (oldest dropped first) — see
merge_same_day. The state records which post each run of lines came from as
"posts", so a re-run of a post replaces its own lines instead of stacking on
top of itself or wiping the other post's. Each entry also keeps the post's
"title", and its "url" when the payload carries one, so the game can caption
the lines with the post they came from (DialogueManager) — [{"id", "lines",
"title", "url"}].

Where an author can be put (find_spots): every landmark in LANDMARKS, in the
outdoor rooms. A landmark that belongs to one town names its rooms, so a
sprite reused elsewhere does not carry the name along. Indoor rooms are
opt-in: a station room offers only the landmarks flagged "indoors" (today
just its platform, and the model is told to pick that only for a post about
the station or the train ride), and konbini / izakaya interiors are never
offered.

Districts (config.json "districts", written by tools/districts.py; issue
#219): every named area of a town is offered too, as "Room · Name (area)"
with its one-line description, and each named spot says which district it
is in — so a post that names an area and no landmark ("we stayed in
Asakusa") still lands there. An area's cell is an ordinary, free, reachable
one inside its bounds, nearest its `stand` cell: never a road, a stair, a
door, the cell in front of one, or a seam (area_cell).

Run from gamev2/ (normally by the www-jp game-npc-pipeline workflow; the unit
checks are `python3 tools/test_blog_to_npc.py`):

  python3 tools/blog_to_npc.py --payload post.json [--dry-run] [--mock]
  python3 tools/blog_to_npc.py --voice-backfill [--dry-run]
  python3 tools/blog_to_npc.py --backfill-posts posts.json [--dry-run]
  python3 tools/blog_to_npc.py --rehome Julia 2025-11-12 "Market · the vending machines" [--dry-run]

--voice-backfill makes no LLM call and places nobody: it speaks every existing
dated state that has dialogue but no voice (a state with "drunk": true gets
the drunk voice), so history placed before voices existed can be voiced once
the ElevenLabs env is configured. With --dry-run it only reports the lines and
characters it would send, which is the number ElevenLabs bills on.

--backfill-posts makes no LLM call and places nobody either: it fills in the
post title and url on states that were placed before those were recorded.
posts.json is a list of {"id", "title", "url"} (optionally "author" and
"date" too — see backfill_posts for how a state is matched to its post).

--rehome moves a placement that already exists to another spot (issue #121:
history placed on a station platform, before the rule above, for a post that
is not about the station). No LLM call: the day's dialogue, photo, voice and
post captions go along unchanged — see rehome. Repeat the flag to move several.

post.json is the blog payload: {"post_id", "title", "author", "date",
"content"} and optionally "url" (the post's page; recorded when present) —
author is the GitHub login. Needs ANTHROPIC_API_KEY unless --mock (canned
LLM response, for testing the placement plumbing: the first spot, or the
district the post names — named_area). With --mock a payload may
steer the canned response with "mock": {"spot", "dialogue", "drunk"} (any of
them), which is how tools/rehearse_blog.py — the dress rehearsal of this
whole path, in a scratch copy of config.json — sends each post to the
landmark it is about. "mock" is ignored without --mock.

The post's day (post_date): "date" is the moment the post was published, in
UTC as GitHub gives it. A trip with "utcOffset" (hours; devhouse 3 has 9,
Japan) dates its posts by the clock where the group is, so a post written at
8 in the morning in Sapporo is that day's and not the day before's. A trip
without one (devhouse 2) keeps the UTC date its history was written with.

Cross-room moves rely on resolveNpc semantics: an NPC definition whose base
has "present": false stays hidden until a dated state sets present true, so
authors can hop between rooms with one hidden base def per visited room.

Trips (config.json "trips", src/utils/Trips.js): the game only applies the
states dated inside the trip — and the stay — that the game date belongs to,
and a base NPC marked "trip" / "stay" stands there only on those dates. So
before an author's first post of a trip they are at the trip's base spot,
that post moves them exactly as above, and when the group moves base
everyone is at the new base until they post from it. Nothing here needs to
know which trip a post is from; trip_window / resolve_pos mirror the game's
rule only so a new arrival is not put on a cell somebody is standing on.
"""
import argparse
import datetime
import json
import os
import re
import sys

from post_photos import import_post_photo, prune_photos
from post_voice import prune_voices, voice_dialogue

# GitHub login -> NPC name (must exist in config, or be creatable from
# <name>_front/_back/_side sprites)
AUTHOR_NPCS = {
    'baely': 'Bailey',
    'damiante': 'Damian',
    'dbut2': 'Dylan',
    'jughents': 'Julia',
    # Devhouse 3 (issue #117): these three have sprites and base NPCs, but
    # their blog logins are not known yet. REPLACE each '<... github login>'
    # key with the author's GitHub login, lower-case — e.g. 'octocat': 'Khoi'.
    # Until then the key can never match a post (see is_login) and their posts
    # are skipped with a warning that names the login to put here.
    '<khoi github login>': 'Khoi',
    '<sam github login>': 'Sam',
    '<xander github login>': 'Xander',
}


def is_login(key):
    """Could `key` be a GitHub login (as process_post sees one: lower-cased)?
    Letters, digits, single inner hyphens, underscores (Enterprise Managed
    User logins: 'name_shortcode') and an app's '[bot]' suffix — so a
    placeholder key, which has spaces and angle brackets, never is one."""
    return bool(re.fullmatch(r'[a-z0-9](?:[a-z0-9_]|-(?=[a-z0-9_])){0,38}(?:\[bot\])?', key))


def npc_for_author(author, authors=None):
    """NPC name for a blog author's GitHub login (any case), or None. Only
    real logins are looked up, so a placeholder key is never an author."""
    author = (author or '').strip().lower()
    return (AUTHOR_NPCS if authors is None else authors).get(author) if is_login(author) else None


def awaiting_login(authors=None):
    """NPC names whose AUTHOR_NPCS entry is still a placeholder."""
    authors = AUTHOR_NPCS if authors is None else authors
    return sorted(npc for key, npc in authors.items() if not is_login(key))


def unmapped_author_warning(post_id, author, authors=None):
    """The line printed when a post is skipped because nobody maps its
    author to an NPC — it has to say what to change, and where."""
    waiting = awaiting_login(authors)
    who = f"'{author}': '<NPC name>'" if author else "the author's GitHub login"
    return (f'WARNING: #{post_id}: blog author {author!r} is not mapped to an NPC — post skipped. '
            f'Add {who} to AUTHOR_NPCS in gamev2/tools/blog_to_npc.py'
            + (f' (still waiting for a login: {", ".join(waiting)})' if waiting else '') + '.')

# landmark tile-key prefix -> spot label offered to the model:
#   (prefix, label[, stand][, options])
# `stand` is the cell to stand on, relative to the matching tile — the first
# one in the room whose stand cell is free, else the first (see find_spots).
# options:
#   'rooms': (room keys)  the label names one place, so only these rooms offer
#                         it — other rooms built from the same sprites do not
#   'indoors': True       offered inside station rooms, and only there. Without
#                         it a landmark is matched in outdoor rooms only, so an
#                         interior is never picked up by a prop it happens to
#                         contain (see find_spots)
LANDMARKS = [
    # the hall's tile cell is its top-left corner, under the roof's eaves (the
    # roof is 5x6 on Tops and hides anyone behind it) — stand below the steps
    ('shrine-building', 'the shrine', (1, 6)),
    ('torii-red', 'the torii gate'),
    ('red-pagoda', 'the pagoda'),
    ('fox-statue', 'the fox statues', (0, 2)),   # 1x2, only the base collides: stand in front, not on its head
    ('pond-autotile_corner-nw', 'the pond'),
    # 3x4, its tile cell the top-left corner and its door in the middle of the
    # south face — stand on the pavement beside the door, not behind the store
    # (in front of the door is where shoppers step out, #184)
    ('seven-eleven', 'the 7-Eleven', (0, 4)),
    ('blue-bell', 'the temple bell'),
    # the canopy's tile cell is its top-left corner; the trunk is under its
    # middle, two rows down — stand on the ground in front of the trunk (#183)
    ('sakura-large-top', 'the sakura trees', (1, 3)),
    ('white-vending-machine-top', 'the vending machines'),
    # Named landmarks. These are single sprites many cells tall, whose tile
    # cell is their top-left corner (the tip of a tower) — so each carries the
    # cell, relative to that corner, where someone visiting it would stand:
    # on the ground at its foot, clear of doorways and archways.
    # Tokyo's districts (issue #219): the things a post about Asakusa or the
    # palace names, which the generic rows above call "the shrine" / "the pond"
    ('castle-stairs', 'Senso-ji temple', (0, 1), {'rooms': ('Market',)}),          # the foot of the main hall's steps, at their west end
    ('red-small-pagoda-top', 'the temple gate', (5, 3), {'rooms': ('Market',)}),   # the approach, just south of the gate building
    ('building-tier-red', 'the izakaya', (0, 2), {'rooms': ('Market',)}),          # the pavement west of its door (7,37), not in front of it
    ('blue-wall-gate', 'the Imperial Palace gate', (-1, 6), {'rooms': ('Tokyo',)}),   # below the gate's stone steps, west of the path
    ('moat-south', 'the palace moat', (10, 2), {'rooms': ('Tokyo',)}),             # the outer bank, south of the water
    ('tokyo-tower_', 'Tokyo Tower', (9, 14)),          # beside the east leg
    ('tokyo-station_', 'Tokyo Station', (24, 9)),      # the forecourt, east of the door
    ('tsutenkaku_', 'Tsutenkaku Tower', (5, 14)),      # the plaza in front of it
    ('dotonbori-arch_', 'the Dotonbori arch', (0, 6)),  # through the arch, on the west pavement clear of the road and its signal (#106)
    ('dotonbori-wheel_', 'the Dotonbori ferris wheel', (6, 12)),   # the canal bank below it
    ('discount-store_', 'the Don Takote discount store', (3, 8)),  # beside its doors (in front is where shoppers step out, #91)
    # Hokkaido (issue #43)
    ('sapporo-clock-tower_', 'the Sapporo Clock Tower', (2, 8)),   # the pavement at its porch
    ('sapporo-tv-tower_', 'the Sapporo TV Tower', (3, 13)),        # in front of the entrance
    # Odori Park (issue #219, stage 2). The park itself is the hot-drinks tent's
    # (there is one): its visitor stands on the plaza beside the fountain, on
    # the path down the middle (issue #119). Then what is in it, each with the
    # cell someone looking at it stands on - in front, never on its footprint
    ('snowfest-stall-drinks_', 'Odori Park', (-1, 4), {'rooms': ('Sapporo',)}),
    ('snow-sculpture-castle_', 'the snow castle', (2, 4), {'rooms': ('Sapporo',)}),        # the court, at the foot of its steps
    ('snow-sculpture-tanuki_', 'the snow tanuki', (0, 3), {'rooms': ('Sapporo',)}),        # the path in front of it
    ('snow-sculpture-bear_', 'the snow bear', (1, 2), {'rooms': ('Sapporo',)}),            # the path in front of it
    ('snowfest-stall-corn_', 'the snow festival stalls', (3, 3), {'rooms': ('Sapporo',)}),   # the path, beside the corn tent's counter
    ('odori-fountain_', 'the Odori fountain', (1, 3), {'rooms': ('Sapporo',)}),            # the plaza, south of the basin
    # Tanukikoji, the covered arcade (issue #219, stage 3): each stands on the arcade street, beside a door, never in front of one
    ('tanukikoji-gate_', 'Tanukikoji arcade', (0, 4), {'rooms': ('Sapporo',)}),            # inside the gate, at its west post
    ('tanukikoji-shop-crab_', 'the crab shop', (2, 4), {'rooms': ('Sapporo',)}),           # under the crab, east of the door
    ('tanukikoji-shop-souvenir_', 'the souvenir shop', (0, 4), {'rooms': ('Sapporo',)}),   # at the window, west of the door
    # Susukino (issue #219, stage 4): each stands on the tram street's north side, beside a door or the gate's
    # mouth, never in front of one. Sapporo's `ramen alley` is its own row, and Asahikawa's is its own below
    ('susukino-neon-corner_', 'Susukino crossing', (3, 7), {'rooms': ('Sapporo',)}),       # under the fox board, east of the door
    ('susukino-ramen-gate_', 'ramen alley', (-2, 3), {'rooms': ('Sapporo',)}),             # on the street west of the gate: a wanderer (two cells) never reaches its mouth
    ('bus-stop_', 'the streetcar stop', (-1, -1), {'rooms': ('Sapporo',)}),                # on the platform, beside the stop sign
    # Asahikawa (issue #219, stage B): the town's own art
    ('asahikawa-station-front_', 'Asahikawa Station', (1, 5), {'rooms': ('Asahikawa',)}),   # Heiwa-dori, west of the hall's doors
    ('asahibashi-deck_', 'the bridge over the frozen river', (1, 0), {'rooms': ('Asahikawa',)}),    # the deck's north end, in the riverbank district
    ('asahikawa-ramen-gate_', 'ramen alley', (3, 3), {'rooms': ('Asahikawa',)}),   # on the alley, east of the gate: not in front of a ramen door
    ('zoo-gate_', 'the Asahiyama Zoo gate', (2, 4), {'rooms': ('Asahikawa',)}),   # the snow in front of the porch
    # Sendai (issue #66). Each stands its visitor in the open, in front
    ('sendai-masamune_', 'the Aoba Castle ruins', (3, 4), {'rooms': ('Sendai',)}),   # the terrace, beside the statue's plinth
    ('sendai-zuihoden_', 'Zuihoden', (2, 6), {'rooms': ('Sendai',)}),        # the landing at the head of the steps
    ('sendai-pub_', 'the HUB pub', (3, 5), {'rooms': ('Sendai',)}),          # the pavement beside its door
    ('sendai-kiln_', 'the Nikka distillery', (3, 6), {'rooms': ('Sendai',)}),   # the lane, beside the kiln house's door
    ('matsushima-ferry_', 'Matsushima bay', (-2, -1), {'rooms': ('Sendai',)}),   # the promenade, by the moored boat
    # Fukuoka (issue #67)
    ('fukuoka-tower_', 'Fukuoka Tower', (0, 12), {'rooms': ('Fukuoka',)}),   # the plaza at its foot, beside the entrance
    ('yatai-ramen', 'the yatai stalls', (1, 3), {'rooms': ('Fukuoka',)}),   # on the promenade, at a stall's stools
    ('hakata-yamakasa_', 'Kushida shrine', (0, 4), {'rooms': ('Fukuoka',)}),   # in front of the Yamakasa float
    ('canal-city_', 'Canal City', (2, 6), {'rooms': ('Fukuoka',)}),   # the plaza, beside the doors
    ('dazaifu-hall_', 'Dazaifu Tenmangu', (1, 5), {'rooms': ('Fukuoka',)}),   # the court below the steps, off the bridge's axis
    ('building-entrance-1', 'Hakata Station', (3, 1), {'rooms': ('Fukuoka',)}),   # the forecourt, east of the door
    # Hokuriku (issue #68): Kanazawa, and Shirakawa-go and Toyama, walked to from it
    ('kanazawa-ishikawa-gate_', "Kanazawa Castle's Ishikawa gate", (6, 6), {'rooms': ('Kanazawa',)}),   # the garden path below the gate, far enough off that a wander never ends in the gateway
    ('kanazawa-kotoji_', 'Kenrokuen garden', (-1, 1), {'rooms': ('Kanazawa',)}),   # the pond's bank, beside the Kotoji lantern
    ('kanazawa-chaya-a_', 'the Higashi Chaya teahouse row', (2, 4), {'rooms': ('Kanazawa',)}),   # the paved lane, beside a teahouse door
    ('kanazawa-whisky-bar_', 'the whisky bar', (2, 4), {'rooms': ('Kanazawa',)}),   # the pavement beside its door
    ('sendai-gate_', 'the Nagamachi samurai lane', (-1, -2), {'rooms': ('Kanazawa',)}),   # the earth lane, across the canal from the gate
    ('shirakawa-bridge_', 'the suspension bridge', (10, 2), {'rooms': ('Shirakawago',)}),   # the lane at the village bridgehead: far enough off that a wander never ends on the one-cell deck
    ('shirakawa-lookout_', 'the Shirakawa-go viewpoint', (1, -1), {'rooms': ('Shirakawago',)}),   # the terrace, at the rail
    ('shirakawa-gassho_', 'the gassho farmhouses', (3, 5), {'rooms': ('Shirakawago',)}),   # the lane, beside the big house's door
    ('toyama-glass-museum_', 'the Glass Art Museum', (1, 6), {'rooms': ('Toyama',)}),   # the pavement beside its doors
    ('toyama-tram-stop_', 'the tram stop', (3, 1), {'rooms': ('Toyama',)}),   # beside the shelter
    ('toyama-ramen_', 'the black ramen shop', (2, 4), {'rooms': ('Toyama',)}),   # the old street, beside its door
    ('toyama-port-tower_', 'the port observation tower', (-1, 6), {'rooms': ('Toyama',)}),   # the quay at its foot, west of the entrance
    # Kansai (issue #255): Himeji, walked to from Osaka
    ('himeji-keep_', 'Himeji Castle', (4, 8), {'rooms': ('Himeji',)}),   # the terrace in front of the keep's middle, where the camera looks up at it
    ('himeji-kokoen-gate_', 'Koko-en garden', (1, 5), {'rooms': ('Himeji',)}),   # the garden's path, inside the gate
    ('okayama-keep_', 'Okayama Castle', (2, 7), {'rooms': ('Okayama',)}),         # (20, 9): in front of the keep, off the steps' columns
    ('okayama-crane_', 'Korakuen garden', (-1, 1), {'rooms': ('Okayama',)}),      # (27, 31): the lawn beside the first crane
    ('okayama-momotaro_', 'the Momotaro statue', (0, 3), {'rooms': ('Okayama',)}),    # (8, 20): the plaza in front of him
    ('okayama-bizen-stall_', 'the Bizen-ware stall', (1, 3), {'rooms': ('Okayama',)}),  # (16, 18): the pavement at its counter
    ('nara-daibutsuden_', 'the Great Buddha Hall', (4, 8), {'rooms': ('Nara',)}),   # (35, 10): the court in front of the hall, off the axis
    ('nara-nandaimon_', 'the Nandaimon gate', (1, 4), {'rooms': ('Nara',)}),       # (35, 16): the plaza below its west post, off the gateway
    ('nara-senbei-stall_', 'the deer cracker stall', (0, 2), {'rooms': ('Nara',)}),   # (41, 18): the plaza at its counter
    ('nara-deer-stag_', 'the deer of Nara Park', (1, 0), {'rooms': ('Nara',)}),    # (13, 29): the lawn beside the first stag
    ('shrine-building', 'Kasuga Taisha', (2, 6), {'rooms': ('Nara',)}),            # (45, 32): the approach, east of the door's column
    ('karuizawa-fingerpost_', 'the road from Tokyo', (-1, 1), {'rooms': ('Karuizawa',)}),   # the verge beside its foot, clear of the road and the gate's landing cells
    ('karuizawa-falls_', 'Shiraito Falls', (1, 5), {'rooms': ('Karuizawa',)}),       # (13, 8): the bank, at the pool's south-west corner
    ('karuizawa-corn-stall_', 'the corn stall', (2, 2), {'rooms': ('Karuizawa',)}),  # (21, 8): at the east end of the counter
    # Inside a station (issue #73): the west end of the platform, by the
    # vending machine — clear of the train doors, the arrival cell and the exit
    ('white-vending-machine-top', 'the platform', {'indoors': True}),
]

MODEL = 'claude-sonnet-5'
MAX_DIALOGUE_LINES = 4
MAX_LINE_CHARS = 160
# an author's lines for one day, when several posts share a date
MAX_DAY_LINES = 2 * MAX_DIALOGUE_LINES

# claude-sonnet-5 list price, USD per million tokens (standard, not the intro
# rate — keeps the per-post projection conservative once intro pricing ends)
PRICE_IN_PER_M = 3.00
PRICE_OUT_PER_M = 15.00


def load_config():
    return json.load(open('config.json'))


def save_config(cfg):
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))


def overworld_rooms(cfg):
    """The rooms the pipeline keeps an author's whereabouts in: everything but
    the `interior` rooms (konbini, izakaya, the airports) and any room that
    says `"blog": false` (issue #218: the home city and the airport's rail
    stop are on no trip, so nothing there is ever offered). Station rooms are
    in here — they hold placements — but are indoors as far as spots go
    (is_indoors)."""
    return {k: r for k, r in cfg['rooms'].items() if not r.get('interior') and r.get('blog') is not False}


def is_indoors(cfg, room_key):
    """An interior, or a station room (those carry no `interior` flag: they
    are listed under config.stations)."""
    return bool(cfg['rooms'][room_key].get('interior')) or room_key in cfg.get('stations', {})


def landmark_fields(entry):
    """(prefix, label, (dx, dy), options) of a LANDMARKS entry."""
    prefix, label, *rest = entry
    stand = next((r for r in rest if isinstance(r, tuple)), (0, 0))
    options = next((r for r in rest if isinstance(r, dict)), {})
    return prefix, label, stand, options


def landmark_applies(cfg, room_key, options):
    """Whether a landmark with these options may be offered in room_key."""
    if 'rooms' in options and room_key not in options['rooms']:
        return False
    return bool(options.get('indoors')) == is_indoors(cfg, room_key)


def decode_tiles(cfg, layer):
    pal = cfg.get('tilePalette')
    out = {}
    for xy, v in (layer.get('tiles') or {}).items():
        out[xy] = pal[v] if isinstance(v, int) else v
    return out


def find_spots(cfg):
    """Every landmark that applies to its room -> {'Room · label': (room, x, y)}.

    Outdoor rooms offer the ordinary landmarks. A station room offers only
    landmarks flagged 'indoors', and `interior` rooms (konbini, izakaya) offer
    nothing — see landmark_applies.

    A landmark is anchored on its first matching tile. One with a `stand`
    offset moves on to the first tile whose stand cell is in the open: free
    to stand on (walkable_near returns it unchanged) and with no building
    drawn across it. So a tree that stands against a building does not send
    its visitor round the back (issue #189: Market's first sakura has the
    7-Eleven where its visitor would stand, its second the roof of a
    high-rise); with no such tile the first match stays."""
    spots, settled = {}, set()
    for room_key, room in overworld_rooms(cfg).items():
        behind = None   # the room's cells behind a sprite, worked out when first asked for
        landmarks = [(prefix, label, stand)
                     for prefix, label, stand, options in map(landmark_fields, LANDMARKS)
                     if landmark_applies(cfg, room_key, options)]
        for layer in room.get('layers', []):
            tiles = decode_tiles(cfg, layer)
            for xy, key in tiles.items():
                for prefix, label, (dx, dy) in landmarks:
                    spot_id = f'{room_key} · {label}'
                    if not key.startswith(prefix) or spot_id in settled:
                        continue
                    x, y = map(int, xy.split(','))
                    cell = (x + dx, y + dy)
                    if (dx, dy) != (0, 0) and behind is None:
                        behind = overhead_cells(cfg, room_key, standing=True)
                    # no stand cell to judge, or this one is in the open
                    if (dx, dy) == (0, 0) or (cell not in behind and walkable_near(cfg, room_key, *cell) == cell):
                        settled.add(spot_id)
                    elif spot_id in spots:
                        continue
                    spots[spot_id] = (room_key, *cell)
    return spots


def room_cells(cfg, room_key):
    """(cells_w, cells_h, floored, blocked) for a room — the sets hold 'x,y'
    keys: cells with a Floor tile, and cells on a collision layer."""
    room = cfg['rooms'][room_key]
    gs = cfg['game']['gridSize']
    cells_w = round(room.get('worldWidth', cfg['game']['worldWidth']) / gs)
    cells_h = round(room.get('worldHeight', cfg['game']['worldHeight']) / gs)
    blocked, floored = set(), set()
    for layer in room.get('layers', []):
        tiles = decode_tiles(cfg, layer)
        target = blocked if layer.get('collision') else (floored if layer['name'] == 'Floor' else None)
        if target is not None:
            target.update(tiles)
    return cells_w, cells_h, floored, blocked


def overhead_cells(cfg, room_key, standing=False):
    """(x, y) of every cell of a room that an overhead sprite is drawn across:
    a canopy, roof, gate beam or lamp head on a layer with z >= 7 (Tops), which
    the game draws over whoever stands there (RoomManager's overheadBias), so
    an author placed on one is hidden behind it (issue #183).

    With `standing`, also every cell of a sprite that stands on the ground
    (z >= 2: a building, a statue). Those are drawn over whoever is behind
    them too — the roof rows of a tall building carry no collider — and
    find_spots keeps a landmark's standing cell off them (issue #189).

    A sprite's size in cells comes from its spriteMetadata anchor, which is
    the centre of its top-left cell (anchorX 0.1667 = three cells wide)."""
    meta = cfg.get('spriteMetadata', {})
    cells = set()
    for layer in cfg['rooms'][room_key].get('layers', []):
        if layer.get('z', 0) < (2 if standing else 7):
            continue
        for xy, key in decode_tiles(cfg, layer).items():
            x, y = map(int, xy.split(','))
            m = meta.get(key, {})
            w = max(1, round(0.5 / (m.get('anchorX') or 0.5)))
            h = max(1, round(0.5 / (m.get('anchorY') or 0.5)))
            cells.update((x + i, y + j) for i in range(w) for j in range(h))
    return cells


def city_districts(cfg, room_key):
    """The stitched city `room_key` is a district of -> [(room, x, y, w, h)] for
    every district of it, in config order, in cells from the union's top-left;
    None for a room that is in no city.

    The game merges the rooms listed in config `cities` into ONE walkable room
    at load (src/systems/CityStitcher.js): the seam transporters between them
    are dropped and you simply walk across. This is the only part of that
    stitch the pipeline needs — who sits where, and that a LATER listed room
    owns the cells it overlaps with an earlier one (its floor and colliders
    are the ones there). test_blog_to_npc.py pins the result, cell for cell,
    to what `node tools/play.js reach` gets from the stitcher itself."""
    for city in (cfg.get('cities') or {}).values():
        listed = city.get('rooms', [])
        if len(listed) < 2 or not any(m['room'] == room_key for m in listed):
            continue
        if any(m['room'] not in cfg['rooms'] for m in listed):
            continue                       # the game refuses to stitch this city too
        min_x, min_y = min(m['x'] for m in listed), min(m['y'] for m in listed)
        return [(m['room'], m['x'] - min_x, m['y'] - min_y) + room_cells(cfg, m['room'])[:2] for m in listed]
    return None


def city_reachable(cfg, districts):
    """{district: {(x, y)}} — the cells of each district (its own coordinates)
    a player can walk to in the stitched city: one flood over the merged
    grid, from every door into it (a transporter that does not lead to a
    sibling district) and from the spawn point if it is in the city.

    Flooded afresh on every call (tens of milliseconds), never cached: a
    caller may edit a district's layers or doors in place between calls."""
    members = {d[0] for d in districts}
    walkable = {}
    for room, ox, oy, w, h in districts:        # a later district overwrites the cells it shares
        _, _, floored, blocked = room_cells(cfg, room)
        for y in range(h):
            for x in range(w):
                xy = f'{x},{y}'
                walkable[(x + ox, y + oy)] = xy in floored and xy not in blocked
    todo = []
    for room, ox, oy, _, _ in districts:
        todo += [(t['gridX'] + ox, t['gridY'] + oy) for t in cfg['rooms'][room].get('transporters', [])
                 if t.get('targetRoom') not in members]
        player = cfg.get('player') or {}
        if player.get('startRoom') == room:
            todo.append((player['startX'] + ox, player['startY'] + oy))
    seen = set(todo)
    while todo:
        x, y = todo.pop()
        for cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if cell not in seen and walkable.get(cell):
                seen.add(cell)
                todo.append(cell)
    return {room: {(x - ox, y - oy) for x, y in seen if 0 <= x - ox < w and 0 <= y - oy < h}
            for room, ox, oy, w, h in districts}


def reachable_cells(cfg, room_key):
    """(x, y) of every cell the player can walk to from the room's ways in, or
    None for a room that has none to start from — callers then do not filter
    on reachability at all (test_spots fails an overworld room like that).

    A room on its own is entered by its transporters. A district of a
    stitched city (config `cities`: Tokyo, Market, Palace, Park) is
    also walked into from its neighbours, with no transporter involved, so it
    is flooded as part of the whole city (city_reachable) — a district whose
    only door is a konbini is not judged from that door alone, and one with
    no door at all (Tokyo) still gets its answer (issue #124)."""
    districts = city_districts(cfg, room_key)
    if districts:
        return city_reachable(cfg, districts)[room_key]
    cells_w, cells_h, floored, blocked = room_cells(cfg, room_key)
    todo = [(t['gridX'], t['gridY']) for t in cfg['rooms'][room_key].get('transporters', [])]
    if not todo:
        return None
    seen = set(todo)
    while todo:
        x, y = todo.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            key = f'{nx},{ny}'
            if ((nx, ny) not in seen and 0 <= nx < cells_w and 0 <= ny < cells_h
                    and key in floored and key not in blocked):
                seen.add((nx, ny))
                todo.append((nx, ny))
    return seen


def walk_region(cfg, room_key):
    """Every cell a player can walk to, in room_key's coordinates — for a
    district of a stitched city the whole city's (so cells of its neighbours
    lie outside the room's own bounds): where a walk that leaves the district
    and comes back may go. None for a room with no way in (reachable_cells)."""
    districts = city_districts(cfg, room_key)
    if not districts:
        return reachable_cells(cfg, room_key)
    ox, oy = next((d[1], d[2]) for d in districts if d[0] == room_key)
    by_room = city_reachable(cfg, districts)
    return {(x + dx - ox, y + dy - oy) for room, dx, dy, _, _ in districts for x, y in by_room[room]}


def walls_in(cell, free):
    """Would somebody standing on `cell` be in the way? `free` is the set of
    cells that can be walked on with everyone else where they are (it holds
    `cell`). An NPC is solid, so they are in the way when nobody could walk
    up to them, or when the cells around them stop being one walk: a lane
    one cell wide, the mouth of a dead end, the cell in front of a door —
    whatever lies beyond would be sealed off, people standing there
    included (issue #119: a post about ramen alley put its author in the
    middle of the alley, and nobody could reach the far end of it)."""
    x, y = cell
    around = [c for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if c in free]
    if not around:
        return True
    want, seen, todo = set(around[1:]), {cell, around[0]}, [around[0]]
    while todo and want:
        cx, cy = todo.pop()
        for c in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if c in free and c not in seen:
                seen.add(c)
                want.discard(c)
                todo.append(c)
    return bool(want)


def walkable_near(cfg, room_key, gx, gy, occupied=frozenset(), allowed=None, reach=12):
    """Nearest cell someone can stand on and be walked up to: floored,
    uncollided, not a transporter, not an occupied cell (the test of
    GameScene.findWalkableNear) and connected to one of the room's ways in —
    so a landmark standing in a fenced garden puts its visitor outside the
    fence, not in with it. In a district of a stitched city "connected" means
    walkable in the city as the game merges it (reachable_cells). `occupied`
    is (x,y) tuples already taken by other NPCs (resolved positions, not base
    defs — see occupied_cells).

    A cell under a canopy or roof (overhead_cells) is passed over, so nobody
    is stood where the tree hides them (issue #183), and so is a cell inside a
    sprite that stands on the ground (standing=True: the head of a statue or
    a vending machine, which only collide at the base). Only when no open
    cell is in range does one of those do — inside a sprite before under a
    roof.

    Nor a cell where they would be in the way (walls_in): everything that
    could be walked to before can be walked to with them standing there, and
    nobody already there — `occupied` — is left with no cell to be walked up
    to from.

    `allowed`, when given, is a further test a cell (x, y) must pass (a
    district's bounds and ground, area_cell), and `reach` how many rings of
    cells round (gx, gy) are searched (12: eleven cells away at most)."""
    cells_w, cells_h, floored, blocked = room_cells(cfg, room_key)
    portals = {f"{t['gridX']},{t['gridY']}" for t in cfg['rooms'][room_key].get('transporters', [])}
    reachable = reachable_cells(cfg, room_key)
    overhead = overhead_cells(cfg, room_key)
    behind = overhead_cells(cfg, room_key, standing=True)
    region = walk_region(cfg, room_key)
    free = None if region is None else region - set(occupied)

    def ok(x, y):
        key = f'{x},{y}'
        if not (0 <= x < cells_w and 0 <= y < cells_h and key in floored
                and key not in blocked and key not in portals and (x, y) not in occupied
                and (reachable is None or (x, y) in reachable)):
            return False
        if allowed is not None and not allowed((x, y)):
            return False
        if free is None:
            return True
        if walls_in((x, y), free):
            return False
        # a neighbour who could only be walked up to from this cell
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n in occupied and not any(c in free and c != (x, y) for c in
                                         ((n[0] + 1, n[1]), (n[0] - 1, n[1]), (n[0], n[1] + 1), (n[0], n[1] - 1))):
                return False
        return True

    inside = covered = None
    for rad in range(0, reach):
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if max(abs(dx), abs(dy)) != rad:
                    continue
                cell = (gx + dx, gy + dy)
                if not ok(*cell):
                    continue
                if cell not in behind:
                    return cell
                if cell not in overhead:
                    inside = inside or cell
                covered = covered or cell
    return inside or covered


# what marks a district's id apart from a landmark's: "Sapporo · Odori Park" is
# the spot under the park's lanterns, "Sapporo · Odori Park (area)" the park
AREA = ' (area)'
# ground nobody is stood on for an area: carriageway, rails, a zebra crossing
NOT_PLAIN = ('road', 'toyama-tram-rail', 'tram-rail', 'train-track', 'crossing-')


def districts_of(cfg, room_key):
    """The districts of a room, from config `districts` (tools/districts.py
    writes it): [{key, name, description, bounds, stand, spots}]."""
    return (cfg.get('districts') or {}).get(room_key) or []


def area_id(room_key, district):
    return f"{room_key} · {district['name']}{AREA}"


def find_areas(cfg):
    """Every district that can be offered -> {'Room · Name (area)': (room,
    district)}. Outdoor rooms only: a station or an interior has none."""
    return {area_id(room_key, d): (room_key, d)
            for room_key in overworld_rooms(cfg) if not is_indoors(cfg, room_key)
            for d in districts_of(cfg, room_key)}


def district_at(cfg, room_key, x, y):
    """The district of room_key whose bounds hold cell (x, y), or None."""
    for d in districts_of(cfg, room_key):
        x0, y0, x1, y1 = d['bounds']
        if x0 <= x <= x1 and y0 <= y <= y1:
            return d
    return None


def plain_cells(cfg, room_key):
    """(x, y) of the room's ordinary ground: a Floor cell that is not road or
    rail, with no stair or crossing laid over it and no water under it (a
    walkable cell on the Water layer is the deck of a bridge or a pier) —
    Trips.plain in the game, plus the carriageway."""
    floor, spoiled = set(), set()
    for layer in cfg['rooms'][room_key].get('layers', []):
        if layer.get('collision'):
            continue
        for xy, key in decode_tiles(cfg, layer).items():
            cell = tuple(map(int, xy.split(',')))
            if layer['name'] == 'Water' or 'stairs' in key or key.startswith(NOT_PLAIN):
                spoiled.add(cell)
            elif layer['name'] == 'Floor':
                floor.add(cell)
    return floor - spoiled


def doorway_cells(cfg, room_key):
    """(x, y) of every transporter of the room and the four cells round it:
    a door, the cell in front of it where people step out, and a seam into a
    neighbouring district with the cell beside it."""
    cells = set()
    for t in cfg['rooms'][room_key].get('transporters', []):
        x, y = t['gridX'], t['gridY']
        cells.update(((x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return cells


def area_cell(cfg, room_key, district, occupied=frozenset()):
    """Where somebody placed in a district stands: the free cell nearest its
    `stand` cell (the middle of its bounds without one) that is inside the
    bounds, on ordinary ground (plain_cells), in the open (not behind or
    under a sprite), not a doorway or the cell in front of one, not on the
    room's edge (the row or column a stitched district shares with its
    neighbour) — and everything walkable_near asks of any cell: reachable,
    nobody on it, nobody walled in. Only when every such cell is taken does
    a road cell do (never a stair, a bridge deck or the track). None when the
    district has no cell at all."""
    x0, y0, x1, y1 = district['bounds']
    cells_w, cells_h = room_cells(cfg, room_key)[:2]
    plain, doors = plain_cells(cfg, room_key), doorway_cells(cfg, room_key)
    behind = overhead_cells(cfg, room_key, standing=True)

    def allowed(cell):
        x, y = cell
        return (x0 <= x <= x1 and y0 <= y <= y1 and 0 < x < cells_w - 1 and 0 < y < cells_h - 1
                and cell in plain and cell not in doors and cell not in behind)

    def crowded(cell):
        # every ordinary cell is taken (a district that is mostly a road stub, on a day everybody
        # is there): the carriageway does, still inside the bounds and clear of doors and seams
        x, y = cell
        return (x0 <= x <= x1 and y0 <= y <= y1 and 0 < x < cells_w - 1 and 0 < y < cells_h - 1
                and cell not in doors and cell not in behind and cell not in wet)

    wet = {tuple(map(int, xy.split(','))) for layer in cfg['rooms'][room_key].get('layers', [])
           if not layer.get('collision') for xy, key in decode_tiles(cfg, layer).items()
           if layer['name'] == 'Water' or 'stairs' in key or key.startswith(('train-track', 'tram-rail'))}
    ax, ay = district.get('stand') or ((x0 + x1) // 2, (y0 + y1) // 2)
    reach = max(cells_w, cells_h)
    return (walkable_near(cfg, room_key, ax, ay, occupied, allowed=allowed, reach=reach)
            or walkable_near(cfg, room_key, ax, ay, occupied, allowed=crowded, reach=reach))


def all_spots(cfg):
    """Everything a post can be placed at -> {id: (room, x, y)}: the named
    spots (find_spots) and the districts (find_areas), a district by the cell
    it resolves to with nobody about. Place through stand_cell, which knows
    an area from a landmark."""
    spots = find_spots(cfg)
    for spot_id, (room_key, district) in find_areas(cfg).items():
        cell = area_cell(cfg, room_key, district)
        if cell is not None:
            spots[spot_id] = (room_key, *cell)
    return spots


def stand_cell(cfg, spot_id, spots, occupied=frozenset()):
    """(room, cell) for a spot id of all_spots with `occupied` cells taken —
    cell None when there is nowhere to stand. A landmark: the nearest free
    cell to its standing cell (walkable_near). A district: area_cell."""
    room_key, ax, ay = spots[spot_id]
    if spot_id.endswith(AREA):
        found = find_areas(cfg).get(spot_id)
        if found:
            return room_key, area_cell(cfg, room_key, found[1], occupied)
    return room_key, walkable_near(cfg, room_key, ax, ay, occupied)


def offer_lines(cfg, spot_ids):
    """The "Available spots" list as the placement model reads it: a named
    spot with the district it is in, then every district with its one-line
    description (issue #219: the label and description are what lets a post
    that names an area and no landmark be placed)."""
    spots, areas = find_spots(cfg), find_areas(cfg)
    lines = []
    for spot_id in spot_ids:
        if spot_id in areas:
            _, d = areas[spot_id]
            lines.append(f"- {spot_id}: {d['description']}")
        else:
            d = district_at(cfg, *spots[spot_id]) if spot_id in spots else None
            lines.append(f'- {spot_id}' + (f" (in {d['name']})" if d else ''))
    return '\n'.join(lines)


def named_area(post, spot_ids):
    """The district on offer that a post names in its title or text ("a day
    in Asakusa" -> 'Market · Asakusa (area)'), the longest name first, as a
    whole word; None when it names none. What --mock answers with when it is
    not steered: the real model reads the same names, with their descriptions."""
    text = f"{post.get('title') or ''}\n{post.get('content') or ''}"
    named = [(len(name), spot_id) for spot_id in spot_ids if spot_id.endswith(AREA)
             for name in [spot_id[:-len(AREA)].split(' · ', 1)[-1]]
             if re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', text)]
    return max(named)[1] if named else None


def generate(post, npc_name, spot_ids, mock=False, offers=None):
    """Claude Sonnet turns the post into ({spot, dialogue, drunk}, usage).
    usage is None for --mock, else the response.usage token counts.
    `offers` is the spot list as the model reads it (offer_lines: districts
    with their descriptions); without it, the bare ids."""
    if mock:
        canned = {'spot': named_area(post, spot_ids) or spot_ids[0], 'dialogue': [
            f"I just wrote about {post['title']}!",
            'Come read it on the blog.',
        ], 'drunk': False}
        steer = post.get('mock')
        if isinstance(steer, dict):
            canned.update({k: steer[k] for k in canned if k in steer})
        return canned, None

    import anthropic
    # generous retries: fresh/low-tier accounts have small per-minute limits
    client = anthropic.Anthropic(max_retries=5)

    schema = {
        'type': 'object',
        'properties': {
            'spot': {'type': 'string', 'enum': spot_ids},
            'dialogue': {'type': 'array', 'items': {'type': 'string'}},
            'drunk': {'type': 'boolean'},
        },
        'required': ['spot', 'dialogue', 'drunk'],
        'additionalProperties': False,
    }

    system = (
        'You turn devhou.se blog posts into game content for a cozy pixel-art '
        'game about a group of friends in Japan. Given a blog post, you pick '
        'where in the game world its author should be found, and write the '
        'short dialogue they say when the player walks up to them.\n\n'
        'Dialogue rules: first person, in the voice of the author riffing on '
        'their own post; 3-4 lines; each line under 140 characters; playful '
        'and specific to the post (mention real details from it); no markdown, '
        'no URLs, no @mentions. The last line should be a small sign-off or '
        'quip.\n\n'
        'Spot rules: choose the location that best matches the post\'s '
        'content or mood (e.g. food near the 7-Eleven, reflection near the '
        'shrine or pond). A spot named "the platform" is indoors, on the '
        'platform of that town\'s train station: choose one only when the '
        'post is mainly about that station or the train ride itself. For '
        'everything else, including a day that merely involved a train, '
        'choose an outdoor spot. A spot ending "(area)" is a whole district '
        'of a town, listed with what is there; a named spot says which '
        'district it is in. Prefer the named spot the post is about. Choose '
        'an area when the post names that district, or is about what its '
        'description says, and no named spot fits — never a spot in another '
        'town or district just because its name sounds close.\n\n'
        'Drunk rule: set drunk to true only when the post itself reads as if '
        'it was written drunk (slurred or rambling prose, typos played for '
        'laughs, the author saying so) — it picks the voice the dialogue is '
        'read aloud in. A sober post about drinking is false.'
    )

    user = (
        f"Author: {npc_name}\n"
        f"Post title: {post['title']}\n"
        f"Post date: {post['date']}\n\n"
        f"Post content:\n{post['content'][:8000]}\n\n"
        f"Available spots:\n" + (offers or '\n'.join(f'- {s}' for s in spot_ids))
    )

    # small max_tokens matters beyond cost: the rate limiter reserves
    # max_tokens against the per-minute output ceiling, and the JSON we
    # want is tiny. Thinking off for the same reason.
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            thinking={'type': 'disabled'},
            system=system,
            messages=[{'role': 'user', 'content': user}],
            output_config={'format': {'type': 'json_schema', 'schema': schema}},
        )
    except anthropic.RateLimitError as e:
        # A throughput 429 carries anthropic-ratelimit-* / retry-after headers
        # and is worth retrying. A 429 with NEITHER is a spend/usage cap or a
        # workspace restriction — retrying won't help; say so.
        hdrs = dict(e.response.headers)
        rl = {k: v for k, v in hdrs.items()
              if 'ratelimit' in k.lower() or k.lower() == 'retry-after'}
        if rl:
            print('  rate-limit headers:', json.dumps(rl))
            raise
        print('  no rate-limit headers on this 429 — this is a spend/usage cap '
              'or workspace restriction, not throughput.')
        print('  Check the Anthropic Console: Settings -> Limits (workspace '
              'spend limit) and Billing (usage limit). Topping up the credit '
              'balance does not raise a spend limit.')
        print(f'  request_id: {getattr(e, "request_id", None)}')
        raise SystemExit(2)
    text = next(b.text for b in response.content if b.type == 'text')
    return json.loads(text), response.usage


# a full stop after one of these is not the end of a sentence
ABBREVIATIONS = {'mr', 'mrs', 'ms', 'dr', 'prof', 'st', 'mt', 'vs', 'approx',
                 'e.g', 'i.e', 'a.m', 'p.m'}


def ends_sentence(line, i):
    """Whether the character at line[i] closes a sentence (and more text
    follows it, which the caller is about to cut off)."""
    ch = line[i]
    if ch in '。！？':
        return True
    if ch not in '.!?…' or line[i + 1] != ' ':
        return False
    word = line[:i].rsplit(' ', 1)[-1].lower().lstrip('("\'“‘')
    return not (ch == '.' and word in ABBREVIATIONS)


def trim_line(line, limit=MAX_LINE_CHARS):
    """One dialogue line, whitespace-normalised and at most `limit` characters
    — never cut mid-word. An over-long line is trimmed back to its last
    complete sentence when that keeps at least half of it; otherwise to the
    last whole word (or, for unspaced Japanese, the last 、 clause) with an
    ellipsis to show it trails off."""
    line = ' '.join(line.split())
    if len(line) <= limit:
        return line
    half = limit // 2
    for i in range(limit - 1, half - 1, -1):
        if ends_sentence(line, i):
            return line[:i + 1]
    head = line[:limit - 1]            # leave room for the ellipsis
    cut = head.rfind(' ')
    if cut < half:
        cut = head.rfind('、')
    if cut < half:
        cut = len(head)                # one unbroken run: nothing better to cut at
    return head[:cut].rstrip(' ,;:-–—、') + '…'


def clean_dialogue(lines):
    """The model's lines made safe for the dialogue box: blanks dropped, each
    trimmed to MAX_LINE_CHARS on a sentence/word boundary, at most
    MAX_DIALOGUE_LINES of them."""
    return [trim_line(line) for line in lines if line.strip()][:MAX_DIALOGUE_LINES]


def npc_in_room(room, name):
    return next((n for n in room.get('npcs', []) if n['name'].lower() == name.lower()), None)


TRIP_LEAD = 14   # days before its start a trip opens (Trips.LEAD in the game)


def trip_window(cfg, date):
    """What `date` can see — {'trip', 'stay', 'from'} or None with no trips
    (mirrors Trips.windowFor in the game): its trip is the latest one opened
    by then (a trip opens `lead` days, default TRIP_LEAD, before its start;
    the first trip, for a date before them all), its stay the latest one of
    that trip begun by then, and `from` the first day whose dated states
    still apply (the start of that stay, else of the trip). `early` is a
    lead-in day of a later trip: `from` is the day it opened and its base
    NPCs are not there yet."""
    iso = re.compile(r'\d{4}-\d{2}-\d{2}$')
    trips = sorted((t for t in cfg.get('trips') or []
                    if t.get('id') and iso.match(t.get('start') or '') and iso.match(t.get('end') or '')
                    and t['start'] <= t['end']), key=lambda t: t['start'])
    if not trips:
        return None
    def opens(t):
        lead = t.get('lead')
        lead = lead if isinstance(lead, int) and not isinstance(lead, bool) and lead >= 0 else TRIP_LEAD
        return (datetime.date.fromisoformat(t['start']) - datetime.timedelta(days=lead)).isoformat()
    trip = ([t for t in trips if opens(t) <= date] or trips[:1])[-1]
    stays = sorted((s for s in trip.get('stays') or [] if s.get('room') and iso.match(s.get('from') or '')),
                   key=lambda s: s['from'])
    stay = ([s for s in stays if s['from'] <= date] or stays[:1] or [None])[-1]
    if date < trip['start'] and trip is not trips[0]:
        return {'trip': trip, 'stay': stay, 'early': True, 'from': opens(trip)}
    return {'trip': trip, 'stay': stay, 'early': False,
            'from': stay['from'] if stay and stay['from'] > trip['start'] else trip['start']}


def is_day(text):
    """Is `text` a real calendar day written YYYY-MM-DD?"""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', text or ''):
        return False
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def post_date(cfg, post):
    """The day a post belongs to, 'YYYY-MM-DD' ('' or a short string when
    the payload has no usable date — the caller skips those).

    "date" is the moment of publishing; GitHub gives it in UTC
    ('2027-02-24T23:30:00Z'). When the trip that moment belongs to carries
    "utcOffset" (hours ahead of UTC where the group is), the day is the one
    on the clock there — 08:30 on the 25th in Japan, in that example, which
    matters most on the days the game starts everyone afresh (a trip's first
    day, the day the group moves base: dated the day before, the post would
    be history by the morning it was written). A trip with no "utcOffset", a
    bare date, or a time with no zone: the first ten characters, as ever."""
    raw = str(post.get('date') or '').strip()
    day = raw[:10]
    if len(raw) <= 10:
        return day
    try:
        at = datetime.datetime.fromisoformat(raw.replace('Z', '+00:00').replace('z', '+00:00'))
    except ValueError:
        return day
    if at.tzinfo is None:
        return day
    utc = at.astimezone(datetime.timezone.utc)

    def local(trip):
        offset = trip.get('utcOffset')
        if isinstance(offset, bool) or not isinstance(offset, (int, float)):
            return None
        return (utc + datetime.timedelta(hours=offset)).date().isoformat()

    # a trip that owns the day on its own clock wins: the first hours of its
    # first lead-in day are still the day before in UTC, which is the trip
    # before's (and that one may keep UTC days)
    for trip in cfg.get('trips') or []:
        there = local(trip) if isinstance(trip, dict) else None
        window = trip_window(cfg, there) if there else None
        if window and window['trip'] is trip:
            return there
    window = trip_window(cfg, utc.date().isoformat())
    return (local(window['trip']) if window else None) or day


def resolve_pos(npc, date, window=None):
    """(present, gridX, gridY) for an NPC as of date — base overlaid by every
    state dated on-or-before, in order (mirrors resolveNpc in the game). With
    a `window` (trip_window) it is scoped as the game scopes it: a base
    marked "trip" / "stay" is absent outside that trip / stay, and states
    from before the window are skipped."""
    present = npc.get('present') is not False
    if window and npc.get('trip'):
        if npc['trip'] != window['trip']['id'] or window.get('early') or (
                npc.get('stay') and (window['stay'] or {}).get('room') != npc['stay']):
            present = False
    x, y = npc.get('gridX'), npc.get('gridY')
    for d in sorted(npc.get('states', {})):
        if window and d < window['from']:
            continue
        if d <= date:
            st = npc['states'][d]
            present = st.get('present', present)
            x, y = st.get('gridX', x), st.get('gridY', y)
    return present, x, y


def occupied_cells(cfg, room_key, date, exclude_name):
    """Cells taken by other NPCs present in room_key as of date — and, for a
    district of a stitched city, by anyone standing in a neighbouring
    district on a cell the two share (their maps overlap by a row or a
    column), in room_key's own coordinates."""
    districts = city_districts(cfg, room_key) or [(room_key, 0, 0, 0, 0)]
    here = next(d for d in districts if d[0] == room_key)
    occ = set()
    window = trip_window(cfg, date)
    for room, ox, oy, _, _ in districts:
        for n in cfg['rooms'][room].get('npcs', []):
            if n['name'].lower() == exclude_name.lower():
                continue
            present, x, y = resolve_pos(n, date, window)
            if present and x is not None:
                occ.add((x + ox - here[1], y + oy - here[2]))
    return occ


def placement_room(cfg, npc_name, date):
    """The room that holds this NPC's placement dated `date`, or None."""
    for room_key, room in overworld_rooms(cfg).items():
        st = (npc_in_room(room, npc_name) or {}).get('states', {}).get(date)
        if st and st.get('present') is not False and 'gridX' in st:
            return room_key
    return None


def stay_end(cfg, npc_name, date):
    """The date of this NPC's next placement after `date`, in any room — the
    day they leave a spot taken on `date` — or None if they never move on."""
    later = [d for room in overworld_rooms(cfg).values()
             for d, st in (npc_in_room(room, npc_name) or {}).get('states', {}).items()
             if d > date and 'gridX' in st]
    return min(later) if later else None


def occupied_during(cfg, room_key, date, exclude_name):
    """Cells other NPCs stand on in room_key at any time while exclude_name
    would be standing there: from `date` until their next placement, or until
    the placement stops applying (a later trip, or a later stay of its trip,
    starts everyone from its base again — trip_window).

    occupied_cells answers for one day. History is not always written in date
    order (a backfill, a re-homed placement), so someone may already be
    recorded as arriving on a later day while this NPC is still here."""
    end = stay_end(cfg, exclude_name, date)

    def still_here(d):
        window = trip_window(cfg, d)
        return (end is None or d < end) and (window is None or window['from'] <= date)

    days = {date}
    for n in cfg['rooms'][room_key].get('npcs', []):
        if n['name'].lower() != exclude_name.lower():
            days.update(d for d in n.get('states', {}) if d > date and still_here(d))
    occ = set()
    for d in days:
        occ |= occupied_cells(cfg, room_key, d, exclude_name)
    return occ


def hidden_base_def(name, x, y):
    """An NPC definition that doesn't exist until a dated state says so."""
    base = name.lower()
    return {
        'name': name,
        'sprite': f'{base}_front',
        'gridX': x, 'gridY': y,
        'gridOffsetX': 0, 'gridOffsetY': 0,
        'dialogue': [],
        'directionalSprites': {'up': f'{base}_back', 'down': f'{base}_front',
                               'left': '', 'right': f'{base}_side'},
        'autoFlip': {'horizontal': True, 'vertical': False},
        'present': False,
    }


# what a placement writes into a dated state, besides `present`
PLACEMENT_KEYS = ('gridX', 'gridY', 'dialogue', 'photo', 'voice', 'drunk', 'posts')


def same_day_placement(cfg, npc_name, date):
    """The state an earlier post already placed this NPC with on `date`, or
    None. (At most one room holds it: apply() strips the others.)"""
    for room in overworld_rooms(cfg).values():
        npc = npc_in_room(room, npc_name)
        st = (npc or {}).get('states', {}).get(date)
        if st and st.get('present') is not False and st.get('dialogue'):
            return st
    return None


def post_entry(post_id, lines, title=None, url=None):
    """One element of a state's "posts": which post `lines` lines of its
    dialogue came from, with the post's title and url when they are known
    (the game captions the lines with the title, and links it to the url)."""
    entry = {'id': str(post_id), 'lines': lines}
    title = ' '.join(title.split()) if isinstance(title, str) else ''
    if title:
        entry['title'] = title
    if isinstance(url, str) and url.startswith(('http://', 'https://')):
        entry['url'] = url
    return entry


def merge_same_day(earlier, post_id, dialogue, photo, drunk, title=None, url=None):
    """Fold a post into the day's existing placement, if other posts made
    one. Returns (dialogue, photo, drunk, posts) to place with.

    Dated states are keyed by date, so two posts by one author on one day
    share a state. The post processed last wins the spot (the caller places
    there) and the photo if it has one; its lines follow the other posts',
    and when the day runs past MAX_DAY_LINES the oldest lines are the ones
    dropped. The day reads as drunk if any post did (one voice speaks the
    whole state).

    "posts" on the state says which lines are whose: [{"id", "lines"}, ...]
    in dialogue order (each with the post's "title" / "url" when known — see
    post_entry), listing only posts that still have lines in it. A
    re-run of a post therefore replaces just that post's own lines and keeps
    the others'. A state from before "posts" was recorded (or one edited so
    the counts no longer add up), or a payload without a post_id, replaces
    the day's dialogue outright, as the pipeline always did.
    """
    if post_id is None:
        return dialogue, photo, drunk, None
    post_id = str(post_id)
    mine = post_entry(post_id, len(dialogue), title, url)
    made_by = (earlier or {}).get('posts')
    if not (isinstance(made_by, list) and made_by
            and all(isinstance(p, dict) and isinstance(p.get('lines'), int) for p in made_by)
            and sum(p['lines'] for p in made_by) == len(earlier['dialogue'])):
        return dialogue, photo, drunk, [mine]
    kept, others, at = [], [], 0
    for p in made_by:
        if str(p.get('id')) != post_id:
            kept += earlier['dialogue'][at:at + p['lines']]
            others.append(dict(p))
        at += p['lines']
    if not others:
        return dialogue, photo, drunk, [mine]
    over = len(kept) + len(dialogue) - MAX_DAY_LINES
    if over > 0:
        kept = kept[over:]
        for p in others:                    # oldest first
            gone = min(over, p['lines'])
            p['lines'] -= gone
            over -= gone
    others = [p for p in others if p['lines'] > 0]
    return (kept + dialogue, photo or earlier.get('photo'),
            drunk or earlier.get('drunk') is True, others + [mine])


def apply(cfg, npc_name, date, target_room, x, y, dialogue, photo=None,
          voice=None, drunk=False, posts=None):
    """Dated states: appear at the spot in the target room, vanish elsewhere.
    `photo` and `voice` are always written (null when the post had none) so
    state merging never carries an older post's photo or spoken clips forward.
    `drunk` is kept so --voice-backfill can pick the right voice later, and
    `posts` (which post each run of lines came from) for merge_same_day."""
    changes = []
    for room_key, room in overworld_rooms(cfg).items():
        npc = npc_in_room(room, npc_name)
        if room_key == target_room:
            if npc is None:
                npc = hidden_base_def(npc_name, x, y)
                room.setdefault('npcs', []).append(npc)
                changes.append(f'{room_key}: added hidden base def')
            st = npc.setdefault('states', {}).setdefault(date, {})
            st.update({'present': True, 'gridX': x, 'gridY': y,
                       'dialogue': dialogue, 'photo': photo, 'voice': voice})
            if drunk:
                st['drunk'] = True
            else:
                st.pop('drunk', None)
            if posts:
                st['posts'] = posts
            else:
                st.pop('posts', None)
            changes.append(f'{room_key}: present at ({x},{y}) from {date}'
                           + (f' with photo {photo}' if photo else '')
                           + (f' with voice {voice}' if voice else ''))
        elif npc is not None:
            st = npc.setdefault('states', {}).setdefault(date, {})
            st['present'] = False
            # an earlier post the same day may have placed them here: that
            # placement moved to target_room, so nothing of it stays behind
            for key in PLACEMENT_KEYS:
                st.pop(key, None)
            changes.append(f'{room_key}: absent from {date}')
    changes += repair_presence(cfg, npc_name, date, target_room)
    return changes


def repair_presence(cfg, npc_name, from_date, active_room):
    """Keep history chronological when a post is older than existing states.

    States merge in date order and 'present' persists until overridden — so a
    present:false written at an old date would hide the NPC straight through
    newer position-bearing states that never said 'present: true' (they were
    authored when presence was implicit). Walk every later placement in date
    order and make presence explicit at each move: the NPC reappears wherever
    a newer state placed them, and the room they left goes absent.
    """
    placements = []   # (date, room_key)
    for room_key, room in overworld_rooms(cfg).items():
        npc = npc_in_room(room, npc_name)
        for d, st in (npc.get('states', {}) if npc else {}).items():
            if d > from_date and 'gridX' in st:
                placements.append((d, room_key))

    changes = []
    for d, room_key in sorted(placements):
        npc = npc_in_room(cfg['rooms'][room_key], npc_name)
        npc['states'][d].setdefault('present', True)
        if room_key != active_room:
            prev = npc_in_room(cfg['rooms'][active_room], npc_name)
            if prev is not None:
                prev.setdefault('states', {}).setdefault(d, {})['present'] = False
                changes.append(f'{active_room}: absent from {d} (moves on to {room_key})')
            changes.append(f'{room_key}: presence restored from {d}')
            active_room = room_key
    return changes


def rehome(cfg, npc_name, date, spot_id, spots):
    """Move the placement `npc_name` has on `date` to another spot, keeping
    everything the post gave it (dialogue, photo, voice, drunk, posts).
    Returns the change lines, like apply(). Raises ValueError when there is
    nothing to move or nowhere to stand.

    The room they leave gets the bare `present: false` a normal move leaves
    behind, the new room a hidden base def if they were never there, and the
    later history is re-checked (repair_presence) — it is apply() with the
    old state's content. The cell is one nobody else stands on for as long
    as they stay (occupied_during).

    A spot in the room they are already in changes the cell and nothing else
    (#190): presence everywhere is already right for that date, so no state
    is added in other rooms and no key the state lacked is written."""
    if spot_id not in spots:
        raise ValueError(f'unknown spot {spot_id!r}')
    from_room = placement_room(cfg, npc_name, date)
    if from_room is None:
        raise ValueError(f'{npc_name} has no placement dated {date}')
    room_key = spots[spot_id][0]
    cell = stand_cell(cfg, spot_id, spots, occupied_during(cfg, room_key, date, npc_name))[1]
    if cell is None:
        raise ValueError(f'no walkable cell near {spot_id}')
    state = npc_in_room(cfg['rooms'][from_room], npc_name)['states'][date]
    old = dict(state)   # a copy: when the spot is in another room apply() strips the old state
    moved = f'{npc_name} {date}: {from_room} ({old["gridX"]},{old["gridY"]}) -> {spot_id} {cell}'
    if room_key == from_room:
        state['gridX'], state['gridY'] = cell
        return [moved]
    return [moved] + \
        apply(cfg, npc_name, date, room_key, cell[0], cell[1], old.get('dialogue', []),
              old.get('photo'), old.get('voice'), old.get('drunk') is True, old.get('posts'))


def report_usage(usage):
    """Per-post token counts and a projected cost, for planning at scale."""
    if usage is None:
        print('usage: (mock — no LLM call)')
        return
    ci = getattr(usage, 'cache_creation_input_tokens', 0) or 0
    cr = getattr(usage, 'cache_read_input_tokens', 0) or 0
    inp, out = usage.input_tokens, usage.output_tokens
    # cache writes bill ~1.25x, reads ~0.1x; this pipeline doesn't cache, but
    # count them so the projection stays honest if that changes
    cost = ((inp + 1.25 * ci + 0.1 * cr) * PRICE_IN_PER_M
            + out * PRICE_OUT_PER_M) / 1_000_000
    print(f'usage: {inp} in + {out} out'
          + (f' ({ci} cache-write, {cr} cache-read)' if ci or cr else '')
          + f'  ≈ ${cost:.4f}/post'
          + f'  ×100 posts ≈ ${cost * 100:.2f}'
          + f'  ({MODEL} @ ${PRICE_IN_PER_M:g}/${PRICE_OUT_PER_M:g} per M)')


def reset_states(cfg):
    """Wipe pipeline/demo history back to the canonical base cast: strip every
    NPC's dated `states`, and drop the hidden base defs the pipeline added in
    non-home rooms (a base with `present: false`). Leaves the real NPCs and
    their base position/dialogue untouched — those are the pre-first-post
    fallback."""
    removed = 0
    for room in overworld_rooms(cfg).values():
        kept = []
        for npc in room.get('npcs', []):
            npc.pop('states', None)
            if npc.get('present') is False:
                removed += 1
            else:
                kept.append(npc)
        room['npcs'] = kept
    print(f'reset: cleared all NPC states, removed {removed} hidden base defs')


def process_post(cfg, post, spots, spot_ids, mock=False, dry_run=False):
    """Generate + place one post into cfg. Returns (record | None, usage).
    record describes the placement for the issue comment: npc, room, spot."""
    author = (post.get('author') or '').strip().lower()
    npc_name = npc_for_author(author)
    if not npc_name:
        warning = unmapped_author_warning(post.get('post_id'), author)
        print(warning)
        if os.environ.get('GITHUB_ACTIONS'):
            # an annotation on the workflow run, so the skip is seen without
            # opening the log
            print(f'::warning title=Blog author has no NPC::{warning}')
        return None, None

    date = post_date(cfg, post)
    if not is_day(date):
        print(f'#{post.get("post_id")}: bad date {post.get("date")!r} — skipped')
        return None, None

    result, usage = generate(post, npc_name, spot_ids, mock=mock, offers=offer_lines(cfg, spot_ids))
    spot_id = result.get('spot')
    dialogue = clean_dialogue(result.get('dialogue', []))
    if spot_id not in spots or not dialogue:
        print(f'#{post.get("post_id")}: unusable content (spot={spot_id!r}, '
              f'{len(dialogue)} lines) — skipped')
        return None, usage

    room_key = spots[spot_id][0]
    cell = stand_cell(cfg, spot_id, spots, occupied_during(cfg, room_key, date, npc_name))[1]
    if cell is None:
        print(f'#{post.get("post_id")}: no walkable cell near {spot_id} — skipped')
        return None, usage

    print(f'#{post.get("post_id")} {date} {author} -> {npc_name} @ {spot_id} {cell}')
    for line in dialogue:
        print(f'  » {line}')
    photo = import_post_photo(post, dry_run=dry_run)
    drunk = result.get('drunk') is True
    earlier = same_day_placement(cfg, npc_name, date)
    said = len(dialogue)
    dialogue, photo, drunk, posts = merge_same_day(
        earlier, post.get('post_id'), dialogue, photo, drunk,
        title=post.get('title'), url=post.get('url'))
    if posts and len(posts) > 1:
        print(f'  same day as post(s) {", ".join(p["id"] for p in posts[:-1])}: this spot '
              f'wins, {len(dialogue) - said} of their line(s) kept ahead of these {said}')
    voice = voice_dialogue(npc_name, date, dialogue, drunk=drunk, dry_run=dry_run)
    for c in apply(cfg, npc_name, date, room_key, cell[0], cell[1], dialogue,
                   photo, voice, drunk, posts):
        print(f'  {c}')
    record = {
        'post_id': post.get('post_id'),
        'npc': npc_name,
        'room': cfg['rooms'][room_key].get('name', room_key),
        'spot': spot_id.split(' · ', 1)[-1],   # "the vending machines", "Asakusa (area)"
        'date': date,
        'photo': bool(photo),
        'voice': bool(voice),
    }
    return record, usage


def voice_backfill(cfg, dry_run=False):
    """Speak every dated state that has dialogue but no voice. Only the blog
    authors' NPCs have voices. Returns the number of states voiced."""
    voiced = pending = lines = chars = 0
    for room_key, room in cfg['rooms'].items():
        for npc in room.get('npcs', []):
            if npc['name'] not in AUTHOR_NPCS.values():
                continue
            for date, st in sorted(npc.get('states', {}).items()):
                dialogue = st.get('dialogue')
                if not dialogue or st.get('voice'):
                    continue
                pending += 1
                lines += len(dialogue)
                chars += sum(len(line) for line in dialogue)
                print(f'{room_key} {npc["name"]} {date}: {len(dialogue)} lines')
                voice = voice_dialogue(npc['name'], date, dialogue,
                                       drunk=st.get('drunk') is True, dry_run=dry_run)
                if voice:
                    st['voice'] = voice
                    voiced += 1
    print(f'voice backfill: {pending} unvoiced state(s), {lines} lines, {chars} chars'
          f' · {voiced} {"would be voiced" if dry_run else "voiced"}')
    return voiced


def backfill_posts(cfg, entries):
    """Fill in post titles and urls on states placed before they were
    recorded (issue #79). `entries` is a list of {"id", "title", "url"},
    optionally with "author" (GitHub login) and "date". Returns the number of
    states changed. No state's dialogue, spot, photo or voice is touched.

    A state is matched to its post by, in order:
      1. its own "posts" — every entry whose id is in the list gets that
         post's title and url;
      2. its photo — a photo is filed under the id of the post it came from,
         so a state with no "posts" and photo N is post N's;
      3. author and date, for a state with neither: the one listed post by
         that NPC's author on that day. Several posts on the day cannot be
         told apart (the last one processed wrote the state), so the state is
         reported and left alone.
    A state matched by 2 or 3 gains "posts": [{id, lines: all of them, ...}].
    """
    by_id, by_day = {}, {}
    for e in entries:
        if not isinstance(e, dict) or e.get('id') is None:
            continue
        by_id[str(e['id'])] = e
        npc_name = AUTHOR_NPCS.get(str(e.get('author') or '').lower())
        date = post_date(cfg, e)
        if npc_name and is_day(date):
            by_day.setdefault((npc_name, date), []).append(e)

    changed = unmatched = 0
    used = set()
    for room_key, room in cfg['rooms'].items():
        for npc in room.get('npcs', []):
            for date, st in sorted(npc.get('states', {}).items()):
                if not st.get('dialogue') or st.get('present') is False:
                    continue
                where = f'{room_key} {npc["name"]} {date}'
                before = json.dumps(st.get('posts'), sort_keys=True)
                made_by = st.get('posts')
                if isinstance(made_by, list) and made_by:
                    st['posts'] = [
                        post_entry(p['id'], p.get('lines'),
                                   by_id[str(p['id'])].get('title') or p.get('title'),
                                   by_id[str(p['id'])].get('url') or p.get('url'))
                        if isinstance(p, dict) and str(p.get('id')) in by_id else p
                        for p in made_by]
                    found = [str(p['id']) for p in made_by
                             if isinstance(p, dict) and str(p.get('id')) in by_id]
                else:
                    same_day = by_day.get((npc['name'], date), [])
                    if st.get('photo') is not None and str(st['photo']) in by_id:
                        e = by_id[str(st['photo'])]
                    elif len(same_day) == 1:
                        e = same_day[0]
                    else:
                        if len(same_day) > 1:
                            print(f'{where}: {len(same_day)} posts that day '
                                  f'({", ".join(str(x["id"]) for x in same_day)}) and no photo '
                                  'to tell them apart — left alone')
                        e = None
                    found = [str(e['id'])] if e else []
                    if e:
                        st['posts'] = [post_entry(e['id'], len(st['dialogue']),
                                                  e.get('title'), e.get('url'))]
                used.update(found)
                if not found:
                    unmatched += 1
                elif json.dumps(st.get('posts'), sort_keys=True) != before:
                    changed += 1
                    print(f'{where}: ' + ', '.join(
                        f'#{p["id"]} {p.get("title", "(no title)")!r}' for p in st['posts']))
    unused = sorted(set(by_id) - used, key=lambda i: (len(i), i))
    print(f'post backfill: {changed} state(s) updated, {unmatched} with no post in the list'
          + (f', {len(unused)} listed post(s) matched nothing: {", ".join(unused)}' if unused else ''))
    return changed


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--payload', help='single blog post payload JSON file')
    src.add_argument('--payloads-dir', help='directory of payload JSONs — processed in date order (backfill)')
    src.add_argument('--voice-backfill', action='store_true',
                     help='speak existing dated states that have dialogue but no voice (no LLM, no placement)')
    src.add_argument('--backfill-posts', metavar='POSTS_JSON',
                     help='fill post title/url into existing states from a JSON list of '
                          '{id, title, url[, author, date]} (no LLM, no placement)')
    src.add_argument('--rehome', nargs=3, action='append', metavar=('NPC', 'DATE', 'SPOT'),
                     help='move an existing placement to another spot, e.g. --rehome Julia 2025-11-12 '
                          '"Market · the 7-Eleven" (no LLM; dialogue, photo and voice go along; repeatable)')
    ap.add_argument('--reset', action='store_true', help='clear all NPC states + hidden defs before placing (backfill)')
    ap.add_argument('--dry-run', action='store_true', help='generate + place, but do not write config')
    ap.add_argument('--mock', action='store_true', help='skip the LLM (canned response)')
    ap.add_argument('--summary-out', help='write a JSON summary of placements (for the issue comment)')
    args = ap.parse_args()

    if args.voice_backfill:
        if args.reset:
            ap.error('--reset cannot be combined with --voice-backfill')
        cfg = load_config()
        voiced = voice_backfill(cfg, dry_run=args.dry_run)
        if args.dry_run:
            print('dry run — config.json not written')
        else:
            if voiced:
                save_config(cfg)
                print('config.json updated')
            prune_voices(cfg)
            prune_photos(cfg)
        return 0

    if args.backfill_posts:
        if args.reset:
            ap.error('--reset cannot be combined with --backfill-posts')
        entries = json.load(open(args.backfill_posts))
        if isinstance(entries, dict):
            entries = entries.get('posts')
        if not isinstance(entries, list):
            ap.error('--backfill-posts wants a JSON list of {id, title, url}')
        cfg = load_config()
        changed = backfill_posts(cfg, entries)
        if args.dry_run:
            print('dry run — config.json not written')
        elif changed:
            save_config(cfg)
            print('config.json updated')
        return 0

    if args.rehome:
        if args.reset:
            ap.error('--reset cannot be combined with --rehome')
        cfg = load_config()
        spots = all_spots(cfg)
        for npc_name, date, spot_id in args.rehome:
            try:
                for line in rehome(cfg, npc_name, date, spot_id, spots):
                    print(line if line.startswith(npc_name) else f'  {line}')
            except ValueError as e:
                ap.error(f'--rehome {npc_name} {date}: {e}')
        if args.dry_run:
            print('dry run — config.json not written')
        else:
            save_config(cfg)
            print('config.json updated')
        return 0

    if args.payload:
        posts = [json.load(open(args.payload))]
    else:
        import glob
        posts = [json.load(open(p)) for p in glob.glob(os.path.join(args.payloads_dir, '*.json'))]
        # chronological: earlier posts placed first so history builds forward
        posts.sort(key=lambda p: str(p.get('date', '')))
    print(f'{len(posts)} post(s) to process')

    cfg = load_config()
    if args.reset:
        reset_states(cfg)

    spots = all_spots(cfg)
    spot_ids = sorted(spots)
    print(f'{len(spot_ids)} candidate spots ({len(find_areas(cfg))} of them districts) across '
          f'{len(overworld_rooms(cfg))} overworld rooms')

    records = []
    tot_in = tot_out = 0
    for post in posts:
        try:
            record, usage = process_post(cfg, post, spots, spot_ids,
                                         mock=args.mock, dry_run=args.dry_run)
        except SystemExit:
            raise
        except Exception as e:
            # one bad post shouldn't sink a 60-post backfill; report and move on
            print(f'#{post.get("post_id")}: ERROR {type(e).__name__}: {e} — skipped')
            continue
        if record:
            records.append(record)
        if usage is not None:
            tot_in += usage.input_tokens
            tot_out += usage.output_tokens

    if len(posts) > 1 or tot_in:
        cost = (tot_in * PRICE_IN_PER_M + tot_out * PRICE_OUT_PER_M) / 1_000_000
        print(f'placed {len(records)}/{len(posts)} posts · usage {tot_in} in + {tot_out} out '
              f'≈ ${cost:.4f} total ({MODEL} @ ${PRICE_IN_PER_M:g}/${PRICE_OUT_PER_M:g} per M)')

    # summary for the workflow: only placements (empty list -> no comment)
    if args.summary_out:
        json.dump({'placed': records}, open(args.summary_out, 'w'))

    if args.dry_run:
        print('dry run — config.json not written')
    elif records or args.reset:
        save_config(cfg)
        print('config.json updated')
        prune_voices(cfg)   # clip sets the new config no longer points at
        prune_photos(cfg)   # prints whose state lost its placement
    else:
        # nothing placed, config untouched: a post that failed after its photo
        # was imported has left a print no state names
        prune_photos(load_config())
    return 0


if __name__ == '__main__':
    sys.exit(main())
