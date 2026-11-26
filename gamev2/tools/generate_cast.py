#!/usr/bin/env python3
"""generate_cast.py — bake interim sprite sets for cast members without art.

The character creator (src/CharacterCreator.js) composes a character at
runtime from the hand-drawn cast: the head of one donor, the torso of another,
the legs of a third, an optional beard, each palette-swapped. This tool bakes
the same composite OFFLINE into real sprite files, so someone who has no
hand-drawn sprites yet is still a first-class cast member — an NPC, a Menu →
Character entry, a figure in the title line-up, a blog author:

  assets/sprites/<name>_{front,back}_frame_{0..3}.png, <name>_side_frame_{0,1}.png
  config.json spriteMetadata <name>_front / _back / _side (cloned from a donor)
  config.json rooms.<room>.npcs — their base NPC (HOME below), added once

Everything that follows from having a sprite set is derived from that data
(CharacterSelect.available) — nothing else lists the cast.

The looks live in ONE place, LOOKS below: edit a donor or a colour and re-run.
The frames are a pure function of LOOKS and the donor sprites, so a re-run
with nothing changed rewrites identical files.

REPLACING AN INTERIM SET WITH REAL ART: drop the ten hand-drawn PNGs over the
generated ones (same names, 64x64, same template as the rest of the cast) and
remove that name from LOOKS so a later run does not overwrite them. No code or
config change is needed.

The compose logic is a line-for-line port of CharacterCreator.composePixels /
addSlot / inBeardBox (the five rules marked TIDY included); the donor
palettes, the beard donors and the cut rows are READ from CharacterCreator.js
(never copied here), so those cannot drift. The baked frames are
pixel-identical to the creator's preview of the same look — a unit test in
tools/test_game.js composes every look with the game's code and compares.
`--check` verifies the files on disk still match LOOKS.

Run from gamev2/ with a Python that has Pillow:

  /Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_cast.py
  ... tools/generate_cast.py --check            # exit 1 if a file is stale
  ... tools/generate_cast.py --sheet out.png    # contact sheet: whole cast, every frame
"""
import argparse
import json
import math
import os
import re
import sys

from PIL import Image

# ---------------------------------------------------------------- the looks
#
# name -> parts (which cast member lends the head / torso / legs / beard) and
# colours (hex, or None to keep the donor's own). Same shape as a creation
# saved by the character creator (`gamev2_custom_character`), so a look can
# be designed in the game's creator and copied here (the bake is what the
# creator previews).
#
# INTERIM looks for the devhouse 3 members (issue #117): nobody described
# what they look like, so these are deliberately neutral and only chosen to
# be told apart from each other and from the existing five at a glance.
LOOKS = {
    'khoi': {
        'parts': {'hair': 'james', 'top': 'damian', 'legs': 'bailey', 'beard': None},
        'colors': {'skin': '#f6c39a', 'hair': '#1a1208', 'top': '#3a6fd8', 'legs': '#2b2b33', 'beard': None},
    },
    'sam': {
        'parts': {'hair': 'dylan', 'top': 'bailey', 'legs': 'julia', 'beard': None},
        'colors': {'skin': '#fdcba2', 'hair': '#8a5a2b', 'top': '#7e4fc9', 'legs': '#8a5a2b', 'beard': None},
    },
    'xander': {
        'parts': {'hair': 'james', 'top': 'damian', 'legs': 'julia', 'beard': 'bailey'},
        'colors': {'skin': '#f4bc8e', 'hair': '#b0491f', 'top': '#d9d9d9', 'legs': '#032e48', 'beard': '#b0491f'},
    },
}

# Where each of them stands before their first blog post moves them
# (tools/blog_to_npc.py): room, cell, and what they say. The NPC is marked
# with the trip and the stay it is the base cast of (config.json "trips",
# src/utils/Trips.js: TRIP below, and the room as the stay), so it only
# stands there on that trip's dates while the group is based in that room.
# The rest of the devhouse 3 base cast (the other four in Sapporo, all seven
# in Asahikawa) is plain config data with the same marks. Added to config.json
# only while the room has no NPC of that name, so a position or line edited
# later (by hand, tools/npc_state.py or the blog pipeline) is never undone.
# The lines are placeholders: friendly, undated, and no facts about anyone.
HOME = {
    'khoi': ('Sapporo', 38, 8, [
        "Hey, I'm Khoi.",
        "Devhouse 3 is on: Hokkaido, in the snow.",
    ]),
    'sam': ('Sapporo', 20, 26, [
        "Hi, I'm Sam!",
        "Sapporo first, then Asahikawa. I'm looking forward to all of it.",
    ]),
    'xander': ('Sapporo', 35, 17, [
        "Xander here.",
        "Hokkaido with the devhouse crew. This should be a good one.",
    ]),
}

TRIP = 'devhouse3'              # the trip HOME is the base cast of

DIRS = ('front', 'back', 'side')
MOUTH = (0xe5, 0x3b, 0x44)      # the one mouth colour every cast sprite uses
GV2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(GV2, 'assets', 'sprites')
CREATOR_JS = os.path.join(GV2, 'src', 'CharacterCreator.js')


# ------------------------------------------- tables read from the creator

def creator_tables():
    """DONORS, BEARDS and CUTS as declared in CharacterCreator.js."""
    src = open(CREATOR_JS).read()

    def block(name, opener, closer):
        m = re.search(r'static %s = %s(.*?)\n    %s;' % (name, re.escape(opener), re.escape(closer)), src, re.S)
        if not m:
            sys.exit(f'generate_cast: cannot find `static {name}` in {CREATOR_JS}')
        return m.group(1)

    donors = {}
    for name, body in re.findall(r'^\s*(\w+):\s*\{(.*)\},?\s*$', block('DONORS', '{', '}'), re.M):
        donors[name] = {slot: re.findall(r'#[0-9a-fA-F]{6}', colours)
                        for slot, colours in re.findall(r'(\w+):\s*\[([^\]]*)\]', body)}
        if set(donors[name]) != {'skin', 'hair', 'top', 'legs'}:
            sys.exit(f'generate_cast: unexpected DONORS entry for {name}: {donors[name]}')
    cuts = {}
    for d, body in re.findall(r'^\s*(\w+):\s*\{(.*)\},?\s*$', block('CUTS', '{', '}'), re.M):
        cuts[d] = {k: [int(n) for n in re.findall(r'\d+', v)]
                   for k, v in re.findall(r'(\w+):\s*\[([^\]]*)\]', body)}
    m = re.search(r'static BEARDS = \[([^\]]*)\];', src)
    beards = re.findall(r"'(\w+)'", m.group(1)) if m else None
    if not donors or set(cuts) != set(DIRS) or not beards:
        sys.exit(f'generate_cast: could not read DONORS / CUTS / BEARDS from {CREATOR_JS}')
    return donors, beards, cuts


# ------------------------------------------------ colour maths (as the JS)

def js_round(v):
    return int(math.floor(v + 0.5))     # Math.round, not Python's banker's rounding


def hex_to_rgb(h):
    n = int(h[1:], 16)
    return ((n >> 16) & 255, (n >> 8) & 255, n & 255)


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0, 0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = ((g - b) / d + (6 if g < b else 0)) / 6
    elif mx == g:
        h = ((b - r) / d + 2) / 6
    else:
        h = ((r - g) / d + 4) / 6
    return h, s, l


def hsl_to_rgb(h, s, l):
    if s == 0:
        v = js_round(l * 255)
        return (v, v, v)

    def hue(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1 / 6: return p + (q - p) * 6 * t
        if t < 1 / 2: return q
        if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
        return p
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return tuple(js_round(hue(p, q, t) * 255) for t in (h + 1 / 3, h, h - 1 / 3))


def add_slot(mapping, srcs, chosen_hex):
    """Shade-preserving recolour of a slot (CharacterCreator.addSlot)."""
    if not srcs or not chosen_hex:
        return
    anchor = rgb_to_hsl(*hex_to_rgb(srcs[0]))
    chosen = rgb_to_hsl(*hex_to_rgb(chosen_hex))
    for src in srcs:
        s = rgb_to_hsl(*hex_to_rgb(src))
        l = min(0.97, max(0.04, chosen[2] + (s[2] - anchor[2])))
        mapping[hex_to_rgb(src)] = hsl_to_rgb(chosen[0], chosen[1], l)


def in_beard_box(d, frame, x, y):
    """CharacterCreator.inBeardBox."""
    if d == 'back':
        return False
    if d == 'front':
        off = (frame % 2) * 2
        return 28 + off <= y < 36 + off
    off = -2 if frame == 1 else 0
    return 26 + off <= y < 34 + off and x >= 22


# ------------------------------------------------------------ the compose

def frame_path(name, d, i):
    return os.path.join(SPRITES, f'{name}_{d}_frame_{i}.png')


def compose_frame(look, d, frame, tables):
    """One frame of a look (CharacterCreator.composePixels): legs band → torso
    band → head (+ trailing hair) → beard overlay, each part recoloured with
    its own donor-scoped palette map."""
    donors, beards, cuts = tables
    parts, colors = look['parts'], look['colors']
    top_start, bottom_start = cuts[d]['top'][frame], cuts[d]['bottom'][frame]

    src = {part: Image.open(frame_path(parts[part], d, frame)).convert('RGBA')
           for part in ('hair', 'top', 'legs')}
    if parts.get('beard'):
        src['beard'] = Image.open(frame_path(parts['beard'], d, frame)).convert('RGBA')
    W, H = src['hair'].size

    maps = {'hair': {}, 'top': {}, 'legs': {}, 'beard': {}}
    add_slot(maps['hair'], donors[parts['hair']]['skin'], colors.get('skin'))
    add_slot(maps['hair'], donors[parts['hair']]['hair'], colors.get('hair'))
    add_slot(maps['top'], donors[parts['top']]['skin'], colors.get('skin'))
    add_slot(maps['top'], donors[parts['top']]['top'], colors.get('top'))
    add_slot(maps['legs'], donors[parts['legs']]['skin'], colors.get('skin'))
    leg_def = donors[parts['legs']]
    leg_srcs = leg_def['legs'] + leg_def['top'] if leg_def['legs'] else leg_def['top']
    add_slot(maps['legs'], leg_srcs, colors.get('legs'))
    if parts.get('beard'):
        add_slot(maps['beard'], donors[parts['beard']]['hair'], colors.get('beard'))

    def classifier(donor):
        return {hex_to_rgb(h): slot for slot in ('skin', 'hair', 'top', 'legs') for h in donors[donor][slot]}

    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = out.load()
    data = {part: img.load() for part, img in src.items()}
    cls = {part: classifier(parts[part]) for part in src}

    def klass(part, x, y):
        """Slot of a donor pixel, '' for an opaque unclassified one (outline,
        eyes, mouth), None for transparent / out of frame."""
        if not (0 <= x < W and 0 <= y < H):
            return None
        r, g, b, a = data[part][x, y]
        return None if a == 0 else cls[part].get((r, g, b), '')

    def near(part, x, y, test):
        """Does any donor pixel within one art pixel (the cast is drawn on a
        2px grid) of (x,y) pass test(klass, x, y, rgb)?"""
        return any(test(klass(part, nx, ny), nx, ny, data[part][nx, ny][:3])
                   for ny in range(max(0, y - 2), min(H, y + 3))
                   for nx in range(max(0, x - 2), min(W, x + 3)))

    def each(part, fn, recolour=lambda x, y, c: True):
        for y in range(H):
            for x in range(W):
                r, g, b, a = data[part][x, y]
                if a == 0:
                    continue
                c = cls[part].get((r, g, b))
                if fn(x, y, c):
                    rgb = maps[part].get((r, g, b), (r, g, b)) if recolour(x, y, c) else (r, g, b)
                    px[x, y] = rgb + (a,)

    # The five TIDY rules below (the creator has the same five) clean up
    # what a plain band cut leaves behind when the parts come from different
    # donors.
    mixed_top = parts['top'] != parts['hair']

    # LEGS: everything from the waist down, plus this donor's legs-slot
    # pixels that poke above it
    each('legs', lambda x, y, c: c != 'hair' and (y >= bottom_start or (c == 'legs' and y >= top_start)))

    # TOP: the torso band, plus this donor's top-slot pixels above the
    # shoulder line. TIDY 1: where the top donor shows its own trousers
    # inside the torso band (damian's hem) and someone else's legs are worn,
    # nothing draws those pixels — fill the holes with the top's colour.
    top_anchor = hex_to_rgb(donors[parts['top']]['top'][0])
    for y in range(top_start, bottom_start):
        for x in range(W):
            if klass('top', x, y) == 'legs' and px[x, y][3] == 0:
                px[x, y] = maps['top'].get(top_anchor, top_anchor) + (255,)
    # TIDY 5a: the top donor's own long hair (julia) hangs into the torso
    # band and is not worn with the top — nor is the part of its outline
    # that touches nothing but that hair, a stray strand behind the shoulder.
    def strand_outline(x, y):
        return (mixed_top and klass('top', x, y) == ''
                and near('top', x, y, lambda k, nx, ny, _: k == 'hair')
                and not near('top', x, y, lambda k, nx, ny, _: k in ('skin', 'top', 'legs')))
    each('top', lambda x, y, c: c not in ('hair', 'legs')
         and ((top_start <= y < bottom_start) or (c == 'top' and y < top_start))
         and not strand_outline(x, y))

    # HEAD: everything above the shoulder line except this donor's own
    # clothing, plus hair pixels at ANY row.
    # TIDY 2: the outline of the head donor's own high sleeve (james, side
    # view) is not part of the head — with another top it is a stray tick.
    def sleeve_outline(x, y):
        return (mixed_top and klass('hair', x, y) == ''
                and near('hair', x, y, lambda k, nx, ny, _: k == 'top' and ny < top_start)
                and not near('hair', x, y, lambda k, nx, ny, _: k in ('skin', 'hair')))
    # TIDY 3: hair-coloured pixels touching the mouth are the inside of an
    # open mouth (dylan), not hair — recoloured they read as a moustache that
    # comes and goes with the walk cycle. Heads with facial hair are exempt:
    # there the pixels round the mouth really are beard.
    def mouth_inside(x, y, c):
        return (c == 'hair' and parts['hair'] not in beards
                and near('hair', x, y, lambda k, nx, ny, rgb: rgb == MOUTH))
    each('hair', lambda x, y, c: c not in ('top', 'legs') and (y < top_start or c == 'hair')
         and not sleeve_outline(x, y),
         recolour=lambda x, y, c: not mouth_inside(x, y, c))

    # TIDY 4: close the shoulder line. The row of outline above the torso
    # band comes from the head donor; where its shoulders are narrower than
    # the top worn, the top's upper edge is left bare — borrow those outline
    # pixels from the top donor.
    if mixed_top:
        for y in range(max(0, top_start - 2), top_start):
            for x in range(W):
                if px[x, y][3] == 0 and klass('top', x, y) == '' and px[x, y + 2][3] != 0 \
                        and klass('top', x, y + 2) == 'top':
                    px[x, y] = data['top'][x, y]

    # TIDY 5b: where that hair covered the back of the shirt, nothing drew
    # it: a see-through hole under the new head, over the hair's lower
    # outline. Fill what is enclosed with the top's colour, and turn the
    # outline right under it into shirt too.
    if mixed_top:
        # flood the transparent background in from the border: what is left is a hole
        outside = set()
        stack = [(x, y) for x in range(W) for y in (0, H - 1)] + [(x, y) for y in range(H) for x in (0, W - 1)]
        while stack:
            x, y = stack.pop()
            if (x, y) in outside or not (0 <= x < W and 0 <= y < H) or px[x, y][3] != 0:
                continue
            outside.add((x, y))
            stack += [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        filled = set()
        for y in range(top_start, bottom_start):
            for x in range(W):
                hole = klass('top', x, y) == 'hair' and px[x, y][3] == 0 and (x, y) not in outside
                if hole or (klass('top', x, y) == '' and (x, y - 2) in filled):
                    px[x, y] = maps['top'].get(top_anchor, top_anchor) + (255,)
                    if hole:
                        filled.add((x, y))

    # BEARD: the donor's facial-hair pixels, on top of the new face
    if parts.get('beard'):
        each('beard', lambda x, y, c: c == 'hair' and in_beard_box(d, frame, x, y))
    return out


def frame_counts(cfg, donor):
    sm = cfg['spriteMetadata']
    return {d: sm[f'{donor}_{d}']['frameCount'] for d in DIRS}


def base_npc(name, x, y, dialogue, room_key):
    """A cast NPC definition — the shape roomgen.make_npc writes — scoped to
    the trip and the stay (the room) it is the base cast of."""
    return {'name': name.capitalize(), 'sprite': f'{name}_front', 'gridX': x, 'gridY': y,
            'trip': TRIP, 'stay': room_key,
            'gridOffsetX': 0, 'gridOffsetY': 0, 'dialogue': dialogue,
            'directionalSprites': {'up': f'{name}_back', 'down': f'{name}_front',
                                   'left': '', 'right': f'{name}_side'},
            'autoFlip': {'horizontal': True, 'vertical': False}}


def validate(tables):
    donors, beards, _ = tables
    for name, look in LOOKS.items():
        if not re.fullmatch(r'[a-z]+', name) or name in donors or name == 'custom':
            sys.exit(f'generate_cast: bad look name {name!r} (lowercase letters, not an existing donor)')
        for part in ('hair', 'top', 'legs'):
            if look['parts'].get(part) not in donors:
                sys.exit(f'generate_cast: {name}: unknown {part} donor {look["parts"].get(part)!r}')
        if look['parts'].get('beard') and look['parts']['beard'] not in beards:
            sys.exit(f'generate_cast: {name}: {look["parts"]["beard"]!r} has no beard to lend')


def contact_sheet(cfg, path, scale=4):
    """Every frame of every cast member with a full sprite set, one per row."""
    sm = cfg['spriteMetadata']
    names = sorted(k[:-6] for k in sm if k.endswith('_front') and f'{k[:-6]}_back' in sm and f'{k[:-6]}_side' in sm)
    cols = [(d, i) for d in DIRS for i in range(max(sm[f'{n}_{d}']['frameCount'] for n in names))]
    sheet = Image.new('RGBA', (len(cols) * 64 * scale, len(names) * 64 * scale), (96, 112, 128, 255))
    for r, n in enumerate(names):
        for c, (d, i) in enumerate(cols):
            if not os.path.exists(frame_path(n, d, i)):
                continue
            im = Image.open(frame_path(n, d, i)).convert('RGBA').resize((64 * scale, 64 * scale), Image.NEAREST)
            sheet.alpha_composite(im, (c * 64 * scale, r * 64 * scale))
    sheet.save(path)
    print(f'contact sheet: {path} (rows: {", ".join(names)})')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='verify the files on disk match LOOKS; write nothing')
    ap.add_argument('--sheet', metavar='PNG', help='also write a contact sheet of the whole cast')
    args = ap.parse_args()

    tables = creator_tables()
    validate(tables)
    cfg_path = os.path.join(GV2, 'config.json')
    cfg = json.load(open(cfg_path))
    sm = cfg['spriteMetadata']

    stale, wrote, registered = [], 0, []
    for name, look in LOOKS.items():
        donor = look['parts']['hair']       # frame counts / metadata follow the head donor, as the creator does
        for d, count in frame_counts(cfg, donor).items():
            for i in range(count):
                img, path = compose_frame(look, d, i, tables), frame_path(name, d, i)
                same = os.path.exists(path) and Image.open(path).convert('RGBA').tobytes() == img.tobytes()
                if same:
                    continue
                if args.check:
                    stale.append(os.path.relpath(path, GV2))
                else:
                    img.save(path, optimize=True)
                    wrote += 1
            key = f'{name}_{d}'
            if key not in sm:
                if args.check:
                    stale.append(f'config.json spriteMetadata.{key}')
                else:
                    sm[key] = json.loads(json.dumps(sm[f'{donor}_{d}']))
                    registered.append(key)

    placed = []
    for name, (room_key, x, y, dialogue) in HOME.items():
        if name not in LOOKS:
            sys.exit(f'generate_cast: HOME names {name!r}, who has no look')
        npcs = cfg['rooms'][room_key].setdefault('npcs', [])
        if any(n['name'].lower() == name for n in npcs):
            continue
        if args.check:
            stale.append(f'config.json rooms.{room_key}.npcs: {name.capitalize()}')
        else:
            npcs.append(base_npc(name, x, y, dialogue, room_key))
            placed.append(f'{name.capitalize()} in {room_key} at ({x},{y})')

    if args.check:
        for s in stale:
            print(f'STALE {s}')
        print(f'generate_cast --check: {len(LOOKS)} look(s), {len(stale)} stale')
        return 1 if stale else 0

    if registered or placed:
        # the project's config format (see blog_to_npc.save_config)
        open(cfg_path, 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    print(f'generate_cast: {", ".join(LOOKS)} — {wrote} frame(s) written, '
          f'{len(registered)} spriteMetadata key(s) added'
          + (f', base NPC(s) added: {"; ".join(placed)}' if placed else ''))
    if args.sheet:
        contact_sheet(cfg, args.sheet)
    return 0


if __name__ == '__main__':
    sys.exit(main())
