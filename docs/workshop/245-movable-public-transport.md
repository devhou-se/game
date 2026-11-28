# Design: public transport that moves and can be ridden (#245)

All paths are under `gamev2/` unless they start with `docs/workshop/`.

## Context

Three vehicles stand in a street as solid map tiles and never move (screenshots of today:
`245-design-toyama-tram-today.png`, `245-design-sfb-cable-car-today.png`, `245-design-sfb-tram-today.png`):

| Room | Sprite | Cells today | Rails |
|---|---|---|---|
| Toyama (a district of `HokurikuCity`) | `toyama-tram_0_0` (5x2) | 19-23, rows 20-21 | `toyama-tram-rail`, row 21, columns 11-40 |
| SanFranbourne | `sfb-cable-car_0_0` (3x2) | 10-12, rows 15-16 | `sfb-rail-h`, row 16, columns 4-27 and 32-55 |
| SanFranbourne | `sfb-tram_0_0` (4x2) | 47-50, rows 15-16 | (the avenue's crossing, 28-31, has no rail) |

The ticket asks that they (a) move through the town on a route and (b) can be ridden.

The mover exists: `src/AmbientTrams.js` runs a car along a room's declared `tramways` (#219), but no room
declares one, and a car is decoration that fades in and out at a terminus and carries nobody.

Outcome: each of the three runs back and forth along its rails, stopping at stops. Bump one while it stands at
a stop and you are on board: you travel with it, the camera follows, and at any stop the up / down keys (the
d-pad on a phone) put you off on that side of the street.

Not in this change: buses (the game has bus-stop signs but no bus sprite), Sendai's moored ferry (a boat on a
pier, and `AmbientTrams` is horizontal rails only) and Sapporo's streetcar (#219 stage 4, not placed yet).

## Approach

**Routes: the three become `tramways` lines of a new kind, a shuttle.** The generators stop placing the
vehicle tiles (and their colliders) and write `tramways` into the room's config instead, as Toyama's generator
already writes `waterways`. A line marked `"shuttle": true` has one car that is always in the street: it never
fades or leaves, stands at each terminus for `headway` seconds and runs back mirrored. Lines without the flag
behave exactly as today.

**Which way the art faces.** `AmbientTrams` assumes a car's art heads east and mirrors it going west. Both
trams are drawn heading **west** (amber head lamp on the left, red tail lamp on the right:
`tools/generate_hokuriku_art.py` `tram`, `tools/generate_sanfranbourne_art.py` `tram`); the cable car is
symmetric. So a tramway may say `"faces": "west"` (default east): the car is mirrored only when it runs against
its art, and a shuttle's **first trip heads the way its art faces**. Without this the trams would run tail lamp
first, with the night headlight glowing on the red lamp.

San Franbourne gets **two shuttles, split at the avenue**: the cable car on the western rails, the tram on the
eastern. `docs/ambient-traffic.md` sketched one line with both sprites taking turns; that is rejected because a
car that fades out at a terminus cannot keep a passenger and is absent most of the time. Two lines on one row
are safe here because their cells do not overlap (a test holds that).

**On room load each car stands at its first stop, which is the cells it occupies today, unmirrored** (the
first trip heads the way the art faces), so the towns look exactly as authored until it pulls away.

**Collision.** A moving car stays what it is today: decoration that passes through people (the documented
level-crossing rule). A shuttle **standing at a stop or terminus is solid** over its art's cells, through one
dynamic check in `CollisionSystem`. That is what makes the bump, the game's one way of using anything, work.
The car is not a tile, so this is not an `Interactions` rule. `CollisionSystem` is also run by
`tools/world-model.js` (`play.js`) and the unit tests, whose scene has no `ambientTrams`: the check is skipped
there.

**Riding** is a small new class, `TramRide`. While riding, the player's sprite is hidden and placed at the
car's middle on the rail row every frame, and `gridX` / `gridY` are the cell under it; so the camera follow,
chunk streaming, the district in the HUD and the map dot all keep working unchanged. Input is the existing
keys only: the menu (ESC) still opens; the direction keys do not walk; up / down at a halt gets off **on that
side only** (if that side is blocked you are told so and stay on: being put off on the other side with the key
still held would walk you straight back into the car and on board again). It is free (no fare).

## Changes

### `src/AmbientTrams.js`

Pure functions (unit-tested):

| Function | Change |
|---|---|
| `line(def, layers, offset, cols)` | Result gains `shuttle` (bool), `name` (string, default `'tram'`, used in toasts) and `faces` (`-1` when `def.faces === 'west'`, else `1`). `def.shuttle === true` with an open end or more than one sprite returns `null` (cannot run). |
| `flipped(dir, faces)` (new) | `dir !== faces`: the art is mirrored only when the car runs against the way it is drawn. With no `faces` this is today's `dir < 0`. |
| `direction(trip, faces)` | Gains `faces` (default `1`): `faces` on even trips, `-faces` on odd ones, so a car's first trip heads the way its art faces. Without it, as today. |
| `plan(line, opts)` | For a shuttle: a stop's left edge is snapped to whole cells, `Math.round((s.x + 0.5) - width / GS / 2) * GS` (odd-width cars are unchanged; the 4-wide tram no longer straddles half cells); after the last run a **layover leg** `{ x0: toX, x1: toX }` of `headway * 1000` ms is appended; the plan carries `shuttle: true`. |
| `at(plan, ms)` | `alpha` is 1 for a shuttle plan. |
| `firstHalt(plan)` (new) | `t0` of the first leg with `x0 === x1` (a stop, else the layover). |
| `footprint(row, x, GS, width, height)` (new) | Cells under a car whose left edge is `x`: `{ x0: Math.round(x / GS), x1: x0 + Math.round(width / GS) - 1, y0: row - Math.round(height / GS) + 1, y1: row }`, inclusive. |

Runtime:

- `depart`: `dir` defaults to `direction(state.trip, line.faces)`; `img.setFlipX(flipped(plan.dir, line.faces))`
  (replacing `plan.dir < 0` and its "the art heads east" comment). A shuttle's **first** departure
  (`state.trip === 0` before the increment) sets `t = firstHalt(plan)`. The rule lives here, not in
  `onRoomChange`, so the three ways a car starts (room load, `cross`, the retry after a texture that was not
  loaded yet) agree.
- `onRoomChange`: a shuttle's state starts with `wait: 0` and is departed at once.
- `update`: when a shuttle's trip ends it is not retired: a new plan with `dir = -plan.dir`, `t = 0`, the same
  image with `flipX` updated through `flipped`. Other lines are untouched.
- `carAt(x, y)` (new): the line state of a shuttle that is halted now (`at(...).stopped`) and whose footprint
  holds the cell, else `null`. A line with no `plan` or `image` (its texture is missing) has no car: skipped.
- `cross(index)` on a shuttle resets `trip` to 0 and departs, so it starts over in its first halt as on room
  load (testing).

### `src/TramRide.js` (new; add to `index.html` after `AmbientTrams.js`)

`scene.tramRide = new TramRide(scene)`, built in `GameScene.create` beside `ambientTrams`.

- `riding` (getter): a car is being ridden.
- `check(x, y)`: called on a bump. `car = ambientTrams.carAt(x, y)`; none, or `roomManager.isTransitioning`:
  `false`. Otherwise board: remember the car's **line state** (not its image), set `carried = true`, hide the
  player, toast `Hints.text(scene, 'On the <name> · ↑/↓: get off at a stop')` via `scene.shop.toast`, return
  `true`.
- `update()`: while riding, every frame: read `state.image` and `state.plan` afresh; if either is gone (the
  line was cleared or re-sent under the rider) end the ride where the player is: show the sprite,
  `setIdleFrame()`, clear the car. Otherwise `player.sprite.setVisible(false)`; sprite at
  (`img.x + img.width / 2`, `(row + 0.5) * GS`); `gridX = Math.floor(sprite.x / GS)`, `gridY = row`. When the car
  goes from moving to halted, toast `Hints.text(scene, '↑/↓: get off')`.
- `handleInput(heading)`: applies `TramRide.step`; on a side, `alight(side)`.
- `alight(side)`: `TramRide.alightCell(...)` with `free = (x, y) => scene.checkCollision(player, x, y, x, y)`.
  A cell: set `gridX` / `gridY` and the sprite to it (`cell * GS + GS / 2`), face away from the car
  (`updateDirectionSprite(0, side)`), `setIdleFrame()`, show the sprite, clear the car, then
  `scene.checkTransporter()` as a finished step does (so a door or a station's board cell beside a stop acts
  as if stepped onto, rather than leaving the player standing on it unfired; there is none beside today's
  lines). None: toast `'No room to get off on this side'`, stay on.
- `onRoomChange()`: a ride in progress ends: clear the car, show the sprite (the room swap places the player).

Pure functions:

| Function | Rule |
|---|---|
| `TramRide.step(carried, heading, halted)` | Returns `{ carried, side }`. Heading `{0, 0}`: `carried` false, no side. Still `carried` (the key that boarded is still down): no side. Otherwise `side = heading.y` (-1 north, 1 south) when `halted` and `heading.y !== 0`, else no side. |
| `TramRide.alightCell(foot, side, free)` | Columns `foot.x0..x1` ordered by distance from `Math.floor((x0 + x1) / 2)`, west first on a tie; tried on the asked side's row only (`y0 - 1` north, `y1 + 1` south). First `free(x, y)` wins: `{ x, y }`; none: `null`. It never falls to the other side. |

### Wiring

- `src/systems/CollisionSystem.js` `checkCollision`: after the noclip return, `false` if
  `this.scene.ambientTrams` exists and any cell to check has `carAt(x, y)`. The guard is required: the same
  class runs in `tools/world-model.js` and under `tools/test_game.js`, where the scene has no `ambientTrams`.
  It applies to NPCs too. Only target cells are tested, so someone the car stopped on can step out; a player
  who steps further into it boards.
- `src/GameScene.js`: build `tramRide`; in `checkNPCInteraction`, right after the NPC check,
  `if (this.tramRide && !this.dialogueManager.isVisible() && this.tramRide.check(targetGridX, targetGridY)) return;`
  (the guard every other bump handler there has: an NPC the car stopped on is talked to, not talked to and
  boarded at once); in `update`, `this.tramRide.update()` directly after `ambientTrams.update(...)`; fix the
  comment on the `ambientTrams` line.
- `src/systems/InputHandler.js`: `heading(latched = false)` reads each key through `this.held(key)` when
  `latched` (a tap that goes down and up between two frames is otherwise never seen; `ShrineVisit`'s callers
  are unchanged). In `routeInput`, after the menu branch and before `handlePlayerMovement()`:
  `if (tramRide && tramRide.riding) { tramRide.handleInput(this.heading(true)); <sync lastKeyState.up / .down from isDown, as handlePlayerMovement does>; return; }`.
  Without the sync an up / down held on the tram moves the menu's selection when ESC opens it (the #220 class
  of bug).
- `src/systems/RoomManager.js` `applyRoomSwap`: `tramRide.onRoomChange()` before `ambientTrams.onRoomChange`.

No change to `Occlusion`, the name label or `updateCharacterDepths`: all three already skip or follow a hidden
player sprite.

### Map data (rooms touched: **Toyama** in `HokurikuCity`, **SanFranbourne**)

- `tools/generate_toyama.py`: drop `TRAMCAR` and its `b.stamp('toyama-tram', ...)` (and from the final
  `print`); write `cfg['rooms']['Toyama']['tramways']` beside `waterways`; update the docstring.
- `tools/generate_sanfranbourne.py`: drop the two `place('Collidables', ...)` calls for `sfb-cable-car` and
  `sfb-tram`; write `cfg['rooms'][KEY]['tramways']` before `rg.save_config`.
- Run both generators, then `python3 tools/config_to_tiled.py Toyama SanFranbourne`, then rebuild `assets/map`
  with `tools/make_worldmap.py` (Pillow).
- Nothing is removed from `tilePalette`, `spriteMetadata` (the cars must stay loaded) or `tools/make_prefabs.py`.

### Docs

- `docs/ambient-traffic.md`, Streetcars: which rooms declare lines; `shuttle` and `name`; halted cars are solid;
  riding; replace the "Could it run San Franbourne's cable car and tram?" paragraph with what was built.
- `docs/architecture.md`: `TramRide.js` in the file list, the `AmbientTrams.js` line, a sentence under
  Collision Detection.
- `docs/hud-input-touch.md`, Input Handling: on a tram the direction keys do not walk; up / down gets off.
- `docs/landmarks-and-towns.md` (Toyama, line 192): the tram runs.

## Data and interfaces

`config.json` (written by the generators; coordinates are the room's own):

```json
"Toyama":        { "tramways": [
  { "row": 21, "from": 11, "to": 40, "sprite": "toyama-tram_0_0", "shuttle": true, "name": "tram",
    "faces": "west", "stops": [21], "speed": 256, "dwell": 6, "headway": 8 } ] }
"SanFranbourne": { "tramways": [
  { "row": 16, "from": 4,  "to": 27, "sprite": "sfb-cable-car_0_0", "shuttle": true, "name": "cable car",
    "stops": [11, 20], "speed": 192, "dwell": 5, "headway": 8 },
  { "row": 16, "from": 33, "to": 55, "sprite": "sfb-tram_0_0", "shuttle": true, "name": "tram",
    "faces": "west", "stops": [48], "speed": 256, "dwell": 6, "headway": 8 } ] }
```

- New optional keys on a tramway: `shuttle` (bool), `name` (string) and `faces` (`"east"`, the default, or
  `"west"`: the way the sprite is drawn heading). On a shuttle `headway` is the seconds it stands at each
  terminus.
- First stops put each car on today's cells: Toyama 19-23 (under the shelter at 20-22), cable car 10-12, tram
  47-50. The two trams set off west first (their art's heading), the cable car east; the first halt is the same
  stop either way. Stop 20 is San Franbourne's bus-stop sign; the tram's line starts at 33 so the car clears the traffic
  light drawn over column 32. Speeds are a starting point (walking is 320 px/s): tune by eye.
- No save data, no new keys, no new art.

## Tests

Unit (`node tools/test_game.js`):

- `tools/tests/glows-trams.test.js`, new tests: `line` sets `shuttle` / `name` / `faces` and refuses a shuttle
  with an open end or two sprites; a shuttle `plan` has cell-aligned stops for widths 192, 256 and 320, ends
  with a layover leg of `headway`, and `at` gives alpha 1 at both termini; `firstHalt` (the same stop for
  `dir` 1 and -1 on a one-stop line); `footprint`; `flipped` and `direction(trip, faces)` (east-facing art:
  as today; west-facing art: first trip west and unmirrored, mirrored going east); a non-shuttle plan is
  unchanged (the existing tests stay as they are). Extend `checkTramways`: a declared `shuttle: true` yields
  `line.shuttle`; no two lines of a room on one row overlap; every halt of a shuttle's two plans (both
  directions) is on whole cells; every cell `from..to` on the car's rows is free of `Colliders`; every halt
  has a walkable cell on the row north **and** one on the row south of its footprint (a side is never
  silently swapped, so each must work). The test has no textures: a car's size in cells comes from
  `spriteMetadata` (`Math.round(0.5 / anchorX)` wide, `Math.round(0.5 / anchorY)` tall: 5x2, 3x2, 4x2 for the
  three).
- New `tools/tests/tram-ride.test.js` (it loads `src/TramRide.js` into the runner's context itself, as
  `glows-trams.test.js` loads `AmbientTrams.js`): `TramRide.step` (held boarding key does not get off; release
  then up / down does; nothing while moving; left / right never) and `TramRide.alightCell` (middle column
  first, a blocked cell moves along the same row, never the other side, `null` when that side is walled in).
  And the collision rule, on the `WorldModel` the runner already builds (its scene has no `ambientTrams`):
  a step it allowed before is still allowed (no crash on the missing mover); with a stub
  `ambientTrams = { carAt }` set on that scene, `checkCollision` refuses exactly the cells the stub names.
- The latched heading and the `lastKeyState` sync are Phaser-side glue: the browser check below covers them.
- `tools/tests/kanazawa.test.js` lines 294-296: replace with: at least 20 rails on one row; no `toyama-tram_0_0`
  tile; one shuttle on that row spanning exactly the rails; its stop is in the shelter's columns.
- `tools/tests/airports.test.js`: remove `sfb-cable-car` and `sfb-tram` from `LANDMARKS` and assert neither is
  placed; replace the "is on the rails" loop with: two shuttles on the rails' row, one per sprite, every cell of
  each on a rail tile.

Browser (`tools/browser/regress.js`, see `tools/browser/README.md`), two new checks:

- `tram-ride`: `switchRoomInstant('Toyama', 21, 19)`, `ambientTrams.cross(0)`; the car is on cells 19-23 and
  not mirrored. A real down key, held with `hold()` until `tramRide.riding`: the player hidden, a toast shown,
  and still on board while the key stays down. Do not wait out the timetable (a dwell of 6 s and a run of
  3 to 6.4 s, twice, would add half a minute to a 25 s regression): it is a pure function of time, so the check
  moves the clock, `lines[0].t = <t0 of the plan's next halt leg> - 300`, then waits for `at(...).stopped`.
  Then: `gridX` has moved along the line and the camera's `worldView` holds the car. Open and close the menu
  with up held: the selection has not moved. A real up key held until not riding: the player visible on row 19
  above the car, facing up, and (key still held a moment) walking away, not back on board. Walking down into
  the standing car from outside boards again.
- `phone-landscape-tram`: the same with `&touch=1` at 844x390, boarding and getting off with the d-pad; the
  toast reads `d-pad`, not `↑/↓`.

All checks, from `gamev2/`: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`,
`node tools/play.js check`, `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`, plus
`node tools/play.js lint Toyama` and `lint SanFranbourne`. The art checks and `make_worldmap.py` need Pillow:
`python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -r tools/requirements-art.txt` works in the Workshop
container.

Play it before returning: all three cars, both directions (the amber lamp leads, and at night the headlight
is on it), day and `?tod=night` (the car is lit), stitched and `?stitch=0` for Toyama, 1280x960 with keys and
844x390 with touch; open the menu and Time Travel mid-ride; get off north at the cable car's second stop,
where the bus-stop sign (20,14) takes the middle cell (you are put off at 19,14, not on the south side); no
halt on today's maps has a whole side blocked, so the "no room" toast is the unit test's to hold;
`node tools/play.js` `warp` and `move` across both streets (the terminal player has no cars and must not
crash).

## Risks and open questions

- **A moving car still passes through people** standing on the rails. Kept on purpose (the existing rule);
  making the timetable wait for obstacles is a different, larger change.
- **A car that stops on someone** makes them solid-surrounded for a few seconds: they can always step out of
  the footprint, except a cell with a blocker directly behind it (San Franbourne 20,15 under the bus-stop sign),
  where a player's next step boards and an NPC waits out the dwell.
- **The world map pictures lose the three vehicles**, since they are no longer map tiles; so do Tiled, Studio
  and `play.js render`. (`assets/map/world-map.png` is tooling art; the game does not draw it.)
- **Walking into a standing car boards it**, wanted or not. In Toyama the way south (columns 18-19) passes the
  stop (cells 19-23): a player walking down column 19 while the car stands there is on board, and gets through
  by letting go and pressing down again (off on the south side). Column 18 is clear.
- **Riding paints the rail row** for the Paint the Board achievement (`gridX` / `gridY` follow the car), and
  the cells under the old static cars become walkable ground like the rest of the street. Harmless.
- **`play.js` does not model the cars** (as with the other ambient movers): the terminal player cannot ride,
  and sees open road where they stood.
- **Riding is slower than sprinting** and the lines are short (about 25 cells): it is charm, not transport.
  Speeds and dwells are config and easy to change.
- Open: buses need a bus sprite (art), and Sendai's ferry needs a vertical, water-borne mover. Neither blocks
  this change.

## Review

Design adversary pass. Each point: what is wrong, the fix, and whether the body above now has it.

1. **The collision check would crash the terminal game and the tests.** `CollisionSystem` is not only the
   browser's: `tools/world-model.js` (so `play.js`, `play.js check`) and `tools/test_game.js` build it on a
   scene with no `ambientTrams`, and the design called `scene.ambientTrams.carAt(...)` unguarded.
   Fix: `this.scene.ambientTrams &&` before the call; a unit test on the world model with and without a stub
   mover. **Adopted.**
2. **The trams would run backwards.** `AmbientTrams` mirrors a car going west because "the art heads east",
   but both trams are drawn heading west (amber head lamp left, red tail lamp right); only the cable car is
   symmetric. As designed they run tail lamp first, the night headlight sits on the red lamp, and on load the
   tram is the mirror image of today's tile. Fix: a `faces` key (`"west"`), `flipped(dir, faces)`, and a first
   trip that heads the way the art faces, so the car on load is pixel for pixel today's. **Adopted.**
3. **Getting off on a blocked side put you straight back on.** `alightCell` fell to the other side; the key is
   still held, so the next frame walks the player into the solid car and boards again (and again at the next
   press). Fix: the asked side only; a toast, `'No room to get off on this side'`, when it is blocked; the
   config test now wants a free cell on both sides of every halt. **Adopted.**
4. **Bumping an NPC the car stopped on both talked and boarded.** The boarding check ran after the NPC check
   with no guard, unlike every other handler in `checkNPCInteraction`. Fix: `!dialogueManager.isVisible()`.
   **Adopted.**
5. **Input while riding dropped taps and left a stale key state.** `heading()` reads `isDown` only, so a tap
   that goes down and up between two frames never gets off (the regression README warns about exactly this);
   and returning before `handlePlayerMovement` never syncs `lastKeyState.up / down`, so an up or down held on
   the tram moves the menu selection when ESC opens it. Fix: `heading(true)` reads the latched keys; the
   riding branch syncs the two states. **Adopted.**
6. **The browser check's timing was wrong, and waiting is the wrong method.** "Halt again in under 10 s":
   Toyama's dwell is 6 s and its run to the east terminus 6.4 s (1088 px at 256 px/s, eased at both ends,
   x1.5), 12.4 s; two checks that sit through that add about half a minute to a 25 s regression. Fix: the
   timetable is a pure function of time, so the check sets the line's clock to just before the next halt; keys
   are held with `hold()` until the game has seen them. **Adopted.**
7. **Getting off onto a door would leave the player standing on it unfired** (`checkTransporter` only runs
   when a step finishes). None is beside today's lines, but nothing kept it that way. Fix: `alight` calls
   `scene.checkTransporter()` like a finished step. **Adopted** (one line; rejecting such cells would need a
   new lookup).
8. **A ride could outlive its car.** `TramRide` kept the image; `cross()`, a room swap or a texture that is not
   loaded leaves a destroyed or missing image, and `carAt` would read a `null` plan. And the "start in the
   first halt" rule sat in `onRoomChange` only, so the retry path after a late texture started the car
   elsewhere. Fix: the ride keeps the line state and ends itself when its image or plan is gone; `carAt` skips
   a line with no car; the first-halt rule moves into `depart`. **Adopted.**
9. **The pinned map test could not know a car's size.** "The car's rows" and "cell-aligned" need the art's
   width and height, and the unit tests have no textures. Fix: take the cells from `spriteMetadata` anchors
   (`0.5 / anchorX`, `0.5 / anchorY`), and assert every halt of both directions is on whole cells. **Adopted.**
10. **`tram-ride.test.js` would not find `TramRide`.** The runner loads a fixed list of source files. Fix: the
    test loads `src/TramRide.js` itself, as the tram tests load `AmbientTrams.js`. **Adopted.**
11. **Walking into a standing car boards it whether you meant to or not**, and Toyama's way south passes the
    stop. A simpler car that is not solid (board by stepping into its cells) was considered: it has the same
    accident, and a car that halts on a standing player would then have to decide whether they are aboard.
    The bump is the game's rule for using things. **Not changed**; the accident and the way through are now
    under Risks.
12. **Riding is slower than walking** end to end (Toyama: 15.4 s for 25 cells against 5 s on foot), mostly
    dwell. **Not changed**: the numbers are config, the ticket asks for moving and rideable, not for fast, and
    how long a tram should stand is the owner's taste. Shorten `dwell` / `headway` if it drags in play.
13. **Maps lose the vehicles** (world map, Tiled, Studio, `play.js render`). **Not changed**: a car that moves
    cannot also be a tile, and the world-map PNG is not drawn in the game. Now stated under Risks, with the
    side effects on Paint the Board.
14. **Scope against the ticket ("buses or trams, etc").** Checked every room: the only vehicle sprites are
    these three and Sendai's ferry; ten rooms have a bus-stop sign and none has a bus. Buses and the ferry are
    #249. **No change**: the design covers what exists.

Checked and found right: neither line reaches a room edge (no "open" end); the rail rows and the row above
are free of colliders once the tiles are gone; the stop snapping lands on today's cells (19-23, 10-12, 47-50);
`Occlusion` and the name label already handle a hidden player; the car textures load from `spriteMetadata`;
`Hints` turns `↑/↓` into `d-pad`; the stitched city's offsets are applied by `declared()`; the browser
regression has no existing check in Toyama or San Franbourne to disturb.
