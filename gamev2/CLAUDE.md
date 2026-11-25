# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a browser-based 2D grid game built with Phaser 4.2.0. It features grid-based movement, a room/teleportation system, and Python-generated sprite tiles.

## Technology Stack

- **Engine**: Phaser 4.2.0 (loaded via CDN — jsdelivr, since cdnjs does not yet host 4.x)
- **Languages**: JavaScript (ES6+ classes)
- **Asset Generation**: Python 3 with PIL/Pillow
- **No Build Process**: Direct HTML file execution

## Running the Game

**Option 1: Direct file access**
Open `index.html` directly in a web browser. No build step required.

**Option 2: Local server (recommended)**
```bash
python3 -m http.server 8000
```
Then navigate to `http://localhost:8000` in your browser.

**Option 3: No browser (for agents)**
`node tools/play.js <command>` plays the game as text: it loads the real map, collision and NPC-date
code from `src/` into Node, with no Phaser and no dependencies. Walk, talk to NPCs, follow teleports,
ride trains, time travel, inspect cells, `lint` a room's map, `render` it to a PNG, and run `check` to
confirm the world is still playable after a map change. `node tools/play.js help` lists the commands; the `play-game` skill
(`.claude/skills/play-game/SKILL.md`) is the full guide, including what the tool cannot do.
It plays the world the game plays: the Tokyo districts are stitched into one room by the game's own
`CityStitcher` (see "Stitched cities" below), so `goto Market 5 24` from Tokyo is one walk with no teleport,
`where` reads `Market 5,24 (TokyoCity 111,24)`, and every coordinate you type or read is still the
district's own. `--stitch=0` anywhere on the command line models what `?stitch=0` plays instead.

`node tools/test_game.js` runs the game's own decision code in Node, with no browser: which train a
station parks, the departures board's order and scrolling, room display names, the dialogue hint wording,
touch buttons cancelling their touch, which post a dialogue line is captioned with, the default game date,
trips (which NPCs exist on a date, where a player starts, what the intro says, Time Travel's trip jump).
When a fix lives in a Phaser-side class, pull the decision into a static function there and add a case.

`python3 tools/check_generators.py [generator ...]` checks that the room generators still rebuild the
committed world: it runs each one in a scratch copy and fails, naming the rooms and cells, if `config.json`
would change (issue #107, see "Generated rooms stay regenerable"). It also re-seeds every room with
`config_to_tiled.py` and fails if a committed `tiled/*.tmj` would change (a config edit whose map was not
re-seeded), and runs the art / prefab tools (`make_prefabs`, `generate_hokkaido`, `_tsutenkaku`,
`_discount_art`, `_cooler_art`, `make_snow_tiles`, `make_road_tiles`, the `extract_*.py` scripts) and fails
if `assets/sprites`, `tiled/prefabs` or `config.json` would change (issue #186). Run it after any edit to a
generated room, a map or a generator. The room and map checks take a few seconds and need no Pillow; the
art tools are listed as `skip` without it, so use `/Library/Developer/CommandLineTools/usr/bin/python3
tools/check_generators.py` to cover them (ten seconds; `extract_city` also needs a Japanese system font,
see `generate_ads.find_font`, and reports `FAIL ... did not finish` where none is readable).

## Studio

`studio/` is a read-only view of the whole world for developers, served at `/studio/` (locally
`http://localhost:8000/studio/`, live at `game.devhou.se/studio/`). It lays every room out together and
overlays collision, unreachable cells, teleports (arrows to their targets), train links, interactions and
where each person stands on a chosen day. Click a cell for its tiles, what a bump does, the NPC's lines
and photo, and the `play.js` command that puts you there. Maps are still edited in Tiled.
Tokyo is drawn as the one stitched city the game plays (woodland included, the five districts outlined and
named inside it; the inspector gives the district's own cell and the city cell, the owning district where two
overlap); the **Stitched** button, or `/studio/?stitch=0`, shows the five rooms joined by seam teleports instead.
In that five-room view, where a city's districts overlap on the map (Palace / Park share four rows) the later
district in the city's `rooms` list is drawn on top and takes the click, as in the stitched city
(`WorldModel.stackOrder`). Click the selected cell again for the room underneath (`WorldModel.stackPick`):
that is how the covered seam transporters (Palace 38..39,21, Market 54..56,47) are inspected - and, in the
stitched view, the city's woodland under a town that sits inside its box (none does since issue #174).

It has no logic of its own: `tools/world-model.js` (rooms, collision, NPC dates, interactions, the
problem survey) is shared with `tools/play.js`, so the page and the terminal tool always agree.

## Architecture

### File Structure

- `index.html` - Entry point, loads Phaser CDN and game scripts from `src/`
- `config.json` - JSON configuration file defining game constants, rooms, NPCs, and objects
- `tiled/*.tmj` - Room maps, authored in the Tiled editor (the map source of truth at
  runtime — see `tiled/README.md`; config.json's room layers are only a fallback)
- `src/game.js` - Phaser game configuration (viewport: 1280×960, physics setup)
- `src/systems/Viewport.js` - Where the canvas sits in the window, and where the touch controls go (see Small Viewports and Touch)
- `src/systems/UIScale.js` - World zoom, HUD magnification and overlay fitting for small, cropped or touch-covered canvases (see Small Viewports and Touch)
- `src/utils/Hints.js` - The one helper that words key hints for keyboard or touch (see Small Viewports and Touch)
- `src/utils/JapaneseFont.js` + `fonts/` - The pixel fonts, and the Japanese face added to each of them (see Fonts and Japanese Text)
- `src/utils/Trips.js` - The devhouse trips as data: which trip a date belongs to, and everything that follows (see Trips)
- `src/GameScene.js` - Main game scene (room system, HUD, input handling, collision)
- `src/Character.js` - Character movement class with grid-based tweening
- `src/DialogueManager.js` - NPC dialogue system with multi-line conversations
- `src/systems/Occlusion.js` - Scenery fades while someone stands hidden behind it, and their name label
  with it (see "Walking behind things" below)
- `src/utils/Interactions.js` - The one table of what a bump opens (shops, ponds, clocks, the drinking
  table). `Shop`, `Fishing`, `DrinkingGame`, `GameScene` and `tools/play.js` all read it; add a rule here
  rather than a tile-name check in a feature file
- `src/MenuManager.js` - In-game menu system (ESC key toggle)
- `src/DatePicker.js` - Time Travel calendar (menu, or the HUD date). Marks three different days: today (gold), the day the
  game is on (blue — a trip day, usually a year of months from today) and the cursor (green box). The legend names only
  colours that are on the month shown; the jump row under the selected date moves the cursor to today / the game's day (click, tap, or SHIFT + up / down), and the trips row above it to a trip
- `src/TitleScreen.js` - Title / splash screen shown at boot (cast line-up, press SPACE / tap to start)
- `src/Intro.js` - New-player intro (who devhouse is, controls as keycaps, where to start); replayable from the menu as How to Play
- `assets/portraits/` - Optional hand-drawn character portraits (`manifest.json` + `<name>.png`, see its README)
- `src/Voice.js` - Spoken NPC dialogue (lazy per-line audio clips) and the shared mute setting
- `src/AmbientTrains.js` / `src/AmbientBoats.js` - Decorative passing trains and moat boats (see Ambient Traffic)
- `src/TrafficLights.js` - Decorative traffic-signal cycle (see Street accessories)
- `editor/` - Canvas editor for `config.json` room data (see `editor/README.md`)
- `studio/` - Read-only view of the whole world (see Studio above)

### Visual Editor

`/editor/` edits one room of `config.json` at a time: inspect a cell, paint collision, place and edit
transporters, set the spawn, resize the room. It saves by downloading a new `config.json`. The game loads
rooms from `tiled/*.tmj`, so run `python3 tools/config_to_tiled.py <Room> [<Room> ...]` after replacing the
file (any number of rooms; an unknown name is an error and nothing is written).

### Core Constants (config.json)

All game constants are loaded from `config.json` and applied in GameScene.create():
- `gridSize`: 64 pixels per cell
- `worldWidth`: 960 pixels (15 grid cells wide)
- `worldHeight`: 640 pixels (10 grid cells tall)
- `deadzoneCells`: 4 (creates effective 5×5 cell camera deadzone)
- `moveDuration`: 200ms per cell movement
- `npcWanderInterval`: 5000ms between NPC wander attempts
- `npcWanderRadius`: 2 cells from NPC spawn point (a wandering NPC never steps onto a transporter or the cell beside one — `NPCManager.atDoorway` — so nobody blocks the cell in front of a door)

### Grid-Based Movement System

Characters move in discrete grid cells using Phaser tweens. Movement is collision-checked before execution. The system supports:
- Diagonal movement with path collision detection
- Speed multipliers (e.g., Shift key doubles speed by halving duration)
- Movement queuing during active tweens

Player movement bounds are calculated based on camera deadzone to prevent camera leaving world bounds.

### Room System

Rooms are defined in `config.json` and loaded into `GameScene.rooms`. Each room has:
- `name`: Display name
- `boundary`: Array of [x, y] points defining a polygon boundary (optional, defaults to rectangular world bounds)
- `npcs`: Array of NPC definitions with position (absolute or offset from center), sprite, name, and dialogue.
  An NPC may also carry dated state updates under `states` (`{"YYYY-MM-DD": {fields}}`): at load, every
  state dated on-or-before the game date is applied over the base definition in chronological order —
  so viewing July 27 shows the July 26 update if the next one is July 28. The game date is
  `?date=YYYY-MM-DD` when given, else the default below; a state of `{"present": false}` removes the NPC
  from that date. Author states with `python3 tools/npc_state.py <Room> <Npc> <date> --dialogue ... --pos X,Y`
  (see `src/utils/NpcStates.js`)
  - **Trips scope it** (see Trips below): only states dated inside the game date's trip — and its
    current stay — are applied, and a base NPC marked `"trip"` / `"stay"` exists only on those dates.
  - **Default game date** (`defaultGameDate()`, issues #54, #118): while today is inside a trip
    (`config.trips` start to end) the game date is today, post or no post. Otherwise today is mapped
    onto a content day of the most recent trip that has posts: days since the day after that trip's
    last post, modulo its number of content days, indexes its sorted list (the day after the last is
    the first again) — so a visitor with no `?date=` always opens on a day that has posts, the next
    real day shows the next one, and two trips are never read as one long span. The content days
    (`contentChangeDates`) and the trips are handed over by `setTripDates(config)` at the top of
    `GameScene.create()`; nothing is hard-coded. The default is fixed when the config loads
    (`bootToday`), so a session left open past midnight keeps the day its NPCs were resolved for.
    The HUD shows that date, led by the trip's name on a trip day (`devhouse 3 · February 20 2027`,
    `Trips.dateLabel`) — when the line still ends two `HUD_PADDING`s short of the `menu` button with
    it: `GameScene.layoutHUD()` measures title | room | date | wallet with the HUD's own text objects and
    drops the name where it does not fit (the konbini, the Don Takotes,
    Asahikawa Station: long room names), so the wallet is never pushed under the button. On a small
    screen the same routine goes on to drop the game's title and then to wrap the date and wallet to a
    second row, where the trip's name comes back if the row has room (see Small Viewports and Touch). Anything
    that lengthens the HUD line must keep going through that check. `?date=` and Time Travel always win; `setGameDate()` drops the param
    only for the date a clean URL already gives, so picking today's real date between trips is an
    explicit `?date=` like any other. `tools/play.js` and the studio open on the same day
    (`WorldModel.defaultDate()` calls `defaultGameDate`).
- `objects`: Array of static obstacles with position (absolute or offset from center) that block movement
- `transporters`: Array of teleport points with position, targetRoom, and target position

Position system supports both absolute grid coordinates (`gridX`/`gridY`) or center-relative offsets (`gridOffsetX`/`gridOffsetY`).

Room transitions use camera fade effects (250ms fade out, 250ms hold, 250ms fade in; on the last camera drawn, see Small Viewports and Touch) and block input during transition via `isTransitioning` flag.
Walking between the districts of a stitched city (below) is NOT a room transition.

### Stitched cities: one continuous Tokyo (issues #40 / #41)

Tokyo, Market, Palace, Park and Machi are still five Tiled maps and five room keys in `config.json` — but at
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
  have a sprite (`updateStreaming`, every frame; retired sprites are pooled OFF the display list), about
  1,000 at a time versus ~3,500 for the old Tokyo room. `floorSprites` is therefore "the sprites that exist
  now" — read `tileRecords` / `standingArt()` when you need the whole room (AmbientBoats does). Night lamp
  halos are culled the same way (`DayNight.cullGlows`).
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
- **`?stitch=0`** is the safety valve: no cities, the five districts are separate rooms joined by the fade
  transporters exactly as before. `?cull=0` keeps stitching but creates every sprite (for measuring).
- **Adding a district / a second city**: place the map in `devhouse.world` so the shared road lines up,
  add it to `cities.<City>.rooms`, run `tools/sync_cities.py` and `tools/make_worldmap.py`. Keep the hidden
  seam transporters in the maps — `?stitch=0` (and `play.js --stitch=0`, which `play.js check` runs too) still use them.

### Walking behind things (issues #76 / #93)

Standing art is Y-sorted, so a character north of a roof, a tower, a torii top, a high-rise or a tree crown is
drawn under it. `src/systems/Occlusion.js` keeps them in view with one rule for every room, day or night:

- A character is **hidden** when art drawn over them (higher depth) covers more than half of their body
  with opaque pixels (12 sample points; coverage is read from a quarter-size alpha mask per texture, built
  the first time that texture is in the way — so the opening of a torii, the gap between Tokyo Tower's legs
  and the empty corners of a tree crown do not count).
- The pieces doing the covering **fade to 40%** (`Occlusion.ALPHA`, over `FADE_MS` = 160 ms) and come back
  when the character steps out. A building that is one sprite fades whole (Tokyo Tower, the Dotonbori arch
  and wheel, high-rises, house roofs), and so does a roof LAID FROM TILES (issue #172: Market's hall and
  its gate; it used to open a pale window of one to three tiles): a hit on a roof-part record
  (`Occlusion.ROOF_PARTS` - the families roofs are laid from - on an overhead layer) brings every part
  that touches it, directly or through other parts (`Occlusion.roof(rec)`: an edge in common, a corner
  alone is not enough), so the hall, the gate and each wing are one roof each. A roof is worked out the
  first time one of its tiles hides somebody, by walking outward through the chunk buckets, and kept on
  the records (`rec.roof`), which last as long as the room: no room scan at load or per frame (0.5 ms for
  the hall's 68 tiles, once). Tree crowns never group; add a family to `ROOF_PARTS` when a new roof is
  laid from tiles. Wall signs
  (`roomManager.signArt`) fade the same way.
- The character's **name label fades with them** (to `LABEL_ALPHA` = 60%, as much as the character shows
  through art at 40%) instead of floating over the roof at full strength. A label whose character stops being
  tested (an NPC that walks off camera) snaps back to full. Labels stay at depth 900 — they are never hidden by a tree in front of them — the fade
  is what says "behind". The player's own label (created characters only) and NPC labels follow the same rule.
- It applies to the player and to every NPC on camera, so a friend who wanders behind a roof is still
  findable. It is cheap: characters are only re-tested when they move, and only against the art of the
  4-cell chunks they stand in (`RoomManager.artNear`, the buckets tile streaming uses — built for every
  room) plus the room's wall signs; nothing scans the room per frame.
- The fade is stored on the tile RECORD (`rec.fade`), not the sprite, so a streamed sprite that is retired
  and re-made keeps it (`RoomManager.spawnTile` applies it). Code that sets a tile sprite's alpha for its
  own reasons would fight it — none does today.
- `GameScene.update` calls `occlusion.update()` right after `updateCharacterDepths()`. For a before/after
  look in the console: `game.scene.keys.GameScene.occlusion.enabled = false`.
- Layering consequences for maps: a walk-behind strip no longer hides anyone, so "the player vanishes
  behind X" is not a reason to add colliders any more (colliders are for where you cannot stand).

### Trips (issues #118, #131, #130, #96, #59)

The trips are data — `config.json` top-level `trips`, read through `src/utils/Trips.js` (pure functions
of the config and a date; `tools/play.js`, the studio and `tools/test_game.js` run the same code):

```json
"trips": [
  { "id": "devhouse2", "name": "devhouse 2", "where": "Japan", "start": "2025-10-02", "end": "2025-11-18",
    "members": ["bailey", "damian", "dylan", "julia"], "home": { "room": "Tokyo", "x": 29, "y": 38 } },
  { "id": "devhouse3", "name": "devhouse 3", "where": "Hokkaido", "start": "2027-02-18", "end": "2027-02-28",
    "members": ["bailey", "damian", "dylan", "julia", "khoi", "sam", "xander"],
    "home": { "room": "Sapporo", "x": 33, "y": 12 },
    "stays": [ { "from": "2027-02-18", "room": "Sapporo", "x": 33, "y": 12 },
               { "from": "2027-02-25", "room": "Asahikawa", "x": 31, "y": 12 } ],
    "utcOffset": 9 }
]
```

`members` are sprite base names (James is the default player sprite, never a member; `credits` is a
separate list and is not read for any of this). `stays` is optional: where the group is based from each
date. Give every stay its `x`, `y`: one without a cell is ignored as a start (the player lands at the
trip's `home`, possibly a room away from the cast) and `play.js check` reports it. devhouse 2's dates are the span of its blog posts.
`utcOffset` (hours ahead of UTC where the group is; optional) is read by the blog pipeline only: a trip
that has it dates its posts by the clock there (`blog_to_npc.post_date`, see The blog rehearsal below).
devhouse 2 has none on purpose — its history was written with UTC dates, and an offset would re-date a re-run post.

**The trip a game date belongs to** (`Trips.forDate`) is the latest one that has OPENED by then — the
days after a trip still belong to it — or the first trip for a date before them all. A trip opens
`"lead"` days before its `start` (default `Trips.LEAD`, 14; `trip.opens`): a post from the travel days on
the way there is that trip's content day, not the previous trip's (it would otherwise join the previous
trip's cycle and shift the between-trips default date). On those lead-in days (`windowFor(...).early`)
the previous trip is history and the new trip's base NPCs are not standing anywhere yet — only people
who have posted since it opened are placed — and from the trip's first day the lead-in posts are history
too and everyone is at the base. A lead-in day is not a trip day (`Trips.during`): no
picker underline, and the default date only lands there once it has a post. Once the trip is over the
default date cycles over the trip's own days only (`Trips.defaultDate`), so a post from the road is never
the day a later visitor opens on (unless it is all the trip has). `blog_to_npc.py`
(`trip_window`, `TRIP_LEAD`) mirrors the rule.

**The lead-in says so** (issue #164, `Trips.leadIn(trips, date)` → `{ trip, days, stay }` or null): nobody
has arrived, and an empty base with no explanation read as a bug. On a lead-in day
- the HUD counts down — `devhouse 3 in 8 days · February 10 2027`, shortened to `in 8d`, then `soon`, then
  the bare date as the line runs out of room (`Trips.dateLabel`; in Sapporo with the starting ¥5,000 it is
  `in 8d`) — for new and returning players alike;
- the intro's page 1 reads "devhouse 3, their trip to Hokkaido, starts on February 18. This is the little
  world they will be walking around." (`Intro.tripCopy(..., starts)`), and page 3 "They have not arrived
  yet: devhouse 3 starts here in Sapporo on February 18. Have a look around before they get here."
  (`Trips.arrivalText` → `Trips.whereText(groups, here, arrival)` → `Intro.meetCopy`). When somebody has
  posted from the road it is "Today Bailey is here in Palace. devhouse 3 starts in Sapporo on February 18.
  Walk into Bailey to say hello." (one person is walked into by name; "Go and find one to say hello." when
  nobody is placed on an ordinary day);
- the player starts at the trip's first base (the first stay's cell, Sapporo 33,12) — where they will
  arrive — unless somebody has posted, in which case beside them, like any other day (`Trips.startFor`).
A real visitor on those days is still shown a day of the trip before (the default game date); page 1
then ends "… devhouse 3 starts on February 18." (`Trips.upcoming(trips, today)`), and stops saying so the
day the trip starts. Days before the FIRST trip are not a lead-in (they show its base cast). The trip decides:

- **Who exists** (`Trips.windowFor` → `resolveNpc(npc, date, trips)`). A base NPC marked `"trip": "<id>"`
  is there only on that trip's dates, and with `"stay": "<room>"` only while the group is based in that
  room; otherwise it resolves as if its base said `present: false`. Dated states are applied only from
  the window's first day (the start of the stay, else of the trip) — earlier ones are another trip's
  history — and a state inside the window still places anybody anywhere. So: devhouse 2's base cast
  (Bailey, Damian, Julia in Tokyo; Dylan in Machi) carries `"trip": "devhouse2"`; devhouse 3 has a base
  NPC for all seven in Sapporo (`"stay": "Sapporo"`) and in Asahikawa (`"stay": "Asahikawa"`) with two
  neutral lines each, so on 18-24 Feb 2027 everyone stands in Sapporo and from the 25th in Asahikawa
  before anyone has posted; Khoi, Sam and Xander are nowhere on a 2025 date. A member's first post of a
  trip moves them as usual (`blog_to_npc.py` needs no trip knowledge: it writes a dated state where they
  are and `present: false` everywhere else, both inside the window), and when the group moves base
  everyone is at the new base until they post from it. NPCs with no `trip` (the izakaya opponents,
  Yukimura's villager, the pipeline's hidden per-room defs) are unscoped apart from the state window.
  Resolution of every NPC on every devhouse 2 day was compared before and after the change: identical,
  apart from the three new members being absent.
- **The default game date** — see Default game date above.
- **Where the player starts** (`Trips.startFor(config, date, { played })` → `{ room, x, y }`,
  the same terms a door target is written in — a DISTRICT cell (`Tokyo 29,38`, `Machi 22,10`), never a
  stitched-city one: `GameScene.startPosition()` is the one caller and puts the player there through
  `roomManager.resolve`, so the start is the same cell with `?stitch=0`; "the room" below is the district.
  EVERY player — new (#96, #59) or returning, after a reload or a Time Travel hop (#166) — starts where
  there is someone to talk to: the room with the most members that day, never counting the
  member they are playing as; a tie goes to the room fewest doors / train rides from home
  (`Trips.hopsFrom`), then config order. In the home room they stand on the home cell when somebody is
  within `Trips.NEAR` (6) cells; otherwise on the cell nearest the group, at least two cells from
  everyone, that can be walked to from the room's arrivals (`Trips.standNear`: Floor tile, no collider,
  inside the boundary, not a door). On every devhouse 2 post day, as any character, that is within 6
  cells of someone (unit-tested). "Home" (`Trips.homeFor`) is the trip's own cell for the date — the
  stay's cell (the first stay's on a lead-in day), else `home`, else `config.player.startRoom/X/Y` — and
  is where a player lands when nobody is anywhere (a lead-in day with no posts) or no cell can be found.
  Why not the trip home for returning players, as it was until #166: there is no saved position to
  restore, the home has nobody near it on most devhouse 2 days (Tokyo 29,38 while the cast is in Machi),
  and a Time Travel hop is made to see that day's people. Saving the last position was the alternative; it
  would put a returning player in a room the cast left weeks of game time ago after every date change.
  `CharacterSelect.become` calls `GameScene.resettleNewPlayer()`: a
  player who has not taken a step and has just become the only member near their start cell (the
  creator's name Easter egg, or Menu → Character) is moved to wherever `startFor` says now. With
  somebody still within `Trips.NEAR` cells (`Trips.hasCompany`) they stay exactly where they are, and
  the first step off the start cell ends it (`update()` clears `bootStart`; `GameScene.playerIsAt` compares
  through `resolve`).
  `config.player.startRoom/X/Y` — what the editor's Spawn tool writes — is now only the fallback for a
  config with no trips (and the reachability seed in `AchievementManager` / `world-model.js`): to move
  where the game opens, edit the trip's `home` / `stays` cell. The headless model (`tools/play.js`) still
  OPENS a session on the trip's own cell (`Trips.homeFor`: Tokyo 29,38 on a devhouse 2 day), the same
  place every day, which is what a script wants; `play.js start` goes where the game puts a player.
- **The intro** — who devhouse is (`Intro.cast`: `CharacterSelect.lineup` of the trip's members, alphabetical —
  the cast row draws them and the sentence under it names them), which trip this is and whether it is on right now (`Intro.welcomeCopy`), and where everyone
  is today (`Trips.membersByRoom` + `Trips.whereText`).
- **Time Travel** (`src/DatePicker.js`) — a trip's own days are underlined in the grid whether or not
  they have posts, and a row under the grid names every trip (the selected day's is lit). A click / tap
  on a name, or SHIFT + left/right (touch: hold the sprint pill and press ◀ ▶), jumps to that trip's
  first day with posts, or its first day when it has none (`Trips.jump` / `Trips.landing`). The row
  under the selected date jumps to today (SHIFT + up) or back to the day the game is on (SHIFT + down). No new key.
  The legend under the grid (`DatePicker.legend`) explains each mark: dot = blog post, underline = trip
  (only when the config has trips), and of the two coloured days only those on the month shown —
  gold = today, blue = you are here (the game's day, when it is not today; issue #98). It is worded
  shorter when the line would not fit the panel (52 characters).

**Adding a trip**: add it to `trips`; give its base cast NPC definitions in the room(s) they are based
in, marked with `trip` (and `stay` when the trip has stays) — the shape `tools/generate_cast.py`
`base_npc` writes; keep the lines neutral, they are what people say until their first post. Then
`node tools/play.js check` (it surveys every day of every trip: base NPCs must be walkable-up-to, and
every home / stay cell and every new-player start must be a free cell that leads somewhere) and
`node tools/play.js trips` / `start` to see where a player lands on the current `date`.

**Boundary System:**
- Each room can define a custom polygon boundary to restrict player movement
- Boundaries are arrays of grid coordinate points: `[[x1,y1], [x2,y2], [x3,y3], ...]`
- If no boundary is specified, defaults to rectangular bounds matching world dimensions
- Player movement is validated using point-in-polygon detection (cell center must be inside boundary)
- Boundaries can create non-rectangular rooms (L-shapes, hexagons, irregular polygons, etc.)
- The visual editor provides a boundary editing tool for creating custom shapes

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

### HUD System

Semi-transparent bar at top showing: `{game.title} | {room name} | {game.date}` with clickable menu button
- The room segment is the room's display `name` from config, never its key (`GameScene.hudRoomName()`, the
  one place that decides it; falls back to the key for a room with no name). Generated interiors get a
  human name from their generator: `7-Eleven · Sapporo` (`generate_konbinis.py` `store_name()`, numbered
  only where a host has several stores: `7-Eleven · Market 3`), `Don Takote · Osaka`
  (`generate_discount_stores.py` `store_name()`), `Sapporo Station` (`generate_stations.py`
  `station_name()`). Nothing reads `room.name` as an identifier - room keys are the identifiers.
- Inside the stitched city the "room" is the district underfoot (`roomManager.currentDistrict()`, kept in
  `hudDistrict`), so the segment changes as you cross from one district into the next
- Title and date loaded from `config.json`
- Uses `window.devicePixelRatio` for retina display text rendering
- Fixed to camera with `setScrollFactor(0)`
- Depth 1000+ to render above game elements
- Menu button (right-aligned) opens MenuManager on click

### Fonts and Japanese Text (issue #78)

The game draws text in three pixel fonts, loaded in `GameScene.preload` and used by family name
everywhere: `PressStart2P` (HUD, title), `PixelOperatorMono` (dialogue, captions, overlays) and
`PixelOperatorMonoBold` (name plates, labels, toasts). None has kana or kanji, and blog-derived dialogue
and post titles are sometimes Japanese.

- **One Japanese face for all three**: `fonts/DotGothic16-Regular.ttf` (SIL OFL, full JIS kana + kanji,
  drawn on a 16px grid - credit, licence and hash in `fonts/README.md`). `src/utils/JapaneseFont.js`
  registers it as a second `FontFace` of each family, limited by `unicode-range` to the Japanese blocks
  (`JapaneseFont.RANGES`), so the browser picks it per character. Every existing
  `fontFamily: 'PixelOperatorMono'`, the canvas measuring in `DialogueManager`, and the creator's DOM
  input get Japanese glyphs with no change at the call site - **do not add a font stack or a second
  family name for Japanese**; a new family needs only a `load.font` line and an entry in
  `JapaneseFont.FAMILIES` (a unit test keeps the two in step). Latin text, arrows and the d-pad glyphs
  are outside the ranges and render exactly as before; a character DotGothic16 lacks falls back to the
  system font.
- **Loading**: 2 MB, so it is not in the boot queue. `GameScene.preload` starts `JapaneseFont.load` when
  the Phaser loader completes; it fetches the file once (one buffer shared by the three faces) and then
  `JapaneseFont.refresh` redraws any Text object already showing Japanese (canvas text drawn before a font
  is ready stays in the fallback otherwise). If the fetch fails the game warns and carries on with the
  system font, and `JapaneseFont.retry` (called by `DialogueManager.show`) fetches again the next time a
  dialogue opens. Kana and kanji are one em wide in both, so wrapping does not change when it arrives.
- **Metrics**: Phaser sizes a line box from the Latin font (ascent 18px at 24px); Japanese glyphs stand
  about 3px taller. Text with padding (name plate, caption, toasts) has room; the dialogue text has
  `DialogueManager.TEXT_PAD_TOP` blank rows above its first line for this, and `layout()` still adds 8px
  of leading to a line with Japanese in it so rows do not touch. An unpadded Text that may show Japanese
  needs the same top padding - and in `PressStart2P`, whose box has no descent, a row of bottom padding:
  call `JapaneseFont.fit(text)` after its text is set (and after a `setText` that may change it). It pads
  top and bottom by `padRows` (an eighth of an em) only while the text has Japanese in it, so Latin text is
  untouched and a vertically centred Text does not move; a bottom-anchored Text in a PixelOperator face
  (the descent already holds the glyphs) passes `{ below: false }` so its baseline does not lift. The HUD
  room name, the Character screen rows and the created player's name label (top only) use it (#155); the other overlay `text()` helpers show Latin only today.
- Signage is not text: the ad pool and the Don Takote sign are pre-rendered sprites
  (`tools/generate_ads.py`, `tools/extract_city.py`), so they do not use this font.

### Shop, Food and Drink (issues #12, #46, #82, #83, #84)

`src/Shop.js` owns the yen wallet, the inventory, the buy/items overlays and the
food & drink effects. Everything starts with a bump (`GameScene.checkNPCInteraction`
→ `Shop.checkShopInteraction`, which only fires on BLOCKED cells):

| Bump | Opens (`Shop.VENUES`) |
|------|-----------------------|
| any `vending-machine*` tile, any room (bump the machine's foot from the cell in front) | `vending` — items with `where: 'vending'` |
| `office-counter*` in a konbini | `counter` — every vending + counter item |
| `office-shelf-drinks` / `-shelf-glass` / `office-fridge` / `office-freezer` in a konbini | `drinks` — the drinks only |
| `office-shelf-snacks` in a konbini | `snacks` — the food only |
| `office-counter2*` (the bar) in a room with `"shopMenu": "izakaya"` | `izakaya` — items with `where: 'izakaya'` |

- A "konbini" is any room with `interior: true` and `shopEnabled !== false` — the
  7-Eleven interiors and the Don Takote discount stores (below). The
  Izakaya is `shopEnabled: false` + `shopMenu: "izakaya"` (set in
  `tools/generate_inaka.py`): its shelves and tables stay furniture, only the bar
  sells, and the drinking game's `triggerCells` are checked first so they never
  open a menu.
- **Vending machines are solid down to their foot** (issue #101). A machine is a cabinet
  tile over a foot tile (`*-vending-machine-top*` over `-bottom` / `-base*`; the tall ones
  are a 1x2 cabinet sprite over a base), and the foot is only the last 14-18px of the
  cabinet - with the foot cell walkable the player stood on the machine's lower half. Both
  the foot and the cabinet cell above it collide (the empty top cell of a tall machine
  stays walk-behind); the vending rule matches both tiles, so the bump that opens the shop
  is on the foot, from the cell in front - which must be walkable and lead somewhere (issue
  #137: lint error `vending-no-front`; the roof-top row 27 in front of Market's (22,26) and
  (23,26) is a walk-behind strip for that, the roof is solid from row 28). The
  `vending-white` / `vending-red` prefabs carry both colliders; `node tools/play.js lint`
  fails a room with `vending-walkable` otherwise, and `python3 tools/seal_vending.py [Room ...] [--dry-run]` repairs room data
  (it refuses to seal a cell holding a transporter or a dated NPC). The same goes for the fixtures
  INSIDE a store (issue #152): a shelf or cooler is bumped from the cell below it, so lint fails with
  `shop-no-front` when any column of a konbini / Don Takote shelf or cooler has no walkable cell under
  it that the door leads to (the till, against the front wall, needs any reachable side), and with
  `shop-sealed-floor` when a store has bare floor the door does not lead to (issue #182: the corner
  water dispenser stood one row below the back wall and boxed in the corner cell above it, beside the
  cooler run - `generate_konbinis.py` now stands it in the back corner, and where that would leave a
  single cell between it and the coolers the run grows one unit to meet it, so the back row has no
  one-cell nook on either side of it).
  `play.js check` reports every room's lint errors too (`WorldModel.lintProblems`, issue #178), so a
  store cut off from its door shows up there as `KonbiniMarket1: lint shop-no-front: ...`.
  `check` exits 1 when it lists any problem, like `lint` (issue #188), so a script or CI step can gate on it.
  `generate_konbinis.py` lays a store out as coolers | walkway | aisle | walkway | (aisle | walkway) |
  counter row: a two-cell `office-fridge` pushes the aisles down a row, the last aisle stops two rows
  short of the counter row (one on the row above it closed the ring and sealed the back of the store
  off from the door - `KonbiniMarket1` and `KonbiniMarket3` were like that), and a five-row store gets
  the one-cell freezer instead of the fridge. Keep NPC spots and
  door arrivals off the cell in front of a machine's cabinet.
- **Don Takote** (issue #91): every `discount-store` facade has a shop floor -
  `DonTakoteMarket`, `DonTakoteOsaka`, `DonTakoteSapporo` (HUD: `Don Takote · Osaka`; the room's
  `shopTitle: "DON TAKOTE"` titles the till's list instead of `KONBINI` - `Shop.titleFor`), built
  by `tools/generate_discount_stores.py [Host ...]` on the konbini pattern. 27x19 room, one
  fixed floor plan (so a town generator can wire its door without running it first): the
  facade's own sign on a yellow back wall, a wall-to-wall back row (drink coolers one side,
  shelving the other), three ranks of shelves either side of a centre aisle, cartons of
  stock in the front corners, one till by the three-cell door mat. What is seeded per store
  (host + door cell) is the stock, the floor and which side the till is on. It adds no shop
  code: `interior: true` makes it a konbini to `Interactions.js`, so the counter, shelves
  and coolers sell through the rows above (the buy list is still titled KONBINI). The
  signage (`don-takote-sign` / `-wall` / `-wall-top` / `-pop-yen` / `-pop-sale`) is cut from
  the facade sprite by `tools/generate_discount_art.py` (Pillow, no font needed).
  **Doors**: `generate_osaka.py` and `generate_sapporo.py` stamp the facade with
  `seal=False` and add `don.door_transporter(host, door)` themselves, so regenerating the
  town keeps the shop open; Market is ported, so `generate_discount_stores.py` lifts the
  one door collider and adds the transporter there (and does the same, idempotently, for
  the generated hosts). The cell in front of the door must be free - the script asserts it.
  A new host: stamp the facade, add the host to `ALL_HOSTS`, run the script, then
  `config_to_tiled.py` for the store room and the host.
- **Catalogue**: `Shop.DEFAULT_ITEMS` (or `config.json` `shop.items`, which replaces
  it wholesale). Each item: `id` (a save-file key — don't rename), `name`, `price`,
  `where`, `category` (`drink` | `food` | `gear`), `desc`, `icon`, and `effect` or
  `permanent`. Keep `desc` truthful — the use toast is generated from the `effect`
  numbers by `effectSummary()`, so the two are read side by side. The fish
  (`category: 'fish'`, see below) are appended to whichever catalogue is in use.
- **Icons** (`src/ItemIcons.js`, issue #82): every item has a 16x16 pixel icon, shown
  at 2x on a small slot square in the buy / sell lists, the Items screen and the HUD
  effect chips. They are drawn in code, data-first: `icon: { shape, colors }` names
  a pixel map in `ItemIcons.SHAPES` (16 strings of 16 characters: `.` transparent,
  `o` outline, `w` white, `e` silver, `k` grey, and the item's own `a` body / `b`
  shade / `c` `d` accents) and fills in its colours. An item with no `icon` gets
  `ItemIcons.DEFAULTS[category]`. Textures are made once, keyed `item-<id>`.
  **Real art needs no code change**: drop `<id>.png` in `assets/items/` and list the
  id in `assets/items/manifest.json` — it is preloaded under the same key and
  `ItemIcons.ensure()` only draws what is missing (see `assets/items/README.md`).
  `node tools/test_game.js` checks every item has a distinct, well-formed icon; look
  at new ones in a list before shipping them — the panels are dark, which is what
  the slot square is for.
- **Effects are additive buffs only** (no hunger/energy stat, nothing gates
  movement). The keys an `effect` may carry are listed in `Shop.EFFECT_KINDS`:
  `speed`, `scramble`, `steady` (read by `InputHandler` via `movementModifier()`),
  `fishBite`, `fishWindow`, `fishLuck` (read by `Fishing` via `shop.buff(key)`),
  `headStart`, `prizeBonus` (read by `DrinkingGame`, locked in when a round
  starts; Bailey mirrors the head start, so his +10 gimmick survives), plus `secs`.
  To add a new kind: add it to `EFFECT_KINDS` with a `describe`, then read it with
  `shop.buff('key')` where it applies.
- **Slots**: one `drink` effect and one `food` effect at a time (`Shop.SLOTS`, slot
  = the item's category). The same item refreshes its timer; a different item in
  the slot replaces it and the toast says which. Active effects show as chips
  under the right end of the HUD bar with the time left, and in the Items screen.
- **Buying**: ↑/↓ pick, ←/→ quantity (1-9, capped by the wallet), ENTER/SPACE buy,
  SHIFT+ENTER/SPACE "buy & use now" (touch: hold the sprint pill and tap A; mouse:
  the `‹ ›`, `[ buy ]` and `[ buy & use now ]` buttons). Buy-list rows do NOT select on
  hover (the stepper sits under them, so a mouse heading for it would drag the
  selection down): a click/tap picks a row, clicking the picked row buys it. Rows
  show `have ×N` and dim the price you cannot afford. Hint lines switch to A / B /
  sprint wording when touch controls are on (`Hints.text`). No extra key bindings.
- Expired effects are queued in `shop.woreOff` and toasted ("X wore off") by the
  250ms chip timer once no other toast or shop overlay is up, so the message is
  never lost. Against Bailey the showdown banner says he matches the head start.
- **Fish are items** (issue #83). `Fishing.CATCHES` is the one table: `id`, `name`,
  `odds`, `value`, plus `desc`, `icon` and `grilled` (an effect). `Shop.fishItems()`
  turns every catch worth something into a catalogue item (`category: 'fish'`,
  `sell: value`, `effect: grilled`, `effectName: 'Grilled <name>'`, sold nowhere).
  A landed fish goes into the bag through `shop.addCatch(c)` — the wallet is not
  touched — and the toast says what it was, that it is in the bag and what it sells
  for. A catch worth nothing (the old boot) is thrown back with a toast and never
  becomes an item. `shop.caught` counts landings per species and feeds the
  **Big Catch** achievement (`AchievementManager.fishingProgress()`: land a rare
  fish, `Fishing.isRare` = worth `Fishing.RARE_VALUE` or more).
- **Selling**: a venue with `buys: true` in `Shop.VENUES` (the konbini `counter`, the
  `izakaya` bar — not vending machines or the shelves) gets one more row under its
  items, `sell your catch ›`. ENTER on it flips the same panel to the SELL list (the
  fish held, their price, ←/→ quantity up to what is held, ENTER sells, the row
  `‹ back to the menu` returns); `shop.mode` is `'buy'` or `'sell'` and
  `refreshStock()` rebuilds the list for it. A venue with `grills: true` (the
  izakaya) also offers SHIFT+ENTER / `[ grill & eat ]`: one fish is eaten for its
  `grilled` effect in the FOOD slot. A raw fish cannot be used from the Items screen
  (the toast says where to take it). `Shop.sellValue(item, qty)` is the price; items
  without `sell` are worth nothing, so a shop never buys its own stock back. No new
  key bindings.
- **Save blob** `localStorage.gamev2_shop`:
  `{ v: 3, money, items: {id: count}, effects: {drink|food: {id, until}}, used: {id: count}, caught: {id: count} }`.
  `until` is an absolute epoch-ms expiry, so buffs survive reloads and room changes
  and lapse on time; on load it is clamped to the item's own duration and effects
  for unknown items are dropped. Older blobs load as-is and are rewritten as v3 on
  the next save: the issue #12 one (`{money, items}`) and v2 (no `caught`, no fish)
  — the wallet is never changed by loading.
  `used` counts consumption and feeds two achievements in
  `AchievementManager.consumptionProgress()`: **Taste Tester** (use every
  consumable) and **Regular Customer** (25 uses), both listed in the Achievements
  overlay.
- Test hook: `scene.shop.clockOffset` (ms) fast-forwards the shop's clock so a
  test can expire a buff without waiting.
- **Nomikai showdown stake** (`src/DrinkingGame.js`, issue #84). The ready screen has
  a stake row from `DrinkingGame.STAKES` — `FRIENDLY` (stake 0, wins ¥100 on the
  house), `SMALL TAB` (¥500) and `BIG TAB` (¥2,000), each `{ id, label, stake,
  winnings }` — picked with ←/→ (A/D, the touch d-pad) or a click/tap. A stake the
  wallet does not cover is greyed and cannot be picked — trying to (→ or a tap) toasts
  what it needs and what the wallet holds; the last pick is remembered
  while it is still affordable. The line under it says what is at risk and what the
  pool is. Money moves like this, and nowhere else: the stake leaves the wallet in
  `begin()`; a win pays `DrinkingGame.pool(option, prizeBonus)` = stake +
  winnings × bonus (so Karaage's +50% applies to the winnings, never the stake); a
  draw returns the stake; a loss pays nothing more, so it costs exactly the stake;
  ESC mid-round (`leave()`) forfeits the stake with a toast; ESC on the ready screen
  or the result costs nothing. The result screen leaves on ENTER / ESC, and on
  SPACE (the touch A button) once `DrinkingGame.RESULT_GRACE_MS` has passed, so the
  last mashes of a round do not dismiss it. The effect hooks are unchanged (`headStart` and
  `prizeBonus` are locked in when the round starts) and so is the Bailey rule: when
  the player is Damian, Bailey mirrors every press and the head start and wins by
  his ten bonus gulps, so any stake put up against him is lost.
- `node tools/test_game.js` covers the pure parts of all of this without a browser:
  icons, sell values, catches into the bag, save migration, stake / pool maths and a
  whole stubbed round at every stake (win, lose, draw, walk-out, vs Bailey).

### Title Screen and Character Portraits (issue #9)

**Title screen** (`src/TitleScreen.js`, `scene.titleScreen`): shown on every page load, after
`window.hideLoader()` and BEFORE the first-run character creator — `GameScene.create()` passes the rest of
the boot flow (the `CharacterCreator.shouldAutoShow()` check) as the `show(onStart)` callback. It draws the
game title (`config.game.title`), the devhouse members (`CharacterSelect.lineup()`, from `config.members`) lined up with a small hop
travelling along the line, and a blinking start prompt, at depth 9000 on an opaque backdrop the colour of
the HTML loader.
- SPACE / ENTER / ESC (so touch A and B too) or a tap/click anywhere dismisses it. While it is up it is
  **priority 0 in `InputHandler.handleInput()`**: no movement, menu or overlay input reaches the game.
  The triple-backtick debug chord is ignored too (`DebugManager.onBacktick` checks `titleScreen.isVisible()`).
- **`?notitle=1` skips it** — use it in tests and dev URLs that drive input straight after boot
  (the loader contract is unchanged: `#loader` is removed as before and the scene is live underneath).
- **In-game reloads skip it once**: `setGameDate()` (Time Travel / the HUD date) navigates with a full page
  load, so it sets the one-shot `sessionStorage` flag `gamev2_skip_title` first and `TitleScreen.shouldShow()`
  consumes it — a date hop lands straight back in the world, while a manual refresh of that URL shows the
  title again. Any future in-game action that reloads the page should set the same flag.

### New-Player Intro (issue #39)

`src/Intro.js` (`scene.intro`): a three-page overlay in the usual panel style (depth 2000-2003).
1. **Welcome to devhouse** (`Intro.welcomeCopy`, see Trips) — the friends: the members of the game date's
   trip (`Intro.cast` — `CharacterSelect.lineup` of that trip's `members`, alphabetical), drawn in the cast
   row above and named in the sentence under it (not `credits`, not James); which trip it is ("They are on devhouse 3 right now, in Hokkaido" while it is on, "This is
   devhouse 2, their trip to Japan" otherwise); NPC lines coming from the blog posts ("once they start
   writing" for a trip with no posts yet); and the HUD date picking the day ("Time Travel in the menu" to
   visit another day or another trip — the game always opens on a trip day, see the default game date
   under `npcs`). On a lead-in day it says when the trip starts instead, and in the real days before a
   trip it adds "devhouse 3 starts on February 18." (issue #164, see Trips).
2. **How to play** — move / sprint / interact / talk / menu drawn as keycaps (the interact row also
   lists what a bump starts: people, shops, trains, the izakaya); when
   `touchControls.enabled` the same rows are drawn as the on-screen d-pad, sprint pill and A / B buttons,
   plus a one-line keyboard reminder (the page is redrawn if the input in use changes while it is up).
3. **Where to start** — there is no quest system, so it points at real things: the friends (`whereFriendsAre()`
   → `Trips.whereText`: the ones in the room — the district, in a stitched city — the player is standing in are named — "Today Bailey, Damian
   and Julia are here in Machi, and Dylan is in Inaka.", "Today everyone is here in Sapporo." — and
   other rooms are listed by display name, three at most; whoever the player is playing as is not
   counted; on a lead-in day "They have not arrived yet: …", `Intro.meetCopy`), exploring, and Paint the Board (with the live progress bar from `achievementManager`).

Fishing controls and map travel are **deliberately absent** (fishing is learned when a rod is bought; map
travel is a debug feature) — keep them out when editing the copy.
- **Input**: SPACE / ENTER (touch A) or a tap anywhere turns the page and the last page closes it; ESC
  (touch B) skips the lot. It is the first entry in `InputHandler`'s overlay list, so nothing moves or
  opens underneath, and `DebugManager.onBacktick` ignores the debug chord while it is up.
- **Boot flow is strictly sequential, never stacked**: loader → title → (first visit) character creator →
  intro → world. `CharacterCreator.show({ onClose })` runs the callback once from `hide()` — confirmed or
  cancelled — and `GameScene.create()` uses it to open the intro.
- **Gate**: localStorage `gamev2_intro_seen`. `Intro.shouldAutoShow(firstVisit)` sets it to `pending` when a
  first visit begins (so a reload half way through the creator or the intro still gets the intro) and
  `hide()` sets it to `1` (finished or skipped). A returning player — a character already saved, key absent
  — is never shown it automatically, and a Time Travel reload does not replay it.
- **`?nointro=1`** suppresses the automatic showing (and leaves the gate untouched) — combine with
  `?notitle=1` in tests that start from a fresh profile. Tests that pre-seed `gamev2_character` never see it.
  NOTE: every profile, seeded or not, starts next to the cast of the game date (e.g. Machi 22,10 on
  2025-11-11) since #166 — there is no fixed Tokyo 29,38 spawn any more. A test that needs a known cell
  must pin the date (`?date=`) and read `Trips.startFor`, or move the player itself
  (`roomManager.switchRoomInstant`).
- **How to Play** in the ESC menu replays it at any time (`scene.intro.show()`). It is the only controls
  reference: the separate Controls menu entry and overlay (#38) were folded into page 2 (#55), so a new
  global binding or bump interaction is documented there.

**Dialogue portrait** (`DialogueManager.showPortrait`): the speaker is shown dating-sim style as a large
bust in the same wooden frame as the blog photo (`drawFrame`, shared by both), standing on the panel's
top-left corner with the name plate bridging frame and panel. The blog-photo frame keeps the top-right;
the two never overlap (20px gap) and share a bottom edge (`panelY - 12`). The bust is the head-and-shoulders band of `<name>_front_frame_0`
(`DialogueManager.BUST`, a 48x40 crop) at 5x in a 240x200 window. A speaker whose sprite is not a
directional `<name>_front` 64px character sprite falls back to the old look (`showFullSprite`: whole sprite
at 2x centred above the panel, name above it).

**Post caption** (issue #79): a dated state may carry `"posts": [{id, lines, title?, url?}, ...]` — which
blog post each run of its dialogue lines came from (`tools/blog_to_npc.py` writes it; same-day posts share
a state). `postForLine` in `src/utils/NpcStates.js` maps the line being said to its post, and
`DialogueManager.updatePostCaption` shows `from: <post title>` on a small plate straddling the panel's top
edge at its right end (under the blog photo when there is one), cut with an ellipsis at
`CAPTION_MAX_WIDTH`. It appears only when a title is recorded and the `lines` counts add up to the
dialogue — states placed before titles were kept show nothing, and nothing is invented for them. With a
`url` (http/https only) the caption is light blue and a click or tap on it opens the post in a new tab
instead of advancing; without one a click on it advances like the rest of the overlay. The link opens on
release, and only when the press began on that same link, so the release of a press that advanced the
dialogue never opens the next line's post; the hit area reaches `CAPTION_HIT_PAD` above and below the
plate for fingers. It adds no key
binding and changes no hint or panel size. `posts` belong to the dialogue they were written with:
`resolveNpc` clears them when a later state changes the dialogue without naming its own (same rule as
`voice`). The plumbing is `resolved.posts` → `NPCManager.spawnNPC` → `npc.posts`, exactly like `photo`;
`play.js` prints `from: <title> <url>` under an NPC's lines.
- **Recording**: the payload's `title` is always kept; `url` only if the payload has one (today's payload is
  `{post_id, title, author, date, content}` — the www-jp workflow has to add `url` for links to appear).
- **Backfill**: `python3 tools/blog_to_npc.py --backfill-posts posts.json [--dry-run]` fills title/url into
  existing states from a list of `{id, title, url}` (optionally `author`, `date`). A state is matched by
  its `posts` ids, else by its photo id (a photo is filed under its post's id), else by author + date when
  exactly one listed post fits; anything else is reported and left alone. No LLM call, no placement.
  The shipped states have not been backfilled (the post list lives in the www-jp repo: `site/content/<id>.md`
  front matter), so no caption shows in the live game yet.

**Real art drop-in, no code change**: put `assets/portraits/<name>.png` in place and add `<name>` to
`assets/portraits/manifest.json` (`{"portraits": ["bailey", ...]}`, shipped empty). `preload()` loads only
the listed names as textures `portrait-<name>` (so a character without art never 404s; a malformed
manifest is treated as empty; a listed name with no PNG logs one 404 and falls back to the sprite), and both the dialogue
frame and the title line-up use that texture instead of the sprite when it exists. Size/format rules are in
`assets/portraits/README.md` (240x200 window, 6:5; 240x200, 120x100 or 48x40 PNGs scale cleanly).
No hand-drawn portraits exist yet — everything shown today is derived from the overworld sprites.

### Playing as the Cast: Character Menu and the Name Easter Egg (issues #15, #45)

`src/CharacterSelect.js` (Menu → Character) swaps the player to a cast member with a full sprite set
(`CharacterSelect.available(config)`: james, bailey, damian, dylan, julia, khoi, sam, xander — derived from
`spriteMetadata`, never listed in code). The whole swap lives in ONE
place, `CharacterSelect.become(scene, name)`: it writes `localStorage.gamev2_character = <name>`, swaps the
live player sprite, and calls `syncNpcPresence()` (that person's NPC leaves the world) and
`syncPlayerNameLabel()`. `CharacterSelect.applySaved` restores it on reload.

`src/CharacterCreator.js` (first-run, or Menu → Create Character) has an Easter egg on top of that: type one
of those names as your own (`castMatch()` — whole name, trimmed, case-insensitive; "baileyx" and the
sprite-less credits names Gloria/Yashuk do nothing) and the live preview flips to that person's own sprite,
the part/colour rows and RANDOM dim and lock, and a "hey, it's Bailey!" hint appears; it all reverts as soon
as the name stops matching. A creation that was already saved under one of those names opens as itself
(`eggArmed` is false until the name box is edited). START/ENTER then calls `CharacterSelect.become` and toasts "You are Bailey!"
instead of saving a composite. It deliberately skips `CharacterCreator.save()`, so an earlier creation in
`gamev2_custom_character` survives and is still offered as the custom row in Menu → Character.

### The Cast, and Interim Sprites for People Without Art (issue #117)

**The cast is data.** A cast member is a name with a full sprite set in `config.json` `spriteMetadata`
(`<name>_front`, `_back`, `_side`; 4 + 4 + 2 frames of 64x64 in `assets/sprites/<name>_<dir>_frame_<i>.png`).
`CharacterSelect.available(config)` derives the list, and everything playable reads it: Menu → Character,
the creator's name Easter egg, `syncNpcPresence` (you never meet yourself) and `tools/play.js as <name>`.
No code lists the names. The ONE explicit list is `config.json` top-level `members` (sprite base names;
shown alphabetically whatever order the list is written in: bailey, damian, dylan, julia, khoi, sam, xander) — the devhouse members, read through
`CharacterSelect.lineup(config)` by the title line-up ONLY (the intro's cast row and its sentence pass the game date's trip
members, `lineup(config, trip.members)` — `Intro.cast`, see Trips). A listed name with no
sprite set is skipped; a sprite set that is not listed never appears there (James is the default player
sprite and selectable, but not a member — issue #56). The line-ups size themselves for any
number (title: spacing and scale from the count; intro: the row closes up, then drops to 1x; the Character
menu's rows close up when the roster outgrows the screen).

**Devhouse 3** (Sapporo 18-25 Feb, Asahikawa 25-28 Feb) adds Khoi, Sam and Xander to Bailey, Damian, Dylan and
Julia. They have no hand-drawn sprites yet, so `tools/generate_cast.py` bakes INTERIM ones: the character
creator's composite (head / torso / legs / beard donors + recolours), run offline and saved as real PNGs.

```bash
/Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_cast.py                # write frames, register
/Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_cast.py --check        # exit 1 if stale
/Library/Developer/CommandLineTools/usr/bin/python3 tools/generate_cast.py --sheet x.png  # contact sheet, LOOK at it
```

- **The looks are one table**, `LOOKS` at the top of the tool (same shape as a creation saved by the
  creator, so a look can be designed in the game and copied over; the bake is what the creator
  previews). Today, all placeholders — nobody has
  described what they look like:

  | name | head | hair | top | legs | beard | skin |
  |---|---|---|---|---|---|---|
  | khoi | james | `#1a1208` black | damian, `#3a6fd8` blue | bailey, `#2b2b33` charcoal | none | `#f6c39a` |
  | sam | dylan | `#8a5a2b` light brown | bailey, `#7e4fc9` purple | julia, `#8a5a2b` brown | none | `#fdcba2` |
  | xander | james | `#b0491f` auburn | damian, `#d9d9d9` off-white | julia, `#032e48` navy | bailey's, `#b0491f` | `#f4bc8e` |

- **Faithful port, read not copied**: the compose is `CharacterCreator.composePixels` line for line (the DOM-free
  half of `composeFrame`), and
  `DONORS` / `BEARDS` / `CUTS` are parsed out of `src/CharacterCreator.js` at run time, so those tables
  cannot drift (the tool exits if it cannot find them). The output is pixel-identical to the creator's
  (a unit test composes every look with the game's code and compares it with the baked PNGs — change one
  side and port it to the other). Both carry five marked `TIDY` rules that remove
  the artefacts of a plain band cut between different donors: holes where the top donor shows its own trousers in the torso band
  (damian's hem), the stray outline of the head donor's own high sleeve (james, side frame 1), mouth-interior
  pixels recoloured as hair (dylan — a moustache that flickers with the walk cycle), an open shoulder
  line where the head donor's shoulders are narrower than the top worn, and what the top donor's own long hair
  leaves in the torso band (julia's top on another head: a stray strand of outline behind the shoulder in side
  view, and in back view a see-through hole over a dark band — the hole and the outline under it become shirt).
- **`dylan` as a top donor**: his shirt is a two-teal checker (both teals are in `DONORS.dylan.top`), so a
  recolour keeps the checker as two shades. It is solid: a unit test keeps every donor sprite hole-free.
- **Replacing an interim set with real art**: drop the ten hand-drawn PNGs over the generated ones (same file
  names, same 64x64 template as the rest of the cast) and delete that name from `LOOKS`, or the next run
  overwrites them. Nothing else changes. Generated sets are cast, not creator donors (`DONORS` holds the
  measured palettes of the hand-drawn five); a hand-drawn replacement can be added there.
- **Base NPCs** come from the same tool (`HOME`: room, cell, two placeholder lines that state no facts about
  anyone). They are added only while the room has no NPC of that name, so later edits and the blog pipeline's
  states are never undone. All three stand in Sapporo — Khoi by the station house (38,8), Sam on the Odori
  park path (21,27), Xander on the Clock Tower plaza (35,17) — and are marked `"trip": "devhouse3",
  "stay": "Sapporo"`, so they are there on devhouse 3's Sapporo days only (issue #131, see Trips), until
  their first post moves them. The rest of the devhouse 3 base cast (the other four in Sapporo, all seven
  in Asahikawa) is plain config data with the same marks.
- **Blog authors** (`AUTHOR_NPCS` in `tools/blog_to_npc.py`, GitHub login → NPC name): the three are listed
  under placeholder keys (`'<khoi github login>'`) because their logins are NOT known. A placeholder can never
  match a post (`is_login`: only login-shaped keys are looked up — letters, digits, inner hyphens, underscores, a
  `[bot]` suffix). Replace the key with the
  real lower-case login and that author's posts start placing their NPC. Until then — and for any other
  unknown author — the post is skipped with `WARNING: #<id>: blog author '<login>' is not mapped to an NPC`,
  which names the login to add, the file, and who is still waiting (also a `::warning::` annotation under
  GitHub Actions). `tools/test_blog_to_npc.py` covers mapped, unmapped and placeholder authors.

### Voiced Dialogue (text-to-speech)

NPC dialogue can be read aloud. A resolved NPC state carrying `"voice": <voiceId>` (passed through
`syncNpcPresence` → `NPCManager.spawnNPC` exactly like `"photo"`) has one clip per dialogue line at
`assets/voice/<voiceId>/<lineIndex>.mp3` (0-based index into that state's `dialogue`).

- **Client** (`src/Voice.js`, `scene.voice`): `DialogueManager.updateText()` calls `voice.playLine()` as each
  line is shown (which stops the previous line's clip) and `close()` calls `voice.stop()`. Clips are NOT
  preloaded — the source is set at dialogue time on ONE shared `HTMLAudioElement`, which is created and
  unlocked (10 ms of silence played inside the first key press / tap, capture-phase listeners removed once
  it succeeds) because `playLine()` runs from Phaser's update loop and iOS Safari only lets a
  gesture-played element start from there (the unlock is untested on a real iOS device). An NPC without `voice`, a clip
  that fails to load/decode, or a rejected `play()` is a silent no-op (the only trace of a 404 is the
  browser's own network log line, which is why the pipeline never records a partial clip set).
- **Mute**: the ESC menu's `Voices: ON/OFF` row (flips in place, menu stays open) persists in localStorage
  `gamev2_voice_muted` (`'1'` = muted; default ON). It is the game's shared audio setting — other audio
  features should read `scene.voice.isMuted()` / subscribe with `scene.voice.onMuteChange(fn)`.
- **State merging**: clips belong to the exact lines they were generated from, so in `resolveNpc` a state
  that sets `dialogue` without naming `voice` clears the inherited voice (and `tools/npc_state.py --dialogue`
  drops a state's `voice`).
- **Pipeline** (`tools/post_voice.py`, called by `tools/blog_to_npc.py` after the photo import): with
  `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_<NPC>` (e.g. `ELEVENLABS_VOICE_BAILEY`, `_DAMIAN`, `_DYLAN`,
  `_JULIA`, `_KHOI`, `_SAM`, `_XANDER` — the name is derived from the NPC name, so a new author needs no code
  change, only the secret AND a line passing it in the `env:` of www-jp's `game-npc-pipeline.yaml` /
  `game-npc-backfill.yaml`, which list each one by hand) set, each dialogue line is POSTed to the ElevenLabs text-to-speech REST API (stdlib `urllib`)
  and the dated state gets `"voice": "<npc>-<date>-<hash>"`. Optional: `ELEVENLABS_VOICE_<NPC>_DRUNK` (used
  when the LLM's new `drunk` boolean says the post reads as drunk; the state then also carries
  `"drunk": true`) and `ELEVENLABS_MODEL` (default `eleven_multilingual_v2`). Best-effort like photos:
  unconfigured or failing, it logs one `voice: ... — skipped` line and the placement lands with
  `"voice": null`. A clip set is all-or-nothing, and an unchanged re-run reuses the clips on disk.
  After every config write `prune_voices()` deletes clip directories no state references any more, so the
  pipeline workflow must commit `gamev2/assets/voice` (additions and deletions, e.g. `git add -A`) together
  with `config.json` — a recorded `voice` whose clips were not deployed 404s on every line.
  `prune_photos()` (`tools/post_photos.py`) does the same for `assets/photos/<id>.png` prints no state names
  any more (a later same-day post's photo won, the NPC left the room, `--reset`; it also runs when a run
  places nothing, for a post that failed after its photo was imported), so `gamev2/assets/photos`
  must be committed the same way; `test_blog_to_npc.py` fails on an orphaned or missing print.
- **Backfill**: `python3 tools/blog_to_npc.py --voice-backfill [--dry-run]` voices existing dated states
  that have dialogue but no voice (no LLM call, no placement). `--dry-run` prints the line/character
  totals ElevenLabs would bill for.
- **Not live yet**: no API key or cloned voice ids exist, so no state has a `voice` and the game is silent.

### Featured locations / landmarks (issue #17)

Named landmarks are ordinary multi-cell sprites on a room's `Collidables` layer (Y-sorted by their feet:
solid at the base, walk-behind above), each wrapped in a prefab so generators can `b.stamp()` them:

| Landmark | Room | Sprite key | Art |
|---|---|---|---|
| Tokyo Tower | Palace (feet continue into Park) | `tokyo-tower_0_0` | line-art placeholder (ported from Godot) |
| Tokyo Station | Palace | `tokyo-station_0_0` | line-art placeholder (ported from Godot) |
| Tsutenkaku Tower | Osaka | `tsutenkaku_0_0` | line-art placeholder drawn by `tools/generate_tsutenkaku.py` |
| Dotonbori entrance arch | Osaka | `dotonbori-arch_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |
| Dotonbori ferris wheel | Osaka | `dotonbori-wheel_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |
| Sapporo Clock Tower | Sapporo | `sapporo-clock-tower_0_0` | shaded pixel art drawn by `tools/generate_hokkaido.py` |
| Sapporo TV Tower | Sapporo | `sapporo-tv-tower_0_0` | shaded pixel art drawn by `tools/generate_hokkaido.py` |

- **Osaka** (`tools/generate_osaka.py`, 50x46) is a generated town reachable only by train, like Yukimura:
  station house -> arch over the main street -> the canal bridge -> Canal-side Avenue -> Tsutenkaku on its
  plaza, with the ferris wheel on the north bank. The Dotonbori canal (rows 20-22) runs the whole width of
  the map under the bridge and carries the ambient boats (issue #61, see Ambient Traffic); the main street
  and the avenue are its asphalt roads (issues #106 / #151, see Street accessories) and the discount store by the arch opens into `DonTakoteOsaka` (issue #91, see Shop). The tower stands on the street's axis, so a shrub garden fills the ground behind
  it and the street forks round at the avenue (otherwise the player walks hidden behind the sprite for ten cells); the
  platform-edge fence and the continuous border hedges keep the player off the ballast and out from behind
  the fences. `OsakaStation` is registered in `tools/generate_stations.py`
  (`STATIONS` / `TOWN_DOORS`) and so in config `stations`; Osaka sits detached in `devhouse.world`.
  The legacy `Scenes/osaka/osaka_outside.tscn` is an old copy of the Tokyo overworld, not Osaka — do not
  port it (`tools/doport.py` / `render_rect.py` do take `PORT_SCENE=<path>` for a genuinely different scene).
- **Adding a landmark**: put a cell-aligned PNG in `assets/sprites/` (register `spriteMetadata` with
  `anchorX = 32/width`, `anchorY = 32/height`, plus `tileNames`), add a prefab spec to
  `tools/make_prefabs.py` (colliders = the base cells only), stamp it from the room generator, and add it to
  `LANDMARKS` in `tools/blog_to_npc.py` so blog NPCs can be placed there. A landmark entry may carry a third
  element `(dx, dy)`: the cell, relative to the sprite's top-left, where a visitor stands (tall sprites'
  own cell is their tip, not their foot), and an options dict:
  - `{'rooms': ('Machi',)}` — the label names one place, so only those rooms offer it. Use it whenever a
    label would be wrong in another town built from the same sprites (`the old-town lane` is Machi's;
    Asahikawa's machiya row is `ramen alley` — issue #100).
  - `{'indoors': True}` — offered inside station rooms, and only there (issue #73).
- **Where blog NPCs may be put** (`find_spots` / `walkable_near` in `tools/blog_to_npc.py`): outdoor rooms
  offer the ordinary landmarks. Interiors are opt-in: a station room (a key of `config.stations`; they
  carry no `interior` flag) offers only `indoors` landmarks — today `the platform`, its west end by the
  vending machine — and the model is told to pick it only for a post about that station or the train ride
  itself. `interior: true` rooms (konbini, izakaya) are never offered. The cell chosen is the nearest free
  one to the landmark's standing cell that can be walked to from one of the room's ways in, so a
  landmark inside a fence (Market's fox statues) puts its visitor outside it. A room on its own is entered
  by its transporters; a district of the stitched Tokyo city is also walked into from its neighbours, so
  `reachable_cells` floods the whole city as the game merges it (`city_districts` / `city_reachable`: doors
  and the spawn point as seeds, a later-listed district owning the cells it overlaps — issue #124) and
  `occupied_cells` counts a neighbour standing on a shared cell. Tokyo, whose only transporters are seams,
  is judged like the rest; an outdoor room with no way in at all now fails the test instead of silently
  skipping the reachability filter. `python3
  tools/test_blog_to_npc.py` checks all of this over every room in `config.json`: add a room or a
  landmark and it tells you if a spot is mislabelled, unreachable, or lands on a station's doors.
  **Never in the way** (issue #119, `walls_in`): an NPC is solid, so the cell must also leave everything
  that could be walked to still walkable — not the middle of a one-cell lane, the mouth of a dead end or
  the cell in front of a door — and must not take the only cell a neighbour could be walked up to from.
  Asahikawa's `ramen alley` is one cell wide: its standing cell (10,15) is refused and the author stands in
  the shop doorway beside it (9,14); before the rule a ramen post sealed off the west half of the alley,
  Sam's base spot included. `walk_region` is the whole stitched city for a district, so a walk that leaves
  the district and comes back counts.
- **The blog rehearsal** (issue #119): `python3 tools/rehearse_blog.py [--keep DIR] [-v]` (`--keep` takes a new or empty
  directory, or one an earlier rehearsal kept — it refuses anything else, and anything in or around `gamev2/`) runs
  `blog_to_npc.py` end to end the way the www-jp `game-npc-pipeline` workflow does (one `--payload … --mock
  --summary-out …` per post) for a devhouse 3's worth of synthetic posts — all seven members, Sapporo and
  Asahikawa days, a lead-in post, a day trip, two posts on one day, photos, voices, a drunk post, posts
  published before 09:00 in Japan, a re-run — in a SCRATCH directory, never the committed `config.json` or
  assets (both are fingerprinted before and after). Nothing leaves the machine: `--mock` for the LLM, local
  stand-ins for the photo download and the ElevenLabs call, `anthropic` un-importable, every socket connect
  refused and counted. The result is checked against the written config AND through the game's own code
  (`node tools/play.js --config=<scratch>/config.json`: every NPC resolved on every day from 4 Feb to 1 Mar
  2027, plus `check`). Run it after touching `blog_to_npc.py`, a Hokkaido map, the trips or the cast.
  What it needs from the tools:
  - `--mock` is steerable: a payload's `"mock": {"spot", "dialogue", "drunk"}` overrides the canned
    response (ignored without `--mock`), so a rehearsed post goes to the landmark it is "about".
  - `node tools/play.js --config=<file>` plays another config against this checkout's maps and sprites,
    with its own session file.
  - **Posts are dated by the day in Japan** (`post_date`, the trip's `utcOffset`): the payload's `date` is
    GitHub's `createdAt`, in UTC, and the pipeline used to keep its first ten characters — so a post
    written before 09:00 in Japan was dated the day before, and on the two days the game starts everyone
    afresh (18 Feb, and 25 Feb when the base moves to Asahikawa) it was history before it was published.
  - The new members' logins are still placeholders (`AUTHOR_NPCS`): the rehearsal proves such a post is
    skipped with the warning, then maps made-up `rehearsal-<name>` logins in memory only. A real login is
    used as soon as it is filled in. The run ends with a TO DO line while any placeholder remains.
  - `Sapporo · Odori Park` is a spot (the park's lanterns, `rooms: ('Sapporo',)`): the six landmarks issue
    #119 names all have one.
  - The photo print is rendered for real only where `tools/requirements-photos.txt` is installed
    (opencv-contrib: `cv2.saliency`); elsewhere a stand-in writes the 160×144 print and the summary line
    says so. Serve a kept scratch directory to a browser (route `config.json`, `assets/photos/9*.png`,
    `assets/voice/`) to see the result in the game.
- **The world map shows the stitched city** (issue #146): after the rooms are drawn, `tools/make_worldmap.py`
  renders each config `cities` entry with `node tools/play.js render <City>` — the room the game plays,
  woodland and seam patches included — and pastes it over the city's bounding box. **The train-only towns
  stand clear of that box in `devhouse.world`** (issue #174: Yukimura above Machi, Inaka and Osaka in a
  column west of it; they used to sit inside the box and showed as clearings in Tokyo's woods). The tool
  warns if a town is ever placed back inside (it is still redrawn on top), and `tools/test_game.js` fails.
  Widening the world costs nothing on the Map screen while it stays wider than about 1.47:1 - the
  overlay is height-limited. `world-map.json` keeps the same contract (one rect per room), so the "You" marker, NPC dots and map-click travel work as before. Regenerate
  `assets/map` with the tool whenever a district, `cities.<City>.backdrop` or `patch` changes.
- **World map without Tiled**: `tools/make_worldmap.py` uses `tmxrasterizer` when Tiled is installed and
  otherwise (or with `--pil`) draws the rooms itself via `node tools/play.js render`, which is also the
  "look at the render" step for a new room: `node tools/play.js render <Room> out.png [--scale .5] [--colliders]`.
- **Re-homing a placement** (issue #121): `python3 tools/blog_to_npc.py --rehome <NPC> <YYYY-MM-DD>
  "<Room> · <label>" [--dry-run]` (repeatable) moves an existing placement to another spot with no LLM call
  — `rehome()` hands the day's dialogue, photo, voice and `posts` to `apply()`, so the room left behind
  keeps a bare `present: false`, the new room gets a hidden base def if needed and later history is
  re-checked. Use it instead of hand-editing a cross-room move. Seven placements made on a station platform
  before #73, for posts about somewhere else, were moved this way (Karuizawa apple pie and Shirakawa-go to
  Yukimura, the Lake Biwa rides to Inaka, the castles to Machi's pagoda, the izakaya night and Hakata
  ramen to Market's 7-Eleven); the travel-day posts stay on their platforms. The cell is free for the
  whole stay (`occupied_during`: from that date until the NPC's next placement, or until a later trip or
  stay starts everyone from its base again — `trip_window`), not just on the day — history is not always
  written in date order — and `process_post` uses the same check.
  `test_blog_to_npc.py` also checks the shipped history: each NPC is in at most one room on any dated
  day, and no two share a cell.
- **Generated rooms stay regenerable** (issue #107): a room generator re-run on an unchanged world leaves
  `config.json` byte-identical, and `python3 tools/check_generators.py` fails when one would not. That
  holds for `generate_machi`, `_inaka`, `_yukimura`, `_osaka`, `_sapporo`, `_asahikawa`, `_konbinis`,
  `_discount_stores` and `_stations`, each run on its own:
  - a town generator ends with `b.finish()` (`roomgen.Builder`), which runs the picket-fence and
    solid-track passes itself — `fix_fences.py` / `seal_tracks.py` are the same code
    (`roomgen.picket_fences` / `roomgen.seal_tracks`) for a room named on the command line, and are no
    longer a step to remember after a town generator;
  - it keeps what it does not own from the room as it stands: NPCs (the blog pipeline's states), Machi's
    ad `signage`, and a 7-Eleven door wired by `generate_konbinis.py` (`roomgen.kept_door`; with none to
    keep, on a first build, the door is sealed until `generate_konbinis.py <Host>` runs). Doors are listed in
    the order the room already has them (`roomgen.kept_order`; the shop generators replace their door in
    place), so a first build followed by the shop generators also passes the check.
  So a generated room may be changed either way — edit the generator and re-run it, or make a surgical
  edit (`/adjust-game`, `stamp_prefab.py`) **and mirror it in the generator** — and the check tells you if
  the two have come apart. Never leave it failing: a generator that has drifted silently drops the hand
  edit the next time someone runs it. (That is what had happened to `generate_machi.py`: it wiped the blog
  NPCs, the signage and the stitched city's gate colliders, and resurrected the legacy `Konbini` room.)
  Ported rooms (Tokyo, Market, Park, Palace) have no generator; their map is the source of truth.
- `tools/generate_stations.py` keeps an existing station room's NPCs (the blog pipeline parks dated NPC
  states there), and `tools/seal_tracks.py` takes room names; a track cell with a road under it (Palace's level
  crossing) is left open.

### Stations and the departures board (issues #48, #104)

Config `stations` is the rail registry, written by `tools/generate_stations.py` from its `STATIONS` dict:
`label`, `town`, `train`, `board` / `arrive` / `trainCell`, plus the two fields that lay out the board:

- **`order`** - position on the departures board. It is the station's position in `STATIONS` (the
  registry itself is saved with sorted keys, so key order means nothing - that is how Asahikawa came to
  be pre-selected everywhere).
- **`parent`** - the station key of the city this one is a day trip from (Inaka and Yukimura ->
  `TokyoStation`, Asahikawa -> `SapporoStation`). One level only.

`src/StationPicker.js` builds the board with the static `StationPicker.board(stations, fromKey, cameFrom)`:
cities in `order`, each followed by its day trips indented and tagged `day trip`. The station you are at
is not a destination; it is left out unless it has day trips, in which case it stays as their grey,
unselectable `you are here` heading. A station with no `order` sorts last by label, and a `parent` that is
unknown, itself or itself a day trip is ignored, so bad data never hides a station. **Starting row**: the
station you last arrived from by train (`TrainTravel.cameFrom(roomKey)`, in memory for the session - the
way back is one press), else a day-trip station's parent city, else the first destination.

At most `StationPicker.MAX_VISIBLE` (7) rows show; a longer board scrolls (the `you are here` heading is
a row, so a city with day trips scrolls one station sooner). The selection pulls the window along
(`StationPicker.scrollTop`, which also keeps a day trip's city on screen above it), the mouse wheel moves
it a row, the arrows above / below the list page it on click or tap, and a press that starts on a row and
travels more than `DRAG_SLOP` drags the list instead of picking the row (that is why a row boards on
pointer-up, not pointer-down). A pointer scroll never leaves the selection off screen: it moves to the
nearest row in view (`StationPicker.clampSelection`), or to the row under a resting mouse. W/S or the arrows
wrap and skip the heading; SPACE/ENTER boards; ESC, or a click outside the panel, steps back. It is all
drawn in the usual 1280x960 overlay space at depth 2000-2003, so `UIScale` magnifies it on phones.

**Adding a station**: add it to `STATIONS` where it belongs on the board (with `parent` for a day trip)
and to `TOWN_DOORS`, then re-run `generate_stations.py`. `node tools/test_game.js` checks the real
registry's board. To see a long board without adding rooms, intercept `config.json` in playwright and add
fake `stations` entries (do not ride to them).

### Hokkaido: Sapporo and Asahikawa (issue #43)

Two generated towns reachable only by train (`SapporoStation`, `AsahikawaStation` in
`tools/generate_stations.py`; both sit detached to the north in `devhouse.world`). They are devhouse 3's
two bases: the trip's base cast stands in Sapporo on 18-24 Feb 2027 and in Asahikawa from the 25th (see
Trips; the generators keep a room's NPCs), and on any other date the rooms are empty unless the blog
pipeline has placed someone there.

- **Sapporo** (`tools/generate_sapporo.py`, 56x43) is the one town on a street GRID: two east-west streets
  (rows 20-22, 31-33) and three north-south (columns 14-16, 30-32 the station avenue, 44-46), `road-plain`
  asphalt where they cross (roads are ordinary walkable Floor tiles). North of the first street: the
  high-rise row + discount store (west), the station plaza, the **Clock Tower** on its paving and the
  konbini (`KonbiniSapporo1`). Between the streets: **Odori Park**, a strip of snow trees and lanterns with a
  path down the middle, closed at the east end by the **TV Tower**. South: houses on a lane and a
  frozen-pond corner. The high-rises stand shoulder to shoulder with a hedge closing the ground behind
  them, and both landmarks collide along their silhouettes (see their prefab comments): the Clock
  Tower is solid up to its pyramid roof (only the roof tip is walk-behind) and the TV Tower up to the top
  of its lattice (only the thin mast is), so the tower's shaft closes Kita-Odori's roadway at columns
  49-50 and you pass it on the north pavement. Nobody is fully hidden behind either landmark (on the pavement at (49-50,19) the foot of the mast covers half the player).
- **Asahikawa** (`tools/generate_asahikawa.py`, 42x32) is the small day-trip town: **ramen alley** (three
  machiya under red `ramen-banner` nobori), a frozen **river** running bank to bank with one timber
  **bridge**, and on the south bank a torii, the blue shrine and cottages. The river is laid by hand
  (`ice-pond-autotile` edge-n / center / edge-s rows, solid) because `Builder.pond` is two rows tall.
- **Art**: `tools/generate_hokkaido.py` (needs Pillow) draws the Clock Tower, TV Tower, bridge, banner and
  `road-plain` - at half size, pixel-doubled, in the GuttyKreum palette with a 1px ink outline, so they sit
  at the 2x scale of the building crops. They are not line-art placeholders. The LimeZu `Tileset_53_MV`
  clock tower was rejected (16px art - pixels twice the size - and more saturated). `--preview out.png`
  writes a contact sheet. It also derives the `dirt-snow-autotile` family (9 roles) from
  `dirt-outside-autotile` by swapping the green grass fringe for a snow bank - use it for dirt paths on
  snow ground (Asahikawa and Yukimura's shrine path do, #105) - and `gravel-snow-autotile` from
  `gravel-autotile` the same way (`SNOW_FAMILIES`), which the rail corridors of Yukimura, Sapporo and
  Asahikawa use (#125). `test_game.js` fails a snow-ground room that lays either grass-fringed family.
- **Flat sprites over water**: `Over Floor` and `Water` share one fixed depth, so a multi-cell sprite on
  `Over Floor` is drawn UNDER water tiles. The bridge therefore sits on `Non-Collidables` with
  `spriteMetadata.depthBias: -200` (written by `generate_hokkaido.py`'s `FLAT` table): above every ground
  layer, below everything Y-sorted, so the player walks on it. Its cells are simply left out of the
  river's colliders.
- **Konbini interiors per host**: `tools/generate_konbinis.py [Host ...]` - with host names it (re)builds
  only those hosts' stores (`generate_konbinis.py Sapporo`), leaving every other konbini room untouched.
  `generate_sapporo.py` re-seals the konbini door, so run it after every Sapporo regeneration. (The
  discount store's door is wired by `generate_sapporo.py` itself and survives a regeneration; its
  interior is `generate_discount_stores.py Sapporo`.)
- **Build order**: `generate_hokkaido.py`, `make_prefabs.py`, `generate_sapporo.py`,
  `generate_asahikawa.py`, `generate_konbinis.py Sapporo`, `generate_discount_stores.py Sapporo`,
  `generate_stations.py` (the towns fence and seal themselves - `b.finish()`), then
  `config_to_tiled.py Sapporo Asahikawa SapporoStation AsahikawaStation KonbiniSapporo1 DonTakoteSapporo`
  (it takes any number of rooms and fails, writing nothing, on a name that is not a room - #102) and
  `node tools/play.js lint <Room>` (lint reads the Tiled map).
- Blog NPCs can be sent to `the Sapporo Clock Tower`, `the Sapporo TV Tower`, `the bridge over the frozen
  river`, `ramen alley` and `the frozen pond` (`LANDMARKS` in `tools/blog_to_npc.py`), besides the generic
  shrine / torii / 7-Eleven / vending spots.
- A room missing from `assets/map/world-map.json` is fine: the Map overlay still opens (no dot, "you are
  here: <room>") and `TrainTravel.dirTo` treats it as x=0. Re-run `tools/make_worldmap.py` to add new rooms.

### Generic city buildings: high-rises, the discount store, machiya (issue #18)

Street buildings beyond the ported houses / konbini / shrines. Each is ONE sprite on `Collidables` wrapped in
a prefab (`building()` in `tools/make_prefabs.py`): solid from the ground up, with only the top two rows (the
roof line) walk-behind, as behind a house roof - so the player is never lost behind a tower. Doors are
sealed and lead nowhere, except the discount store's, which opens into its Don Takote shop floor (issue #91,
see Shop, Food and Drink).

| Prefab | Cells | Placed in |
|---|---|---|
| `highrise-yellow` (ochre office block) | 4x8 | Market (15,22), Palace (48,6) |
| `highrise-blue` (blue-grey office block) | 5x11 | Osaka (3,7) |
| `highrise-glass` (curtain-wall tower) | 4x10 | Osaka (42,29) |
| `highrise-apartment` (tiled-balcony flats) | 5x8 | Osaka (3,30) |
| `midrise-apartment` (the same block, two floors lower) | 5x6 | Palace (40,10), feet on the forecourt edge |
| `discount-store` (the "Don Quijote") | 5x8 | Market (46,22), Osaka (13,9) by the Dotonbori arch, Sapporo (16,11) - each with an interior |
| `machiya-black` / `-red` / `-blue` (Kyoto townhouse) | 5x5 | Machi (4/9/14,17): the old-town lane |

- **Art** is assembled by `tools/extract_city.py` from the GuttyKreum RPG Maker tile kits in `../Assets/GuttyKreum`
  (Osaka `GK_Osaka_C_2`, Dotonbori `GK_DB_B`, Japanese City `GK_JC_C_2`) - a kit holds a roof cap, one window
  floor, a ground floor, roof edges..., so the script repeats floors / middle columns to get the size wanted
  (change the arguments in `BUILDINGS` for a taller or wider block; `--preview out.png` writes a contact sheet).
  **Scale is 2x**: one 32px RPG Maker tile = one 64px cell, the scale of every ported building (doors are one
  cell wide). The Dotonbori arch / ferris wheel are deliberately 4x landmarks - do not copy that for buildings.
  Do not mix in the LimeZu `Modern_Exteriors` pack (different, more saturated style).
- **The discount store** carries no real branding, like the ad pool: its sign is drawn by `extract_city.py`
  with `tools/generate_ads.py`'s text helpers - ドン・タコーテ ("Don Takote"), yellow board, blue band, a red
  octopus. It needs a Japanese font from `generate_ads.find_font()` (macOS system fonts).
- **Placing one**: generated rooms `b.stamp('highrise-glass', x, y)` in their generator (Osaka does). Ported
  rooms and Machi use **`tools/stamp_prefab.py <Room> --add <prefab> x y [--remove <prefab> x y] [--dry-run]`**,
  which refuses to write if the prefab overlaps another standing sprite, lands on a solid cell, covers a
  transporter or any dated NPC position (under its solid rows or its walk-behind roof rows), or cuts walkable
  cells off from the room's transporters (flood-fill). To change a building prefab's collision, `--remove` it
  from the ported rooms first, re-run `make_prefabs.py`, then `--add` it back. Then
  `config_to_tiled.py`, `play.js lint` (it reads the Tiled map), `make_worldmap.py`.
- Blog NPCs can be sent to `the Don Takote discount store` and `the old-town lane` (`LANDMARKS` in
  `tools/blog_to_npc.py`).

### Street accessories: traffic lights, zebra crossings, kerbside props, no bins (issue #19)

All art comes from `tools/extract_street.py` (run it before `make_prefabs.py`); every piece is a prefab.

| Prefab | Cells | What / collision |
|---|---|---|
| `traffic-light` | 1x3 | Japanese signal: horizontal 3-lamp vehicle head + pedestrian head + push button on one pole. One sprite on `Collidables`: base cell solid, the two cells above walk-behind |
| `crossing-h` / `crossing-v` | 1x3 / 3x1 | zebra crossing over a horizontal / vertical road, flat `Over Floor` paint, walkable. Origin = the road's top kerb row / left kerb column; stamp two or three side by side for a wider one |
| `utility-pole` | 1x3 | wooden pole with a transformer; base solid |
| `road-mirror` | 1x2 | orange convex mirror; base solid |
| `bus-stop`, `bicycle-blue`, `bicycle-orange`, `scooter-grey`, `scooter-red`, `traffic-cone` | 1x1 | solid |

- **Traffic-light art is drawn, not extracted** (`traffic_light()` in `extract_street.py`): no GuttyKreum sheet has a
  signal, and the only one in the repo (LimeZu `Modern_Exteriors`, `Tileset_2_MV`) is a western vertical head in 16px
  art - at game scale its pixels are twice the size of everything around it. The drawn one uses the GuttyKreum prop
  palette on the same 2x grid. Four frames, four sprite keys: `traffic-light_0_0` (vehicles green / red man - the one
  maps place), `-amber`, `-stop` (vehicles red / green man), `-stop-blink` (green man dark).
- **The cycle** (`src/TrafficLights.js`, `scene.trafficLights`): purely decorative, gates nothing. Every 200ms it
  swaps the texture of every signal sprite in `roomManager.floorSprites` to the frame of one shared wall-clock cycle
  (`TrafficLights.PHASES`: go 6s, amber 1.6s, stop 5.2s, blink 2.4s), so all signals agree and the pedestrian lamps
  run opposite the vehicle lamps. It keeps no room state and needs no room-change hook - it re-reads the loaded tile
  sprites whenever that array is replaced, and checks for that every frame so a freshly loaded room never shows a
  stale green. At night it re-lights the lit lamps with one additive Graphics above the DayNight grade
  (`TrafficLights.LAMPS` = the lamp rectangles per frame; keep it in step with `traffic_light()` in
  `extract_street.py` if the art changes). Test hooks: `trafficLights.phase()` and `trafficLights.clockOffset` (ms).
- **Crossings match the road** because they are cut from the same sheet as the `road-edge-*` / `road-div-*` tiles
  (Temples & Shrines `GK_TS_A5`). The top / left kerb tiles are the bottom / right ones flipped: the sheet's own
  have a heavily worn second stripe that reads as a glitch in game. The Japanese City `GK_JC_A5_2` crossings are on a much darker asphalt - not those.
- **Where**: signalled crossings in Tokyo (south road at the palace path, west road), Market (north road on the
  temple axis, east road, south road at the torii), Palace (east road), Park (south road, east road) and Osaka
  (the main street, between the arch and the bridge); props scattered through those, and Machi.
- **Osaka's roads** (issues #106 / #151, `generate_osaka.py`): the **main street** is columns 23-26 from row
  11 to the avenue - `road-edge-left`, `road-lane-left`, `road-lane-right`, `road-edge-right` - with the dark
  brick either side as its pavement. It ends square a row below the station door (`road-corner-nw`, two
  `road-edge-top`, `road-corner-ne`), runs under the arch and over the bridge, and meets **Canal-side
  Avenue** (rows 25-27, the standard `road-edge-top` / `road-div-horizontal` / `road-edge-bottom`, pavements
  on rows 24 and 28) at a T-junction whose box is `road-plain`, as in Sapporo. The avenue runs from one edge
  of the map to the other, through a gap in the border hedge at both ends. The street is four cells wide,
  not the usual three, **on purpose**: the arch's opening is four cells and the arch is the landmark, so
  the road keeps its axis and gets its centre line from the two lane tiles, which carry half the line each
  on their shared edge. Those, and the mitred two-kerb corners (`road-corner-nw|ne|sw|se`), are derived
  from the sheet's own road tiles by **`tools/make_road_tiles.py`** (Pillow; no new art). The crossing is the `crossing-v`
  tiles laid by hand with the middle one repeated (the prefab is three cells). It is on row 18 and
  both signals stand just south of it at the bridgehead (bases `(22,19)` and `(27,19)`): north of it their
  heads would be lost in the arch's side boards. The pavement is one cell either side of the road
  but two on the bridge (columns 21-22 and 27-28, rows 19-23; the canal's water stops at columns 20 and 29), so
  there is a way round the signal posts without stepping into the road (issue #139). The bus stop stands on the kerb at `(21,11)`.
  Nothing is placed in the rows / columns where Tokyo, Market, Palace and Park overlap (`devhouse.world`).
  A signal on the north side of a road needs three free rows above the kerb - Market's north road and Tokyo's are
  too close to the map edge, so Market's crossing has both signals on its south kerb.
- **Placing more**: `tools/stamp_prefab.py <Room> --add traffic-light x y` (x,y = the TOP cell; the base is two rows
  down), `--add crossing-h x y` etc.; generated rooms `b.stamp()` them (the Osaka / Machi placements are mirrored in
  their generators).
- **No rubbish bins, anywhere** ("definitely no rubbish bins!!" - Japanese streets have none). The `office-bin`
  sprite is retired (PNG and `spriteMetadata` deleted in #109; its `tilePalette` slot stays as a dead entry because
  the palette is positional - never place it): konbini corners get a water dispenser / plant (`generate_konbinis.py`) and the Izakaya
  seats are `izakaya-stool_0_0` (drawn by `extract_street.py`; the stools are furniture - the drinking game's
  `triggerCells` are the table cells and the bar still sells). `node tools/play.js lint` (tools/world-model.js) enforces it per room, and `play.js check` across ALL
  rooms and reports an ERROR `rubbish-bin` for any placed tile whose key or tile name is a bin / dumpster / trash
  can (`BIN_RE`), whatever `--room` was asked for. Do not extract the bins / dumpsters in the asset packs.

## Asset Generation

Python scripts in `tools/` directory generate 64×64 PNG tiles saved to `assets/`:
- `generate_tile.py` - Player tile (yellow border) → `assets/single-tile.png`
- `generate_npc_tile.py` - NPC tile → `assets/npc-tile.png`
- `generate_transporter_tile.py` - Transporter tile (green border) → `assets/transporter.png`
- `generate_object_tile.py` - Object tile (black border) → `assets/object-tile.png`
- `generate_grid.py` - Background grid → `assets/background-grid.png`

Run with: `python3 tools/generate_<type>.py`

`tools/generate_cooler_art.py [--preview out.png]` draws `office-fridge_0_0`, the konbini's upright
glass-door drinks cooler (issue #140): 1x2 cells, fully procedural (no source image or font, so a re-run is
byte-identical), in the steel greys and glass blues of the `office-shelf-*` / `office-freezer` furniture
and, like them, drawn at half size and pixel-doubled. Size (64x128) and anchor (0.5, 0.25) are fixed by the
maps that already place it - change the art, not the footprint. Needs Pillow.

## Key Implementation Details

### Collision Detection
All intermediate cells in movement path are checked for:
- Room boundaries (polygon containment check; in a stitched city: inside any district's boundary)
- Collision-layer tiles (`roomManager.isBlocked(x, y)` — a set lookup; collider markers have no sprite)
- Objects (static obstacles)
- Stationary character positions
- Moving character destinations
- Path crossing (swap detection)

### Character Sprite Positioning
Sprites are centered at: `gridPos * GRID_SIZE + GRID_SIZE/2`

### Input Handling
The whole game runs on WASD/arrows + SPACE/ENTER + SHIFT, with ESC as the single
system key — no other bindings (no T shortcut, no ,/. month keys). Touch controls
synthesize the same keys (d-pad → WASD, A → SPACE, B → ESC, sprint pill → SHIFT).
- **Movement**: WASD or arrows move 1 cell, Shift doubles speed (not distance)
- **Time Travel**: arrows / WASD move a day or a week, SHIFT + left/right jumps to the previous / next trip, SHIFT + up / down to today / the game's day,
  SPACE/ENTER travels, ESC closes
- **Menu / overlays**: ESC toggles the menu (and closes any overlay), W/S or ↑/↓ navigate, SPACE/ENTER activates
- **Dialogue**: SPACE/ENTER advances, ESC closes
- **Title screen**: SPACE/ENTER/ESC or a tap starts the game (`?notitle=1` skips the screen)
- **Intro**: SPACE/ENTER or a tap turns the page, ESC skips (`?nointro=1` skips the first-visit intro)
- **Character creator**: ↑/↓ pick a row, ←/→ change it, ENTER/SPACE plays, ESC cancels. RANDOM is the last
  row (←/→ re-rolls, or click/tap it) — it has no key of its own (#53). ENTER/SPACE plays on that
  row too (deliberate: the roll you like is kept with the usual key; if ENTER rolled there it would
  throw the look away)
- **Hidden debug menu**: triple-press backtick (``` within a second) — rows for
  the grid view/inspector, the N/E/X flag keys, map-click travel, a time-of-day
  pin (AUTO/day/dusk/night/dawn, same effect as `?tod=`), exact wallet amount
  (prompt), and noclip (all default off, persisted in localStorage). Deliberately
  absent from How to Play. Map-click travel on the menu's Map overlay
  only works when its toggle is on.
- Input blocked when `player.isMoving` or `isTransitioning`
- Supports diagonal movement with simultaneous key presses

### Small Viewports and Touch (issues #49, #50, #57, #81, #85, #110-#114, #116)
The game always renders 1280x960; everything below is about showing that on anything else. A
1280x960-or-larger window driven by mouse and keyboard is untouched by all of it (pixel-identical).

**The layout rule, per kind of window** (canvas size is never traded for controls):

| window | canvas | touch controls | world | text floor |
|---|---|---|---|---|
| desktop (>= 1280x960) | 1:1 or a whole multiple, centred both ways | none | as authored | as authored |
| small desktop / laptop window | exact fit, centred | none | as authored (never zoomed: all 20 x 15 cells stay in view) | overlays magnified to desktop size or the canvas; HUD >= ~11 CSS px |
| touchscreen laptop | same as the row above it would get | hidden until the screen is touched, gone again on a key press; when up, translucent over the canvas's bottom corners | same | same; keyboard wording until touched |
| tablet, 4:3-ish landscape | fills the window | translucent over the bottom corners (0.75x) | as authored | overlays kept clear of the controls |
| landscape phone | full height | in the side bars (0.8-1x); on phones under 400px tall, 0.6x and partly over the corners | 2x (10 x 7.5 cells) | HUD ~11 CSS px, hint lines >= 10, body text 9-10 on the tallest panels |
| portrait phone / tablet | fills the height above the controls; the window crops its sides (a tall slice, >= 560 canvas px wide) | under the canvas, full size | as authored in the slice (about 9.5 x 15 cells) | HUD ~11, hint lines >= 10; panels wider than the slice shrink to it (the 920px intro lands at ~7 CSS px body text) |

- **Canvas layout — `src/systems/Viewport.js`.** `Viewport.apply(game)` is the only place the canvas
  style is written (`src/game.js` calls it at boot, on window resize, on rotation and on
  `visualViewport` resize; `TouchControls` when its controls come or go). The canvas is
  `position: fixed` from the stylesheet on: a 1280px canvas in the page flow makes a phone browser
  widen its layout viewport, after which `window.innerWidth` is not the screen. Whole-integer scale
  when the window is big enough, exact fit otherwise, centred both ways. `Viewport.layout()` then
  places the controls — `portrait`, `side`, `bottom` or `over`, in that order of preference (see the
  file header) — and reports two things in canvas px that UIScale makes the game fit:
  `crop` (how much of the canvas is off each side of the window, portrait only) and `insets` (how far
  the controls reach in over the canvas, `over` only). `Viewport.CONTROLS` holds the controls'
  footprint — keep it in step with the stylesheet in `TouchControls._build`. `Viewport.current` is
  the layout in force.
- **Three layers, three cameras — `src/systems/UIScale.js` (`scene.uiScale`).** Nothing is given a
  second layout; instead, whenever the canvas is shown below 1:1, is cropped, or has controls over
  it, the picture is split by depth and each layer is drawn by its own camera:
  - **World** (everything else, main camera): on a phone or tablet only (`uiScale.handheld()`: a
    finger is the main pointer, or `?touch=1` — decided once per session, so a mouse/keyboard window
    of any size keeps all 20 x 15 cells and a touchscreen laptop does not jump when touched), zoomed
    in quarter steps towards 0.8x of authored size on screen, at most 2x and never to fewer than 8
    cells across (`worldScale()`). The follow deadzone is divided by the zoom, and its width scaled
    to a cropped (portrait) view, so the player keeps the same share of the view ahead of them. Use
    `camera.worldView` / `pointer.worldX`, never `scrollX + width`, and do not assume
    `cameras.main.x === 0`. A stitched city's chunk streaming (`RoomManager.streamRect`) and the
    lamp-halo cull (`DayNight.cullGlows`) already measure the zoomed, cropped view (centre
    `scrollX + width / 2`, half-size `width / 2 / zoom`); tiles streamed in mid-walk get their camera
    the same frame, because the split below is re-applied to the whole display list on `prerender`.
    A room whose `boundary` is narrower than that view (a konbini on a phone) is held centred in it:
    `GameScene.applyRoomBounds` narrows the camera bounds to the view around
    `roomManager.contentColumns()`, and runs again on scene event `'worldviewchange'` (zoom or view
    width changed). With the whole canvas in view the bounds are the room's, as always.
    The room-change fade (`RoomManager.switchRoom`) runs on the camera drawn last — the `'ui'`
    camera while the split is on — so it covers the HUD and overlays as the single camera's fade does.
  - **HUD** (depth 1000-1999 with scroll factor 0, `'hud'` camera): magnified from the top-left by
    `hudScale()` (towards 0.7x on screen). That leaves the bar less width, so `GameScene.layoutHUD()`
    lays it out for `cameras.main.width / hudZoom`: it drops the game's title, then wraps date and
    wallet onto a second row. `scene.hudWidth` / `scene.hudBarHeight` are the bar's size in HUD
    coordinates (the shop's effect chips hang off them); scene event `'hudscalechange'` says when to
    lay out again. Anything new on the HUD goes at depth 1000-1999, scroll factor 0. The date,
    wallet and `menu` buttons take a tap anywhere in the height of their row (`layoutHUD` sets their
    hit areas), not just on the glyphs, which are about 11 CSS px tall on a phone.
  - **Overlays** (depth >= 2000, `'ui'` camera): zoomed in on the overlay's content (everything
    except full-screen dimmers) until it is as big as on a desktop or fills its space — the view less
    a 12px margin, less the controls' `insets` (fitted between the controls or above them, whichever
    is bigger). A box too big for a space that is cut down (insets, or a cropped view) is shrunk to
    fit; otherwise overlays are never shrunk. Dimmers are stretched back over the whole view.
  - On a portrait phone all three cameras get the visible slice as their **viewport**, so
    `cameras.main.width` is the visible width (612 at 390x844) and `x` is not 0. Overlays built while
    that is so centre themselves in it; ones built for another width (the persistent menu and
    dialogue, anything left up while the phone is turned) are re-centred and fitted like any content.
    Read `cameras.main.width` when you draw, not once at construction, unless the thing is a
    full-screen dimmer.

  Rules this puts on overlay code:
  - Overlays live at depth 2000+, HUD at 1000-1999, world below. A new overlay gets all of the above
    for free.
  - Draw panels with Graphics `fillRect` / `strokeRect` / rounded rects / circles / triangles (their
    extents are tracked — Graphics has no bounds of its own) or any object with `getBounds()`.
  - Do not read raw `pointer.x` / `pointer.y` against overlay coordinates: use the handler's
    `localX` / `localY` (the map's click-to-travel does).
  - DOM placed over an overlay goes through `scene.uiScale.project(x, y)` and `.zoom`, and listens
    for the scene events `'uiscalechange'` AND `'inputmodechange'` (the character creator's name
    input does — from the layout the panel was drawn with, not a fresh one). The second matters on a
    big touch-capable window: the controls coming or going move the canvas with no window resize and
    no zoom change.
  - UIScale moves and scales three kinds of overlay object for the frame and puts them back
    (`UIScale.put` / `home`): dimmers, floats and hint lines. Do not tween the position or scale of
    those; alpha is fine.
  - Two per-object opt-outs: `obj.uiScaleSkip = true` for something at depth 2000+ that is NOT an
    overlay (the debug grid, flag labels and stats text — it stays with the world, or with the HUD
    if its scroll factor is 0); `obj.uiFloat = true` for something magnified but belonging to no
    overlay (the shop toast): it stays where it was authored on the canvas — except that a float
    which would cover the open overlay's content slides into the strip under (or over) the panel
    when one is tall enough to hold it (`UIScale.clearOf`). When neither is, the overlay gives up a
    strip under itself for it and keeps it until it closes, so a toast never sits on the panel's
    hint lines and the panel does not pulse.
  - **Hint lines never go below 10 CSS px** (`UIScale.MIN_HINT`): any overlay Text whose string came
    from `Hints.text` is scaled up in place (to at most 1.6x, and the panel's width) when its panel
    could not be magnified enough. Body text has no floor — keep it at 18px or more.
  - An overlay that already fills the canvas cannot be magnified; its text can use
    `scene.uiScale.textSize('14px')` instead (the map's labels do — up to 1.6x). The HUD bar shows
    through a dimmer and is taller where it is magnified, so anything such an overlay draws near the
    top edge needs its own background there (the map's title gets one when `uiScale.hudZoom > 1`).
- **Touch in use, not touch available — `src/systems/TouchControls.js` (issue #116).** The controls
  show while touch is the input being used: a device whose main pointer is a finger
  (`(pointer: coarse)` — phones, tablets) starts with them, a touchscreen laptop does not; the first
  real `touchstart` anywhere brings them up and a real (trusted) press of a game key outside a text
  field takes them away, as often as the player switches. `?touch=1` forces them on.
  `touchControls.enabled` is "on screen now"; `setEnabled()` re-lays the canvas, rewords every hint
  on screen (`Hints.refresh`), redraws the intro's controls page and emits the scene event
  `'inputmodechange'`. Never test for touch capability anywhere else.
- **Hint wording — `src/utils/Hints.js`.** Write the hint for the keyboard and pass it through
  `Hints.text(scene, 'SPACE/ENTER: start · ESC: leave')`; with touch controls on it comes back as
  `A: start · B: leave` (SPACE/ENTER → A, ESC → B, ↑/↓ and arrows / WASD → d-pad, ←/→ → ◀ ▶, SHIFT → sprint, click → tap).
  `{ tap: true }` for overlays where a tap anywhere confirms (dialogue, intro): `TAP or A`. Use
  `Hints.touch(scene)` rather than testing `touchControls.enabled`. Never hand-write a touch string:
  every string `Hints.text` hands out is remembered, which is how a line already on screen is
  reworded when the input changes and how UIScale knows a hint line when it sees one. A hint must be
  its own Text object, set to exactly what `Hints.text` returned.
- **A touch on a control stays on the control.** Phaser listens for touches on the whole window, so
  a tap on the A button used to reach the overlay underneath as well (dialogue advanced twice, the
  intro skipped a page, B closed and reopened the menu). `TouchControls._own` default-prevents the
  touch events on every control, which Phaser's window handlers respect. Any new DOM control over
  the page needs the same.
- **Testing**: playwright contexts with `hasTouch` AND `isMobile` (without `isMobile` the layout
  viewport never misbehaves the way a phone's does) at 844x390, 667x375, 390x844, 1024x768 and
  1366x1024; `page.touchscreen.tap` or CDP `Input.dispatchTouchEvent` for real touches (a d-pad press
  needs a held touch, not an instant tap). Headless Chrome with `hasTouch` reports a coarse pointer,
  so a touchscreen laptop needs `matchMedia('(pointer: coarse)')` stubbed to false. `?touch=1` shows
  the controls with a mouse. `tools/test_game.js` covers `Viewport.layout`, `UIScale.fit`, the hint
  registry and `TouchControls.touchFirst` without a browser.
