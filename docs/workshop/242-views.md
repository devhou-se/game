# Views: Fukuoka Tower's lift and observation deck, a ride on the Dotonbori wheel (#242)

## Context

Fukuoka Tower (`fukuoka-tower_0_0`, 4x12, `generate_fukuoka.py` `TOWER = (10, 7)`) and the Dotonbori ferris
wheel (`dotonbori-wheel_0_0`, 12x12, `generate_osaka.py` `WHEEL = (33, 7)`) are sealed landmarks: you walk up,
the camera looks up (`game.lookUp`), and that is all. The ticket asks that going up the tower shows the view
from inside (enter, a lift with a little "going up / going down" animation, then an observation deck) and that
riding the wheel plays a view animation.

Outcome:
- **Tower.** The glass door drawn in the tower's base opens. Walking in plays a short lift ride (the cabin, a
  height counter, Momochi dropping away behind the glass) and puts you on a new room, the observation deck,
  whose back wall is floor-to-ceiling windows over the beach, the bay and the city. Walking back onto the lift
  plays the ride down and puts you on the plaza in front of the door.
- **Wheel.** A gondola waits in the boarding gate under the wheel. Bumping it plays one turn of the wheel: the
  view from inside a gondola rising over Dotonbori, cresting, and coming back down. You step off where you got on.
- Both rides can be skipped, work from the keyboard and by touch, and follow the game's day and night; so do
  the deck's windows.

All under `gamev2/`. Two commits, the tower first; the wheel builds on the tower's `ViewRide.js` and art helpers
and can be held back without touching the tower.

## Approach

**One cutscene class, `src/ViewRide.js`, modelled on `src/AirTravel.js`** (curtain, picture at depth 3000,
skip rule, input held at InputHandler's priority 0, rules as static functions with unit tests). A ride is a
picture of where you are sitting (a frame with a window) over a view that pans as you rise: two tall layers,
`far` and `near`, each bottom-aligned to the window at height 0 and top-aligned at height 1; `far` is the
shorter picture, so it moves less (parallax). `far` is opaque and holds the day sky (flat bands, drawn by the
art tool), so the code has no sky colours of its own. The hour is the game's own grade: both layers are tinted
with `DayNight.GRADES[period]` (what the street outside is multiplied by), and where that grade has `lights`
(night) a `lights` picture (lit windows, neon) is drawn untinted over `near`. The lift and the wheel differ only
in data: the frame, the three pictures, the duration and the height curve (the lift eases 0 -> 1 or 1 -> 0; the
wheel is `(1 - cos 2πt) / 2`, slow at the bottom and the top as a wheel is).

**The deck is one more owned-door interior**, built the way Canal City is (`generate_mall.py`, two door leaves):
a generator on `tools/interiors.py`, the door found by sprite and wired with `rg.open_door`, a row in
`roomgen.OWNED_DOORS` so a Fukuoka rebuild keeps it, `generate_fukuoka.py` not edited. The lift's doors are the
deck's doorway (front wall, south): the ordinary exit, drawn as a lift sill.

**The deck's windows follow the hour, with the grade the street has.** The panes are drawn once, by day. An
`interior` is never graded (and `lanternLight` only dims it warm at night), which would leave a noon view in
the windows at midnight, straight after a ride up through the night. So the deck carries one new room flag,
`daylight: true`: `DayNight.gradeFor` grades such an interior as it grades outdoors (dawn, dusk, night; lights
and `Glows` on at night). The ride tints its layers with the same grade, so the window you rode up behind and
the windows you step out to agree by construction. `interior` stays (it is also what keeps the blog pipeline
out and what `Interactions` reads).

**A lift ride is a property of the room pair, not of the transporter**: the deck carries the marker
`deck: {host, doors}` (which `OWNED_DOORS` needs anyway), and `RoomManager.liftFor(configRooms, from, to)`
answers `'up'` for a transporter into a room that has `deck`, `'down'` for one out of a room that has it. It is
given **`config.rooms`** (`scene.config.rooms`, as `DayNight` and `Career` read their flags): the runtime
`roomManager.rooms` are rebuilt objects that carry no markers. It lives on `RoomManager` because that file is
already loaded wherever the rule is asked (the game, `tools/play.js`, `tools/test_game.js`, `/studio/`);
`ViewRide.js` is only the picture and is loaded by the game alone. Markers are read from `config.json`, so
`config_to_tiled.py`, the `.tmj` format and `TiledAdapter.js` are untouched (a per-transporter flag would have
had to pass through all three).

**The wheel boards at the gate it already has.** The wheel's sprite draws an empty boarding gate at the foot of
its opening (prefab cells (4,10), (5,10), solid: Osaka (37,17), (38,17)), but no gondola in it and nothing that
says it can be ridden. `generate_osaka.py` stands one new 2x2 prop, `wheel-boarding_0_0`, a gondola, in that
gate, and the bump rule is on the prop (not on `dotonbori-wheel`, whose footprint is 12x12 and whose legs you
brush past). Only two cells become solid, and the other half of the opening (columns 39-40) stays open to walk
under the wheel. The rule follows the prop through Osaka's #219 rebuild, whatever the wheel becomes. No new room.

## Changes

### Commit 1: the tower

- `tools/roomgen.py`: `DECK_DOORS = {'fukuoka-tower_0_0': [(1, 11), (2, 11)]}` (Fukuoka (11,18), (12,18); fronts
  (11,19), (12,19)), `DECK_PREFIX = 'Deck'`, row `DECK_PREFIX: ('deck', DECK_DOORS)` in `OWNED_DOORS`. Reword the
  `TOWER_DOORS` comment: Fukuoka Tower is no longer "not in here" for want of a door, it has its own table.
- `tools/generate_tower_deck.py` (new; copy `generate_mall.py`'s shape): `HOST = 'Fukuoka'`,
  `KEY = 'DeckFukuoka1'`, `NAME = 'Tower Deck'` (10 characters: the phone bar keeps its countdown). Floor
  18x6 at `OX, OY = 1, 6`, `WALL = 5`, room 20x15 (the smallest room there is; a five-row wall costs no size).
  - Back wall, 5 rows, `back_wall(..., WALL, view=True)`: six panes `deck-in-window-1..6` (3x5 each), glass
    from the floor to the ceiling: the view is what the room is for, and takes a third of the screen.
  - Floor `deck-in-floor-a/b` (dark carpet), `side_walls`, `front_wall` with the doorway at floor columns 8-9,
    thresholds `deck-in-lift-w/e` (the lift's sill), `deck-in-doorlight` as the pub has.
  - Fittings, all solid, none in floor columns 8-9: three coin binoculars `deck-in-binoculars` (1x2, `stand`,
    foot on floor row 0, between panes), a brass map plinth `deck-in-compass` (2x1), the padlock fence
    `deck-in-locks` (2x1, east end), two benches `deck-in-bench` (2x1, no line), a sign `deck-in-lift-sign`
    (1x2, `stand`, beside the doorway), ceiling lights `deck-in-downlight` on `Tops`.
  - `it.doorway(8, HOST, [front for _, front in doors])`; `it.room(NAME, npcs=<kept>, deck={'host': HOST,
    'doors': [...]}, daylight=True, shopEnabled=False)` (no `lanternLight`: see `DayNight` below);
    `rg.open_door` per leaf, each leaf to its own half of the doorway; assert exactly one tower. Prints the
    rooms to re-seed and lint, as the others do.
- `tools/interiors.py`: `room()`'s docstring and its `interior` comment name the new flag (`daylight`: graded by
  the hour as the street is).
- `tools/generate_tower_deck_art.py` (new, Pillow, `--preview`; imports `register`, `wall_side`, `wall_front`,
  `threshold`, `doorlight` from `generate_pub_art.py` as the mall's tool does; no font, so it is not a
  `FONT_TOOLS` entry). Draws:
  - the `deck-in-*` pieces above (registered with `register()`);
  - **one panorama**, three canvases as wide as the deck's wall (1152 display px, 576 as drawn) and at most
    1024 px tall: `near` (the plaza, the beach and Marizon pier at the bottom, rising to the bay shore, the
    dome and city blocks; transparent above its skyline), `far` (the bay, the islands, the horizon and, above
    it, the day sky in flat bands; opaque, at least as tall as the lift's window), `lights` (only the lit
    pixels of `near`);
  - the cutscene pictures, saved at display size (pixel-doubled) as `assets/sprites/<key>.png` and registered
    the way `train-interior-*` is (`spriteMetadata[key] = {frameCount: 1, anchorX: 0.5, anchorY: 0.5}`, no
    `tileNames` entry): `view-lift` (640x640: a glass lift cabin from inside, steel frame, a plain dark panel
    across the top for the counter, a window opening 384x448) and `view-fukuoka-near` / `-far` / `-lights`,
    which are **the middle 384 columns** of the three canvases (the lift comes up in the middle of the deck);
  - the six panes, cut from the same canvases at their full width: `far` with `near` on top, both as the lift
    shows them at height 1, the 320 px band that holds the horizon, mullions over it. One view, drawn once;
    what you see arriving at the top is what panes 3 and 4 show. Helpers the wheel's tool will reuse (sky
    bands, a skyline of blocks with windows and a matching lights mask, cut-to-window) are plain functions of
    this module.
- `src/DayNight.js`: `gradeFor` returns `DayNight.GRADES[period]` for a room that is not `interior` **or is
  `daylight`**; the header comment and the function's say so. Nothing else changes: `apply()` already builds
  the glows whenever the grade has `lights`.
- `src/systems/RoomManager.js`: `static liftFor(configRooms, from, to)` -> `'up'` if `configRooms[to].deck`,
  `'down'` if `configRooms[from].deck`, else `null` (missing rooms are `null`; no comparison with `deck.host`,
  which is a district key where `from` would be a stitched city's). `checkTransporter`: before `switchRoom`,
  `const dir = RoomManager.liftFor(this.scene.config.rooms, this.currentRoom, trans.targetRoom)`; if `dir`
  and `this.scene.viewRide`, `this.scene.viewRide.lift(dir, trans)` and return true.
- `src/ViewRide.js` (new; add to `index.html` after `AirTravel.js`). Static, tested:
  - `RIDES = { lift: { frame: 'view-lift', view: 'view-fukuoka', ms: 4500, top: 123, window: {x, y, w, h},
    panel: {x, y, w, h} } }` (`wheel` is added in commit 2; rectangles in the frame picture's own px),
    `FADE = 350`, `SKIP_AFTER = 700`.
  - `height(ride, dir, elapsed)` -> 0..1: lift eased in and out, `'down'` its mirror; clamped.
  - `metres(ride, h)` -> `Math.round(h * top)`; `pan(h, layerH, winH)` -> px the layer has moved down
    (`Math.round(h * (layerH - winH))`); `canSkip(elapsed)`.
  - `tint(period)` -> `{ tint, lights }` from `DayNight.GRADES[period]`: `tint` is the grade's colour at its
    alpha over white (per channel `255 - (255 - c) * alpha`; `0xffffff` by day), which is what the MULTIPLY
    rectangle does to the deck; `lights` is the grade's.
  - `scale(worldZoom, viewW, viewH, frameW, frameH)` -> `Math.max(1, Math.min(worldZoom || 1, viewH / frameH,
    viewW / frameW))`. `TrainTravel.cutsceneScale` only knows the height; a portrait phone's view is as narrow
    as 560 canvas px (`Viewport.MIN_VISIBLE`), and at the world's zoom a frame 640 wide would lose its window's
    sides there. At scale 1 a 640 px frame still overhangs a 560 px view by 40 px a side, so every ride's
    `window` and `panel` lie inside the frame's middle 560 columns (a test).
  Instance (`scene.viewRide`, `riding`): `lift(dir, trans)` does what `AirTravel.go` does - `riding = true`,
  `roomManager.isTransitioning = true`, clear the skip keys' JustDown, fade a curtain in, then
  `roomManager.switchRoomInstant(trans.targetRoom, trans.targetX, trans.targetY)` behind it, build the picture,
  run it for `ms` or until skipped, fade out, release both flags. The picture is built as
  `AirTravel.buildCutscene` builds its own: a container at depth 3000, scroll factor 0, the `getBounds`
  override, plain shapes (no Graphics), scale `ViewRide.scale(worldZoom, W, H, 640, 640)` with `W`, `H` read
  from `cameras.main` when it is built, a tap zone at depth 3005. In it: `far`, `near` (+ `lights` when the
  grade has them), tinted by `tint(scene.dayNight.period())`; a few bars of the tower's lattice sliding past
  against the travel (rectangles); the frame, untinted (a lit cabin); the player's standing frame seen from
  behind (`getDirectionalSpriteKey(baseSpriteKey, 'up')`) on the cabin floor; on the panel a triangle (a shape:
  up or down). Each layer is cropped to the window every frame (`setCrop`, as the dialogue photo is), so
  nothing shows outside the frame.
  The words are overlay text, made the way `AirTravel` makes its route line and hint (depth 3001, outside the
  container, `setResolution(1)`, its own background box, so `UIScale` keeps them readable on a phone): the
  counter `"<n> m"` in `PixelOperatorMonoBold`, centred on the panel's centre (the panel is plain, so text that
  `UIScale` grows still sits on it), `setText` only when the whole number changes; and the hint
  `Hints.text(scene, 'SPACE: skip the ride', { tap: true })`. The file must load without Phaser, as
  `AirTravel.js` does (the tests load it in Node, with `DayNight.js`).
- `src/GameScene.js`: construct `this.viewRide` beside `airTravel`. `src/systems/InputHandler.js` `routeInput`:
  a priority-0 branch for `viewRide.riding` exactly like `airTravel.flying` (only `viewRide.handleInput()`,
  SPACE / ENTER / ESC skip, `lastKeyState` synced).
- `src/utils/Interactions.js`, `flavour` rows (one dry lowercase line each, in the table's voice):
  `deck-window` `/^deck-in-window/`, `binoculars` `/^deck-in-binoculars/`, `compass` `/^deck-in-compass/`,
  `padlocks` `/^deck-in-locks/`, `lift-sign` `/^deck-in-lift-sign/`. The only facts to use: the deck is 123 m up,
  the tower 234 m.
- `src/utils/Glows.js` `SPRITES`: the downlight, and two or three small cool spots on each pane where the city
  is (the room is `daylight`: at night it is graded as the street is and these show).
- `tools/world-model.js` `step()`: `transported` gains `lift: 'up' | 'down'` when `RoomManager.liftFor(
  this.config.rooms, from, t.targetRoom)` says so (asked before `enter`; no key when it is `null`, so what
  reads `transported` today is unchanged). No loader list changes: `RoomManager.js` is already in the lists of
  `tools/play.js`, `tools/test_game.js` and `studio/index.html`. `play.js` prints it ("the lift goes up").
- `tools/check_generators.py`: `generate_tower_deck` in `GENERATORS`, **at the end of the first list, after
  `generate_mall`** (the shared `plumbing` test wants an interior's generator after `generate_temple` and
  before `districts`; "after `generate_fukuoka`" would fail it), `generate_tower_deck_art` in `ART_TOOLS`.
- Generated: `config.json` (`rooms.DeckFukuoka1`; Fukuoka: two colliders off, two hidden transporters;
  `spriteMetadata`, `tileNames`, `tilePalette` appended), `tiled/deckfukuoka1.tmj`, `tiled/fukuoka.tmj`
  (`config_to_tiled.py DeckFukuoka1 Fukuoka`), the PNGs.
- Docs: `docs/landmarks-and-towns.md` (a "Fukuoka Tower's deck" section after Canal City's; the Fukuoka
  section and the sentence that landmark towers stay sealed; the ride, its skip rule and its input, as
  `trains-and-stations.md` describes the flight), `docs/architecture.md` (file list),
  `docs/buildings-and-street-props.md` and `docs/generators-and-checks.md` (the `daylight` flag, where
  `lanternLight` is described), `docs/tools-play-test-studio.md` (the `lift` field), `tools/browser/README.md`
  (what `regress.js` covers).

### Commit 2: the wheel

- `tools/generate_wheel_art.py` (new, in `ART_TOOLS`; reuses commit 1's helpers; must not name a `deck-in-`
  sprite or `DeckFukuoka1`: the deck's `plumbing` test reads every other `generate_*.py` for them):
  `wheel-boarding_0_0` (2x2: a red gondola with blue glass like the eight on the wheel, door open, drawn to sit
  in the wheel's boarding gate, with no platform of its own; `register()`), and `view-gondola` (640x640: the
  inside of a gondola, red frame, a wide window 512x320, a grab rail), `view-dotonbori-near` (the canal and its
  bridges at the bottom, the neon boards, roofs behind them), `view-dotonbori-far` (the city out to the
  horizon, Tsutenkaku small in it, the day sky above; opaque), `view-dotonbori-lights`. The Dotonbori layers
  are 64 px wider than the window, for the sideways drift.
- `tools/generate_osaka.py`: `b.prop('wheel-boarding_0_0', WHEEL[0] + 4, WHEEL[1] + 9, 2, 2)`: Osaka (37,16),
  over the gate. (37,16) and (38,16) become solid; (37,17) and (38,17) already are. Bumped from (37,18) or
  (38,18) below, (37,15) or (38,15) above, (39,16) or (39,17) beside it; (39..40, 16..18) stays open. Re-run,
  `config_to_tiled.py Osaka`, `make_worldmap.py` if its output changes. Look at the render: the wheel's sprite
  (foot on row 18) sorts in front of the prop (foot on row 17), so the gate's bars cross the gondola's lower
  half, which is the look wanted (a gondola docked in the gate); if it reads as a muddle, give the prop a
  `depthBias` so it draws over the gate.
- `src/utils/Interactions.js`: `{ kind: 'wheel', group: 'ride', pattern: /^wheel-boarding/, footprint: true }`.
- `src/ViewRide.js`: `RIDES.wheel = { frame: 'view-gondola', view: 'view-dotonbori', ms: 14000, drift: 32,
  window, panel }`; `height` for it is `(1 - cos 2πt) / 2`; `drift(ride, elapsed)` -> `Math.round(drift *
  sin 2πt)` px sideways (`near` by all of it, `far` by a third). `check(gridX, gridY)`: `interactionAt(x, y,
  'ride')`, one ride per bump by `ShrineVisit.fresh` / `.carried` exactly as `PalaceVisit.check` does (with
  `hold(heading)`), then `wheel()`: the same sequence as `lift` with no room swap; the player ends on the same
  cell, facing the gondola.
- `src/GameScene.js`: `this.viewRide.check(...)` in `checkNPCInteraction` after the flights check, guarded like
  it (`!this.viewRide.riding`, no dialogue open); `this.viewRide.hold(this.inputHandler.heading())` in `update`.
- `tools/world-model.js`: `'ride'` in `interactionAt`'s group list; `describe()`: "rides the wheel: one turn,
  the view over Dotonbori, and back on this cell".
- Generated: `config.json` (Osaka, metadata), `tiled/osaka.tmj`, PNGs, `assets/map` if changed.
- Docs: `docs/landmarks-and-towns.md` (Osaka section: the boarding gondola and the ride), the same small
  edits as commit 1 elsewhere.

## Data and interfaces

- `config.json`: new room `DeckFukuoka1` (`interior`, `daylight`, `shopEnabled: false`,
  `deck: {host: 'Fukuoka', doors: [[11, 18], [12, 18]]}`). `deck` is new: the owned-door marker, and what makes
  a transporter between the two rooms a lift ride. `daylight` is new: an interior graded by the hour as the
  street is. New sprites `deck-in-*`, `wheel-boarding_0_0`, and the cutscene pictures `view-*` (keys without
  `_0_0`, not tiles).
- `Interactions.RULES`: new group `ride` (kind `wheel`); five `flavour` rows.
- `RoomManager.liftFor`; `DayNight.gradeFor` reads `daylight`; `ViewRide` statics above;
  `scene.viewRide.riding`. `world-model` `step().transported.lift`.
- No new key bindings, no save data, no `.tmj` format change, no change to `generate_fukuoka.py`.

## Tests

`tools/tests/views.test.js` (new), with `tools/tests/interiors.js` for the deck (`{HOST: 'Fukuoka',
KEY: 'DeckFukuoka1', NAME: 'Tower Deck', MARK: 'deck', SPRITE: 'fukuoka-tower_0_0', DOORS: [[1, 11], [2, 11]],
STAND: [0, 12], PREFIX: 'deck-in-', BEHIND: 10}`; `BEHIND: 10` because only the base, rows 10-11, was ever
solid from side to side):
- the tower opens (`I.doorsOpen`): two leaves, two sills, each leaf to its own half; room flags (`interior`,
  `daylight`, no `lanternLight`, `shopEnabled: false`), name, size; `hudBrief('Tower Deck')` fits.
- nobody in the way on any date (`I.nobodyInTheWay`; Damian's 2025-11-10 cell is the stand cell beside the door).
- the deck is a deck: the panes solid from end to end and inside the boundary, every fitting solid, all floor
  reachable, `I.walkThrough` bumps every kind and leaves by the lift; `I.plumbing` (which also holds the
  generator's place in `check_generators.py`).
- the held key: north of each arrival cell is not an exit, south of each plaza front cell is not a transporter.
- `RoomManager.liftFor` with the decoded config's rooms: `'up'` / `'down'` for the tower's four transporters,
  `null` for every other transporter in the config and for a room that does not exist. The world model walks
  it: a step onto a leaf reports `transported.lift === 'up'`, a step onto a sill `'down'`. And the game asks
  with the right rooms: `RoomManager.js` holds `RoomManager.liftFor(this.scene.config.rooms,` (a source
  assertion, as `airports.test.js` makes of its own wiring); with the runtime rooms the ride would silently
  never play.
- `DayNight.gradeFor({interior: true, daylight: true}, p)` is `GRADES[p]` for the four periods; the deck's own
  config room gets the night grade at night and none by day; a plain interior and a `lanternLight` one are
  graded as before.
- `ViewRide.tint`: white and no lights by day, the night grade's colour with lights at night, between for
  dawn and dusk; equal to what `gradeFor` gives the deck, period by period.
- `height` (lift: 0 -> 1 monotonic, down its mirror; wheel: 0, 1, 0 at t = 0, 0.5, 1 and symmetric), `metres`
  (0 and 123 at the ends), `canSkip`, `pan` / `drift` (with the committed PNG sizes read from disk, the window
  never shows past an edge of a layer at any height; `far` is opaque and at least the window's height).
- `scale`: 1 on a desktop; the world's zoom on a landscape phone until the frame would be taller than the
  view; held down by the width on a portrait phone (612 px wide: 1); never below 1. Every ride's `window` and
  `panel` are inside the frame's middle 560 columns.
- the wheel: the prop's four cells answer `{kind: 'wheel', group: 'ride'}`, the wheel's legs answer nothing,
  (39,17) under the wheel can still be walked through, and **on every survey date at least one of the cells
  it is bumped from is free of NPCs and reachable** (not "no NPC in front of it on any date": the blog
  pipeline keeps visitors off doorways only, and a post that stood somebody by the gate would turn the
  checks red); `world.describe`.
- every `view-*` key a ride names is in `spriteMetadata` and on disk.

`tools/browser/regress.js`, new cases: `tower-lift` (walk in with the key held: `riding`, then
`DeckFukuoka1` on the arrival cell or north of it, never back in Fukuoka; walk onto the lift: Fukuoka, in
front of the door), `tower-lift-skip` (SPACE before 700 ms does nothing, after it ends the ride),
`tower-deck-night` (`?tod=night`: the grade rectangle is visible on the deck and its glows are built; by day
neither), `wheel-ride` (bump: `riding`; ends on the same cell; the key still held does not ride again), the
lift on a 667x375 touch phone (the hint line and the counter are at least 10 CSS px, the frame inside the
view) and on a 390x844 one (the frame's window and the counter inside the visible width).

Run, from `gamev2/` (art tools need Pillow: a venv with `pip install -r tools/requirements-art.txt`):
`node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js check`,
`python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`,
`node tools/play.js lint DeckFukuoka1 Fukuoka Osaka`, the browser regression. Then play it: both rides and the
deck at 1280x960, at 667x375 with `?touch=1` and at 390x844 with `?touch=1`, each with `?tod=day`,
`?tod=dusk` and `?tod=night`, screenshots (and each art tool's `--preview`) looked at and saved to
`/work/media/`. Step out of the lift at night and compare the last frame of the ride with the deck's windows.

## Risks and open questions

- **The pictures carry the feature** and are the largest any art tool here has drawn in code. Judge them by
  eye at every size and period; a view that reads as stripes is not done. Keep to the house style (half
  size pixel-doubled, GuttyKreum palette, 1 px ink outline on the frames).
- **The night look is the street's**: a day picture multiplied by the night grade, with lights over it, not a
  painted night sky. It is what every outdoor room looks like at night, and it is what makes the ride and the
  deck agree. If the tinted sky reads too bright behind the lights, darken the day sky's bands in the art
  (both the ride and the panes follow), not the tint.
- **Map data is serial.** Rooms touched: Fukuoka (the door only), Osaka (one prop), new `DeckFukuoka1`. Both
  towns have a #219 rebuild pending: if the tower moves, re-run `generate_tower_deck.py`; the boarding prop is
  placed from `WHEEL`, sits in the gate the wheel's own sprite draws, and must be carried into the new layout.
- `isTransitioning` is held through the wheel ride with no room swap after it; check that nothing waits on a
  swap to release it, and that a skip during either fade cannot end the ride twice (`AirTravel`'s `landed` guard).
- The camera looks up at the tower where the ride down puts you; `landmarkView.reset()` in `applyRoomSwap`
  should settle it under the curtain. Check on a phone.
- Owner's taste, not blocking: the deck's name (`Tower Deck`); both rides are free; the lengths (4.5 s lift,
  14 s wheel); the flavour lines; the wheel's view is drawn from inside a gondola looking out rather than the
  wheel seen turning from outside; Damian's post about the view from the tower stays at its foot (interiors
  are never offered to the blog pipeline) unless the owner wants him on the deck.

## Review

The design adversary's pass over the above. Each point: what was wrong, the fix, and whether the body now
has it.

1. **The lift would never have played.** `checkTransporter` passed `this.rooms` to `liftFor`, but
   `RoomManager.initializeRooms` rebuilds each room as `{name, boundary, npcs, objects, transporters, floor,
   layers, signage, ...}` and drops every marker, `deck` included: `liftFor` would always answer `null` and
   every walk into the tower would be a plain room fade. The unit test as written (config rooms) would have
   passed all the same. *Fix:* pass `this.scene.config.rooms`; a source assertion on the call, a world-model
   step that reports the lift, and the `tower-lift` regression. **Adopted.**
2. **A loader was missed, and the rule sat in the wrong file.** `tools/world-model.js` is loaded in three
   places, not two: `studio/index.html` loads it in a browser, and a `ViewRide.liftFor` in `step()` would be a
   `ReferenceError` on the first step in Studio. *Fix:* the rule is `RoomManager.liftFor` (that file is in all
   three lists already), `ViewRide.js` is loaded by the game only, no list is edited. **Adopted.**
3. **`liftFor` compared `deck.host` with `from`.** In a stitched city `currentRoom` is the city and the marker
   names the district, so a deck there would never go up. Not a bug today (Fukuoka stands alone), but the
   comparison buys nothing: only the host's door leads into a deck. *Fix:* `'up'` if the target has `deck`,
   `'down'` if the room you are in has it. **Adopted.**
4. **The deck's windows would show noon at midnight.** The deck was `interior` + `lanternLight`: no grade at
   dawn or dusk, a faint warm dim at night, over panes painted with a day sky, while the ride a second
   earlier showed the hour. Against "follow the game's day and night" for about half of every day. *Fix:* a
   room flag `daylight` that makes `DayNight.gradeFor` grade the deck as it grades the street, and the ride
   tints with the same grade, so the two cannot disagree. **Adopted.** (Not adopted: a runtime backdrop behind
   transparent panes, or one set of panes per period swapped by code. Both are new machinery for what one
   line in `gradeFor` does.)
5. **Sky colours lived in two places** (bands in `ViewRide.sky`, a painted sky in the panes), free to drift
   apart. *Fix:* the day sky is drawn once, into the opaque `far` picture; the code only tints. `sky(period)`
   becomes `tint(period)`. **Adopted.**
6. **"One view, drawn once" did not add up.** The layers were "the window's width" (384 px) but the six panes
   are 1152 px across; they could only have been a stretch or a second drawing. *Fix:* the panorama is drawn
   at the wall's width; the lift's layers are its middle 384 columns, the panes its horizon band. **Adopted.**
7. **The view was a three-row strip in the room built to show it.** *Fix:* a five-row back wall (as Canal
   City's), panes 3x5; the room is 20x15 either way. **Adopted**; it is a judgement by eye, and the fittings
   are unchanged.
8. **The picture's scale ignored the width.** `TrainTravel.cutsceneScale` is `min(zoom, viewH / carH)`; on a
   portrait phone (view 560-612 canvas px wide, zoom above 1) a 640 px frame at 1.5 is 960 wide and the
   gondola's 512 px window loses its sides. *Fix:* `ViewRide.scale` also takes `viewW / frameW`; windows and
   panels stay in the frame's middle 560 columns; a 390x844 case in the regression and in the play-through.
   **Adopted.**
9. **The counter was a Text inside a scaled picture, rewritten every frame.** `UIScale` treats overlay text on
   its own terms (it grows single lines on a phone), which is why `AirTravel` keeps its words out of the
   container. *Fix:* the counter is overlay text made as `AirTravel` makes its route line, centred on a plain
   panel, `setText` only when the number changes. **Adopted.**
10. **`check_generators.py` order.** "After `generate_fukuoka`" fails `interiors.js` `plumbing`, which wants an
    interior's generator after `generate_temple`. *Fix:* after `generate_mall`. **Adopted.** (The same test
    reads every other `generate_*.py` for `'deck-in-` and `DeckFukuoka1`: noted on the wheel's art tool.)
11. **"The wheel's sprite has nothing to board" was wrong, and the prop shut the way under the wheel.** The
    sprite draws an empty boarding gate, solid on (37,17), (38,17). The prop at (39..40, 16..17) beside it
    made row 17 solid from leg to leg, so the walk under the wheel was closed, and its bump cells were the
    two directly above (39,19), where the blog pipeline stands the wheel's visitors (Damian, and Dylan in
    three of his states). *Fix:* the gondola stands in the gate, (37..38, 16..17): two new solid cells, columns
    39-40 stay open, six cells to bump it from, none of them next to the visitors' cell. Checked on the
    committed map: no cell becomes unreachable either way. **Adopted**, with the render to be looked at.
12. **A test the blog pipeline could turn red.** "No NPC in front of the prop on any date" depends on posts
    not yet written: the pipeline protects doorways, not bump cells. *Fix:* assert that on every survey date
    at least one bump cell is free and reachable. **Adopted.**
13. **"lift" is already a kind** in `Interactions` (`lobby-lift`, group `career`). `transported.lift` and
    `viewRide.lift()` are a field and a method, not a kind, and nothing matches on the word. **Not adopted**:
    no rename; do not add an `Interactions` kind called `lift` for the deck's sill.
14. **Simpler alternative considered: no cutscene class, a text card over the ordinary fade** ("going up...").
    It would meet "a little animation" at a fraction of the art, but the ticket's other half (the wheel's
    "views animation") needs the panning view anyway, and the lift then costs one more frame picture.
    **Not adopted.**

Nothing here needs the owner's decision before implementation; the taste items stay as listed under Risks.
