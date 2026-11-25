# Stations and the departures board

The rail registry (`config.stations`, `tools/generate_stations.py`) and the departures board. Decorative passing trains are in `ambient-traffic.md`.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

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
