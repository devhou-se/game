# Design: smaller Devhouse floors in Tokyo (#228)

## Context

"There's way too much open space for how much furniture is in the room. The room has gotta be like half the
size it is rn."

Measured from `gamev2/config.json` (cells you can stand on / floor cells, stairs excluded):

| Floor | Size | Standable | Share |
|---|---|---|---|
| Tokyo 3F / 4F / 5F / 6F | 14x8 | 71 / 88 / 81 / 80 of 111 | 64-79% |
| Osaka 1F-4F | 9x10 | 50-55 of 90 | 56-60% |
| a konbini, for scale | | | 59-62% |

Tokyo's 3F-6F are the outliers: each is one open room 11 cells wide beside the stair hall, and on a phone
(about 9x5 cells on screen) most of the view is bare boards (`before-tokyo-4f-phone.png` on the ticket).
Osaka's floors are split into small rooms and are already as full as a konbini.

Outcome: Tokyo's 3F-6F hold the same furniture on a floor with about half the walking space. Nothing else
about the houses changes: same rooms, same fixtures, same stairs and street door, same art.

## Approach

Shrink Tokyo's 3F-6F from 14x8 to **10x7** by rewriting their grids in `tools/generate_devhouses.py`
(`FLOORS`, `ZONES`, `shell`) and re-running the generator. The floor data is the only thing that changes;
the engine, the art kit, the palette and `Interactions.js` are untouched.

- The stair hall keeps its three columns (partition, two hall cells) and loses its open row above the
  stairwell. The living area west of it goes from 11x8 = 88 cells to 7x7 = 49 (56%); standable cells go
  71 / 88 / 81 / 80 → **30 / 47 / 42 / 39**, about half on every floor.
- 10x7 is the smallest footprint that holds every floor's fixtures: 3F needs seven rows (kitchen, walkway,
  chairs, table, chairs, stools, counters) and seven columns (sofa, walkway, the 4-wide table, walkway); the
  hall needs seven rows (3-row wet room for 5F's bath, wall, stairwell, stair down, arrival cell). All four
  floors share it so the stairs stay on the same room cells all the way up, as #69 requires.
- The floor is centred in the 20x15 room (`ox=5`), so a desktop shows it in the middle of the screen. 1F and
  2F stay the 2x4 stair hall, moved with the hall above them (`ox=13, oy=7`).
- Every fixture count in the #69 plan (`PLAN` in `devhouse.test.js`) is kept; pieces only move.
- Osaka is left as it is (see Risks).

The grids below were built and checked in a scratch tree: the generator's reachability asserts pass, lint is
clean for `Park` and the six floors, `test_game.js` (296), `play.js check`, `check_generators.py`,
`sync_cities.py --check` and the browser regression (24/24, including `devhouse-enter`,
`devhouse-stair-held`, `phone-landscape-devhouse`) pass with the test edits listed under Tests. Renders:
`after-tokyo-*.png` on the ticket.

## Changes

### `gamev2/tools/generate_devhouses.py`

`shell`:

```python
    return (10, 7, 5, 4, 15) if n >= 3 else (2, 4, 13, 7, 15)
```

`ZONES`:

```python
WET = [('tile', 8, 0, 9, 2)]            # Tokyo's wet rooms, at the head of the stair hall
    'T3F': WET, 'T4F': WET, 'T5F': WET + [('tatami', 0, 0, 4, 6)], 'T6F': WET,
```

`FLOORS` (`T1F` and `T2F` unchanged; Osaka unchanged):

```python
 'T3F': dict(wall='pnpppppppp', front='         u', rows=[
    '..K+RK+|bx',
    '..........',
    'J.nnnn.|..',
    '+.T+++.|--',
    '+.ssss.|#.',
    'p.oooo.|d.',
    '..X+X+....']),
 'T4F': dict(wall='ppnppnpppp', front='         u', rows=[
    'DY.Q+..|bx',
    '.+........',
    '.......|..',
    '.......|--',
    '.......|#.',
    'B.B.B.p|d.',
    '+.+.+.....']),
 'T5F': dict(wall='uuuuppLppp', front='         u', rows=[   # L: "Staff Only"
    'D....|.|bA',
    '.....|...+',
    'F.F.F|.|.x',
    '+.+.+|.|--',
    '.......|#.',
    '.z.z.|.|d.',
    'l...p|....']),
 'T6F': dict(wall='pnppnppppp', front='          ', rows=[   # two single beds end to end
    'B.|....|bm',
    '+.........',
    'B.|wHe.|..',
    '+.|w+e.|--',
    '.......|#.',
    'p......|d.',
    'X+X+X+....']),
```

Hall (floor columns 7-9, the same on all four floors): partition in column 7, open on row 1 (to the wet
room) and row 6 (to the stairs); wet room rows 0-2; `--` row 3; stairwell row 4; `d` row 5; arrival row 6;
`u` on the front row under column 9. Update the docstrings/comments only where they state a size.

Then, from `gamev2/` with `PYTHONDONTWRITEBYTECODE=1`:

```bash
python3 tools/generate_devhouses.py
python3 tools/config_to_tiled.py Park DevhouseTokyo1F DevhouseTokyo2F DevhouseTokyo3F DevhouseTokyo4F DevhouseTokyo5F DevhouseTokyo6F
node tools/play.js lint Park DevhouseTokyo1F DevhouseTokyo2F DevhouseTokyo3F DevhouseTokyo4F DevhouseTokyo5F DevhouseTokyo6F
```

Expected diff: `config.json` (the six `DevhouseTokyo*` rooms and one transporter target in `Park`),
`tiled/devhousetokyo{1..6}f.tmj`, `tiled/park.tmj` (two values). The four Osaka rooms, `tilePalette` and
everything outside `rooms` stay byte-identical. No art tool, no `make_worldmap.py` (interiors are not on
the map), no `devhouse.world` change.

### `gamev2/tools/tests/devhouse.test.js`

Constants that follow the moved cells (see Data and interfaces):

- stair test: up `[[14, 11, 13, 10]]`; down `n === 1 ? [[13, 11, 13, 17]] : [[13, 9, 14, 10]]`; stairwell
  `[[13, 8]]`; its comment (`a stair up at 14,11 and a stair down at 13,9 … 1F's mat at 13,11`).
- held-key "first draft" block: `[down.gridX, down.gridY] = [13, 11]`; copy Floor `'14,11'` to `'13,11'`;
  `[up.targetX, up.targetY] = [13, 10]`; expected
  `['DevhouseTokyo1F 14,11 s -> DevhouseTokyo2F 13,11', 'DevhouseTokyo2F 13,11 s -> DevhouseTokyo1F 14,11']`;
  the same string in the JSDoc example near the top of the file.
- 6F beds: `[[5, 4], [5, 6]]`.

New test, `Tokyo's Devhouse floors are 10x7 in the middle of the room and no more than half of one is bare
(#228)`: for `DevhouseTokyo3F..6F`, the non-void Floor cells that are not exits span exactly x 5-14, y 4-10
in a 20x15 room, and at most 48 of them are `stand`-able (today's values after the change: 30, 47, 42, 39;
before: 71, 88, 81, 80). `PLAN` and every other assertion stay as they are.

### `gamev2/docs/landmarks-and-towns.md`

In "The Devhouses of Tokyo and Osaka", "A floor is data": `14x8 floors` → `10x7 floors, centred in the
room`, plus one sentence: a floor is kept about half furniture (#228; `devhouse.test.js` holds the ceiling),
so a new piece goes on the existing footprint rather than a wider one.

## Data and interfaces

No schema, API, palette or save change. Room cells that move (Tokyo only):

| | Before | After |
|---|---|---|
| 3F-6F floor, room cells | x 3-16, y 4-11 | x 5-14, y 4-10 |
| Stair up (1F-5F) → lands on | 16,12 → 15,11 | 14,11 → 13,10 |
| Stair down (2F-6F) → lands on | 15,10 → 16,11 | 13,9 → 14,10 |
| Stairwell | 15,9 | 13,8 |
| 1F street mat → `Park` | 15,12 → 13,17 | 13,11 → 13,17 |
| `Park` door 13,16 → 1F | 15,11 | 13,10 |

The held-key rule holds as before: `u` is walked into heading south and lands on the hall's bottom row
under `d`, with void below it; `d` is walked into heading north (or west from its east neighbour) and lands
on the hall's bottom row above `u`, whose north and west neighbours are plain floor. Saved `gamev2_painted_tiles` for these rooms keep
cells that no longer exist; progress is counted against reachable cells, so they are ignored.

## Tests

From `gamev2/` (`export PYTHONDONTWRITEBYTECODE=1`):

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py
python3 tools/sync_cities.py --check
```

Browser regression (`tools/browser/README.md`): `regress.js` must stay 24/24 with no assertion edits; its
Devhouse checks read doors and stairs from the config.

As a player, desktop and a 667x375 touch phone, with screenshots: walk in from `Park` 13,16, hold UP/DOWN
through every flight to 6F and back out to 13,17; on each floor walk the loop round the furniture, bump the
locked doors, the bath (5F), the bunk (4F) and the washer (6F), and enter each wet room.

## Risks and open questions

- **Scope is Tokyo 3F-6F only.** The ticket says "the room"; Osaka's floors are already as full as a
  konbini and are made of small rooms, so they are not touched. If the owner also meant Osaka, the same
  recipe applies (new 9x10 → smaller grids in `FLOORS`), as a follow-up.
- **4F stays the emptiest** (47 standable cells): its plan is three beds, a bunk, a sofa and a tansu, and
  the hall fixes the depth at seven rows. Making it fuller means adding furniture the #69 plan does not
  have, which is the owner's call.
- **3F is tight by design**: one-cell walkways round the table, as in the Osaka kitchen. Reachability is
  asserted by the generator and lint.
- **Map data is serial.** The change rewrites `config.json` rooms and one `Park` transporter. If `master`
  moved under it, rebase, re-run the three commands above and the checks rather than merging the JSON.
