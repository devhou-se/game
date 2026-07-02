"""Godot-3 autotile bitmask helpers, shared by doport.py (semantic subtile
names like gravel-autotile_edge-n) and config_to_tiled.py (Tiled wang/terrain
sets so the Terrain Brush paints floors with automatic edges).

Bitmask bits (3x3): TL=1 T=2 TR=4 L=8 C=16 R=32 BL=64 B=128 BR=256.
A set bit means "connects to same terrain on that side"; the role names the
OPEN (non-connecting) sides: edge-n faces north, corner-nw is the blob's
top-left corner, center connects everywhere.
"""
import re

BITS = {'nw': 1, 'n': 2, 'ne': 4, 'w': 8, 'c': 16, 'e': 32, 'sw': 64, 's': 128, 'se': 256}
_ADJ = {'n': ('nw', 'ne'), 'e': ('ne', 'se'), 's': ('sw', 'se'), 'w': ('nw', 'sw')}
_OPP = {'n': 's', 'e': 'w', 's': 'n', 'w': 'e'}


def parse_bitmasks(tres_path):
    """tres -> {tid: {(cx,cy): mask}} for every autotile with bitmask_flags."""
    txt = open(tres_path).read()
    out = {}
    for m in re.finditer(r'(\d+)/autotile/bitmask_flags = \[(.*?)\]', txt, re.S):
        flags = {}
        for mm in re.finditer(r'Vector2\( (\d+), (\d+) \), (\d+)', m.group(2)):
            flags[(int(mm.group(1)), int(mm.group(2)))] = int(mm.group(3))
        if flags:
            out[int(m.group(1))] = flags
    return out


def role(mask):
    """Bitmask -> canonical role name; falls back to t<mask> for exotic pieces."""
    n, e, s, w = bool(mask & 2), bool(mask & 32), bool(mask & 128), bool(mask & 8)
    open_ = [d for d, b in (('n', n), ('e', e), ('s', s), ('w', w)) if not b]
    # a missing corner only matters when both adjacent edges connect (inner corner)
    inner = sorted(c for c, (bit, e1, e2) in
                   {'nw': (mask & 1, n, w), 'ne': (mask & 4, n, e),
                    'sw': (mask & 64, s, w), 'se': (mask & 256, s, e)}.items()
                   if e1 and e2 and not bit)
    if not open_:
        base = 'center' if not inner else 'inner-' + '-'.join(inner)
        return base
    if len(open_) == 1:
        base = 'edge-' + open_[0]
    elif len(open_) == 2:
        a, b = open_
        base = ('edge-' + a + b) if _OPP[a] == b else 'corner-' + ''.join(sorted(open_, key='nswe'.index))
    elif len(open_) == 3:
        closed = next(d for d in 'nesw' if d not in open_)
        base = 'end-' + _OPP[closed]
    else:
        base = 'single'
    if inner:
        base += '-inner-' + '-'.join(inner)
    return base


def subtile_roles(flags):
    """{(cx,cy): mask} -> {(cx,cy): role}, deduping repeats (-2, -3 by row order)."""
    byrole = {}
    for (cx, cy), mask in flags.items():
        byrole.setdefault(role(mask), []).append((cy, cx))
    out = {}
    for r, lst in byrole.items():
        for i, (cy, cx) in enumerate(sorted(lst)):
            out[(cx, cy)] = r if i == 0 else f'{r}-{i + 1}'
    return out


def role_to_wangid(rolename):
    """Role -> Tiled wangid [n, ne, e, se, s, sw, w, nw] (1 = terrain, 0 = open).
    Returns None for names that aren't autotile roles."""
    r = re.sub(r'-\d+$', '', rolename)  # strip variant ordinal
    idx = {'n': 0, 'ne': 1, 'e': 2, 'se': 3, 's': 4, 'sw': 5, 'w': 6, 'nw': 7}
    wang = [1] * 8

    def open_edge(d):
        wang[idx[d]] = 0
        for c in _ADJ[d]:
            wang[idx[c]] = 0

    m_inner = re.search(r'-?inner((?:-(?:nw|ne|sw|se))+)$', r)
    if m_inner:
        for c in m_inner.group(1).strip('-').split('-'):
            wang[idx[c]] = 0
        r = r[:m_inner.start()] or 'center'
    if r == 'center':
        return wang
    if r == 'single':
        return [0] * 8
    m = re.fullmatch(r'edge-([nesw])', r)
    if m:
        open_edge(m.group(1)); return wang
    m = re.fullmatch(r'edge-(ns|ew)', r)
    if m:
        for d in m.group(1): open_edge(d)
        return wang
    m = re.fullmatch(r'corner-([ns][ew])', r)
    if m:
        for d in m.group(1): open_edge(d)
        return wang
    m = re.fullmatch(r'end-([nesw])', r)
    if m:
        for d in 'nesw':
            if d != _OPP[m.group(1)]: open_edge(d)
        return wang
    return None
