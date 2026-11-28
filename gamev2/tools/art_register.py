#!/usr/bin/env python3
"""art_register.py — put a city's drawn-ahead sprites into config.json (issue #219).

The art tools of the cities that were drawn before they were rebuilt
(generate_asahikawa_art.py and the ones after it) only wrote PNGs. Each calls
register() from its main() with the keys its city's stage places, so art for a
city that is not rebuilt yet stays out of config.json.

For each key: spriteMetadata {frameCount: 1, anchorX: 32 / width, anchorY:
32 / height} (the centre of the sprite's top-left cell, rounded to four places
as roomgen.register_metadata does) and its tileNames name; a `glow` list for
a sprite that is lit at night (src/utils/Glows.js reads it: spots in cells
from the sprite's top-left); `depthBias: -200` for a sprite that lies on the
ground and is walked ON (a bridge deck on Non-Collidables).

Not a generator: it has no main and writes nothing by itself. config.json is
rewritten only when something changed, so a second run of an art tool is a no-op.
"""
import json
import re

MAX_R = 2.5                                  # a halo is never wider than this, in cells (glows-trams.test.js)
LAMP = re.compile(r'lamp-post|-lanterns')    # DayNight lights these keys itself: no spots of their own
FLAT_BIAS = -200                             # under everyone standing on it (RoomManager reads depthBias)


def colour(c):
    """A colour as the int Glows.js takes: '#f6dc8c', 'f6dc8c', (r, g, b[, a]) or an int."""
    if isinstance(c, int):
        return c
    if isinstance(c, str):
        return int(c.lstrip('#'), 16)
    r, g, b = c[:3]
    return (r << 16) | (g << 8) | b


def spot(x, y, color, r=0.8, a=0.5, ry=None):
    """One glow spot in cells from the sprite's top-left, radii clamped to MAX_R."""
    s = {'x': round(x, 2), 'y': round(y, 2), 'r': round(min(r, MAX_R), 2), 'color': colour(color), 'a': round(a, 2)}
    if ry:
        s['ry'] = round(min(ry, MAX_R), 2)
    return s


def name_of(key):
    return key.rsplit('_', 1)[0] if 'autotile' in key else key[:-len('_0_0')]


def entries(built, glow=None, flat=()):
    """{key: (spriteMetadata entry, tileNames name)} for every sprite of `built` ({key: image})."""
    out = {}
    for key, im in built.items():
        meta = {'frameCount': 1, 'anchorX': round(32 / im.width, 4), 'anchorY': round(32 / im.height, 4)}
        spots = (glow or {}).get(key)
        if spots and not LAMP.search(key):
            meta['glow'] = [spot(s['x'], s['y'], s['color'], s.get('r', 0.8), s.get('a', 0.5), s.get('ry'))
                            for s in spots]
        if key in flat:
            meta['depthBias'] = FLAT_BIAS
        out[key] = (meta, name_of(key))
    return out


def register(built, glow=None, flat=(), path='config.json'):
    """Write the entries of `built` into the config at `path`; True if it changed."""
    cfg = json.load(open(path))
    before = json.dumps(cfg, sort_keys=True)
    for key, (meta, name) in entries(built, glow, flat).items():
        cfg['spriteMetadata'][key] = meta
        cfg.setdefault('tileNames', {})[key] = name
    if json.dumps(cfg, sort_keys=True) == before:
        return False
    open(path, 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    return True
