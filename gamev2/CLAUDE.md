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

`node tools/test_game.js` runs the game's own decision code in Node, with no browser: which train a
station parks, the departures board's order and scrolling, room display names, the dialogue hint wording,
touch buttons cancelling their touch, which post a dialogue line is captioned with, the default game date.
When a fix lives in a Phaser-side class, pull the decision into a static function there and add a case.

## Studio

`studio/` is a read-only view of the whole world for developers, served at `/studio/` (locally
`http://localhost:8000/studio/`, live at `game.devhou.se/studio/`). It lays every room out together and
overlays collision, unreachable cells, teleports (arrows to their targets), train links, interactions and
where each person stands on a chosen day. Click a cell for its tiles, what a bump does, the NPC's lines
and photo, and the `play.js` command that puts you there. Maps are still edited in Tiled.

It has no logic of its own: `tools/world-model.js` (rooms, collision, NPC dates, interactions, the
problem survey) is shared with `tools/play.js`, so the page and the terminal tool always agree.

## Architecture

### File Structure

- `index.html` - Entry point, loads Phaser CDN and game scripts from `src/`
- `config.json` - JSON configuration file defining game constants, rooms, NPCs, and objects
- `tiled/*.tmj` - Room maps, authored in the Tiled editor (the map source of truth at
  runtime — see `tiled/README.md`; config.json's room layers are only a fallback)
- `src/game.js` - Phaser game configuration (viewport: 1280×960, physics setup)
- `src/systems/Viewport.js` - Where the canvas sits in the window and how big the touch controls are (see Small Viewports and Touch)
- `src/systems/UIScale.js` - Magnifies overlays when the canvas is shown smaller than 1:1 (see Small Viewports and Touch)
- `src/utils/Hints.js` - The one helper that words key hints for keyboard or touch (see Small Viewports and Touch)
- `src/utils/JapaneseFont.js` + `fonts/` - The pixel fonts, and the Japanese face added to each of them (see Fonts and Japanese Text)
- `src/GameScene.js` - Main game scene (room system, HUD, input handling, collision)
- `src/Character.js` - Character movement class with grid-based tweening
- `src/DialogueManager.js` - NPC dialogue system with multi-line conversations
- `src/utils/Interactions.js` - The one table of what a bump opens (shops, ponds, clocks, the drinking
  table). `Shop`, `Fishing`, `DrinkingGame`, `GameScene` and `tools/play.js` all read it; add a rule here
  rather than a tile-name check in a feature file
- `src/MenuManager.js` - In-game menu system (ESC key toggle)
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
- `npcWanderRadius`: 2 cells from NPC spawn point

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
  - **Default game date** (`defaultGameDate()`, issue #54): the trip is the set of dated days in the
    config (`contentChangeDates`, handed over by `setTripDates(config)` at the top of `GameScene.create()` —
    nothing is hard-coded). While today is between the first and last of them the game date is today.
    Outside the trip, today is mapped onto a trip day: days since the day after the trip's last day,
    modulo the number of trip days, indexes the sorted list (the day after the trip ends is its first day
    again) — so a visitor with no `?date=` always opens on a day that has posts, and the next real day
    shows the next trip day. The default is fixed when the config loads (`bootToday`), so a session left
    open past midnight keeps the day its NPCs were resolved for. On most trip days nobody is in the start room (Tokyo); they are in the
    neighbouring rooms. The HUD shows that date. `?date=` and Time
    Travel always win; `setGameDate()` drops the param only for the date a clean URL already gives, so
    picking today's real date after the trip is an explicit `?date=` like any other. `tools/play.js`
    and the studio open on the same day (`WorldModel.defaultDate()` calls `defaultGameDate`).
- `objects`: Array of static obstacles with position (absolute or offset from center) that block movement
- `transporters`: Array of teleport points with position, targetRoom, and target position

Position system supports both absolute grid coordinates (`gridX`/`gridY`) or center-relative offsets (`gridOffsetX`/`gridOffsetY`).

Room transitions use camera fade effects (250ms fade out, 250ms hold, 250ms fade in) and block input during transition via `isTransitioning` flag.
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
  106,0); the 16 hidden seam transporters (target = a sibling district) are dropped; `RoomManager.rooms`
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
  instead of scanning every sprite). A city (~25k tiles with the woods) is **streamed**: records are
  bucketed in 4-cell chunks and only those within 3 cells of the view have a sprite
  (`updateStreaming`, every frame; retired sprites are pooled OFF the display list), about 1,100 at a time versus ~4,300 for the
  old Tokyo room. `floorSprites` is therefore "the sprites that exist now" — read `tileRecords` /
  `standingArt()` when you need the whole room (AmbientBoats does). Night lamp halos are culled the same
  way (`DayNight.cullGlows`). A held key against a wall re-runs the bump checks (`GameScene.checkNPCInteraction`,
  whose shop check scans every tile of the room) at most every 150ms for the same cell, not every frame — in a stitched city only; every other room
  (and all of `?stitch=0`) checks every frame as before.
- **Systems that re-read the room** — `TrafficLights` rebuilds its signal list whenever `floorSprites` is
  replaced (every chunk change), so signals streamed in are put on the current phase before they scroll into
  view and its night glow follows them; `UIScale`'s overlay camera re-filters the display list every frame it
  is up, which covers sprites coming back from the pool; `Intro.whereFriendsAre` asks `roomManager.npcsIn(room)`
  (a district's own `rooms[...].npcs` is empty once it is stitched).
- **Tools** — `tools/play.js`, `tools/world-model.js` (lint / render / check) and `/studio/` model rooms from
  `config.json` + the `.tmj` files and do not stitch: there Tokyo is still five rooms joined by the 16 seam
  transporters, i.e. what `?stitch=0` plays. `play.js check` / `lint` therefore keep guarding the districts
  one map at a time; the stitched room itself is only checked by `tools/sync_cities.py --check` and the game.
- **`?stitch=0`** is the safety valve: no cities, the five districts are separate rooms joined by the fade
  transporters exactly as before. `?cull=0` keeps stitching but creates every sprite (for measuring).
- **Adding a district / a second city**: place the map in `devhouse.world` so the shared road lines up,
  add it to `cities.<City>.rooms`, run `tools/sync_cities.py` and `tools/make_worldmap.py`. Keep the hidden
  seam transporters in the maps — `?stitch=0` and the tools still use them.

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
- **`AmbientBoats`** - any room with straight moat tiles (today: the Tokyo moat) gets a boat. A "run" is a
  line of consecutive cells holding the same plain `moat-<north|south|east|west>` tile; `-rocks` tiles,
  corner pieces and gaps end a run, so a boat never crosses rocks, the bridge gap in the south moat or the
  stone bank. Runs too short for a boat to travel `MIN_TRAVEL` are dropped. The open-water strip inside the
  tile is measured from the tile image itself (`waterBand`: the longest stretch of the dominant colour
  across the middle of the tile), so no per-tile offsets are hard-coded. A boat fades in at one end of a
  run, drifts to the other at `SPEED` with a small bob and fades out - it cannot leave by the screen edge
  the way a train does. Runs with a boat's length of water on camera (below the HUD bar) are preferred.
  Depth is `calculateLayerDepth(1) + 1`: above the flat ground/water layers, below everything Y-sorted.
  Because scenery standing on the near bank is drawn over the water, `clearWater()` narrows each run's band
  to the lanes that room sprites of higher depth leave in view (a lane covered for more than `COVER_LIMIT`
  of the run is hidden) and the run is dropped if what is left is narrower than a boat. That is why Tokyo's
  north moat has no boats: the `blue-wall-short` palace wall hides the lower half of its channel. Tokyo ends
  up with 8 runs (5 south, 1 west, 2 east). A tree crown overhanging one end of a run is allowed.
- **Boat art is procedural** (`AmbientBoats.buildTexture`): no boat sprite exists, so each livery
  (`AmbientBoats.LIVERIES`: `wood`, `lacquer`, `white`) is drawn to a canvas on the tile art's 4x pixel
  grid, once per facing, under the key `boat-<livery>-<right|left|down|up>`. `ensureTexture()` only draws a
  key that is not already loaded, so real art replaces it by loading a sprite under the same key (keep it
  within `AmbientBoats.size()`, or update `ART`, since run fitting uses that size).
- **Testing** - both expose `cross()` to send one immediately (a no-op in a room with no track / no water):
  `game.scene.keys.GameScene.ambientTrains.cross()` / `.ambientBoats.cross(run, dir, livery)` (all optional;
  `run` is an entry of `ambientBoats.runs`, `dir` is `1` or `-1`). A new water tile family needs its name
  added to `AmbientBoats.WATER_TILE`; ponds are not waterways.

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
  untouched and a vertically centred Text does not move. The HUD room name, the Character screen rows and
  the created player's name label use it (#155); the other overlay `text()` helpers show Latin only today.
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
  (it refuses to seal a cell holding a transporter or a dated NPC). Keep NPC spots and
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
1. **Welcome to devhouse** — the friends (named from `CharacterSelect.lineup(config)`, the same list the cast row draws), the
   Japan trip, NPC lines coming from the trip's blog posts, and the HUD date picking the day ("Time Travel
   in the menu" to visit another day of the trip — the game always opens on a trip day, see the default
   game date under `npcs`).
2. **How to play** — move / sprint / interact / talk / menu drawn as keycaps (the interact row also
   lists what a bump starts: people, shops, trains, the izakaya); when
   `touchControls.enabled` the same rows are drawn as the on-screen d-pad, sprint pill and A / B buttons,
   plus a one-line keyboard reminder (touch controls are also on for touchscreen laptops).
3. **Where to start** — there is no quest system, so it points at real things: the friends (`whereFriendsAre()`:
   "around Tokyo" when one of them is in the start room on the game date, otherwise the rooms they are
   in that day are named — on most trip days Tokyo is empty), exploring, and Paint the Board (with the
   live progress bar from `achievementManager`).

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
`CharacterSelect.lineup(config)` by the title line-up and the intro's cast row ONLY. A listed name with no
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
  side and port it to the other). Both carry four marked `TIDY` rules that remove
  the artefacts of a plain band cut between different donors: holes where the top donor shows its own trousers in the torso band
  (damian's hem), the stray outline of the head donor's own high sleeve (james, side frame 1), mouth-interior
  pixels recoloured as hair (dylan — a moustache that flickers with the walk cycle), and an open shoulder
  line where the head donor's shoulders are narrower than the top worn.
- **`dylan` as a top donor**: his shirt is a two-teal checker (both teals are in `DONORS.dylan.top`), so a
  recolour keeps the checker as two shades. It is solid: a unit test keeps every donor sprite hole-free.
- **Replacing an interim set with real art**: drop the ten hand-drawn PNGs over the generated ones (same file
  names, same 64x64 template as the rest of the cast) and delete that name from `LOOKS`, or the next run
  overwrites them. Nothing else changes. Generated sets are cast, not creator donors (`DONORS` holds the
  measured palettes of the hand-drawn five); a hand-drawn replacement can be added there.
- **Base NPCs** come from the same tool (`HOME`: room, cell, two placeholder lines that state no facts about
  anyone). They are added only while the room has no NPC of that name, so later edits and the blog pipeline's
  states are never undone. All three stand in Sapporo — Khoi by the station house (38,8), Sam on the Odori
  park path (21,27), Xander on the Clock Tower plaza (35,17) — and are undated, so they are there on every
  game date until their first post moves them.
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

- **Osaka** (`tools/generate_osaka.py`, 50x40) is a generated town reachable only by train, like Yukimura:
  station house -> arch over the main street -> the canal bridge -> Tsutenkaku on its plaza, with the ferris
  wheel on the north bank. The main street is the town's one asphalt road (issue #106, see Street
  accessories) and the discount store by the arch opens into `DonTakoteOsaka` (issue #91, see Shop). The tower stands on the street's axis, so a shrub garden fills the ground behind
  it and the street forks round (otherwise the player walks hidden behind the sprite for ten cells); the
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
  one to the landmark's standing cell that can be walked to from one of the room's transporters, so a
  landmark inside a fence (Market's fox statues) puts its visitor outside it. `python3
  tools/test_blog_to_npc.py` checks all of this over every room in `config.json`: add a room or a
  landmark and it tells you if a spot is mislabelled, unreachable, or lands on a station's doors.
- **World map without Tiled**: `tools/make_worldmap.py` uses `tmxrasterizer` when Tiled is installed and
  otherwise (or with `--pil`) draws the rooms itself via `node tools/play.js render`, which is also the
  "look at the render" step for a new room: `node tools/play.js render <Room> out.png [--scale .5] [--colliders]`.
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
`tools/generate_stations.py`; both sit detached to the north in `devhouse.world`). Base rooms have no NPCs -
the blog pipeline places people there.

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
  `generate_stations.py`, `fix_fences.py Sapporo Asahikawa`, `seal_tracks.py Sapporo Asahikawa`, then
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
| `highrise-glass` (curtain-wall tower) | 4x10 | Osaka (42,22) |
| `highrise-apartment` (tiled-balcony flats) | 5x8 | Osaka (3,24) |
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
- **Osaka's road** (issue #106, `generate_osaka.py`): the main street's middle four columns (23-26, rows 11-22)
  are asphalt - `road-edge-left`, two `road-plain`, `road-edge-right` - with the dark brick either side as its
  pavement; it starts a row below the station door and ends at the tower's garden. It is four cells wide, not
  the usual three, because the arch's opening and the tower's archway are both an even number of cells, so
  only an even road sits on their axis; it therefore has no centre line, and its crossing is the `crossing-v`
  tiles laid by hand with the middle one repeated (the prefab is three cells). The crossing is on row 18 and
  both signals stand just south of it at the bridgehead (bases `(22,19)` and `(27,19)`): north of it their
  heads would be lost in the arch's side boards. The pavement is one cell either side of the road
  but two on the bridge (columns 21-22 and 27-28, rows 19-22; the canal's ponds stop at columns 20 and 29), so
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
- Collision-layer tiles (`roomManager.isBlocked(x, y)` — a set lookup)
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

### Small Viewports and Touch (issues #49, #50, #57, #81, #85)
The game always renders 1280x960; everything below is about showing that on a phone. Desktop-sized
windows (canvas at 1:1 or larger, no touch controls) are untouched by all of it.

- **Canvas layout — `src/systems/Viewport.js`.** `Viewport.apply(game)` is the only place the canvas
  style is written (`src/game.js` calls it at boot and on every window resize; Phaser's own
  `autoCenter` is off). Whole-integer scale when the window is big enough, exact fit otherwise. With
  touch controls on screen the controls get their own strip of the window and **never overlap the
  canvas**: a gutter each side (`side`, landscape phones) or a strip underneath (`bottom`, portrait
  phones and 4:3 tablets), whichever leaves the canvas bigger; the controls shrink to as little as
  0.75x (`--tc-scale` on `#touch-controls`) when that buys the canvas room, and further on windows
  under 360px wide so the d-pad and the buttons never overlap each other. `Viewport.CONTROLS` holds the
  controls' footprint — keep it in step with the stylesheet in `TouchControls._build`.
  `Viewport.current` is the layout in force (`mode`, `scale`, `controls`, canvas rect).
- **Overlay magnification — `src/systems/UIScale.js` (`scene.uiScale`).** Overlays are authored in
  fixed pixels and are NOT given a second layout. When the canvas is shown below 1:1 and an overlay is
  up, every object at **depth >= 2000** is drawn by a second camera that zooms in on the overlay's
  content (everything except full-screen dimmers) until it is as big as on a desktop or fills the
  canvas with a 12px margin, whichever comes first. At 844x390 that is 1.3-2.5x. Rules this puts on
  overlay code:
  - Overlays live at depth 2000+, world and HUD below it. A new overlay gets the zoom for free.
  - Draw panels with Graphics `fillRect` / `strokeRect` / rounded rects / circles / triangles (their
    extents are tracked — Graphics has no bounds of its own) or any object with `getBounds()`.
  - Do not read raw `pointer.x` / `pointer.y` against overlay coordinates: use the handler's
    `localX` / `localY` (the map's click-to-travel does).
  - DOM placed over an overlay goes through `scene.uiScale.project(x, y)` and `.zoom`, and listens
    for the scene event `'uiscalechange'` (the character creator's name input does).
  - Two per-object opt-outs: `obj.uiScaleSkip = true` for something at depth 2000+ that is NOT an
    overlay and must stay on the world camera (the debug grid, flag labels and stats text — otherwise
    the collision tint stops lining up with the world on any window under 960px tall);
    `obj.uiFloat = true` for something magnified but belonging to no overlay (the shop toast): it
    never moves or shrinks the overlay it appears over and stays where it was authored on the canvas —
    except that a float which would cover the open overlay's content slides into the strip under (or
    over) the panel when one is tall enough to hold it (`UIScale.clearOf`; a panel that fills the
    canvas height leaves no strip, and the toast stays put over it).
  - The magnification applies to ANY window showing the canvas below 1:1, not only phones: a
    1440x800 laptop draws overlays at 1.2x. Only windows of 1280x960 and up are untouched.
  - An overlay that already fills the canvas cannot be magnified; its text can use
    `scene.uiScale.textSize('14px')` instead (the map's labels do — up to 1.6x).
- **Hint wording — `src/utils/Hints.js`.** Write the hint for the keyboard and pass it through
  `Hints.text(scene, 'SPACE/ENTER: start · ESC: leave')`; with touch controls on it comes back as
  `A: start · B: leave` (SPACE/ENTER → A, ESC → B, ↑/↓ and arrows / WASD → d-pad, ←/→ → ◀ ▶, SHIFT → sprint, click → tap).
  `{ tap: true }` for overlays where a tap anywhere confirms (dialogue, intro): `TAP or A`. Use
  `Hints.touch(scene)` rather than testing `touchControls.enabled`. Never hand-write a touch string.
- **A touch on a control stays on the control.** Phaser listens for touches on the whole window, so
  a tap on the A button used to reach the overlay underneath as well (dialogue advanced twice, the
  intro skipped a page, B closed and reopened the menu). `TouchControls._own` default-prevents the
  touch events on every control, which Phaser's window handlers respect. Any new DOM control over
  the page needs the same.
- **Testing**: playwright contexts with `hasTouch` at 844x390, 390x844 and 1024x768;
  `page.touchscreen.tap` or CDP `Input.dispatchTouchEvent` for real touches (a d-pad press needs a
  held touch, not an instant tap). `?touch=1` shows the controls with a mouse.
