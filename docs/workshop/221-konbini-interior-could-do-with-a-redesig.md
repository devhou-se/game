# Konbini interior redesign (#221)

## Context

The 13 konbini interiors (`Konbini<Host><n>`, built by `gamev2/tools/generate_konbinis.py`) are the oldest
generated rooms: a chequered blue floor floating in the void, a one-row white wall with office posters, a short
run of coolers, one long row of office shelves, an office desk with a computer for a till, and a stone-paver
door mat. Each store's box size and furniture are random. They read as an office, not a shop.

The newer interiors (houses, tower lobbies, the palace hall, the arcade) have a two-row drawn back wall,
furniture standing against it, purpose-drawn art and a hand-authored floor plan.

Outcome: every 7-Eleven is laid out like a Pokémon Mart (a clerk in a counter nook in one back corner, shelf
blocks you walk around, a door mat at the bottom centre) and dressed like a real 7-Eleven (orange/green/red
stripe, a wall of drink coolers, an open chiller of onigiri and bento, gondolas, coffee machine, ATM, copier,
magazines), drawn with a bespoke `konbini-*` kit. What a store does is unchanged: same room keys, names,
doors, shop lists, stamps, free water and time-travel clock.

## Approach

Rewrite `generate_konbinis.py` on the `generate_houses.py` pattern: a few named text-grid layouts on a shell
with a two-row back wall, a seeded choice of layout, mirror and stock, and a generator-side check. Draw the
kit in a new art tool on the `generate_chikagai_art.py` pattern. Add the kit's sprites to the existing bump
rules in `src/utils/Interactions.js`.

- **Scope is the `Konbini*` rooms only.** No `office-*` sprite is changed or deleted: Don Takote, the
  Tanukikoji shop floors (`ShopSapporo1..3`) and the izakaya still use them.
- **The drinks coolers stay `office-fridge_0_0`** (`generate_cooler_art.py`): it is already bespoke, in the
  right style, and has its own rule and test. It moves from the floor to standing against the back wall.
- **The clerk is part of the counter sprite**, not an NPC: NPCs here are the cast and blog posts, and a bump
  on the counter must open the shop, not a dialogue.
- **The room still floats in the void** like every other interior, but gains thin wall-top edges at the sides
  and front (as the arcade has), so it reads as a room.

### The shell

Room 20x15 as now. The floor is `FW` x `FH` cells with `FH = 6`, `FW` = the layout's width, top-left at
`(FX, FY) = ((20 - FW) // 2, 4)`. The wall is rows `FY-2` and `FY-1`. The door mat is the two middle columns
(`FW // 2 - 1`, `FW // 2`) on row `FY + FH`, each a hidden transporter to the store's `front`; the player
arrives on the cell above the left mat cell, `(FX + FW // 2 - 1, FY + FH - 1)`. `boundary` is the floor
rectangle plus the two mat cells. `interior: true`, no `shopEnabled` key, as now.

### The layouts

One character per cell, unmirrored (counter in the west corner). `wall` is the back wall by column; `floor`
is `FH` rows.

```
'aisles' (12 wide)        'freezer' (12 wide)       'small' (10 wide)
wall  Ttkwwwwwwwww        wall  Ttkwwwwwwwww        wall  Ttkwwwwwww
      Cc.DDDDOOOWA              Cc.DDDOOKWXA              Cc.DDDOOWA
      cc..........              cc..........              cc........
      cc.Gg.Gg.Gg.              cc.Gg.Gg.Ff.              cc.Gg.Gg..
      ...gg.gg.gg.              ...gg.gg....              ...gg.gg..
      ............              ............              ..........
      B.........Mm              B.........Mm              B.......Mm
door       ^^                        ^^                       ^^
```

- wall (1x2 sprites at `(x, FY-2)` on `Collidables`, both cells solid): `w` plain, `k` with the clock,
  `Tt` the tobacco rack (2 wide, behind the till).
- against the wall, floor row 0 only (1x2 sprites placed at `(x, FY-1)` on `Collidables`, solid at `(x, FY)`,
  exactly as `AT_WALL` in `generate_houses.py`): `D` drinks cooler, `O` open chiller (alternate a / b),
  `K` coffee machine, `W` water, `X` copier, `A` ATM.
- floor (on `Collidables`, every cell of the piece solid): `.` free; `Cc` the counter (2x3, top-left at
  row 0); `Gg` a gondola (2x2); `Ff` chest freezer (2x1); `Mm` magazine rack (2x1); `B` basket stack (1x1).

Rules the layouts obey, and `check_store()` asserts for every built room (model it on `check_interior()` in
`generate_houses.py`): every free floor cell is reachable from the arrival cell; the cell under every column
of every `D`, `O`, `K`, `W` and gondola is free (the `shop-no-front` lint); the counter, `A`, `X`, `Ff`, `Mm`
each have a free cell on some side; the cell under the clock wall (`k`, floor row 0) is free; the arrival
cell and both mat cells are free. A new layout must pass the same check.

Per store, from the existing seed (`md5(f"{host}:{door}")`, unchanged): `rng.choice` of the layout, a
left-right mirror (`flip(c, w)` as in `generate_houses.parse`; multi-cell pieces keep their own left and
right, the counter swaps `konbini-counter-w` for `-e`), and the stock of each gondola in reading order from
a seeded shuffle of `snacks, noodles, bread, daily`. If the hash happens to give Asakusa's six stores one
plan, add the store's ordinal to the choice so they differ; the test below requires at least two plans
there.

Around the floor, on `Floor` in the void cells that touch it (as `generate_chikagai.py` lines 129-137):
`konbini-side-w` / `-e` beside it, `konbini-front` under it (not under the mat), `konbini-front-w` / `-e` at
the two front corners. The floor itself is `konbini-floor-a` / `-b` by `(c + r) % 2`; the mat is
`konbini-mat_0_0` on `Over Floor` at the left mat cell, over two floor tiles.

### The kit

`gamev2/tools/generate_konbini_art.py`, copied in structure from `generate_chikagai_art.py`: imports the
palette and helpers of `generate_station_art.py` (`new, box, text, centred, latin, kana`, `ORANGE / GREEN /
RED` for the stripe, as `kiosk()` there uses them), draws at 32px a cell and doubles, 1px ink outline, text
only in the repo's fonts, no randomness that is not seeded, `SPRITES = {key: (fn, label)}`, `--preview
out.png`, registers `spriteMetadata` (`frameCount: 1`, `anchorX: 32 / width`, `anchorY: 32 / height`,
unrounded) and `tileNames`.

| key (`_0_0`) | cells | what it shows | bump |
|---|---|---|---|
| `konbini-floor-a`, `-b` | 1x1 | pale vinyl floor tile, two tones close together | |
| `konbini-side-w`, `-e`, `konbini-front`, `-front-w`, `-front-e` | 1x1 | wall tops seen from above on a void cell; the front one a glazed shopfront | |
| `konbini-mat` | 2x1 | the door mat between parted sliding glass doors | |
| `konbini-wall` | 1x2 | white wall, the orange/green/red stripe along its top, skirting | |
| `konbini-wall-clock` | 1x2 | the same with a round clock | time travel |
| `konbini-wall-tobacco` | 2x2 | the same with the numbered cigarette rack and a small 7 logo plate | |
| `konbini-counter-w`, `-e` | 2x3 | an L counter closing a corner nook: the clerk (cap, striped uniform, facing the camera) in the nook, the till and a hot-snack case on the counter top beside them, the counter's front face along the bottom with a steamer on it. No lettering; `-e` is `-w` flipped | `counter` |
| `konbini-chiller-a`, `-b` | 1x2 | lit open chiller: onigiri and sandwiches; bento and noodles | `snacks` |
| `konbini-coffee` | 1x2 | coffee machine on a cabinet, cups | `drinks` |
| `konbini-water` | 1x2 | hot-water pot and a water tap on a stand, paper cups | `water` |
| `konbini-atm` | 1x2 | bank ATM | flavour |
| `konbini-copier` | 1x2 | multifunction copier | flavour |
| `konbini-gondola-snacks`, `-noodles`, `-bread` | 2x2 | a shelf block: its top with goods seen from above, its front face in three shelves | `snacks` |
| `konbini-gondola-daily` | 2x2 | the same with umbrellas, socks, chargers | flavour |
| `konbini-freezer` | 2x1 | ice-cream chest with sliding glass lids | flavour |
| `konbini-magazines` | 2x1 | low magazine rack | flavour |
| `konbini-baskets` | 1x1 | a stack of shopping baskets | |

A sprite is exactly its cells x 64px; nothing overhangs a cell the player can stand on (the 1x2 pieces stand
over the wall's lower half, as in the houses). No rubbish bin in any of it.

## Changes

- **`gamev2/tools/generate_konbini_art.py`** (new): the kit above.
- **`gamev2/tools/generate_konbinis.py`**: keep `ALL_HOSTS`, `find_stores()`, `store_name()`, the seed, and
  the whole tail that wires the host door (unseal, replace the transporter in place, `save_config`). Replace
  `OFFICE_KEYS`, `furnish()` and `build_interior()` with `LAYOUTS`, the piece tables (`WALLS`, `AT_WALL`,
  `FURNITURE`), `parse(layout, mirror)`, `build_interior(store)` returning `(room, arrive)`, and
  `check_store()`. `register_metadata()` goes (the art tool registers the kit; `office-fridge_0_0` is
  registered by its own tool) and the generator asserts every key it places is in `spriteMetadata`. Rewrite
  the docstring (the run order: art tool, generator, `config_to_tiled.py`, `play.js lint`). Remove the
  comments about corner fillers and nooks that no longer apply.
- **`gamev2/tools/check_generators.py`**: `ART_TOOLS += ['generate_konbini_art']`.
- **`gamev2/src/utils/Interactions.js`** `RULES`: extend the four konbini patterns and add rows; nothing else
  in the file changes.
  - `counter`: `/^(blue-shrine-platform-base|office-counter|konbini-counter)/`
  - `drinks`: `/^(office-(shelf-drinks|shelf-glass|fridge|freezer)|konbini-coffee)/`
  - `snacks`: `/^(office-shelf-snacks|konbini-(chiller|gondola-(snacks|noodles|bread)))/`
  - `water`: `/^(office-watercooler|konbini-water)/`
  - new, beside the existing `clock` row: `{ kind: 'clock', group: 'clock', pattern: /^konbini-wall-clock/,
    footprint: true }` (the wall sprite sits on the upper wall cell; the bump lands on the lower one)
  - new `flavour` rows with `footprint: true` and a `say` line in the voice of the others (lower case, dry,
    one or two short sentences), kinds `atm`, `copier`, `magazines`, `ice-cream`, `sundries` for
    `konbini-atm`, `-copier`, `-magazines`, `-freezer`, `-gondola-daily`. Suggested:
    'the cash machine speaks four languages. your card speaks none of them' /
    'the copier also sells concert tickets. none for tonight' /
    'this week\'s manga, thick as a brick and taped shut' /
    'ice cream, whatever the season. the lid is cold enough to stick to' /
    'umbrellas, socks, phone chargers. everything you forgot to pack'.
- **Generated data** (run from `gamev2/`, with a Python that has Pillow for the first step):
  1. `python3 tools/generate_konbini_art.py` (PNGs in `assets/sprites/`, metadata in `config.json`)
  2. `python3 tools/generate_konbinis.py` (all 13 rooms, the 13 host door targets; `tilePalette` grows at
     its end only)
  3. `python3 tools/config_to_tiled.py` for the 13 `Konbini*` rooms and the hosts `Market Park Sapporo Sendai
     Fukuoka Kanazawa SanFranbourne`
  4. `node tools/play.js lint` for the same rooms; `node tools/play.js render <Room> out.png` and look at one
     store of each layout, mirrored and not.
- **Tests** (`gamev2/tools/tests/`): see Tests.
- **Docs**, to say what is now true: `gamev2/docs/shop-and-economy.md` (the bump table rows for a konbini;
  the paragraph on the row layout and the #182 corner filler; the water line: every 7-Eleven now has a
  dispenser on its back wall), `gamev2/docs/landmarks-and-towns.md` ("Konbini interiors per host": layouts,
  kit, run order), `gamev2/docs/generators-and-checks.md` (the art tool list; the `generate_cooler_art.py`
  paragraph: the cooler now stands against the wall), `gamev2/docs/buildings-and-street-props.md` and
  `gamev2/tiled/README.md` (the lines about konbini corner fillers and walkway rows),
  `.claude/skills/generate-room/SKILL.md` where it describes a konbini's layout.

Commit as one change: `gamev2: <what changed> (#221)`, no attribution lines.

## Data and interfaces

- `config.json`: new `spriteMetadata` and `tileNames` entries for the kit; new keys appended to
  `tilePalette` (never reordered); the 13 `Konbini*` rooms rebuilt (`layers`, `boundary`, `transporters`);
  in each host, only the konbini door transporter's `targetX` / `targetY` change.
- Unchanged: room keys and `name`s, the door cells in the hosts, where you step out (`front`), `interior`,
  `Shop.VENUES`, the save blob, `Stamps`, no new localStorage key, no new JS file.
- `Interactions.RULES` as listed. Don Takote rooms also count as "konbini" to these rules but place no
  `konbini-*` sprite, so nothing changes there.

## Tests

Update:
- `map-data.test.js` "no store has floor its furniture seals off (#182)": keep the lint-clean loop; replace
  the `office-watercooler` position, `dispensers >= 5` and nook assertions with: every `Konbini*` room has
  exactly one `konbini-water_0_0`, against the back wall, with the cell under it reachable from the door.
- `map-data.test.js` "every shelf, cooler and till ... can be bumped": must still pass as written; if the
  fixture count falls under 150, set the threshold to just under the new count rather than loosening it.
- Leave as they are and confirm they pass: the `office-fridge` art test, `world-model-lint.test.js` (walling
  off row `transporters[0].gridY - 2` of `KonbiniMarket1` must still give `shop-no-front`: that row is the
  walkway under the gondolas), `sapporo.test.js` ("you arrive just inside its mat"), the Sendai / Fukuoka /
  Kanazawa door tests, `stitched-city.test.js`, `occlusion-camera.test.js`.

Add `konbini.test.js`:
- every `Konbini*` room: 20x15, `interior`, two exit transporters side by side that both lead to the cell
  below the host's door; the host's door transporter targets the cell above the left one;
- every room has, reachable by a bump from a cell the door leads to (use `Interactions.all` and a flood fill
  as `map-data.test.js` does): one `counter`, at least three `drinks`, at least two `snacks`, one `water`,
  one `clock`, and at least one flavour object;
- the only `office-*` sprites placed in a konbini are `office-fridge_0_0` and the `office-void-autotile*`
  fill;
- the stores are not all alike: at least two layouts and both mirrors occur across the 13, and Asakusa's
  six are not one plan (compare the sorted `Colliders` cells);
- each `konbini-*` PNG is a whole number of 64px cells, its metadata anchor is `32 / width`, `32 / height`,
  the two floor tiles are fully opaque, `konbini-counter-e` is `-w` mirrored;
- `Interactions.match` for each kit key in a konbini room gives the kind in the table, and gives nothing for
  `konbini-chiller-a_0_0` in a room with `shopEnabled: false`.

Run, from `gamev2/`:

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py
python3 tools/sync_cities.py --check
```

then the browser regression (`tools/browser/README.md`; `konbini-enter`, `konbini-shop`, `konbini-exit` are
written against any konbini and should pass unchanged), and play it in Chromium with real keys: walk in from
the street, bump the counter, a cooler, a chiller, a gondola, the water, the clock and a flavour object, walk
every aisle, leave. Do it at 1280x960 and at a phone size in both orientations (`?touch=1`), for one store of
each layout, and save the screenshots to `/work/media/`.

## Risks and open questions

- **Art bytes differ by machine.** In the Workshop container plain `python3` has no Pillow (`pip install
  Pillow` in a venv works), and with it every existing art tool already reports `DRIFT` in
  `check_generators.py`: the pixels are identical but the PNG compression is not (checked on
  `office-fridge_0_0`). So here: run `check_generators.py` with plain `python3` (room generators and Tiled
  maps checked, art tools `skip`) and it must pass; separately confirm `generate_konbini_art.py` run twice
  gives identical files. The PNGs committed from the container may show as `DRIFT` on the owner's machine
  until the tool is re-run there once; say so in the hand-off.
- **Map data is serial.** `config.json` rooms, the palette and `tiled/` conflict with any town rebuild landing
  meanwhile. After a rebase, re-run steps 1-4 rather than merging `config.json` by hand.
- **Phones.** A 12-wide floor is one cell wider than the widest store today (11) and wider than a landscape
  phone's view (10 cells), so the camera scrolls, as it already does in the lobbies. Check the counter nook
  and the back wall are readable at phone zoom; if not, drop to 10 wide for all three layouts.
- **The look is the deliverable.** The table fixes what each sprite is and how big; the drawing is the
  implementer's. Judge it from renders against `HouseSendai2` and `ChikagaiSapporo`, and iterate before
  wiring tests.
- Open, with the choice made here: the clerk is drawn into the counter (not an NPC); the Tanukikoji shop
  floors and Don Takote keep the old `office-*` furniture and will look older than the konbini next to them.
  Both can be revisited by the owner; neither blocks this change.
