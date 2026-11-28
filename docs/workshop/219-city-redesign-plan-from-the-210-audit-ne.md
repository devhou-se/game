# Design: the rest of the city redesign — Susukino, Asahikawa, Hokuriku, Sendai, Osaka, Fukuoka, Asakusa, Park (#219)

## Context

#219 is the owner's decision to redesign every city from the #210 audit, one city at a time, each as its own
commit that carries its own interiors. Landed so far: the district labels (`c8276a2d`) and Sapporo stages 1–3.
Left, in the owner's order:

| Stage | City | State today |
|---|---|---|
| A | Sapporo stage 4: Susukino and the streetcar | unfinished on `origin/wip/219-sapporo-stage4` (`593f0e80`, based on old master `e3cb4d0d`) |
| B | Asahikawa | art drawn (`generate_asahikawa_art.py`), not registered, map untouched |
| C | Kanazawa re-skin, Shirakawa-go and Toyama touch-ups | Kanazawa art drawn (`generate_kanazawa_art.py`); nothing drawn for the touch-ups |
| D | Sendai | art drawn (`generate_sendai_town_art.py`) |
| E | Osaka | art drawn (`generate_osaka_art.py`) |
| F | Fukuoka | art drawn (`generate_fukuoka_town_art.py`) |
| G | Tokyo: Asakusa and the station art (#70) | nothing drawn |
| H | Tokyo: Park into Ueno and Shibuya (#94) | nothing drawn |

A and B are due before the devhouse 3 lead-in (30 days before 18 Feb 2027).

What the plan's text did not know, and this design allows for:

- The owner's later rulings: Sendai keeps its samurai quarter with art of its own; Canal City gets its atrium
  (#217) instead of staying sealed; a shrine hall keeps its interior wherever a shrine remains (#212);
  Asakusa's six 7-Elevens stay; posts 587 and 610 are a separate pipeline item.
- Work that landed after the plan: the Devhouse stands on Park's west square (#69), Park's east court holds
  `ShrinePark1` and `PagodaPark3` with post 535 beside it (#212, #214), Market and Palace have lobbies (#216),
  and Osaka now holds nine dated states, not four (the Lake Biwa posts were re-homed there).
- Master has moved since this design was first written (it was written on `2a70cc8d`; the cells and line
  numbers below were re-checked against `origin/master` = `2cbd3e7a`). #217 has landed: `PubSendai1` behind
  `sendai-pub`, `DistillerySendai1` behind `sendai-kiln` and the mall atrium behind `canal-city`, with
  `generate_pub.py`, `generate_distillery.py`, `generate_mall.py`, their rows in `roomgen.OWNED_DOORS` (so
  `save_config` keeps those doors through a town rebuild) and `taproom` / `tasting` in `Shop.VENUES`. Stages D
  and F leave those three sprites, their cells and their door offsets alone. The smaller Devhouse floors (#228)
  and the repository tidy (#229: `Assets/` is now `art-source/`, a Checks workflow runs the no-browser gates
  without Pillow) have landed too.

Intended outcome: every city passes the plan's tests (`check_distinct.py`: buildings ≤ 0.25, sprites ≤ 0.40,
own ≥ 1/3; a crop of any district says which city it is; every district has a named spot), no dated post is
lost, and every building the plan does not call a landmark has a door cell that either opens or can be opened
later.

## Approach

One design, eight stages, **one commit per stage** (`gamev2: … (#219)`), in the order above. Each stage is
built on the result of the one before and leaves every check green. The implementer works down the list and
may stop at a stage boundary; the summary says which stages landed, and a later run continues from here.
Nothing in a later stage is started before the earlier one is committed (map data is serial).

**Before stage A: bring master into the branch.** This branch holds only this file and is four commits behind
`origin/master`. `git merge origin/master` (clean; do not rebase a pushed branch), then start. If master has
moved past `2cbd3e7a`, re-read the stage's *Fixed* list against it before building.

**How to read the cells below.** A cell marked *fixed* must hold: station door cells, doors of interiors that
are kept, seams, kept landmarks, kept stand cells. Every other cell is a target: a piece may move a cell or
two where `play.js lint`, a walk-behind overlap or the crop test asks, and where only a band is named (`rows
25–29`) the implementer picks the cells. Footprints, door offsets and solid cells come from each art tool's
`--manifest`, not from this document.

**Recipe for every stage** (stages name only what differs):

0. Once, before anything: set up the imaging stack the city sprites were written with (Pillow 11.3.0 on
   zlib-ng 2.2.4; recipe: `.workshop/Dockerfile` on `origin/workshop/222-…`: zlib-ng 2.2.4 `--zlib-compat`,
   `pip install Pillow==11.3.0`, `LD_PRELOAD` of its `libz.so.1`), then record the baseline on the untouched
   checkout: `python3 tools/check_generators.py > /tmp/cg-baseline.txt`. On `2cbd3e7a` with that stack it
   **exits 1**: 54 `ok`, 2 `skip` (no Japanese font) and `DRIFT` for five art tools this ticket never touches
   (`generate_konbini_art.py`, `generate_pub_art.py`, `generate_distillery_art.py`, `generate_mall_art.py`,
   `generate_devhouse_art.py`; their PNGs were committed from another zlib, #230 and #235 track it). Do not
   regenerate those here. The six city art tools (`generate_sapporo_art.py`, `generate_asahikawa_art.py`,
   `generate_kanazawa_art.py`, `generate_sendai_town_art.py`, `generate_osaka_art.py`,
   `generate_fukuoka_town_art.py`) reproduce their committed bytes on that stack and drift on stock zlib; if
   one of them is not `ok` in the baseline, the stack is wrong: fix it before going on. An art tool rewrites
   every PNG each time it runs (there is no `--help` and no dry run, and `--manifest`, `--sheet`, `--scenes`
   each need a path), so never run one outside the pinned stack and never commit a PNG whose pixels did not
   change.
1. **Register the stage's art** (see Shared code): `register()` in the art tool, the tool in
   `check_generators.ART_TOOLS`, prefabs in `make_prefabs.py` for anything stamped with colliders or doors,
   door-table rows in `roomgen.py`, the new building prefixes in `check_distinct.LANDMARK_ART`. Write the
   manifest (`--manifest <path>`) after any art fix and place from that, not from an older copy.
2. **Edit the town generator** (or, for Tokyo, the stage's re-runnable script). Keep `prev.get('npcs')`, keep
   konbini doors with `rg.kept_door`, write one hidden station transporter per station door cell.
3. **Interiors**: re-run `generate_houses.py <Town>`, `--lobbies <Town>`, `--shops <Town>`, `generate_konbinis.py`,
   `generate_shrines.py`, `generate_pagodas.py`, `generate_discount_stores.py`, `generate_stations.py` as the
   stage needs, then the town generator again (so its second run is a no-op). `generate_houses.py` prunes
   and renumbers houses, lobbies and shops in `config.json` in door (y, x) order, but it does not delete the
   `tiled/*.tmj` of a pruned room, and `generate_shrines.py` / `generate_konbinis.py` prune nothing: delete by
   hand the `tiled/*.tmj` of every room that went, the rooms of shrines and konbinis whose building is gone,
   and any stray `gk_blank` collider `shut_door` left on a cell with no building. `save_config` first
   restores the old house transporters on a cell that is still a door, so the stage is not finished until
   `generate_houses.py <Town>` has run after the last town build. A door whose front cell cannot be stood on
   (a lamp, a prop, an NPC, a blog spot) is shut by the generator: keep door-front cells empty.
4. **World**: `generate_stations.TOWN_DOORS` if a door moved; `devhouse.world` and `hokuriku.SIZE` if a room
   changed size (keep x, y; `sync_cities.py --check`).
5. **Labels and people**: `tools/districts.py` (bounds, stand, description; districts of one room never
   overlap and each stand is inside its bounds, `test_blog_to_npc.py` checks both), `blog_to_npc.LANDMARKS`
   rows (`rooms`-scoped). Every new row carries a stand offset onto a walkable cell that is outside every
   sprite's box and is not the cell in front of a door: a row without one stands the visitor on the sprite's
   top-left cell, which `test_blog_to_npc.py` refuses. Rows whose sprite is no longer placed are deleted.
   Base NPCs: Sapporo's are in `generate_cast.HOME`; every other town's live only in `config.json` and are
   kept by `prev.get('npcs')`, so move one only where its cell became solid or a door front, and rewrite a
   base line that names a thing the stage removes. A dated state stores its own cell and follows nothing:
   `blog_to_npc.py --rehome <NPC> <DATE> "<Room> · <label>"` for each dated post whose spot moved or vanished
   (`--dry-run` first; it keeps dialogue, photo and voice). No dated state is deleted. Then
   `rehearse_blog.py` and `test_blog_to_npc.py` cases that place a post at a label the stage removed are
   re-aimed at the label that replaces it.
   Trip start cells are not stored either: `Trips.standNear` picks the cell two from the day's crowd with the
   shortest walk from an arrival cell (a station exit or a door's way out). A new door near a crowd moves
   it. For each trip day in the town run `play.js date <day>` and `start` before and after the build; where
   the cell moved, look at it in a render and update the pin (`dates-trips.test.js`).
6. `config_to_tiled.py` for the room and every interior touched, `make_worldmap.py`.
7. `node tools/play.js lint <Room>` (0 errors), `play.js render <Room> out.png`, and the crop test: three
   960x640 crops per district must show something of that city's own.
8. **Tests**: update every test that pins a changed cell, count or sprite to the new value (never loosen to
   "any"); add the stage's own assertions to `tools/tests/<town>.test.js` (new file where none exists).
9. **Docs**: the town's section in `gamev2/docs/landmarks-and-towns.md`, interior tables there, and the lines
   the stage makes untrue in `blog-pipeline.md`, `generators-and-checks.md`, `trains-and-stations.md`,
   `ambient-traffic.md`, `buildings-and-street-props.md`, `hud-input-touch.md`; generator docstrings.
10. `python3 tools/check_distinct.py`; when the town meets the targets (or is no worse on any number where
    it cannot yet), `--update` the baseline.
11. All gates (Tests section), then play it in a browser by day and `?tod=night` at 1280x960, 844x390 and
    667x375, with `?date=` set to a day someone stands there; screenshots to `/work/media/`.

**Rules that hold in every stage**

- **Station fronts.** Each town's own front is placed so that today's station door cell is one of its door
  cells. `TOWN_DOORS` and arrival cells therefore do not move (trip start cells are computed; step 5). Every
  door cell of the front gets a hidden transporter to the station's entry (Sapporo's `for x, y in
  station_doors` pattern).
- **Doors.** A new building with a door gets a row in the table that matches what it is. The shapes differ:
  `HOUSE_DOORS['<sprite>_0_0'] = (dx, dy)` (one bare tuple); `TOWER_DOORS`, `SHRINE_DOORS` and `SHOP_DOORS`
  take a list, `['<sprite>_0_0'] = [(dx, dy), …]`. Houses, lobbies and shrine halls are what the owner asked
  each city to carry; they are always opened.
- **Shops.** A shopfront is opened with a `SHOP_DOORS` row and a `generate_houses.SHOP_TYPES` row
  `'<sprite family>': (label, venue, shelf sprite)`. Every shop floor is the one `SHOP` layout, so:
  the label is 11 characters or fewer (`hud-phone-layout.test.js` checks every room name against the phone
  bar); the venue is a `Shop.VENUES` id whose **title** fits the front (`souvenirs` OMIYAGE, `bakery`,
  `kissa` KISSATEN, `standbar` STAND BAR, `taproom` THE PUB, `tasting` TASTING BAR, `drugstore`, `crab`, and
  from stage A `bar` KARAOKE BAR and `ramen` RAMEN ALLEY); where no title fits, the stage adds one venue row
  with a fitting title that sells existing catalogue items only (no new items); `izakaya` is not reused (it
  buys and grills fish). **At most one front
  of a venue is opened per street**: the others of that venue, and every front that sells nothing the
  catalogue has (bookshop, arcade, shogi parlour, department store, museum, billboard, sign tower), keep a
  solid door cell with no table row ("can be opened later"). A shop is not a store: no stamp, and it does
  not count for Konbini Pilgrim. A stage that runs short may seal any shop this way and say so; it may not
  seal a house, a lobby or a hall. `bar` and `ramen` exist only once stage A has landed.
- Landmarks stay sealed. No interior is kept alive for a building that is removed.
- **Shared on purpose** (not counted against a city): 7-Eleven, vending machines, Don Takote, lamp posts,
  basic trees. A label is never hung on a shared sprite when the city has its own piece for the place.
- **Glow.** Each lit piece gets a `spriteMetadata.glow` list of `{x, y, r, ry?, color, a}` in cells from the
  sprite's top-left, with `r` and `ry` clamped to 2.5. A sprite whose key matches `lamp-post` or `-lanterns`
  gets none (the lamp rule already lights it). `glows-trams.test.js` enforces both.
- **Stores and counts.** A new 7-Eleven or Don Takote is one more stamp and one more store in Konbini
  Pilgrim's total (`Stamps.stores` is every store room in config, by design; the achievement is computed
  from the save each time, so a player who had every stamp reads N of N+1 until they visit the new one).
  Stage B adds one (16 → 17) and stage H one more. Say so in the commit message and the hand-back.

**Choices made where the plan left one open or facts have changed** (the owner may overrule any of them; none
blocks the work):

| # | Choice | Why |
|---|---|---|
| 1 | Asahikawa's stock shrine, torii and foxes go; the zoo gate takes their place; `ShrineAsahikawa1` is deleted | the plan; "stock shrine: Tokyo only"; no post stands there |
| 2 | Asahikawa gets a 7-Eleven on Heiwa-dori with its interior | the plan lists "the konbini"; it is shared kit |
| 3 | Kanazawa is 60x44, not "about 60x40" | Nagamachi needs rows 33–43 for canal, bridge, gate, lane and house |
| 4 | Kanazawa's `teramachi-hall` on the hill hosts `ShrineKanazawa1` | a temple hall remains, so its interior stays (#212); post 707 keeps a home |
| 5 | Shirakawa-go and Toyama keep their sizes; the far bank is filled, not trimmed | the stitched seams and Toyama's river and path columns derive from those sizes |
| 6 | Sendai stays 70x48 | the shrink was the samurai quarter, which the owner kept |
| 7 | Osaka stays 50x46, not "about 50x40", and keeps one tower (the blue one), not two | with nine states 50x40 is under the plan's own 250 cells per state; the avenue's rows become the south-bank row; Tsutenkaku and its post keep their cells; a second tower has no site between the wheel (to col 44) and the border hedge (col 48) |
| 8 | Fukuoka is 58x62, not "about 56x58": only cols 58–61 are cut | Dazaifu's court and pond reach col 55 and Old Hakata needs cols 54–55, so the hedge cannot stand west of col 56; rows 57–61 are the Dazaifu approach, its lamps, the fence and the border, and cutting one would put the fence on the lamp row |
| 9 | Fukuoka's small pagoda and `PagodaFukuoka1` go; `fukuoka-kushida-hall` hosts `ShrineFukuoka1` | the plan removes the pagoda (#214's design already expects it); Kushida remains a shrine |
| 10 | Asakusa loses its three townhouses and the high-rise **and** `HouseMarket1..3`, `LobbyMarket1` | the plan; an interior without a building cannot stay |
| 11 | Park: **Shibuya on the west half, Ueno on the east** (the plan said the reverse); room key and name stay `Park` | the Devhouse (west) and the shrine court, pagoda and post 535 (east) were built after the plan; Ueno really has the pagoda, shrine and pond, Shibuya the towers; nothing built moves |
| 12 | Post 520 is re-homed to the distillery but its dialogue is not regenerated | that needs the post text and an API key; the owner re-runs the blog workflow for 520 |
| 13 | Sendai gets no ramen front; `sendai-gyutan` stands where the plan says "a ramen shop" | no ramen front was drawn for Sendai and gyutan is the city's own dish; a ramen front can be drawn later |
| 14 | Of the shopfronts, one per venue per street is opened; the others keep sealed door cells | every shop floor is the same layout, so two of a kind on one street are the same room twice; the plan allows "can be opened later" |
| 15 | Fukuoka's three Nakasu bars stand on the south bank and the Ohori corner becomes their pavement and sand (district `south-bank`) | there is no free ground north of the river; the plan lets the Ohori pond go |

## Changes

All paths are under `gamev2/` unless they start with `devhouse.world`.

### Shared code (added in the first stage that needs it)

- **`tools/art_register.py`** (new, stage B): `register(built, glow=None, flat=(), path='config.json')`, the
  one body the five drawn-ahead art tools call from `main()`. For each key of `built` it writes what
  `generate_sapporo_art.register` writes (`spriteMetadata {frameCount: 1, anchorX: 32/w, anchorY: 32/h}`,
  `tileNames`; anchors rounded to four places, as every existing entry is, so a redrawn sprite of the same
  size leaves its entry byte-identical), plus `glow[key]` (a list of spots already in cells; it clamps
  `r`/`ry` to 2.5 and drops any key matching `lamp-post|-lanterns`) and `depthBias: -200` for each key in `flat`. It rewrites
  `config.json` only on a change. It does **not** read the tools' piece tables: the five tools store their
  lights in five shapes (Asahikawa: `glow=[(cell, [px, py], '#hex', what)]` in pixels with no radius, manifest
  key `night_glow`; Kanazawa `[x, y, '#hex']`; Sendai and Fukuoka `[x, y, colour, r?, a?]`; Osaka
  `L(x, y, int, r, a, ry=)`), so each tool gets a small `glow_spots()` of its own that returns `{key:
  [{x, y, r, color, a}]}` (Asahikawa: x = px/64, y = py/64, r about 0.6–0.9, a about 0.5) and a `FLAT` set
  taken from its pieces' layer. It registers only the keys the stage passes in, so art for a later city stays
  unregistered until its stage. An overlay drawn on ice or water (`ice-crack-*`, `ice-fishing-hole`) goes on
  `Non-Collidables`, above the `Water` layer; check it in the render.
- **`tools/roomgen.py`** door tables, one row per new building with a door, in the shapes given under
  Doors: `HOUSE_DOORS` (houses), `TOWER_DOORS` (lobbies), `SHOP_DOORS` + `generate_houses.SHOP_TYPES` (shops),
  `SHRINE_DOORS` + `generate_shrines` `LOOKS`/`NAMES` (halls; a look is `'blue'` or `'red'`, `None` asserts a
  stock shrine roof). Offsets are the manifest's `doors`.
- **`tools/tests/station-interior.test.js`** l.112–115 (stage B): a town may have one to three side-by-side
  station door cells, all leading to the station's entry (today only Sapporo may have two). Where a town
  test takes "the first transporter into the station" and expects the mats to return below it
  (`sendai.test.js`), compare against `TOWN_DOORS`' exit cell instead.
- **`tools/check_distinct.py`** `LANDMARK_ART`: the patterns are anchored and decide what counts as a
  building, so add building prefixes only, never a whole family name that also holds ground or props:
  `heiwa-shop-`, `ramen-(shoyu|narrow|miso)-front`, `asahibashi-`, `hokkaido-house-`, `zoo-(gate|ticket-booth)`
  (not `heiwa-`, `ramen-`, `zoo-`, `penguin-`: those would count `heiwa-paving-autotile`, Sapporo's
  `ramen-alley-lanterns` and the props); the same care for `kenrokuen-`, `chaya-`, `katamachi-`,
  `nagamachi-`, `teramachi-`, `osaka-` and the later cities. Print the table before and after: a city whose
  numbers moved for another city's prefix is a wrong pattern.
- **`src/utils/Trips.js:573`, `tools/blog_to_npc.py:642, 689`** (stage C): the "not plain ground" match is
  `/stairs/`; widen it to `stair` so `teramachi-stair` is never a start cell or an area post's cell.
- **`tools/check_generators.py`**: each art tool in `ART_TOOLS`, each new generator in `GENERATORS`.

### Stage A — Sapporo stage 4 (Susukino, the streetcar)

Port `593f0e80` onto current master; do not redo it.

The port below was run end to end on `2cbd3e7a` in a scratch checkout for this review; the numbers in steps 4
and 5 are from that run.

1. `git cherry-pick -n 593f0e80`, keeping its code, tool, test and art changes and **discarding** its
   generated outputs (they are built on old master): `git checkout HEAD -- devhouse.world
   gamev2/config.json gamev2/tiled/sapporo.tmj gamev2/assets/map/world-map.json
   gamev2/assets/map/world-map.png gamev2/tools/distinct_baseline.json`, and unstage and delete the `tiled/`
   files it adds (`lobbysapporo3.tmj`, `shopsapporo4.tmj`, the eight new `tiled/prefabs/*.tmj`); the
   generators write them again. The eleven new PNGs (`susukino-asphalt-autotile_*`,
   `susukino-ramen-stall-a/-b`) are kept.
2. Four files then still conflict. They are **not** all "keep both sides":
   - `src/Shop.js` `Shop.VENUES`: keep master's three rows (`bakery`, `kissa`, `standbar`) and add the
     branch's two after them, before `pub:`: `bar: { title: 'KARAOKE BAR', sells: i => ['highball',
     'nama-beer', 'edamame'].includes(i.id) }` and `ramen: { title: 'RAMEN ALLEY', sells: i => ['karaage',
     'edamame', 'nama-beer'].includes(i.id) }`. #217's `taproom` and `tasting` below are untouched.
   - `src/utils/Interactions.js`: take **master's side whole** (the chika-shop rows, #217's `taproom` and
     `tasting`, and the wider `drinks` / `snacks` konbini patterns) and add one row before `drinks`:
     `{ kind: 'ramen', group: 'shop', pattern: /^susukino-ramen-stall/, footprint: true }`. The branch's side
     carries the old, narrower `drinks` and `snacks` patterns: keeping them breaks the konbini shelves.
   - `tools/tests/hud-phone-layout.test.js`: take master's side whole (the shrine, Marunouchi, San
     Franbourne and pagoda assertions) and add `'Lobby · Sapporo 3'` to its `kinds(bare[715], 'Lobby')` list,
     after `'Lobby · Sapporo 2'`.
   - `tools/generate_sapporo.py`, two hunks: in the docstring the branch's two lines and master's
     `generate_chikagai.py Sapporo` line; in the body master's block that stamps
     `chikagai.TOWNS['Sapporo']['exits']`, then the branch's Susukino block and its border loop (master's
     own border header and `for y in range(7, 41, 2):` line go). `import chikagai` and the stage 3 props
     merge without conflict.
3. Regenerate in the order of `wip-handoff/sapporo4_apply.sh` (it is in the branch's second commit,
   `f3294b8e`: `git show f3294b8e:wip-handoff/sapporo4_apply.sh`; its `PIL_PY` default is a macOS path, so run
   its steps by hand on the pinned stack): `generate_sapporo_art.py` and `make_prefabs.py` →
   `generate_sapporo.py` → `generate_houses.py --shops Sapporo` → `--lobbies Sapporo` → `generate_sapporo.py`
   → `devhouse.world` slot (grows north, south edge kept: y -3264 → -3776, height 2752 → 3264, no overlap) →
   `districts.py` → `config_to_tiled.py Sapporo ShopSapporo1..4 LobbySapporo1..3` → `make_worldmap.py` → lint
   → `check_distinct.py --update`. `generate_chikagai.py` is not re-run: the arcade's four street doors are
   kept by `save_config`. Do not commit `wip-handoff/`.
4. Result on `2cbd3e7a`: room 56x51; `susukino-neon-corner` (33,40) → `LobbySapporo3`, door (35,46)
   (`TOWER_DOORS [(2,6)]`); `susukino-karaoke` (39,42) → `ShopSapporo4` "Karaoke bar · Sapporo", door (40,46)
   (`SHOP_DOORS [(1,4)]`, type `bar`); ramen gate (27,44), stalls at x 18/21/24; `room['tramways']` on row 48
   with a stop at x 23; 38 districts in 12 rooms; lint 0 errors for Sapporo, `ShopSapporo4`, `LobbySapporo3`
   and `ChikagaiSapporo`; Sapporo 0.06 / 0.17 / 80%; `play.js check`, `sync_cities.py --check` and
   `test_blog_to_npc.py` pass; `check_generators.py` reads exactly as the step 0 baseline (54 ok, 2 skip, the
   same five DRIFT lines), so every generator is a no-op on its second run.
5. Three unit tests then fail and are fixed in the tests: `lobbies.test.js` twice (the total, 16 → 17, in
   "every lobby is behind the doors of a tower…", l.129; and `dry run: 15 interior(s)` → 16 in "a block of
   flats with a 7-Eleven…", l.150, whose second dry run includes Sapporo) and `sapporo.test.js` "Susukino:
   no sealed building…" (its regex finds `standbar:` before `bar:` and reads its four items; anchor it on a
   word boundary). `glows-trams.test.js` passes as it is: master's test already accepts a room that declares
   `tramways`.
6. Not run in the review, still to do: `node tools/test_game.js --reverse`, `rehearse_blog.py`, the browser
   regression, and the browser walk (ride past the stop, the karaoke bar's counter, a bump on a ramen counter,
   the neon by night).
7. Docs: Sapporo's section, `ambient-traffic.md` (a room now declares `tramways`), the shop table.

If the ref is missing from the checkout, rebuild from the values in step 4; the asphalt family and the two
ramen stalls then have to be redrawn in `generate_sapporo_art.py`.

### Stage B — Asahikawa (42x32, slot unchanged)

Fixed: room size; river rows 17–19; station door (32,9) with exit (32,10); south lane rows 28–29; the path on
cols 20–21. Asahikawa has no dated post. The trip start is computed (today (31,12)); re-check it per recipe
step 5. Stage B needs stage A (`ramen` in `Shop.VENUES`).

| Where | Change |
|---|---|
| Station | `house-blue` out; `asahikawa-station-front` at (28,5), doors (32,9), (33,9). Platform strip dropped, with the row-5 platform-edge fence on cols 18–34. The row-6 fence runs only where no building's top row stands on it: cols 1–11, 15–17, 24–27, 38–40 (the 7-Eleven, sake shop, bakery and the front all start on row 5 or 6; `Builder.put` raises on a second tile in a cell) |
| Heiwa-dori | `heiwa-paving-autotile` over about (11,10)–(38,12) with a leg (19,13)–(22,15) to the bridgehead. North side, feet on row 9, west to east: `seven-eleven` (12,6) door (13,9); `heiwa-shop-books` (15,7); `heiwa-shop-sake` (18,6); `heiwa-shop-bakery` (21,6); `heiwa-shop-woodcraft` (24,7). Crane and owl ice sculptures, `heiwa-bench`, `heiwa-lamp-post` on the paving. Props in the way go: `tree-snow` (13,6), the hedge on col 17 rows 7–10, `lantern-red` (19,15), (22,15). The yard behind the shops (cols 2–11, rows 7–10) must not become a walkable dead end: close it on col 11 or plant it |
| Ramen alley | machiya trio and `ramen-banner` props out; `ramen-shoyu-front` (2,10), `ramen-narrow-front` (6,10), `ramen-miso-front` (8,10), feet on row 13, on `ramen-alley-autotile` rows 14–15, cols 2–16; `asahikawa-ramen-gate` (11,11) is one way in from Heiwa-dori (the alley is also open at its east end; the gate is not a choke point); lanterns, crates, stockpot. The stand (8,15) is already accepted today; the cell the pipeline refuses is (10,15) (a prop foot on row 14 above a bank shrub on row 16 leaves a one-cell lane). Rule for the rebuild: no prop foot on row 14 directly above a row-16 shrub, so every alley cell on row 15 can be stood on |
| Asahibashi | `asahikawa-bridge` out. In the art tool set `BRIDGE_ROWS = 5`; the arch glow rows are hard-coded for the old height (`y=414`, near l.2086 and l.2094) and `--manifest` asserts until they are computed from `BRIDGE_ROWS`; fix the "2x7" texts. Three committed PNGs change (deck, both arches). `asahibashi-deck` at (20,16) over rows 16–20, `-arch-w` on col 19, `-arch-e` on col 22, `-brace` at (19,18) on Tops |
| Riverbank | `house-red`/`-black`/`-blue` out (the one at (37,25), today's `HouseAsahikawa1`, is not replaced); `hokkaido-house-red`, `-blue`, `-red` at (4,23), (9,23), (14,23), doors (5,26), (10,26), (15,26); `tree-snow` (13,22) and `sakura-small` (15,26) go (one is a door front); the white vending machine at (7,25) stays (a rehearsal case stands there); `ice-fishing-tent`, `-hole`, `ice-crack-a/-b` on the river; `snow-fence-h` runs |
| Zoo gate | `shrine` prefab, foxes and `torii-red` out; `zoo-gate` at (29,22) (feet row 25). The drawn gate has no back: its manifest makes (0,3) and (4,3) solid and (1..3,3) walk-through. Give its prefab three more solid cells, (1..3,2), so the arch is a porch one cell deep and nobody walks on under the roof into the wood; `zoo-fence-h`/`-end` either side, `zoo-ticket-booth`, `penguin-walk-a/-b`, `zoo-seal-statue` |

- Art fix while registering: the ramen gate's long-vowel mark is drawn as a vertical bar
  (`generate_asahikawa_art.py` near l.1093/1116); draw it horizontal. `asahikawa-bridge_0_0` and
  `ramen-banner_0_0` are still drawn by `generate_hokkaido.py` (its `--scenes` reads the banner); leave that
  tool and its PNGs alone.
- Interiors: `HOUSE_DOORS['hokkaido-house-red_0_0'] = (1, 3)` and the same for `-blue` → `HouseAsahikawa1..3`
  in door order (5,26), (10,26), (15,26): all three keys are re-used for new houses. Add `'Asahikawa'` to
  `generate_konbinis.ALL_HOSTS` → `KonbiniAsahikawa1` (stores 16 → 17). Shops, by the Shops rule: sake →
  `standbar` "Sake bar"; bakery → `bakery` "Bakery"; woodcraft → `souvenirs` "Woodcraft"; `ramen-shoyu-front`
  → `ramen` "Ramen"; the other two ramen fronts and the bookshop keep sealed door cells →
  `ShopAsahikawa1..4`. `generate_shrines.py` prunes nothing: delete the `ShrineAsahikawa1` room, its
  transporter and `tiled/shrineasahikawa1.tmj` by hand.
- Labels (`rooms: ('Asahikawa',)`, each with its offset): `asahikawa-station-front_` 'Asahikawa Station'
  (1,5) → (29,10); `asahibashi-deck_` keeps the old text 'the bridge over the frozen river' (1,-1) → (21,15)
  (so `rehearse_blog.py` case 9011 and `test_blog_to_npc.py:384` stand); `asahikawa-ramen-gate_` 'ramen
  alley' (3,3) → (14,14), not a cell in front of a ramen door; `zoo-gate_` 'the Asahiyama Zoo gate' (2,4) →
  (31,26). Delete the dead rows `asahikawa-bridge_` and `ramen-banner_` (`blog_to_npc.py:229–230`).
- Districts (they may not overlap; the first draft's did): `station-front` (11,5,39,12) stand (28,11);
  `ramen-alley` (2,13,16,15) stand (8,15); `riverbank` (2,16,39,27) stand (23,21), its description gaining the
  houses and the zoo gate.
- People: base NPCs keep their cells (Bailey (29,12), Damian (34,13), Dylan (24,14), Julia (24,22), Khoi
  (13,14), Sam (7,15), Xander (33,28)) unless one became solid or a door front. Julia's base line "There's a
  shrine on this side of the frozen river." is rewritten to the zoo gate.
- Rehearsal and pipeline cases aimed at what goes: `rehearse_blog.py` 9013 and 9017 ("the shrine"), 9014
  ("the torii gate") → the zoo gate; 9018 ("the vending machines") holds only while (7,25) stays;
  `test_blog_to_npc.py:861`; `:921–925` loses its one-cell lane and is rebuilt on a synthetic room, not on
  Asahikawa.
- Tests: `shrines.test.js` (l.33, 44, 199: 7 → 6 halls and the transporter order; l.385–418 runs a scratch
  rebuild on Asahikawa's shrine and is re-hosted on a town that keeps one), `houses.test.js` (l.54, 145, 236,
  280, 295–329, 418: the machiya and `SHOP_SIGNS` assertions go, the riverside row replaces them),
  `konbini.test.js:52` (13 → 14), `hud-phone-layout.test.js:183–184, 236–237`, `map-data`, `npcs`,
  `japan-map`; new `asahikawa.test.js`: front on the door cell, bridge deck walkable and flat, three
  reachable houses, nothing walkable behind the zoo gate, every row-15 alley cell accepted, stand cells
  walkable.
- Docs: `blog-pipeline.md:66`; `landmarks-and-towns.md` l.276, 348, 462, 481, 590, 629, 647, 695 ("east
  fox"); `buildings-and-street-props.md:29`; `ambient-traffic.md:61`.

### Stage C — Kanazawa, Shirakawa-go, Toyama

**Kanazawa: 60x52 → 60x44** (`hokuriku.SIZE`; `devhouse.world` height 3328 → 2816; x, y, the avenue on rows
30–32 and all ten seams unchanged; the stitched city stays 110x66).

Fixed: station door (33,9), exit (33,10); seams (59,30..32); `seven-eleven` (19,25) → `KonbiniKanazawa1`;
stand cells (11,29), (14,19), (46,20), (48,22), (19,29) (six dated posts stand on them and keep their cells).
Start cells are computed (today (13,29), (46,24), (21,29)); re-check per recipe step 5.

| District | Change |
|---|---|
| Station front | `house-black` out; `kanazawa-station-dome` at (30,6), doors (33,9), (34,9); what it covers goes (the platform cells on cols 30–31, the lamp at (30,7), the lanterns at (31,8), (35,8)). `kanazawa-tsuzumi-gate` at (31,11) (feet row 15), **not** on row 10: the exit cell (33,10) must not be under its roof; the hedge cell under its east post (col 36) is cleared. `kanazawa-bus-stop` replaces the stock one at (56,29). The main street (cols 32–34) starts at row 16 |
| Higashi Chaya | lane on `chaya-stone-autotile`; `kanazawa-chaya-a/-b` out; `chaya-front-a` at (12,15) (its door front is then (13,19), not post 669's cell (14,19)) with `-b`, `-c`, `chaya-gold-leaf-shop`, `chaya-phono-museum` beside it (feet row 18) |
| Temple hill | the solid wood (2,7)–(19,14) opens: `teramachi-stair` in a gap of the fronts, `teramachi-gate`, `teramachi-hall` on the hilltop. Eight rows hold stair, gate, hall and a court with no row to spare: if the manifest heights do not fit, the gate goes, not the hall. The old south-east Teramachi block, the stock shrine and its foxes are deleted with the rows |
| Katamachi | machiya, `highrise-yellow`, `midrise-apartment`, the shrub fill out; `katamachi-whisky-bar` at (9,24) door (10,28); `katamachi-yakitori` west of it; east of the 7-Eleven only six columns are free (25–30) and `katamachi-izakaya` plus `-kissaten` need seven: the izakaya goes in, the kissaten only if a vending machine or sign gives up its column. All feet on row 28; a paved lane on cols 14–17, rows 21–28 joins the avenue to the Chaya lane (the walls on rows 21–22 open there), `katamachi-andon-lanterns` along it; the ground behind the fronts stays closed |
| Castle | `kanazawa-ishikawa-gate`, `castle-wall-siding`, cones, grey foundations out; `kanazawa-castle-gate` at (42,15) (gateway cols 43–44; at (42,14) post 662 on (46,20) is more than three cells from it and `kanazawa.test.js`'s `near` fails), castle-wall family in line with its feet, `-turret`, `-storehouse` (door cell sealed), lawn in place of gravel |
| Kenrokuen | about (39,21)–(57,28) on `garden-path-autotile` over `garden-moss`; `kenrokuen-kotoji` (the land piece) at (49,20) with `kenrokuen-kotoji-water` in the pond below it (`kanazawa.test.js:258` wants water two rows under the lantern), a larger pond, yukitsuri pines, `kenrokuen-teahouse`, `kenrokuen-bridge` |
| Nagamachi (rows 33–43) | `sendai-gate`, `sendai-earthen-wall`, the four townhouses, the far-bank court out. Canal on rows 34–35 (`nagamachi-canal-n/-s` on the `Water` layer with colliders); `kanazawa-canal-bridge` at (20,33) from the avenue pavement; `nagamachi-wall` family with feet on row 39 and `nagamachi-wall-gate` openings where the lane must be reached; `nagamachi-samurai-gate` at (18,37) (walk cell (20,39)); `nagamachi-samurai-house` at (24,36) door (26,39); lane on rows 40–41, cols 2–33; wall on row 42 (the wall pieces are 1x2: check their tops against row 41's walkers); fence row 43 |

- No `sendai-gate` or `sendai-earthen-wall` remains in any Hokuriku room (`sendai-pine`/`-cedar`/`-maple`
  trees stay: the owner decided against a new tree set). `hokuriku.Kit.wall` stamps `sendai-earthen-wall`
  today and `generate_kanazawa.py` calls it at l.143, 200, 214: give `Kit.wall` the wall family as a
  parameter and pass `nagamachi-wall` / the castle-wall family; grep the three Hokuriku generators so no
  caller is left on the old default.
- Interiors:
  - `SHRINE_DOORS['teramachi-hall_0_0'] = [(2,3)]`, `generate_shrines.LOOKS['teramachi-hall_0_0']` (`'blue'`
    or `'red'`, whichever the roof is nearer; `None` would assert a stock roof) and a `NAMES` row calling it
    a temple ('Temple · Kanazawa' unless the owner prefers a name); run `generate_shrines.py Kanazawa` by
    name → `ShrineKanazawa1` (its old room is replaced, not duplicated; delete the stale tmj if the key
    changes).
  - `HOUSE_DOORS['nagamachi-samurai-house_0_0'] = (2, 3)` → `HouseKanazawa1` (a town's only house is named
    without a number; the phone-bar test pins the names).
  - Shops, by the Shops rule: `chaya-gold-leaf-shop` → `souvenirs` "Gold leaf"; `chaya-front-a` → `kissa`
    "Teahouse"; `katamachi-whisky-bar` → `tasting` "Whisky bar" (TASTING BAR, highballs); `katamachi-izakaya`
    → `standbar` "Izakaya"; `chaya-front-b/-c`, the yakitori front, the kissaten and the phonograph museum
    keep sealed door cells → `ShopKanazawa1..4`.
  - `HouseKanazawa2..4` and `LobbyKanazawa1/2` are pruned by the generators (delete their tmj). Kanazawa then
    has no tower: it drops out of the lobby host lists and is no longer a place with a job; say so in the
    hand-back.
- Labels (`rooms: ('Kanazawa',)`), offsets chosen to keep the fixed stand cells: `kanazawa-castle-gate_`
  (4,5) → (46,20); `kenrokuen-kotoji_` (-1,2) → (48,22) (the trailing `_` keeps it off `-kotoji-water`);
  `chaya-front-a_` (2,4) → (14,19); `katamachi-whisky-bar_` (2,5) → (11,29); `nagamachi-samurai-gate_` 'the
  Nagamachi samurai lane' (5,4) → (23,41), on the lane and clear of the gate's walk cell; `teramachi-hall_`
  'the temple on the hill' (1,4); `kanazawa-station-dome_` 'Kanazawa Station' (-1,4) → (29,10). The old rows
  go, including `sendai-gate_` with `rooms: Kanazawa`. Re-home 652 (Damian 11-06, today (18,39)) to the
  samurai lane and 707 (Bailey 11-09, today (45,44)) to the temple on the hill; the other six Kanazawa posts
  keep their cells.
- Districts: `higashi-chaya` keeps (2,13,30,20) and is renamed 'Higashi Chaya' (growing it north would
  overlap `station-front` (20,5,37,11)); new `teramachi` 'Temple hill' (2,7,19,12), stand at the hall's label
  cell; `nagamachi` (2,34,33,43) with stand (22,41) (its old stand (18,39) is now wall); `kenrokuen`
  (39,21,58,28); `castle` and `katamachi` descriptions follow the new pieces.

**Shirakawa-go and Toyama: touch-ups, sizes unchanged** (the seam rows and Toyama's river and path columns
come from `hokuriku.AT`, l.35–39, and these sizes).

- New **`tools/generate_hokuriku_town_art.py`** (helpers imported from `generate_kanazawa_art.py`, same
  `PIECES` / `--sheet` / `--manifest` shape, registered through `art_register`): `shirakawa-openair-farmhouse`
  (4x4, sealed), `shirakawa-icecream-stand` (2x3 counter), `shirakawa-ryokan` (5x5, door), `shirakawa-onsen`
  (3x2 pool, solid), `toyama-iwase-front-a`, `-b` (5x5, door at (2,4) like the machiya), `toyama-old-house`
  (3x5, door). Palette and outline weight follow the existing `shirakawa-*` and `toyama-*` sprites.
- Shirakawa-go: on the far bank the wood north and south of the bus bay opens just enough for the open-air
  farmhouse and the stand beside the road (cols 1–8, rows 5–16); the rest stays wood. The south farmhouse
  (18,23) becomes `shirakawa-ryokan`: its door front (20,28) is in the solid south wood today, so row 28 is
  cleared on cols 19–23 and joined to the east path; the onsen pool takes the paddies on cols 24–26, rows
  25–27. The viewpoint terrace is deepened, not widened: rows 4–7 on cols 28–31 (row 3 is under the peaks and
  cols 26–27 are the retaining wall). Districts: `village` shrinks to (16,7,35,22) and the new `ryokan`
  'Ryokan and onsen' is (16,23,35,28) (it may not sit inside `village`); the far-bank description gains the
  open-air museum. `HOUSE_DOORS` row for the ryokan → `HouseShirakawago1`.
- Toyama: the three machiya (12,10), (17,10), (22,10) give way to the two Iwase fronts; the five columns
  left over take trees and a bench, not a third stock house. By the Shops rule only `toyama-iwase-front-a`
  opens (`souvenirs` "Iwase shop"); `-b` keeps a sealed door cell (two `souvenirs` rooms on one street
  would be the same room twice). `house-blue` (24,25) becomes `toyama-old-house`; its door front is in the
  south wood, so row 31 is cleared from the door to the south path (or the house stands a row higher) →
  `HouseToyama1`; the south wood east of col 30 thins to half, keeping the solid edge
  `kanazawa.test.js:79–94` checks. Label `toyama-old-house_` 'the old house', inside `tram-street`'s bounds
  (grow them to row 31; `iwase` ends at row 16, so there is no overlap).
- Tests: `kanazawa.test.js` (size; l.170, 240, 249–259: stand table, post cells for 652 and 707, the kotoji
  water cell, the `sendai-earthen-wall ≥ 60` assertion becomes `nagamachi-wall` pieces, the bridge leads
  through the new gate; l.79–94 Toyama's south edge), `houses.test.js:329–415`, `lobbies.test.js:97–98,
  128–131, 150` (Kanazawa leaves both host lists; the totals drop by two), `shrines.test.js:34, 44, 186–200,
  386–449` (the `clear=` string goes; l.430–447 pins the old hall's cells), `japan-map`,
  `hud-phone-layout:166–238, 303–315`, `test_blog_to_npc.py:372–386, 1283–1294`; a case that
  `teramachi-stair` is never a start cell or an area post's cell (Shared code).

### Stage D — Sendai (70x48, slot unchanged)

Fixed: station door (35,9), exit (35,10); the stair (49,16); castle terrace and `sendai-masamune` (9,7);
`sendai-zuihoden` (47,8), its steps and its nine earthen-wall tiles on row 19; `sendai-pub` (26,16) door
(28,20) → `PubSendai1`; `sendai-kiln` (3,28) door (5,33) → `DistillerySendai1`; `seven-eleven` (38,17) →
`KonbiniSendai1`; `matsushima-pier`, `-ferry`, `matsushima-ball-rock` (62,18; Bailey's 10-27 line names it)
and the waterway; Aoba-dori (road rows 22–24); the samurai doors (17,33), (22,33), (27,33), (26,44); the cells
of the dated states the #217 tests pin: Julia 10-29 (29,21) (`pub.test.js`), Damian 10-29 and Julia 10-30
(6,34) (`distillery.test.js:22–28`). The trip start (55,24) is computed and pinned at
`dates-trips.test.js:304–321`: no new open door within two cells of the Matsushima crowd.

Because #217 has landed, `generate_sendai.py` must not name its rooms or art (`PubSendai1`, `DistillerySendai1`,
`pub-in-`, `distillery-in-`: `pub.test.js` and `distillery.test.js` check the generator's text), and
`generate_pub.py` / `generate_distillery.py` are not re-run: `roomgen.OWNED_DOORS` keeps both doors through
the town build, and `check_generators.py` shows it.

| District | Change |
|---|---|
| Station front | `house-black` out; `sendai-station-front` at (31,5) (cols 31–39), doors (34..36,9); deck spans and tanabata streamers on `sendai-plaza-autotile` |
| Downtown | main street cols 34–36, rows 12–32 becomes the pedestrian zelkova avenue on `sendai-jozenji-autotile` with `sendai-zelkova-a/-b` and `sendai-jozenji-statue`; where it meets Aoba-dori (rows 22–24) the road tiles stay and a crossing band is laid across cols 34–36. `highrise-yellow` → `sendai-midrise` at (22,15), doors (23,20), (24,20): the `lamp-blue` at (24,21) is a door front, move it to x=21. `sendai-izakaya` at (31,17) door (32,20) beside the pub (the vending machines at (31,17), (32,17) go; the bus stop at (33,13) stays or moves to the plaza). `highrise-apartment` out. Its block (cols 38–42, rows 9–16) faces the back of the 7-Eleven and cannot hold a street front: `sendai-gyutan` (4 wide) stands at its north end, about (38,10) (below the station front, which now reaches col 39 and row 9), facing a small paved court on rows 14–16 that opens onto the avenue's east pavement (col 37); `sendai-zunda` at (41,18) door (43,20) on Aoba-dori, where the two shrubs are (it must end before the Zuihoden wall on col 44). The arcade pieces (gate, roofs, floor, the kokeshi and sasakama shops) have no site that passes: they are not placed in this stage |
| Nikka | yard on `sendai-brick-yard-autotile`; `sendai-cask-rack`, `sendai-red-maple`. The free ground beside the kiln is cols 8–14: `sendai-yamadera` (6x6) and `sendai-distillery-warehouse` (6x4) do not both fit. Yamadera is the plan's piece: it stands at about (8,26) with cedars planted along its top edge (its manifest wants a wooded edge behind it), and the warehouse is left out unless the manifest shows both fit |
| Samurai quarter | machiya → `sendai-samurai-house-a` at (15,30), (25,30) and `-b` at (21,30); courtyard house → `-b` at (25,41) (4 wide: check col 28); the six other generic houses → at most three samurai buildings, each reachable (`-a`, `-b`) or `sendai-samurai-store` (door cell sealed); the solid compounds they stood in open only as far as those doors; both `sendai-gate`s ((20,36), (44,31)) → `sendai-samurai-gate` (4x3: check its overhang on the lane); earthen walls here → board-fence family; lane on `sendai-samurai-lane-autotile`; `sendai-kabuto-stand`, well, propped pine, stepping stones, andon lamp posts |
| Matsushima | concrete promenade → `sendai-boardwalk-autotile`. The promenade is three columns (56–58) and stays clear from row 5 to row 46: `sendai-cruise-booth` and `sendai-oyster-shack` stand on the open ground west of it, south of Aoba-dori (about cols 50–55, rows 26–31), the shack with a sealed door cell. `sendai-godaido` on an islet at about (62,20), clear of the ball rock, reached by `sendai-red-bridge` on row 23 from (59,23); nothing new at x ≥ 59, y ≥ 30 (`sendai.test.js` keeps that water solid); `sendai-bay-lamp-post` |

- After stages C and D no `sendai-gate` is placed anywhere and Sendai's `sendai-earthen-wall` count falls from
  76 to Zuihoden's 9. `sendai.test.js:74` (wall ≥ 60) and `:77` (a loop over gates that throws on none) are
  rewritten for the board fence and `sendai-samurai-gate`; `test_blog_to_npc.py:386` (the `sendai-gate_` label
  in Kanazawa) moves to `nagamachi-samurai-gate_` in stage C.
- Interiors: `TOWER_DOORS['sendai-midrise_0_0'] = [(1,5),(2,5)]` → `LobbySendai1` (same door cell (23,20));
  `HOUSE_DOORS['sendai-samurai-house-a_0_0'] = (2, 3)`, `-b` `(1, 3)` → `HouseSendai1..N` (today's four are
  keyed 2..5 and `houses.test.js` pins `[2,3,4,5]`; the generator renumbers from 1; N = 4 to 6). Shops, by the
  Shops rule, offsets from the manifest: `sendai-izakaya` (1,3) → `standbar` "Izakaya"; `sendai-gyutan` (2,3)
  → a new venue row `gyutan` (title 'GYUTAN', sells `karaage`, `edamame`, `nama-beer`) "Gyutan";
  `sendai-zunda` (2,2) → `kissa` "Zunda cafe"; the oyster shack sealed → `ShopSendai1..3`. The `STOREFRONTS`
  rule in `generate_houses.py` is generic code and stays; with the flats gone its tests
  (`lobbies.test.js:134–166`) move to a scratch room with a tower and a 7-Eleven across its door.
- Labels (`rooms: ('Sendai',)`, each with its offset): `sendai-station-front_` 'Sendai Station' (2,5) →
  (33,10); `sendai-yamadera_` 'Yamadera' (below its stair); `sendai-kabuto-stand_` 'the samurai residence'
  (0,3); `sendai-godaido_` 'Godaido hall', standing on the promenade at the bridge head; `sendai-zelkova-a_`
  'the zelkova avenue' (1,4). The pub, kiln, Masamune, Zuihoden and ferry rows are untouched. Districts:
  `station-front` grows to (22,6,39,11) and `downtown` stays (22,12,42,21), so they still do not overlap;
  downtown's description drops "ramen" and "hotels" and gains gyutan, zunda and the zelkova avenue;
  `samurai-quarter`'s drops "earthen walls".
- Post 520 (Bailey 2025-10-30, today (38,21)): `--rehome Bailey 2025-10-30 "Sendai · Nikka distillery
  (area)"`; the dry run on current master lands it on (8,34), not on (5,34), the cell in front of the kiln
  door. Dialogue untouched (choice 12); the hand-back names 520 as waiting for the owner's pipeline run.
- Tests: `sendai.test.js` (wall, gate, pine and machiya counts; the building regex; `lobbyDoor`; `opened`;
  the Matsushima cells; `near('Bailey 2025-10-30', …)` → the kiln; "the mats return below the first station
  transporter" → `TOWN_DOORS`' exit), `houses.test.js:329–364`, `lobbies.test.js:96, 102, 128–166` (the dry
  run now says `sendai-midrise`), `pub.test.js`, `distillery.test.js` (unchanged and green),
  `dates-trips.test.js:304–321`, `japan-map`, `energy`, `hud-phone-layout:207`, `regress.js:813–817`,
  `test_blog_to_npc.py:386, 572–596`.
- Docs: `landmarks-and-towns.md` l.468, 567, 580–582 besides Sendai's own section.
- `generate_sendai_town_art.py` keeps exporting `bar, glyph, puff, grounded, family` (Fukuoka's tool imports
  them).

### Stage E — Osaka (50x46, slot unchanged)

Fixed: station door (24,9), exit (24,10); canal rows 20–22, all water outside the deck, with its waterway
(`from 0` to `W-1`, three rows) and the deck on cols 21–28; `highrise-blue` at (3,7), door (5,17) →
`LobbyOsaka1`; `devhouse-osaka` (9,10) door (10,16); `discount-store` (13,9) door (15,16); `dotonbori-arch`
(21,12) and its posts on (21,16), (21,17), (28,16), (28,17); `dotonbori-wheel` (33,7) and its stand (39,19)
(posts 568, 615, 764, Dylan's base cell and `dates-trips.test.js:364` all stand there); the tower's cells
(21,29)–(28,41) and stand (26,43); platform vending machines (15,6), (17,6). The trip start is computed
(today (19,19)); re-check per recipe step 5.

Row bands, north to south:

| Rows | Band |
|---|---|
| 0–8 | rail and platform strip; `osaka-station-front` (10x6) at (20,4), doors (24,9), (25,9); what it covers goes (the platform cells on cols 20–22, the lamp at (21,7), the fence on (27..29,6)) |
| 9–10 | forecourt; the bus stop (21,11) moves to it or goes |
| 11–16 | north fronts, feet on row 16 (the blue tower keeps its own row 17), west to east: `highrise-blue`; Devhouse; Don Takote; `osaka-okonomiyaki-front` (18,13); arch; `osaka-crab-restaurant` (29,12); wheel with `osaka-takoyaki-stand` at (37,13) inside its frame only if a cell beside it can be stood on (else it stands on the boardwalk). **No second tower**: the wheel reaches col 44 and the border hedge is on col 48, so `highrise-glass` (4 wide) has no site |
| 17–19 | north `osaka-boardwalk-autotile`; `osaka-canal-rail` on row 19 with a post at each end and every third cell, **absent on cols 33–44** (the wheel's stand and the three posts are on (39,19)) and at the pier; `osaka-boat-pier` at (14,17) with its gate on (16,19) (the bikes on (13,17), (14,17) go; the scooter and the utility pole stay unless a footprint takes their cell); `osaka-neon-lanterns`, queue rope, menu board |
| 20–22 | canal; `osaka-quay-wall`/`-drain` on row 20 only if they are drawn on the bank cells' edge, not on water cells. `osaka-boat-landing` and `osaka-river-boat` are **not** moored by default: the ambient boats sail the full width of rows 20–22 and `roads-waterways.test.js:57–66` wants every canal cell water. They go in only if a one-row waterway (row 22; `AmbientBoats` reads `rows \|\| 1`) is shown in the browser to pass clear of a boat moored on rows 20–21 at about (17,20); the test's water loop is then rewritten to except the mooring |
| 23–24 | south boardwalk |
| 25–30 | south-bank fronts, feet on row 30, none on cols 21–28: `osaka-gyoza-izakaya`, `osaka-sprinter-billboard`, `osaka-dragon-ramen`, `osaka-sign-tower-a`, `-b` (7 tall: its top reaches the boardwalk, check the walk-behind); `osaka-shinsekai-arch` at (22,25) over the street, feet on row 28. The border closes the old avenue's ends (rows 24–28 at cols 0–1 and 48–49) |
| 31–32 | lantern lane, in two halves: cols 21–28, rows 29–37 are behind the tower and stay solid as today (a walker there is hidden by Tsutenkaku); the halves join through the south boardwalk and the plaza; `osaka-retro-paving-autotile` from here south |
| 33–37 | Shinsekai fronts, feet on row 37, cols 2–17 and 32–47: `osaka-oni-kushikatsu`, `-retro-arcade`, `-shogi-parlour`, `-tachinomi`, `-shooting-gallery`; `-gacha-row`, `-gacha-single`, `-lucky-idol`, `-fugu-lantern`, `-fugu-sign`, `-shinsekai-lanterns`, `-beer-crates` |
| 38–43 | Tsutenkaku plaza; fence row 44 |

- No road tile, traffic light, sakura, `highrise-apartment` or `house-*` remains. `osaka-wheel-mall` is not
  placed (it is Umeda's HEP Five, which the owner decided against).
- Tsutenkaku: the `tsutenkaku` prefab points at `osaka-tsutenkaku_0_0` (colliders unchanged);
  `game.lookUp.sprites['osaka-tsutenkaku'] = 0`; LANDMARKS row becomes `osaka-tsutenkaku_` (5,14); the old
  palette slot stays as a dead entry (the palette is append-only); `generate_tsutenkaku.py` leaves
  `ART_TOOLS` if nothing else uses its sprite; `check_distinct.py:49` names `tsutenkaku`: add
  `osaka-tsutenkaku` beside it.
- Interiors: `--lobbies Osaka` → one lobby, `LobbyOsaka1` "Lobby · Osaka" (blue); `LobbyOsaka2/3` and
  `HouseOsaka1/2` are pruned (delete their four tmj). Shops, by the Shops rule, offsets from the manifest:
  `osaka-crab-restaurant` (1,4) → `crab` "Crab house"; `osaka-dragon-ramen` (1,4) → `ramen` "Ramen";
  `osaka-oni-kushikatsu` (2,4) → a new venue row `kushikatsu` (title 'KUSHIKATSU', sells `karaage`,
  `edamame`, `nama-beer`, `highball`) "Kushikatsu"; `osaka-tachinomi` (1,3) → `standbar` "Stand bar"; the
  okonomiyaki front, the gyoza izakaya, the billboard (it has a door cell at (2,5)), the arcade, the shogi
  parlour, the shooting gallery and the two sign towers keep sealed door cells → `ShopOsaka1..4`.
- Labels, each with its offset: `dotonbori-wheel_` keeps (6,12) → (39,19); `osaka-boat-pier_` 'the Dotonbori
  boat pier' (2,1); `osaka-shinsekai-arch_` 'the Shinsekai gate' (2,-1) → (24,24), north of the arch so it is
  inside a district; `osaka-crab-restaurant_` 'the crab sign' (0,5) → (29,17), beside the door front (30,17),
  not on it. Districts: `dotonbori` (2,9,47,30) stand (31,18); `shinsekai` (2,31,47,44) stand (20,40).
- Posts (a dated state follows nothing; each keeps its cell unless re-homed): 568, 615, 764 (the wheel,
  (39,19)), 768 (arch), 769 (tower), 636 (vending) keep their cells; re-home 590 and 754 (both on (17,35)
  under a sakura that goes) → "Osaka · the Dotonbori boat pier" and "Osaka · Shinsekai (area)", and 681 →
  "Osaka · Dotonbori (area)" (its cell (30,17) is the crab restaurant's door front).
- Tests: `roads-waterways.test.js:22` and l.68–77 (Osaka's road assertions go; l.46–66 its waterway
  assertions stay), `dates-trips.test.js:342, 363` ('Osaka 17,35' for 754 → its new cell),
  `madeup-towns.test.js:40–66`, `houses.test.js:263, 338`, `lobbies.test.js:52, 81, 85, 128–131, 150`
  (totals drop by two), `:263–282` (it runs the house generator on Osaka) and `:285–321` (its scenario is
  built on Osaka's glass tower and flats: re-host it on a town that keeps two towers, or on a scratch room),
  `devhouse.test.js:111, 217` (they name `HouseOsaka1/2`), `stitched-city.test.js:225`, `energy.test.js`,
  `career.test.js:527` (check), `hud-phone-layout` ('Lobby · Osaka'), `test_blog_to_npc.py:410` (`SAKURA`
  moves to `Market`), `:503`; new `osaka.test.js`: no road or sakura, the rail's gap at the wheel, every
  re-homed post on its spot, nothing walkable behind the tower.
- Docs: `buildings-and-street-props.md:23–30, 43, 81–83, 103`; `landmarks-and-towns.md:16–18`;
  `ambient-traffic.md:15, 56, 68`; `generators-and-checks.md:13, 51`.

### Stage F — Fukuoka (62x62 → 58x62)

Cut cols 58–61 only (choice 8); `devhouse.world` slot 3968x3968 → 3712x3968 with x, y kept; the waterway's
`to` follows `W - 1`. The east hedge (`W - 2`) then stands on cols 56–57 and the last walkable column is 55.
Every literal at x ≥ 56 in `generate_fukuoka.py` moves west or goes (about twenty lines: lamps at 58, the
vending pair on (55,35), (56,35), trees, the plum at (56,47)); `Builder.put` raises on a cell outside the
room, so the generator says which.

Fixed: station door (30,9), exit (30,10); avenue cols 29–32; yatai row 34 and its ten stalls; river rows
40–42; south lane rows 57–58 with its lamps on row 59 and the fence on row 60; `fukuoka-tower` (10,7);
`canal-city` (12,24) with door cells (15,29), (16,29) → the mall atrium (#217), and what `mall.test.js` and
`tests/interiors.js:120–123` pin round it: the mall's colliders as they are (its top two rows, 24–25, carry
none), the cells (15..16,30..31) free, Julia's dated cell (14,30); `canal-fountain` (23,27); `hakata-yamakasa`
(42,27); `dazaifu-hall` (44,44) → `ShrineFukuoka2`, its bridge, torii, the court `rect(38,49,55,56)` and the
pond `b.pond(39,50,54)`; `seven-eleven` (49,15) → `KonbiniFukuoka1`; stand cells (11,37), (42,31), (10,19),
(45,49), (32,10), (14,30). Fukuoka holds eight dated states (two more are in `FukuokaStation`); all keep their
cells. Start cells are computed (today (30,10) and (16,30)); re-check per recipe step 5.

`generate_mall.py` is not re-run and `generate_fukuoka.py` and the art tool must not name the mall's rooms or
art (`mall.test.js:195`); `OWNED_DOORS` keeps the two door cells.

| District | Change |
|---|---|
| Hakata Station | `house-blue` out; `fukuoka-hakata-station` at (26,4) (cols 26–34, rows 4–9), doors (29..31,9), on `fukuoka-station-plaza-autotile`; what it covers goes (the row-6 fence on cols 26–28, platform cells, the lamp at (33,7)). The three high-rises, `midrise-apartment`, `house-black`, `house-red` out; in their row (feet on row 18, door fronts clear of the lamps on x 19, 23, 37, 42, 47, the bus stop (27,19) and the stand (49,19)): `fukuoka-dept-store` (15,13), `fukuoka-office` (20,13) door (22,18), `fukuoka-ramen-shop` (38,15) door (40,18), `fukuoka-mentaiko-shop` (43,16) door (45,18); the Christmas market on the plaza: three `fukuoka-xmas-hut-*`, `fukuoka-xmas-tree`, `fukuoka-illumination-arch` |
| Canal City | mall untouched; a strip of `fukuoka-canal` (with `-jets`, `-end-e/-w`, `fukuoka-canal-bridge`) on `fukuoka-canal-paving-autotile` on rows 30–31, cols 19–28 only (west of col 19 are the mall's pinned cells) |
| Old Hakata | stock `shrine-red` → `fukuoka-kushida-hall` at (36,27), door (38,30) (the cell `ShrineFukuoka1` has today); `pagoda-small` and both machiya out; `fukuoka-senbei-shop` at (33,27), `fukuoka-tochoji-hall` (45,27) (door cell (47,30) sealed), `fukuoka-hakata-ori-shop` (50,27) door (52,30), the `hakata-bei` wall family |
| Nakasu | promenade on `fukuoka-riverwalk-autotile`; `fukuoka-river-rail` and `-rail-lanterns` along the bank; `fukuoka-nakasu-gate` at (29,31) over the avenue end of the yatai row. There is no free ground north of the river for the three bars: they stand on the **south bank**, west of the avenue, with feet on row 47: `fukuoka-neon-bar` (10,44) door (11,47), `fukuoka-motsunabe-shop` (17,44) door (19,47), `fukuoka-pub` (22,44) door (24,47) |
| South bank | the Ohori lawn, its pond and its two sakura go. Below the bars' pavement (rows 49–58, cols 6–28) the west coast's sand carries on as `fukuoka-beach-autotile` with umbrellas |
| Momochi | sand → `fukuoka-beach-autotile` with the shore set (`shore_pieces(land, sea)`) down the coast; `fukuoka-beach-house`, umbrellas, `fukuoka-lifeguard-chair` inside the district's own bounds (6,6,15,23), beside the tower |
| Dazaifu | court and pond unchanged; `fukuoka-hedge` family closes the block so the way in is under the torii (the east side is already the room's hedge); `fukuoka-umegae-stall`, `fukuoka-lattice-cafe`; `fukuoka-plum-autumn` (3x3) in place of the plum trees (2x3) wherever three columns are free, at least four of them; `fukuoka-ox-statue`, `fukuoka-stone-lantern` |

- Cheap art fixes while registering: the plum name boards read "ウ乂" and should read ウメ. The `メ` glyph is
  shared (`generate_sapporo_art.py:151`): override it in the Fukuoka tool's own `KANA.update` (l.120), not in
  Sapporo's; every Fukuoka PNG that spells it changes (ramen, mentaiko) and is committed. The department
  store's sign says "TENJIN" (l.2789), another district, and should say HAKATA.
- `shore_pieces` lives in `generate_fukuoka_town_art.py` (l.3193), which imports Pillow; the tests run
  `python3 tools/generate_fukuoka.py` without it. Move `shore_pieces` to `roomgen.py` (no imaging import) and
  have both call it there.
- Interiors:
  - `SHRINE_DOORS['fukuoka-kushida-hall_0_0'] = [(2,3)]`, `LOOKS[...] = 'red'`, its `LARGE` entry if the
    hall is the large layout, a sealed-door prefab, and a `KINDS` row in `shrines.test.js:14–17` →
    `ShrineFukuoka1` (same key, same door cell).
  - `generate_pagodas.py` with no town deletes `PagodaFukuoka1` (delete its tmj).
  - `TOWER_DOORS['fukuoka-office_0_0'] = [(2,5)]` → the one lobby, "Lobby · Fukuoka"; the three other lobbies
    and `HouseFukuoka1..4` are pruned (delete their tmj). The prune's `shut_door` leaves `gk_blank`
    colliders on old door cells, some now outside the room ((58,31)) or on open ground ((57,31), (56,18)):
    remove every collider with x ≥ 58 and any on a cell with no building.
  - Shops, by the Shops rule: `fukuoka-ramen-shop` → `ramen` "Ramen"; `fukuoka-mentaiko-shop` → `souvenirs`
    "Mentaiko"; `fukuoka-hakata-ori-shop` → `souvenirs` "Hakata-ori" (another street); `fukuoka-pub` →
    `taproom` "Pub"; `fukuoka-neon-bar` → `bar` "Neon bar"; `fukuoka-lattice-cafe` → `kissa` "Cafe" (it has
    two door cells: both in its `SHOP_DOORS` row); the department store, the senbei shop, the motsunabe shop
    and the umegae stall keep sealed door cells → `ShopFukuoka1..6`.
- Labels, each with its offset: 'Hakata Station' moves from `building-entrance-1` to
  `fukuoka-hakata-station_` (6,6) → (32,10); `fukuoka-kushida-hall_` is not labelled (the float's row
  'Kushida shrine' stays); `fukuoka-tochoji-hall_` 'Tochoji temple'; `fukuoka-xmas-tree_` 'the Christmas
  market'; `fukuoka-nakasu-gate_` 'the Nakasu gate'; `fukuoka-beach-house_` 'Momochi beach';
  `fukuoka-neon-bar_` 'the Nakasu bars'.
- Districts (single rectangles, none overlapping): every x1 of 59 becomes 55; `hakata-station`
  (26,3,44,10); `old-hakata` (33,24,55,32); `nakasu` (9,33,55,42); `dazaifu` (33,43,55,56); `momochi` and
  `canal-city` unchanged (`momochi` cannot grow south: Canal City and Nakasu lie between); new `south-bank`
  'Nakasu south bank' (6,43,28,58), stand on the bars' pavement at about (18,48), description: the bars across
  the river from the yatai, the sand at the river mouth.
- Tests: `fukuoka.test.js` (l.37 and l.50 station door and `building-entrance-1`; three station doors, and
  the exit pinned to `TOWN_DOORS` (30,10) with the (30,9) transporter written first; l.65–66, 78, 102 the
  vending count, 132, 169 landmarks, 175–187, 200–201 `plum-tree_ ≥ 4` → `fukuoka-plum-autumn`, 213 posts, 263
  the world slot), `mall.test.js` (unchanged and green), `lobbies.test.js:92–95, 128–131, 150` (totals drop
  by three), `houses.test.js:329, 338`, `pagodas.test.js:14, 31, 43, 220, 240, 300–380`,
  `shrines.test.js:14–17, 35–36, 44, 63, 143, 379–460`, `hud-phone-layout:179–237` ('Lobby · Fukuoka'),
  `madeup-towns`, `map-data.test.js:192`, `japan-map.test.js:51`, `test_blog_to_npc.py:1161, 1276–1278`.

### Stage G — Tokyo: Asakusa and the station art (#70)

Ported rooms have no town generator. Each change is a re-runnable script in `GENERATORS` that edits only its
own cells of `config.json` (the `generate_izakaya.py` pattern: constants for cells, replace in place, a second
run is byte-identical), followed by the interior generators.

- New **`tools/generate_tokyo_art.py`** (in `ART_TOOLS`, registered through `art_register`; add
  `asakusa-` to `check_distinct.LANDMARK_ART` in this stage and `shibuya-`, `ueno-` building prefixes in H,
  or Tokyo's numbers read worse than its baseline 0.158 / 0.324 / 55%):
  - `tokyo-station_0_0` redrawn in pixel art (red brick, the domes, white banding) on its exact 41x8 cells
    and anchor, same key: no map change. Its `spriteMetadata` must come out byte-identical (anchors are
    stored rounded to four places; see `art_register`).
  - `tokyo-tower_0_0` redrawn 8x14 (was 8x15), same key; `spriteMetadata` anchor follows the new height. Not
    8x12: Tsutenkaku is 8x13 and `generate_tsutenkaku.py:5–9` calls it "the shorter tower".
  - `asakusa-stall-row-a`, `-b` (5 wide, 2 tall, solid): the street runs north–south, so a stall is seen
    from its side. `-a` stands on the west side with its awning and counter to the east, `-b` is its mirror
    for the east side. `asakusa-kaminarimon-lantern` (2x3, hangs in the gate, not solid).
- New **`tools/generate_asakusa.py`**:
  - Market: the two blank roofs are cleared and refilled with stalls, five per side. Read their extent from
    the colliders, not the roof art: cols 20–24 and 31–35, rows 27–37 (eleven rows; the west roof's row 27
    is walkable today; five stalls take ten, the eleventh gets a tree or a lantern post). The street between
    them (cols 25–30) and its lantern posts on cols 25 and 30 stay.
  - The lantern hangs in the gate at (27,22). The gate's roof tiles are on `Tops` at those cells and a cell
    holds one tile per layer: stamp the lantern on `Other` (or anchor it at (27,23), under the roof) and check
    in the render that it is drawn in front of the gate and behind nobody.
  - The three townhouses (roofs (11,31), (37,32), (42,32)) and `highrise-yellow` (15,22) are lifted with
    their colliders and with the signage that belonged to them (`7-11-sign-left` (14,24), the cones (14,30),
    (15,30)); their ground is refilled with stalls or trees. `KonbiniMarket5` (16,31), door (17,34), stands
    beside the high-rise and is not touched, nor are the other five 7-Elevens, the izakaya, Don Takote, the
    hall, the pagoda and the shrine.
  - Palace: the tower's tile moves from (8,6) to (8,4) and it now ends on row 17 (its top overlaps the station
    roof two rows more than it does today; if that reads badly in the render, fall back to 8x12 at (8,6) and
    correct the Tsutenkaku docstring); its colliders move to the same leg shape three rows up (rows 15–17),
    off the road; the legs then stand on the plaza at cols 8 and 15: check the pavement still passes. In the
    stitched city Palace rows 18–21 are Park rows 0–3, and Park carries its own copy: the `tokyo-tower-feet` tile at (8,0) **and twelve colliders** on (9..14,0), (8,1),
    (9,1), (14,1), (15,1), (8,2), (15,2). The script deletes the tile and all twelve, and
    `cities.TokyoCity.drop` goes.
- Then `generate_houses.py Market` and `--lobbies Market` delete `HouseMarket1..3` and `LobbyMarket1`; delete
  `tiled/housemarket1..3.tmj` and `tiled/lobbymarket1.tmj` by hand and remove the stray `gk_blank` colliders
  the prune leaves.
- Labels: `tokyo-tower_` offset (9,13) from the new tile cell → stand (17,17); 'the temple gate' moves from
  `red-small-pagoda-top` to `asakusa-kaminarimon-lantern_` with offset (-1,2) → (26,24), today's cell; `asakusa-stall-row-a_` 'the
  stall street' with an offset onto the street. `lookUp.sprites['tokyo-tower']` and `['tokyo-station']` stay.
  Asakusa's district description names the stalls. No post moves.
- Tests: `houses.test.js` (`Market: [1,2,3]` goes), `lobbies.test.js:89–91, 128–131, 150` (Market leaves both
  host lists; the totals drop by one), `occlusion-camera.test.js:270`, `roads-waterways`, `stitched-city`,
  `hud-phone-layout.test.js` ('Lobby · Asakusa' goes; l.315), `konbini` (still six),
  `test_blog_to_npc.py:1218–1248` (l.1226); new assertions: no tower collider on Palace rows 18–20 **and none
  on Park rows 0–2, cols 8–15**; the road under the old feet can be walked end to end in the stitched city;
  the stall cells are solid and the street between them is open; the lantern is over the street.
- Docs: `stitched-city.md:22` and the `drop` comment in `CityStitcher.js` (the dropped feet),
  `landmarks-and-towns.md:14–15` (both sprites are no longer line-art placeholders), `:465`, `:564` (the
  Market houses and lobby).

### Stage H — Tokyo: Park into Shibuya (west) and Ueno (east) (#94)

Needs stage A (`bar` in `Shop.VENUES`).

New **`tools/generate_park.py`** (in `GENERATORS`): owns Park's cells inside the pavement ring (cols 4–51,
rows 5–36) **except** these, which it never writes:

- the Devhouse (10,9)–(14,16), its door (13,16), its door front (13,17) and its square's floor (6,7)–(18,18);
- `KonbiniPark1` (24,4), door (25,7), door front (25,8); `KonbiniPark2` (33,21), door (34,24), door front
  (34,25);
- the three pagodas (34,7), (34,11), (34,15) with their tops on (34,4), (34,8), (34,12), the doors (34,17),
  (35,17) and the sealed rear door cells `pagodas.test.js:61–65` pins;
- the shrine (roof (39,7), hall (40,9), door (41,13)); the bell (46,8)–(47,11); both torii;
- the `traffic-light` at (24,36) with its collider on (24,38); rows 0–3; the ring roads and seams; hidden base
  cells (23,3), (23,4);
- the cells labels and people stand on: (33,10) (post 535), (24,8), (23,10), (41,15).

- Art, added to `generate_tokyo_art.py`: `shibuya-karaoke-izakaya` (4x5, door), `shibuya-screen` (a lit
  billboard for a tower side, with `glow`), `ueno-swan-boat-a`, `-b` (2x2, on water, solid), `ueno-boat-dock`
  (3x2, flat), and two 1x1 flat decals `shibuya-zebra-diag-a`, `-b`. The scramble is **not** a new autotile
  (a blob set cannot carry the two diagonals): it is `road-plain_0_0` floor with Tokyo's existing
  `crossing-h-*` / `crossing-v-*` bands on its four sides and the two decals laid along the diagonals on
  `Over Floor`. Ground, walkable; the game has no cars.
- Shibuya, cols 4–31:
  - the scramble replaces the dirt octagon, about (6,21)–(18,35); the Devhouse on its square faces it from
    the north;
  - a street runs east from the scramble on rows 23–25 to col 31, where it meets Ueno's paths; the old
    hedged dirt square and the gravel paths under the buildings below are cleared;
  - north side, feet on row 22: `discount-store` at (19,15) door (21,22) (the sakura on (19,15), (19,16) and
    the shrub on (19,18) go); `shibuya-karaoke-izakaya` at (24,18) door on row 22; the six vending machines
    stay on rows 10–11;
  - south side, three towers whose roofs line the street and whose doors (row 36) open on the south
    pavement, clear of the traffic light's cell (24,36): `highrise-blue` at (19,26) door (21,36);
    `highrise-glass` at (25,27) doors (26,36), (27,36); `highrise-yellow` at (29,29) door (30,36) (move
    them a column if the manifest widths differ, never onto (24,36)); `shibuya-screen` on the blue tower's
    street side.
- Ueno, cols 32–51: the shrine court is kept as built; south of it a pond about (37,26)–(49,33) with the two
  swan boats and the dock on its north bank, gravel paths round it and to the court's torii, autumn trees
  from Tokyo's own `tree-1/2/3` and sakura (no `sendai-*` trees).
- Interiors: `--lobbies Park` → `LobbyPark1..3`; add `'Park'` to `generate_discount_stores.ALL_HOSTS` →
  `DonTakotePark` (one more store and stamp: 17 → 18); `shibuya-karaoke-izakaya` is a shop with venue `bar`
  "Karaoke bar" → `ShopPark1`.
- Labels (`rooms: ('Park',)`): `ueno-boat-dock_` 'the swan boats' with an offset onto the bank. Two unscoped
  rows start matching in Park and each must land on a walkable cell: 'the Don Takote discount store' (→
  (22,23), on the street) and 'the pond' on `pond-autotile_corner-nw` (keep the bank cell it picks clear).
  `shibuya-scramble` has no sprite to label, so the crossing's spot is the district stand. Districts
  `shibuya` (4,3,31,37) stand on the scramble and `ueno` (32,3,52,37) stand at the dock replace `Park`;
  `districts.py:30, 85` and its docstring follow. Room names do not change ("Park", "Lobby · Park 1..3", "Don
  Takote · Park"): the owner's display-name table left Park as it is, and districts are read by the blog
  model, not the HUD.
- Posts: Bailey 2025-11-04 (625) from Tokyo (32,21) → "Park · the swan boats"; Bailey 2025-11-02 (578) from
  Tokyo (30,22) → "Park · Shibuya (area)". Bailey's 2025-11-18 state on the same Tokyo cell (32,21) stays.
  Post 535 stays.
- Tests: `test_blog_to_npc.py:1218–1220` (it asserts one district per Tokyo room, named as the room: Park now
  has two) and `:1248` (`['Park'][0]`); `lobbies.test.js:128–131, 150` (Park joins both host lists; the
  totals rise by three); discount-store and stamp counts; `energy`, `hud-phone-layout`, `stitched-city` (Park
  reach, no pockets), `pagodas`, `shrines`, `devhouse` (all still true); new `park.test.js`: every kept
  footprint and cell above unchanged, scramble walkable end to end, both posts on their spots.
- Docs: `landmarks-and-towns.md:1095` (the district `Park`) besides Park's own section.
- Before this stage, re-read Park on the master it lands on: if anything else was built in Park since this
  design, add its footprint to the kept list rather than moving it.

## Data and interfaces

- **Room sizes and world slots** (`config.json` `worldWidth/Height`, `devhouse.world`, `assets/map/world-map.*`):
  Sapporo 56x51 (grows north); Kanazawa 60x44; Fukuoka 58x62; all others unchanged. `hokuriku.SIZE` follows.
- **`config.json`**: new `spriteMetadata`/`tileNames` entries per stage, some with `glow` (first use of that
  field in data; `Glows.js` already reads it) and `depthBias`; `tilePalette` only grows; Sapporo gains
  `tramways`; `game.lookUp.sprites['osaka-tsutenkaku']`; `cities.TokyoCity.drop` removed; districts added
  (`susukino`, `teramachi`, `ryokan`, `south-bank`, `shibuya`, `ueno`), `Park` removed.
- **Rooms removed**: `ShrineAsahikawa1` (by hand); `HouseKanazawa2..4`, `LobbyKanazawa1/2`; `LobbyOsaka2/3`,
  `HouseOsaka1/2`; the three surplus Fukuoka lobbies, `HouseFukuoka1..4`, `PagodaFukuoka1`;
  `HouseMarket1..3`, `LobbyMarket1`. For every one of them the `tiled/*.tmj` is deleted by hand. **Added**:
  `LobbySapporo3`, `ShopSapporo4`, `KonbiniAsahikawa1`, `Shop<Town>*` per stage, `HouseShirakawago1`,
  `HouseToyama1`, `LobbyPark1..3`, `DonTakotePark`, `ShopPark1`. **Kept under the same key and door cell**:
  `PubSendai1`, `DistillerySendai1`, the mall atrium, `LobbySendai1`, `LobbyOsaka1`, `ShrineFukuoka1/2`,
  `ShrineKanazawa1`, every konbini. House, lobby and shop keys are renumbered by their generators in (y, x)
  order.
- **Counts players can see**: stores (stamps, Konbini Pilgrim's total) 16 → 17 in stage B → 18 in stage H.
  Lobbies (job sites): +1 in A, −2 in C (Kanazawa has none after it), −2 in E, −3 in F, −1 in G, +3 in H.
- **Door tables** (`roomgen.py`), **`SHOP_TYPES`**, **`Shop.VENUES`**: `bar`, `ramen` from stage A; `gyutan`
  (stage D) and `kushikatsu` (stage E), each one row selling existing catalogue items; an `Interactions` row
  only for a counter that is bumped rather than entered.
- **`blog_to_npc.LANDMARKS`** and **`districts.py`**: rows as listed per stage. The blog workflow in
  `devhou-se/www-jp` is not changed.
- New tools: `art_register.py`, `generate_hokuriku_town_art.py`, `generate_tokyo_art.py`,
  `generate_asakusa.py`, `generate_park.py`. `shore_pieces` moves into `roomgen.py`. No change to the save
  format, URLs or the deploy workflow.

## Tests

Per stage, from `gamev2/`, before the commit:

```bash
node tools/test_game.js && node tools/test_game.js --reverse
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py > /tmp/cg-stage.txt; diff /tmp/cg-baseline.txt /tmp/cg-stage.txt
python3 tools/sync_cities.py --check
python3 tools/check_distinct.py
node tools/play.js lint <Room> [<City>]
python3 tools/rehearse_blog.py
node tools/browser/regress.js              # 20 of 20
```

All are green except `check_generators.py`, which cannot be on today's master with the art stack installed
(recipe step 0): its gate is the **diff against the step 0 baseline**. The only lines that may differ are
new `ok` lines for the tools and generators the stage added; a new `DRIFT` or a missing line fails the
stage. If #230 / #235 land first the baseline is simply all `ok`. Also run the unit tests once in a shell
without Pillow (`python3` without the venv): the Checks workflow runs them that way, and a generator a test
spawns must not import an art tool.

What each stage must prove beyond the updated pins:

- every station door cell enters the station and the station's mats return to the cell below the *fixed* door;
- every interior named as kept is entered from the same host cell; every interior named as removed is gone
  from `config.json` **and** `tiled/`; no transporter points at a missing room; no `gk_blank` collider is
  left on a cell with no building or outside the room;
- every dated post in the town stands on a walkable cell within two cells of the sprite its label names, and
  no NPC stands on the cell in front of a door;
- each district's stand cell is walkable, no two districts of a room overlap, and `districts.py --report`
  lists no label outside a district;
- for each trip day in the town, `play.js date <day>` then `start` gives a walkable cell that is not a door
  front, and the pinned cells in `dates-trips.test.js` are the ones looked at in a render;
- every shop room's name fits the phone bar (`hud-phone-layout.test.js`) and its counter opens the venue
  named in the stage;
- the town generator (or the Tokyo script) run twice is a no-op (the `check_generators.py` diff);
- `check_distinct.py`: the town at or under 0.25 / 0.40 and at or over 1/3 own, or the reason it cannot be yet
  is in the commit message; no *other* town's numbers moved.

Browser check per stage (Playwright): walk from the station door to each district's stand cell and into one
interior of each kind the stage adds, by day and `?tod=night`, at 1280x960, 844x390 and 667x375; for stage A
also watch a streetcar stop and leave. Screenshots to `/work/media/`.

## Risks and open questions

- **Size.** This is eight map rebuilds. A run that finishes A and B meets the dated deadline; the rest follow
  from the same design. Stopping mid-stage is the only bad outcome: a stage is committed whole or not at all.
- **Byte-exact art.** With the wrong Pillow or zlib every city art tool reports drift on untouched master.
  With the right one five other tools still drift (recipe step 0), so the gate is the baseline diff, not a
  green run.
- **Undrawn art** (stages C touch-ups, G, H): about 16 new pieces with no reference sheet. They must pass the
  crop test beside the existing Tokyo and Hokuriku art; if a piece does not read, the stage ships without that
  piece rather than with a weak one, and says so.
- **Unverified cells.** Stage A was built end to end on a scratch copy of `2cbd3e7a`. For B–H the *fixed*
  cells, door offsets, district bounds and the conflicts named in each stage were checked against master's
  `config.json`, generators and manifests in the review, but no town was built: lint and reachability
  decide, and the *fixed* cells are the contract. The tightest fits, where a piece is most likely to be
  dropped: Kanazawa's temple hill (eight rows), Katamachi east of the 7-Eleven, Sendai's Nikka yard and
  gyutan court, Osaka's takoyaki stand, Fukuoka's Old Hakata row.
- **#217 interplay.** #217 is on master. Stages D and F do not re-run its generators; they keep its three
  host sprites, door cells and dated cells fixed, and its tests (`pub`, `distillery`, `mall`) stay green
  untouched. A town generator that names one of its rooms fails those tests.
- **Serial lane.** Any other map change landing on master mid-stage conflicts in `config.json` and `tiled/`;
  rebase by re-running the generators, never by merging the JSON.
- **Saved state.** The save holds no room key for a house, lobby or shop and no player position, so
  renumbered and removed interiors lose nothing. What a player does see: Konbini Pilgrim is computed from the
  save each time, so someone who had every stamp reads 16 of 17 after stage B and until they visit the new
  store (and again after H). A career in progress is kept (`merged`, `shifts`, `earned`); only the places to
  sign on change.
- **Dialogue that names a removed thing.** Post 520 still says "this 7-Eleven" at the distillery until the
  owner re-runs the pipeline for it (the plan asked for new dialogue; it needs the post text and an API key
  this pipeline does not have); posts 590 and 754 were placed by a sakura label and move to the pier and
  Shinsekai without new dialogue; post 731 on Fukuoka (10,19) says "Took a walk around Ohori Park" after the
  Ohori lawn has gone; Julia's post 501 in Sendai mentions ramen. Base lines are rewritten in the stage
  (Asahikawa's shrine line); dated lines are listed in the hand-back, not edited.
- **Shop floors are one layout.** Every opened shop is the same room with a different shelf and menu. The
  Shops rule keeps two of a kind off one street, but a player who enters five shops in a town sees five
  near-identical rooms. Distinct shop interiors are a later ticket, not this one.
- **Tokyo Tower's height.** 8x14 keeps it taller than Tsutenkaku; the fallback 8x12 does not.
- **Owner calls.** The choices in the Approach table are defaults, not questions; the ones most likely to be
  overruled are 1 (Asahikawa's shrine), 7 (Osaka's size and single tower), 8 (Fukuoka only loses four
  columns), 10 (Asakusa's interiors), 11 (Park mirrored), 13 (no ramen front in Sendai) and 15 (the Nakasu bars on the
  south bank). Posts 587 and 610 stay out of scope.

## Review

Design review on `origin/master` = `2cbd3e7a`. Stage A's port was run end to end in a scratch checkout; for
B–H each claim below was checked against `config.json`, the generators, the art manifests and the tests. No
criticism needs the owner before work can start.

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | The design was written on a stale base: #217 (pub, distillery, mall atrium), #228 and #229 had landed, yet it treated #217 as "may land" and told D and F to re-run its generators | Context and Risks state what is on master; D and F fix #217's cells and tests and do not re-run its generators; "merge master first" added to the Approach | yes |
| 2 | "All gates green" cannot be met: with the pinned art stack `check_generators.py` exits 1 on untouched master (five art tools drift, #230/#235) | Step 0 records a baseline; the gate is a diff against it | yes |
| 3 | Stage A's conflict advice ("keep both sides") breaks the konbini shelves (`Interactions.js`) and drops master's venue rows; the generated outputs of the old commit were to be merged by hand | Exact per-file resolutions, a discard list for generated files, the regeneration order and the three tests that fail afterwards, all from a real run | yes |
| 4 | `art_register` was specified to read each tool's lights, but the five tools store them in five shapes (one in pixels with no radius); and it would give `lamp-post` / `-lanterns` sprites a glow, which `glows-trams.test.js` forbids | Each tool gets a `glow_spots()`; `register()` takes cells, clamps to 2.5, skips lamp and lantern keys, rounds anchors as the existing entries | yes |
| 5 | Door-table rows were written in the wrong shape (`HOUSE_DOORS` takes one tuple, the others a list) and shrine halls need `LOOKS` (and `NAMES`/`LARGE`) rows the design never mentioned | Shapes stated in the Doors rule and used in every stage | yes |
| 6 | "Shops by the door rule" was unbuildable as written: `SHOP_TYPES` needs a label, a venue and a shelf; most named fronts have no fitting venue; `izakaya` buys and grills fish; several fronts on one street would open identical rooms; labels over 11 characters fail the phone-bar test | New Shops rule and an explicit shop table per stage; at most one front of a venue per street; two new venue rows (`gyutan`, `kushikatsu`); the rest sealed | yes |
| 7 | District bounds overlapped in Asahikawa, Kanazawa, Shirakawa-go and Fukuoka (`test_blog_to_npc.py` refuses overlap), and "`momochi` grows south" is impossible for one rectangle | Non-overlapping bounds given per stage; new districts `teramachi`, `ryokan` (beside `village`), `south-bank` | yes |
| 8 | Many new `LANDMARKS` rows had no stand offset, so a visitor would stand on the sprite's top-left cell (refused), and several given offsets landed on a door front, a wall or outside a district | Every row has an offset and its resulting cell; the rule is in recipe step 5 | yes |
| 9 | Trip start cells were listed as *fixed*, but they are computed by `Trips.standNear` and move when a door opens near the day's crowd | Removed from the Fixed lists; a before/after check per trip day; Sendai's oyster shack sealed so (55,24) holds | yes |
| 10 | "Posts follow the wheel" (Osaka): a dated state follows nothing; and the wheel's new stand (39,18) was inside the wheel's box in a sealed pocket | Offset (6,12) and the cell (39,19) kept; the canal rail has a gap on cols 33–44 | yes |
| 11 | The stage B text had the wrong refused cell ((8,15) is accepted today; (10,15) is not), a fence through three buildings' top rows, an art constant (`BRIDGE_ROWS`) whose change makes `--manifest` assert, and a zoo gate "closed behind" that the art leaves open | Corrected cells, the fence columns, the art fix and three extra solid cells in the gate's prefab | yes |
| 12 | Stage B removes things other files still aim at: rehearsal cases 9013/9014/9017, Julia's base line, the scratch shrine test hosted on Asahikawa, dead `LANDMARKS` rows; `generate_shrines.py` does not prune | Listed; the bridge keeps its old label text so two cases stand; the shrine room is deleted by hand | yes |
| 13 | Kanazawa: the tsuzumi gate at (31,10) puts the arrival cell under its roof; `chaya-front-a` at (13,15) puts a door front on post 669; the castle gate at (42,14) fails the post-662 test; `Kit.wall` still stamps `sendai-earthen-wall`; the samurai-lane label blocked the lane mouth; `teramachi-stair` is not matched by `/stairs/` | Cells moved by one, `Kit.wall` takes the family, offsets changed, the match widened | yes |
| 14 | Shirakawa-go and Toyama: the terrace "widening" ran under the peaks and into the wall; the ryokan's and the old house's door fronts were in solid wood; two `souvenirs` fronts side by side | Terrace deepened instead; rows cleared to the doors; one Iwase front opened | yes |
| 15 | Sendai: gyutan and zunda do not fit the flats' block and would face the back of the 7-Eleven; Yamadera and the warehouse do not both fit; booth and shack block the three-column promenade; a lamp stands on the midrise's door front; the plan's ramen shop was dropped silently; the arcade had no site; removing the gates and walls breaks `sendai.test.js:74, 77` | Sites given; warehouse and arcade left out; choice 13 records the ramen shop; tests listed | yes |
| 16 | Osaka: `highrise-blue` was moved a row without saying so; the glass tower has no site; a moored boat breaks the waterway test and sits in the ambient boats' lane; the lantern lane ran behind Tsutenkaku; `devhouse.test.js` and a `lobbies.test.js` scenario are built on rooms that go | Blue tower fixed at (3,7); one tower (choice 7); pier only, mooring optional and conditional; the lane in two halves; tests listed | yes |
| 17 | Fukuoka at 56x60 contradicts its own Fixed list: the Dazaifu court and pond reach cols 54–55, the fence would land on the lane, and Old Hakata lacks two columns; the Nakasu bars had no cells | 58x62 (choice 8); bars on the south bank with their own district; Old Hakata cells given | yes |
| 18 | Fukuoka: `shore_pieces` in a Pillow-importing module breaks tests in CI; fixing the `メ` glyph in the shared table would change Sapporo's PNGs; the mall's pinned cells were not in the Fixed list; "nine posts" is eight; the prune leaves colliders outside the smaller room | `shore_pieces` to `roomgen.py`; the glyph overridden in Fukuoka's tool; Fixed list extended; collider clean-up | yes |
| 19 | Asakusa: the road under Tokyo Tower stays blocked, because Park carries twelve colliders of its own for the feet; the roofs are eleven rows, not ten; the lantern's cell already holds a `Tops` tile; a 5x2 stall "facing the street" is a side view; an 8x12 Tokyo Tower is shorter than Tsutenkaku | Park's colliders deleted and tested; rows from the colliders; lantern on `Other`; side-view stalls; 8x14 at (8,4) with a fallback | yes |
| 20 | Park: the kept list missed the traffic light (inside the glass tower's footprint), pagoda tops and rear doors, both konbini door fronts, label stand cells and the Devhouse square; `shibuya-scramble-autotile` cannot carry diagonals; `test_blog_to_npc.py:1218–1220` asserts one district per Tokyo room; `check_distinct` would read Tokyo as worse | Kept list extended, towers shifted a column, the scramble built from existing road pieces and two decals, tests and prefixes listed | yes |
| 21 | `LANDMARK_ART` additions as whole family names (`heiwa-`, `ramen-`, `zoo-`) would count ground and props as buildings and catch Sapporo's `ramen-alley-lanterns` | Building prefixes only; print the table before and after | yes |
| 22 | Saved state was "assumed" safe and store counts were left to "check before stage H" | Stated precisely: nothing lost; Konbini Pilgrim reads N of N+1 after B and H, by design of #209; said in each commit | yes |
| 23 | `generate_houses.py` prunes rooms but leaves their `tiled/*.tmj`; shrines and konbinis are not pruned at all | Recipe step 3 and the per-stage lists | yes |
| 24 | Plan gap: post 520's dialogue was to be regenerated | Not possible here (needs the post text and an API key); choice 12 stays and the hand-back names it | no: cannot be done in this pipeline |
| 25 | Plan gap: Asakusa "townhouses and high-rise out" removes one of Tokyo's job sites until stage H; keeping the tower would be safer | The plan and the owner's table ("high-rise: Shibuya and Osaka's station front only") are explicit; choice 10 stays and is flagged | no: the plan decides |
| 26 | #94 asks for Park to become Shibuya and Ueno, but the HUD still says "Park" | The owner's display-name ruling left Park unchanged; districts carry the names for the blog model | no: owner's earlier ruling |
| 27 | Asahikawa's plan budget was "six new sprites and one ground tile"; the drawn set registers about 34 | The art exists and passes its own sheet; only what the map places is registered | no: nothing to change |
| 28 | Simpler alternative: one stage per ticket instead of eight in one design | The owner asked for the rest of the plan in one design; the stage boundary rule already lets a run stop after any stage | no |
