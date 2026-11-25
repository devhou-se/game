# Ambient traffic: passing trains and boats

The decorative trains and moat / canal boats (`src/AmbientTrains.js`, `src/AmbientBoats.js`) and the `waterways` data.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Ambient Traffic (issue #29)

Purely decorative movers that make a room feel alive. Both are built in `GameScene.create()`, re-armed by
`RoomManager.switchRoom()` through `onRoomChange(roomKey)` (which also destroys whatever is on screen), find
their route in the room's map data rather than in coordinates, have no collision, and send the first one
3-10s after you enter a room and another every 15-40s after it finishes.

- **`AmbientTrains`** - any room with `train-track*` tiles that is not a `stations` room (Palace, Inaka,
  Yukimura, Osaka, Sapporo, Asahikawa) gets a train running the topmost track row, off-screen edge to
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
    count it as scenery hiding the canal. Frozen water (Asahikawa's river,
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
