# Design: pagoda interiors (#214)

## Context

Pagodas are sealed scenery. The owner wants each one enterable, with "nice cool interiors": a small square
room round a central pillar with a steep stair. The ticket also asks for a count from the map data and a
decision on upper floors (separate rooms or one room).

**Count** (from `config.json` room layers; coordinates are the district's own):

| Room (HUD name) | What stands there | Door cells → front cells | Result |
|---|---|---|---|
| `Market` (Asakusa) | one five-roofed pagoda: `pagoda-floor_0_0` at 10,10 on `Collidables` under `red-pagoda-spacing` ×2 and `red-pagoda-roof` | 11,12 → 11,13 | opens: `PagodaMarket1` |
| `Park` | three `red-pagoda-small-base_0_0` in one column (34,7 / 34,11 / 34,15), drawn overlapping so they read as one tall tower | 34,9+35,9 and 34,13+35,13: fronts are solid (the next pagoda's roof). 34,17+35,17 → 34,18 / 35,18 | 1 and 2 stay sealed; the front one opens: `PagodaPark3` |
| `Fukuoka` | one `red-pagoda-small-base_0_0` at 57,29 (prefab `pagoda-small`, Tochoji) | 57,31+58,31 → 57,32 / 58,32 | opens: `PagodaFukuoka1` |
| `Tokyo` (Imperial Palace) | two `pagoda-floor_0_0` on `Over Floor` (18,20 and 40,20) | 19,22 and 41,22 already lead into `PalaceHallTokyo1` | not pagodas: the palace's towers (#215), untouched |

Five pagodas, three interiors. No other room has one (`red-pagoda-roofs_*` / `red-small-pagoda-top_*` in
Market are Senso-ji's roofs and gate). No NPC position and no blog stand cell ("the pagoda": Market 10,5,
Park 34,11, Fukuoka 57,29) is on a door or front cell.

Outcome: walk into each of the three, climb every floor to the top, walk back out to where you came in;
doors survive town rebuilds; all checks pass.

## Approach

**One room per pagoda, holding every floor** as a cutaway of the tower: storeys stacked up the screen, ground
floor at the bottom, each narrower than the one below, eaves flaring into the dark at every level and the
roof and spire on top. You walk up each steep stair yourself (it runs through the back wall into a hatch in
the floor above) and the camera scrolls up the tower with you. Chosen over one room per floor because that
costs a 750 ms fade per floor, 10 more rooms and `.tmj` files, and floor numbers that do not fit a phone's
HUD bar; the cutaway is also what makes it read as a tower.

It follows the interior roll-out pattern exactly (houses, shrines, temple): a generator builds the rooms from
scratch, unseals the door cell on the host, puts a hidden transporter on it (replaced in place, so a re-run
is a byte-identical no-op), and a row in `roomgen.OWNED_DOORS` keeps the door through a town rebuild. Finding
pagodas and the stay-sealed rules are `generate_houses.find_houses`, reused, not copied.

Geometry (cells; room `W = 21`, `cx = 10`, `S` storeys, storey `k = 0` is the ground floor):

- `S` and floor widths: `pagoda-floor` 5 → `(9, 9, 7, 7, 5)`; `red-pagoda-small-base` 3 → `(9, 7, 5)`;
  Park's is 5, by an explicit override `TALLER = {('Park', (34, 17)): 5}` (two more pagodas are stacked behind it).
- `H = 7 + 8 * S` (47 or 31). Rows 0..5: roof and spire. `top(k) = 6 + 8 * (S - 1 - k)`. Per storey:
  rows `top`, `top+1` back wall; `top+2 .. top+6` floor, columns `cx - w//2 .. cx + w//2`; `top+7` the floor's
  cut edge and eaves (ground floor: the threshold).
- Heart pillar on every storey: solid at `(cx, top+4)`, drawn 3 tall. On the ground floor it is the
  `shumidan` sprite instead: the pillar on a base 3 wide (solid `cx-1 .. cx+1`, four small Buddhas), with the
  offering box solid at `(cx, top+5)`.
- Stair `k → k+1`: column `sx = cx + 2` (k even) or `cx - 2` (k odd); walkable cells `(sx, top(k)+1)`,
  `(sx, top(k))`, `(sx, top(k)-1)`; it lands on the hatch cell `(sx, top(k+1)+6)`. Alternating sides makes you
  walk round the pillar on every floor.
- Way in: both host doors arrive on `(cx, top(0)+6)`; the mat `(cx, top(0)+7)` is a hidden transporter to the
  front cell of the first open door (the lobby rule for a pair of doors).
- `room['boundary']`, the outline of `floors ∪ stairs ∪ mat` (`interiors.outline`, through the `Interior` shell), holds movement; walls and eaves are flat tiles on
  `Floor` / `Over Floor` with no colliders. Nothing on `Tops` over a stair column.
- Fittings, each on the back-wall rows and bumped from the floor cell below it: ground floor, a candle stand
  each side of the base (on the floor, solid at `(cx ± 3, top+4)`); middle storeys, one fitting at column `2 * cx - sx` (the side
  away from the stair) from `(sutra chests, thousand-Buddha niches)` by `(seed_of(host, door) + k) % 2`; top
  storey, a slatted window at `cx`. One hanging lantern (`Tops`) per storey, not over the stair or hatch.

```
           /\             rows 0-5: roof and spire
       ____||____
       | W  |   |         k=2, 5 wide: window W, hatch h (bottom left)
       |h___|___|
     ____H__________
     |      |    h |      k=1, 7 wide: stair H up at cx-2, hatch h (bottom right)
     |______|______|
    _____________H____
    |  o   [B]   o   |    k=0, 9 wide: stair H up at cx+2, Buddhas and box B, candles o
    |_______[]_______|    the mat under the centre
```

## Changes

All under `gamev2/`.

- `tools/roomgen.py`: `PAGODA_DOORS = {'pagoda-floor_0_0': [(1, 2)], 'red-pagoda-small-base_0_0': [(0, 2), (1, 2)]}`,
  `PAGODA_PREFIX = 'Pagoda'`, row `PAGODA_PREFIX: ('pagoda', PAGODA_DOORS)` appended to `OWNED_DOORS`.
  (`outline(cells)` was to move here from `generate_chikagai.py`; #224 landed first and put it in
  `tools/interiors.py`, so nothing else in `roomgen.py` changes.)
- `tools/generate_houses.py`: `find_houses(cfg, host, kind)` accepts a kind dict as well as a `KINDS` name
  (`K = KINDS[kind] if isinstance(kind, str) else kind`). No behaviour change for existing kinds.
- `tools/generate_pagodas.py` (new, shaped like `generate_shrines.py`): `[Town ...] [--dry-run]` via `rg.cli`;
  no town = every host named in a `pagoda` marker. Per host: `find_houses` with
  `dict(prefix=rg.PAGODA_PREFIX, marker='pagoda', label='Pagoda', what='pagoda', doors=rg.PAGODA_DOORS)`
  (it reads `Collidables` only and excludes doors in use, so the palace towers never appear); delete the
  host's stale `Pagoda*` rooms and shut their doors (`rg.shut_door`); shut skipped ones; build, and open the
  rest with `rg.open_door`, as `generate_houses.apply` does. Room: the `interiors.Interior` shell (#224; its
  floor is the ground floor, the other storeys and the stairs join its `walk`), `interior`,
  `lanternLight`, `shopEnabled: False`, name `Pagoda · <host name>` (a number only if the town opens more than
  one), marker below. Asserts before saving: every floor, stair and hatch cell is reached from the arrival
  cell; every bumpable sprite has a reachable cell below it. Prints the rooms to re-seed and lint.
- `tools/generate_pagoda_art.py` (new, shaped like `generate_temple_art.py`): draws `pagoda-in-*` PNGs into
  `assets/sprites/` and registers them in `spriteMetadata` (the generator appends them to `tilePalette`, 795 to 825): `board-a/b`, `wall`
  (+ `-w`/`-e` ends), `edge` (+ ends), `eave-w/e`, `roof` pieces and `spire`, `stair` (1×3), `hatch`,
  `threshold`, `doorlight`, `pillar` (1×3), `shumidan` (3 wide), `saisen`, `shokudai`, `toro-hang`, `kyozo`,
  `senbutsu`, `window`. Dark timber, vermilion posts, old gold; dim, lit by the candles and lanterns.
- `tools/check_generators.py`: `generate_pagodas` in `GENERATORS`, `generate_pagoda_art` in `ART_TOOLS`.
- `src/utils/Interactions.js`: widen the temple offering rule to `/^(temple|pagoda)-in-saisen/` (the same ¥5
  through `TempleVisit`, no new code); flavour rules (data only, ≤ 96 characters, wording may be tuned):
  `pagoda-in-pillar` "the heart pillar runs from the ground to the spire and touches no floor. it sways in quakes";
  `pagoda-in-shumidan` "four small Buddhas sit round the foot of the pillar, one facing each wind";
  `pagoda-in-kyozo` "chests of sutras tied with cord, labelled in a hand nobody writes any more";
  `pagoda-in-senbutsu` "a wall of tiny gilt Buddhas, a thousand of them. you count eleven and give up";
  `pagoda-in-window` "through the slats: tiled roofs, then more roofs. the wind is louder up here".
- `src/utils/Glows.js`: `Glows.SPRITES` rows for `pagoda-in-shokudai_0_0` and `pagoda-in-toro-hang_0_0`.
- `src/utils/NpcStates.js`: `'Pagoda'` in `HUD_KINDS` (a phone's bar reads "Asakusa pagoda").
- Generated data: run `generate_pagoda_art.py`, then `generate_pagodas.py Market Park Fukuoka`, then
  `config_to_tiled.py PagodaMarket1 PagodaPark3 PagodaFukuoka1 Market Park Fukuoka`. This changes
  `config.json` (three rooms, one collider off and one transporter per door cell on the hosts, palette) and
  `tiled/`. Nothing outdoors looks different, so no world-map rebuild.
- `tools/tests/pagodas.test.js` (new); `docs/landmarks-and-towns.md`: a "Pagodas" section after "Temple main
  hall" (the count table, the cutaway, how to wire a new town) and the House interiors sentence that says
  pagodas want an interior of their own; one line beside the temple's offering in `docs/shop-and-economy.md`.

No new JS file, no new key bindings, no new sprite outdoors.

## Data and interfaces

- Room marker: `pagoda: {host, door: [x, y], doors: [[x, y], ...], storeys: 3 | 5}`.
- Room keys `Pagoda<Host><n>`, `n` in door `(y, x)` order counting sealed ones (Park's open one is 3).
- `tilePalette`: appended only. Save data: nothing new (the offering uses the existing wallet).

## Tests

`tools/tests/pagodas.test.js`, modelled on `temple.test.js` and `houses.test.js`:

- the roll-out is exactly `PagodaMarket1` (5 storeys), `PagodaPark3` (5), `PagodaFukuoka1` (3); Park 1 and 2
  are sealed; `PalaceHallTokyo1` still owns Tokyo 19,22 and 41,22;
- each door both ways, stitched and with `?stitch=0`: in from the front cell, out onto the front cell;
- a walk from the mat to the top storey and back; every floor cell reachable; pillar, box and each fitting
  can be bumped and resolve to the right rule (`offering` in group `temple` for the box);
- the door is kept through a scratch rebuild of Fukuoka (`roomgen.save_config`); `OWNED_DOORS` has the row;
- no NPC on any date and no blog spot on a door or front cell; a generator re-run changes nothing.

Run from `gamev2/`: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js check`,
`python3 tools/check_generators.py` (with Pillow), `python3 tools/sync_cities.py --check`,
`node tools/play.js lint` on the three rooms and three hosts, and `tools/browser/regress.js`. Then play it in
Chromium at desktop size and 667×375 with `?touch=1`, day and night: enter each pagoda, climb to the top,
leave; look at screenshots of every storey (saved to `/work/media/`).

## Risks and open questions

- **The cutaway must read.** The stair, the hatch and the player drawn against wall tiles are the weak
  points; check them in the browser first, before drawing the fittings. If the player sorts behind a wall or
  eave tile, move that tile to `Floor`.
- **Fukuoka's pagoda is due to go** in the #219 rebuild (replaced by `fukuoka-tochoji-hall`). Then
  `keep_house_doors` drops the door and `generate_pagodas.py` with no town deletes `PagodaFukuoka1`; whoever
  rebuilds must re-run it. If another agent holds Fukuoka's map now, land Market and Park and leave Fukuoka.
- New doors can move a trip day's start cell (as #208's did): `play.js check` and the start-position tests
  will say; update those assertions deliberately.
- `play.js lint` may want a rule widened for a room with a `pagoda` marker (`world-model.js`); the
  `house-sealed-floor` rule is not asked for here.
- Owner's taste, not blocking: Park's tower as 5 storeys, the offering box in every pagoda, and the wording
  of the five lines are proposals.
