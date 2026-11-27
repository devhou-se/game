# Design: seats you can sit on, beds you can get into (#227)

All paths are under `gamev2/` unless they start with `docs/workshop/`.

## Context

Every chair, stool, sofa, bench and bed is a solid block: its art is on `Collidables` and an invisible
`gk_blank` collider sits under it, so the player walks round it (`227-design-bed-today.png`). The ticket asks
that the player can get onto them — no new animation, "just the ability to stand on top of them to look like
they're on the furniture" — and that in a bed the sheets are drawn over the player so they look tucked in.

Outcome: walking into a seat puts you on it, sat the way the seat faces; walking into a bed puts you in it,
head on the pillow, blanket over you. Walking off is an ordinary step. Keyboard and touch alike, in every room
that has the furniture today. Mock-ups made by driving the real game from a throwaway script (no repo change):
`227-design-bed-tucked-mock.png`, `227-design-seat-poses-mock.png`.

## Approach

**Code only.** No change to `config.json`, `tiled/`, generators, art or `devhouse.world`. The furniture keeps
its sprite, layer and colliders; what makes it a seat is a rule table keyed by sprite name.

**Getting on is walking into it.** The game's one verb is the bump, so there is no new key. A blocked step is
allowed when it is the **player**, the step is **one cell, straight** (not diagonal), and the target is a
**solid seat cell** with no object or character on it. Seats stay solid to NPCs, to diagonal steps, and to
everything that asks "is this ground?": `CollisionSystem.checkCollision` is unchanged, so `world.canStep`,
`path`, `reachable()`, `play.js reach`, the lint and the blog pipeline's pinned reachability
(`test_blog_to_npc.py` `test_city_reach`) do not move. The seat step is a second question
(`checkSeatStep`), asked only by the player's own move.

Checked over the shipped world with a script (it becomes a unit test): every solid seat cell can be got onto
from reachable floor, and seats open exactly one cell of new floor — `Sapporo 41,29`, a snow pocket between an
Odori bench, a lamp post and two snowbanks. Harmless; pinned in the test.

**The look is three things**, all derived each frame from where the player is, none saved:

1. **Lift** — the sprite is drawn `dy` px off its cell (up onto a seat cushion, down onto a pillow) by moving
   its origin, so `sprite.x/y`, depth sorting, the camera and Occlusion see the same cell-centred sprite as
   ever. While stepping, `dy` slides from the old cell's value to the new one's.
2. **Facing** — at rest the player is turned the way the seat faces (`face`); stools and backless benches
   leave you as you arrived.
3. **Layering** — on a solid seat the player sorts as if standing at the furniture's foot row
   (`max(own feet row, y + h)`), which puts them over a two-cell bed instead of under it. A **cover** — a
   second image of the same furniture sprite, cropped to a rectangle (blanket, bath water, a chair back seen
   from behind) — is drawn one depth step above the player. That is the "tucked in", with no new art.

   During a step the seat being entered and the seat being left both stay in force (depth and covers), so the
   player slides under a blanket and out from under it rather than popping.

**A separate table, `Seats.RULES`, not rows in `Interactions.RULES`.** `Interactions.match` gives one rule per
sprite and the bunk and the bath already have their `flavour` rule; and `houses.test.js` / `lobbies.test.js`
pin that a futon and a lobby sofa answer no bump. A seat is not something a bump opens. `Seats` is shaped like
`Interactions` (pattern → data, footprint from the sprite size, an index per room).

**Flavour lines.** The bunk and the bath can no longer be bumped head-on, so their existing `flavour` line is
said when you settle on them (same toast, same guards). Nothing else speaks.

### What is a seat

Seat cells are the footprint cells that are **blocked** (a station bench is 2×2 with only its bottom row
solid: that row is the seat). `open: true` means the opposite: the footprint's walkable cells are the seat
(pose only — no step rule, cover or depth change). `pose` is one pose, or an array with one per footprint
row, top first. `dy` and `cover` are starting values from the prototype: tune them by eye, to the look given.

| kind | pattern | pose | look |
|---|---|---|---|
| `stool` | `^(izakaya-stool\|devhouse-stool\|devhouse-garden-seat)_` | `{ dy: -14 }` | feet on the seat top |
| `chair` | `^devhouse-chair-n_` | `{ face: 'down', dy: -10 }` | sat facing the viewer |
| `chair` | `^devhouse-chair-s_` | `{ face: 'up', dy: -12, cover: [0, 0, 64, 64] }` | head over the chair back |
| `chair` | `^devhouse-chair-w_` / `-e_` (two rows) | `{ face: 'right', dy: -10 }` / `{ face: 'left', dy: -10 }` | side on, facing the table |
| `armchair` | `^devhouse-armchair_` | `{ face: 'down', dy: -8 }` | |
| `toilet` | `^devhouse-toilet_` | `{ face: 'down', dy: -8 }` | |
| `sofa` | `^lobby-sofa_` | `{ face: 'down', dy: -12 }` | on the cushions |
| `sofa` | `^lobby-sofa-back_` | `{ face: 'up', dy: -22, cover: [0, 0, 128, 64] }` | head over the sofa back |
| `sofa` | `^devhouse-sofa_` | `{ face: 'right' }` | on the cushions, back to the armrest side |
| `bench` | `^station-bench_` | `{ face: 'down', dy: -20 }` | on the planks, in front of the backrest |
| `bench` | `^station-bench-back_`, `open: true` | `{ face: 'up', dy: 6 }` | behind the backrest (the row is walkable today), head showing |
| `bench` | `^odori-bench_` | `{ face: 'down', dy: -16 }` | |
| `bench` | `^temple-in-bench_` | `{ dy: -22 }` | feet on the red cloth |
| `seats` | `^airport-seats_` | `{ face: 'down', dy: -12 }` | |
| `bed` | `^home-bed_` | `[{ face: 'down', dy: 14, cover: [0, 56, 64, 72] }, {}]` | head on the pillow, blanket to the chin; foot cell: stood on the blanket |
| `futon` | `^home-futon-` | `[{ face: 'down', dy: 12, cover: [0, 46, 64, 82] }, {}]` | same |
| `bunk` | `^devhouse-bunk_` | `[{ face: 'down', dy: 4, cover: [0, 40, 64, 40] }, {}]` | in the top bunk |
| `bath` | `^devhouse-bath_` | `[{ face: 'down', dy: 10, cover: [0, 52, 64, 76] }, { face: 'down', cover: [0, 100, 64, 28] }]` | in the water to the neck; lower cell: legs behind the rim |

`_` after the name keeps `lobby-sofa_0_0` and `lobby-sofa-back_0_0` (and the two station benches) apart.

### Not in this change

NPCs sitting; a sit animation or any new art; the kotatsu (a table: its bump line stays); zabuton (already
floor you walk on); the benches inside tram and bus shelters; map, generator or config edits; achievements;
a fresh-press gate (a held key walks you onto and across a sofa, as it walks you anywhere).

## Changes

### `src/utils/Seats.js` (new; pure, no Phaser — add to `index.html` after `Interactions.js`)

A plain object like `Interactions`:

- `RULES` — the table above: `{ kind, pattern, pose, open? }`.
- `match(key)` → the first rule or `null`.
- `index(room, { sizeOf, isBlocked })` → `Map "x,y" → cell`, each sprite key matched once (as
  `Interactions.all` does). `cell = { kind, key, x, y, w, h, row, pose, solid }`: `x,y,w,h` the furniture's
  footprint, `row` this cell's row in it, `pose` that row's pose (`{}` when none), `solid` whether the cell is
  blocked. First furniture to claim a cell keeps it.
- `lookup(index, x, y)` → cell or `null`.
- `canStepOn(cell, fx, fy, tx, ty)` → `cell && cell.solid && |tx-fx| + |ty-fy| === 1`.
- `dyAt(from, to, t)` → the lift between two cells (`null` = floor = 0) at progress `t` in 0..1, linear.
- `footRow(cells, feetRow)` → `max(feetRow, c.y + c.h for each solid c)`.

### `src/systems/Seating.js` (new; add to `index.html` after `Occlusion.js`)

`class Seating { constructor(scene); update(); onRoomChange(); }`, holding `this.covers` (two images, created
on first use, hidden when idle) and `this.on` (the cell settled on).

`update()` — nothing while `trainTravel.riding` (covers hidden). Otherwise, with `from` = the cell being left
(`startGridX/Y` while `isMoving`, else `gridX/Y`), `to` = `player.getTargetPosition()`, `a = rm.seatAt(from)`,
`b = rm.seatAt(to)` and `t` = how far the sprite is from `from`'s centre, in cells, capped at 1:

1. `player.setLift(Seats.dyAt(a, b, t))`.
2. At rest on a seat: if `pose.face` differs from the player's facing, set `facingX/Y`,
   `updateDirectionSprite`, `setIdleFrame`. If the cell's furniture is not `this.on`'s, remember it and, if
   `rm.interactionAt(x, y, 'flavour')` has a `say`, toast it under the same guards as the flavour bump in
   `GameScene.checkNPCInteraction`. At rest off a seat: `this.on = null`.
3. For the solid ones of `b`, `a`: `row = Seats.footRow(...)`; player depth `rm.yDepth(row * 10 + 5)`; one
   cover image per cell that has `pose.cover` — `setTexture(key)`, origin 0,0 at `(x, y) * GRID_SIZE`,
   `setCrop(...cover)` (after `setTexture`), depth `rm.yDepth(row * 10 + 6)`, visible. Hide unused covers.

`onRoomChange()` hides the covers, clears `this.on`, `player.setLift(0)`.

### `src/Character.js`

Keep `anchorX/anchorY` from the sprite config and `this.lift = 0`. Add
`setLift(dy)`: no-op when unchanged; else `sprite.setOrigin(anchorX, anchorY - dy / sprite.displayHeight)`.

### `src/systems/CollisionSystem.js`

Add `checkSeatStep(character, seat, tx, ty, fx, fy)`: `character.isPlayer`, `Seats.canStepOn(seat, …)`, the
target inside the boundary, and `checkObjectCollision` / `checkCharacterCollision` on the target cell.
`checkCollision` is not touched.

### `src/systems/RoomManager.js`

- `seatIndex = null` beside `interactionIndex` (constructor, `clearFloorTiles`).
- `seatAt(gridX, gridY)`: builds `Seats.index(this.rooms[this.currentRoom], { sizeOf, isBlocked })` on first
  use, then `Seats.lookup`. Lift the `sizeOf` closure out of `interactionAt` into a method both use.
- `applyRoomSwap`: call `scene.seating.onRoomChange()` with the other `onRoomChange` hooks.

### `src/GameScene.js`

- `this.seating = new Seating(this)` after `this.occlusion`.
- `checkCollision`: `collisionSystem.checkCollision(…) || collisionSystem.checkSeatStep(character,
  this.roomManager.seatAt(tx, ty), tx, ty, fx, fy)`.
- `update()`: `this.seating.update()` between `updateCharacterDepths()` and `occlusion.update()`.
- The player's name label follows the lifted sprite (`+ this.player.lift`).

### `tools/world-model.js`, `tools/play.js`, loaders

- Load `utils/Seats.js` wherever `utils/Interactions.js` is loaded for the model: `tools/play.js`,
  `tools/test_game.js` (both lists), `studio/index.html`.
- `WorldModel.seatAt(x, y)`: its own `Seats.index` (`sizeOf` = `this.cells`, `isBlocked` = `this.blocked`),
  cached, dropped in `enter()`.
- `step(dir)`: when `canStep` fails and `collisionSystem.checkSeatStep(player, this.seatAt(tx, ty), …)`
  passes, move and return `{ moved: true, seat, interaction }` (`interaction` = the cell's `flavour`, if any).
  `canStep`, `path`, `reachable` unchanged — `goto` never routes over furniture.
- `play.js`: `move` prints `w: got on the bed at 5,6` (plus the flavour line) and carries on with its count,
  as it does for `crossed`; `inspect` adds `a seat (bed): walking straight into it gets you on it` (open:
  `you sit when you stop here`); `look`/`map` print a solid seat cell as `h` where nothing else claims it,
  with the legend and a note line.

### Docs

`docs/architecture.md`: the two files in File Structure; a short "Sitting on furniture" section after
Collision Detection (the step rule, lift, facing, layering, how to add a seat). `docs/occlusion.md`: the
foot-row sort and the cover. `docs/tools-play-test-studio.md` and `.claude/skills/play-game/SKILL.md`: `move`
onto a seat, `h`. `docs/landmarks-and-towns.md`, where new furniture is told to add an `Interactions` rule:
"or a `Seats.RULES` row if it is something to sit on".

## Data and interfaces

No config, map, save or `localStorage` change; no new key binding, overlay or hint. New code surface:
`Seats` (above), `Seating`, `Character.setLift` / `.lift`, `CollisionSystem.checkSeatStep`,
`RoomManager.seatAt`, `WorldModel.seatAt`, `step()`'s `seat` field. Adding a seat later is one `Seats.RULES`
row, provided the sprite is on `Collidables` over colliders.

## Tests

New `tools/tests/seats.test.js` (names unique):

- **the table**: each family's key gives its kind and pose; `lobby-sofa` and `lobby-sofa-back` differ; kotatsu,
  tables, zabuton match nothing; every rule matches a sprite placed in the shipped world; a pose array is as
  long as the sprite is tall in cells; every `cover` lies inside the sprite (PNG header).
- **the index**: `HouseFukuoka1` bed at 5,6 → 5,6 (row 0, cover, solid) and 5,7 (row 1, solid);
  `AsahikawaStation` bench at 5,11 → only 5,12 and 6,12; bench-back at 6,7 → 6,7 and 7,7, not solid.
- **the step**: `checkSeatStep` true for the player straight onto the bed; false diagonally, for an NPC, with
  a character on the cell, for an open cell; `world.canStep` onto the bed still false and `world.reachable()`
  holds no solid seat cell.
- **the model**: from `HouseFukuoka1 6,6`, `step('w')` → `moved`, `seat.kind === 'bed'`, player at 5,6;
  `step('e')` steps off; `path()` to the far side of a seat goes round it.
- **the shipped world**: every solid seat cell of every room can be got onto from `survey().reach` by
  straight steps (over other seats if need be); the floor that seats open is exactly `Sapporo 41,29`.
- **the maths**: `dyAt` at 0, ½, 1 and floor↔seat; `footRow` on a bed's pillow row is `y + 2`, on a one-cell
  chair is the player's own.

Existing tests must pass unchanged (nothing they pin moves). Browser regression, `tools/browser/regress.js`:
add a `seats` check to `desktop()` — in `HouseFukuoka1` hold left from 6,6 into the bed: cell 5,6, facing
down, `player.lift > 0`, player depth above the bed's tile record, a visible cover above the player, the bed
not faded; hold right: lift 0, no cover, feet depth again; then onto `devhouse-chair-n` at `DevhouseTokyo3F
6,6` (lift < 0, facing down) — and one to the touch phone profile: the d-pad onto a lobby sofa. Screenshots
to `$SHOTS`.

Run from `gamev2/`: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js
check`, `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`, then the regression
(`tools/browser/README.md`). Then play it, desktop and `?touch=1` at a phone size, and look at a screenshot
of every row of the table at rest plus a bed mid-step in and out; put them in `/work/media/`.

## Risks and open questions

- **Pose numbers are by eye.** The mock used these values; the cast's other sprites and the back views may
  want a pixel or two. The table is the only place to change.
- **Furniture stops being an obstacle to the player** (a held key crosses a row of chairs). That is the
  ticket's "stand on top of them"; if it grates, gate the step on a fresh press (`ShrineVisit.fresh`) later.
- **The cover is not a tile record**: Occlusion and chunk streaming do not know it. Fine in ordinary rooms,
  which is where every seat is; a seat in stitched Tokyo would be the first test of it there.
- **`setCrop` / origin shift in Phaser 4.2** worked in the prototype with no console error; the regression
  check keeps it honest.
- **New seat sprites from other work** need a row; the tests catch a dead row, not a missing one.
- Owner's call, not blocking — built as listed unless told otherwise: the **bath and toilet** count as
  "other furniture that fits"; the **kotatsu** does not; the bunk's and bath's lines move from bump to sit.
