#!/usr/bin/env python3
"""extract_shrine.py — re-section the blue shrine roof (issue #42).

`shrine-top_0_0` was sliced 160x160 native px out of the GuttyKreum temple atlas,
which cut the roof flat along its bottom: the down-swept eave corners and the
brackets under them were missing. The whole roof needs 160x192 — the same
section the red roof (`red-shrine-top`, tile 117) always had.

The crop rectangle is NOT repeated here: it is read from the Godot tileset
(`Assets/Tilemap/GuttyKreum.tres`, tile `shrine-top`), the same place
`doport.py` slices from, so a re-port produces the identical sprite. The art is
upscaled 2x NEAREST like every ported tile and the script refuses to write a
sprite whose art touches the edge of its section (= still clipped).

One edge contact is expected and allowed: between the eave brackets the bottom
32px of the section show the top of the hall's wall, which carries on down into
`shrine-building`. Both tiles are cut from the same atlas, so stacked in the
game (roof on Tops at the building's cell -1,-2) those pixels coincide exactly.
Only bottom-edge art outside the building's columns counts as clipped.

Besides the PNG it keeps everything that records the sprite's size in step:
  - config.json `spriteMetadata` anchor (centre of the top-left cell, the
    doport convention: 16 / native size);
  - `imagewidth` / `imageheight` in the tileset and the tile-object `width` /
    `height` of every `tiled/*.tmj` and `tiled/prefabs/*.tmj` that uses it
    (Tiled-only bookkeeping — the game reads the real texture size).
Placement is untouched: the section grew downwards, so the top-left cell is the
same. Needs Pillow (plain python3 here has none — use the CommandLineTools
one). Run from gamev2/:
    PY=/Library/Developer/CommandLineTools/usr/bin/python3
    $PY tools/extract_shrine.py            # write
    $PY tools/extract_shrine.py --check    # report edge clipping only
"""
import glob, json, re, sys
from PIL import Image

TRES = '../Assets/Tilemap/GuttyKreum.tres'
# sprite key -> (Godot tile name in TRES, tile it sits on top of)
SPRITES = {'shrine-top_0_0': ('shrine-top', 'shrine-building')}


def tile_source(txt, name):
    """(atlas path, native crop box) of the named single-region tile."""
    tid = re.search(r'^(\d+)/name = "%s"$' % re.escape(name), txt, re.M).group(1)
    ext = re.search(r'^%s/texture = ExtResource\( (\d+) \)' % tid, txt, re.M).group(1)
    path = re.search(r'\[ext_resource path="res://([^"]+)" type="Texture" id=%s\]' % ext, txt).group(1)
    x, y, w, h = (int(float(v)) for v in re.search(
        r'^%s/region = Rect2\( ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+) \)' % tid, txt, re.M).groups())
    return '../' + path, (x, y, x + w, y + h)


def clipped_edges(im, below=None):
    """Names of the edges that opaque art touches — a sprite cut mid-art.
    `below` is the (x0, x1) span, in section px, of the tile stacked underneath:
    bottom-edge art inside it continues into that tile and is not a cut."""
    a = im.getchannel('A')
    w, h = im.size
    if below:
        a.paste(0, (below[0], h - 1, below[1], h))
    strips = {'top': (0, 0, w, 1), 'bottom': (0, h - 1, w, h), 'left': (0, 0, 1, h), 'right': (w - 1, 0, w, h)}
    return [n for n, box in strips.items() if a.crop(box).getbbox()]


def sync_tiled(key, size):
    """Record the new sprite size in every Tiled map that references it."""
    for path in sorted(glob.glob('tiled/*.tmj') + glob.glob('tiled/prefabs/*.tmj')):
        raw = open(path).read()
        tmj = json.loads(raw)
        ts = tmj['tilesets'][0]
        gids = set()
        for t in ts['tiles']:
            if t['image'].endswith(f'/{key}.png'):
                t['imagewidth'], t['imageheight'] = size
                gids.add(ts['firstgid'] + t['id'])
        for layer in tmj['layers']:
            for o in layer.get('objects', []):
                if o.get('gid') in gids:
                    o['width'], o['height'] = size
        out = json.dumps(tmj, indent=1)
        if gids and out != raw:
            open(path, 'w').write(out)
            print(f'  updated {path}')


def main():
    check = '--check' in sys.argv[1:]
    txt = open(TRES).read()
    cfg = json.load(open('config.json'))
    for key, (name, base) in SPRITES.items():
        atlas, box = tile_source(txt, name)
        base_atlas, base_box = tile_source(txt, base)
        assert base_atlas == atlas, (atlas, base_atlas)
        native = Image.open(atlas).convert('RGBA').crop(box)
        edges = clipped_edges(native, (base_box[0] - box[0], base_box[2] - box[0]))
        print(f'{key}: {atlas} {box} -> {native.width * 2}x{native.height * 2}px, '
              f'clipped edges: {", ".join(edges) or "none"}')
        if check:
            continue
        if edges:
            sys.exit(f'{key}: art touches the {"/".join(edges)} edge of {box} — widen tile "{name}" in {TRES}')
        big = native.resize((native.width * 2, native.height * 2), Image.NEAREST)
        assert big.width % 64 == 0 and big.height % 64 == 0, (key, big.size)
        big.save(f'assets/sprites/{key}.png')
        cfg['spriteMetadata'].setdefault(key, {'frameCount': 1}).update(
            anchorX=round(16.0 / native.width, 4), anchorY=round(16.0 / native.height, 4))
        cfg.setdefault('tileNames', {})[key] = name
        sync_tiled(key, big.size)
    if not check:
        open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
