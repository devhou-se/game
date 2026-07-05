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
MAX_DIALOGUE_LINES = 5
MAX_LINE_CHARS = 160


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


def walkable_near(cfg, room_key, gx, gy):
    """Nearest walkable cell (floored, uncollided, not a transporter, not
    another NPC's spot) — a python port of GameScene.findWalkableNear."""
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
    npcs = {f"{n['gridX']},{n['gridY']}" for n in room.get('npcs', [])}

    def ok(x, y):
        key = f'{x},{y}'
        return (0 <= x < cells_w and 0 <= y < cells_h and key in floored
                and key not in blocked and key not in portals and key not in npcs)

    for rad in range(0, 12):
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if max(abs(dx), abs(dy)) != rad:
                    continue
                if ok(gx + dx, gy + dy):
                    return gx + dx, gy + dy
    return None


def generate(post, npc_name, spot_ids, mock=False):
    """Claude Sonnet turns the post into {spot, dialogue}."""
    if mock:
        return {'spot': spot_ids[0], 'dialogue': [
            f"I just wrote about {post['title']}!",
            'Come read it on the blog.',
        ]}

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
        'their own post; 3-5 lines; each line under 140 characters; playful '
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
        # surface the provisioned limits — tells apart "account limits not
        # active yet" (all zeros/absent) from "genuinely out of throughput"
        for k, v in e.response.headers.items():
            if 'ratelimit' in k.lower() or k.lower() == 'retry-after':
                print(f'  {k}: {v}')
        raise
    text = next(b.text for b in response.content if b.type == 'text')
    return json.loads(text)


def npc_in_room(room, name):
    return next((n for n in room.get('npcs', []) if n['name'].lower() == name.lower()), None)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--payload', required=True, help='blog post payload JSON file')
    ap.add_argument('--dry-run', action='store_true', help='generate + place, but do not write config')
    ap.add_argument('--mock', action='store_true', help='skip the LLM (canned response)')
    args = ap.parse_args()

    post = json.load(open(args.payload))
    author = (post.get('author') or '').lower()
    npc_name = AUTHOR_NPCS.get(author)
    if not npc_name:
        print(f'no NPC mapped for author {author!r} — nothing to do '
              f'(known: {sorted(AUTHOR_NPCS)})')
        return 0

    date = str(post.get('date', ''))[:10]
    if len(date) != 10:
        print(f'bad post date {post.get("date")!r}')
        return 1

    cfg = load_config()
    spots = find_spots(cfg)
    spot_ids = sorted(spots)
    print(f'{len(spot_ids)} candidate spots across '
          f'{len(overworld_rooms(cfg))} overworld rooms')

    result = generate(post, npc_name, spot_ids, mock=args.mock)
    spot_id = result['spot']
    dialogue = [line.strip()[:MAX_LINE_CHARS]
                for line in result['dialogue'] if line.strip()][:MAX_DIALOGUE_LINES]
    if spot_id not in spots or not dialogue:
        print(f'model returned unusable content: spot={spot_id!r}, {len(dialogue)} lines')
        return 1

    room_key, ax, ay = spots[spot_id]
    cell = walkable_near(cfg, room_key, ax, ay)
    if cell is None:
        print(f'no walkable cell near {spot_id} ({ax},{ay})')
        return 1

    print(f'post #{post.get("post_id")} by {author} -> {npc_name} at '
          f'{spot_id} cell {cell} on {date}')
    for line in dialogue:
        print(f'  » {line}')

    changes = apply(cfg, npc_name, date, room_key, cell[0], cell[1], dialogue)
    for c in changes:
        print(f'  {c}')

    if args.dry_run:
        print('dry run — config.json not written')
    else:
        save_config(cfg)
        print('config.json updated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
