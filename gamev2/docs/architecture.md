# Architecture

The file map of `src/`, the core constants, grid movement and collision, and how the game's files are loaded
(as they are when you work on it, packed by a build when it is deployed).

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

## Architecture

### File Structure

- `index.html` - Entry point, loads Phaser CDN and game scripts from `src/` (the list between its `build:scripts` marks)
- `config.json` - JSON configuration file defining game constants, rooms, NPCs, and objects
- `tiled/*.tmj` - Room maps, authored in the Tiled editor (the map source of truth at
  runtime — see `tiled/README.md`; config.json's room layers are only a fallback)
- `src/game.js` - Phaser game configuration (viewport: 1280×960, physics setup)
- `src/systems/Viewport.js` - Where the canvas sits in the window, and where the touch controls go (see Small Viewports and Touch)
- `src/systems/UIScale.js` - World zoom, HUD magnification and overlay fitting for small, cropped or touch-covered canvases (see Small Viewports and Touch)
- `src/systems/LandmarkView.js` - The camera looks up in front of a landmark marked in config `game.lookUp` (see Small Viewports and Touch)
- `src/utils/Hints.js` - The one helper that words key hints for keyboard or touch (see Small Viewports and Touch)
- `src/utils/Glows.js` - Glow spots a placed sprite lights at night: neon boards, lit fronts (see Neon and lit fronts at night)
- `src/utils/Assets.js` - Where the files the scene loads come from: the file itself, or its copy in the deploy build's packs (see Loading and the deploy build)
- `src/utils/JapaneseFont.js` + `fonts/` - The pixel fonts, and the Japanese face added to each of them (see Fonts and Japanese Text)
- `src/AirTravel.js` - The flights between the two airports (issue #218): who can fly where, the cabin cutscene and its skip rule (see Airports and flights in `trains-and-stations.md`)
- `src/ViewRide.js` - A ride with a view (issue #242): the lift up Fukuoka Tower and a turn on Osaka's ferris wheel (bump the gondola at its foot), the view panning behind the window, the lift's counter, the hour's tint and the skip rule (see "Fukuoka Tower's deck" and "A turn on the Dotonbori wheel" in `landmarks-and-towns.md`)
- `src/utils/Places.js` - The towns as real places in Japan for the Map overlay: config `places`, which town a room is in, who is where, label layout (see The Map overlay in `hud-input-touch.md`)
- `src/utils/Trips.js` - The devhouse trips as data: which trip a date belongs to, and everything that follows (see Trips)
- `src/GameScene.js` - Main game scene (room system, HUD, input handling, collision)
- `src/Character.js` - Character movement class with grid-based tweening
- `src/DialogueManager.js` - NPC dialogue system with multi-line conversations
- `src/systems/Occlusion.js` - Scenery fades while someone stands hidden behind it, and their name label
  with it (see "Walking behind things" in `occlusion.md`)
- `src/utils/Interactions.js` - The one table of what a bump opens (shops, ponds, clocks, a home's flavour lines, the drinking
  table, a shrine's offering box and fortune stand, the palace's dais and visitors' book, a temple's incense burner, offering box and fortune drawers, a pagoda's offering box and fittings, a tower lobby's reception desk and lifts). `Shop`, `Fishing`, `DrinkingGame`, `ShrineVisit`, `PalaceVisit`, `TempleVisit`, `Career`, `GameScene` and `tools/play.js` all read it; add a rule here
  rather than a tile-name check in a feature file
- `src/utils/Seats.js` - The one table of furniture the player can get on (chairs, stools, sofas, benches, beds, futons, the bunk,
  the bath) and the pose on each: the lift, the facing, the piece of its sprite drawn over the player (see Sitting on furniture)
- `src/systems/Seating.js` - Draws the player on that furniture every frame: the lift, the facing, the sort, the cover
  (see Sitting on furniture)
- `src/ShrineVisit.js` - The offering box and the fortune stand inside a shrine's worship hall (see "Shrine worship halls"
  in `landmarks-and-towns.md`)
- `src/PalaceVisit.js` - Requesting an audience at the dais and signing the visitors' book inside the palace's audience hall
  (see "The palace's audience hall" in `landmarks-and-towns.md`)
- `src/TempleVisit.js` - Wafting the incense, the offering box and the fortune drawers inside a temple's main hall; the
  fortune is the shrines' omikuji, decided by `ShrineVisit` (see "The temple's main hall" in `landmarks-and-towns.md`)
- `src/Career.js` - The job in the office towers: signing on at a tower lobby's reception desk, a shift of arrow-row
  tickets up the lifts, the ladder of titles and what it pays (see "Career" in `shop-and-economy.md`)
- `src/MenuManager.js` - In-game menu system (ESC key toggle)
- `src/Energy.js` - The rules of the energy meter and the konbini stamp card (`Energy`, `Stamps`: pure functions, no Phaser);
  `Shop` holds the state and draws the meter (see "Energy and the stamp card" in `shop-and-economy.md`)
- `src/DatePicker.js` - Time Travel calendar (menu, or the HUD date). Marks three different days: today (gold), the day the
  game is on (blue — a trip day, usually a year of months from today) and the cursor (green box). The legend names only
  colours that are on the month shown; the jump row under the selected date moves the cursor to today / the game's day (click, tap, or SHIFT + up / down), and the trips row above it to a trip
- `src/TitleScreen.js` - Title / splash screen shown at boot (cast line-up, press SPACE / tap to start)
- `src/Intro.js` - New-player intro (who devhouse is, controls as keycaps, where to start); replayable from the menu as How to Play
- `src/RotatePrompt.js` - "Rotate your phone for a better experience": a brief toast on a portrait phone (see `hud-input-touch.md`)
- `assets/portraits/` - Optional hand-drawn character portraits (`manifest.json` + `<name>.png`, see its README)
- `src/Voice.js` - Spoken NPC dialogue (lazy per-line audio clips) and the shared mute setting
- `src/AmbientTrains.js` / `src/AmbientBoats.js` - Decorative passing trains and moat boats (see Ambient Traffic)
- `src/AmbientTrams.js` - The streetcars on a room's declared `tramways` (see Ambient Traffic): Toyama's tram, San Franbourne's cable car and tram
- `src/TramRide.js` - Riding one: bump a car standing at a stop, travel with it, up / down gets off (see "Shuttles" in Ambient Traffic)
- `src/TrafficLights.js` - Decorative traffic-signal cycle (see Street accessories)
- `editor/` - Canvas editor for `config.json` room data (see `editor/README.md`)
- `studio/` - Read-only view of the whole world (see Studio in `tools-play-test-studio.md`)

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

## Key Implementation Details

### Collision Detection
All intermediate cells in movement path are checked for:
- Room boundaries (polygon containment check; in a stitched city: inside any district's boundary)
- Collision-layer tiles (`roomManager.isBlocked(x, y)` — a set lookup; collider markers have no sprite)
- Objects (static obstacles)
- Stationary character positions
- Moving character destinations
- Path crossing (swap detection)
- A streetcar standing at a stop (`AmbientTrams.carAt`): solid over its art's cells for everyone, and the player's
  bump boards it (`TramRide`). Not a tile, so not in the collision layer; skipped where the scene has no cars
  (`tools/world-model.js`, the unit tests)

### Sitting on furniture (issue #227)
Chairs, stools, sofas, benches, beds, futons, the bunk, the bath and the toilet can be got onto. There is no
sitting animation and no new art: the player stands on the furniture's cell and is drawn to look as if they
were on it. Which furniture, and how, is one table, `Seats.RULES` in `src/utils/Seats.js` (pure, no Phaser).

- **Getting on is a step.** The furniture's cells stay blocked: `checkCollision` is unchanged, so NPCs, the
  model's paths and reach, `lint` and the blog pipeline all still see an obstacle. `GameScene.checkCollision`
  then asks `CollisionSystem.checkSeatStep`, which lets through one thing only: the PLAYER's one-cell,
  STRAIGHT step onto a solid seat cell (`RoomManager.seatAt`) with nobody and no object on it. Stepping off,
  or along a sofa, is the same step; a held key walks across a row of chairs. A diagonal never gets on.
- **A seat's cells** are the blocked cells of the sprite's footprint (`Seats.index`). A rule with `open: true`
  is the other case - a bench drawn with its back to you over floor you walk on (`station-bench-back`): its
  walkable cells take the pose when you stop there, and nothing about stepping or sorting changes.
  A rule with `at: [[col, row], ...]` keeps only those cells of the footprint (issue #367): the street ramen
  counters (`susukino-ramen-stall-a` / `-b`, `yatai-ramen`) are walls with their stools painted on, and only
  the middle stool, `[1, 2]`, sits on its cell's centre, so it is the seat; the outer stools are paint. From
  the stool, up again bumps the counter and opens its list (a bump on an outer column still does, standing).
- **The pose** is `{ face, dy, cover }`, or one per footprint row for furniture you lie in. `dy` is the lift:
  `Character.setLift` moves the sprite's origin, so the sprite's `x`/`y` (and with them the camera, Occlusion's
  samples and the grid) stay on the cell; it slides from the old cell's lift to the new one's during the step
  (`Seats.dyAt`). `face` turns the player once they stop (a dining chair faces its table). The name label
  follows the lift.
- **Layering** (`src/systems/Seating.js`, run from `GameScene.update` after `updateCharacterDepths()` and
  before `occlusion.update()`): on solid furniture the player sorts at the furniture's foot row
  (`Seats.footRow`) instead of their own, so they are drawn in front of the bed they lie in. `cover` is a
  rectangle of the furniture's own sprite - a bed's blanket, the rim of the bath, the back of a chair seen
  from behind - drawn again one depth step above the player: that is what tucks them in.
- **A line the furniture says** (`Interactions`' `flavour` rules: the bunk, the bath) is said when the player
  settles on it (once each time they get on that piece), under the same guards as a bump. Furniture that is not a seat
  still says its line on the bump.
- **Adding a seat** is one `Seats.RULES` row, provided the sprite stands on `Collidables` over colliders: a
  `pattern` for its key, a `kind`, and a pose tuned by eye in the browser. `tools/tests/seats.test.js` fails a
  row no sprite in the world matches, a pose array that is not one per sprite row, and a `cover` outside the
  sprite. The kotatsu, tables and zabuton are deliberately not seats.

### Character Sprite Positioning
Sprites are centered at: `gridPos * GRID_SIZE + GRID_SIZE/2`

## Loading and the deploy build

Working on the game needs no build: `index.html` loads the scripts in its list one by one, and
`GameScene.preload()` asks Phaser's loader for `config.json`, the `.tmj` maps and about a thousand small
PNGs, each as its own request. That is fine from a local server and slow over a real network, so **what is
deployed is a build** of the same files (issue #244).

**In the game.** Every image and JSON file the scene loads goes through `src/utils/Assets.js`:

- `Assets.json(path)` is what to give `load.json`: unbuilt, the path with a `?t=` cache-buster; built, the
  parsed object from the data pack (Phaser's `load.json` takes either).
- `Assets.url(path, bust)` is what to give `load.image` / `load.spritesheet`: unbuilt, the path (`bust`: with
  a cache-buster, for art that is replaced under the same name); built, a `blob:` URL of the file's bytes in a
  pack.

Texture keys, frames and everything that reads them are the same either way. A file the packs do not have
falls back to its path, and so does the whole game if a pack cannot be fetched: the built site also holds
every loose file. The fonts are not packed (`load.font` fetches the file itself).

`GameScene.preload()` queues the fonts, then either everything else (`queueAssets()`, unbuilt) or the two
packs named in `window.GAME_BUILD`, and `queueAssets()` once both have arrived. The **photos** (a third of
the image bytes, seen only in a dialogue) do not hold up the boot in either mode: `loadPhotos()` fetches them
at the end of `create()`, after the loading screen is gone, and a dialogue opened before its photo has
arrived shows none. When a load pass completes, `Assets.release()` revokes the `blob:` URLs and lets go of
the packs. `src/game.js` sets the loader to 32 parallel downloads (Phaser's phone default is 6) and to load
an image as an `<img>`, not an XHR.

**The build.** `node tools/build_dist.js [--out <dir>] [--commit <sha>]` (from `gamev2/`; Node only, nothing
to install) writes the published site to `dist/` at the repository root, which is not committed:

| File | What it is |
|---|---|
| `pack/game.<hash>.js` | the scripts `index.html` lists, in its order, as one file |
| `pack/data.<hash>.json` | `{ json: { path: parsed JSON }, images: { path: [offset, length] }, photos: { … } }` |
| `pack/images.<hash>.bin` | every image the boot loads, end to end |
| `pack/photos.<hash>.bin` | the NPC photos, fetched once the game is up (a new post changes only this pack and the data pack) |
| `index.html` | the script list replaced by the bundle and `window.GAME_BUILD = { commit, data, images, photos }`; preload hints for the two packs the boot waits for |
| everything else | a copy of `gamev2/` (no dotfiles, `node_modules` or `__pycache__`): the fallback files, `/studio/`, `/editor/` |

`<hash>` is the first 12 hex digits of the file's SHA-256, so the same sources give the same names and bytes.
`firebase.json` serves `/pack/**` as `immutable` for a year and `index.html` as `no-cache`: a returning
player re-downloads only the page and whichever packs changed.

**What goes in the packs is not listed anywhere.** The build runs the game's own `preload()` and
`queuePhotos()` against a loader that only takes notes, with a recording `Assets`, and packs what they asked
for. So:

- a new sprite, map, manifest entry or photo is packed without touching the build;
- a load that does not go through `Assets` **fails the build** (and `tools/tests/build.test.js`), as does a
  file the game asks for that is not in `gamev2/`, or a loader method the recorder does not know (add it to
  `recordLoads` in `tools/build_dist.js`);
- the scripts become one file, so a file must not rely on being a script of its own (no `'use strict'` at the
  top of a file).

**The deploy** (`.github/workflows/firebase-hosting-gamev2.yml`) runs the build with the commit, publishes
`dist/`, and is green only if the live `index.html` is the built one (it carries the commit) and a pack is
served as `immutable`. A `firebase deploy` by hand publishes whatever is in `dist/`: run the build first.

To play the built game: `node tools/build_dist.js`, then serve `dist/` (`python3 -m http.server 8001` from
`dist/`). The browser regression runs against it the same way (`tools/browser/README.md`).
