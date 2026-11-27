# Stations and the departures board

The rail registry (`config.stations`, `tools/generate_stations.py`) and the departures board. Decorative passing trains are in `ambient-traffic.md`.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Stations and the departures board (issues #48, #104)

Config `stations` is the rail registry, written by `tools/generate_stations.py` from its `STATIONS` dict:
`label`, `town`, `train`, `board` / `arrive` / `trainCell`, plus the two fields that lay out the board:

- **`order`** - position on the departures board. It is the station's position in `STATIONS` (the
  registry itself is saved with sorted keys, so key order means nothing - that is how Asahikawa came to
  be pre-selected everywhere).
- **`parent`** - the station key of the city this one is a day trip from (Asahikawa -> `SapporoStation`; Tokyo has none
  since its two made-up day trips, Inaka and Yukimura, were deleted - issue #68). One level only.

A station's `label` need not be its town's name: `FukuokaStation` is labelled `Hakata` (the board says Hakata,
the room's HUD name is `Hakata Station`, the town room is `Fukuoka`).
A town's station can serve places with none: `KanazawaStation` is the only stop in the stitched Hokuriku
city (issue #68) - Shirakawa-go and Toyama are walked to from Kanazawa and are not on the board.

`src/StationPicker.js` builds the board with the static `StationPicker.board(stations, fromKey, cameFrom)`:
cities in `order`, each followed by its day trips, tagged `day trip` (not indented). The station you are at
is not a destination; it is left out unless it has day trips, in which case it stays as their grey,
unselectable `you are here` heading. ESC (or a tap outside the panel) closes the board and walks you back off the train (`StationPicker.cancel` / `.stepBack`). A station with no `order` sorts last by label, and a `parent` that is
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

**Adding a station**: add it to `STATIONS` where it belongs on the board (with `parent` for a day trip;
`'size': 'large'` for a city terminus) and to `TOWN_DOORS`, optionally its Japanese name to `STATION_JA`,
then run `generate_station_art.py` (its name board; needs Pillow) and `generate_stations.py`, and
`config_to_tiled.py` for the station room and its town. `node tools/test_game.js` checks the real
registry's board. To see a long board without adding rooms, intercept `config.json` in playwright and add
fake `stations` entries (do not ride to them).

### The station interior (issue #206)

Every station room is built by one template, `station_interior` in `tools/generate_stations.py`, so a new
row in `STATIONS` gets the whole station. Top to bottom:

| Rows | What |
|---|---|
| 0-1 | the back wall in the line's colour (`station-wall-orange` main line, `-green` branch line) with the station's name boards on row 1, clear of the parked train (row 0 is under the HUD bar) |
| 2-3 | the track: `station-track-n` / `-s` on `station-ballast`, solid except the train's two door cells on row 3 (`board`) |
| 4 | the platform edge (`station-platform-edge`: coping, white line, yellow tactile strip); you step off the train onto it |
| 5-8 | the platform: a door mark under each door (row 5), lamps, benches facing the train, the timetable, a red vending machine, the hanging platform sign and clock; **the white vending machine at `(2,6)` and the cells west of it are the blog pipeline's platform spot and stay put in every station** (shipped history stands on `(1..2, 5..7)`) |
| 9 | the gate line: `station-gate` cells in the middle are the only way through (walkable, on the `Other` layer so they need no collider); tube railing, the ticket machines and the kiosk close the rest. The LED departures sign hangs over the gates (`Tops`) |
| 10 .. h-3 | the concourse: the tactile path from the gates to the exit, benches, planters, the post box; in a large station also pillars, lockers, the route map and a tactile branch past the machines to the kiosk |
| h-2, h-1 | the front wall, with the stairs in the middle; the two exit mats are on the last row |

- **Size** is `STATIONS[...]['size']`, looked up in `SIZES`: `small` (the default, 24x15, two gates, train at
  column 7 - the size and cells every station had before, so a town door written for `11,11` is still
  right) or `large` (36x20, four gates, train at column 13: Tokyo, Kanazawa, Osaka, Sendai, Sapporo, Hakata). Everything else is
  derived in `layout(size)`; nothing is hand-placed per station. A village stop (a station with a
  `parent`) also gets the station cat.
- **Registry fields** written per station besides `label` / `town` / `train` / `order` / `parent`:
  `size`; `board` (the door cells, `[trainX + 1, 3]` and `[trainX + 8, 3]`); `trainCell` (`[trainX, 4]`);
  `arrive` (a platform cell by the gates - `play.js ride` and the world check land there); **`entry`**
  (where a town door puts you: three cells above the exit, `[11, 11]` in a small station); `ja` (the
  Japanese name, from `STATION_JA`, when there is one).
- **Town doors land on `entry`.** `generate_stations.py` points every transporter that leads into a
  station at that station's `entry`, and a town generator whose station is not small reads it back
  (`cfg['stations'][key]['entry']`, as `generate_osaka.py`, `generate_sendai.py`, `generate_sapporo.py`,
  `generate_fukuoka.py` and `generate_kanazawa.py` do) so that a re-run
  of the town alone writes the same door. Giving an existing small station `'size': 'large'` therefore
  needs that one line in its town generator, or `check_generators.py` reports the town.
- **Stepping off**: you leave the train by the door you boarded by, counted along the train
  (`TrainTravel.exitDoor(from, to, x)`) - not at the same X, which in a station of another size is a
  window.
- **The 7-Eleven kiosk** (`station-kiosk`, 4x3, solid) is a shop front inside the station, not a separate
  room: `Interactions.RULES` has a `counter` rule for `station-kiosk*` with no room condition, so bumping
  any cell of the booth - from the concourse in front of its counter, or from either side - opens the
  ordinary konbini list (buying and selling fish, titled KONBINI). A station stays a non-`interior` room:
  the blog pipeline places people in it and the night grade applies (the platform lamps are
  `station-lamp-post`, so `DayNight` lights them).
- **The departures board** you choose from is still opened by walking onto a door cell of the train; the
  LED sign over the gates is scenery.
- **Art**: `tools/extract_station.py` cuts the floors, track, benches, notice boards, railing, stairs,
  planters, post box and cat from the GuttyKreum Train Station pack (the pack the trains come from, 4x).
  `tools/generate_station_art.py` draws what the pack lacks, as shaded pixel art in the pack's palette
  (never line art): walls, gates, ticket machines, the kiosk, pillar, lamp, lockers, the hanging signs
  and **one name board per station** (`station-name-<town>`, read from `STATIONS` / `STATION_JA` without
  running the generator) - text in the game's own fonts (`PressStart2P`, `PixelMplus12` at its native
  12px), so no system font is needed and a re-run is byte-identical. Both are in `check_generators.py`'s
  art list; `--preview out.png` writes a contact sheet.
- **Tests**: `tools/tests/station-interior.test.js` checks every station of the registry (size, gates as
  the only way to the platform, the door / entry / exit cells both ways, the kiosk, the blog cells, the
  signs); `trains-stations.test.js` holds `exitDoor`; `tools/browser/regress.js` `train-ride` rides between
  two stations with real keys.

### Airports and flights (issue #218)

The home city (San Franbourne, see `landmarks-and-towns.md`) is overseas: **the only way between it and Japan is
by air**. Config `airports` is the registry, written by `tools/generate_airports.py` from its `AIRPORTS` dict:

| Field | What |
|---|---|
| `serves` | the room the airport belongs to: `Palace` (Tokyo) for `HanedaAirport`, `SanFranbourne` for `SanFranbourneAirport`. `Places.of` follows it, so Haneda is in Tokyo's dot on the Map |
| `label` | what the flights board calls it (`Tokyo`). Left out when it is just the name of the room it serves, so the home city's name is written once |
| `order` | its place on the board |
| `arrive` | where you stand after a flight: in front of the gate |
| `entry` | where a door from outside puts you |

- **Getting there.** Tokyo's airport is a stop on the rail system: `HanedaStation` (`Haneda Airport` on every
  departures board, a small main-line station, `STATIONS` row with `'blog': False`). Its `town` is the airport
  hall itself, so its stairs lead straight into `HanedaAirport` and the hall's way out leads back to the
  platform. The home airport opens onto the city by the terminal's doors. No station serves the home city.
- **One template**, `airport_interior` in `tools/generate_airports.py` (36x22), top to bottom: the back wall
  (windows onto the apron, **the gate** in the middle and **the departures board** beside it); the carpeted
  **gate lounge** with banks of seats and **the pub** against the west wall; **the security line** - two scanner
  arches you walk through (on `Other`, no collider, like a ticket gate), x-ray belts and tube railing closing
  the rest of the row; the **check-in hall** with desks, the **7-Eleven kiosk**, benches and trolleys; the front
  wall with the way out. Both airports are `interior` rooms with `shopEnabled: false` (no day/night grade, never
  offered to the blog pipeline).
- **Boarding** is one `Interactions` rule, `flights` (`airport-gate*` / `airport-board*`): a bump opens the
  departures board in flight mode - `StationPicker.show(room, { flights: true })`, the same list, keys, scrolling
  and touch rules over `AirTravel.registry(config)`, titled FLIGHTS. Picking a row calls `AirTravel.go`.
- **The 7-Eleven** is the station's booth (`station-kiosk`) and its existing rule: the konbini list. **The pub**
  is one more rule (`airport-bar*`, kind `pub`) and one more row of `Shop.VENUES`: the izakaya's drinks and food
  through the ordinary shop list, titled AIRPORT PUB; it buys no fish. **Neither stamps the Stamp Card** - an
  airport is not a store (`Stamps.isStore`), exactly as a station's kiosk does not stamp. The city's own 7-Eleven
  (`KonbiniSanFranbourne1`) is an ordinary konbini interior and does count, so Konbini Pilgrim now needs a flight.
- **The flight** (`src/AirTravel.js`): the screen fades, the room is swapped under a black curtain, and the
  cabin plays for `AirTravel.DURATION` (9 s): `plane-interior` (the train interiors' size, shown at 2x like them,
  its windows cut through) over ONE sky, so every window shows the same hour (issue #220: a long day-to-dusk
  picture used to slide behind them, and the front of the plane was in daylight while the back was in the dark).
  The sky is repainted as the flight goes: `AirTravel.skyAt(f)` gives six flat bands from the top of the sky to
  the horizon, the sea, the cloud's tint and the stars' strength for a time of day `f` and has no x;
  `AirTravel.skyTime(progress, dir)` runs `f` from day to night flying out and back again flying home; a few
  small clouds drift past window after window, each at its own speed (`AirTravel.clouds`), and the same few
  stars stand in every window at night. The colours are the stops `plane-sky.png` was painted from (`AirTravel.SKY`;
  a unit test holds them to the picture, which stays registered but is no longer drawn). They are plain shapes, not
  a Graphics: `UIScale` measures what a Graphics draws and would squeeze the picture on a phone. The player is in
  a window seat. On a phone it
  is magnified as the train ride is (`TrainTravel.cutsceneScale`, #201). The picture tells `UIScale` it is a
  backdrop exactly the size of the view (`getBounds`), so the parts that run off the sides are never squeezed in.
  You step off in front of the other airport's gate (`arrive`).
- **Input** is locked as on a train, except that a flight can be skipped: SPACE / ENTER / ESC (A / B on touch)
  or a tap, from `AirTravel.SKIP_AFTER` (0.7 s) after the cabin comes up (`AirTravel.canSkip`) - the press that
  boarded cannot skip it. `InputHandler` hands every frame to `AirTravel.handleInput` while `flying`.
- **Rules as static functions** (`registry`, `destinations`, `canFly`, `direction`, `routeText`, `canSkip`,
  `progress`, `skyTime`, `skyAt`, `clouds`, `windows`), tested in `tools/tests/airports.test.js` with the template, the city and the rule
  that no train reaches it. `Trips.hopsFrom` counts a flight as one hop; `play.js` has `fly <airport>` and the
  world check arrives at every gate.
- **Adding an airport**: a row in `AIRPORTS` (`serves`, `out`: where its way out leads), a door or station that
  leads to its `entry`, then `generate_airports.py`, `config_to_tiled.py` and `play.js lint`. Every airport
  flies to every other.
