# City buildings and street accessories

High-rises, the discount store, machiya; traffic lights, zebra crossings, kerbside props, Osaka's roads, and the no-bins rule.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Generic city buildings: high-rises, the discount store, machiya (issue #18)

Street buildings beyond the ported houses / konbini / shrines. Each is ONE sprite on `Collidables` wrapped in
a prefab (`building()` in `tools/make_prefabs.py`): solid from the ground up, with only the top two rows (the
roof line) walk-behind, as behind a house roof - so the player is never lost behind a tower. Doors are
sealed and lead nowhere, except the discount store's, which opens into its Don Takote shop floor (issue #91,
see Shop, Food and Drink). Of the ported houses, one opens: the red house at Market `(6,33)` is the Izakaya
(issue #68, door `(7,37)`, a `lantern-red` either side; `tools/generate_izakaya.py`). Houses (the
`house-*` townhouses, and a machiya with no shop sign) get a generic home interior from
`tools/generate_houses.py` - Asahikawa's three cottages so far (issue #208, see House interiors). The high-rises and
apartment blocks get a lobby from the same tool (`--lobbies`; Osaka's three so far, issue #216, see Tower lobbies).

| Prefab | Cells | Placed in |
|---|---|---|
| `highrise-yellow` (ochre office block) | 4x8 | Market (15,22), Palace (48,6) |
| `highrise-blue` (blue-grey office block) | 5x11 | Osaka (3,7) |
| `highrise-glass` (curtain-wall tower) | 4x10 | Osaka (42,29) |
| `highrise-apartment` (tiled-balcony flats) | 5x8 | Osaka (3,30) |
| `midrise-apartment` (the same block, two floors lower) | 5x6 | Palace (40,10), feet on the forecourt edge |
| `discount-store` (the "Don Quijote") | 5x8 | Market (46,22), Osaka (13,9) by the Dotonbori arch, Sapporo (16,11) - each with an interior |
| `machiya-black` / `-red` / `-blue` (Kyoto townhouse) | 5x5 | Machi (4/9/14,17): the old-town lane |

- **Art** is assembled by `tools/extract_city.py` from the GuttyKreum RPG Maker tile kits in `../Assets/GuttyKreum`
  (Osaka `GK_Osaka_C_2`, Dotonbori `GK_DB_B`, Japanese City `GK_JC_C_2`) - a kit holds a roof cap, one window
  floor, a ground floor, roof edges..., so the script repeats floors / middle columns to get the size wanted
  (change the arguments in `BUILDINGS` for a taller or wider block; `--preview out.png` writes a contact sheet).
  **Scale is 2x**: one 32px RPG Maker tile = one 64px cell, the scale of every ported building (doors are one
  cell wide). The Dotonbori arch / ferris wheel are deliberately 4x landmarks - do not copy that for buildings.
  Do not mix in the LimeZu `Modern_Exteriors` pack (different, more saturated style).
- **The discount store** carries no real branding, like the ad pool: its sign is drawn by `extract_city.py`
  with `tools/generate_ads.py`'s text helpers - ドン・タコーテ ("Don Takote"), yellow board, blue band, a red
  octopus. It needs a Japanese font from `generate_ads.find_font()` (macOS system fonts).
- **Placing one**: generated rooms `b.stamp('highrise-glass', x, y)` in their generator (Osaka does). Ported
  rooms and Machi use **`tools/stamp_prefab.py <Room> --add <prefab> x y [--remove <prefab> x y] [--dry-run]`**,
  which refuses to write if the prefab overlaps another standing sprite, lands on a solid cell, covers a
  transporter or any dated NPC position (under its solid rows or its walk-behind roof rows), or cuts walkable
  cells off from the room's transporters (flood-fill). To change a building prefab's collision, `--remove` it
  from the ported rooms first, re-run `make_prefabs.py`, then `--add` it back. Then
  `config_to_tiled.py`, `play.js lint` (it reads the Tiled map), `make_worldmap.py`.
- Blog NPCs can be sent to `the Don Takote discount store` and `the old-town lane` (`LANDMARKS` in
  `tools/blog_to_npc.py`).

### Street accessories: traffic lights, zebra crossings, kerbside props, no bins (issue #19)

All art comes from `tools/extract_street.py` (run it before `make_prefabs.py`); every piece is a prefab.

| Prefab | Cells | What / collision |
|---|---|---|
| `traffic-light` | 1x3 | Japanese signal: horizontal 3-lamp vehicle head + pedestrian head + push button on one pole. One sprite on `Collidables`: base cell solid, the two cells above walk-behind |
| `crossing-h` / `crossing-v` | 1x3 / 3x1 | zebra crossing over a horizontal / vertical road, flat `Over Floor` paint, walkable. Origin = the road's top kerb row / left kerb column; stamp two or three side by side for a wider one |
| `utility-pole` | 1x3 | wooden pole with a transformer; base solid |
| `road-mirror` | 1x2 | orange convex mirror; base solid |
| `bus-stop`, `bicycle-blue`, `bicycle-orange`, `scooter-grey`, `scooter-red`, `traffic-cone` | 1x1 | solid |

- **Traffic-light art is drawn, not extracted** (`traffic_light()` in `extract_street.py`): no GuttyKreum sheet has a
  signal, and the only one in the repo (LimeZu `Modern_Exteriors`, `Tileset_2_MV`) is a western vertical head in 16px
  art - at game scale its pixels are twice the size of everything around it. The drawn one uses the GuttyKreum prop
  palette on the same 2x grid. Four frames, four sprite keys: `traffic-light_0_0` (vehicles green / red man - the one
  maps place), `-amber`, `-stop` (vehicles red / green man), `-stop-blink` (green man dark).
- **The cycle** (`src/TrafficLights.js`, `scene.trafficLights`): purely decorative, gates nothing. Every 200ms it
  swaps the texture of every signal sprite in `roomManager.floorSprites` to the frame of one shared wall-clock cycle
  (`TrafficLights.PHASES`: go 6s, amber 1.6s, stop 5.2s, blink 2.4s), so all signals agree and the pedestrian lamps
  run opposite the vehicle lamps. It keeps no room state and needs no room-change hook - it re-reads the loaded tile
  sprites whenever that array is replaced, and checks for that every frame so a freshly loaded room never shows a
  stale green. At night it re-lights the lit lamps with one additive Graphics above the DayNight grade
  (`TrafficLights.LAMPS` = the lamp rectangles per frame; keep it in step with `traffic_light()` in
  `extract_street.py` if the art changes). Test hooks: `trafficLights.phase()` and `trafficLights.clockOffset` (ms).
- **Crossings match the road** because they are cut from the same sheet as the `road-edge-*` / `road-div-*` tiles
  (Temples & Shrines `GK_TS_A5`). The top / left kerb tiles are the bottom / right ones flipped: the sheet's own
  have a heavily worn second stripe that reads as a glitch in game. The Japanese City `GK_JC_A5_2` crossings are on a much darker asphalt - not those.
- **Where**: signalled crossings in Tokyo (south road at the palace path, west road), Market (north road on the
  temple axis, east road, south road at the torii), Palace (east road), Park (south road, east road) and Osaka
  (the main street, between the arch and the bridge); props scattered through those, and Machi.
- **Osaka's roads** (issues #106 / #151, `generate_osaka.py`): the **main street** is columns 23-26 from row
  11 to the avenue - `road-edge-left`, `road-lane-left`, `road-lane-right`, `road-edge-right` - with the dark
  brick either side as its pavement. It ends square a row below the station door (`road-corner-nw`, two
  `road-edge-top`, `road-corner-ne`), runs under the arch and over the bridge, and meets **Canal-side
  Avenue** (rows 25-27, the standard `road-edge-top` / `road-div-horizontal` / `road-edge-bottom`, pavements
  on rows 24 and 28) at a T-junction whose box is `road-plain`, as in Sapporo. The avenue runs from one edge
  of the map to the other, through a gap in the border hedge at both ends. The street is four cells wide,
  not the usual three, **on purpose**: the arch's opening is four cells and the arch is the landmark, so
  the road keeps its axis and gets its centre line from the two lane tiles, which carry half the line each
  on their shared edge. Those, and the mitred two-kerb corners (`road-corner-nw|ne|sw|se`), are derived
  from the sheet's own road tiles by **`tools/make_road_tiles.py`** (Pillow; no new art). The crossing is the `crossing-v`
  tiles laid by hand with the middle one repeated (the prefab is three cells). It is on row 18 and
  both signals stand just south of it at the bridgehead (bases `(22,19)` and `(27,19)`): north of it their
  heads would be lost in the arch's side boards. The pavement is one cell either side of the road
  but two on the bridge (columns 21-22 and 27-28, rows 19-23; the canal's water stops at columns 20 and 29), so
  there is a way round the signal posts without stepping into the road (issue #139). The bus stop stands on the kerb at `(21,11)`.
  Nothing is placed in the rows / columns where Tokyo, Market, Palace and Park overlap (`devhouse.world`).
  A signal on the north side of a road needs three free rows above the kerb - Market's north road and Tokyo's are
  too close to the map edge, so Market's crossing has both signals on its south kerb.
- **Placing more**: `tools/stamp_prefab.py <Room> --add traffic-light x y` (x,y = the TOP cell; the base is two rows
  down), `--add crossing-h x y` etc.; generated rooms `b.stamp()` them (the Osaka / Machi placements are mirrored in
  their generators).
- **No rubbish bins, anywhere** ("definitely no rubbish bins!!" - Japanese streets have none). The `office-bin`
  sprite is retired (PNG and `spriteMetadata` deleted in #109; its `tilePalette` slot stays as a dead entry because
  the palette is positional - never place it): konbini corners get a water dispenser / plant (`generate_konbinis.py`) and the Izakaya
  seats are `izakaya-stool_0_0` (drawn by `extract_street.py`; the stools are furniture - the drinking game's
  `triggerCells` are the table cells and the bar still sells). `node tools/play.js lint` (tools/world-model.js) enforces it per room, and `play.js check` across ALL
  rooms and reports an ERROR `rubbish-bin` for any placed tile whose key or tile name is a bin / dumpster / trash
  can (`BIN_RE`), whatever `--room` was asked for. Do not extract the bins / dumpsters in the asset packs.
