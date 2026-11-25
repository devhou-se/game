#!/usr/bin/env python3
"""seal_vending.py — make every vending machine solid down to its foot (issue #101).

A machine is a cabinet tile with a foot tile under it (`*-vending-machine-top*`
over `-bottom` / `-base*`; the tall ones are a 1x2 cabinet sprite over a base).
The Godot port and the first `vending-*` prefabs put a collider on the cabinet
only, so the player could walk onto the foot cell and stand on the machine.

For each named room (default: all) this adds a collider to the two lowest cells
of every machine column - the foot and the cabinet cell above it. The empty
top cell of a tall machine stays walk-behind. Idempotent. It refuses to seal a
cell that holds a transporter or that an NPC stands on in any dated state, and
writes nothing in that case.

Generators get the same result from the prefabs (tools/make_prefabs.py), so
this is for ported rooms and for repairing data `play.js lint` flags as
`vending-walkable`. It edits config.json: run config_to_tiled.py afterwards.

Run from gamev2/:  python3 tools/seal_vending.py [Room ...] [--dry-run]
"""
import json, struct, sys


def cells(key):
    with open(f'assets/sprites/{key}.png', 'rb') as f:
        f.read(16); w, h = struct.unpack('>II', f.read(8))
    return max(1, round(w / 64)), max(1, round(h / 64))


def machine_cells(room, pal):
    out = set()
    for L in room['layers']:
        for xy, i in L.get('tiles', {}).items():
            key = pal[i] if isinstance(i, int) else i
            if 'vending-machine' not in key:
                continue
            x, y = map(int, xy.split(','))
            w, h = cells(key)
            out |= {(x + a, y + b) for a in range(w) for b in range(h)}
    return out


def must_be_solid(machine):
    """The foot of each machine column and the cell above it."""
    feet = {(x, y) for (x, y) in machine if (x, y + 1) not in machine}
    return feet | {(x, y - 1) for (x, y) in feet if (x, y - 1) in machine}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    cfg = json.load(open('config.json'))
    pal = cfg['tilePalette']
    unknown = [r for r in args if r not in cfg['rooms']]
    if unknown:
        sys.exit(f'not a room: {", ".join(unknown)}')
    if 'gk_blank' not in pal:
        pal.append('gk_blank')
    blank = pal.index('gk_blank')
    refused, total = [], 0
    for name in args or sorted(cfg['rooms']):
        room = cfg['rooms'][name]
        solid = {xy for L in room['layers'] if L.get('collision') for xy in L['tiles']}
        need = sorted(c for c in must_be_solid(machine_cells(room, pal)) if f'{c[0]},{c[1]}' not in solid)
        if not need:
            continue
        taken = {(t['gridX'], t['gridY']) for t in room.get('transporters', [])}
        for n in room.get('npcs', []):
            taken.add((n.get('gridX'), n.get('gridY')))
            taken |= {(s['gridX'], s['gridY']) for s in (n.get('states') or {}).values() if 'gridX' in s}
        clash = [c for c in need if c in taken]
        if clash:
            refused.append(f'{name}: a transporter or an NPC stands on {clash}')
            continue
        layer = next((L for L in room['layers'] if L['name'] == 'Colliders'), None) or \
            next(L for L in room['layers'] if L.get('collision'))
        for (x, y) in need:
            layer['tiles'][f'{x},{y}'] = blank
        total += len(need)
        print(f'{name}: sealed {len(need)} cell(s): {" ".join(f"{x},{y}" for x, y in need)}')
    if refused:
        sys.exit('nothing written:\n  ' + '\n  '.join(refused))
    if not dry and total:
        open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
    print(f'{total} cell(s) sealed' + (' (dry run - nothing written)' if dry else ''))


if __name__ == '__main__':
    main()
