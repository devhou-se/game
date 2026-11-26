# The stitched city (TokyoCity)

How the five Tokyo districts are merged into one runtime room, and what every system and tool has to know about it.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Stitched cities: one continuous Tokyo (issues #40 / #41)

Tokyo, Market, Palace, Park and Machi (room KEYS: the player reads their display names, "Imperial Palace",
"Asakusa", "Marunouchi", "Park", issue #219 — see `name` in `maps-and-rooms.md`) are still five Tiled maps and five room keys in `config.json` — but at
load they are merged into ONE runtime room, `TokyoCity`, so you walk between them with no fade, no input
block and no reload, and the next district is on screen before you reach it. Inaka, Yukimura, Osaka, Sapporo and
Asahikawa were always single maps; interiors and trains keep their fade.

- **Data** — config `cities`: `{"TokyoCity": {"name", "rooms": [{"room", "x", "y"}...], "drop", "patch", "backdrop"}}`.
  `rooms` lists the districts with their world-cell offsets, copied from `../devhouse.world` (not deployed)
  by **`python3 tools/sync_cities.py`** (`--check` exits 1 on any disagreement; `tools/make_worldmap.py`
  runs the check first, even when the map art is `custom`, and at boot `CityStitcher.plan` re-checks the offsets against `assets/map/world-map.json`
  — a city that fails is reported with `console.error` and its districts stay separate rooms). The list
  ORDER matters: a later room owns the cells it overlaps with an earlier one (Tokyo/Market share a column,
  Market/Palace a row, Palace/Park four rows), and the loser's tiles and colliders there are left out.
  `drop` removes art a neighbour already draws (Park's `tokyo-tower-feet` copy of the Palace tower's base).
  `patch` = `{district: {layer name: {"x,y": tile | null}}}` (district cells) touches up single tiles in
  the stitched room only, without editing the map: Park's top-left road corner becomes the straight road
  Palace's west road now carries through it. Anything that changes where you can STAND belongs in the
  district's own map instead (the two grass cells beside Machi's east gate, which only the seam teleport
  used to keep you off, have their collider in `machi.tmj`): `findWalkableNear`, `?stitch=0`,
  `tools/play.js` and `tools/blog_to_npc.py` read the district data and never see a patch.
- **Merge** — `src/systems/CityStitcher.js` (`build`): layers, objects, signage and door transporters are
  translated into merged cells (the union's top-left is 0,0 — Machi is at 0,22, Tokyo at 48,1, Market at
  106,0); the 22 hidden seam transporters (target = a sibling district) are dropped; `RoomManager.rooms`
  gets the city next to its districts, which stay as data and are never entered. **`config.rooms` is not
  touched** — it still has exactly the authored rooms, so `tools/blog_to_npc.py`, the world map, the
  generators and the seam transporters themselves are unchanged.
- **Coordinates** — everything authored stays district-local. `roomManager.resolve(room, x, y)` maps a
  legacy `('Market', x, y)` to the city room (used by `applyRoomSwap`, so konbini exits, the station exit,
  train arrivals and map travel land correctly with no data edits; by `syncNpcPresence` for NPC homes and
  dated-state positions; by the player start). The inverse is `roomManager.localize(x, y)` /
  `districtsAt(x, y)` and **`roomManager.currentDistrict()`** — use that, not `currentRoom`, for anything
  per district: the HUD name (updates as you cross), `AchievementManager` (painted and counted per district
  in district cells, so old saves stay valid; a shared cell counts once, for its owner), the map's "You"
  marker and NPC dots (`roomManager.npcsIn(room)`), debug flags. `npc.homeRoom` is an NPC's district and its
  wander box is clamped to it. Code that scans `rooms[currentRoom].layers` (shop, fishing, glows, ambient
  traffic, clocks) just works: the city's layers are the merged ones.
- **The woods** — the union is L-shaped and the camera is clamped to its bounding box, so every cell no
  district covers is filled by `CityStitcher.buildBackdrop` from config `backdrop`: grass, unevenly spaced
  trees, shrubs, the missing kerb of the road down Palace's west side (`edges`), and the Palace railway
  carried on west through a cutting (`extend`; it stops `extendStop` cells short of Machi so the wood
  closes over its end). It is scenery: `RoomManager.checkBoundary` only admits
  district cells. Backdrop layers are named `Backdrop ...`, never `Floor`.
- **Depth** — Y-sorted depth is 10 per row, and 109 rows would climb past the name labels (900) and the HUD
  (1000), so a city has a `depthScale` (0.77). Anything Y-sorted must go through **`roomManager.yDepth()`**
  (tiles, signage, characters and the ambient train do).
- **Performance** — `RoomManager.loadFloorTiles` indexes every tile as a record (`tileRecords`: cell, key,
  depth, pixel bounds) and collision as a set (`blockedCells`; `CollisionSystem` does one lookup per cell
  instead of scanning every sprite). In EVERY room (stitched or not) a collision layer's `gk_blank` markers
  feed that set only: they are not records and never get a sprite (issue #148 — it was 2,440 records in the
  city, 858 sprites in the old Tokyo room, 37 in a konbini); the debug overlay and inspector read colliders
  from the set. Anything else painted on a collision layer still blocks and is drawn. A city (~23k tiles
  with the woods) is **streamed**: records are bucketed in 4-cell chunks (`buildChunks` — every room is
  bucketed, `Occlusion` looks art up by place through `artNear`) and only those within 3 cells of the view
  — and of the point the camera follows, which is above the player while it looks up at a landmark
  (`LandmarkView`, see Small Viewports and Touch) —
  have a sprite (`updateStreaming`, every frame; retired sprites are pooled OFF the display list), about
  1,000 at a time versus ~3,500 for the old Tokyo room. `floorSprites` is therefore "the sprites that exist
  now" — read `tileRecords` / `standingArt()` when you need the whole room (AmbientBoats does). Night lamp
  halos are culled the same way (`DayNight.cullGlows`).
- **The city's index is kept** (issue #175) — a streamed city's records, `blockedCells` and chunks are the
  same on every visit, so `loadFloorTiles` builds them on the first entry and keeps them in
  `roomManager.tileIndexes`; leaving a konbini or a station afterwards only spawns the sprites of the chunks
  in view (the swap went from 18 ms to 8 ms, 73 ms to 32 ms on a 4x-throttled CPU). `clearFloorTiles` hands
  kept records back with no sprite and no Occlusion fade. Only a stitched, streamed room is kept
  (`RoomManager.keepsIndex`): with `?cull=0` or `?stitch=0`, and in every other room, each entry rebuilds as
  before. A kept index is used only while the room object, its layer list and each layer's tile table are
  the same objects (`RoomManager.indexFits`) — stitching again or giving a room new layers / a new tile
  table rebuilds it; code that changes a tile of a live room IN PLACE must call
  `roomManager.forgetTileIndex(roomKey)` (nothing in the game does; the studio and editor never run
  `loadFloorTiles`).
- **Bumps are a lookup** (issue #145) — what a blocked step opens (shop / pond / clock) comes from
  **`roomManager.interactionAt(x, y, group)`**: the room's interactive cells are indexed once, on the first
  bump after a room load (`Interactions.index`: cell -> interactions, footprints expanded; thrown away by
  `clearFloorTiles`), so a bump costs the same in a konbini and in the city (0.002 ms; the scan it replaced
  was 7.5 ms, 30 ms on a 4x-throttled CPU). A held key against a wall therefore asks every frame again in
  every room — the 150 ms throttle the stitch added is gone. `Shop`, `Fishing` and the clock check all go
  through it; do not call `Interactions.find` (a full scan) from per-frame code.
- **Systems that re-read the room** — `TrafficLights` rebuilds its signal list whenever `floorSprites` is
  replaced (every chunk change), so signals streamed in are put on the current phase before they scroll into
  view and its night glow follows them; `UIScale`'s overlay camera re-filters the display list every frame it
  is up, which covers sprites coming back from the pool; `Intro.whereFriendsAre` reads the cast from config per district (`Trips.membersByRoom`) and names
  "here" with `roomManager.currentDistrict()` (a district's own `rooms[...].npcs` is empty once it is
  stitched — ask `roomManager.npcsIn(room)` for live NPCs).
- **Tools** (issue #144) — `tools/world-model.js` (shared by `tools/play.js` and `/studio/`) loads
  `src/systems/CityStitcher.js` and calls `RoomManager.stitchCities` — the same two functions the game's
  `setupCities` runs — so the tools hold the room the game plays, not a second implementation of it.
  `play.js` walks the city continuously (`goto Market 5 24` from Tokyo; a step that changes district says
  `walked from Tokyo into Market`), always speaks DISTRICT coordinates (`where` = `Market 5,24 (TokyoCity
  111,24)`; `look` rules its map in the district's cells, so a neighbour's cells are negative or past the
  edge; sessions are saved as district + cell), `check` surveys the stitched world AND then the separate
  rooms (problems only the fallback has are tagged `[--stitch=0]`, so the seam transporters stay guarded),
  `lint` with no room lints every district and then `TokyoCity` (floor holes anywhere in the bounding box,
  colliders lost to an overlap, a `patch` gone wrong; `Backdrop ...` layers are scenery and are not linted
  as objects), `lint <District>` is unchanged, `render TokyoCity out.png` draws the city with its woods,
  and `reach` prints the walkable cells of every room as JSON. `--stitch=0` (play.js) / `?stitch=0`
  (studio) give the five rooms joined by the 22 seam transporters, i.e. what the game's `?stitch=0` plays.
  `tools/blog_to_npc.py` has no node at hand, so it carries a ten-line port of "who sits where, later room
  owns the overlap" (`city_districts` / `city_reachable`); `tools/test_blog_to_npc.py` pins it to
  `play.js reach` for every cell of every room.
- **The west gate** (issue #147): where Machi's dirt path meets Tokyo (Tokyo cells `(0..1, 41..42)`, Machi
  `(47, 20..21)`) the lane is a two-cell brick apron between the lantern pair, Machi's path runs out through
  the gate instead of ending in a rounded cap, and Tokyo's road corner beside it is a square junction box
  (kerb down column 2, `road-corner-sw` at `(2,43)`, `road-plain` inside). It is district data in both
  maps, so `?stitch=0` shows the same gate. The lower lantern stands on `(1,44)`: a lantern is two cells
  tall and one cell further north its head hung over the lane.
- **Road junctions are plain boxes** (issue #179): the port drew every three-cell road straight through
  each junction, so a joining road's mouth was closed by the other road's kerb and its centre line ran
  on into the junction. **`python3 tools/square_junctions.py`** lays each of the twelve 3x3 boxes in
  Tokyo, Market and Park the way #147 laid the west gate: `road-plain` throughout, the kerb along a
  CLOSED side (the far side of a T, the outside of a bend), a mitred `road-corner-*` where two closed
  sides meet. `JUNCTIONS` lists them per district (top-left cell + closed sides); a box may hang over
  the map edge - the Tokyo/Market road is half in each map - and the neighbour's entry lays the rest.
  Sides are as the district reads on its own (`?stitch=0`): Park's top row is a kerb there, and
  `cities.TokyoCity.patch` opens it (`Park` cells `0,0 1,0 54,0 55,0 56,0`) where Palace's roads run
  in. Park's west road is half in the woods, so `cities.TokyoCity.backdrop.edges` gives it its kerb
  beside `road-plain` as well and a `road-corner-sw` beside the bottom kerb. Idempotent; a new junction
  is one more entry (then `config_to_tiled.py` for the districts and `make_worldmap.py`).
  `ARMS` in the same tool lays a stretch of an east-west road the port paved over as road (issue #194:
  two cells of brick across the avenue either side of the Tokyo/Market crossroads).
- **`?stitch=0`** is the safety valve: no cities, the five districts are separate rooms joined by the fade
  transporters exactly as before. `?cull=0` keeps stitching but creates every sprite (for measuring).
- **The second city** (issue #68): `HokurikuCity` stitches Kanazawa, Shirakawa-go and Toyama (see
  "Hokuriku" in `landmarks-and-towns.md`). Nothing in the stitcher, `RoomManager`, the tools or the blog
  pipeline is Tokyo-specific - every one of them loops over config `cities` - so the second city needed no
  code change; `tools/tests/kanazawa.test.js` walks it stitched and with `--stitch=0`. A city's key sorts
  into config order (`HokurikuCity` before `TokyoCity`): do not read "the city" as the first entry.
- **Adding a district / a second city**: place the map in `devhouse.world` so the shared road lines up,
  add it to `cities.<City>.rooms`, run `tools/sync_cities.py` and `tools/make_worldmap.py`. Keep the hidden
  seam transporters in the maps — `?stitch=0` (and `play.js --stitch=0`, which `play.js check` runs too) still use them.
