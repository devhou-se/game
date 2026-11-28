# City buildings and street accessories

High-rises, the discount store, machiya; traffic lights, zebra crossings, kerbside props, Osaka's roads, and the no-bins rule.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Generic city buildings: high-rises, the discount store, machiya (issue #18)

Street buildings beyond the ported houses / konbini / shrines. Each is ONE sprite on `Collidables` wrapped in
a prefab (`building()` in `tools/make_prefabs.py`): solid from the ground up, with only the top two rows (the
roof line) walk-behind, as behind a house roof - so the player is never lost behind a tower. A building is
stamped with its door sealed; the discount store's opens into its Don Takote shop floor (issue #91,
see Shop, Food and Drink) and every high-rise's and apartment block's into a lobby (issue #216, see Tower
lobbies in `landmarks-and-towns.md`). Of the ported houses, one opens: the red house at Market `(6,33)` is the Izakaya
(issue #68, door `(7,37)`, a `lantern-red` either side; `tools/generate_izakaya.py`). Houses (the
`house-*` townhouses, and a machiya with no shop sign) get a generic home interior from
`tools/generate_houses.py` - in Fukuoka, Market, Osaka and Sendai (issue #208, see House interiors; Sapporo's last townhouses went when Tanukikoji was built and Asahikawa's are Hokkaido houses of its own art, #219). The high-rises and
apartment blocks get a lobby from the same tool (`--lobbies`; twenty-six in the nine towns that have a tower, all but Sendai's flats over its 7-Eleven, issues #216 and #219, see Tower lobbies), and a shopfront in `roomgen.SHOP_DOORS` a small shop floor (`--shops`; Tanukikoji's three, Susukino's karaoke bar, in Asahikawa Heiwa-dori's three and the shoyu ramen counter, and Kyu-Karuizawa Ginza's three, see Shop floors).

| Prefab | Cells | Placed in |
|---|---|---|
| `highrise-yellow` (ochre office block) | 4x8 | Market (15,22), Palace (48,6), Shinjuku (21,4) and (25,22) |
| `highrise-blue` (blue-grey office block) | 5x11 | Osaka (3,7), Shinjuku (15,1) and (5,19) |
| `highrise-glass` (curtain-wall tower) | 4x10 | Osaka (42,29), Shinjuku (10,2) and (12,20) |
| `highrise-apartment` (tiled-balcony flats) | 5x8 | Osaka (3,30), Shinjuku (4,4) and (18,22) |
| `midrise-apartment` (the same block, two floors lower) | 5x6 | Palace (40,10), feet on the forecourt edge; Shinjuku (26,6) |
| `sapporo-office-brick` / `sapporo-office-glass` (Sapporo's own office blocks, `roof=1`: only the top row is walk-behind) | 4x7 / 5x6 | Sapporo (49,9) / (10,11) - each with a lobby |
| `discount-store` (the "Don Quijote") | 5x8 | Market (46,22), Osaka (13,9) by the Dotonbori arch, Sapporo (16,11) - each with an interior |
| `machiya-black` / `-red` / `-blue` (Kyoto townhouse) | 5x5 | Sendai, Kanazawa, Toyama's old street, Fukuoka (Asahikawa's ramen alley has fronts of its own since #219) |
| `devhouse-tokyo` (the trips' house in Minato, six storeys; `door=3`) / `devhouse-osaka` (the one on Dotonbori, four; `door=1`) | 5x8 / 3x7 | Park (10,9) under Tokyo Tower / Osaka (9,10) beside Don Takote - each opens onto its floors (issue #69, see "The Devhouses of Tokyo and Osaka"; art `tools/generate_devhouse_art.py`) |

- **Art** is assembled by `tools/extract_city.py` from the GuttyKreum RPG Maker tile kits in `../art-source/GuttyKreum`
  (Osaka `GK_Osaka_C_2`, Dotonbori `GK_DB_B`, Japanese City `GK_JC_C_2`) - a kit holds a roof cap, one window
  floor, a ground floor, roof edges..., so the script repeats floors / middle columns to get the size wanted
  (change the arguments in `BUILDINGS` for a taller or wider block; `--preview out.png` writes a contact sheet).
  **Scale is 2x**: one 32px RPG Maker tile = one 64px cell, the scale of every ported building (doors are one
  cell wide). The Dotonbori arch / ferris wheel are deliberately 4x landmarks - do not copy that for buildings.
  Do not mix in the LimeZu `Modern_Exteriors` pack (different, more saturated style; it left the tree with the
  Godot project and is in git history, see `art-source/README.md`).
- **The discount store** carries no real branding, like the ad pool: its sign is drawn by `extract_city.py`
  in the house look (`tools/house_look.py`), built like the ad pool's boards - ドン・タコーテ ("Don Takote") in
  the game's own `fonts/PixelMplus12-Grid.ttf`, a shaded gold board in a steel housing, marquee bulbs, a blue
  band, a red octopus (#346). It needs no system font, so `check_generators.py` checks it wherever Pillow is.
- **Placing one**: generated rooms `b.stamp('highrise-glass', x, y)` in their generator (Osaka does). Ported
  rooms use **`tools/stamp_prefab.py <Room> --add <prefab> x y [--remove <prefab> x y] [--dry-run]`**,
  which refuses to write if the prefab overlaps another standing sprite, lands on a solid cell, covers a
  transporter or any dated NPC position (under its solid rows or its walk-behind roof rows), or cuts walkable
  cells off from the room's transporters (flood-fill). To change a building prefab's collision, `--remove` it
  from the ported rooms first, re-run `make_prefabs.py`, then `--add` it back. Then
  `config_to_tiled.py`, `play.js lint` (it reads the Tiled map), `make_worldmap.py`.
- Blog NPCs can be sent to `the Don Takote discount store` (`LANDMARKS` in `tools/blog_to_npc.py`).

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
  signal, and the only one the project had (LimeZu `Modern_Exteriors`, `Tileset_2_MV`, now in git history) is a western vertical head in 16px
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
  temple axis, east road, south road at the torii), Palace (east road), Park (south road, east road), Shinjuku
  (the avenue, columns 22-23, issue #94) and Osaka (the main street, between the arch and the bridge); props
  scattered through those.
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
  down), `--add crossing-h x y` etc.; generated rooms `b.stamp()` them (Osaka's placements are in its
  generator).
- **No rubbish bins, anywhere** ("definitely no rubbish bins!!" - Japanese streets have none). The `office-bin`
  sprite is retired (PNG and `spriteMetadata` deleted in #109; its `tilePalette` slot stays as a dead entry because
  the palette is positional - never place it): a 7-Eleven's bottom corners get shopping baskets and a magazine rack (`generate_konbinis.py`) and the Izakaya
  seats are `izakaya-stool_0_0` (drawn by `extract_street.py`; the stools are furniture - the drinking game's
  `triggerCells` are the table cells and the bar still sells). `node tools/play.js lint` (tools/world-model.js) enforces it per room, and `play.js check` across ALL
  rooms and reports an ERROR `rubbish-bin` for any placed tile whose key or tile name is a bin / dumpster / trash
  can (`BIN_RE`), whatever `--room` was asked for. Do not extract the bins / dumpsters in the asset packs.

### Neon and lit fronts at night: glow spots (issue #219)

`DayNight.buildGlows` lights a CELL: every tile whose key matches `lamp-post` or `-lanterns` gets one warm halo.
A neon board or a shop window is part of a sprite many cells big, so it is declared per sprite instead, as **glow
spots** (`src/utils/Glows.js`), and every placed copy of that sprite gets them - at night only, in any room that is
graded at night.

- **A spot** is `{ x, y, r, ry, color, a, pulse, flicker }`: `x`, `y` the centre in cells from the sprite's top-left
  corner (so `2.5` is half way across the third cell, whatever the art's scale), `r` the radius in cells across and
  `ry` down (default `r`), `color` `0xRRGGBB` (default the lamps' `0xffb366`), `a` the strength 0..1, `pulse`
  `{ period, depth }` a slow swell down to `1 - depth` and back, `flicker: true` a neon tube that sags to 55% for a
  tenth of a second about one time in sixteen. Keep a radius under 2.5 cells (the halo cull's margin is four).
- **Where they come from**: the sprite's `glow` list in `config.json` `spriteMetadata` if it has one (an empty list
  turns the sprite off), else its row in `Glows.SPRITES`. The table exists because Sapporo's art landed before its
  sprites were registered; a row can be moved into `spriteMetadata` as it is. It holds `susukino-neon-corner`,
  `susukino-karaoke`, `susukino-ramen-gate`, `tanukikoji-gate` and the three `tanukikoji-shop-*` (placed in Tanukikoji since stage 3: the bulbs under the arch, the shops' lit windows), `sapporo-station-front`, `sapporo-konbini` and the
  two `snowfest-stall-*` (placed in Odori Park since stage 2, with `odori-lamp-post`, which the lamp rule lights; pink / cyan / yellow / green boards, warm windows, the cool white of the station's clock
  and name board). `susukino-neon-lanterns` and `ramen-alley-lanterns` are lanterns by name and are lit by the
  lamp rule, so they are not in it. Every row but `sapporo-konbini` is placed since stage 4 built Susukino (the
  fox board, the karaoke front, the ramen gate); that one lights nothing until it is. Indoors the table also holds the temple hall's
  lights, `devhouse-lantern_0_0`, the stone lantern in the Osaka Devhouse's roof garden (the one Devhouse floor
  that is `lanternLight`, issue #69), and the pendant lamps and the town's lights in the panes of Fukuoka
  Tower's deck (`deck-in-downlight`, `deck-in-window-1..6`; the room is `daylight`, graded as the street is, issue #242). A unit
  test (`tools/tests/glows-trams.test.js`) holds every glowing sprite, in the table or in `spriteMetadata`, to
  having art, spots on it and radii the cull allows; registering or placing one needs no change to it.
- **Cost**: each spot is one Image of a single shared 96px halo texture (`glow-halo`, made the first time a room
  needs it), tinted, stretched and blended ADD at depth 955 with the lamps' halos - one quad, where a lamp's
  Graphics halo is re-tessellated every frame. They are in `dayNight.glows` and are hidden off camera by the same
  `cullGlows`, which also re-lights the ones in view (`Glows.shown`): a pulse or flicker (`Glows.level`, a pure
  function of time), and **the fade of its own building** - each sprite glow keeps its tile record, and while
  `Occlusion` has the building ghosted because somebody is behind it (`rec.fade`, 0.4) its glow is drawn at that
  share of its strength and comes back with it (issue #220). A lamp post's or lantern's halo has no record: a post
  is not part of the building beside it and stays lit.
- **To light a new sprite**: look at its art on a 64px grid, add a row (or a `glow` list), and check it at
  `?tod=night`. A light that is one cell big and stands alone is better named `*-lanterns` / `*lamp-post*`.

