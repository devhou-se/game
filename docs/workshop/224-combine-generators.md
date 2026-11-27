# 224 — Combine generators: shared building blocks for interiors

## Context

`gamev2/tools/roomgen.py` gives every generator a `Builder`, the config loader and the kept-door
rules, but each interior generator still writes the rest by hand. The same code is repeated in
`generate_izakaya`, `_konbinis`, `_discount_stores`, `_houses` (three builders), `_shrines`,
`_palace`, `_temple`, `_chikagai`, `_stations` and `_airports`:

| Repeated | Where |
|---|---|
| The room shell: void fill, a lit floor box at an offset, floor-coordinate `put`/`solid` closures, back wall, side walls, front wall and thresholds, mat cells with hidden exit transporters, a hand-written `boundary` polygon, `interior` and its flags | all eight interior generators (10 `fill('office-void-autotile')`) |
| "Sprite plus solid footprint" helper, under five names and signatures (`solid`, `solid_furniture`, `put_solid`, `stand(layer, x, y, sprite, solid)`, `stand(fx, foot, piece, w, h)`) | every generator above, `generate_sanfranbourne`, `generate_sendai` (`solid_rect`), `hokuriku.Kit.solid_rect` |
| Opening the host's door: pop the collider, replace the transporter in place by cell, delete duplicates, else append | 8 copies (plus the izakaya's signage, same idiom) |
| Flood-fill "every floor cell can be reached" | houses, chikagai (the other six have none) |
| `png_size`, `register_metadata`, md5 seeds, "Label · Town n" names, the railing-run loop | konbinis / discount stores / houses / shrines; stations / airports |

Outcome: a new interior is a short script that composes shared blocks (shell, walls, props, doorway,
host door) and adds only its own art table and layout. The committed world does not change: every
generator still reproduces `config.json` byte for byte (`tools/check_generators.py`).

## Approach

Three layers, each generator migrated in its own commit and gated by `check_generators.py` and by the
golden sweep under Tests:

1. **Primitives on `rg.Builder`** (room coordinates) — usable by towns and interiors.
2. **Host-door mechanics in `roomgen.py`**, beside `kept_door` / `keep_house_doors`, which already own
   the door rules.
3. **A new module `tools/interiors.py`** with `class Interior`: the shell, working in floor
   coordinates. Not named `generate_*.py` and free of `Shrine`/`PALACE_`/`TEMPLE_`/`House`/`Lobby`
   literals, because tests forbid those strings in other `generate_*.py` files. It holds only what is
   about a void-shell interior; anything a town generator also needs goes in `roomgen.py`.

Each generator keeps what is its own: door discovery rules (which sprite is a door, skip rules,
numbering), art keys, furniture tables, layouts, markers, prints and CLI. Nothing moves between
generators, no generator is merged or renamed, and `check_generators.GENERATORS` is unchanged.

Scope for town generators: they adopt only the Builder primitives where they carry a local copy
(below). Their layout helpers (`generate_sendai`'s `building`/`house`/`trees`/`wall`/`paved`,
Sapporo's roads, `hokuriku.Kit`) stay: the ticket is about interiors, and towns are serial map data.
The two airport terminals are `interior` rooms but not void-shell rooms; they stay on `Builder` and
their own boundary, and take the primitives only.

## Changes

### `gamev2/tools/roomgen.py` (add; nothing existing changes meaning)

- `Builder.solid(x, y, w=1, h=1)` — collider over a `w`×`h` rect (two-argument calls, including
  `prefab.stamp`'s, behave as now).
- `Builder.place(layer, x, y, key, solid=())` — `put`, then a collider on each `(dx, dy)` in `solid`.
- `Builder.prop(key, x, y, w=1, h=1, layer='Collidables')` — sprite on its top-left cell, footprint
  `w`×`h` solid. The footprint is always explicit (the izakaya's 3-wide table is 2 solid).
- `Builder.stand(key, x, foot, w=1, h=2, layer='Collidables')` — a piece `h` rows tall drawn at
  `foot - h + 1`, only its `foot` row solid over `w` cells (walked behind).
- `Builder.railing_row(y, taken, fam='station-railing')` — the end/post/mid run in every gap of row
  `y` (stations and airports; they are towns and terminals, so it does not live in `interiors.py`).
- `block(w, h, y0=0)` — `[(dx, dy)]` offsets for `place` (from `generate_sanfranbourne`).
- `png_size(key)` → pixels from the PNG header; `sprite_cells(key)` → `(max(1, round(w/64)),
  max(1, round(h/64)))`, cached. For `b.prop(key, x, y, *rg.sprite_cells(key))`. `sprite_cells`
  rounds, as the konbini's and the discount store's `put_solid` do; `hokuriku.Kit.dress` floors
  (`w // 64`) and must keep doing so on `png_size`, not switch to `sprite_cells`.
- `register_metadata(cfg, keys)` — from konbinis / discount stores (same anchors, same rounding).
  Only the loop: the discount store's `assert not k.startswith('don-takote'), '… run
  tools/generate_discount_art.py first'` stays in `generate_discount_stores.py`, before the call.
- `pin(items, item)` — replace the entry of `items` on `item`'s `(gridX, gridY)` in place, delete later
  entries on that cell, append if there is none. Returns `item`.
- `open_door(host_room, cell, target, arrive)` — pop `cell` from the `Colliders` layer, then
  `pin(host_room.setdefault('transporters', []), transporter(*cell, target, *arrive, hidden=True))`.
  (The discount store pops from every layer flagged `collision`; every room in the config has exactly
  one, named `Colliders`, so the two are the same — checked.)
- `shut_door(host_room, cell, prefix)` — `generate_houses.seal` moved verbatim (it always assigns
  `transporters`, as now).
- `find_sprites(room, keys, layers=None)` — `[(x, y, key)]` for every tile whose palette key is in
  `keys` (on `layers`, default all), sorted by `(y, x, key)`. Used by both `find_stores`, by
  `find_halls` and by the palace's `towers()` (which re-sorts as it does now). The temple's `leaves()`
  (a prefix match on `rg.DOOR_LAYERS`) and `find_houses` keep their own loops: their matching is not a
  key-set lookup, and their order is what numbers the rooms.

Constraints (asserted by `tools/tests/*.test.js` on the source text): keep the `*_DOORS` / `*_PREFIX`
/ `OWNED_DOORS` rows literally as they are; `roomgen.py` must have exactly one `def keep_…`, and no
`keep_interior_doors` / `KEPT_DOORS`.

One meaning per name: once a generator is migrated it defines no local `solid`, `prop` or `stand`,
and no `place` but the town generators' one-line wrapper that adds `_0_0` and calls `b.place`. Today
`stand` means two things (`stand(layer, x, y, sprite, solid)` in stations, airports,
San Franbourne and the arcade; `stand(fx, foot, piece, w, h)` in the temple and the palace). The
first becomes `place`, the second is `Builder.stand`.

### `gamev2/tools/interiors.py` (new, `import roomgen as rg`)

```python
VOID = 'office-void-autotile'
outline(cells)                  # from generate_chikagai.py, plus a bound on its walk (below)
reachable(walk, starts)         # flood fill over a set of cells -> the cells reached
seed_of(text)                   # int(md5(text.encode()).hexdigest()[:8], 16)
named(cfg, label, host, n=None) # f"{label} · {rooms[host].get('name', host)}" + (f' {n}' if n else '')

class Interior:
    def __init__(self, fw, fh, ox=None, oy=3, w=None, h=None)
        # w = w or max(20, fw + 2*(ox or 1));  ox = (w - fw) // 2 if ox is None
        # h = h or max(15, oy + fh + 3)        (Builder refuses a room under 20x15)
        # b = rg.Builder(w, h), filled with VOID
        # walk = the fw x fh floor as ROOM cells; exits = []
    cell(fx, fy)                                    # floor cell -> room cell
    put(layer, fx, fy, key, replace=False)          # the Builder calls, in floor coordinates
    solid(fx, fy, w=1, h=1)
    place(layer, fx, fy, key, solid=())
    prop(key, fx, fy, w=1, h=1, layer='Collidables')
    stand(key, fx, foot, w=1, h=2, layer='Collidables')
    floor(key_of)                                   # Floor tile key_of(fx, fy) on every floor cell
    back_wall(pieces, depth)                        # [(fx, key, w)]: one piece `depth` rows tall, drawn at
                                                    # row -depth on Collidables, solid w x depth
    side_walls(west, east, above)                   # Floor keys on columns -1 and fw, rows -above..fh-1
    front_wall(key, gap, thresholds=())             # Floor row fh: key off the `gap` columns, thresholds on them
    doorway(fx, host, front, n=2, fy=None, inward=-1, mat=None)
                                                    # n exit cells from (fx, fy or fh), west to east: each is
                                                    # added to walk and gets one hidden exit to `front` (one
                                                    # cell for all, or a list of n). Returns the room cell
                                                    # beside each on the floor: one row up (inward=-1), or one
                                                    # row down (inward=1, a door in a north wall). Draws
                                                    # nothing unless `mat` is given (a Floor key for the cells)
    room(name, npcs=None, pockets=(), **flags)      # b.room(...) with the exits; boundary = outline(walk);
                                                    # interior = True; room.update(flags); asserts every walk
                                                    # cell without a collider (less `pockets`, FLOOR cells) is
                                                    # reached from the exits. Sets `reached` on the Interior
```

- All arguments are floor coordinates, `pockets` included. `walk` alone is room cells (`it.cell(fx,
  fy)` converts), and is public: a generator adds cells that are floor but not exits (a house's
  genkan, the arcade's corridors).
- `exits` are in the order `doorway` was called and are never sorted. That order is the room's
  `transporters` list, so each generator calls `doorway` in the order it lists its exits today (the
  arcade: the order of `chikagai.TOWNS[host]['exits']`, which is not west to east).
- `put` takes whole palette keys. The temple and the palace pass piece names through
  `s = lambda piece: f'temple-in-{piece}_0_0'` today and the shrine has two such mappers (`k`, `s`);
  they stay in the generator and wrap the key at the call (`it.put(layer, fx, fy, s('…'))`).
- `back_wall` is for a piece as tall as the wall (temple, shrine, house, konbini). A wall of stacked
  panels (the discount store: `wall-top` over `wall`) is a `prop` per panel.
- `room()` sets nothing but `interior`; `shopEnabled`, `lanternLight`, `shopMenu`, `drinkingGame` and
  the ownership marker are passed as `flags`. It must not default any of them: the konbini and the
  discount store have no `shopEnabled` key, and adding one changes their bytes.
- `outline` hangs (and grows a list without end) on cells that only touch at a corner: two edges
  leave the shared corner, one overwrites the other in `nxt`, and the walk never comes back to its
  start. Reproduced on `[(0, 0), (1, 1)]`. Now that any generator can pass it any `walk`, the loop is
  bounded: `assert len(path) <= len(nxt), 'the floor is not one piece'` inside it. Valid shapes return
  what they do today.
- The reachability assert is stricter than `play.js lint` (`shop-sealed-floor` / `house-sealed-floor`
  exempt a cell under art). A cell that is closed on purpose is listed in `pockets`.

Checked while designing: `outline()` of the cells inside the committed `boundary` equals that
boundary for all 58 interior rooms, and all are fully reachable from their exits except one cell
under the izakaya's east lantern, room cell (17, 3). The izakaya passes `pockets=[(15, 0)]` (the same
cell in its floor coordinates, `ox=2, oy=3`); the map is not changed here. Checked in review: of 3000
synthetic konbinis and 500 synthetic discount stores built by today's code, none has a floor cell
that cannot be reached, so the new assert does not lie in wait for a future door.

### Generators (one commit each, in this order; output byte-identical after each)

| File | Change |
|---|---|
| `generate_temple.py`, `generate_palace.py` | `build()` uses `Interior(FW, FH, OX, OY)`; local `put`/`solid`/`stand` closures, shell, exits and boundary go (the piece-name mapper `s` stays); the back-wall table goes through `back_wall`; the wiring loop becomes `rg.open_door`. `leaves()` stays as it is; `towers()` may use `rg.find_sprites`; `rg.TEMPLE_DOORS` / `rg.PALACE_DOORS` must still appear. |
| `generate_shrines.py` | Same for `build_interior`; `find_halls` keeps its order and numbering, names via `interiors.named`. Keep the text `rg.cli(__doc__, sys.argv[1:])` before `rg.load_config()` and a use of `rg.SHRINE_DOORS`. |
| `generate_konbinis.py`, `generate_discount_stores.py` | Shell from `Interior` (konbini: `fw=bw-2, fh=bh-4, ox=x0+1, oy=y0+2, w=ROOM_W, h=ROOM_H`); `put_solid` → `b.prop(key, x, y, *rg.sprite_cells(key))`; drop local `png_size`, `register_metadata` (→ `rg.register_metadata`; the discount store keeps its art assert), `store_name`, the wiring loop. Seed strings and the order of `rng` calls must not change (`f"{host}:{door}"`, `f"don:{host}:{door}"`; the konbini draws `bw`, `bh`, then the floor, then furnishes). `build_interior(store)`, `room_key`, `door_transporter`, `ARRIVE`, `ALL_HOSTS` and `def main(argv):\n    hosts = rg.cli(__doc__, argv) or ALL_HOSTS` stay (Osaka and Sapporo import them). |
| `generate_izakaya.py` | `Interior(16, 10, ox=2, oy=3, w=20, h=15)`; `solid_furniture` → `prop`; door via `rg.open_door`, signage via `rg.pin`; `pockets=[(15, 0)]`. Keep the `SIGNS` literals and `npcs=… or [damian, bailey]`. |
| `generate_houses.py` | `build_interior` / `build_lobby` / `build_shop` share `Interior` (their three `solid` closures, boundaries and exits go; the genkan cells are added to `walk`; each has one mat, `doorway(…, n=1)`, the house's a row lower, `fy=FH + 1`); `check_interior` keeps only the "every flavour object can be bumped" half, on the Interior's `reached`; `seal` → `rg.shut_door`, wiring → `rg.open_door`; `seed_of` wraps `interiors.seed_of` with its own string. `main`'s first lines, `SHOP_SIGNS`, the `--variants` JSON and the `--dry-run` message stay exactly. |
| `generate_chikagai.py` | `outline` moves out; local `stand` → `place`; the floor cross is `Interior` plus `walk |= corridors`; the exits are `doorway(…, fy=…, inward=1)` in the north walls and `inward=-1` in the south stem, called in the table's order; inline flood fill goes; wiring → `rg.open_door`. |
| `generate_stations.py`, `generate_airports.py`, `generate_sanfranbourne.py` | Local `stand` → a local `place` (one line: `b.place(layer, x, y, sprite + '_0_0', solid)`), every call site renamed and nothing else about it changed; local `block` → `rg.block`; both railing loops → `b.railing_row`; the inline PNG header read in `generate_stations.py` (train sprites) → `rg.png_size`. Stations' Palace facade carve stays. |
| `generate_sendai.py`, `hokuriku.py` | `solid_rect` bodies call `b.solid(x0, y0, x1-x0+1, y1-y0+1)`; `Kit.dress` reads sizes with `rg.png_size` and keeps its `// 64`. Nothing else. |

List order is what keeps the bytes: a room's transporters stay in the order the generator lists its
exits today (`doorway` call order), host doors are pinned in place, `find_*` numbering is untouched.
Dict insertion order and palette order do not matter (`sort_keys`, and every committed key is already
in the palette).

### Docs and tests

- `gamev2/docs/generators-and-checks.md`: a short "Interior building blocks" part under
  "Generated rooms" — the three layers, the `Interior` calls in the order a generator makes them,
  the worked example below, and what a new interior has to decide:
  - its row in `OWNED_DOORS` and its `{host, door}` marker (or `kept_door` in the town's generator);
  - `shopEnabled=False`, unless it is a store: `interior: true` alone makes every counter a konbini's
    (`Interactions.js`, `Energy.isStore`);
  - `lanternLight` / `shopMenu` if it wants them; a `Shop.VENUES` / `Interactions` rule for a bump;
  - who draws the mat (a `front_wall` threshold, or `doorway(mat=…)`).
- `gamev2/docs/hud-input-touch.md` (lines 12–14) names `generate_konbinis.py` `store_name()` and
  `generate_discount_stores.py` `store_name()`, which go: point both at `interiors.named`.
- `.claude/skills/generate-room/SKILL.md` (lines 10, 67) and `gamev2/tiled/README.md` (line 72): the
  exemplar they name, `generate_machi.py`, no longer exists; point interiors at `tools/interiors.py`
  with `generate_temple.py` as the example. (`tiled/README.md` line 168 is history and stays.)
- `gamev2/tools/tests/generator-blocks.test.js` (new, found by name).

The worked example — the whole of a new interior but its art and its `OWNED_DOORS` row. It goes in
the doc, and the new test builds exactly this in memory (no `save_config`) so the doc cannot rot:

```python
import roomgen as rg
from interiors import Interior

cfg = rg.load_config()
HOST, DOOR, KEY = 'Market', (7, 37), 'TeaRoomMarket1'          # an example, not a room to add
it = Interior(10, 6)                                           # a 10x6 floor, centred in a 20x15 room
it.floor(lambda fx, fy: 'office-warm-autotile_center')
it.back_wall([(fx, 'office-wall-white_0_0', 1) for fx in range(10)], depth=1)
it.prop('office-counter2_0_0', 6, 0, *rg.sprite_cells('office-counter2_0_0'))
inside = it.doorway(4, HOST, (DOOR[0], DOOR[1] + 1), mat='office-warm-autotile_center')
cfg['rooms'][KEY] = it.room('Tea Room', npcs=cfg['rooms'].get(KEY, {}).get('npcs', []),
                            shopEnabled=False, tearoom={'host': HOST, 'door': list(DOOR)})
rg.open_door(cfg['rooms'][HOST], DOOR, KEY, inside[0])
rg.save_config(cfg)
```

## Data and interfaces

No change to `config.json`, its schema, `tilePalette`, `tiled/*.tmj`, `devhouse.world`, the game's
JavaScript or any generator's command line. The only new interface is the Python API above.

## Tests

New `tools/tests/generator-blocks.test.js`, running `python3` from `gamev2/` on a read-only snippet
(the `spawnSync` pattern in `shrines.test.js`; never `save_config`). The snippets use sprite keys that
exist on disk (`Builder.room()` validates them): the ones in the worked example.

- `Builder.solid` rect, `place`, `prop`, `stand`, `railing_row` lay exactly the expected sprite and
  collider cells.
- `rg.pin` / `open_door`: replaces in place keeping the index, removes duplicates on the cell,
  appends when new, and a second call changes nothing; `shut_door` seals and drops only its prefix.
- `Interior`: the worked example yields a 20×15 room, the eight-corner boundary, two hidden exits west
  to east, `interior: true` and the passed flags; a small floor with no `ox` is centred; exits of
  several `doorway` calls keep call order; `inward=1` returns the cell below; a boxed-in floor cell
  fails `room()` unless listed in `pockets` (floor coordinates).
- `outline` on made-up shapes: a rectangle with a mat, a cross (the arcade), mats on two edges (the
  palace) give the expected corners, clockwise from the first (smallest x, then y); a hole, two
  pieces and two cells touching at a corner (both orders) raise instead of hanging (run with a
  `timeout` on `spawnSync`).
- Source text: no room generator (the `GENERATORS` list of `check_generators.py`; art tools have
  their own `outline` / `png_size`) contains `ts[at[0]] = `, `def png_size`, `def outline`,
  `def stand(` or `fill('office-void-autotile')`. This assertion fails until the last generator is
  moved, and every commit must pass `test_game.js`: the test takes its list of migrated files from a
  constant that each migration commit extends, and the last commit replaces it with `GENERATORS`.

Not a test: "`outline(cells inside boundary) == boundary` for every committed interior". It was the
design's check that `outline` can replace the hand-written polygons (it holds for all 58), and
`check_generators.py` proves it for good once the generators call `outline`. As a standing test it
would only constrain a future interior that draws its own boundary (the airports do).

**Golden sweep (run during the migration, not committed).** `check_generators.py` proves only the
inputs the committed world has: 13 konbini doors' seeded boxes, 7 shrine halls (no large blue one),
the house layouts as the towns happened to draw them, one arcade. A block that is wrong for an input
nobody has yet would pass and ship. So, before the first migration commit, in a
scratch copy as `check_generators.py` makes one (`config.json` copied, `tools` / `assets` / `tiled`
linked; never in the repository — `generate_konbinis.py` and `generate_shrines.py` run and save on
import), record `md5(json.dumps(room, sort_keys=True))` of:

- `generate_konbinis.build_interior(store)` for 300 made-up doors (`{'host': 'Market', 'door':
  (i % 60, i // 60), 'front': (0, 0), 'key': 'K', 'name': 'x'}`): every box size, floor and furnishing
  branch;
- `generate_discount_stores.build_interior(store)` for 100 made-up doors;
- `generate_houses.py --variants` (its JSON), `build_interior` for the 4 layouts × 32 seeds,
  `build_lobby`, and `build_shop` for every family in `SHOP_TYPES`;
- `generate_shrines.build_interior(hall)` for red / blue × small / large.

After each of those generators is migrated, run the same script against the new tools: every digest
must be equal. The builder functions keep their names and arguments, so one script serves both sides.
(Run on today's code in review to confirm it is practical: 3000 konbinis and 500 discount stores
build in a few seconds.) The commit message of each migration says the sweep matched.

Run from `gamev2/` after every commit (baseline today: all 20 room generators and `config_to_tiled`
report `ok`; art tools are skipped without Pillow, which this change does not need):

```bash
python3 tools/check_generators.py     # the gate: config.json byte-identical
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/sync_cities.py --check
```

`git diff --stat` must show no change to `config.json` or `tiled/`. No browser regression is needed:
nothing a player can see changes.

## Risks and open questions

- **Byte identity.** The risks are list order and seeded `rng` call order (konbinis, discount
  stores, house variants). One generator per commit with `check_generators.py <name>` and the golden
  sweep between keeps a break local. If a generator cannot be moved onto a block without changing
  its output, leave that part local and say so in the commit rather than bend the block.
- **Tests that read generator source.** The literals named above must survive; `houses`, `lobbies`,
  `shrines`, `palace` and `temple` tests also re-run generators in a scratch copy with `tools/`
  symlinked, so `interiors.py` must import with the script's directory on the path only.
- **New assert.** `Interior.room()` adds a reachability check to six generators that had none. It
  passes for every committed room (izakaya pocket listed) and for 3500 made-up stores; a future
  seeded konbini with a walled-in cell will now fail loudly instead of shipping.
- **Collisions with other work.** Interiors tickets #214, #216, #217, #221 touch the same
  generators. Land this first or rebase them onto it; do not run it beside a town rebuild.
- **Not done here:** folding `generate_sendai`'s town helpers into `hokuriku.Kit`, a shared
  char-grid layout parser (only houses use one), `png_size` copies in non-generator tools
  (`config_to_tiled`, `make_prefabs`, `rehearse_blog`), and closing the izakaya pocket (a map change).
- No open question blocks implementation.

## Review

The design was checked against the code before anyone builds it. Its own claims hold (58 interior
rooms; `outline` reproduces every committed boundary; one unreached cell, the izakaya's; every room
has one collision layer, `Colliders`; `check_generators.py` is green today). What was wrong or
missing, and what was done about it:

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | **The byte gate does not cover what the committed world does not exercise.** The konbini's box is seeded per door (13 doors today), the large blue shrine hall has never been built, houses use the seed bits their towns happened to draw. A block that is wrong for another input passes `check_generators.py` and breaks the next town. | A golden sweep during the migration: digests of rooms built from made-up inputs by the old code, compared after each migration commit. Tried on today's code; it is quick. | Yes — Tests, Risks |
| 2 | **`outline` hangs on cells that touch only at a corner** (reproduced: `[(0, 0), (1, 1)]` never returns; in the other order it asserts). Harmless while one generator fed it one shape; as the shared boundary of every interior, a slip in `walk` stalls an unattended run and eats memory. "Moved verbatim" would ship that. | Bound the walk inside the loop with the assert it already has; test a hole, two pieces and the corner case with a timeout. | Yes — `interiors.py`, Tests |
| 3 | **`doorway` only fits a door in the south wall.** The arcade's north exits arrive one row *below* their cells, and "the room cell just inside" was defined as the row above. Its exits are also in the table's order (north, hall, hall, south), not "west to east" as the design said of all transporters. | `inward=-1 / 1`; exits keep `doorway` call order and are never sorted; the body says so where it said west to east. | Yes — `interiors.py`, Generators |
| 4 | **Nothing said who draws the mat.** Temple, palace and shrine draw it as a `front_wall` threshold; konbini, discount store and izakaya put a Floor tile by hand. A new interior without a front wall would get its exits on void. | `doorway` draws nothing unless `mat=<Floor key>`; the docs list it among the things a new interior decides. An assert "no walkable void" was considered and dropped: the arcade's stair cells are void on Floor on purpose. | Yes (the option); no (the assert) |
| 5 | **`pockets` was in room cells while every other argument is a floor cell.** | Floor coordinates: the izakaya passes `(15, 0)`. `walk` is named as the one thing in room cells. Noted too that the assert is stricter than lint, which exempts cells under art. | Yes |
| 6 | **`Interior(fw, fh)` with the defaults builds a room `Builder` refuses** (under 20×15) for any small floor, i.e. for the "short new interior" the ticket wants. | `w` and `h` clamp to 20 and 15; `ox=None` centres the floor. Every migrated generator passes its own values, so no bytes move (temple, palace, shrine `ox=1`; houses 5, lobby 4, shop 6; izakaya `h=15`; discount `w=27`). | Yes |
| 7 | **One name, two meanings.** `stand(layer, x, y, sprite, solid)` in four generators is not the new `Builder.stand` (a tall piece on its foot). The design allowed "a one-line local alias" without naming it. | The local wrapper is called `place` and only adds `_0_0`; a migrated generator defines no local `solid` / `prop` / `stand`; the source-text test bans `def stand(`. | Yes |
| 8 | **`railing_row` and `register_metadata` were put in `interiors.py`** though their users are stations and airports (towns and terminals) and metadata registration is not about interiors. Station generators would import the interior shell for a loop. | Both go in `roomgen.py` (`Builder.railing_row`, `rg.register_metadata` beside `png_size`). | Yes |
| 9 | **The shared `register_metadata` would lose the discount store's "run generate_discount_art.py first" assert.** | The assert stays in `generate_discount_stores.py`, before the call. | Yes |
| 10 | **`sprite_cells` rounds; `hokuriku.Kit.dress` floors.** "Reads sizes with `rg.png_size`" invites using `sprite_cells`, which moves a collider for any sprite 1.5 cells wide. | Said in both places: `dress` keeps `// 64` on `png_size`. | Yes |
| 11 | **`find_sprites`: "may use" names no user**, so it could land unused, or be forced onto loops it does not fit. | Named: both `find_stores`, `find_halls`, the palace's `towers()`. The temple's `leaves()` and `find_houses` keep their loops. | Yes |
| 12 | **The source-text test cannot pass until the last generator moves**, but each migration is its own commit and every commit must pass `test_game.js`. | The test reads a list of migrated files that each commit extends; the last commit swaps it for `GENERATORS`. | Yes |
| 13 | **"`outline(cells inside boundary) == boundary` for every committed interior" as a standing test** repeats what `check_generators.py` proves once generators call `outline`, and would bind future interiors that draw their own boundary (the airports do). | Replaced by `outline` on made-up shapes; the committed-rooms check stays what it was, a design-time proof. | Yes |
| 14 | **Docs missed.** `docs/hud-input-touch.md` cites `store_name()` in both store generators, which the design removes; `tiled/README.md` line 72 names `generate_machi.py` as the pattern, as the skill does. | Both added to the docs list. | Yes |
| 15 | **Ticket gap: nothing showed that a new interior really is short**, or what it must decide beyond the shell (`interior: true` alone makes a room a konbini). | A worked example (a dozen lines) in the docs that the new test builds, and the list of decisions. | Yes |
| 16 | **`Interior.put` takes whole keys; the temple, palace and shrine closures take piece names.** A silent mismatch for whoever migrates them. A `key=` mapper on `Interior` would hide it. | The mappers stay in the generators and wrap the key at the call. No mapper on `Interior`: the shrine has two. | Yes (the note); no (the mapper) |
| 17 | **`back_wall` does not fit a wall of stacked panels** (the discount store's `wall-top` over `wall`). | Said so: those are a `prop` per panel. | Yes |
| 18 | **Houses' bump check needs the flood `room()` already ran.** | `room()` leaves `reached` on the Interior. | Yes |
| 19 | **Mixed argument order**: `put` / `place` take the layer first, `prop` / `stand` the key first. | Not changed. `place` keeps the signature its four generators use, so their migration is a rename; `prop` keeps the houses', izakaya's and konbini's. A swapped argument is caught at once (`Builder.validate` finds no such sprite, or the byte gate fails). | No |
| 20 | **Simpler alternative: Builder primitives and `open_door` only, no `Interior`.** It would remove the wiring copies and the helper zoo at a fraction of the risk. | Not taken: the shell (void, offset closures, mats, exits, the hand-written boundary) is the largest repeated part and the one a new interior has to get right; the sweep (1) is what makes moving it safe. The order of commits already lands the primitives first, so stopping after them is possible if the shell fights back. | No |
| 21 | Smaller things left out: a `kept_npcs` helper (three one-liners that differ, the izakaya's has a default cast), a shared closing report (every generator prints its own), merging `place` into `prop`. | None: each would save a line or two and blur a block. | No |

This stage changed no code. The baseline was re-run (`check_generators.py` on 13 room generators,
the interior ones among them: all `ok`); the blocks themselves are untested until they are written.

## After the konbini redesign (#221)

#221 landed on master while this was in review and rewrote `generate_konbinis.py` (text-grid plans, the
`konbini-*` kit, a two-row back wall). Master was merged in and the konbini row of the table above was redone
on the new generator; what differs from the design:

- The store is `Interior(fw, FH, ox=(ROOM_W - fw) // 2, oy=FY, w=ROOM_W, h=ROOM_H)`: `floor`, `side_walls`,
  `front_wall` (the mat is its one threshold), `back_wall`, `stand` for what leans on the wall, `prop` for the
  rest, `doorway`, `room`. No seeded box, `put_solid`, `sprite_cells` or `register_metadata` (the art tool
  registers the kit; the generator still asserts every key it placed is registered). `plan_of` draws from
  `interiors.seed_of` of the same text, in the same order.
- `check_store()` keeps the store's own rules (a free cell under what sells, a free side on the rest, the way in
  free) on `it.reached`; its flood fill is `Interior.room()`'s.
- Three additions to `Interior`, each needed to reproduce #221's rooms byte for byte and off by default:
  `side_walls` / `front_wall` take `layer=` (the kit's wall tops are `Over Floor` art on the void, not Floor
  tiles); `doorway(mat=)` also takes `key_of(fx, fy)` (the mat's two cells are two tones);
  `back_wall(..., view=True)` puts the wall in the boundary (`it.view`: #221 drew its outline round the wall so
  a phone's camera does not cut it off), and `room()` fails if a `view` cell is neither floor nor solid.
- Golden sweep against master's generator: 3000 made-up stores (all 144 plans: 3 layouts x 2 mirrors x 24
  stocks), plus 500 Don Takotes, the four shrine halls, 4 house layouts x 64 seeds, the lobby and the shops
  before and after the `Interior` additions.
