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

Run from gamev2/ (normally by the www-jp game-npc-pipeline workflow; the unit
checks are `python3 tools/test_blog_to_npc.py`):

  python3 tools/blog_to_npc.py --payload post.json [--dry-run] [--mock]
  python3 tools/blog_to_npc.py --voice-backfill [--dry-run]
  python3 tools/blog_to_npc.py --backfill-posts posts.json [--dry-run]

--voice-backfill makes no LLM call and places nobody: it speaks every existing
dated state that has dialogue but no voice (a state with "drunk": true gets
the drunk voice), so history placed before voices existed can be voiced once
the ElevenLabs env is configured. With --dry-run it only reports the lines and
characters it would send, which is the number ElevenLabs bills on.

--backfill-posts makes no LLM call and places nobody either: it fills in the
post title and url on states that were placed before those were recorded.
posts.json is a list of {"id", "title", "url"} (optionally "author" and
"date" too — see backfill_posts for how a state is matched to its post).

post.json is the blog payload: {"post_id", "title", "author", "date",
"content"} and optionally "url" (the post's page; recorded when present) —
author is the GitHub login. Needs ANTHROPIC_API_KEY unless --mock (canned
LLM response, for testing the placement plumbing).

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
# `stand` is the cell to stand on, relative to the first matching tile.
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
    ('seven-eleven', 'the 7-Eleven'),
    ('blue-bell', 'the temple bell'),
    ('sakura-large-top', 'the sakura trees'),
    ('white-vending-machine-top', 'the vending machines'),
    # Machi's lane. Asahikawa's ramen alley is built from the same machiya
    # prefabs and has its own name below (issue #100)
    ('machiya-', 'the old-town lane', (2, 5), {'rooms': ('Machi',)}),   # on the lane, at a shop door
    # Named landmarks. These are single sprites many cells tall, whose tile
    # cell is their top-left corner (the tip of a tower) — so each carries the
    # cell, relative to that corner, where someone visiting it would stand:
    # on the ground at its foot, clear of doorways and archways.
    ('tokyo-tower_', 'Tokyo Tower', (9, 14)),          # beside the east leg
    ('tokyo-station_', 'Tokyo Station', (24, 9)),      # the forecourt, east of the door
    ('tsutenkaku_', 'Tsutenkaku Tower', (5, 14)),      # the plaza in front of it
    ('dotonbori-arch_', 'the Dotonbori arch', (0, 6)),  # through the arch, on the west pavement clear of the road and its signal (#106)
    ('dotonbori-wheel_', 'the Dotonbori ferris wheel', (6, 12)),   # the canal bank below it
    ('discount-store_', 'the Don Takote discount store', (3, 8)),  # beside its doors (in front is where shoppers step out, #91)
    # Hokkaido (issue #43)
    ('sapporo-clock-tower_', 'the Sapporo Clock Tower', (2, 8)),   # the pavement at its porch
    ('sapporo-tv-tower_', 'the Sapporo TV Tower', (3, 13)),        # in front of the entrance
    ('asahikawa-bridge_', 'the bridge over the frozen river', (1, -1)),   # the north bridgehead
    ('ramen-banner_', 'ramen alley', (-1, 2)),                     # on the lane, outside a shop
    ('ice-pond-autotile_corner-nw', 'the frozen pond', (0, -1)),   # on the bank (the ice is solid)
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
    the `interior` rooms (konbini, izakaya). Station rooms are in here — they
    hold placements — but are indoors as far as spots go (is_indoors)."""
    return {k: r for k, r in cfg['rooms'].items() if not r.get('interior')}


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
    nothing — see landmark_applies."""
    spots = {}
    for room_key, room in overworld_rooms(cfg).items():
        landmarks = [(prefix, label, stand)
                     for prefix, label, stand, options in map(landmark_fields, LANDMARKS)
                     if landmark_applies(cfg, room_key, options)]
        for layer in room.get('layers', []):
            tiles = decode_tiles(cfg, layer)
            for xy, key in tiles.items():
                for prefix, label, (dx, dy) in landmarks:
                    spot_id = f'{room_key} · {label}'
                    if key.startswith(prefix) and spot_id not in spots:
                        x, y = map(int, xy.split(','))
                        spots[spot_id] = (room_key, x + dx, y + dy)
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


def reachable_cells(cfg, room_key):
    """(x, y) of every cell the player can walk to from the room's ways in
    (its transporters), or None for a room that has none to start from —
    callers then do not filter on reachability at all. Transporters are the
    only seeds: if rooms ever join some other way, seed from that too."""
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


def walkable_near(cfg, room_key, gx, gy, occupied=frozenset()):
    """Nearest cell someone can stand on and be walked up to: floored,
    uncollided, not a transporter, not an occupied cell (the test of
    GameScene.findWalkableNear) and connected to one of the room's ways in —
    so a landmark standing in a fenced garden puts its visitor outside the
    fence, not in with it. `occupied` is (x,y) tuples already taken by other
    NPCs (resolved positions, not base defs — see occupied_cells)."""
    cells_w, cells_h, floored, blocked = room_cells(cfg, room_key)
    portals = {f"{t['gridX']},{t['gridY']}" for t in cfg['rooms'][room_key].get('transporters', [])}
    reachable = reachable_cells(cfg, room_key)

    def ok(x, y):
        key = f'{x},{y}'
        return (0 <= x < cells_w and 0 <= y < cells_h and key in floored
                and key not in blocked and key not in portals and (x, y) not in occupied
                and (reachable is None or (x, y) in reachable))

    for rad in range(0, 12):
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if max(abs(dx), abs(dy)) != rad:
                    continue
                if ok(gx + dx, gy + dy):
                    return gx + dx, gy + dy
    return None


def generate(post, npc_name, spot_ids, mock=False):
    """Claude Sonnet turns the post into ({spot, dialogue, drunk}, usage).
    usage is None for --mock, else the response.usage token counts."""
    if mock:
        return {'spot': spot_ids[0], 'dialogue': [
            f"I just wrote about {post['title']}!",
            'Come read it on the blog.',
        ], 'drunk': False}, None

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
        'choose an outdoor spot.\n\n'
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
        f"Available spots:\n" + '\n'.join(f'- {s}' for s in spot_ids)
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
    """Cells taken by other NPCs present in room_key as of date."""
    occ = set()
    window = trip_window(cfg, date)
    for n in cfg['rooms'][room_key].get('npcs', []):
        if n['name'].lower() == exclude_name.lower():
            continue
        present, x, y = resolve_pos(n, date, window)
        if present and x is not None:
            occ.add((x, y))
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

    date = str(post.get('date', ''))[:10]
    if len(date) != 10:
        print(f'#{post.get("post_id")}: bad date {post.get("date")!r} — skipped')
        return None, None

    result, usage = generate(post, npc_name, spot_ids, mock=mock)
    spot_id = result.get('spot')
    dialogue = clean_dialogue(result.get('dialogue', []))
    if spot_id not in spots or not dialogue:
        print(f'#{post.get("post_id")}: unusable content (spot={spot_id!r}, '
              f'{len(dialogue)} lines) — skipped')
        return None, usage

    room_key, ax, ay = spots[spot_id]
    occ = occupied_cells(cfg, room_key, date, npc_name)
    cell = walkable_near(cfg, room_key, ax, ay, occ)
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
        'spot': spot_id.split(' · ', 1)[-1],   # "the vending machines"
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
        date = str(e.get('date') or '')[:10]
        if npc_name and len(date) == 10:
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

    spots = find_spots(cfg)
    spot_ids = sorted(spots)
    print(f'{len(spot_ids)} candidate spots across '
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
