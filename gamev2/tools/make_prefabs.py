#!/usr/bin/env python3
"""make_prefabs.py — seed gamev2/tiled/prefabs/*.tmj, the object library.

Each prefab is an ordinary small Tiled map you can open and edit in Tiled:
sprites on object layers (tagged with the room layer they belong to), solid
cells painted with the visible collider-marker tile on a `Colliders` layer,
and doors as `kind=door` points on a `Meta` layer. prefab.py stamps these
into rooms; doors come back as cells the generator can wire transporters to.

Run from gamev2/:  python3 tools/make_prefabs.py
"""
import json, os, struct

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiled', 'prefabs')
GS = 64

def png_size(key):
    with open(f'assets/sprites/{key}.png', 'rb') as f:
        f.read(16); return struct.unpack('>II', f.read(8))

def props(d):
    return [{'name': n, 'type': 'bool' if isinstance(v, bool) else 'int' if isinstance(v, int) else 'string', 'value': v}
            for n, v in d.items()]

Z = {'Floor': 0, 'Over Floor': 1, 'Water': 1, 'Non-Collidables': 4, 'Collidables': 5, 'Other': 6, 'Tops': 7}

def building(w, h, door, roof=2, door_w=1):
    """A single-sprite street building, w x h cells. Everything collides except
    the top `roof` rows, which are walk-behind (the house-roof convention): a
    tower whose whole upper half was open hid the player in a pocket up to
    5x6 cells deep. The door cell(s) sit in the bottom row from column `door`."""
    return dict(w=w, h=h, sprites=None,
                colliders=[(x, y) for x in range(w) for y in range(roof, h)],
                doors=[(door + i, h - 1) for i in range(door_w)])


# name -> dict(w, h, sprites=[(layer, dx, dy, key)], colliders=[(dx,dy)], doors=[(dx,dy)])
PREFABS = {
    'lantern-red':  dict(w=1, h=2, sprites=[('Tops', 0, 0, 'red-lanterns_6_3'), ('Collidables', 0, 1, 'red-lanterns_4_1')],
                         colliders=[(0, 1)], doors=[]),
    'lamp-blue':    dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'blue-lamp-post_0_0')], colliders=[(0, 0)], doors=[]),
    'sakura-large': dict(w=3, h=3, sprites=[('Tops', 0, 0, 'sakura-large-top_0_0'), ('Collidables', 1, 2, 'sakura-large-base_0_0')],
                         colliders=[(1, 2)], doors=[]),
    'sakura-small': dict(w=1, h=2, sprites=[('Tops', 0, 0, 'sakura-small_0_0')], colliders=[(0, 1)], doors=[]),
    'tree-green':   dict(w=2, h=3, sprites=[('Tops', 0, 0, 'tree-3-top_0_0'), ('Collidables', 0, 2, 'tree-3-base-shadow_0_0')],
                         colliders=[(0, 2), (1, 2)], doors=[]),
    'shrub-large':  dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'shrub-large-circle_0_0')],
                         colliders=[(0, 0), (0, 1), (1, 0), (1, 1)], doors=[]),
    'shrub-small':  dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'shrub-small-circle_0_0')], colliders=[(0, 0)], doors=[]),
    # snow-dusted variants (recoloured by tools/make_snow_tiles.py) for Yukimura
    'tree-snow':    dict(w=2, h=3, sprites=[('Tops', 0, 0, 'tree-3-top-snow_0_0'), ('Collidables', 0, 2, 'tree-3-base-shadow-snow_0_0')],
                         colliders=[(0, 2), (1, 2)], doors=[]),
    'shrub-large-snow': dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'shrub-large-circle-snow_0_0')],
                             colliders=[(0, 0), (0, 1), (1, 0), (1, 1)], doors=[]),
    'shrub-small-snow': dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'shrub-small-circle-snow_0_0')], colliders=[(0, 0)], doors=[]),
    'torii-red':    dict(w=6, h=5, sprites=[('Tops', 0, 0, 'torii-red-top_0_0'), ('Collidables', 1, 3, 'torii-red-feet_0_0')],
                         colliders=[(1, 3), (4, 3), (1, 4), (4, 4)], doors=[]),
    # The blue shrine hall, 5x8: the whole roof (re-sectioned by tools/extract_shrine.py
    # so its eaves are not cut off) overhangs the 3-wide hall by a cell each side
    # and two rows above it. Never place shrine-building without a roof on top —
    # its own roof rows are a 3-cell slice that the Tops sprite is there to cover.
    'shrine':       dict(w=5, h=8, sprites=[('Tops', 0, 0, 'shrine-top_0_0'), ('Collidables', 1, 2, 'shrine-building_0_0')],
                         # solid: the hall, plus every cell the roof would hide a walker in (the row
                         # behind the hall and the eave columns) — nobody vanishes under the roof
                         colliders=[(x, y) for x in (1, 2, 3) for y in range(2, 7) if (x, y) != (2, 6)]
                                   + [(x, 1) for x in range(5)] + [(x, y) for x in (0, 4) for y in (2, 3, 4)], doors=[(2, 6)]),
    # A GuttyKreum townhouse, top to bottom (matching the pack's promo):
    #   roof (3, with the eaves) + rafter (the window wall) + tier (the tiled
    #   awning band) + entrance (the ground-floor door). 6 cells tall.
    'house-blue':   dict(w=3, h=6, sprites=[('Tops', 0, 0, 'building-roof-blue_0_0'), ('Collidables', 0, 3, 'building-rafter-blue_0_0'), ('Collidables', 0, 4, 'building-tier-blue_0_0'), ('Collidables', 0, 5, 'building-entrance-1_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (3, 4, 5) if (x, y) != (1, 5)], doors=[(1, 5)]),
    'house-red':    dict(w=3, h=6, sprites=[('Tops', 0, 0, 'building-roof-red_0_0'), ('Collidables', 0, 3, 'building-rafter-red_0_0'), ('Collidables', 0, 4, 'building-tier-red_0_0'), ('Collidables', 0, 5, 'building-entrance-3_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (3, 4, 5) if (x, y) != (1, 5)], doors=[(1, 5)]),
    'house-black':  dict(w=3, h=6, sprites=[('Tops', 0, 0, 'building-roof-black_0_0'), ('Collidables', 0, 3, 'building-rafter-black_0_0'), ('Collidables', 0, 4, 'building-tier-black_0_0'), ('Collidables', 0, 5, 'building-entrance-2_0_0')],
                         colliders=[(x, y) for x in range(3) for y in (3, 4, 5) if (x, y) != (1, 5)], doors=[(1, 5)]),
    'seven-eleven': dict(w=3, h=4, sprites=[('Collidables', 0, 0, 'seven-eleven_0_0')],
                         colliders=[(x, y) for x in range(3) for y in range(4) if (x, y) != (1, 3)], doors=[(1, 3)]),
    'sign-7-11':    dict(w=1, h=2, sprites=[('Tops', 0, 0, '7-11-sign-left_0_0')], colliders=[(0, 1)], doors=[]),
    # A vending machine is two tiles: the cabinet (top) and its foot (bottom - the
    # last 14px of the cabinet). BOTH cells collide: with only the cabinet solid
    # the player stood on the foot, drawn over the machine's lower half (#101).
    # The shop opens by bumping either cell (Interactions.js matches both tiles),
    # so you buy from the cell in front of the foot. `play.js lint` enforces it
    # (`vending-walkable`); tools/seal_vending.py repairs a room's data.
    'vending-white': dict(w=1, h=2, sprites=[('Other', 0, 0, 'white-vending-machine-top_0_0'), ('Other', 0, 1, 'white-vending-machine-bottom_0_0')],
                          colliders=[(0, 0), (0, 1)], doors=[]),
    'vending-red':  dict(w=1, h=2, sprites=[('Other', 0, 0, 'red-vending-machine-top_0_0'), ('Other', 0, 1, 'red-vending-machine-bottom_0_0')],
                         colliders=[(0, 0), (0, 1)], doors=[]),
    'bell-blue':    dict(w=2, h=4, sprites=[('Tops', 0, 0, 'blue-bell-top_0_0'), ('Collidables', 0, 2, 'bell-blue-baseless_0_0')],
                         colliders=[(0, 2), (1, 2)], doors=[]),
    'fox-statue':   dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'fox-statue-base-1_0_0')], colliders=[(0, 1)], doors=[]),
    # The GuttyKreum small pagoda, two 2x3 pieces stacked flush: spire + hip
    # roof + balcony on top, pent roof + walls + door below. 6 cells tall,
    # house convention: overhead art on Tops, only the wall storey collides.
    # (Born inverted and overlapping — the spire rendered mid-structure.)
    'pagoda-small': dict(w=2, h=6, sprites=[('Tops', 0, 0, 'red-pagoda-small-top_0_0'), ('Collidables', 0, 3, 'red-pagoda-small-base_0_0')],
                         colliders=[(x, y) for x in (0, 1) for y in (3, 4, 5)], doors=[]),
    # ---- Osaka landmarks (one big sprite each; art from tools/extract_dotonbori.py
    #      and tools/generate_tsutenkaku.py). All sit on Collidables so they Y-sort
    #      by their feet: solid at the base, walk-behind above it. -----------------
    # Dotonbori entrance arch: only the two posts collide (columns 0 and 7), so
    # the street runs straight under the sign through columns 1-6.
    'dotonbori-arch':  dict(w=8, h=6, sprites=[('Collidables', 0, 0, 'dotonbori-arch_0_0')],
                            colliders=[(x, y) for x in (0, 7) for y in (4, 5)], doors=[]),
    # The oval ferris wheel: the two truss legs (columns 2-3 and 8-9) and the
    # boarding gate between them collide; the rest of the ring is overhead.
    'dotonbori-wheel': dict(w=12, h=12, sprites=[('Collidables', 0, 0, 'dotonbori-wheel_0_0')],
                            colliders=[(x, y) for x in (2, 3, 8, 9) for y in (9, 10, 11)] + [(4, 10), (5, 10)], doors=[]),
    # Tsutenkaku Tower: the legs and the body over the archway collide; the two
    # cells in the archway mouth stay open so you can step in under the tower.
    # The colliders follow the splay of the legs (row 9 = where they leave the
    # deck, cols 2-5; rows 10-11 cols 1-6; the feet span all 8) so there is no
    # invisible wall on the empty plaza beside them.
    'tsutenkaku':      dict(w=8, h=13, sprites=[('Collidables', 0, 0, 'tsutenkaku_0_0')],
                            colliders=[(x, 9) for x in range(2, 6)]
                                      + [(x, y) for x in range(1, 7) for y in (10, 11)]
                                      + [(x, 12) for x in range(8) if x not in (3, 4)], doors=[]),
    # ---- generic city buildings (issue #18; art assembled by tools/extract_city.py
    #      at the 2x scale of the houses). One sprite each on Collidables, so it
    #      Y-sorts by its feet: solid from the ground up, only the top two rows
    #      (the roof line) are walk-behind. Doors are listed so a generator can
    #      wire an interior later; stamped sealed, the whole footprint is solid. --
    'highrise-yellow':    building(4, 8, door=1),
    'highrise-blue':      building(5, 11, door=2),
    'highrise-glass':     building(4, 10, door=1, door_w=2),
    'highrise-apartment': building(5, 8, door=2),
    'midrise-apartment':  building(5, 6, door=2),
    # the discount store ("Don Quijote"): generated parody sign over the facade
    'discount-store':     building(5, 8, door=2),
    # Kyoto-style two-storey townhouses: the main roof (rows 0-1) is overhead,
    # the upper wall, pent roof and shopfront (rows 2-4) are solid.
    'machiya-black':      building(5, 5, door=2),
    'machiya-red':        building(5, 5, door=2),
    'machiya-blue':       building(5, 5, door=2),
    # ---- Hokkaido (issue #43; art drawn by tools/generate_hokkaido.py) ---------
    # Sapporo Clock Tower: the hall and its roof (rows 4-7) and the tower rising
    # out of it (rows 1-3, the middle three columns - shaft and pyramid roof)
    # collide; only the roof's tip and finial (row 0) are walk-behind, which hide
    # nobody. The air either side of the tower is open, so nobody is walled off
    # from snow they can see.
    'sapporo-clock-tower': dict(w=5, h=8, sprites=[('Collidables', 0, 0, 'sapporo-clock-tower_0_0')],
                                colliders=[(x, y) for x in range(5) for y in range(4, 8)]
                                          + [(x, y) for x in (1, 2, 3) for y in (1, 2, 3)], doors=[(2, 7)]),
    # Sapporo TV Tower: the colliders follow the silhouette - the base building
    # (rows 11-12), the splayed legs (rows 9-10), the shaft with the clock and
    # the deck (rows 5-8) and the lattice above the deck (rows 3-4: it is dense
    # enough to hide a person). Only the mast (rows 0-2) is walk-behind.
    'sapporo-tv-tower':    dict(w=6, h=13, sprites=[('Collidables', 0, 0, 'sapporo-tv-tower_0_0')],
                                colliders=[(x, y) for x in (2, 3) for y in range(3, 9)]
                                          + [(x, y) for x in range(1, 5) for y in (9, 10)]
                                          + [(x, y) for x in range(6) for y in (11, 12)], doors=[]),
    # ---- Sapporo's own buildings (issue #219; art drawn by tools/generate_sapporo_art.py) --
    # The station front: everything collides from the wings' roof line down (rows
    # 2-6), and so do the glazed hall (columns 3-8, row 1) and the tower stub
    # behind the east wing (columns 7-8, row 0): nothing of it is walk-behind.
    # The doors under the clock are a pair, as the sprite draws them.
    'sapporo-station-front': dict(w=10, h=7, sprites=[('Collidables', 0, 0, 'sapporo-station-front_0_0')],
                                  colliders=[(x, y) for x in range(10) for y in range(2, 7)]
                                            + [(x, 1) for x in range(3, 9)] + [(7, 0), (8, 0)],
                                  doors=[(4, 6), (5, 6)]),
    # The red-brick government hall (Akarenga): the hall and its slate roof (rows
    # 2-5) and the dome on its drum (the middle column above them) collide.
    'sapporo-akarenga':      dict(w=7, h=6, sprites=[('Collidables', 0, 0, 'sapporo-akarenga_0_0')],
                                  colliders=[(x, y) for x in range(7) for y in range(2, 6)] + [(3, 0), (3, 1)],
                                  doors=[(3, 5)]),
    # The two office blocks: only the top row (the roof plant, the KITA board) is
    # walk-behind - a wall of windows is not something to stand behind.
    'sapporo-office-brick':  building(4, 7, door=2, roof=1),
    'sapporo-office-glass':  building(5, 6, door=2, roof=1),
    # ---- Odori Park (issue #219, stage 2). The snow sculptures collide along their
    # silhouettes, so nobody stands inside one: the castle from its roof down
    # (the air beside the keep, above the two wing turrets, is open), the tanuki
    # and the bear all over.
    'snow-sculpture-castle': dict(w=5, h=4, sprites=[('Collidables', 0, 0, 'snow-sculpture-castle_0_0')],
                                  colliders=[(x, y) for x in range(5) for y in (2, 3)]
                                            + [(x, y) for x in (1, 2, 3) for y in (0, 1)], doors=[]),
    'snow-sculpture-tanuki': dict(w=2, h=3, sprites=[('Collidables', 0, 0, 'snow-sculpture-tanuki_0_0')],
                                  colliders=[(x, y) for x in range(2) for y in range(3)], doors=[]),
    'snow-sculpture-bear':   dict(w=3, h=2, sprites=[('Collidables', 0, 0, 'snow-sculpture-bear_0_0')],
                                  colliders=[(x, y) for x in range(3) for y in range(2)], doors=[]),
    # The festival tents: solid all over, as a yatai is (nobody stands inside
    # the canvas). The counter faces south: you bump it from the row below.
    'snowfest-stall-corn':   dict(w=3, h=3, sprites=[('Collidables', 0, 0, 'snowfest-stall-corn_0_0')],
                                  colliders=[(x, y) for x in range(3) for y in range(3)], doors=[]),
    'snowfest-stall-drinks': dict(w=3, h=3, sprites=[('Collidables', 0, 0, 'snowfest-stall-drinks_0_0')],
                                  colliders=[(x, y) for x in range(3) for y in range(3)], doors=[]),
    # The frozen fountain: the basin (rows 1-2) and the stem with its bowls (the
    # middle column above it).
    'odori-fountain':        dict(w=3, h=3, sprites=[('Collidables', 0, 0, 'odori-fountain_0_0')],
                                  colliders=[(x, y) for x in range(3) for y in (1, 2)] + [(1, 0)], doors=[]),
    # The park's lamp (its key holds `lamp-post`: lit at night): the foot collides,
    # the globe is overhead. The bench is solid.
    'odori-lamp':            dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'odori-lamp-post_0_0')],
                                  colliders=[(0, 1)], doors=[]),
    'odori-bench':           dict(w=2, h=1, sprites=[('Collidables', 0, 0, 'odori-bench_0_0')],
                                  colliders=[(0, 0), (1, 0)], doors=[]),
    # What the plough leaves along a kerb: one solid cell each.
    'snowbank-h':            dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'snowbank-h_0_0')], colliders=[(0, 0)], doors=[]),
    'snowbank-v':            dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'snowbank-v_0_0')], colliders=[(0, 0)], doors=[]),
    'snowbank-pile':         dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'snowbank-pile_0_0')], colliders=[(0, 0)], doors=[]),
    # The bridge over Asahikawa's frozen river: a flat deck you walk ON. It sits
    # on Non-Collidables with a negative depthBias (spriteMetadata, written by
    # generate_hokkaido.py) so it draws over the ice but under everyone on it.
    'asahikawa-bridge':    dict(w=2, h=5, sprites=[('Non-Collidables', 0, 0, 'asahikawa-bridge_0_0')],
                                colliders=[], doors=[]),
    # A ramen shop's nobori: the pole's foot collides, the cloth is overhead.
    'ramen-banner':        dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'ramen-banner_0_0')],
                                colliders=[(0, 1)], doors=[]),
    # ---- Sendai (issue #66; art drawn by tools/generate_sendai_art.py) ----------
    # Date Masamune on his plinth: the plinth (rows 2-3) collides, horse and rider
    # above it are walk-behind.
    'sendai-masamune':     dict(w=3, h=4, sprites=[('Collidables', 0, 0, 'sendai-masamune_0_0')],
                                colliders=[(x, y) for x in range(3) for y in (2, 3)], doors=[]),
    # Zuihoden: solid from the eaves down; only the ridge row is walk-behind (and
    # the generator plants cedars behind it, so nobody gets there).
    'sendai-zuihoden':     dict(w=7, h=5, sprites=[('Collidables', 0, 0, 'sendai-zuihoden_0_0')],
                                colliders=[(x, y) for x in range(7) for y in range(1, 5)], doors=[(3, 4)]),
    # A samurai gate: the wing walls and posts (columns 0 and 3, the two wall
    # rows) collide; the two-cell gateway between them is open, the roof overhead.
    'sendai-gate':         dict(w=4, h=3, sprites=[('Collidables', 0, 0, 'sendai-gate_0_0')],
                                colliders=[(x, y) for x in (0, 3) for y in (1, 2)], doors=[]),
    # One cell of earthen wall, 1x2 and solid; stamp them side by side.
    'sendai-earthen-wall': dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'sendai-earthen-wall_0_0')],
                                colliders=[(0, 0), (0, 1)], doors=[]),
    'sendai-pine':         dict(w=2, h=3, sprites=[('Collidables', 0, 0, 'sendai-pine_0_0')],
                                colliders=[(0, 2), (1, 2)], doors=[]),
    'sendai-cedar':        dict(w=2, h=4, sprites=[('Collidables', 0, 0, 'sendai-cedar_0_0')],
                                colliders=[(0, 3), (1, 3)], doors=[]),
    'sendai-maple':        dict(w=2, h=3, sprites=[('Collidables', 0, 0, 'sendai-maple_0_0')],
                                colliders=[(0, 2), (1, 2)], doors=[]),
    'sendai-stone-lantern': dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'sendai-stone-lantern_0_0')],
                                 colliders=[(0, 1)], doors=[]),
    'sendai-pub':          building(5, 5, door=2),
    # The distillery's kiln house: the brick hall (rows 3-5) and the kiln tower
    # rising out of it (rows 1-2, the middle three columns) collide.
    'sendai-kiln':         dict(w=5, h=6, sprites=[('Collidables', 0, 0, 'sendai-kiln_0_0')],
                                colliders=[(x, y) for x in range(5) for y in (3, 4, 5)]
                                          + [(x, y) for x in (1, 2, 3) for y in (1, 2)], doors=[(2, 5)]),
    'sendai-barrels':      dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'sendai-barrels_0_0')],
                                colliders=[(0, 1), (1, 1)], doors=[]),
    # Matsushima bay: islets and the moored sightseeing boat stand in the water
    # (solid already); the pier is a flat deck you walk ON (Non-Collidables +
    # depthBias, the asahikawa-bridge recipe).
    'matsushima-islet':       dict(w=3, h=2, sprites=[('Collidables', 0, 0, 'matsushima-islet_0_0')],
                                   colliders=[(x, 1) for x in range(3)], doors=[]),
    'matsushima-islet-small': dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'matsushima-islet-small_0_0')],
                                   colliders=[(0, 1), (1, 1)], doors=[]),
    'matsushima-ball-rock':   dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'matsushima-ball-rock_0_0')],
                                   colliders=[(0, 1), (1, 1)], doors=[]),
    'matsushima-ferry':       dict(w=5, h=2, sprites=[('Collidables', 0, 0, 'matsushima-ferry_0_0')],
                                   colliders=[(x, y) for x in range(5) for y in (0, 1)], doors=[]),
    'matsushima-pier':        dict(w=5, h=1, sprites=[('Non-Collidables', 0, 0, 'matsushima-pier_0_0')],
                                   colliders=[], doors=[]),
    # ---- Fukuoka (issue #67; art drawn by tools/generate_fukuoka_art.py) ----------
    # Fukuoka Tower: the base building (rows 10-11) and the mirrored shaft (the
    # middle two columns, rows 2-9) collide; only the mast is walk-behind. The
    # air either side of the shaft is open - nothing is drawn there to hide in.
    'fukuoka-tower':   dict(w=4, h=12, sprites=[('Collidables', 0, 0, 'fukuoka-tower_0_0')],
                            colliders=[(x, y) for x in (1, 2) for y in range(2, 10)]
                                      + [(x, y) for x in range(4) for y in (10, 11)], doors=[]),
    # A yatai food stall: solid all over - the cart, its stools and the row its
    # canvas roof is drawn on (a stall at the end of the row is open at the side,
    # and nobody should stand inside the roof). You stand in front of the stools.
    'yatai-ramen':     dict(w=3, h=3, sprites=[('Collidables', 0, 0, 'yatai-ramen_0_0')],
                            colliders=[(x, y) for x in range(3) for y in range(3)], doors=[]),
    'yatai-yakitori':  dict(w=3, h=3, sprites=[('Collidables', 0, 0, 'yatai-yakitori_0_0')],
                            colliders=[(x, y) for x in range(3) for y in range(3)], doors=[]),
    'yatai-oden':      dict(w=3, h=3, sprites=[('Collidables', 0, 0, 'yatai-oden_0_0')],
                            colliders=[(x, y) for x in range(3) for y in range(3)], doors=[]),
    # A post strung with paper lanterns (lit at night: the key holds `-lanterns`).
    'yatai-lanterns':  dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'yatai-lanterns_0_0')],
                            colliders=[(0, 1)], doors=[]),
    # The Yamakasa float at Kushida shrine: the trestle and the lowest tier collide.
    'hakata-yamakasa': dict(w=2, h=4, sprites=[('Collidables', 0, 0, 'hakata-yamakasa_0_0')],
                            colliders=[(x, y) for x in (0, 1) for y in (2, 3)], doors=[]),
    'canal-city':      building(8, 6, door=3, door_w=2),
    'canal-fountain':  dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'canal-fountain_0_0')],
                            colliders=[(0, 0), (1, 0), (0, 1), (1, 1)], doors=[]),
    # Dazaifu Tenmangu's hall: solid all the way up, the grove on its roof
    # included - there is only a river bank behind it, and nobody hides there.
    'dazaifu-hall':    dict(w=6, h=5, sprites=[('Collidables', 0, 0, 'dazaifu-hall_0_0')],
                            colliders=[(x, y) for x in range(6) for y in range(5)], doors=[]),
    # The arched bridge over the shrine pond: flat, walked ON (asahikawa-bridge's
    # recipe - Non-Collidables with a negative depthBias in spriteMetadata).
    'dazaifu-bridge':  dict(w=2, h=4, sprites=[('Non-Collidables', 0, 0, 'dazaifu-bridge_0_0')],
                            colliders=[], doors=[]),
    'plum-tree':       dict(w=2, h=3, sprites=[('Tops', 0, 0, 'plum-tree_0_0')], colliders=[(0, 2), (1, 2)], doors=[]),
    # The shrine hall under the red roof (Park's, Kushida's): the `shrine` prefab's
    # footprint and colliders with red-shrine-top on top.
    'shrine-red':      dict(w=5, h=8, sprites=[('Tops', 0, 0, 'red-shrine-top_0_0'), ('Collidables', 1, 2, 'shrine-building_0_0')],
                            colliders=[(x, y) for x in (1, 2, 3) for y in range(2, 7) if (x, y) != (2, 6)]
                                      + [(x, 1) for x in range(5)] + [(x, y) for x in (0, 4) for y in (2, 3, 4)], doors=[(2, 6)]),
    # ---- Hokuriku (issue #68; art drawn by tools/generate_hokuriku_art.py) --------
    # Kanazawa Castle's Ishikawa gate: the turret (columns 0-2) and the walls are
    # solid from the eaves down; the gateway (columns 3-4) is open all the way
    # through, under the gate's roof.
    'kanazawa-ishikawa-gate': dict(w=8, h=4, sprites=[('Collidables', 0, 0, 'kanazawa-ishikawa-gate_0_0')],
                                   colliders=[(x, y) for x in range(8) for y in (1, 2, 3) if x not in (3, 4)]
                                             + [(x, 0) for x in range(3)], doors=[]),
    'kanazawa-kotoji':        dict(w=2, h=2, sprites=[('Collidables', 0, 0, 'kanazawa-kotoji_0_0')],
                                   colliders=[(0, 1), (1, 1)], doors=[]),
    'kanazawa-chaya-a':       building(4, 4, door=1),
    'kanazawa-chaya-b':       building(4, 4, door=1),
    'kanazawa-whisky-bar':    building(4, 4, door=1),
    # flat decks you walk ON (Non-Collidables + depthBias, the asahikawa-bridge recipe)
    'kanazawa-canal-bridge':  dict(w=2, h=4, sprites=[('Non-Collidables', 0, 0, 'kanazawa-canal-bridge_0_0')],
                                   colliders=[], doors=[]),
    'shirakawa-bridge':       dict(w=8, h=2, sprites=[('Non-Collidables', 0, 0, 'shirakawa-bridge_0_0')],
                                   colliders=[], doors=[]),
    'hokuriku-ginkgo':        dict(w=2, h=3, sprites=[('Collidables', 0, 0, 'hokuriku-ginkgo_0_0')],
                                   colliders=[(0, 2), (1, 2)], doors=[]),
    # gassho farmhouses: the ground floor and the gable above it are solid; the
    # generators close the roof's top rows too, so nobody stands behind the thatch
    'shirakawa-gassho':       dict(w=5, h=5, sprites=[('Collidables', 0, 0, 'shirakawa-gassho_0_0')],
                                   colliders=[(x, y) for x in range(5) for y in (2, 3, 4)], doors=[(2, 4)]),
    'shirakawa-gassho-small': dict(w=4, h=4, sprites=[('Collidables', 0, 0, 'shirakawa-gassho-small_0_0')],
                                   colliders=[(x, y) for x in range(4) for y in (2, 3)], doors=[]),
    'shirakawa-hasa':         dict(w=3, h=2, sprites=[('Collidables', 0, 0, 'shirakawa-hasa_0_0')],
                                   colliders=[(x, 1) for x in range(3)], doors=[]),
    'shirakawa-lookout':      dict(w=4, h=1, sprites=[('Collidables', 0, 0, 'shirakawa-lookout_0_0')],
                                   colliders=[(x, 0) for x in range(4)], doors=[]),
    'shirakawa-peak':         dict(w=6, h=4, sprites=[('Collidables', 0, 0, 'shirakawa-peak_0_0')],
                                   colliders=[(x, y) for x in range(6) for y in (2, 3)], doors=[]),
    'shirakawa-bear-sign':    dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'shirakawa-bear-sign_0_0')],
                                   colliders=[(0, 1)], doors=[]),
    'toyama-glass-museum':    building(6, 6, door=2, door_w=2),
    'toyama-tram':            dict(w=5, h=2, sprites=[('Collidables', 0, 0, 'toyama-tram_0_0')],
                                   colliders=[(x, y) for x in range(5) for y in (0, 1)], doors=[]),
    'toyama-tram-stop':       dict(w=3, h=2, sprites=[('Collidables', 0, 0, 'toyama-tram-stop_0_0')],
                                   colliders=[(x, 1) for x in range(3)], doors=[]),
    'toyama-ramen':           building(4, 4, door=1),
    # the port observation tower: the podium (rows 5-6) and the shaft above it
    # (the middle column up to the gallery) collide; the lantern room is overhead
    'toyama-port-tower':      dict(w=3, h=7, sprites=[('Collidables', 0, 0, 'toyama-port-tower_0_0')],
                                   colliders=[(x, y) for x in range(3) for y in (5, 6)]
                                             + [(1, y) for y in (2, 3, 4)], doors=[(1, 6)]),
    # ---- street accessories (issue #19; art from tools/extract_street.py) --------
    # One sprite on Collidables each, so it Y-sorts by its feet: the bottom cell
    # is solid, the pole / head above it is walk-behind. Maps place the green
    # frame; src/TrafficLights.js swaps the texture through the signal cycle.
    'traffic-light':  dict(w=1, h=3, sprites=[('Collidables', 0, 0, 'traffic-light_0_0')], colliders=[(0, 2)], doors=[]),
    'utility-pole':   dict(w=1, h=3, sprites=[('Collidables', 0, 0, 'utility-pole_0_0')], colliders=[(0, 2)], doors=[]),
    'road-mirror':    dict(w=1, h=2, sprites=[('Collidables', 0, 0, 'road-mirror_0_0')], colliders=[(0, 1)], doors=[]),
    'bus-stop':       dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'bus-stop_0_0')], colliders=[(0, 0)], doors=[]),
    'bicycle-blue':   dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'bicycle-blue_0_0')], colliders=[(0, 0)], doors=[]),
    'bicycle-orange': dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'bicycle-orange_0_0')], colliders=[(0, 0)], doors=[]),
    'scooter-grey':   dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'scooter-grey_0_0')], colliders=[(0, 0)], doors=[]),
    'scooter-red':    dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'scooter-red_0_0')], colliders=[(0, 0)], doors=[]),
    'traffic-cone':   dict(w=1, h=1, sprites=[('Collidables', 0, 0, 'traffic-cone_0_0')], colliders=[(0, 0)], doors=[]),
    # Zebra crossings: flat Over Floor paint, one cell wide, spanning the three
    # cells of a road (stamp two side by side for a wider crossing). -h crosses a
    # horizontal road (origin = its top kerb row), -v a vertical one (origin =
    # its left kerb column). Walkable, no collision.
    'crossing-h':     dict(w=1, h=3, sprites=[('Over Floor', 0, 0, 'crossing-h-top_0_0'), ('Over Floor', 0, 1, 'crossing-h-mid_0_0'),
                                              ('Over Floor', 0, 2, 'crossing-h-bottom_0_0')], colliders=[], doors=[]),
    'crossing-v':     dict(w=3, h=1, sprites=[('Over Floor', 0, 0, 'crossing-v-left_0_0'), ('Over Floor', 1, 0, 'crossing-v-mid_0_0'),
                                              ('Over Floor', 2, 0, 'crossing-v-right_0_0')], colliders=[], doors=[]),
}
for _name, _spec in PREFABS.items():
    if _spec['sprites'] is None:                 # building(): one sprite named after the prefab
        _spec['sprites'] = [('Collidables', 0, 0, f'{_name}_0_0')]


def write_prefab(name, spec):
    keys = sorted({k for (_, _, _, k) in spec['sprites']}) + ['collider-marker']
    sizes = {k: png_size(k) for k in keys}
    kid = {k: i for i, k in enumerate(keys)}
    tileset = {'firstgid': 1, 'name': 'gamev2', 'tilewidth': GS, 'tileheight': GS,
               'tilecount': len(keys), 'columns': 0, 'objectalignment': 'topleft',
               'grid': {'orientation': 'orthogonal', 'width': GS, 'height': GS},
               'tiles': [{'id': kid[k], 'image': f'../../assets/sprites/{k}.png',
                          'imagewidth': sizes[k][0], 'imageheight': sizes[k][1]} for k in keys]}
    layers, lid, oid = [], 1, 1
    bylayer = {}
    for (layer, dx, dy, k) in spec['sprites']:
        bylayer.setdefault(layer, []).append((dx, dy, k))
    for layer in sorted(bylayer, key=lambda l: Z[l]):
        objs = []
        for (dx, dy, k) in bylayer[layer]:
            objs.append({'id': oid, 'gid': 1 + kid[k], 'name': k, 'x': dx * GS, 'y': dy * GS,
                         'width': sizes[k][0], 'height': sizes[k][1], 'visible': True})
            oid += 1
        layers.append({'type': 'objectgroup', 'id': lid, 'name': layer + ' ·obj', 'x': 0, 'y': 0,
                       'opacity': 1, 'visible': True, 'draworder': 'index', 'objects': objs,
                       'properties': props({'gv2layer': layer, 'z': Z[layer], 'collision': False})})
        lid += 1
    data = [0] * (spec['w'] * spec['h'])
    for (dx, dy) in spec['colliders']:
        data[dy * spec['w'] + dx] = 1 + kid['collider-marker']
    layers.append({'type': 'tilelayer', 'id': lid, 'name': 'Colliders', 'width': spec['w'], 'height': spec['h'],
                   'x': 0, 'y': 0, 'opacity': 0.6, 'visible': True, 'data': data,
                   'properties': props({'gv2layer': 'Colliders', 'z': 5, 'collision': True})})
    lid += 1
    meta = [{'id': oid + i, 'name': 'door', 'point': True, 'x': dx * GS + GS / 2, 'y': dy * GS + GS / 2,
             'width': 0, 'height': 0, 'visible': True, 'properties': props({'kind': 'door'})}
            for i, (dx, dy) in enumerate(spec['doors'])]
    layers.append({'type': 'objectgroup', 'id': lid, 'name': 'Meta', 'x': 0, 'y': 0, 'opacity': 1,
                   'visible': True, 'draworder': 'index', 'objects': meta, 'properties': props({'gv2meta': True})})
    tmj = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0', 'orientation': 'orthogonal',
           'renderorder': 'right-down', 'width': spec['w'], 'height': spec['h'], 'tilewidth': GS,
           'tileheight': GS, 'infinite': False, 'nextlayerid': lid + 1, 'nextobjectid': oid + len(meta) + 1,
           'properties': props({'gv2prefab': name}), 'tilesets': [tileset], 'layers': layers}
    json.dump(tmj, open(os.path.join(OUT, name + '.tmj'), 'w'), indent=1)


os.makedirs(OUT, exist_ok=True)
for name, spec in PREFABS.items():
    write_prefab(name, spec)
print(f'wrote {len(PREFABS)} prefabs to tiled/prefabs/')
