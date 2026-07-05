#!/usr/bin/env python3
"""blog_to_npc.py — the blog → game pipeline.

A new devhou.se blog post moves its author's NPC somewhere in the game world
and gives them fresh dialogue, both derived from the post's content by Claude
(Sonnet). The result is written as dated NPC states in config.json (see
src/utils/NpcStates.js): the author appears at the chosen spot with the new
dialogue from the post's date, and disappears from wherever they were before.
Time travel (the in-game date picker) replays history faithfully.

Run from gamev2/ (normally by the www-jp game-npc-pipeline workflow):

  python3 tools/blog_to_npc.py --payload post.json [--dry-run] [--mock]

post.json is the blog payload: {"post_id", "title", "author", "date",
"content"} — author is the GitHub login. Needs ANTHROPIC_API_KEY unless
--mock (canned LLM response, for testing the placement plumbing).

Cross-room moves rely on resolveNpc semantics: an NPC definition whose base
has "present": false stays hidden until a dated state sets present true, so
authors can hop between rooms with one hidden base def per visited room.
"""
import argparse
import json
import os
import sys

# GitHub login -> NPC name (must exist in config, or be creatable from
# <name>_front/_back/_side sprites)
AUTHOR_NPCS = {
    'baely': 'Bailey',
    'damiante': 'Damian',
    'dbut2': 'Dylan',
    'jughents': 'Julia',
}

# landmark tile-key prefix -> spot label offered to the model
LANDMARKS = [
    ('shrine-building', 'the shrine'),
    ('torii-red', 'the torii gate'),
    ('red-pagoda', 'the pagoda'),
    ('fox-statue', 'the fox statues'),
    ('pond-autotile_corner-nw', 'the pond'),
    ('seven-eleven', 'the 7-Eleven'),
    ('blue-bell', 'the temple bell'),
    ('sakura-large-top', 'the sakura trees'),
    ('white-vending-machine-top', 'the vending machines'),
]

MODEL = 'claude-sonnet-5'
MAX_DIALOGUE_LINES = 4
MAX_LINE_CHARS = 160

# claude-sonnet-5 list price, USD per million tokens (standard, not the intro
# rate — keeps the per-post projection conservative once intro pricing ends)
PRICE_IN_PER_M = 3.00
PRICE_OUT_PER_M = 15.00


def load_config():
    return json.load(open('config.json'))


def save_config(cfg):
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))


def overworld_rooms(cfg):
    return {k: r for k, r in cfg['rooms'].items() if not r.get('interior')}


def decode_tiles(cfg, layer):
    pal = cfg.get('tilePalette')
    out = {}
    for xy, v in (layer.get('tiles') or {}).items():
        out[xy] = pal[v] if isinstance(v, int) else v
    return out


def find_spots(cfg):
    """Every landmark in every overworld room -> {'Room · label': (room, x, y)}."""
    spots = {}
    for room_key, room in overworld_rooms(cfg).items():
        for layer in room.get('layers', []):
            tiles = decode_tiles(cfg, layer)
            for xy, key in tiles.items():
                for prefix, label in LANDMARKS:
                    spot_id = f'{room_key} · {label}'
                    if key.startswith(prefix) and spot_id not in spots:
                        x, y = map(int, xy.split(','))
                        spots[spot_id] = (room_key, x, y)
    return spots


def walkable_near(cfg, room_key, gx, gy, occupied=frozenset()):
    """Nearest walkable cell (floored, uncollided, not a transporter, not an
    occupied cell) — a python port of GameScene.findWalkableNear. `occupied`
    is (x,y) tuples already taken by other NPCs (resolved positions, not base
    defs — see occupied_cells)."""
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
    portals = {f"{t['gridX']},{t['gridY']}" for t in room.get('transporters', [])}

    def ok(x, y):
        key = f'{x},{y}'
        return (0 <= x < cells_w and 0 <= y < cells_h and key in floored
                and key not in blocked and key not in portals and (x, y) not in occupied)

    for rad in range(0, 12):
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if max(abs(dx), abs(dy)) != rad:
                    continue
                if ok(gx + dx, gy + dy):
                    return gx + dx, gy + dy
    return None


def generate(post, npc_name, spot_ids, mock=False):
    """Claude Sonnet turns the post into ({spot, dialogue}, usage). usage is
    None for --mock, else the response.usage token counts."""
    if mock:
        return {'spot': spot_ids[0], 'dialogue': [
            f"I just wrote about {post['title']}!",
            'Come read it on the blog.',
        ]}, None

    import anthropic
    # generous retries: fresh/low-tier accounts have small per-minute limits
    client = anthropic.Anthropic(max_retries=5)

    schema = {
        'type': 'object',
        'properties': {
            'spot': {'type': 'string', 'enum': spot_ids},
            'dialogue': {'type': 'array', 'items': {'type': 'string'}},
        },
        'required': ['spot', 'dialogue'],
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
        'content or mood (e.g. a post about trains near the station room, '
        'food near the 7-Eleven, reflection near the shrine or pond).'
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


def npc_in_room(room, name):
    return next((n for n in room.get('npcs', []) if n['name'].lower() == name.lower()), None)


def resolve_pos(npc, date):
    """(present, gridX, gridY) for an NPC as of date — base overlaid by every
    state dated on-or-before, in order (mirrors resolveNpc in the game)."""
    present = npc.get('present') is not False
    x, y = npc.get('gridX'), npc.get('gridY')
    for d in sorted(npc.get('states', {})):
        if d <= date:
            st = npc['states'][d]
            present = st.get('present', present)
            x, y = st.get('gridX', x), st.get('gridY', y)
    return present, x, y


def occupied_cells(cfg, room_key, date, exclude_name):
    """Cells taken by other NPCs present in room_key as of date."""
    occ = set()
    for n in cfg['rooms'][room_key].get('npcs', []):
        if n['name'].lower() == exclude_name.lower():
            continue
        present, x, y = resolve_pos(n, date)
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


def apply(cfg, npc_name, date, target_room, x, y, dialogue):
    """Dated states: appear at the spot in the target room, vanish elsewhere."""
    changes = []
    for room_key, room in overworld_rooms(cfg).items():
        npc = npc_in_room(room, npc_name)
        if room_key == target_room:
            if npc is None:
                npc = hidden_base_def(npc_name, x, y)
                room.setdefault('npcs', []).append(npc)
                changes.append(f'{room_key}: added hidden base def')
            st = npc.setdefault('states', {}).setdefault(date, {})
            st.update({'present': True, 'gridX': x, 'gridY': y, 'dialogue': dialogue})
            changes.append(f'{room_key}: present at ({x},{y}) from {date}')
        elif npc is not None:
            st = npc.setdefault('states', {}).setdefault(date, {})
            st['present'] = False
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


def process_post(cfg, post, spots, spot_ids, mock=False):
    """Generate + place one post into cfg. Returns (placed: bool, usage)."""
    author = (post.get('author') or '').lower()
    npc_name = AUTHOR_NPCS.get(author)
    if not npc_name:
        print(f'#{post.get("post_id")}: no NPC for {author!r} — skipped')
        return False, None

    date = str(post.get('date', ''))[:10]
    if len(date) != 10:
        print(f'#{post.get("post_id")}: bad date {post.get("date")!r} — skipped')
        return False, None

    result, usage = generate(post, npc_name, spot_ids, mock=mock)
    spot_id = result.get('spot')
    dialogue = [line.strip()[:MAX_LINE_CHARS]
                for line in result.get('dialogue', []) if line.strip()][:MAX_DIALOGUE_LINES]
    if spot_id not in spots or not dialogue:
        print(f'#{post.get("post_id")}: unusable content (spot={spot_id!r}, '
              f'{len(dialogue)} lines) — skipped')
        return False, usage

    room_key, ax, ay = spots[spot_id]
    occ = occupied_cells(cfg, room_key, date, npc_name)
    cell = walkable_near(cfg, room_key, ax, ay, occ)
    if cell is None:
        print(f'#{post.get("post_id")}: no walkable cell near {spot_id} — skipped')
        return False, usage

    print(f'#{post.get("post_id")} {date} {author} -> {npc_name} @ {spot_id} {cell}')
    for line in dialogue:
        print(f'  » {line}')
    for c in apply(cfg, npc_name, date, room_key, cell[0], cell[1], dialogue):
        print(f'  {c}')
    return True, usage


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--payload', help='single blog post payload JSON file')
    src.add_argument('--payloads-dir', help='directory of payload JSONs — processed in date order (backfill)')
    ap.add_argument('--reset', action='store_true', help='clear all NPC states + hidden defs before placing (backfill)')
    ap.add_argument('--dry-run', action='store_true', help='generate + place, but do not write config')
    ap.add_argument('--mock', action='store_true', help='skip the LLM (canned response)')
    args = ap.parse_args()

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

    placed = 0
    tot_in = tot_out = 0
    for i, post in enumerate(posts):
        if i and not args.mock:
            import time
            time.sleep(1.2)   # gentle spacing so a big backfill stays under RPM
        try:
            ok, usage = process_post(cfg, post, spots, spot_ids, mock=args.mock)
        except SystemExit:
            raise
        except Exception as e:
            # one bad post shouldn't sink a 60-post backfill; report and move on
            print(f'#{post.get("post_id")}: ERROR {type(e).__name__}: {e} — skipped')
            continue
        placed += 1 if ok else 0
        if usage is not None:
            tot_in += usage.input_tokens
            tot_out += usage.output_tokens

    if len(posts) > 1 or tot_in:
        cost = (tot_in * PRICE_IN_PER_M + tot_out * PRICE_OUT_PER_M) / 1_000_000
        print(f'placed {placed}/{len(posts)} posts · usage {tot_in} in + {tot_out} out '
              f'≈ ${cost:.4f} total ({MODEL} @ ${PRICE_IN_PER_M:g}/${PRICE_OUT_PER_M:g} per M)')

    if args.dry_run:
        print('dry run — config.json not written')
    elif placed or args.reset:
        save_config(cfg)
        print('config.json updated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
