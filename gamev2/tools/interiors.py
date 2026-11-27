"""interiors.py — the shell every generated interior is built in (issue #224).

An interior is one lit floor floating in the void: a konbini, a home, a worship
hall, the arcade under a town. Its generator used to write the whole shell by
hand - the void, the floor box at an offset, closures that add the offset, the
mats and their exits, a hand-drawn boundary - and each wrote it a little
differently. `Interior` is that shell, once, in FLOOR coordinates: (0, 0) is
the floor's top-left cell, row -1 is the first row of wall above it and row
`fh` the row below it, where the way out usually is.

A generator makes the calls in this order (docs/generators-and-checks.md,
"Interior building blocks", has a whole one in a dozen lines):

    it = Interior(fw, fh)                  # the room, filled with void, the floor centred in it
    it.floor(lambda fx, fy: key)           # what the floor is laid with
    it.back_wall([(fx, key, w), ...], depth)       # and, if it has them (on the void: layer='Over Floor'):
    it.side_walls(west, east, above)
    it.front_wall(key, gap, thresholds)
    it.prop(...) / it.stand(...) / it.place(...) / it.put(...)    # its furniture: the Builder's calls
    inside = it.doorway(fx, host, front)   # the exit cells, last: where you arrive from the street
    room = it.room(name, shopEnabled=False, <marker>={'host': host, 'door': [x, y]})
    rg.open_door(cfg['rooms'][host], door, key, inside[0])

What stays in the generator: which sprite in a town is its door, its art and
layout, its marker and flags, its name and what it prints. The door in the
host room is roomgen's (open_door / shut_door / pin and drop_stale, beside
the kept-door rules); so is everything a town generator also needs (Builder.prop / stand /
place, sprite_cells, register_metadata). This module holds only what is about
a void-shell room, and imports nothing but roomgen.
"""
import hashlib

import roomgen as rg

VOID = 'office-void-autotile'


def outline(cells):
    """The outline of a set of cells with no holes, as the corners of a polygon:
    clockwise from the corner with the smallest x (then y). Cells that are not one
    piece - two islands, a hole, two that only touch at a corner - are an error."""
    cells = {tuple(c) for c in cells}
    assert cells, 'no floor'
    nxt = {}
    for x, y in cells:
        for a, b, out in (((x, y), (x + 1, y), (x, y - 1)), ((x + 1, y), (x + 1, y + 1), (x + 1, y)),
                          ((x + 1, y + 1), (x, y + 1), (x, y + 1)), ((x, y + 1), (x, y), (x - 1, y))):
            if out not in cells:
                nxt[a] = b
    start = min(nxt)
    path, at = [start], nxt[start]
    while at != start:
        path.append(at)
        # two edges leave a corner where two cells touch, and one of them is lost: the walk
        # would never come back to its start
        assert len(path) <= len(nxt), 'the floor is not one piece'
        at = nxt[at]
    assert len(path) == len(nxt), 'the floor is not one piece'
    corners = [p for i, p in enumerate(path)
               if (p[0] - path[i - 1][0], p[1] - path[i - 1][1]) != (path[(i + 1) % len(path)][0] - p[0], path[(i + 1) % len(path)][1] - p[1])]
    return [list(p) for p in corners]


def reachable(walk, starts):
    """The cells of `walk` that can be walked to from `starts`, a step at a time."""
    seen, todo = set(), [tuple(s) for s in starts]
    while todo:
        x, y = todo.pop()
        if (x, y) in walk and (x, y) not in seen:
            seen.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen


def seed_of(text):
    """A seed from what an interior is (its town and door, as its generator words
    them): the same door is the same room on every run."""
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


def named(cfg, label, host, n=None):
    """A room's display name (the HUD shows it, never the room key): '7-Eleven · Sapporo',
    with its number `n` only where the caller passes one (a town with several)."""
    return f"{label} · {cfg['rooms'][host].get('name', host)}" + (f' {n}' if n else '')


class Interior:
    """A void room with a `fw` x `fh` floor whose cell (0, 0) is room cell (ox, oy).

    Everything takes floor coordinates. `b` is the Builder underneath (room
    coordinates; `cell()` converts), `walk` the set of ROOM cells you can be
    on - the floor to begin with, the exit cells once `doorway` adds them, and
    whatever the generator adds itself (a genkan, a corridor) - `view` the ROOM
    cells nobody walks that the boundary takes in all the same (a back wall
    the camera should not cut off: back_wall(view=True)), and `exits` the
    room's transporters, in the order `doorway` was called."""

    def __init__(self, fw, fh, ox=None, oy=3, w=None, h=None):
        # a Builder is at least 20x15 (the camera): a small floor is centred in that
        w = w or max(20, fw + 2 * (1 if ox is None else ox))
        h = h or max(15, oy + fh + 3)
        self.fw, self.fh = fw, fh
        self.ox, self.oy = (w - fw) // 2 if ox is None else ox, oy
        self.b = rg.Builder(w, h)
        self.b.fill(VOID)
        self.walk = {self.cell(fx, fy) for fx in range(fw) for fy in range(fh)}
        self.view = set()                   # solid cells inside the boundary: see back_wall
        self.exits = []
        self.reached = None                 # set by room(): the cells you can walk to

    def cell(self, fx, fy):
        """The room cell of floor cell (fx, fy)."""
        return (self.ox + fx, self.oy + fy)

    # ---- the Builder's calls, in floor coordinates ------------------------------------
    def put(self, layer, fx, fy, key, replace=False):
        self.b.put(layer, self.ox + fx, self.oy + fy, key, replace)

    def solid(self, fx, fy, w=1, h=1):
        self.b.solid(self.ox + fx, self.oy + fy, w, h)

    def place(self, layer, fx, fy, key, solid=()):
        self.b.place(layer, self.ox + fx, self.oy + fy, key, solid)

    def prop(self, key, fx, fy, w=1, h=1, layer='Collidables'):
        self.b.prop(key, self.ox + fx, self.oy + fy, w, h, layer)

    def stand(self, key, fx, foot, w=1, h=2, layer='Collidables'):
        self.b.stand(key, self.ox + fx, self.oy + foot, w, h, layer)

    # ---- the shell ----------------------------------------------------------------------
    def floor(self, key_of):
        """Lay the floor: the Floor tile `key_of(fx, fy)` on every floor cell."""
        for fx in range(self.fw):
            for fy in range(self.fh):
                self.put('Floor', fx, fy, key_of(fx, fy))

    def back_wall(self, pieces, depth, view=False):
        """The wall above the floor, from pieces as tall as it is: each (fx, key, w) is
        drawn on row -depth and is solid `w` x `depth`. (A wall of stacked panels is a
        prop per panel.)

        view=True puts the wall inside the room's boundary. A phone's camera holds a
        room no taller than its view to the boundary (GameScene.applyRoomBounds):
        drawn round the floor alone, it leaves a wall of two rows or more, and the
        top of whatever stands against it, off the top of the screen."""
        for fx, key, w in pieces:
            self.prop(key, fx, -depth, w, depth)
            if view:
                self.view |= {self.cell(fx + dx, -dy) for dx in range(w) for dy in range(1, depth + 1)}

    def side_walls(self, west, east, above, layer='Floor'):
        """The tops of the side walls: tiles down the columns either side of the floor,
        from `above` rows over it (the back wall's height) to its last row. They are
        Floor tiles in place of the void, or art laid over it (layer='Over Floor')."""
        for fy in range(-above, self.fh):
            self.put(layer, -1, fy, west)
            self.put(layer, self.fw, fy, east)

    def front_wall(self, key, gap, thresholds=(), layer='Floor'):
        """The top of the front wall, on the row below the floor: `key` on every column
        but those in `gap` (the doorway), which take `thresholds`, one each from the
        first (a mat two cells wide is one sprite: one threshold). On `layer`, as
        side_walls."""
        for fx in range(self.fw):
            if fx not in gap:
                self.put(layer, fx, self.fh, key)
        for fx, key in zip(gap, thresholds):
            self.put(layer, fx, self.fh, key)

    def doorway(self, fx, host, front, n=2, fy=None, inward=-1, mat=None):
        """A way out: `n` exit cells from (fx, fy) eastwards, on the row below the floor
        unless `fy` says otherwise. Each joins `walk` and gets one hidden exit to
        `front` in `host` (one cell for all of them, or a list of `n`). Returns the
        room cell beside each on the floor - where you arrive from the street: one row
        up (inward=-1), or one row down for a door in a north wall (inward=1). Nothing
        is drawn unless `mat` is given: a Floor key for the cells, or what floor() takes,
        key_of(fx, fy), for cells that are not all one tile (a front_wall threshold is
        the other way to draw them)."""
        fy = self.fh if fy is None else fy
        fronts = [front] * n if isinstance(front[0], int) else list(front)
        assert len(fronts) == n, f'{n} exit cells, {len(fronts)} cells to leave them for'
        inside = []
        for i, (tx, ty) in enumerate(fronts):
            x, y = self.cell(fx + i, fy)
            if mat:
                self.b.put('Floor', x, y, mat(fx + i, fy) if callable(mat) else mat)
            self.walk.add((x, y))
            self.exits.append(rg.transporter(x, y, host, tx, ty, hidden=True))
            inside.append((x, y + inward))
        return inside

    def room(self, name, npcs=None, pockets=(), **flags):
        """The finished room: the exits as its transporters, its boundary the outline
        of `walk` and `view` (the void round it needs no colliders), `interior` set,
        and `flags` on top - shopEnabled, lanternLight, shopMenu, the generator's own marker.
        None of those has a default: a room that is `interior` and nothing else is a
        store (Interactions.js), so say shopEnabled=False for anything that is not.

        Every cell of `walk` without a collider must be reachable from the exits; a
        cell that is closed off on purpose is listed in `pockets` (floor coordinates)."""
        assert self.exits, f'{name}: no doorway'
        room = self.b.room(name, npcs=npcs, transporters=list(self.exits))
        solid = {tuple(map(int, c.split(','))) for c in self.b.L['Colliders']}
        # the boundary is all that keeps you off a cell with no collider
        open_view = self.view - self.walk - solid
        assert not open_view, f'{name}: in the boundary, not floor and not solid: {sorted(open_view)}'
        room['boundary'] = outline(self.walk | self.view)
        room['interior'] = True          # never graded by day / night, never offered to the blog pipeline
        room.update(flags)
        free = self.walk - solid - {self.cell(*p) for p in pockets}
        self.reached = reachable(free, [(t['gridX'], t['gridY']) for t in self.exits])
        assert self.reached == free, f'{name}: floor nobody can reach: {sorted(free - self.reached)}'
        return room
