# Blog post coverage: everyone stands in a named area, and a check keeps it so (#383)

## Context

The ticket asks whether every person and every blog post in the game stands somewhere that has a region.
The regions are config `districts` (`gamev2/tools/districts.py`, #219): rectangles of a room, each with a
name. Nothing checks that people stand inside one, and "a room need not be covered edge to edge".

**The audit** (run for this design, state-aware: every day from each trip's opening, lead-in included, to its
end, every NPC the game shows that day, resolved the way the game resolves it; the izakaya's
`drinkingGameOpponent` fixtures left out). 83 stands (one person at one cell from one dated state, or the
base, until the next), 325 person-days:

| | devhouse2 | devhouse3 |
|---|---|---|
| in a district | 107 | 65 |
| on a station platform (stations have no districts on purpose) | 36 | 0 |
| outdoors, in no district | 105 | 12 |

Outdoors, in no district (nine stands):

| Who | Room, cell | Days | Why |
|---|---|---|---|
| Bailey, Damian, Dylan, Julia (devhouse2 base) | Tokyo (20,42), (24,42), (16,42), (28,42) | 2025-09-18 until each one's first post (14, 15, 32, 39 days) | they wait on the road south of the palace, rows 41–44; `imperial-palace` stops at row 39 |
| Damian, Dylan (devhouse3 stay base) | Asahikawa (34,13), (24,14) | 2027-02-25..28 | the strip of snow between the plaza and the river, rows 13–15 east of the ramen alley, is in no district |
| Xander (devhouse3 stay base) | Asahikawa (33,28) | 2027-02-25..28 | the lane south of the river, rows 28–29; `riverbank` stops at row 27 |
| Bailey, post 707 | Kanazawa (45,44), at `the shrine` | 2025-11-09..11 | the shrine wood built for this post (south-east, x ≥ 35, y ≥ 34) has no district |
| Dylan, post 636 | Osaka (14,6), at `the vending machines` | 2025-11-05..06 | Osaka's platform strip (rows 6–8) has no district; the post is about Lake Biwa and #382 moves it there |

On a platform (twelve stands, all within two cells of `<Station> · the platform`): TokyoStation, 20–31 Oct
2025 (posts 419, 480, 519, 528, and the states of 20 and 26 Oct that carry no post id); KanazawaStation,
Bailey 5 Nov (642); FukuokaStation, Dylan from 8 Nov (694). These are posts about the journey; the ones
about somewhere else were moved off the platforms by #121 and are pinned off them (`OFF_THE_PLATFORM`).

Everyone else, every Sapporo base included, is inside a district.

Not something a machine can check, and not changed here: posts that stand in a district but at a stand-in for
the place they are about. All are already recorded: Dylan's Lake Biwa posts in Osaka (568, 590, 615, 636,
681: #380–#382); 578 (Shibuya) and 625 (the swan boats) in the Imperial Palace until Park is rebuilt as
Shibuya and Ueno (#219, stage H, no ticket yet); 694 (the ride from Otsu) on Hakata's platform, by #68's
decision.

Outcome: a report anyone can run, a test that fails when somebody stands outside every named area, and the
nine stands above fixed or listed with the ticket that ends them.

Overlays of the four rooms (yellow: districts today; cyan: proposed; red: the stands; green: where the two
Asahikawa people move) are with the ticket's media as `383-coverage-<room>.png`; they may not be on the
implementer's disk.

## Approach

**The rule.** On every day of every trip, lead-in included, each NPC the game shows (fixtures aside) is
*covered* if its cell is inside a district of its room, or its room is a station (a key of
`config.stations`: one room, one spot, "the platform"). Any other room (an interior, a `blog: false` room)
or an outdoor cell in no district is *uncovered*. The check is on the home cell; NPCs wander
`npcWanderRadius` (2) cells from it.

**One function, two users.** `districts.coverage(cfg)` works it out with the pipeline's own mirror of the
game's resolver (`blog_to_npc.trip_window`, `resolve_pos`, `district_at`, as `test_shipped_whereabouts`
does). `python3 tools/districts.py --coverage` prints it; `test_shipped_coverage` in
`tools/test_blog_to_npc.py`, beside `test_districts` and `test_shipped_whereabouts`, asserts on it. (The
sizing comment says "a test in tools/tests"; the district and whereabouts tests and every helper are Python,
so it goes there rather than a second implementation in JavaScript.)

**The fixes.** Where a person stands where their line or post says, the label grows to them; where a person
was only left outside a label's edge, the person moves; where a post is waiting for a room that is ticketed,
it is listed.

1. Tokyo: `imperial-palace` grows south to the room's last inner row, (6,5,54,39) → (6,5,54,44). The room
   is the district ("Imperial Palace"), Bailey's line is "We're camped down here by the road for now", and
   `dates-trips.test.js` pins the four cells. `stand` and the cells an area post gets do not change.
2. Asahikawa: `riverbank` grows south over the lane, (2,16,39,27) → (2,16,39,29), for Xander. Damian and
   Dylan move onto the plaza's south row, inside `station-front`: Damian (34,13) → (34,12), Dylan
   (24,14) → (24,12) (both walkable paving; (23,12) is blocked). No rectangle can take in the snow strip:
   `station-front` or `riverbank` grown over it would overlap `ramen-alley`.
3. Kanazawa: a seventh district over the shrine wood, since the map has a place built for post 707 and no
   name for it: key `teramachi`, name `Teramachi`, bounds (35,34,57,50), stand (46,45). The #219 plan
   reserves `teramachi` for the temple hill that post 707 moves to when that stage is built; the key moves
   with the post then.
4. Osaka, post 636: listed, not fixed. #219 decided Osaka's station front is "a threshold, not a district",
   #274 keeps the post's cell through Osaka's redesign, and #382 re-homes it to Lake Biwa. The list
   (`UNCOVERED`) is checked both ways, so #382 is told to delete the line. **If #382 has landed when this is
   built, the list is empty.**

Tried on a scratch copy of `gamev2/` with exactly these data edits and `asahikawa.test.js`'s pin moved:
`test_blog_to_npc.py`, `play.js check`, `sync_cities.py --check` and `rehearse_blog.py` (313/313) pass;
`check_generators.py` reproduces `districts`, every room and the world map; `test_game.js` fails nothing
about districts, Asahikawa, Kanazawa or the trips. (What did fail there, in both, needs files outside
`gamev2/` that the copy did not have.) A prototype of `coverage` then finds only post 636.

## Changes

All paths under `gamev2/`.

- `tools/blog_to_npc.py`: lift the nested `opens(t)` of `trip_window` to a module function
  `trip_opens(trip)` (ISO date the trip opens: `start` minus `lead`, `TRIP_LEAD` when `lead` is not a
  non-negative int); `trip_window` calls it. No behaviour change.
- `tools/districts.py`:
  - `DISTRICTS`: the three bounds above, and after Kanazawa's `nagamachi`:
    `d('teramachi', 'Teramachi', 'the wood of shrines south of the avenue: a blue-roofed shrine in a clearing among cedars, its stone foxes', (35, 34, 57, 50), stand=(46, 45))`.
  - `UNCOVERED = {('Dylan', '2025-11-05'): "post 636 is about Lake Biwa; it waits by Osaka's platform until #382 re-homes it"}`,
    beside `UNLABELLED`: `(NPC name, first day of the stand) -> why`, with a comment that the test fails on
    a stand that is not listed and on a line that matches no uncovered stand.
  - `coverage(cfg)`: for each trip in start order, each day from `b.trip_opens(trip)` to `trip['end']`,
    each room, each NPC without `drinkingGameOpponent`, `b.resolve_pos(npc, day, b.trip_window(cfg, day))`;
    for those present, `zone` = the name of `b.district_at(cfg, room, x, y)`, else `'the platform'` if the
    room is in `cfg['stations']`, else `None`. Consecutive days of one trip with the same (name, room,
    cell) are one row; a day on which that NPC has a dated state in that room starts a new row. Returns, in
    order of first day, rows
    `{'trip', 'name', 'room', 'cell': (x, y), 'first', 'last', 'days', 'zone', 'posts'}`; `posts` is the
    post ids of the state dated `first` in that room (`[]` for a base stand, or a state with no `posts`).
  - `coverage_problems(cfg)`: the lines both users print: one per uncovered row not in `UNCOVERED`
    (`"<name> stands in no district at <room> (x,y) from <first> to <last> (post <ids>): grow or add a district in tools/districts.py, move them with blog_to_npc.py --rehome, or list the stand in UNCOVERED"`)
    and one per `UNCOVERED` key that matches no uncovered row (`"... is listed in UNCOVERED and is covered now: delete the line"`).
  - `--coverage`: prints, per trip, one line per row (`first..last  Nd  name  room (x,y)  zone | IN NO DISTRICT (reason)  post ids`),
    then person-days per trip (in a district / on a platform / in none), then the problems; exit 1 if there
    are any. Writes nothing. `main` accepts it beside `--report`; the docstring's usage block gets its line
    and a sentence on the rule.
- `config.json`: `districts` rewritten by `python3 tools/districts.py` (never by hand); in
  `rooms.Asahikawa.npcs`, base `gridX`/`gridY` of Damian → 34, 12 and Dylan → 24, 12 (through
  `b.load_config()` / `b.save_config()` so the file's formatting is kept). No layer, palette, `.tmj` or
  world-map change.
- `tools/test_blog_to_npc.py`: `test_shipped_coverage(cfg)`, called in `__main__` after
  `test_shipped_whereabouts` (see Tests).
- `tools/tests/asahikawa.test.js:193`: the pinned `riverbank` bounds become `[2, 16, 39, 29]`.
- `docs/landmarks-and-towns.md`, "Districts": `--coverage` in the "One authored list" bullet; after "a room
  need not be covered edge to edge", the rule (everyone the game shows stands inside a district or on a
  station's platform; `UNCOVERED` lists the exceptions); the table's Kanazawa row gains Teramachi. The table
  is stale in two rows it should match while it is open: Sapporo lacks Susukino, and Karuizawa (Larch road)
  has no row. Hokuriku's Kanazawa paragraph: the shrine wood is the Teramachi district.
- `docs/blog-pipeline.md`, "Districts": two sentences: the rule, and what to do when the test fails after
  a post lands (the three fixes in the message above).

Rooms touched: district data of Tokyo, Asahikawa and Kanazawa; two base NPC cells in Asahikawa. No map.

## Data and interfaces

- `config.districts`: `Tokyo[0].bounds` `[6,5,54,44]`; `Asahikawa[2].bounds` `[2,16,39,29]`; a seventh
  Kanazawa entry `teramachi` with `spots: ["the fox statues", "the shrine"]`. 49 districts in 17 rooms.
  The placement model is offered one more line, `Kanazawa · Teramachi (area): ...`.
- `python3 tools/districts.py --coverage` (new option, exit 0 or 1). `districts.coverage`,
  `districts.coverage_problems`, `districts.UNCOVERED`, `blog_to_npc.trip_opens` (new).
- No game code, no schema change: the game still does not read `districts`.

## Tests

`test_shipped_coverage(cfg)`:

- On a made-up config (one outdoor room with one district, one station, one `interior: true` room, two
  trips with lead-ins, a `trip`-marked base NPC for each): a stand inside the bounds reports the district's
  name; one cell outside reports `None`; in the station `'the platform'`; in the interior `None`; a
  `drinkingGameOpponent` is not a row; the first trip's base has a row from the day that trip opens, the
  second trip's base none before its start (`early`), and neither a row in the other's trip; five days at
  the base then a dated state give two rows, `days` 5 and the rest, the second carrying the state's post
  id, and a second state at the same cell a third; `coverage_problems` names an unlisted stand, and a
  listed one that is covered.
- On the shipped config: `coverage_problems(cfg) == []` (the assertion message is the lines); every member
  of every trip has at least one row in it, so the check cannot pass by seeing nobody; no row's room is an
  `interior: true` room.

Run from `gamev2/`, all passing before the commit: `python3 tools/districts.py` then
`python3 tools/districts.py --coverage` (exit 0, only post 636 marked), `python3 tools/test_blog_to_npc.py`,
`node tools/test_game.js` (about six minutes here), `node tools/play.js check`,
`python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`, and
`python3 tools/rehearse_blog.py` (`blog_to_npc.py` and Asahikawa's cast are touched).

Two NPCs move one and two cells on 25–28 Feb 2027, which a player can see: with
`node tools/play.js date 2027-02-26` and `warp Asahikawa`, `npcs` and `map` show both on the plaza's south
row, each with a free cell to be talked to from; run `tools/browser/regress.js` where a browser is available
(none in the design environment; the ticket would need `workshop/needs:browser`). Put the final `--coverage`
output in the summary: it is the audit's report.

## Risks and open questions

- **One new label.** The sizing comment asks for fixes "within existing rooms and districts". No room or map
  changes, but Kanazawa gains a district and two grow. The alternative for post 707 is to move it off the
  shrine built for it (`kanazawa.test.js` pins it there) or to list it in `UNCOVERED`; if the owner prefers
  the list, drop the `teramachi` line and add `('Bailey', '2025-11-09')`.
- **Stations count as covered.** By design they have no districts and one spot. If the owner wants platform
  posts in town districts instead, that is twelve stands to re-home and the start-room pins in `madeup-towns.test.js`
  (`2025-10-20` opens on Tokyo Station's platform); not done here.
- **Order with #382.** Either order works: this first, #382's re-home makes the `UNCOVERED` line stale and
  the test says to delete it; #382 first, the list ships empty.
- **A future post can fail the check.** The pipeline places at named spots, and six are in no district
  (Sapporo's Don Takote; Osaka's vending machines; Fukuoka's 7-Eleven, vending machines, pond and sakura
  trees), and a crowded spot beside a district's edge can spill a cell outside. `test_blog_to_npc.py` then
  fails on master after the pipeline's commit (Checks does not gate the deploy) and the message names the
  three fixes. Covering those six landmarks is a follow-up, reported with this design.
- **The mirror.** The verdict is the Python resolver's, which mirrors the game's (`resolveNpc`,
  `Trips.windowFor`) as the other shipped-history tests already assume.
- **`node tools/test_game.js` is flaky here** on unchanged master (`check_generators: a PNG packed
  differently ...`, two runs of three): unrelated, reported with this design. Re-run before blaming a change.
