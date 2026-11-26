# Ambient traffic: passing trains, boats and streetcars

The decorative trains and moat / canal boats (`src/AmbientTrains.js`, `src/AmbientBoats.js`) and the `waterways` data;
the streetcar on a room's `tramways` (`src/AmbientTrams.js`).

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Ambient Traffic (issue #29)

Purely decorative movers that make a room feel alive. Both are built in `GameScene.create()`, re-armed by
`RoomManager.switchRoom()` through `onRoomChange(roomKey)` (which also destroys whatever is on screen), find
their route in the room's map data rather than in coordinates, have no collision, and send the first one
3-10s after you enter a room and another every 15-40s after it finishes.

- **`AmbientTrains`** - any room with `train-track*` tiles that is not a `stations` room (Palace, Inaka,
  Yukimura, Osaka, Sendai, Sapporo, Asahikawa) gets a train running the topmost track row, off-screen edge to
  off-screen edge, depth `min(48, (row + 1) * 10 + 4)` - 48 for a track on row 4 or lower, and always just
  under a player standing on the track row (feet depth `(row + 1) * 10 + 5`), so on a level crossing the
  player is drawn over the passing train in every room.
  - **Palace's track is row 3, behind Tokyo Station's roof line** (issue #63). The station sprite
    (rows 2-9, depth 100) is drawn over the train, and its top two rows are empty apart from the domes and
    the centre gable, so on row 3 the rails show along the back of the roof and the whole train runs on
    them, passing behind the domes. It used to be row 5, which is half way up the building: the train was
    a strip of roof sliding along above the station with no rails under it. It is a map change; the
    only code change is the depth rule above (44 on row 3, so the player on the crossing is not drawn
    under the train). Both roads cross it: the west road's two cells, `(0,3)` and `(1,3)`, and the
    east road's three, `(54,3)`-`(56,3)` (issue #138; left unsealed, as `seal_tracks.py` does for any
    track cell over a road, with cones on `(53,4)` and `(57,4)` beside the east one - a unit test
    fails a sealed road-over-track cell in any room). **`(2,2)` must stay open**: with the lantern on
    `(2,1)` and the track sealed from column 2 to the east road, it is the only way from the west
    road into the strip behind the station (rows 0-2) without going round by the east crossing, the
    strip's other entrance - do not put a cone or prop there. From the forecourt the camera cannot reach row 3 - the train is seen from
    the west road, the yards beside the station (rows 4-7) or the strip behind it.
  - In the stitched city the Palace track runs on west through the woods and ends in them, short of Machi:
    an end of track that is not at the room's edge is "closed", and the train fades in / out standing on
    the rails there. The depth rule uses the district's own row and is then moved down by the district's
    offset (`span.lift`), so the Palace train sits at the same place in the draw order as it does unstitched.
- **`AmbientBoats`** - a room gets boats from its waterways, which it finds in the map data in two ways:
  - **moat tiles** (the Tokyo moat): a "run" is a line of consecutive cells holding the same plain
    `moat-<north|south|east|west>` tile; `-rocks` tiles, corner pieces and gaps end a run, so a boat never
    crosses rocks, the bridge gap in the south moat or the stone bank. The open-water strip inside the tile
    is measured from the tile image itself (`waterBand`: the longest stretch of the dominant colour across
    the middle of the tile), so no per-tile offsets are hard-coded.
  - **a room's `waterways` list** in config.json (issue #61; written by the room's generator, so any water
    tile family can be navigable): `{"axis": "h"|"v", "from", "to", "row"|"col", "rows"|"cols", "under": [[a, b], ...]}`
    in cells, inclusive - `from`..`to` along the channel, `rows` wide from `row`. The open water across it
    is measured from the tiles of one cross-section (`stackBand`: the pixel rows that are water along the
    whole tile, so a rock rim that bulges anywhere stays outside). **`under`** lists the cells where a
    bridge deck lies over the channel: the boat carries on beneath and is cropped at the deck's edge
    (`hideUnder`), invisible while wholly under it - so it passes under the bridge and under whoever is
    standing on it, with no depth juggling (the deck is ordinary Floor; the boat is never drawn on it).
    An end on the room's edge is **open**: the boat sails in from off the map and out again, as a train
    does; any other end is closed and the boat fades in / out there. On a waterway longer than the screen
    the boat sets off just out of view rather than from the far end. In a stitched city a district's
    waterways are moved to the district's place. **Osaka's Dotonbori canal** is the one declared waterway
    today (rows 20-22, the whole width of the map, `under` columns 21-28). Its deck is dressed as a
    bridge (issue #180; `tools/make_bridge_tiles.py`, Pillow): `bridge-parapet-w|e` is a stone coping on
    the outer 14px of the deck's edge cells - not solid, so the two-cell pavement keeps its width - and
    `bridge-shade-w|e` is the deck's shadow on the water cell beside it. They lie flat on
    `Non-Collidables` with `depthBias: -200` (the `asahikawa-bridge` recipe: over the Water layer and a
    passing boat, under everyone standing), and the shade is translucent, so `clearWater` does not
    count it as scenery hiding the canal. **Sendai's Matsushima bay** declares the one vertical waterway
    (issue #66: columns 66-68, from just under the rail embankment to the south edge of the map, which is
    its open end; the islets, the pier and the moored boat keep west of it). **Fukuoka's Naka river** is
    another horizontal one (issue #67: rows 40-42, `from` the first rimmed column east of the beach - a
    closed end at the river mouth - `to` the east edge, `under` columns 29-32, the same parapet and shade
    tiles as Osaka's bridge). **Toyama's sea** declares a horizontal one too (issue #68: rows 1-3, from
    the river mouth to the east edge of the map, its open end). Frozen water (Asahikawa's river,
    Yukimura's pond) declares none, so it gets no boats.
  Runs too short for a boat to travel `MIN_TRAVEL` (128px, so a run is at least four cells for either
  hull - the three-cell pockets between the moat's rocks get none) are dropped. On a closed run a boat
  fades in at one end, drifts to the other at `SPEED` with a small bob and fades out. Runs with a boat's
  length plus `MIN_TRAVEL` of water on camera (below the HUD bar) are preferred, so a boat is not spent on
  a sliver of a run at the screen's edge.
  Depth is `calculateLayerDepth(1) + 1`: above the flat ground/water layers, below everything Y-sorted.
  Because scenery standing on the near bank is drawn over the water, `clearWater()` narrows each run's band
  to the lanes that room sprites of higher depth leave in view (a lane covered for more than `COVER_LIMIT`
  of the run is hidden). **What is left decides which boats fit** (`fit()` -> `run.hulls`, issue #62):
  `AmbientBoats.HULLS` has the `punt` (116x44px) and the one-man `skiff` (80x28px), and a livery names its
  hull. Tokyo's north moat shows only a 32px lane above the `blue-wall-short` palace wall (the wall hides
  the lower half of the channel), so its three runs carry skiffs only - a boat is never drawn half behind
  the wall; the south, east and west moat take both. A tree crown overhanging one end of a run is allowed.
- **Boat art is procedural** (`AmbientBoats.buildTexture`): no boat sprite exists, so each livery
  (`AmbientBoats.LIVERIES`: `wood`, `lacquer`, `white` on the punt; `skiff`, `skiffGreen` on the skiff) is
  drawn to a canvas on the tile art's 4x pixel grid, once per facing, under the key
  `boat-<livery>-<right|left|down|up>`. `ensureTexture()` only draws a key that is not already loaded, so
  real art replaces it by loading a sprite under the same key (keep it within `AmbientBoats.size(hull)`, or
  update `HULLS`, since run fitting uses that size).
- **Testing** - both expose `cross()` to send one immediately (a no-op in a room with no track / no water):
  `game.scene.keys.GameScene.ambientTrains.cross()` / `.ambientBoats.cross(run, dir, livery)` (all optional;
  `run` is an entry of `ambientBoats.runs`, `dir` is `1` or `-1`; a livery whose hull does not fit the run
  is replaced by one that does). To make new water navigable, declare it in the room's `waterways` (above)
  from its generator; `AmbientBoats.WATER_TILE` is only for self-describing straight channel tiles like
  the moat. An ordinary pond is not a waterway.

### Streetcars: a room's `tramways` (issue #219)

`AmbientTrains` only runs station liveries on `train-track*` rows. A tram in a street is declared instead, in the
room's config, and **no room declares one yet**: with no `tramways` nothing is built, nothing runs and nothing is
drawn. A unit test (`tools/tests/glows-trams.test.js`) holds every declared row to what can run: a line
`AmbientTrams.line` accepts, inside its room, with cars that are in `spriteMetadata` (so they are loaded).

```json
"tramways": [{ "row": 21, "from": 4, "to": 55, "sprite": "sapporo-streetcar_0_0",
               "speed": 160, "headway": 30, "stops": [14, { "x": 38, "dwell": 6 }], "dwell": 4 }]
```

- **`row`** is the rail row, in the room's own cells: the car's wheels stand on it (its art is drawn up from the
  bottom of that row, like a train on its track bed, so a 5x3 streetcar covers the two rows above too).
  **`from` / `to`** are the first and last rail cell; left out, they are the row's `tram-rail-h` / `tram-rail-cross`
  tiles (`AmbientTrams.RAIL`), so painting the rails is enough. Only a horizontal line exists: the car is side-on art.
- **`sprite`** is a loaded sprite key (it must be in `spriteMetadata` to be loaded; a line whose art is missing
  waits and tries again), or a list of keys taken in turn, one per trip. `speed` is px a second (default 160, 2.5
  cells), `headway` the seconds between one car finishing and the next setting off (30), `stops` the cells it
  stops at - the car's middle over the middle of the cell - each for `dwell` seconds (4) or its own.
- **One car is on a line at a time.** It runs west to east, waits `headway`, and the next runs east to west,
  mirrored (`flipX`; the art heads east). An end on the room's edge is open - the car comes in from off the map
  and leaves the same way; any other end is a terminus, where it fades in / out standing on the last of the rails
  (as the Palace train does at the end of its track). It pulls away from and draws up to a stop or a terminus.
- **It is decoration, like a passing train**: it adds nothing to collision, never waits for anyone, and the player
  can stand in it. Its depth is `(row + 1) * 10 + 4` (`AmbientTrams.depthAt`) - with whatever stands on the rail
  row and one under a character there, so a player on the rails is drawn over the car as it passes through them,
  and one on the row behind is hidden by it. That is the passing train's level-crossing rule without its cap of
  48: a tram is in the street and sorts like anything else on it. Being in the world, it is under the day/night
  grade and darkens at night with the street; it carries no light of its own.
- **The timetable is a pure function of time**: `AmbientTrams.line(def, layers, offset, cols)` normalises a
  declaration (and moves it to its district's place in a stitched city), `AmbientTrams.plan(line, opts)` lays out
  one trip as legs, `AmbientTrams.at(plan, ms)` says where the car is. `GameScene.update` advances it; the car is
  hidden whenever the camera cannot see it, so off screen only that arithmetic runs, and it still arrives on time.
- **Testing**: `game.scene.keys.GameScene.ambientTrams.cross(index, dir)` sends a car now (`dir` 1 east, -1 west).
  Unit tests: `tools/tests/glows-trams.test.js`.
- **Could it run San Franbourne's cable car and tram?** Yes, as one line: `{ "row": <the rail row of the tram
  street>, "from", "to", "sprite": ["sfb-cable-car_0_0", "sfb-tram_0_0"] }` - explicit cells, because those rails
  are part of the street's own tiles, and a terminus at each end, because the street is closed at both. They must
  be ONE line taking turns: two lines on one row know nothing of each other and would drive through one another.
  It is not wired: today both are standing `Collidables` with solid cells, and running them means the map taking
  them (and their colliders) off the street.

