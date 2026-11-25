#!/usr/bin/env python3
"""make_road_tiles.py — the road pieces the ported sheet never had (issues #151, #147).

The road set cut from GK_TS_A5 is a three-cell road: kerb / centre line / kerb
(`road-edge-*`, `road-div-*`) plus `road-plain`. Two things cannot be drawn
with it, so they are derived here from those same tiles (no new art, same
palette, so they sit flush against the originals):

  road-lane-left_0_0    asphalt with the LEFT half of the centre line on its
  road-lane-right_0_0   right edge / the right half on its left edge. Side by
                        side they put the line on the cell boundary, which is
                        where the middle of an EVEN-width road is: Osaka's main
                        street is four cells (kerb, lane, lane, kerb) because
                        the Dotonbori arch's opening is four cells wide.
  road-corner-nw|ne|sw|se_0_0
                        a kerb on two sides, mitred on the diagonal: the end of
                        a road (Osaka's street stops square below the station)
                        and the outer corner of a junction box (Tokyo's west
                        junction, where the lane from Machi comes in).

Deterministic and idempotent: rewrites the six PNGs and registers each key in
config.json spriteMetadata + tileNames (the game only loads a tile that has a
spriteMetadata entry). Needs Pillow.

Run from gamev2/ BEFORE generate_osaka.py:
    /Library/Developer/CommandLineTools/usr/bin/python3 tools/make_road_tiles.py
"""
import json
from PIL import Image

SRC = 'assets/sprites'
T = 64


def load(name):
    im = Image.open(f'{SRC}/road-{name}_0_0.png').convert('RGBA')
    assert im.size == (T, T), (name, im.size)
    return im


def lane(side):
    """Half the centre line on one edge of a plain asphalt cell."""
    out, div = load('plain'), load('div-vertical')
    half = T // 2
    if side == 'left':      # div's left half, slid to this cell's right half
        out.paste(div.crop((0, 0, half, T)), (half, 0))
    else:                   # div's right half, slid to this cell's left half
        out.paste(div.crop((half, 0, T, T)), (0, 0))
    return out


def corner(vert, horiz):
    """Kerb along the top or bottom (`vert`) and along the left or right
    (`horiz`), joined on the cell's diagonal like a mitred frame."""
    a, b = load(f'edge-{vert}'), load(f'edge-{horiz}')
    out = a.copy()
    pa, pb = out.load(), b.load()
    for y in range(T):
        for x in range(T):
            dx = x if horiz == 'left' else T - 1 - x      # distance from the side kerb
            dy = y if vert == 'top' else T - 1 - y        # distance from the top/bottom kerb
            if dx < dy:
                pa[x, y] = pb[x, y]
    return out


TILES = {
    'road-lane-left': lambda: lane('left'),
    'road-lane-right': lambda: lane('right'),
    'road-corner-nw': lambda: corner('top', 'left'),
    'road-corner-ne': lambda: corner('top', 'right'),
    'road-corner-sw': lambda: corner('bottom', 'left'),
    'road-corner-se': lambda: corner('bottom', 'right'),
}


def main():
    cfg = json.load(open('config.json'))
    for name, draw in TILES.items():
        key = f'{name}_0_0'
        draw().save(f'{SRC}/{key}.png')
        cfg['spriteMetadata'][key] = {'anchorX': 0.5, 'anchorY': 0.5, 'frameCount': 1}
        cfg.setdefault('tileNames', {})[key] = name
    open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    print(f'wrote {len(TILES)} road tiles: ' + ' '.join(TILES))


if __name__ == '__main__':
    main()
