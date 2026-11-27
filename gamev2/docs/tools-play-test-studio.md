# Tools: play.js, test_game.js, the Studio and the editor

Playing and checking the game without a browser (`tools/play.js`, `tools/test_game.js`), the Studio and the `config.json` editor.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

## Playing and testing without a browser

**Option 3: No browser (for agents)**
`node tools/play.js <command>` plays the game as text: it loads the real map, collision and NPC-date
code from `src/` into Node, with no Phaser and no dependencies. Walk, talk to NPCs, follow teleports,
ride trains, `fly` between the airports, time travel, inspect cells, `lint` a room's map, `render` it to a PNG, and run `check` to
confirm the world is still playable after a map change. `node tools/play.js help` lists the commands; the `play-game` skill
(`.claude/skills/play-game/SKILL.md`) is the full guide, including what the tool cannot do.
It plays the world the game plays: the Tokyo districts are stitched into one room by the game's own
`CityStitcher` (see "Stitched cities" in `stitched-city.md`), so `goto Market 5 24` from Tokyo is one walk with no teleport,
`where` reads `Market 5,24 (TokyoCity 111,24)`, and every coordinate you type or read is still the
district's own. `--stitch=0` anywhere on the command line models what `?stitch=0` plays instead.
Furniture you can sit on (`src/utils/Seats.js`) is `h` on `look` / `map`: blocked for `goto`, `reach` and
`check`, which never route over it, but `move` straight into it gets you on it as the game does
(`w: got on the bed at 5,6`, with the line it says if it has one) and carries on with its count.
`WorldModel.step()` reports it as `{ moved: true, seat, interaction }`; `inspect` names the seat on a cell.
A door that is a lift (into or out of an observation deck, `RoomManager.liftFor`) is a teleport like any other
here: `step()` reports `transported: { from, to, lift: 'up' | 'down' }` and `move` prints
`transported Fukuoka -> ... (the lift goes up)`. The ride the game plays in between (`ViewRide`) is not modelled.
Nor is the turn on Osaka's wheel: walking into the gondola at its foot is a bump that answers
`rides the wheel: one turn, the view over Dotonbori, and back on this cell` (the `ride` group, `*` on the map).

`node tools/test_game.js` runs the game's own decision code in Node, with no browser: which train a
station parks, the departures board's order and scrolling, room display names, the dialogue hint wording,
touch buttons cancelling their touch, which post a dialogue line is captioned with, the default game date,
trips (which NPCs exist on a date, where a player starts, what the intro says, Time Travel's trip jump).
When a fix lives in a Phaser-side class, pull the decision into a static function there and add a case.
The tests live in `tools/tests/<area>.test.js` (`test_game.js` is only the runner and its shared helpers): add a
`test('name', () => { ... })` to the file for its area, or start a new `*.test.js` there — it is found by name,
no other file needs an edit, and a name already used anywhere is an error.

## Studio

`studio/` is a read-only view of the whole world for developers, served at `/studio/` (locally
`http://localhost:8000/studio/`, live at `game.devhou.se/studio/`). It lays every room out together and
overlays collision, unreachable cells, teleports (arrows to their targets), train links, interactions and
where each person stands on a chosen day. Click a cell for its tiles, what a bump does, the NPC's lines
and photo, and the `play.js` command that puts you there. Maps are still edited in Tiled.
Rooms are laid out by where their towns are in Japan (`config.json` `places`, through `WorldModel.geoOf`):
Hokkaido top right, Fukuoka bottom left, a station or an interior beside its town. The links still decide
what sits next to what, and SanFranbourne sits where the in-game Map draws it, off the south-east.
Tokyo is drawn as the one stitched city the game plays (woodland included, the four districts outlined and
named inside it; the inspector gives the district's own cell and the city cell, the owning district where two
overlap); the **Stitched** button, or `/studio/?stitch=0`, shows the four rooms joined by seam teleports instead.
In that four-room view, where a city's districts overlap on the map (Palace / Park share four rows) the later
district in the city's `rooms` list is drawn on top and takes the click, as in the stitched city
(`WorldModel.stackOrder`). Click the selected cell again for the room underneath (`WorldModel.stackPick`):
that is how the covered seam transporters (Palace 38..39,21, Market 54..56,47) are inspected - and, in the
stitched view, the city's woodland under a town that sits inside its box (none does since issue #174).

It has no logic of its own: `tools/world-model.js` (rooms, collision, NPC dates, interactions, the
problem survey) is shared with `tools/play.js`, so the page and the terminal tool always agree.

### Editing in the Studio

The Studio is read-only until **Edit** is pressed (Chrome or Edge on a computer; the button is absent
elsewhere). Edit asks for the repo folder (or `gamev2/` itself), reloads the world from those files as the
separate rooms each `tiled/*.tmj` holds (never the stitched city), and adds:

- a library of the prefabs in `tiled/prefabs/` - pick one, click a cell to stamp its sprites and colliders;
- **Select** - click a cell, pick a thing on it (person, door, sprite), drag it to move it, Remove it, or
  for a door change where it leads and whether it is hidden. Moving or removing a sprite takes the
  colliders under it that no other standing sprite covers;
- **Solid** - drag to paint colliders, starting on a solid cell to clear them (Shift-drag pans);
- **Link** - click two cells to join them with a hidden door each way (each arrives beside the other).

Every action is a line in the change list with Undo; **Save** writes the changed `tiled/*.tmj` (and
`config.json` when a person moved) into the folder. Nothing is committed - that stays with git.
`studio/edit.js` holds the map operations and a JSON writer that matches Python's `json.dump`, so an
untouched file saves byte-identical and a change is a minimal diff. It has no DOM code. Terrain painting,
new rooms and train stations are still done in Tiled and the generators.

### Visual Editor

`/editor/` edits one room of `config.json` at a time: inspect a cell, paint collision, place and edit
transporters, set the spawn, resize the room. It saves by downloading a new `config.json`. The game loads
rooms from `tiled/*.tmj`, so run `python3 tools/config_to_tiled.py <Room> [<Room> ...]` after replacing the
file (any number of rooms; an unknown name is an error and nothing is written).
