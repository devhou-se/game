#!/usr/bin/env python3
"""sync_cities.py — keep config.json `cities` in step with ../devhouse.world.

A city (config `cities`) is a set of overworld rooms the game stitches into ONE
continuous map at load (src/systems/CityStitcher.js, issues #40/#41). The game
needs each member room's position in world CELLS, but devhouse.world — where
those positions are authored, by dragging maps around in Tiled — lives at the
repo root and is not deployed. So the offsets are copied into config.json:

    "cities": { "TokyoCity": { "rooms": [ {"room": "Tokyo", "x": 0, "y": 1}, ... ] } }

    python3 tools/sync_cities.py            # rewrite the x/y of every listed room
    python3 tools/sync_cities.py --check    # exit 1 (loudly) if they disagree

The room LIST and its ORDER are hand-authored and never touched (a later room
wins the cells it overlaps with an earlier one). `--check` is also run by
tools/make_worldmap.py, and the game re-checks the offsets against
assets/map/world-map.json at boot. Both files are found from this script's
own place in the repo, so it runs from any directory. Stdlib only.
"""
import json, os, sys

GV2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD = os.path.join(os.path.dirname(GV2), 'devhouse.world')
CONFIG = os.path.join(GV2, 'config.json')
GS = 64


def world_cells(world_path=WORLD):
    """{room key (lower-case tmj basename): (x, y, w, h)} in cells — a map that
    is not on the 64px grid (fine for a detached town) maps to None."""
    out = {}
    for m in json.load(open(world_path))['maps']:
        vals = (m['x'], m['y'], m['width'], m['height'])
        out[os.path.basename(m['fileName'])[:-4]] = (
            None if any(v % GS for v in vals) else tuple(v // GS for v in vals))
    return out


def problems(cfg, cells):
    """Every disagreement between config `cities` and the world file, as text."""
    out = []
    for city_key, city in (cfg.get('cities') or {}).items():
        if city_key in cfg['rooms']:
            out.append(f'city "{city_key}" has the same name as a room')
        for m in city.get('rooms', []):
            room = cfg['rooms'].get(m['room'])
            at = cells.get(m['room'].lower())
            if room is None:
                out.append(f'{city_key}: "{m["room"]}" is not a room in config.json')
            elif m['room'].lower() not in cells:
                out.append(f'{city_key}: "{m["room"]}" is not placed in devhouse.world')
            elif at is None:
                out.append(f'{city_key}: {m["room"]} is not on the {GS}px grid in devhouse.world')
            else:
                if (m.get('x'), m.get('y')) != at[:2]:
                    out.append(f'{city_key}: {m["room"]} is at cell {at[:2]} in devhouse.world '
                               f'but ({m.get("x")}, {m.get("y")}) in config.json')
                size = (room['worldWidth'] // GS, room['worldHeight'] // GS)
                if size != at[2:]:
                    out.append(f'{city_key}: {m["room"]} is {size} cells in config.json '
                               f'but {at[2:]} in devhouse.world')
    return out


def check(cfg=None):
    """Exit non-zero, listing every mismatch, unless config and world agree."""
    cfg = cfg or json.load(open(CONFIG))
    bad = problems(cfg, world_cells())
    if bad:
        sys.exit('config.json `cities` is OUT OF SYNC with devhouse.world:\n  ' +
                 '\n  '.join(bad) + '\nfix with: python3 tools/sync_cities.py')


if __name__ == '__main__':
    cfg = json.load(open(CONFIG))
    if '--check' in sys.argv:
        check(cfg)
        n = sum(len(c.get('rooms', [])) for c in (cfg.get('cities') or {}).values())
        print(f'cities in sync with devhouse.world ({n} rooms)')
        sys.exit(0)
    cells = world_cells()
    changed = 0
    for city in (cfg.get('cities') or {}).values():
        for m in city.get('rooms', []):
            at = cells.get(m['room'].lower())
            if at and (m.get('x'), m.get('y')) != at[:2]:
                m['x'], m['y'] = at[:2]
                changed += 1
    if changed:
        # same writer as tools/blog_to_npc.py, so the file diff stays minimal
        open(CONFIG, 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    print(f'{changed} room offset(s) updated')
    check(cfg)
