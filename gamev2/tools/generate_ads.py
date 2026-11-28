#!/usr/bin/env python3
"""generate_ads.py — the advertisement-signage pool (issues #26, #279).

Japanese streets are crammed with dense, noisy business signage. This tool
renders that feeling into a pool of small pixel-art ad images that the game
mounts on building walls at runtime (RoomManager.placeSignage picks randomly
from the pool per room load, so every visit looks a little different).

Shapes match the patterns Damian called out on the issue — single squares,
vertical rectangles, horizontal rectangles, and 2x2 billboards — one grid
cell is 64px in the game, drawn at half size (32px) and doubled:

    square 64x64 · tall 64x128 · wide 128x64 · big 128x128

A board is drawn in the house look (docs/generators-and-checks.md, "House
look: GuttyKreum"; the helpers are tools/house_look.py), the way the sheets'
own sign boards are: an ink outline with its corners clear; a steel housing,
its lip lightest; the lip's shadow on the face; a face that is never flat (a
lit box in scanlines, a painted board shaded); text in the game's PixelMplus12
at 12px, with a band for the sub along the bottom. A big has a picture panel.
Each shape has a fixed layout and a budget (render); a spec that does not fit
raises, naming it.

Two spec sources:
  * The builtin pool below — ad copy, palettes and motifs designed by Claude
    at authoring time (an offline batch of the "AI generates the images"
    plan; no konbini branding, that's reserved to mark enterable stores).
  * --claude N asks Claude (Sonnet) for N extra unique specs at run time.
    Needs ANTHROPIC_API_KEY — meant for ad-hoc bulk jobs, not the web build.

Run from gamev2/:

    python3 tools/generate_ads.py            # render pool + manifest
    python3 tools/generate_ads.py --sheet /tmp/ads.png   # ...and a contact sheet of it
    python3 tools/generate_ads.py --claude 40

Output: assets/ads/<shape>-<nn>.png + assets/ads/manifest.json
"""
import argparse
import json
import os

from PIL import Image, ImageDraw, ImageFont

import house_look as hl
from house_look import rgb

GS = 64
C = GS // 2                 # a cell at half size
SHAPES = {'square': (1, 1), 'tall': (1, 2), 'wide': (2, 1), 'big': (2, 2)}

# A board's parts per palette. face: ('painted', ramp, i) is shaded, ('lit', a, b) is
# scanlines of two tones; title: its colour and shadow (none when the title is darker
# than its face); band: the sub's band (ramp, i) and the sub's colour.
PALETTES = {
    'aka':      dict(face=('painted', 'red', 2), title=('fafcfd', '8a3a22'), band=('gold', 2), sub='172459'),
    'shiro':    dict(face=('painted', 'cream', 2), title=('aa4d31', None), band=('red', 2), sub='fafcfd'),
    'kuro':     dict(face=('lit', '191c2a', '0a1627'), title=('f3d890', '080d16'), band=('red', 2), sub='fafcfd'),
    'ao':       dict(face=('lit', '425faa', '314b8e'), title=('fafcfd', '172459'), band=('gold', 2), sub='172459'),
    'midori':   dict(face=('painted', 'green', 2), title=('fafcfd', '2e4040'), band=('cream', 2), sub='2e4040'),
    'kiiro':    dict(face=('painted', 'gold', 2), title=('172459', None), band=('red', 2), sub='fafcfd'),
    'murasaki': dict(face=('lit', '444679', '3c396d'), title=('c9cbff', '2a233b'), band=('orange', 2), sub='ffe2e0'),
    'orenji':   dict(face=('painted', 'orange', 2), title=('fafcfd', '904a37'), band=('night', 2), sub='f3d890'),
    'pinku':    dict(face=('painted', 'pink', 1), title=('ffe2e0', '83374f'), band=('cream', 2), sub='83374f'),
    'konai':    dict(face=('lit', '2c2d51', '191c2a'), title=('7db9fa', '0a1627'), band=('blue', 2), sub='bbe9ff'),
}
# the steel housing, as the sheets' boxes have it: the lip lightest, the far sides darkest
LIP, LEFT, BOTTOM, RIGHT = rgb('dae2e4'), rgb('a4b0b5'), rgb('47485d'), rgb('575f79')
BAND = 13                   # the sub's band: a lit top row and the 12 rows of the text

# The builtin pool: Claude-authored ads for the crammed-street feel.
# text renders vertically on tall signs, horizontally otherwise; sub is the
# small second line (price, hours, a hook), on the band. A big's motif names its
# picture (PICTURES). No konbini names — reserved.
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
    dict(shape='tall', text='カラオケ', sub=None, pal='murasaki', motif='note'),
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
    dict(shape='wide', text='麺屋一番', sub='豚骨 ¥850', pal='aka', motif='bowl'),
    dict(shape='wide', text='回転寿司', sub='一皿 ¥100', pal='shiro', motif='fish'),
    dict(shape='wide', text='飲み放題', sub='90分 ¥980', pal='kuro', motif='mug'),
    dict(shape='wide', text='カラオケ星', sub='歌い放題', pal='murasaki', motif='note'),
    dict(shape='wide', text='電器のヤマ', sub='大安売り!', pal='ao', motif='bolt'),
    dict(shape='wide', text='喫茶ローズ', sub='モーニング', pal='pinku', motif='steam'),
    dict(shape='wide', text='うどん処', sub='かけ ¥390', pal='kiiro', motif='bowl'),
    dict(shape='wide', text='餃子の王', sub='6個 ¥260', pal='orenji', motif='flame'),
    dict(shape='wide', text='たい焼き', sub='1個 ¥180', pal='shiro', motif='fish'),
    dict(shape='wide', text='サウナ富士', sub='朝風呂あり', pal='ao', motif='steam'),
    dict(shape='wide', text='ゲーセン', sub='新台入荷', pal='konai', motif='star'),
    dict(shape='wide', text='とんかつ勝', sub='定食 ¥1100', pal='kuro', motif=None),
    dict(shape='wide', text='古本まつり', sub='3冊 ¥500', pal='midori', motif=None),
    dict(shape='wide', text='歯科医院', sub='予約制', pal='shiro', motif='cross'),
    # --- bigs: 2x2 billboards ---
    dict(shape='big', text='ストロング', sub='祭り開催中', pal='konai', motif='can'),
    dict(shape='big', text='ノミカイ', sub='挑戦者求む', pal='aka', motif='lantern'),
    dict(shape='big', text='ウイスキー', sub='バー2F', pal='kuro', motif='glass'),
    dict(shape='big', text='温泉旅館', sub='日帰りOK', pal='ao', motif='onsen'),
    dict(shape='big', text='歳末セール', sub='全品半額', pal='kiiro', motif='burst'),
    dict(shape='big', text='映画祭', sub='今週末', pal='murasaki', motif='reel'),
]


# ---- the old text helpers ---------------------------------------------------------
# Kept as they were for tools/extract_city.py's Don Takote sign, which still sets its
# text in a system font (and so is checked only where one is readable); the ads
# themselves no longer use them.
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
    raise SystemExit('no JP-capable font found (looked for ' +
                     ', '.join(sorted({os.path.basename(p) for p, _ in candidates})) +
                     ' — unreadable in a sandboxed shell); run where the system fonts '
                     'are readable, or add one to find_font()')


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



# ---- motifs and pictures, set by hand ---------------------------------------------------
# A small motif is in the title's colour (T) with the board's accent (a: the band's tone)
# and the face's line tone (d), and takes the title's shadow.
MOTIFS = {
    'lantern': ['..dddd..',
                '.TTTTTT.',
                'TTTTTTTT',
                'dddddddd',
                'TTTTTTTT',
                'TTTTTTTT',
                'dddddddd',
                'TTTTTTTT',
                '.TTTTTT.',
                '..dddd..'],
    'bowl':    ['.......T.T',
                '......T.T.',
                '.....T.T..',
                'aaaaaaaaaa',
                'TTTTTTTTTT',
                'TTTTTTTTTT',
                '.TTTTTTTT.',
                '..TTTTTT..',
                '...dddd...'],
    'mug':     ['aaaaaaa...',
                'aaaaaaa...',
                'TTTTTTTTT.',
                'TTTTTTT..T',
                'TTTTTTT..T',
                'TTTTTTT..T',
                'TTTTTTTTT.',
                'TTTTTTT...',
                'TTTTTTT...',
                '.ddddd....'],
    'fish':    ['..TTTTT...',
                '.TTTTTTT.T',
                'TdTTTTTTTT',
                'TTTTTTTTTT',
                '.TTTTTTT.T',
                '..TTTTT...'],
    'note':    ['..TTTTTT',
                '..TTTTTT',
                '..T....T',
                '..T....T',
                '..T....T',
                '.TT...TT',
                'TTT..TTT',
                'TTT..TTT',
                '.T....T.'],
    'flame':   ['...T....',
                '...TT...',
                '..TTT...',
                '..TTTT.T',
                '.TTaTTTT',
                '.TTaaTTT',
                'TTaaaaTT',
                'TTaaaaTT',
                '.TTaaTT.',
                '..TTTT..'],
    'star':    ['....T....',
                '....T....',
                '...TTT...',
                'TTTTTTTTT',
                '.TTTTTTT.',
                '..TTTTT..',
                '..TTTTT..',
                '.TT...TT.',
                '.T.....T.'],
    'steam':   ['.T...T..',
                'T...T...',
                'T...T...',
                '.T...T..',
                '..T...T.',
                '..T...T.',
                '.T...T..',
                'T...T...'],
    'cross':   ['...TTT...',
                '...TTT...',
                '...TTT...',
                'TTTTTTTTT',
                'TTTTTTTTT',
                'TTTTTTTTT',
                '...TTT...',
                '...TTT...',
                '...TTT...'],
    'bolt':    ['....TTT',
                '...TTT.',
                '..TTT..',
                '.TTT...',
                'TTTTTTT',
                '...TTT.',
                '..TTT..',
                '.TTT...',
                '.TT....',
                '.T.....'],
    'coin':    ['...TTTT...',
                '.TTTTTTTT.',
                '.TTTTTTTT.',
                'TTT....TTT',
                'TTT....TTT',
                'TTT....TTT',
                'TTT....TTT',
                '.TTTTTTTT.',
                '.TTTTTTTT.',
                '...TTTT...'],
}

# The bigs' pictures (30x28 at most): their own colours, inked round when set on the panel.
_CAN = ['..hhhhhhhhhh..',
        '.hssssssssssm.',
        'hhmmmmmmmmmmmm',
        'hhssssssssssmm',
        'hhssssssssssmm',
        'eerrrrrrrrrrRR',
        'eerrrrrrrrrrRR',
        'ehhhhhhhhhhhRR',
        'eerrrrrrrrrrRR',
        'eerryyyyyrrrRR',
        'eeryyYyYyyrrRR',
        'eeyyYyyyYyyrRR',
        'eeyYYYyYYYyrRR',
        'eeyyYyyyYyyrRR',
        'eeryyYyYyyrrRR',
        'eerryyyyyrrrRR',
        'eerrrrrrrrrrRR',
        'ehhhhhhhhhhhRR',
        'eerrrrrrrrrrRR',
        'hhssssssssssmm',
        'hhssssssssssmm',
        'hhmmmmmmmmmmmm',
        '.hssssssssssm.',
        '..mmmmmmmmmm..']
_LANTERN = ['.......kkkkkk.......',
            '......kKKKKKKk......',
            '......rrrrrrrr......',
            '....hrrrrrrrrrrR....',
            '...hhrrrrrrrrrrRR...',
            '..hhhrrrrrrrrrrRRR..',
            '.LLLLLLLLLLLLLLLLLL.',
            '.hhhrrrrrrrrrrrrRRR.',
            'hhhhrrrrrrrrrrrrRRRR',
            'hhhhrrrrrrrrrrrrRRRR',
            'LLLLLLLLLLLLLLLLLLLL',
            'hhhhrrrrrrrrrrrrRRRR',
            'hhhhrrrrrrrrrrrrRRRR',
            'hhhhrrrrrrrrrrrrRRRR',
            'hhhhrrrrrrrrrrrrRRRR',
            'LLLLLLLLLrrLLLLLLLLL',
            'hhhhrrrrrrrrrrrrRRRR',
            'hhhhrrrrrrrrrrrrRRRR',
            '.hhhrrrrrrrrrrrrRRR.',
            '.LLLLLLLLLLLLLLLLLL.',
            '..hhhrrrrrrrrrrRRR..',
            '...hhrrrrrrrrrrRR...',
            '....hrrrrrrrrrrR....',
            '......rrrrrrrr......',
            '......kKKKKKKk......',
            '.......kkkkkk.......',
            '.........yy.........',
            '.........yy.........']
_BOTTLE = ['..YY....',
           '..YY....',
           '..gG....',
           '..gG....',
           '..gG....',
           '.ggGG...',
           'gggGGG..',
           'gggGGG..',
           'gppppG..',
           'gpYYpG..',
           'gppppG..',
           'gpYpYG..',
           'gppppG..',
           'gggGGG..',
           'gggGGG..',
           'GGGGGG..']
_GLASS = ['cccccccccccccc',
          'cBBBBBBBBBBBBb',
          'cBBBBBBBBBBBBb',
          'cBwwwwBBBBBBBb',
          'cwiiiiwBwwwwBb',
          'cwiiiiwwiiiiwb',
          'cywiiiywiiiiwb',
          'cyywwwyywwwwYb',
          'cyyyyyyyyyyyYb',
          'cyyyyyyyyyyyYb',
          'cYyyyyyyyyyYYb',
          '.cYYYYYYYYYYb.',
          '..bbbbbbbbbb..']
_ONSEN = ['...rr....rr....rr.....',
          '....rr....rr....rr....',
          '.....rr....rr....rR...',
          '.....rr....rr....rR...',
          '....rr....rr....rr....',
          '...rr....rr....rr.....',
          '...rr....rr....rr.....',
          '....rr....rr....rr....',
          '.....rR....rR....rR...',
          '.....rR....rR....rR...',
          '....rr....rr....rr....',
          '......................',
          '..rr..............rR..',
          '.rr................rR.',
          'rr..................RR',
          'rr..................RR',
          'rr..................RR',
          '.rr................RR.',
          '..rrrr..........RRRR..',
          '....rrrrrrRRRRRRRR....',
          '......RRRRRRRRRR......']
_BURST = ['...........Y....Y...........',
          '..........YyY..YyY..........',
          '.....YY...YyY..YyY...YY.....',
          '......YYY.YyyYYyyY.YYY......',
          '......YyyYYyyyyyyYYyyY......',
          '......YyyyyyyyyyyyyyyY......',
          '.YYYYY.YyyyyyyyyyyyyY.YYYYY.',
          '..YYyyYyyyyyyyyyyyyyyYyyYY..',
          '...YYyyyyyyyyyyyyyyyyyyYY...',
          '....YYyyyyyyyyyyyyyyyyYY....',
          '....YYyyyyyyyyyyyyyyyyYY....',
          '.YYYyyyyyyyyyyyyyyyyyyyyYYY.',
          '.YYyyyyyyyyyyyyyyyyyyyyyyYY.',
          '.YYYyyyyyyyyyyyyyyyyyyyyYYY.',
          '....YYyyyyyyyyyyyyyyyyYY....',
          '....YYyyyyyyyyyyyyyyyyYY....',
          '...YYyyyyyyyyyyyyyyyyyyYY...',
          '..YYyyYyyyyyyyyyyyyyyYyyYY..',
          '.YYYYY.YyyyyyyyyyyyyY.YYYYY.',
          '......YyyyyyyyyyyyyyyY......',
          '......YyyYYyyyyyyYYyyY......',
          '......YYY.YyyYYyyY.YYY......',
          '.....YY...YyY..YyY...YY.....',
          '..........YyY..YyY..........',
          '...........Y....Y...........']
_REEL = ['.......hhhhhhhhhh.......',
         '......hhssssssssmm......',
         '....hhsssskkkkssssmm....',
         '...hhssssskkkksssssmm...',
         '...hssssskkkkkksssssm...',
         '..hsssssskkkkkkssssssm..',
         '.hhsskkssskkkkssskkssmm.',
         '.hsskkkkssskkssskkkkssm.',
         '.hskkkkkksssssskkkkkksm.',
         '.hskkkkkksskksskkkkkksm.',
         '.hsskkkkkskkkkskkkkkssm.',
         '.hssskkksskkkksskkksssm.',
         '.hssssssssskksssssssssm.',
         '.hsssssssssssssssssssssm',
         '.hssssskkksssskkksssssm.',
         '.hsssskkkkksskkkkkssssm.',
         '.hmssskkkkksskkkkksssmm.',
         '..msssskkkkssskkkksssm..',
         '...mssskkkksskkkkssmm...',
         '...mmsssskksssskksmm....',
         '....mmssssssssssssmm....',
         '......mmssssssssmm......',
         '.......mmmmmmmmmm.......']


def _beside(a, b, gap=2, drop=0):
    """Two pictures side by side, b `drop` rows lower, their bottoms padded clear."""
    h = max(len(a), len(b) + drop)
    wa = max(len(r) for r in a)
    a = [r.ljust(wa, '.') for r in a] + ['.' * wa] * (h - len(a))
    b = ['.' * len(b[0])] * drop + b + ['.' * len(b[0])] * (h - len(b) - drop)
    return [ra + '.' * gap + rb for ra, rb in zip(a, b)]


# name -> (rows, colours); a big's spec names its picture in `motif`
PICTURES = {
    'can': (_beside(_CAN, _CAN, gap=3, drop=3),
            dict(h='dae2e4', s='a4b0b5', m='848295', e='e78d7b', r='d16b56', R='aa4d31',
                 y='f3d890', Y='c6a663')),
    'lantern': (_LANTERN, dict(k='2c2d51', K='191c2a', h='e78d7b', r='d16b56', R='aa4d31', L='8a3a22',
                              y='f3d890')),
    'glass': (_beside(_BOTTLE, _GLASS, gap=1, drop=3),
              dict(Y='a7843b', y='c6a663', g='506b6b', G='395050', p='e4cecc', c='bbe9ff', b='5a86de',
                   B='314b8e', w='fafcfd', i='bbe9ff')),
    'onsen': (_ONSEN, dict(r='d16b56', R='aa4d31')),
    'burst': (_BURST, dict(y='f3d890', Y='c6a663')),
    'reel': (_REEL, dict(h='dae2e4', s='a4b0b5', m='575f79', k='2a2636')),
}
# what a picture has set over it: (text, colour), centred
LABELS = {'burst': ('50%', 'aa4d31')}


# ---- a board ------------------------------------------------------------------------
class DoesNotFit(ValueError):
    pass


def parts(pal):
    """A palette's parts as colours: the face's two (base, hi, lo, line) for painting,
    the title, its shadow, the band's material and the sub's colour."""
    p = PALETTES[pal]
    if p['face'][0] == 'painted':
        face = hl.material(*p['face'][1:])
    else:
        a, b = rgb(p['face'][1]), rgb(p['face'][2])
        face = (a, a, b, b)         # a lit box: its rows a and b, its shadow the darker
    title, shadow = p['title']
    return dict(lit=p['face'][0] == 'lit', face=face, title=rgb(title), shadow=shadow and rgb(shadow),
                band=hl.material(*p['band']), band_ramp=p['band'][0], sub=rgb(p['sub']))


def paint_face(im, box, q):
    """A face that is never flat: a lit box in scanlines, a painted board shaded."""
    if q['lit']:
        hl.scanlines(im, box, q['face'][0], q['face'][2])
    else:
        hl.shade(im, box, q['face'])


def motif_image(name, q):
    """A small motif in the board's colours."""
    return hl.pixmap(MOTIFS[name], dict(T=q['title'], a=q['band'][0], d=q['face'][3]))


def picture_image(name):
    rows, colours = PICTURES[name]
    pic = hl.canvas(len(rows[0]) + 2, len(rows) + 2)
    hl.stamp(pic, hl.pixmap(rows, {k: rgb(v) for k, v in colours.items()}), 1, 1)
    hl.outline(pic)
    if name in LABELS:
        s, colour = LABELS[name]
        w, h = hl.text_size(s)
        hl.text(pic, (pic.width - w) // 2, (pic.height - h) // 2, s, rgb(colour))
    return pic


def put(im, picture, x, y, q):
    """A motif with the title's shadow under it."""
    if q['shadow']:
        hl.stamp(im, picture, x + 1, y + 1, q['shadow'])
    hl.stamp(im, picture, x, y)


def render(spec):
    """One spec -> the board at half size. Raises DoesNotFit, naming the spec."""
    cw, ch = SHAPES[spec['shape']]
    w, h = cw * C, ch * C
    q = parts(spec['pal'])
    name = f"{spec['shape']} {spec['text']!r}"
    im = hl.canvas(w, h)
    # the housing, then the ink round it (the corner pixels stay clear)
    hl.fill(im, (1, 1, 1, h - 2), LEFT)
    hl.fill(im, (w - 2, 1, w - 2, h - 2), RIGHT)
    hl.fill(im, (1, 1, w - 2, 1), LIP)
    hl.fill(im, (1, h - 2, w - 2, h - 2), BOTTOM)
    hl.outline(im)
    hl.fill(im, (2, 2, w - 3, 2), q['face'][3])     # the lip's shadow on the face
    x0, x1, y0, y1 = 2, w - 3, 3, h - 3              # the face
    fw = x1 - x0 + 1

    def fits(what, size, room):
        if size[0] > room[0] or size[1] > room[1]:
            raise DoesNotFit(f'{name}: the {what} is {size[0]}x{size[1]}, the room {room[0]}x{room[1]}')

    sub = spec.get('sub')
    if sub:                                           # the band, the sub on its 12 rows
        top = y1 - BAND + 1
        hl.fill(im, (x0, top, x1, y1), q['band'][0])
        hl.fill(im, (x0, top, x1, top), q['band'][1])
        sw, sh = hl.text_size(sub)
        fits('sub', (sw, sh), (24 if cw == 1 else fw, BAND - 1))
        hl.text(im, x0 + (fw - sw) // 2, top + 1 + (BAND - 1 - sh) // 2, sub, q['sub'])
        y1 = top - 1
    motif = spec.get('motif')

    if spec['shape'] == 'big':
        # the picture panel, the face's top 33 rows: scanlines of the band ramp's darkest two
        panel = y0 + 31
        hl.scanlines(im, (x0, y0, x1, panel), hl.tone(q['band_ramp'], 0), hl.tone(q['band_ramp'], 1))
        hl.fill(im, (x0, panel + 1, x1, panel + 1), q['face'][3])
        if motif in PICTURES:
            pic = picture_image(motif)
            fits('picture', pic.size, (fw, 32))
            hl.stamp(im, pic, x0 + (fw - pic.width) // 2, y0 + (32 - pic.height) // 2)
        elif motif:                                   # a motif with no picture: three of it
            m = motif_image(motif, q)
            for i in range(3):
                put(im, m, x0 + fw * (2 * i + 1) // 6 - m.width // 2, y0 + (32 - m.height) // 2, q)
        y0 = panel + 2
        paint_face(im, (x0, y0, x1, y1), q)
        tw, th = hl.text_size(spec['text'])
        fits('title', (tw, th), (fw, y1 - y0 + 1))
        hl.text(im, x0 + (fw - tw) // 2, y0 + (y1 - y0 + 1 - th) // 2, spec['text'], q['title'], q['shadow'])
        return hl.double(im)

    paint_face(im, (x0, y0, x1, y1), q)
    fh = y1 - y0 + 1
    m = motif_image(motif, q) if motif else None
    if spec['shape'] == 'tall':
        if sub and len(spec['text']) > 3:
            raise DoesNotFit(f'{name}: a tall board has a sub under 3 glyphs or fewer')
        for pitch in (14, 13, 12):
            tw, th = hl.text_size(spec['text'], vertical=True, pitch=pitch)
            need = th + (m.height + 1 if m else 0)
            if need <= fh and tw <= fw:
                break
        fits('title and motif', (tw, need), (fw, fh))
        y = y0 + (fh - need) // 3                     # what is left over: a third above, a third between
        if m:
            put(im, m, x0 + (fw - m.width) // 2, y, q)
            y += m.height + 1 + (fh - need) // 3
        hl.text(im, x0 + (fw - tw) // 2, y, spec['text'], q['title'], q['shadow'], vertical=True, pitch=pitch)
        return hl.double(im)

    tw, th = hl.text_size(spec['text'])
    if spec['shape'] == 'square':
        if m and sub and len(spec['text']) > 1:
            m = None                                  # no room beside two glyphs
        side = bool(m and sub)
    else:                                             # wide: the motif left of the title, if it fits
        if m and tw + 12 > fw:
            m = None
        side = bool(m)
    if m and side:
        need = (m.width + 2 + tw, max(m.height, th))
    elif m:
        need = (max(m.width, tw), m.height + 2 + th)
    else:
        need = (tw, th)
    fits('title and motif', need, (fw, fh))
    x, y = x0 + (fw - need[0]) // 2, y0 + (fh - need[1]) // 2
    if m and side:
        put(im, m, x, y + (need[1] - m.height) // 2, q)
        hl.text(im, x + m.width + 2, y + (need[1] - th) // 2, spec['text'], q['title'], q['shadow'])
    elif m:
        put(im, m, x0 + (fw - m.width) // 2, y, q)
        hl.text(im, x0 + (fw - tw) // 2, y + m.height + 2, spec['text'], q['title'], q['shadow'])
    else:
        hl.text(im, x, y, spec['text'], q['title'], q['shadow'])
    return hl.double(im)


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
        'BOLD and SHORT, set in a 12px pixel font: tall signs max 4 characters, '
        'they stack vertically (and a sub only under 3 or fewer); square: 1-2 '
        'characters; wide/big: max 5 full-width characters. sub is an optional '
        'price, hours or hook, max 5 full-width characters (on a square or tall '
        'sign 2); a half-width letter or digit counts as half. Vary business '
        'types: food, drink, baths, games, services, sales. Never any '
        'convenience-store brand.'
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
    ap.add_argument('--sheet', metavar='PNG', help='also write a contact sheet of the pool, in manifest order')
    args = ap.parse_args()

    specs = list(SPECS) + (claude_specs(args.claude) if args.claude else [])

    os.makedirs(args.out, exist_ok=True)
    manifest, counters, images = [], {}, []
    for spec in specs:
        try:
            im = render(spec)
        except DoesNotFit as e:
            if spec in SPECS:
                raise
            print(f'skipped {e}')
            continue
        n = counters[spec['shape']] = counters.get(spec['shape'], 0) + 1
        name = f"{spec['shape']}-{n:02d}"
        im.save(f'{args.out}/{name}.png')
        images.append(im)
        cw, ch = SHAPES[spec['shape']]
        manifest.append({'key': f'ad-{name}', 'file': f'{name}.png',
                         'shape': spec['shape'], 'w': cw, 'h': ch})
    with open(f'{args.out}/manifest.json', 'w') as f:
        json.dump({'ads': manifest}, f, indent=1)
    print(f"{len(manifest)} ads -> {args.out} "
          f"({', '.join(f'{v} {k}' for k, v in sorted(counters.items()))})")
    if args.sheet:
        hl.sheet(images, args.sheet)
        print(f'contact sheet -> {args.sheet}')


if __name__ == '__main__':
    main()
