# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

It is the entry point only: what the game is, how to run and check it, the rules that apply to every
change, and an index of the topic files in `docs/`. Read this file, then the topic files the index points
to for the area you are changing. Document a new system in its topic file; add an index line here only for
a new file. Do not append subsystem detail to this file.

## Project Overview

This is a browser-based 2D grid game built with Phaser 4.2.0. It features grid-based movement, a room/teleportation system, and Python-generated sprite tiles.

Blog posts from the devhouse trips become dated NPCs you can walk up to and talk to; the game date
(`?date=YYYY-MM-DD`, Time Travel) decides who is where. It is served at `game.devhou.se`.

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
`node tools/play.js <command>` plays the game as text (walk, talk, ride trains, time travel, inspect
cells, `lint`, `render`, `check`). `node tools/play.js help` lists the commands; the `play-game` skill
(`.claude/skills/play-game/SKILL.md`) is the full guide. Details: `docs/tools-play-test-studio.md`.

Useful URL params: `?notitle=1&nointro=1` (skip the title and first-visit intro), `?date=YYYY-MM-DD`,
`?tod=day|night`, `?touch=1`, `?stitch=0`.

## Checks to run before finishing

From `gamev2/`:

```bash
node tools/test_game.js                 # the game's decision code, no browser
python3 tools/test_blog_to_npc.py       # the blog pipeline, placements, shipped history
node tools/play.js check                # the world is still playable (every trip day surveyed)
python3 tools/check_generators.py       # generators still rebuild the committed world; .tmj in step
python3 tools/sync_cities.py --check    # config `cities` and devhouse.world agree
```

- Plain `python3` has no Pillow: `check_generators.py` lists the art tools as `skip` without it. Use
  `/Library/Developer/CommandLineTools/usr/bin/python3` to cover them, and for any imaging tool. Elsewhere a venv with
  `pip install -r tools/requirements-art.txt` (the Pillow the Checks workflow uses; any 11.2 or newer works): PNGs are compared by pixels, not bytes (`docs/generators-and-checks.md`).
- After a map edit: `node tools/play.js lint <Room>` and look at `node tools/play.js render <Room> out.png`.
- After touching `blog_to_npc.py`, a Hokkaido map, the trips or the cast: `python3 tools/rehearse_blog.py`.
- A change the player can see: run the browser regression, `tools/browser/regress.js` (how: `tools/browser/README.md`).
  If you change behaviour it asserts on purpose, update that assertion in the same commit, strictly.
- Add or extend a unit test for logic you change (`tools/tests/*.test.js`, `tools/test_blog_to_npc.py`). When a
  fix lives in a Phaser-side class, pull the decision into a static function there and add a case.
  The tests live in `tools/tests/<area>.test.js` (`test_game.js` is only the runner and its shared helpers): add a
  `test('name', () => { ... })` to the file for its area, or start a new `*.test.js` there — it is found by name,
  no other file needs an edit, and a name already used anywhere is an error.

## Working on issues

Claiming an issue, working beside other agents, verifying as a player, landing and fixing are in
`docs/working-on-issues.md`. Read it before starting: several agents push to `master`, Workshop's agents
commit on a `workshop/<n>-<slug>` branch that lands through a pull request instead, and map data is changed
by one agent per town at a time.

## Rules for every change

- **`config.json` `tilePalette` is positional.** Room tile layers are integer indices into it: append
  only, never reorder or delete (a retired sprite's slot stays as a dead entry).
- **Maps**: `tiled/*.tmj` is the map source of truth at runtime; `config.json`'s room layers are the
  fallback and what the generators write. After a config or generator edit, re-seed the map:
  `python3 tools/config_to_tiled.py <Room> [<Room> ...]`. If anything visible moved, rebuild
  `assets/map` with `tools/make_worldmap.py` (needs Pillow).
- **Room generators are the source of truth for generated rooms.** Edit the generator and re-run it, or
  make a surgical edit and mirror it in the generator; never leave `check_generators.py` failing. Ported
  rooms (Tokyo, Market, Park, Palace) have no generator; their map is the source of truth.
- **Everything authored stays district-local.** The four Tokyo districts are stitched into one runtime
  room; coordinates in config, tools and docs are the district's own.
- **New JS files** go in the script list in `index.html` (there is no build step).
- **Input**: the whole game runs on WASD/arrows + SPACE/ENTER + SHIFT, with ESC as the single system key
  — no other bindings. Touch controls synthesize the same keys.
- **Overlays** are registered in `src/systems/InputHandler.js`' overlay list, live at depth 2000+ (HUD
  1000-1999, scroll factor 0; world below) and must work with touch controls. Word every key hint through
  `Hints.text(scene, ...)`; never hand-write a touch string and never test for touch capability outside
  `TouchControls`.
- **What a bump opens** is one table, `src/utils/Interactions.js`: add a rule there rather than a
  tile-name check in a feature file.
- **localStorage keys are prefixed `gamev2_`** (`gamev2_shop`, `gamev2_character`, `gamev2_intro_seen`, ...).
- **Follow the existing panel style and fonts** (`PressStart2P`, `PixelOperatorMono`; Japanese text goes
  through the Japanese face, see `docs/fonts-and-japanese.md`).
- **The cast and the trips are data** (`config.json` `members`, `trips`, `spriteMetadata`); no code lists
  names. James is the default player sprite and selectable, never a member. Do not edit credits. The
  GitHub logins and looks of Khoi, Sam and Xander are not known: do not guess them.
- **No rubbish bins, anywhere** (`play.js lint` / `check` report `rubbish-bin`).

## Index: which topic file to read

All in `gamev2/docs/`. Each line lists the original section titles it holds, so a "see X" in any file can
be found here.

| File | Covers | Read before |
|---|---|---|
| `architecture.md` | File Structure (what each `src/` file is), Core Constants, Grid-Based Movement, Collision Detection, sprite positioning | your first change; adding a source file; touching movement or collision |
| `maps-and-rooms.md` | Room System: room definition, NPC dated `states`, **Default game date**, transporters, room fade, Boundary System | editing room data, NPC states, `?date=` / default-date logic |
| `../tiled/README.md` | Editing maps in Tiled, prefabs, `stamp_prefab.py`, layers | any map or world edit (with the `generate-room` / `adjust-game` skills) |
| `stitched-city.md` | Stitched cities: `TokyoCity`, `CityStitcher`, district coordinates, woods, depth, chunk streaming / performance, seams, `?stitch=0`, adding a district | anything that reads the current room, cell coordinates, tiles on screen, or Tokyo / Market / Palace / Park |
| `occlusion.md` | Walking behind things: `Occlusion.js`, fading scenery and name labels | adding tall sprites, depth changes, "player is hidden behind X" bugs |
| `hud-input-touch.md` | HUD System, Input Handling (all key bindings, debug menu), Small Viewports and Touch: `Viewport`, `UIScale`, the three cameras and world zoom, camera bounds, overlay rules, `TouchControls`, `Hints` | any HUD, overlay, camera, zoom, key-binding, phone or touch change |
| `fonts-and-japanese.md` | Fonts and Japanese Text | drawing any text, especially Japanese |
| `trips-and-dates.md` | Trips: `config.trips`, `Trips.js`, who exists on a date, lead-in, where the player starts, Time Travel / `DatePicker`, adding a trip | trips, stays, members on a date, start position, the calendar |
| `cast-and-characters.md` | Playing as the Cast (Character menu, name Easter egg), The Cast, interim sprites (`generate_cast.py`), blog authors (`AUTHOR_NPCS`) | adding or changing a person, their sprites, or author logins |
| `title-intro-dialogue.md` | Title Screen, New-Player Intro / How to Play, boot flow, Dialogue portrait, Post caption, portrait art drop-in | the boot sequence, intro pages, the dialogue panel |
| `voice.md` | Voiced Dialogue: `Voice.js`, mute, `post_voice.py` | audio, the mute setting, voice clips in the pipeline |
| `blog-pipeline.md` | How a post becomes an NPC, Where blog NPCs may be put, The blog rehearsal, Re-homing a placement | any `blog_to_npc.py` change or pipeline bug (also `trips-and-dates.md`, and the caption / author / voice parts in the three files above) |
| `shop-and-economy.md` | Shop, Food and Drink: wallet, konbini counters, vending machines, Don Takote, items, icons, effects, fishing catches, selling, save blob, nomikai stake, Career (the job in the tower lobbies) | shops, items, money, fishing, the drinking game, the job |
| `trains-and-stations.md` | Stations and the departures board, adding a station | rideable trains, `config.stations`, `generate_stations.py` |
| `ambient-traffic.md` | Ambient Traffic: passing trains, boats, `waterways`, Streetcars (`tramways`) | decorative movers, canals / moats, track tiles, tram lines |
| `landmarks-and-towns.md` | Featured locations / landmarks, Osaka, adding a landmark, Hokkaido (Sapporo, Asahikawa, snow, konbini interiors per host, build order), House interiors, Tower lobbies, the Devhouses of Tokyo and Osaka | adding a landmark, a town, a konbini or discount store to a town, opening a town's houses |
| `buildings-and-street-props.md` | Generic city buildings (high-rises, discount store, machiya), Street accessories (traffic lights, crossings, kerbside props, Osaka's roads, no bins), Neon and lit fronts at night (`Glows.js`) | placing buildings or street furniture; `TrafficLights.js`; making a sprite glow at night |
| `generators-and-checks.md` | `check_generators.py`, Generated rooms stay regenerable, the world map (`make_worldmap.py`), Asset Generation | editing a generated room, a generator, an art tool, or the world map |
| `working-on-issues.md` | The two ways work lands (by hand on `master`, Workshop branches and pull requests), issues and labels, not colliding with other agents, running, the checks, verifying as a player, landing, fixing | starting any issue; before every push |
| `tools-play-test-studio.md` | `tools/play.js`, `tools/test_game.js`, Studio, Visual Editor | using or changing the terminal tools, `world-model.js`, `/studio/`, `/editor/` |

Where to start for common jobs:
- **A new room, konbini or building**: the `generate-room` / `adjust-game` skills, `../tiled/README.md`,
  `generators-and-checks.md`, then `landmarks-and-towns.md` (konbini interiors per host) and
  `shop-and-economy.md` (what its counter sells).
- **Camera, zoom or anything on a phone**: `hud-input-touch.md`; in Tokyo also `stitched-city.md`.
- **A blog-pipeline bug**: `blog-pipeline.md`, then `trips-and-dates.md` and `maps-and-rooms.md` (how
  dated states resolve).
