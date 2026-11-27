---
name: play-game
description: Play, explore, check or render the gamev2 world from the terminal with no browser — walk around, talk to NPCs, follow teleports, ride trains, time travel, inspect any cell, lint a room's map, render it to a PNG, and check the world for broken connections. Use whenever you need to know what is at a place, how to get somewhere, what an NPC says on a date, whether a cell is walkable, or whether a map change left the world playable. Reach for this before starting a browser.
---

# Play the game as text

`gamev2/tools/play.js` runs the game's own map, collision and NPC-date code in
Node. No Phaser, no browser, no install; each call takes about 0.2s.

```bash
cd gamev2
node tools/play.js help
node tools/play.js look
```

One command per call, or several on stdin (one per line, `#` for comments):

```bash
node tools/play.js <<'EOF'
reset
date 2025-11-04
warp Inaka 6 9
move w 3
EOF
```

Your room, cell, date and character persist between calls in a temp file, so
start a task with `reset` unless you mean to continue. The exit code is
non-zero if any command errored.

## Coordinates

Cells are `x,y` from the room's top-left, the same numbers as `gridX`/`gridY`
in `config.json`, Tiled cell coordinates, and the in-game debug inspector.
`n` is up (y - 1), `e` is right (x + 1).

**Tokyo is one stitched city.** The game merges Tokyo, Market, Palace, Park
and Machi into a single room (`TokyoCity`) and so does this tool — it runs the
game's own stitcher. Coordinates are still each district's own, everywhere:
`where` prints `Market 5,24 (TokyoCity 111,24)`, `look` rules its map in the
cells of the district you stand in (a neighbour's cells run negative or past
the edge), and `goto`, `inspect` and `warp` take district cells. Walking from
one district into the next is just a step (`walked from Tokyo into Market`);
`goto Market 5 24` from Tokyo is one walk. `map` draws your district, `map
city` the whole city; `lint TokyoCity` and `render TokyoCity out.png` work on
the merged room, woodland included. Add `--stitch=0` to any command to model
what `?stitch=0` plays: five rooms joined by hidden seam teleports.

## Reading the map

`look [radius]` draws the cells around you; `map` draws the whole room. The
top two rows are the x ruler (tens, then units) and each row starts with its y.

```
Osaka 24,10 on 2026-11-25 as james
      2         3
    8901234567890
  9 .....#>#.....
 10 ......@......
 13 $$...........
> 24,9 to OsakaStation 11,11 (hidden)
$ 18,13 vending
```

| Glyph | Meaning |
|---|---|
| `@` | you |
| `#` | blocked (collider or outside the boundary) |
| `.` | walkable |
| `h` | a seat: blocked, but `move` straight into it gets you on it (chair, sofa, bench, bed...) |
| `>` | transporter |
| `T` | train boarding cell |
| `$` | anything that opens a shop (vending machine, konbini counter or shelf, izakaya bar) |
| `~` | pond (fishing) |
| `?` | wall clock or calendar (time travel) |
| `^` | an airport's gate or departures board (flights) |
| `%` | water cooler or water shelf (free water) |
| `+` | what you use inside a shrine, temple or palace hall (offering box, fortunes, incense, the audience, the guestbook) |
| `*` | anything else a bump answers: furniture that says a line (a bunk, a bath, a locked door, a goldfish bowl) |
| `D` | izakaya drinking-game table |
| `J` | the job: a tower lobby's reception desk and lifts |
| letter | an NPC, by initial |

Everything marked is also listed under the map with its exact cell.

## Getting around

- `move <n|s|e|w> [count] ...` walks cell by cell: `move n 3 e 2`. It stops at
  the first blocked step and tells you what you bumped.
- Furniture to sit on is an `h`. A `move` straight into it gets you on it, as
  in the game (`w: got on the bed at 5,6`), and the walk carries on across it;
  `goto` never routes over furniture, and `reach` does not count it. What the
  tool cannot show is how it looks (the lift, the blanket over you): that is
  `src/systems/Seating.js`, in a browser.
- `goto [room] <x> <y>` pathfinds inside the current room and walks there
  (inside the Tokyo city name a district to cross into it: `goto Park 30 20`).
- Stepping on a `>` changes room, exactly as in the game. `goto` treats
  transporters as walls unless one is the destination, so it never teleports
  you by accident.
- Trains: stand on a `T` cell in a station room, then `ride <station>`
  (`ride osaka`). `ride` with no match lists the destinations. In a station,
  `where` names the parked train: the station's own, or the one you rode in on.
- `warp <room> [x y]` teleports. Without a cell it lands where a transporter
  or train would put you. Use it to get somewhere quickly, not to prove a
  place is reachable.

Bumping is how the game interacts, and it is the same here: walk into an NPC
to get their full dialogue and blog photo path, into a shop, pond, clock or
the izakaya table to learn what would open.

## Asking questions

| Question | Command |
|---|---|
| What rooms exist, how big, what is in them? | `rooms` |
| Where does every teleport lead? | `transporters [room]` |
| Who is where today, and what do they say? | `npcs` |
| Which days have blog content? | `dates` |
| What exactly is on this cell? | `inspect <x> <y>` |
| Is the world still playable? | `check` |
| Is this room's map well formed? | `lint [room]...` |
| What does this room look like? | `render <room> <out.png> [--scale 0.5] [--colliders]` |
| Which cells of a room can be walked to? | `reach [room]...` (JSON, the room's own cells) |

`inspect` lists every tile on every layer covering the cell (including
multi-cell sprites anchored elsewhere), whether a collider blocks it, any
transporter, and what bumping it does.

NPCs depend on the date and on who you are playing:

- `date <YYYY-MM-DD|today>` time travels. The trip ran October to November
  2025; today's date shows wherever each person's last post left them.
- `as <name>` plays a cast member (james, bailey, damian, dylan, julia). That
  person's NPC leaves the world, so to read Dylan's posts play as anyone else.

## Checking a change

After editing a map, a generator, transporters or NPC placements:

```bash
node tools/play.js check
```

It reports transporters that target a missing room, arrivals that land on a
blocked cell, transporters nobody can walk to, rooms nothing leads to,
NPCs standing on a collider or boxed in, and every room's `lint` errors (as
`Room: lint <kind>: ...`, e.g. a store cut off from its door). NPCs are checked for the current
date only, so set `date` first when the change is about a particular day. Any
problem makes the exit code non-zero (the list is printed after `error: `).

`lint` is the map QA gate (it replaced `qa_port.py`): floor holes, solid objects
with no collider, colliders under nothing, overlapping tree canopies, and tall
overhead sprites the player would walk under. With no room it checks them all;
any ERROR makes the exit code non-zero. `render` draws the room in the game's
draw order so you can look at the result; `--colliders` washes solid cells red.

```bash
node tools/play.js lint Osaka
node tools/play.js render Osaka /tmp/osaka.png --scale 0.5 --colliders
```

Then walk it: `warp` next to the change, `look`, and `goto` through any door
you touched in both directions.

## Testing game code that play.js cannot reach

`play.js` runs the world, not the screens. For logic inside a Phaser-side
class (`TrainTravel`, `DialogueManager`, `TouchControls`, ...), pull the
decision into a static function on that class, call it from the Phaser code,
and add a case to `tools/test_game.js`, which loads the real `src/` files into
Node with small stand-ins for `window` and events:

```bash
node tools/test_game.js
```

A class file loads in Node as long as it only touches `Phaser` inside methods.

## What it does not do

- **No live screen.** `render` gives a still picture of a room's map; nothing
  shows NPCs, the HUD, overlays or animation. The studio (`/studio/`) shows
  the whole world with people on it, in a browser.
- **No mini-games or shop.** Fishing, the drinking game, a shift at the job,
  buying items and the wallet are reported as "would open", not simulated.
- **NPCs do not wander.** They stand on their placed cell; in the game they
  drift up to two cells from it.
- **No diagonal steps**, and no overlays, menus, title screen or intro.

## How it stays honest

It loads `src/utils/ConfigCodec.js`, `src/utils/NpcStates.js`,
`src/utils/Interactions.js`, `src/systems/TiledAdapter.js`,
`src/systems/RoomManager.js`, `src/systems/CollisionSystem.js`, `src/Shop.js` and
`src/TrainTravel.js` unmodified, so maps, boundaries, collision, dated NPC states, interaction
triggers and shop catalogues follow the game's real code. Keep those files
free of Phaser calls at load time and in the parts the tool uses
(`initializeRooms`, `checkBoundary`, `checkCollision`, `Interactions`,
`Shop.VENUES`, `Shop.DEFAULT_ITEMS`).

`src/utils/Interactions.js` is the one table of what a bump opens: add a rule
there and the game, `look`, `map` and `inspect` all pick it up.

One thing is still mirrored by hand and must be updated with
the game: which NPCs exist for a date and character (`npcsIn` in
`tools/world-model.js`), from `GameScene.syncNpcPresence`.

The world itself (rooms, movement, pathfinding, NPC presence, the `check`
survey, the `lint` rules, the draw order) lives in `tools/world-model.js`, which the studio page
(`gamev2/studio/`, served at `/studio/`) loads too. Change behaviour there and
both follow; `play.js` is only the command layer. A new command is one entry in
`COMMANDS` plus a line in `help`.
