#!/usr/bin/env python3
"""make_road_tiles.py — the road pieces the ported sheet never had (issues #151, #147).

The road set cut from GK_TS_A5 is a three-cell road: kerb / centre line / kerb
(`road-edge-*`, `road-div-*`) plus `road-plain`. Two things cannot be drawn
with it, so they are made here from that same sheet (no new art, same
palette, so they sit flush against the originals):

  road-lane-left_0_0    asphalt with the LEFT half of the centre line on its
  road-lane-right_0_0   right edge / the right half on its left edge. Side by
                        side they put the line on the cell boundary, which is
                        where the middle of an EVEN-width road is: Osaka's main
                        street is four cells (kerb, lane, lane, kerb) because
                        the Dotonbori arch's opening is four cells wide.
  road-corner-nw|ne|sw|se_0_0
                        a kerb on two sides: the end of a road (Osaka's street
                        stops square below the station) and the outer corner of
                        a junction box (Tokyo's west junction). Cut from the
                        sheet's own corners, the ends of its crossroads' arms,
                        whose kerb curls round the corner (issue #359: a mitre
                        of two edge tiles cut the kerb's shading off on the
                        diagonal). Their seams with the edge tiles the game uses
                        differ from an edge tile's own by a pixel at most.

Deterministic and idempotent: rewrites the six PNGs and registers each key in
config.json spriteMetadata + tileNames (the game only loads a tile that has a
spriteMetadata entry). Needs Pillow, and the sheet in ../art-source.

Run from gamev2/ BEFORE generate_osaka.py:
    /Library/Developer/CommandLineTools/usr/bin/python3 tools/make_road_tiles.py
"""
import json
from PIL import Image

SRC = 'assets/sprites'
SHEET = '../art-source/GuttyKreum/TemplesandShrinesv2/RPGMakerVXAce/GK_TS_A5.png'
T = 64
# the sheet's corner cells (32px; the game's tiles are the sheet doubled): the
# top end of the crossroads' north arm, whose edge cells are road-edge-top
# (128,0), -left (96,32) and -right (160,32), and the bottom end of its south arm
CORNERS = {'nw': (96, 0), 'ne': (160, 0), 'sw': (96, 192), 'se': (160, 192)}


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


def corner(at):
    """Kerb on two sides, as the sheet draws its own corner."""
    x, y = CORNERS[at]
    cell = Image.open(SHEET).convert('RGBA').crop((x, y, x + T // 2, y + T // 2))
    return cell.resize((T, T), Image.NEAREST)


TILES = {
    'road-lane-left': lambda: lane('left'),
    'road-lane-right': lambda: lane('right'),
    'road-corner-nw': lambda: corner('nw'),
    'road-corner-ne': lambda: corner('ne'),
    'road-corner-sw': lambda: corner('sw'),
    'road-corner-se': lambda: corner('se'),
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
