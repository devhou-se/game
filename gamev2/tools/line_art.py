"""line_art.py — paint a line drawing by rule (issue #271).

Tokyo Station, Tokyo Tower and Tsutenkaku were white line drawings, and are
those drawings still: the line art is kept as source in
../art-source/line-art/ and painted here, so the sprite has the drawing's own
outline, lines and windows under its colour. tools/generate_tokyo_art.py and
tools/generate_tsutenkaku.py only say which part of a drawing is which
material (a `zone` function); everything else is these rules, applied on the
half-size grid (one pixel = one pixel of a 32px tile):

  1 classify  a template pixel is clear (alpha 0), a LINE (opaque black) or
              FILL (any other opaque pixel; `accent` when it is the
              template's red)
  2 regions   a region is a 4-connected group of fill pixels of one colour
  3 material  `zone(x, y, accent)` names a material for a fill pixel; a
              region takes the material most of its pixels get, so a zone
              need not trace the drawing's lines and a region is never
              split. `by_region=False` paints pixel by pixel instead (bands
              that cut across a lattice). `Plan` is a zone made of boxes and
              polygons
  4 panes     a region of at most `pane` pixels whose material is in `walls`
              is a window pane: GLAZED, or LAMPLIT where `lit(x, y)` says so
              (it is asked once for a window, with its top-left pixel; panes
              with at most `bar` pixels of line between them are one window)
  5 fill      a material is (base, hi, lo, line). A fill pixel is `hi` where
              the pixel to its left or above it is a line and `lo` where the
              pixel to its right or below it is one (`lo` wins): the light
              comes from the top left, as in the rest of the art. A region
              of at most `pane` pixels is flat
  6 lines     a line pixel is INK where it touches clear or the picture's
              edge (4 neighbours), the window-frame colour where it touches
              glass (8 neighbours: a pane, or a region zoned GLAZED or
              LAMPLIT), INK where it separates two materials or touches no
              fill at all, and otherwise the `line` shade of the one
              material round it: brick courses read as joints, not as black
              bars
  7 alpha     the result's alpha is the template's, pixel for pixel
              (asserted). The caller doubles the picture with Image.NEAREST

Pillow pixel access only: no numpy, and none of Pillow's polygon, ellipse or
line drawing in the output path (Plan fills its own shapes, by scanlines), so
every Pillow paints the same pixels. Importing this
has no side effects and nothing here writes a file. The colours are the house
palette's (generate_hokkaido, generate_sapporo_art, generate_osaka_art).
"""
import os
import sys
from collections import Counter

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_hokkaido import (rgb, INK, CREAM, CREAM_LO, CREAM_DK, WHITE, SNOW, SNOW_LO,   # noqa: E402
                               GLASS, GLASS_DK, STONE, STONE_LO, STONE_DK,
                               GREEN, GREEN_LO, GREEN_HI, RED, RED_HI, RED_LO, RED_DK)
from generate_sapporo_art import (BRICK, BRICK_HI, BRICK_LO, BRICK_DK, SLATE, SLATE_LO,     # noqa: E402
                                  SNOW_SH, WARM, DARK)
from generate_osaka_art import STEEL, STEEL_HI, STEEL_LO, STEEL_DK                          # noqa: E402

SOURCE = '../art-source/line-art'        # from gamev2/, as the extract_* tools read their sheets
BLACK, PAPER, ACCENT = (0, 0, 0, 255), (255, 255, 255, 255), (246, 49, 59, 255)

# ---- the materials: (base, hi, lo, line) ---------------------------------------
BRICKWORK = (BRICK, BRICK_HI, BRICK_LO, BRICK_DK)
BRICK_SHADE = (BRICK_LO, BRICK, BRICK_DK, DARK)             # a face turned from the light
STONEWORK = (CREAM, WHITE, CREAM_LO, CREAM_DK)
STONE_SHADE = (CREAM_LO, CREAM, CREAM_DK, DARK)
SLATES = (SLATE, STONE_LO, SLATE_LO, GLASS_DK)
SLATE_SHADE = (SLATE_LO, SLATE, STONE_DK, GLASS_DK)
WHITE_STEEL = (SNOW, WHITE, SNOW_LO, STONE_LO)
WHITE_SHADE = (SNOW_LO, SNOW, SNOW_SH, STONE_LO)
GREY_STEEL = (STEEL, STEEL_HI, STEEL_LO, STEEL_DK)
GREY_SHADE = (STEEL_LO, STEEL, STEEL_DK, DARK)
COPPER = (GREEN_HI, rgb('a9c796'), GREEN, GREEN_LO)         # weathered copper; its lit edge is a step lighter
COPPER_SHADE = (GREEN, GREEN_HI, GREEN_LO, DARK)
NEON = (RED, RED_HI, RED_LO, RED_DK)
CONCRETE = (STONE, WHITE, STONE_LO, STONE_DK)
SHADOW = (DARK, DARK, DARK, INK)                            # an unlit opening
GLAZED = (GLASS, GLASS, GLASS, GLASS_DK)                    # a pane, flat; its frame is the line colour
LAMPLIT = (WARM, WARM, WARM, GLASS_DK)


def template(key):
    """The line drawing `key` at half size: clear, black lines, white fill and
    the one accent red, nothing else."""
    big = Image.open(os.path.join(SOURCE, key + '.png')).convert('RGBA')
    im = big.resize((big.width // 2, big.height // 2), Image.NEAREST)
    assert im.resize(big.size, Image.NEAREST).tobytes() == big.tobytes(), f'{key}: the line art is not pixel-doubled'
    for count, c in im.getcolors(im.width * im.height):
        assert c[3] == 0 or c in (BLACK, PAPER, ACCENT), f'{key}: {count} pixels of {c}, which is no line, fill or accent'
    return im


def regions(tpl):
    """(label, members): label[y][x] is the index of the region a fill pixel is
    in (-1 for a line, None for clear), members[i] its pixels in scan order."""
    w, h = tpl.size
    px = tpl.load()
    label = [[None] * w for _ in range(h)]
    members = []
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c[3] == 0 or label[y][x] is not None:
                continue
            if c == BLACK:
                label[y][x] = -1
                continue
            i, todo, cells = len(members), [(x, y)], []
            label[y][x] = i
            while todo:
                cx, cy = todo.pop()
                cells.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and label[ny][nx] is None and px[nx, ny] == c:
                        label[ny][nx] = i
                        todo.append((nx, ny))
            members.append(sorted(cells, key=lambda p: (p[1], p[0])))
    return label, members


def windows(label, members, panes, bar):
    """Group the pane regions into windows: two panes with at most `bar` line
    pixels between them, across or down, are in one. {region: its window's
    first pane}."""
    w, h = len(label[0]), len(label)
    head = {i: i for i in panes}

    def find(i):
        while head[i] != i:
            head[i] = head[head[i]]
            i = head[i]
        return i

    for i in sorted(panes):
        for x, y in members[i]:
            for dx, dy in ((1, 0), (0, 1)):
                for step in range(1, bar + 2):
                    nx, ny = x + dx * step, y + dy * step
                    if nx >= w or ny >= h or label[ny][nx] is None:
                        break
                    j = label[ny][nx]
                    if j == -1:
                        continue
                    if j in head and find(j) != find(i):
                        a, b = sorted((find(i), find(j)))
                        head[b] = a
                    break
    return {i: find(i) for i in panes}


def paint(tpl, zone, by_region=True, pane=0, walls=(), lit=None, bar=0):
    """The template painted: rules 1 to 7 of the module's docstring."""
    w, h = tpl.size
    src = tpl.load()
    label, members = regions(tpl)

    # ---- 3: a material for every region, or for every pixel ----------------------
    of = [None] * len(members)                                   # the region's material
    each = {}                                                    # by_region=False: the pixel's
    for i, cells in enumerate(members):
        votes = Counter()
        for x, y in cells:
            m = zone(x, y, src[x, y] == ACCENT)
            votes[m] += 1
            if not by_region:
                each[x, y] = m
        of[i] = max(votes, key=lambda m: (votes[m], -list(votes).index(m)))
    # ---- 4: the panes --------------------------------------------------------------
    panes = {i for i, cells in enumerate(members) if len(cells) <= pane and of[i] in walls}
    window = windows(label, members, panes, bar)
    for i in sorted(panes):
        x, y = members[window[i]][0]
        of[i] = LAMPLIT if lit and lit(x, y) else GLAZED
    flat = {i for i, cells in enumerate(members) if len(cells) <= pane}

    def material(x, y):
        i = label[y][x]
        return of[i] if by_region or i in panes else each[x, y]

    def kind(x, y):
        """None off the picture or on a clear pixel, -1 on a line, else the region."""
        return label[y][x] if 0 <= x < w and 0 <= y < h else None

    out = Image.new('RGBA', tpl.size, (0, 0, 0, 0))
    px = out.load()
    for y in range(h):
        for x in range(w):
            i = label[y][x]
            if i is None:
                continue
            if i >= 0:                                           # ---- 5: fill
                base, hi, lo, _ = material(x, y)
                if i in flat:
                    px[x, y] = base
                elif kind(x + 1, y) == -1 or kind(x, y + 1) == -1:
                    px[x, y] = lo
                elif kind(x - 1, y) == -1 or kind(x, y - 1) == -1:
                    px[x, y] = hi
                else:
                    px[x, y] = base
                continue
            # ---- 6: line
            if any(kind(nx, ny) is None for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                px[x, y] = INK
                continue
            round_it, frame = [], None
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    j = kind(nx, ny)
                    if j is None or j == -1:
                        continue
                    m = material(nx, ny)
                    if m in (GLAZED, LAMPLIT):
                        frame = m[3]
                    elif m not in round_it:
                        round_it.append(m)
            px[x, y] = frame or (round_it[0][3] if len(round_it) == 1 else INK)
    # ---- 7 ---------------------------------------------------------------------------
    assert out.getchannel('A').tobytes() == tpl.getchannel('A').tobytes(), 'the painted picture is not the drawing'
    return out


class Plan:
    """A zone drawn as shapes on the template's grid: start from one material
    and lay boxes and polygons over it, the later over the earlier. Calling
    it is the `zone` paint() wants."""

    def __init__(self, size, ground=None):
        self.w, self.h = size
        self.cells = [[ground] * self.w for _ in range(self.h)]

    def box(self, m, x0, y0, x1, y1):
        """Columns x0..x1 of rows y0..y1, both ends included."""
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            row = self.cells[y]
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                row[x] = m

    def poly(self, m, *points):
        """The pixels whose centres lie inside the polygon (even-odd), by scanlines."""
        ys = [p[1] for p in points]
        for y in range(max(0, int(min(ys))), min(self.h - 1, int(max(ys))) + 1):
            cuts = []
            for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
                if (ay <= y + 0.5) != (by <= y + 0.5):
                    cuts.append(ax + (y + 0.5 - ay) * (bx - ax) / (by - ay))
            cuts.sort()
            for a, b in zip(cuts[::2], cuts[1::2]):
                for x in range(max(0, int(a + 0.5)), min(self.w - 1, int(b - 0.5)) + 1):
                    if a <= x + 0.5 <= b:
                        self.cells[y][x] = m

    def __call__(self, x, y, accent=False):
        return self.cells[y][x]

