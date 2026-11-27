# Rooms, NPC dated states and the default game date

How a room is defined in `config.json` (NPCs and their dated `states`, objects, transporters, boundaries) and how the default game date is chosen. Editing maps in Tiled is in `../tiled/README.md`.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Room System

Rooms are defined in `config.json` and loaded into `GameScene.rooms`. Each room has:
- `name`: Display name. It is what the player reads (HUD, Map, Stamp Card, the intro) and is never an
  identifier: the room KEY is. The four ported Tokyo districts show their real names while their keys stay
  what they were (issue #219): `Tokyo` -> "Imperial Palace", `Market` -> "Asakusa", `Palace` -> "Marunouchi",
  `Park` -> "Park"; the city's dot on the Map is still "Tokyo" (`cities.TokyoCity.name`) and the station room
  is "Tokyo Station". Everything authored, every tool and every doc coordinate keeps using the key
  (`goto Market 5 24`). An interior names its host by the host's display name (`7-Eleven · Asakusa 1`,
  `Shrine · Asakusa`), so rename a host in config and re-run the interior generators.
- `sentenceName` (optional): the name inside a sentence, where the display name does not read after "in"
  (`Tokyo`: "the Imperial Palace" - "Today Sam is here in the Imperial Palace."; `Trips.placeName`).
- `boundary`: Array of [x, y] points defining a polygon boundary (optional, defaults to rectangular world bounds)
- `npcs`: Array of NPC definitions with position (absolute or offset from center), sprite, name, and dialogue.
  An NPC may also carry dated state updates under `states` (`{"YYYY-MM-DD": {fields}}`): at load, every
  state dated on-or-before the game date is applied over the base definition in chronological order —
  so viewing July 27 shows the July 26 update if the next one is July 28. The game date is
  `?date=YYYY-MM-DD` when given, else the default below; a state of `{"present": false}` removes the NPC
  from that date. Author states with `python3 tools/npc_state.py <Room> <Npc> <date> --dialogue ... --pos X,Y`
  (see `src/utils/NpcStates.js`)
  - **Trips scope it** (see Trips in `trips-and-dates.md`): only states dated inside the game date's trip — and its
    current stay — are applied, and a base NPC marked `"trip"` / `"stay"` exists only on those dates.
  - **Default game date** (`defaultGameDate()`, issues #54, #118): while today is inside a trip
    (`config.trips` start to end) the game date is today, post or no post. Otherwise today is mapped
    onto a content day of the most recent trip that has posts: days since the day after that trip's
    last post, modulo its number of content days, indexes its sorted list (the day after the last is
    the first again) — so a visitor with no `?date=` always opens on a day that has posts, the next
    real day shows the next one, and two trips are never read as one long span. The content days
    (`contentChangeDates`) and the trips are handed over by `setTripDates(config)` at the top of
    `GameScene.create()`; nothing is hard-coded. The default is fixed when the config loads
    (`bootToday`), so a session left open past midnight keeps the day its NPCs were resolved for.
    The HUD shows that date bare (`February 20 2027`, `Trips.dateLabel`), on a trip's own days too: the
    trip's name is never in the bar (issue #163 — it used to lead the date where the row had room, so it
    came and went between rooms; Time Travel says which trip a day belongs to). The one thing that leads
    the date is the lead-in countdown (`devhouse 3 in 8 days | February 10 2027`, issue #164, see Trips
    and Dates), and only when the line still ends two `HUD_PADDING`s short of the `menu` button with
    it: `GameScene.layoutHUD()` measures title | room | date | wallet with the HUD's own text objects and
    shortens, then drops, the countdown where it does not fit (the konbini, the Don Takotes,
    Asahikawa Station: long room names), so the wallet is never pushed under the button. On a small
    screen the same routine goes on to drop the game's title and then to wrap the date and wallet to a
    second row, where the countdown comes back if the row has room (see Small Viewports and Touch). Anything
    that lengthens the HUD line must keep going through that check. `?date=` and Time Travel always win; `setGameDate()` drops the param
    only for the date a clean URL already gives, so picking today's real date between trips is an
    explicit `?date=` like any other. `tools/play.js` and the studio open on the same day
    (`WorldModel.defaultDate()` calls `defaultGameDate`).
- `objects`: Array of static obstacles with position (absolute or offset from center) that block movement
- `transporters`: Array of teleport points with position, targetRoom, and target position. You arrive with your back to the door that leads back where you came from, when one is beside the arrival cell (`RoomManager.faceAway`): up the stairs from an underground arcade you face the street

Position system supports both absolute grid coordinates (`gridX`/`gridY`) or center-relative offsets (`gridOffsetX`/`gridOffsetY`).

Room transitions use camera fade effects (250ms fade out, 250ms hold, 250ms fade in; on the last camera drawn, see Small Viewports and Touch) and block input during transition via `isTransitioning` flag.
Walking between the districts of a stitched city (`stitched-city.md`) is NOT a room transition.

**Boundary System:**
- Each room can define a custom polygon boundary to restrict player movement
- Boundaries are arrays of grid coordinate points: `[[x1,y1], [x2,y2], [x3,y3], ...]`
- If no boundary is specified, defaults to rectangular bounds matching world dimensions
- Player movement is validated using point-in-polygon detection (cell center must be inside boundary)
- Boundaries can create non-rectangular rooms (L-shapes, hexagons, irregular polygons, etc.)
- The visual editor provides a boundary editing tool for creating custom shapes
