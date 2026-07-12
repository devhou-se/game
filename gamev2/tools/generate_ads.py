#!/usr/bin/env python3
"""generate_ads.py — the advertisement-signage pool (issue #26).

Japanese streets are crammed with dense, noisy business signage. This tool
renders that feeling into a pool of small pixel-art ad images that the game
mounts on building walls at runtime (RoomManager.placeSignage picks randomly
from the pool per room load, so every visit looks a little different).

Shapes match the patterns Damian called out on the issue — single squares,
vertical rectangles, horizontal rectangles, and 2x2 billboards — one grid
cell is 64px:

    square 64x64 · tall 64x128 · wide 128x64 · big 128x128

Two spec sources:
  * The builtin pool below — ad copy, palettes and motifs designed by Claude
    at authoring time (an offline batch of the "AI generates the images"
    plan; no konbini branding, that's reserved to mark enterable stores).
  * --claude N asks Claude (Sonnet) for N extra unique specs at run time.
    Needs ANTHROPIC_API_KEY — meant for ad-hoc bulk jobs, not the web build.

Run from gamev2/:

    python3 tools/generate_ads.py            # render pool + manifest
    python3 tools/generate_ads.py --claude 40

Output: assets/ads/<shape>-<nn>.png + assets/ads/manifest.json
"""
import argparse
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont

GS = 64
SHAPES = {'square': (1, 1), 'tall': (1, 2), 'wide': (2, 1), 'big': (2, 2)}

# Classic Japanese signage palettes: [background, text, accent]
PALETTES = {
    'aka':     ['#c62828', '#ffffff', '#ffd54f'],   # red / white / gold
    'shiro':   ['#f5f0e6', '#b71c1c', '#263238'],   # white / red / ink
    'kuro':    ['#1c1c22', '#ffd54f', '#ef5350'],   # black / gold / red
    'ao':      ['#1155a8', '#ffffff', '#ffd54f'],   # blue / white / gold
    'midori':  ['#1b7a3d', '#ffffff', '#ffe082'],   # green / white / cream
    'kiiro':   ['#f9c22e', '#212121', '#c62828'],   # yellow / ink / red
    'murasaki': ['#5e3591', '#ffffff', '#ffab40'],  # purple / white / orange
    'orenji':  ['#e2711d', '#ffffff', '#1c1c22'],   # orange / white / ink
    'pinku':   ['#d81b60', '#ffffff', '#ffe082'],   # pink / white / cream
    'konai':   ['#20323e', '#7fd4ff', '#ffffff'],   # night blue / neon
}

# The builtin pool: Claude-authored ads for the crammed-street feel.
# text renders vertically on tall signs, horizontally otherwise; sub is the
# small second line (price, hours, a hook). No konbini names — reserved.
SPECS = [
    # --- squares: one bold word, a lantern-tag feel ---
    dict(shape='square', text='酒', sub=None, pal='aka', motif='lantern'),
    dict(shape='square', text='寿司', sub='¥100', pal='shiro', motif='fish'),
    dict(shape='square', text='湯', sub=None, pal='ao', motif='steam'),
    dict(shape='square', text='薬', sub=None, pal='midori', motif='cross'),
    dict(shape='square', text='呑', sub=None, pal='kuro', motif='mug'),
    dict(shape='square', text='麺', sub=None, pal='kiiro', motif='bowl'),
    dict(shape='square', text='歌', sub='24h', pal='murasaki', motif='note'),
    dict(shape='square', text='肉', sub=None, pal='orenji', motif='flame'),
    dict(shape='square', text='茶', sub=None, pal='midori', motif='steam'),
    dict(shape='square', text='占い', sub=None, pal='konai', motif='star'),
    dict(shape='square', text='本', sub=None, pal='shiro', motif=None),
    dict(shape='square', text='質', sub=None, pal='kuro', motif='coin'),
    # --- talls: vertical banners, the alley classic ---
    dict(shape='tall', text='居酒屋', sub=None, pal='aka', motif='lantern'),
    dict(shape='tall', text='ラーメン', sub=None, pal='kuro', motif='bowl'),
    dict(shape='tall', text='カラオケ', sub='24h', pal='murasaki', motif='note'),
    dict(shape='tall', text='焼肉', sub='食放', pal='orenji', motif='flame'),
    dict(shape='tall', text='パチンコ', sub=None, pal='kiiro', motif='star'),
    dict(shape='tall', text='喫茶店', sub=None, pal='shiro', motif='steam'),
    dict(shape='tall', text='麻雀', sub='3F', pal='midori', motif=None),
    dict(shape='tall', text='スナック', sub=None, pal='pinku', motif='star'),
    dict(shape='tall', text='うなぎ', sub=None, pal='kuro', motif='fish'),
    dict(shape='tall', text='ホテル', sub=None, pal='konai', motif=None),
    dict(shape='tall', text='金物屋', sub=None, pal='ao', motif=None),
    dict(shape='tall', text='ビール', sub='¥290', pal='kiiro', motif='mug'),
    # --- wides: shopfront boards, prices, hooks ---
    dict(shape='wide', text='ラーメン一番', sub='豚骨 ¥850', pal='aka', motif='bowl'),
    dict(shape='wide', text='回転寿司', sub='一皿 ¥100', pal='shiro', motif='fish'),
    dict(shape='wide', text='のみほうだい', sub='90分 ¥980', pal='kuro', motif='mug'),
    dict(shape='wide', text='カラオケ星', sub='フリータイム', pal='murasaki', motif='note'),
    dict(shape='wide', text='電器のヤマ', sub='大安売り!', pal='ao', motif='bolt'),
    dict(shape='wide', text='純喫茶ローズ', sub='モーニング', pal='pinku', motif='steam'),
    dict(shape='wide', text='うどん処', sub='かけ ¥390', pal='kiiro', motif='bowl'),
    dict(shape='wide', text='餃子の王', sub='6個 ¥260', pal='orenji', motif='flame'),
    dict(shape='wide', text='たい焼き', sub='1個 ¥180', pal='shiro', motif='fish'),
    dict(shape='wide', text='サウナ富士', sub='朝風呂あり', pal='ao', motif='steam'),
    dict(shape='wide', text='ゲーセンUFO', sub='新台入荷', pal='konai', motif='star'),
    dict(shape='wide', text='とんかつ勝', sub='定食 ¥1100', pal='kuro', motif=None),
    dict(shape='wide', text='古本まつり', sub='3冊 ¥500', pal='midori', motif=None),
    dict(shape='wide', text='歯科クリニック', sub='予約制', pal='shiro', motif='cross'),
    # --- bigs: 2x2 billboards ---
    dict(shape='big', text='ストロング', sub='祭り開催中', pal='konai', motif='mug'),
    dict(shape='big', text='ノミカイ', sub='挑戦者求む', pal='aka', motif='lantern'),
    dict(shape='big', text='ウイスキー', sub='バー2F', pal='kuro', motif='mug'),
    dict(shape='big', text='温泉旅館', sub='日帰りOK', pal='ao', motif='steam'),
    dict(shape='big', text='歳末セール', sub='全品半額', pal='kiiro', motif='star'),
    dict(shape='big', text='映画祭', sub='今週末', pal='murasaki', motif='star'),
]


def find_font():
    """First present JP-capable font. Bold-ish weight where the TTC allows."""
    candidates = [
        ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2),   # W6 weight index
        ('/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
        ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 0),
        ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 0),
    ]
    for path, index in candidates:
        if os.path.exists(path):
            try:
                ImageFont.truetype(path, 40, index=index)
                return path, index
            except OSError:
                continue
    raise SystemExit('no JP-capable font found — add one to find_font()')


FONT_PATH, FONT_INDEX = None, None


def text_bitmap(text, px, color):
    """Render text at 4x then NEAREST-downscale: chunky pixel glyphs."""
    big = px * 4
    font = ImageFont.truetype(FONT_PATH, big, index=FONT_INDEX)
    l, t, r, b = font.getbbox(text)
    img = Image.new('RGBA', (max(1, r - l), max(1, b - t)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((-l, -t), text, font=font, fill=color)
    return img.resize((max(1, img.width // 4), max(1, img.height // 4)), Image.NEAREST)


def fit_text(text, max_w, max_h, color):
    """Largest pixel-text that fits the box."""
    for px in range(max_h, 5, -1):
        img = text_bitmap(text, px, color)
        if img.width <= max_w and img.height <= max_h:
            return img
    return text_bitmap(text, 6, color)


def paste_center(canvas, img, cx, cy):
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def draw_motif(d, motif, cx, cy, s, color, accent):
    """Tiny pixel glyph; s is the half-size in px."""
    if motif == 'lantern':
        d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=color)
        d.rectangle([cx - s // 2, cy - s - 3, cx + s // 2, cy - s], fill=accent)
        d.rectangle([cx - s // 2, cy + s, cx + s // 2, cy + s + 3], fill=accent)
        d.line([cx, cy - s + 2, cx, cy + s - 2], fill=accent, width=2)
    elif motif == 'bowl':
        d.pieslice([cx - s, cy - s // 2, cx + s, cy + s + 2], 0, 180, fill=color)
        d.line([cx - s + 2, cy - 2, cx + s - 2, cy - 2], fill=accent, width=2)
        d.line([cx - s // 2, cy - s, cx - s // 4, cy - 2], fill=color, width=2)
        d.line([cx + s // 4, cy - s, cx + s // 2, cy - 2], fill=color, width=2)
    elif motif == 'mug':
        d.rectangle([cx - s + 2, cy - s // 2, cx + s - 4, cy + s], fill=color)
        d.rectangle([cx + s - 4, cy - s // 4, cx + s, cy + s // 2], outline=color, width=2)
        d.rectangle([cx - s + 2, cy - s // 2 - 3, cx + s - 4, cy - s // 2], fill=accent)
    elif motif == 'fish':
        d.ellipse([cx - s, cy - s // 2, cx + s - 4, cy + s // 2], fill=color)
        d.polygon([cx + s - 6, cy, cx + s, cy - s // 2, cx + s, cy + s // 2], fill=color)
        d.point([cx - s + 4, cy - 2], fill=accent)
    elif motif == 'note':
        d.ellipse([cx - s + 1, cy + s // 2 - 3, cx - 2, cy + s + 2], fill=color)
        d.line([cx - 3, cy - s, cx - 3, cy + s - 1], fill=color, width=2)
        d.line([cx - 3, cy - s, cx + s - 2, cy - s + 4], fill=color, width=3)
    elif motif == 'flame':
        d.polygon([cx, cy - s, cx + s - 2, cy + s // 2, cx, cy + s, cx - s + 2, cy + s // 2], fill=color)
        d.polygon([cx, cy - s // 3, cx + s // 3, cy + s // 2, cx, cy + s - 2, cx - s // 3, cy + s // 2], fill=accent)
    elif motif == 'star':
        pts = [(cx, cy - s), (cx + s // 3, cy - s // 4), (cx + s, cy - s // 4), (cx + s // 2, cy + s // 4),
               (cx + 2 * s // 3, cy + s), (cx, cy + s // 2), (cx - 2 * s // 3, cy + s),
               (cx - s // 2, cy + s // 4), (cx - s, cy - s // 4), (cx - s // 3, cy - s // 4)]
        d.polygon(pts, fill=color)
    elif motif == 'steam':
        for dx in (-s // 2, s // 2):
            d.arc([cx + dx - 3, cy - s, cx + dx + 3, cy], 90, 270, fill=color, width=2)
            d.arc([cx + dx - 3, cy - s // 3, cx + dx + 3, cy + s // 2], 270, 90, fill=color, width=2)
    elif motif == 'cross':
        d.rectangle([cx - s // 3, cy - s, cx + s // 3, cy + s], fill=color)
        d.rectangle([cx - s, cy - s // 3, cx + s, cy + s // 3], fill=color)
    elif motif == 'bolt':
        d.polygon([cx + s // 3, cy - s, cx - s // 2, cy + s // 4, cx - 2, cy + s // 4,
                   cx - s // 3, cy + s, cx + s // 2, cy - s // 4, cx + 2, cy - s // 4], fill=color)
    elif motif == 'coin':
        d.ellipse([cx - s, cy - s, cx + s, cy + s], outline=color, width=3)
        d.rectangle([cx - s // 2, cy - 2, cx + s // 2, cy + 2], fill=color)


def render(spec, rng):
    """One spec -> RGBA sign image, frame included."""
    w, h = (SHAPES[spec['shape']][0] * GS, SHAPES[spec['shape']][1] * GS)
    bg, fg, accent = PALETTES[spec['pal']]
    img = Image.new('RGBA', (w, h), bg)
    d = ImageDraw.Draw(img)

    # frame: dark outer edge + a bright inner keyline reads "sign" at 64px
    edge = '#141017'
    d.rectangle([0, 0, w - 1, h - 1], outline=edge, width=2)
    d.rectangle([2, 2, w - 3, h - 3], outline=accent, width=1)

    # marquee bulbs on some signs (the pachinko/game-center feel)
    if spec['motif'] in ('star', 'bolt') or rng.random() < 0.25:
        for x in range(8, w - 8, 8):
            d.rectangle([x, 4, x + 1, 5], fill=accent)
            d.rectangle([x, h - 6, x + 1, h - 5], fill=accent)

    pad = 7
    if spec['shape'] == 'tall':
        # vertical banner: one character per row, top-down
        chars = list(spec['text'])
        cell_h = (h - 2 * pad - (12 if spec['sub'] else 0)) // max(1, len(chars))
        for i, ch in enumerate(chars):
            glyph = fit_text(ch, w - 2 * pad - 4, cell_h - 2, fg)
            paste_center(img, glyph, w / 2, pad + cell_h * i + cell_h / 2)
        if spec['sub']:
            paste_center(img, fit_text(spec['sub'], w - 2 * pad, 11, accent), w / 2, h - pad - 5)
        if spec['motif']:
            draw_motif(d, spec['motif'], w // 2, h - pad - (18 if not spec['sub'] else 26), 5, accent, fg)
    elif spec['shape'] == 'big':
        # billboard: big motif band, big text, sub tucked right below it
        top = pad
        if spec['motif']:
            draw_motif(d, spec['motif'], w // 2, pad + 20, 12, accent, fg)
            top = pad + 40
        avail = h - top - pad - (16 if spec['sub'] else 0)
        glyph = fit_text(spec['text'], w - 2 * pad, min(44, avail), fg)
        cy = top + avail / 2
        paste_center(img, glyph, w / 2, cy)
        if spec['sub']:
            paste_center(img, fit_text(spec['sub'], w - 2 * pad, 14, accent),
                         w / 2, cy + glyph.height / 2 + 12)
    else:
        motif_room = 16 if spec['motif'] else 0
        text_h = 22 if spec['shape'] == 'square' else 26
        cy = pad + (h - 2 * pad - (12 if spec['sub'] else 0)) / 2
        if spec['motif']:
            draw_motif(d, spec['motif'], w // 2, int(pad + 12), 7, accent, fg)
            cy += 6
        glyph = fit_text(spec['text'], w - 2 * pad, min(text_h, h - 2 * pad - motif_room), fg)
        paste_center(img, glyph, w / 2, cy)
        if spec['sub']:
            paste_center(img, fit_text(spec['sub'], w - 2 * pad, 12, accent), w / 2, h - pad - 6)
    return img


def claude_specs(n):
    """Ask Claude for n extra unique ad specs (ad-hoc bulk jobs, needs key)."""
    import anthropic
    client = anthropic.Anthropic(max_retries=5)
    schema = {
        'type': 'object',
        'properties': {'ads': {'type': 'array', 'items': {
            'type': 'object',
            'properties': {
                'shape': {'type': 'string', 'enum': list(SHAPES)},
                'text': {'type': 'string'},
                'sub': {'type': ['string', 'null']},
                'pal': {'type': 'string', 'enum': list(PALETTES)},
                'motif': {'type': ['string', 'null'],
                          'enum': ['lantern', 'bowl', 'mug', 'fish', 'note', 'flame',
                                   'star', 'steam', 'cross', 'bolt', 'coin', None]},
            },
            'required': ['shape', 'text', 'sub', 'pal', 'motif'],
            'additionalProperties': False,
        }}},
        'required': ['ads'], 'additionalProperties': False,
    }
    system = (
        'You design tiny Japanese street-advertisement signs for a pixel-art '
        'game. Each ad is a JSON spec. text is the sign copy in Japanese — '
        'BOLD and SHORT (tall signs: max 5 characters, they stack vertically; '
        'square: 1-2 characters; wide/big: max 7). sub is an optional price, '
        'hours or hook (max 8 chars). Vary business types: food, drink, '
        'baths, games, services, sales. Never any convenience-store brand.'
    )
    resp = client.messages.create(
        model='claude-sonnet-5', max_tokens=8000, thinking={'type': 'disabled'},
        system=system,
        messages=[{'role': 'user', 'content': f'Design {n} unique ad specs.'}],
        output_config={'format': {'type': 'json_schema', 'schema': schema}},
    )
    text = next(b.text for b in resp.content if b.type == 'text')
    return json.loads(text)['ads'][:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='assets/ads')
    ap.add_argument('--claude', type=int, default=0, metavar='N',
                    help='also generate N specs live via Claude (needs ANTHROPIC_API_KEY)')
    ap.add_argument('--seed', type=int, default=26)
    args = ap.parse_args()

    global FONT_PATH, FONT_INDEX
    FONT_PATH, FONT_INDEX = find_font()
    rng = random.Random(args.seed)
    specs = list(SPECS) + (claude_specs(args.claude) if args.claude else [])

    os.makedirs(args.out, exist_ok=True)
    manifest, counters = [], {}
    for spec in specs:
        n = counters[spec['shape']] = counters.get(spec['shape'], 0) + 1
        name = f"{spec['shape']}-{n:02d}"
        render(spec, rng).save(f'{args.out}/{name}.png')
        cw, ch = SHAPES[spec['shape']]
        manifest.append({'key': f'ad-{name}', 'file': f'{name}.png',
                         'shape': spec['shape'], 'w': cw, 'h': ch})
    with open(f'{args.out}/manifest.json', 'w') as f:
        json.dump({'ads': manifest}, f, indent=1)
    print(f"{len(manifest)} ads -> {args.out} "
          f"({', '.join(f'{v} {k}' for k, v in sorted(counters.items()))})")


if __name__ == '__main__':
    main()
