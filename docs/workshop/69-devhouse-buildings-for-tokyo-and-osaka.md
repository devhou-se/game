# 69 — Devhouse buildings for Tokyo and Osaka

## Context

The trips' houses are not in the game. The owner wants one Devhouse per city, each an accurate
Easter egg of the real floor plans attached to the ticket:

- **Tokyo, Minato**: six floors. 1F and 2F are closed to us: only the staircase, which has the same
  footprint on every floor; the street entrance is at the bottom of the plan and leads to the up
  stairs only. 3F living/kitchen/dining, 4F bedroom, 5F tatami room and bathroom, 6F bedroom,
  dining and kitchen.
- **Osaka, Dotonbori**: four floors. 1F kitchen/dining and entrance, 2F and 3F tatami bedrooms,
  4F a tatami room and the outdoor zen garden.

Outcome: a Devhouse building stands in each city, its door opens, and every floor is a room you
can walk through, joined by stairs. All paths below are under `gamev2/`.

## Approach

**One room per floor, built on `tools/interiors.py`** by a new `tools/generate_devhouses.py`, the
way `generate_temple.py` builds its hall. A stair cell is a hidden transporter laid with
`Interior.doorway(..., mat=<stair tile>)` whose "host" is the next floor's room, so no engine
change is needed for stairs. Ten rooms: `DevhouseTokyo1F..6F`, `DevhouseOsaka1F..4F`.

**Sites.**

| | Host room | Prefab (new) | Stamp at | Door cell | Front cell |
|---|---|---|---|---|---|
| Tokyo | `Park` (ported) — the empty paved square under Tokyo Tower's feet, cells x 6..18, y 7..18; the Tower is in Minato | `devhouse-tokyo`, 5x8 | 10,9 | 13,16 | 13,17 |
| Osaka | `Osaka` (generated) — the north-bank lot of the black townhouse beside Don Takote, on Dotonbori | `devhouse-osaka`, 3x7 | 9,10 | 10,16 | 10,17 |

Each gets its own exterior sprite rather than a re-used two-storey townhouse: the buildings are six
and four storeys and are meant to be recognised. The Osaka Devhouse replaces the townhouse that is
`HouseOsaka1` today (same door cell), so Osaka's generic houses renumber to `HouseOsaka1..2`.

**Interiors** re-use the `home-*` kit (boards, tatami, walls, kitchen, fridge, beds, futons, tansu,
plants) plus a small `devhouse-*` kit for what a home has not needed so far (stairs, partitions,
dining sets, bathroom fixtures, the garden). Floors are data: one character grid per floor
(below), already checked for row lengths, footprints and reachability.

**Stairs.** A stair cell (`u` up, `d` down) has exactly one free cell directly north or south of it:
its *arrival cell*. Taking `u` on floor N puts you on the arrival cell of `d` on floor N+1; taking
`d` on floor N+1 puts you on the arrival cell of `u` on floor N. Arrival cells are never
transporters. Stair tile keys contain `stairs`, which `Trips`/`blog_to_npc` already exclude from
start and placement cells.

**A held key must not carry you through two flights.** A room change does not clear input:
`Character`'s move ends in `checkTransporter()`, `RoomManager.switchRoom` fades for 750 ms, and
`InputHandler.held()` is still true when it ends, so the same step is taken again from the cell
you arrive on. The rule the grids keep, and the test checks: *for every stair cell and street
door, and every direction it can be entered from, that step repeated from the arrival cell at the
other end does not land on a transporter.* In practice the two ends of a flight are entered in
opposite directions. In Tokyo `u` is on the row below the floor (entered walking south) and `d`
is inside the stair hall at the foot of a `#` stairwell (entered walking north or west); with
both on the front row, as first drawn, holding ↓ on 1F's up stair took you up and straight back
down, on every pair of floors. Osaka's stairs already keep the rule.

## Changes

### `tools/generate_devhouse_art.py` (new, Pillow; style of `generate_house_art.py`)

Draws into `assets/sprites/`, registers `spriteMetadata` for anything larger than a cell
(`rg.register_metadata`; anchors unrounded) and `tileNames`. Cells are 64px.

- Exteriors (one sprite each): `devhouse-tokyo_0_0` (5x8; a slim six-storey block: six window rows
  must read, entrance at column 3 of the ground floor) and `devhouse-osaka_0_0` (3x7; a narrow
  four-storey townhouse, entrance at column 1, greenery over the roof parapet for the garden).
- Floor tiles (1x1): `devhouse-stairs-up_0_0`, `devhouse-stairs-down_0_0`, `devhouse-tile_0_0`
  (wet rooms), `devhouse-gravel_0_0`, `devhouse-stepping-stone_0_0`.
- Walls: `devhouse-wall-h_0_0`, `devhouse-wall-v_0_0` (1x1 partitions), `devhouse-stairwell_0_0`
  (1x1, a flight seen from above), `devhouse-door_0_0` (1x2 back-wall piece, a locked door),
  `devhouse-fence_0_0` (1x2 back-wall piece, bamboo fence).
- Furniture: `devhouse-table-wide_0_0` (4x1), `-table-tall_0_0` (1x3), `-table-small_0_0` (1x2),
  `-chair-n|s|e|w_0_0` (named for the side of the table it sits on; it faces the table),
  `-stool_0_0`, `-counter_0_0` (2x1), `-sofa_0_0` (1x3), `-armchair_0_0`, `-side-table_0_0`,
  `-bunk_0_0` (1x2), `-basin_0_0`, `-toilet_0_0`, `-shower_0_0`, `-bath_0_0` (1x2),
  `-washer_0_0`, `-clothes-rack_0_0` (1x2).
- Garden: `devhouse-rock_0_0`, `-shrub_0_0`, `-lantern_0_0`, `-garden-seat_0_0`,
  `-water-bowl_0_0` (goldfish in it).

### `tools/make_prefabs.py`

Two rows beside `highrise-*`: `'devhouse-tokyo': building(5, 8, door=3)`,
`'devhouse-osaka': building(3, 7, door=1)`. Re-run it.

### `tools/roomgen.py`

`DEVHOUSE_DOORS = {'devhouse-tokyo_0_0': [(3, 7)], 'devhouse-osaka_0_0': [(1, 6)]}`,
`DEVHOUSE_PREFIX = 'Devhouse'`, and the row `DEVHOUSE_PREFIX: ('devhouse', DEVHOUSE_DOORS)` in
`OWNED_DOORS`, so a rebuild of Osaka keeps the door (`keep_house_doors`).

### `tools/generate_osaka.py`

Line 176: `b.stamp('house-black', 9, 11)` becomes `b.stamp('devhouse-osaka', 9, 10)` (sealed; the
lanterns at 8 and 12 stay). No room key or `DEVHOUSE_` name appears in this file.

### `tools/generate_devhouses.py` (new)

Module-level script like `generate_temple.py`: `rg.cli(__doc__, sys.argv[1:])`, `rg.load_config()`,
build, `rg.save_config(cfg)`. Imports only `roomgen` and `interiors`. Two rules other tests
enforce on every `generate_*.py`, this one and the art tool included: `rg.cli(...)` comes before
`rg.load_config()` (`houses.test.js`), and the file never contains another owner's names, not
even in a docstring: `Shrine[A-Z]`, `SHRINE_`, `PalaceHall`, `PALACE_`, `TempleMarket`,
`TEMPLE_`, `temple-in-` (`shrines`, `palace` and `temple` tests). Say "the way a worship hall is
built", not its room key.

- Finds each building with `rg.find_sprites(host_room, [sprite])` (exactly one, else an error);
  door = sprite cell + `rg.DEVHOUSE_DOORS[sprite][0]`, front = the cell below it.
- Shells (stair cells land on the same room cells on every Tokyo floor):
  - Tokyo 3F–6F `Interior(14, 8, ox=3, oy=4, w=20, h=15)`; Tokyo 1F–2F
    `Interior(2, 4, ox=15, oy=8, w=20, h=15)`. In room cells: down is (15,10), on the floor under
    the stairwell at (15,9); up is (16,12), on the row below the floor; 1F's street mat is
    (15,12); the arrivals are (15,11) and (16,11).
  - Osaka `Interior(9, 10, ox=5, oy=4, w=20, h=17)`. Street mat at room (10,14), arrival (10,13).
- Two passes: (1) parse `FLOORS`, collect each floor's stair cells and arrival cells; (2) build.
  Per floor: `it.floor` (zones below), `it.back_wall(pieces, 2)` from the `wall` string,
  furniture with `it.prop` (footprint solid), `it.stand` for `K R D` (foot on their row, drawn one
  row up), `it.put('Over Floor', …)` for cushions, then the exits last:
  `it.doorway(fx, <other floor key>, <its arrival cell>, n=1, fy=fy, inward=±1, mat=<stair tile>)`
  for `u`/`d` (a stair inside the floor is the same call: `fy` is its row, the cell is already
  in `walk`, and `mat` replaces the floor tile under it), and for `=`
  `it.doorway(fx, host, front, n=1, mat='home-genkan_0_0')` plus `home-doormat_0_0` on Over
  Floor. No side or front walls, as in a house.
- `it.room(name, npcs=<kept from the existing room>, shopEnabled=False,
  devhouse={'host': host, 'floor': n})`; the 1F marker also has `'door': [x, y]`, in the host's
  cells. Only the street door is an owned door: `rg.owned_door` is asked about every transporter
  into a `Devhouse…` room, the stairs included, and says no for them only because the other
  floors' markers have no `door`. Do not give them one.
- Names lead with the floor: `Devhouse 3F · Tokyo`, `Devhouse 1F · Osaka`, … (literals `Tokyo`
  and `Osaka`: Park's own name is "Park", so not `interiors.named`). A phone's one-row HUD bar
  shows `hudBrief(name)`, the part before the ` · `: "Devhouse 3F" is 11 characters, which fits
  beside the countdown at both phone widths (13 at 844x390, 11 at 667x375) and says which floor
  you are on. `Devhouse Tokyo · 3F` would have shown "Devhouse Tokyo" on every floor, 14
  characters, with no countdown, and put ten names on `hud-phone-layout.test.js`' two exact
  lists of rooms that drop it.
- Osaka 4F also gets `lanternLight=True`: an `interior` room is never graded by day and night
  (`DayNight.gradeFor`), and a roof garden lit like noon at midnight does not read as outdoors.
  With the flag it dims at night and its lantern glows, as a worship hall does. The other nine
  floors are lit rooms and stay ungraded.
- `rg.open_door(cfg['rooms'][host], door, <1F key>, <1F arrival>)`. A re-run leaves `config.json`
  byte-identical.

Floor zones (default `home-wood-floor_0_0`; tatami is `home-tatami-green_w|e` chequered as in
`generate_houses.py`): Tokyo 3F–6F `devhouse-tile` on cols 12–13, rows 0–2; T5F tatami (0,0)–(6,7).
O1F, O2F tile (0,0)–(2,2); O2F tatami (0,4)–(2,5), (0,7)–(2,9); O3F tile (0,0)–(2,2), (7,9)–(8,9),
tatami (4,0)–(8,2), (0,6)–(2,9); O4F gravel rows 0–3 (`:` cells `devhouse-stepping-stone`), tatami
(0,5)–(4,9).

Legend. 1x1: `.` free, `|` `-` partition (v/h), `#` stairwell, `u` `d` stairs, `=` street mat,
`n s w e` chairs, `o` stool, `z` cushion (`home-zabuton-*`, walkable), `t` side table,
`c` armchair, `p` `home-plant`, `l` `home-andon`, `g` `home-getabako`, `b` basin, `x` toilet,
`h` shower, `m` washer, `r` rock, `y` shrub, `i` lantern, `q` garden seat, `k` water bowl,
`:` stepping stone. Multi-cell, capital at the top-left and `+` on the rest: `K+` `home-kitchen`,
`R` `home-fridge`, `D` `home-tansu`, `B` `home-bed` (1x2), `F` `home-futon-blue|rose` (1x2),
`Y` bunk (1x2), `J` sofa (1x3), `Q+` `lobby-sofa` (2x1), `T+++` table wide, `M` table tall (1x3),
`H` table small (1x2), `X+` counter, `A` bath (1x2), `C` clothes rack (1x2). `wall` (each piece
1x2, sprite `<name>_0_0`): `p` `home-wall-sand`, `n` `home-wall-window-sand`, `u`
`home-wall-fusuma`, `s` `home-wall-shoji`, `L` `devhouse-door`, `f` `devhouse-fence`. `front` is
the row below the floor.

```python
FLOORS = {
 'T1F': dict(wall='Lp', rows=['.p', '..', '..', '..'], front='=u'),
 'T2F': dict(wall='Lp', rows=['..', '#.', 'd.', '..'], front=' u'),
 'T3F': dict(wall='ppnppppppnpppp', front='             u', rows=[
    '....K+RK+..|bx',
    'J.............',
    '+..nnnn....|..',
    '+..T+++....|--',
    '...ssss.......',
    '...........|#.',
    'p..oooo....|d.',
    '...X+X+....|..']),
 'T4F': dict(wall='ppnpppnppppppp', front='             u', rows=[
    'D.Y..Q+....|bx',
    '..+...........',
    '...........|..',
    '...........|--',
    '..............',
    '...........|#.',
    '.B..B..B...|d.',
    '.+..+..+..p|..']),
 'T5F': dict(wall='uuuupppppLpppp', front='             u', rows=[   # L: "Staff Only"
    'D......|...|bA',
    '.......|.....+',
    '.F.F.F.|...|.x',
    '.+.+.+.....|--',
    '.......|......',
    '..z.z..|...|#.',
    '.......|...|d.',
    'l.....p|..p|..']),
 'T6F': dict(wall='ppnppppnpppppp', front='              ', rows=[   # two single beds end to end
    'B..|.......|bm',
    '+.............',
    'B..|...wHe.|..',
    '+..|...w+e.|--',
    '..............',
    '...........|#.',
    '...........|d.',
    'X+X+X+...p.|..']),
 'O1F': dict(wall='pnppppppp', front='     =   ', rows=[
    'hb.|K+R..',
    '...|.....',
    'x.......g',
    '----...|#',
    '...n...|#',
    'D.wMe..|#',
    '..w+e..|#',
    '..w+e..|u',
    'p..s.....',
    'p........']),
 'O2F': dict(wall='pnppnpppp', front='         ', rows=[
    'hb.|....p',
    '...|.....',
    'x......|d',
    '----...|#',
    'B.l|..c|#',
    '+.....t|#',
    '----..c|#',
    'B..|...|u',
    '+........',
    '..l|.....']),
 'O3F': dict(wall='pnppnpppp', front='         ', rows=[
    'hb.|.B..t',
    '...|.+...',
    'x..|....l',
    '--.|-.---',
    'm........',
    '----..|du',
    't..|..|##',
    'B.....|##',
    '+..|..|--',
    '..l|....x']),
 'O4F': dict(wall='fffffffff', front='         ', rows=[
    'yyr....:y',
    '.:..k..:y',
    '.:.....:.',
    'i::::qtq.',
    '-.-------',
    '.ztz.|bC#',
    'B.B.B|.+#',
    '+.+.+|..#',
    '........d',
    'l...p|...']),
}
```

Stair cell → arrival cell (floor coordinates), for the tests. Tokyo 3F–6F: `d` (12,6)→(12,7)
under the stairwell at (12,5), `u` (13,8)→(13,7). Tokyo 2F: `d` (0,2)→(0,3) under the stairwell
at (0,1), `u` (1,4)→(1,3). Tokyo 1F: street mat (0,4)→(0,3), `u` (1,4)→(1,3). Osaka: O1F `u`
(8,7)→(8,8), mat (5,10)→(5,9); O2F `d` (8,2)→(8,1), `u` (8,7)→(8,8); O3F `d` (7,5)→(7,4), `u`
(8,5)→(8,4); O4F `d` (8,8)→(8,9).

These grids were checked by script: row lengths, footprints, every free cell reached from the
exits, one arrival cell per stair, and no held-key bounce on any flight or street door.

A grid may move a piece by a cell where lint or the screenshot demands it. What may not change
is what the plans show, which `devhouse.test.js` counts from `config.json` (sprites by key):

| Floor | Must be there |
|---|---|
| T1F, T2F | nothing but the stairs, a plant on 1F and the locked `devhouse-door` on the wall |
| T3F | 2 kitchens and a fridge; the wide table with 8 chairs; the 1x3 sofa; 2 counters with 4 stools; basin and toilet |
| T4F | 3 beds and a bunk; tansu; `lobby-sofa`; basin and toilet |
| T5F | 3 futons on tatami, 2 cushions, tansu, andon; bath, basin and toilet; the "Staff Only" door; fusuma on the wall |
| T6F | 2 beds end to end on the west wall; the small table with 4 chairs; 3 counters; basin and washer |
| O1F | kitchen and fridge; the tall table with 8 chairs; shower, basin and toilet; getabako on the east wall; tansu |
| O2F | 2 beds, each in its own tatami room; 2 armchairs and a side table; shower, basin and toilet |
| O3F | 2 beds; washer; shower, basin and 2 toilets |
| O4F | gravel on rows 0–3 with stepping stones, a rock, shrubs, the lantern, 2 seats and the water bowl; fence for a back wall; 3 beds on tatami; basin and clothes rack |

The stair cells, the zones and this table stay; the implementer corrects a count here only by
looking at the plan again (the five images on the ticket).

### Other code

- `tools/check_generators.py`: `'generate_devhouses'` in `GENERATORS` (before `districts`),
  `'generate_devhouse_art'` in `ART_TOOLS`.
- `tools/world-model.js:523`: `const homely = roomConfig.house || roomConfig.lobby || roomConfig.devhouse;`
- `src/utils/Places.js:66`: the hop limit `4` becomes `8` (Tokyo 6F is six room changes from
  Park; today it would resolve to no place on the Japan map).
- `src/utils/Interactions.js`: flavour rules in the house voice (lowercase, dry, one line), each
  `{ kind, group: 'flavour', pattern: /^devhouse-…/, footprint: true, say }`: `devhouse-door`
  (locked, not ours), `-bath`, `-washer`, `-water-bowl` (the goldfish), `-bunk`. Not the tables
  (Osaka's is ringed by chairs and lint wants a flavour fixture to have a free side) and not the
  chairs: there are twenty, a flavour line fires when you walk into its fixture, and they ring
  the tables you walk round, so the same line would toast again and again.
- `src/utils/Glows.js`: a row for `devhouse-lantern_0_0` (a warm spot, as `palace-in-andon_0_0`
  has), so the garden's lantern is lit on Osaka 4F at night. Rows only light where the grade has
  lights, so no other room changes.
- `tools/check_distinct.py`: `devhouse-` in `LANDMARK_ART`; `--update` the baseline if Osaka's
  share moves.

### Data: run order (from `gamev2/`, Pillow needed)

Plain `python3` here has no Pillow and `pip install` is refused (PEP 668): make a venv once,
`python3 -m venv /tmp/pil && /tmp/pil/bin/pip install Pillow`, and use `/tmp/pil/bin/python3`
for every line below and for `check_generators.py`. Export `PYTHONDONTWRITEBYTECODE=1` first:
`tools/__pycache__/*.pyc` is tracked, and running the tools rewrites it (if it happens,
`git checkout -- gamev2/tools/__pycache__`).

```bash
python3 tools/generate_devhouse_art.py && python3 tools/make_prefabs.py
python3 tools/generate_osaka.py                 # townhouse out, Devhouse in, sealed
python3 tools/generate_houses.py Osaka          # HouseOsaka1..2; the config room HouseOsaka3 goes
git rm tiled/houseosaka3.tmj                    # nothing else removes it, and no check notices it
python3 tools/stamp_prefab.py Park --add devhouse-tokyo 10 9    # ONCE: Park has no generator
python3 tools/generate_devhouses.py
python3 tools/config_to_tiled.py Osaka Park HouseOsaka1 HouseOsaka2 \
    DevhouseTokyo1F DevhouseTokyo2F DevhouseTokyo3F DevhouseTokyo4F DevhouseTokyo5F DevhouseTokyo6F \
    DevhouseOsaka1F DevhouseOsaka2F DevhouseOsaka3F DevhouseOsaka4F
python3 tools/make_worldmap.py
```

Everything but the stamp can be re-run at will. The stamp is a one-off edit of a ported room:
a second run refuses (the cells are taken), which is the right answer, so after a rebase that
kept Park's stamp, skip that line. `generate_houses.py` deletes a stale `House<Town><n>` room
from `config.json` but not its `tiled/*.tmj`, and `check_generators.py` only compares the maps
of rooms that are in the config, so the orphan has to be removed by hand.

### Docs

`docs/landmarks-and-towns.md`: a "Devhouses" section (sites, floors, the stair rule and the
held-key rule, run order); House interiors table row `Osaka | HouseOsaka1..2`, count 21 → 20.
`docs/generators-and-checks.md`: the generator and art tool. `docs/buildings-and-street-props.md`:
the two prefabs, and the lantern's row under "Neon and lit fronts at night".

## Data and interfaces

- `config.json`: ten new rooms with `interior: true`, `shopEnabled: false`,
  `devhouse: {host, floor[, door]}` (`DevhouseOsaka4F` also `lanternLight: true`); new
  `tilePalette` entries appended; `spriteMetadata` and `tileNames` for the new art; a hidden
  transporter on Park 13,16 and Osaka 10,16 (the latter retargeted from `HouseOsaka1`);
  `HouseOsaka3` removed and `HouseOsaka1..2` rebuilt.
- `tiled/`: ten new maps, `houseosaka1..2`, `osaka` and `park` re-seeded, `houseosaka3.tmj`
  deleted.
- Saved games: painted-tile progress is counted per room over cells that are still reachable,
  so the renumbered houses cost nobody anything; the ten floors add about 560 cells to the
  total, so a finished save drops a little below 100% until they are walked.
- `roomgen.OWNED_DOORS` gains the `Devhouse` row. No trip, station, landmark or `cities` change.

## Tests

New `tools/tests/devhouse.test.js`:

- the ten rooms exist with their names and markers; only each 1F has `door`, and the host has
  exactly one transporter into it, on the door cell under the Devhouse sprite;
  `rg.owned_door` (through a scratch rebuild, below) keeps that one and no stair;
- every stair is mutual and lands on the arrival cell beside the other end; no arrival cell is a
  transporter; Tokyo 1F has one street exit and one up stair and nothing else, 2F only stairs,
  6F no up stair; the stair cells are the same room cells on all six Tokyo floors;
- **the held-key rule**, from `config.json` alone: for every transporter of the ten rooms and
  the two street doors, and each of the four directions whose cell behind it is walkable, the
  target cell plus that direction is not a transporter cell of the target room. (Run against the
  first draft of the grids this fails ten times, once per direction of every Tokyo flight.)
- a walk with the headless model from the street to the top floor and back out, both cities;
- the fixture table above, floor by floor, counted by sprite key; Osaka 4F: rows 0–3 are gravel
  or stepping stone, the back wall is fence, the garden cells are walkable and reached from the
  tatami room, and the room is `lanternLight` (the other nine are not);
- `hudBrief(hudName(name))` is `Devhouse <n>F` for every floor and at most 11 characters;
- `Places.of` gives every floor its city;
- a scratch `generate_osaka.py` rebuild keeps the door; no other `generate_*.py` contains
  `Devhouse[A-Z]` or `DEVHOUSE_`; no `tiled/houseosaka3*` is left (as `houses.test.js` does for
  `housesapporo`); `play.js lint` is clean for the ten rooms, Park and Osaka.

Updated: `houses.test.js` roll-out `Osaka: [1, 2]`; any test that lists Osaka's or Park's
transporters. `hud-phone-layout.test.js` needs no edit: its room loop covers the new names, and
because the brief fits, its two exact lists of rooms without a countdown stay as they are (if
that test asks for a list change, the name is wrong, not the list).

`tools/browser/regress.js`: a `devhouse-enter` case modelled on `konbini-enter` (place at the
front cell, step in, assert room, fade and HUD name), desktop and phone-landscape, then **the
stair with the key held down**: stand on Tokyo 1F's arrival cell above the up stair (16,11),
`page.keyboard.down('ArrowDown')`, read the room key every 100 ms for 3 s (three flights' worth
if it bounced), then `keyboard.up`. Assert the readings go `DevhouseTokyo1F` … `DevhouseTokyo2F`
and never back, and that the player ends on 2F's cell (15,11). Do not use `hold()` for this: it
lets go as soon as its condition is true, which is the one moment the bug cannot show. The same
on Osaka 1F → 2F with `ArrowUp` from (13,12), ending on 2F's (13,5). Screenshots of every floor,
desktop and 667x375, looked at beside the plans (the ticket's five images); Osaka 4F also with
`?tod=night`.

`check_generators.py` is not green on a clean tree in this container, so "passes" needs a
baseline. Before any change (venv Pillow): the 20 generator rows, `config_to_tiled`,
`make_prefabs`, `generate_cast` and `generate_konbini_art` are `ok`; 26 other art rows already
say `DRIFT` (a different Pillow draws them a pixel off) and two are skipped for want of a
Japanese font; exit code 1. The bar: every row that is `ok` before is `ok` after,
`generate_devhouses` and `generate_devhouse_art` are `ok`, and no file drawn by any *other* art
tool is in the commit (`git status` after the run: only `devhouse-*` sprites, the two prefabs,
the world map, config and tiled). `node tools/test_game.js` is 253 passed before the change.

```bash
cd gamev2
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check
python3 tools/check_generators.py && python3 tools/sync_cities.py --check
python3 tools/rehearse_blog.py && python3 tools/check_distinct.py
node tools/play.js lint Park Osaka DevhouseTokyo3F DevhouseOsaka4F   # and the other floors
node tools/browser/regress.js                                         # see tools/browser/README.md
```

## Risks and open questions

None of these needs the owner before work starts; each is an assumption that is cheap to undo.

- **"Minato" is read as the Park district**, on the empty paved square under Tokyo Tower's feet
  (Park x 6..18, y 7..18: no sprite, collider, NPC or transporter on it today). No new district
  is made. If the owner meant another spot, only the stamp cell changes.
- **Osaka's street door is the opening at the bottom of the 1F plan**, onto Dotonbori. The plan
  also shows a door by the shoe rack on the east wall; a townhouse in a row has no east face in
  this game, so the getabako stays on the east wall where the plan has it and you come in at
  the bottom.
- **Exterior look is invented**: the ticket has floor plans only. Photos of the fronts, if the
  owner has them, would replace the two exterior sprites without touching anything else.
- **Osaka's houses renumber**: `HouseOsaka3` disappears and the two Shinsekai houses become 1
  and 2. They keep their layouts (the seed is the town and the door cell, not the number); only
  keys and names change. Nothing references them by number outside tests and docs.
- **Start cells may move**: Park loses 40 free cells and gains an arrival cell, Osaka loses six
  cells behind the old roof. If `play.js check` or a test reports a moved start or placement,
  accept it only when the new door explains it.
- **Not in scope**: moving the devhouse 2 trip `home` (`Tokyo 29,38`) to the Devhouse, placing
  NPCs or blog landmarks inside, working lifts. Each is a small follow-up if wanted.
- **Phones**: if a floor's back wall is cut off at 667x375, pass `view=True` to `back_wall`.
- **Pillow and bytecode**: see the run order (venv; `PYTHONDONTWRITEBYTECODE=1`).
- **Map data is serial**: this touches `config.json`'s palette, Osaka and Park. Rebase and re-run
  the run order (without the stamp, if Park kept it) rather than merging map conflicts by hand.

## Review

Design adversary pass. Checked against the code, the floor plans and a script over the grids
(reachability, footprints, stairs). "Adopted" means the body above already says it.

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | **Tokyo's stairs bounce you while a key is held.** A room change does not clear input (`Character` → `checkTransporter` → `RoomManager.switchRoom`; `InputHandler.held` is still true after the fade), and every Tokyo `u`/`d` was on the front row, entered walking south, with the arrival cell of one directly above the other. Holding ↓ on 1F's stair: up to 2F, straight back down, and so on for every pair of floors (ten cases by script). The unit tests as written would pass. | The held-key rule (Approach, Stairs). Tokyo `d` moves into the stair hall under a `#` stairwell, entered walking north; `u` stays on the front row. New grids T2F–T6F, new stair list, a unit test of the rule and a browser step with the key held across the fade. | Yes |
| 2 | **The names break a test and hide the floor on phones.** `Devhouse Tokyo · 3F` has the brief "Devhouse Tokyo": 14 characters, over the 13 and 11 a phone bar can show beside the countdown, so all ten rooms would have to join two exact lists in `hud-phone-layout.test.js` (the design said the loop "covers" them), and a phone would show the same name on six floors. | `Devhouse 3F · Tokyo`: brief "Devhouse 3F", 11 characters. No list changes; a test line for the brief. | Yes |
| 3 | **`tiled/houseosaka3.tmj` is left behind.** The run order's comment says it "goes"; nothing deletes it (`generate_houses.py` drops the config room only) and `check_generators.py` only looks at rooms in the config. | `git rm` in the run order; a test that no `tiled/houseosaka3*` remains. | Yes |
| 4 | **"Accurate" could not fail a test.** "A grid may move a piece" with no inventory lets a floor lose its bath or half its chairs and stay green. | A fixture table per floor, counted from `config.json` in `devhouse.test.js`; screenshots compared with the plans. | Yes |
| 5 | **Tokyo 6F's beds were drawn as two bunks side by side.** The plan shows two single beds end to end down the west wall. | `B`/`+`/`B`/`+` in column 0, rows 0–3. | Yes |
| 6 | **The "outdoor" zen garden is lit like a room at midnight.** `interior` rooms are never graded, so the roof is the one outdoor place in the game with no night. | `lanternLight=True` on Osaka 4F and a `Glows.js` row for the garden lantern; a `?tod=night` screenshot. | Yes |
| 7 | **A flavour line on every chair is noise.** Twenty chairs, one line, fired by walking into them as you pass a table; and each chair would need a reachable side for lint for ever. | Drop `devhouse-chair` from the flavour rules; keep door, bath, washer, water bowl, bunk. | Yes |
| 8 | **The run order did not run here.** No Pillow in `python3` and `pip` is refused; tracked `.pyc` files get rewritten by running the tools; `stamp_prefab.py` refuses a second run; and `check_generators.py` exits 1 on a clean tree (26 art rows drift), so "passes" was undefined. | Venv and `PYTHONDONTWRITEBYTECODE=1` in the run order, the stamp marked one-off, and a stated baseline and bar under Tests. | Yes |
| 9 | **Rules the new files would trip over.** Other tests scan every `generate_*.py` for other owners' names and for `rg.cli` before `rg.load_config`; the wall legend said "fusuma" and "shoji" without the sprite names; `interiors.named` would call Tokyo's house "Park". | Spelled out under `generate_devhouses.py`, the legend and the names. | Yes |
| 10 | **`owned_door` is asked about stairs too**, since their targets start with `Devhouse`. It is safe only because 2F and up have no `door` in their marker. | Said so beside the marker; the "only each 1F has `door`" test guards it. | Yes |
| 11 | Saved games: do renumbered houses or new rooms lose painted progress? | Checked: progress is painted ∩ reachable per room, so stale keys are harmless; the total grows by about 560 cells. Noted under Data. | Yes (note) |
| 12 | Simpler: arrive *on* the stair tile, or clear held keys on a room change, instead of rule 1. | Not taken: an engine change that touches every door in the game, against this design's own "arrival cells are never transporters", for something a grid fixes. | No |
| 13 | Simpler: leave out Tokyo 1F and 2F (two rooms of nothing but stairs). | Not taken: the owner describes them on the ticket, and they are what makes it six floors. | No |
| 14 | The Devhouse could be the trip's `home` or a blog landmark. | Not taken: not asked for, and it moves start cells and placements that other tests pin. Stays under "Not in scope". | No |
| 15 | Finer accuracy: a sideways bed for Tokyo 4F's east bed, kitchen units along 6F's south wall as tall `stand` sprites, 3F's living/dining divider. | Not taken as requirements: more art for little gain; the implementer may add them under "a grid may move a piece" if the screenshots ask for it. | No |
| 16 | Where "Minato" is, and which of Osaka 1F's two doors is the street door. | Recorded as assumptions under Risks rather than sent back: each is one coordinate to change. | No (assumption) |

Checked and left alone: the Park square is empty and walkable; the Osaka lot is inside the
Dotonbori district's bounds; `building()` puts the sprite on Collidables, so `house_door_at`
and `keep_house_doors` find the door; `Places.of` needs 7 hops for Tokyo 6F, so 8 is enough,
and nothing else in `src/` limits hops; `'Devhouse…'` never matches the `House` prefix
(`startswith`); the Osaka grids match their plans and already keep the held-key rule.
