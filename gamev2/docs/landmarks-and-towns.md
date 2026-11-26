# Landmarks and the train-only towns (Osaka, Sendai, Sapporo, Asahikawa)

Named landmark sprites, adding one, the generated towns of Osaka and Hokkaido (snow, konbini per host, build order), and house interiors.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Featured locations / landmarks (issue #17)

Named landmarks are ordinary multi-cell sprites on a room's `Collidables` layer (Y-sorted by their feet:
solid at the base, walk-behind above), each wrapped in a prefab so generators can `b.stamp()` them:

| Landmark | Room | Sprite key | Art |
|---|---|---|---|
| Tokyo Tower | Palace (feet continue into Park) | `tokyo-tower_0_0` | line-art placeholder (ported from Godot) |
| Tokyo Station | Palace | `tokyo-station_0_0` | line-art placeholder (ported from Godot) |
| Tsutenkaku Tower | Osaka | `tsutenkaku_0_0` | line-art placeholder drawn by `tools/generate_tsutenkaku.py` |
| Dotonbori entrance arch | Osaka | `dotonbori-arch_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |
| Dotonbori ferris wheel | Osaka | `dotonbori-wheel_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |
| Sapporo Clock Tower | Sapporo | `sapporo-clock-tower_0_0` | shaded pixel art drawn by `tools/generate_hokkaido.py` |
| Sapporo TV Tower | Sapporo | `sapporo-tv-tower_0_0` | shaded pixel art drawn by `tools/generate_hokkaido.py` |
| Date Masamune statue (Aoba Castle ruins) | Sendai | `sendai-masamune_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Zuihoden | Sendai | `sendai-zuihoden_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| The pub (HUB) | Sendai | `sendai-pub_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Nikka distillery kiln house | Sendai | `sendai-kiln_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Matsushima sightseeing boat, pier, islets | Sendai | `matsushima-*_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Fukuoka Tower | Fukuoka | `fukuoka-tower_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Yatai stalls (ramen, yakitori, oden) and their lantern posts | Fukuoka | `yatai-ramen_0_0`, `yatai-yakitori_0_0`, `yatai-oden_0_0`, `yatai-lanterns_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Canal City and its fountain | Fukuoka | `canal-city_0_0`, `canal-fountain_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Kushida shrine's Yamakasa float | Fukuoka | `hakata-yamakasa_0_0` (beside a `shrine-red` hall) | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Dazaifu Tenmangu: hall, arched bridge, plum trees | Fukuoka | `dazaifu-hall_0_0`, `dazaifu-bridge_0_0`, `plum-tree_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Kanazawa Castle's Ishikawa gate | Kanazawa | `kanazawa-ishikawa-gate_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Kenrokuen's Kotoji lantern | Kanazawa | `kanazawa-kotoji_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Higashi Chaya teahouses, the whisky bar | Kanazawa | `kanazawa-chaya-a/-b_0_0`, `kanazawa-whisky-bar_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Gassho farmhouses, the suspension bridge, the viewpoint, the peaks | Shirakawago | `shirakawa-*_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Glass Art Museum, tram and stop, black-ramen shop, port observation tower | Toyama | `toyama-*_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |

- **Osaka** (`tools/generate_osaka.py`, 50x46) is a generated town reachable only by train, like Yukimura:
  station house -> arch over the main street -> the canal bridge -> Canal-side Avenue -> Tsutenkaku on its
  plaza, with the ferris wheel on the north bank. The Dotonbori canal (rows 20-22) runs the whole width of
  the map under the bridge and carries the ambient boats (issue #61, see Ambient Traffic); the main street
  and the avenue are its asphalt roads (issues #106 / #151, see Street accessories) and the discount store by the arch opens into `DonTakoteOsaka` (issue #91, see Shop). The tower stands on the street's axis, so a shrub garden fills the ground behind
  it and the street forks round at the avenue (otherwise the player walks hidden behind the sprite for ten cells); the
  platform-edge fence and the continuous border hedges keep the player off the ballast and out from behind
  the fences. `OsakaStation` is registered in `tools/generate_stations.py`
  (`STATIONS` / `TOWN_DOORS`) and so in config `stations`; Osaka sits detached in `devhouse.world`.
  The legacy `Scenes/osaka/osaka_outside.tscn` is an old copy of the Tokyo overworld, not Osaka — do not
  port it (`tools/doport.py` / `render_rect.py` do take `PORT_SCENE=<path>` for a genuinely different scene).
- **Adding a landmark**: put a cell-aligned PNG in `assets/sprites/` (register `spriteMetadata` with
  `anchorX = 32/width`, `anchorY = 32/height`, plus `tileNames`), add a prefab spec to
  `tools/make_prefabs.py` (colliders = the base cells only), stamp it from the room generator, and add it to
  `LANDMARKS` in `tools/blog_to_npc.py` so blog NPCs can be placed there. If it is taller than about five
  rows and worth looking up at, add its sprite family to config `game.lookUp.sprites` (`0` for a landmark
  that is one sprite; see "Looking up at landmarks" in `hud-input-touch.md`). A landmark entry may carry a third
  element `(dx, dy)`: the cell, relative to the sprite's top-left, where a visitor stands (tall sprites'
  own cell is their tip, not their foot), and an options dict:
  - `{'rooms': ('Machi',)}` — the label names one place, so only those rooms offer it. Use it whenever a
    label would be wrong in another town built from the same sprites (`the old-town lane` is Machi's;
    Asahikawa's machiya row is `ramen alley` — issue #100).
  - `{'indoors': True}` — offered inside station rooms, and only there (issue #73).

### Sendai, the samurai town (issue #66)

`tools/generate_sendai.py` (70x48) builds devhouse 2's first base (26-30 October 2025) from what its twelve
posts say happened. It is reachable only by train (`SendaiStation`, a city stop between Osaka and Sapporo on
the board) and sits detached, north-north-east of Tokyo, in `devhouse.world`.

- **Layout**: rail, platform and station house across the north; the main street runs south from the
  forecourt and crosses **Aoba-dori** (rows 22-24). North-west, the **Aoba Castle ruins**: a gravel terrace on
  a two-tier stone wall, up a seven-row flight of steps, with **Date Masamune** on his plinth on the steps'
  axis and the great hall's foundations laid out in paving. North, downtown: an office tower, the **pub**, a
  7-Eleven (`KonbiniSendai1`, `generate_konbinis.py Sendai`) under an apartment block, vending machines.
  North-east, **Zuihoden** on a two-row landing at the head of six steps, in a solid cedar grove behind an
  earthen wall. South-west, the **Nikka distillery** kiln house with casks and autumn maples - one landmark
  for the Sakunami / Yamadera day trip, not a room. South, the **samurai quarter**: an earth lane (rows
  34-35) between earthen walls, machiya, a walled residence garden with a gate on the lane and an open side
  on Aoba-dori (a way through), and a gated courtyard house on the south side. The whole east edge is
  **Matsushima bay**.
- **The bay** is `pond-autotile` water from column 59 (so it can be fished from the promenade or the pier):
  `pond-autotile_edge-w`, the set's missing west bank, is `edge-e` mirrored by `generate_sendai_art.py`. The
  **pier** is flat (`Non-Collidables` + `depthBias: -200`, the `asahikawa-bridge` recipe) and its five cells
  are the only water cells left out of the colliders; the two-deck boat is moored along it. Islets (one is
  post 487's "rock with a ball on top") keep to columns 60-64; columns 66-68 are the room's one `waterways`
  entry (`axis: 'v'`, open at the south edge), which gives it ambient boats (see Ambient Traffic).
- **Nobody under a roof**: the generator makes every building solid over its roof rows too (`building()` /
  `house()`), and the cedar groves and the walled compounds are solid throughout. The south wall stands a row
  back from the lane so its gate's roof is over the verge, not over the lane.
- **Art**: `tools/generate_sendai_art.py` (needs Pillow; `--preview out.png`) draws everything above in the
  `generate_hokkaido.py` style (it imports that file's palette and helpers): half size, pixel-doubled, 1px
  ink outline. The earthen wall is 1x2 and tiles side by side; the gate is 4x3 with a two-cell gateway and
  wing walls that meet the wall's coping.
- **Build order**: `generate_sendai_art.py`, `make_prefabs.py`, `generate_sendai.py`, `generate_konbinis.py
  Sendai`, `generate_stations.py`, `config_to_tiled.py Sendai SendaiStation KonbiniSendai1`, `play.js lint`
  for the three, `make_worldmap.py`.
- Blog NPCs can be sent to `the Aoba Castle ruins`, `Zuihoden`, `the HUB pub`, `the Nikka distillery` and
  `Matsushima bay` (`LANDMARKS`, all `rooms: ('Sendai',)`), besides the generic 7-Eleven / vending / pond
  spots. Ten devhouse 2 placements that had been scattered over Tokyo were re-homed there with `--rehome`;
  post 480 stays on Tokyo Station's platform (its lines are spoken there: "straight here to catch a three
  hour train to Sendai").

### Hokuriku: Kanazawa, with Shirakawa-go and Toyama on foot (issue #68, stage 3)

Three generated rooms that the game stitches into ONE walkable room, **`HokurikuCity`** - the second stitched
city, built with the mechanism Tokyo's districts use (see `stitched-city.md`; nothing in the stitcher is
Tokyo-specific). Kanazawa is the full town and has the region's one station (`KanazawaStation`, a city stop on
the board after Tokyo's day trips: the Hokuriku line). Shirakawa-go and Toyama are small places with NO
station: the owner's rule is that small places are walked to from their town, not ridden to.

- **Layout** (`tools/hokuriku.py`, the one place the three generators agree on it; city cells, the union's
  top-left is 0,0): **Toyama** 44x34 at (66,0), the coast; **Kanazawa** 60x52 at (0,14); **Shirakawa-go**
  (room key `Shirakawago`, display name `Shirakawa-go`) 36x32 at (60,34), below Toyama. Kanazawa's avenue runs
  out of its east edge (rows 30-32) and is Shirakawa-go's road in (rows 10-12); Shirakawa-go's mountain path
  leaves its north edge (columns 24-25) and is Toyama's path in (columns 18-19); the **Sho river** runs down
  Shirakawa-go (columns 10-15) and on through Toyama (columns 4-9) to the sea. Toyama and Kanazawa do not
  touch - six columns of wood lie between them - and no district overlaps another. The gaps of the union are
  filled by the stitcher's woodland (`cities.HokurikuCity.backdrop`, the same spec as Tokyo's; it also carries
  Kanazawa's railway on into the wood). The city is 110x66, so its `depthScale` is 1.
- **Seams**: every seam cell (three road cells, two path cells, each way) carries a hidden transporter
  landing three cells in from the neighbour's edge (`hokuriku.seams`), which is what `?stitch=0` plays; the
  only cells open on a shared edge are those, so nothing can be walked across stitched that cannot be
  crossed unstitched. A dirt path that runs on into the neighbour ends in `edge-w` / `edge-e` pieces, not the
  autotile's rounded cap.
- **Kanazawa** (`tools/generate_kanazawa.py`): rail, platform and station house across the north; the main
  street comes down to **the avenue** (rows 30-32). North-west, **Higashi Chaya**: four teahouses and two
  shops over a paved lane. On the avenue's north side, downtown: a machiya, the **whisky bar**, an office
  tower, a 7-Eleven (`KonbiniKanazawa1`, `generate_konbinis.py Kanazawa`). North-east, **Kanazawa Castle**:
  the **Ishikawa gate** (8x4; the gateway, columns 3-4 of the sprite, is open all the way through) and behind
  it grounds with the keep's foundations and nothing on them ("no castle", "under reconstruction" - the
  cones). Between the gate and the avenue, **Kenrokuen**: the pond with the two-legged **Kotoji lantern** on
  its bank. South-west, **Nagamachi**: an earth lane between earthen walls (Sendai's wall, gate and pine
  sprites), the canal along it, a flat stone bridge (`kanazawa-canal-bridge`, `depthBias: -200`) to a samurai
  gate and a house in its court. South-east, a shrine in a cedar wood (Teramachi, post 707).
- **Shirakawa-go** (`tools/generate_shirakawago.py`): the road in ends at a bus bay under a bear warning; the
  **suspension footbridge** (`shirakawa-bridge`, 8x2: the lower row is the deck, flat with `depthBias: -200`,
  the upper row its far cable) is the only way over the river - the deck row's six water cells are the only
  ones left out of the colliders. On the east bank: gassho-zukuri farmhouses (solid over the whole thatch),
  harvested paddies (`shirakawa-paddy`, a Floor tile you can walk on) with drying racks, the **viewpoint** up
  a flight of steps, and the snow-capped peaks along the north with the pass to Toyama between them.
- **Toyama** (`tools/generate_toyama.py`): the **sea** is the top of the map (`pond-autotile`, so it can be
  fished from the quay; rows 1-3 east of the river mouth are its `waterways` entry, open at the east edge,
  so ambient boats sail it). On the quay, the **port observation tower** (3x7; `game.lookUp.sprites` has it,
  so the camera looks up). Below: Iwase's old street with the **black-ramen shop**, and the tram street with
  the **Glass Art Museum**, the **tram stop** and a tram standing on `toyama-tram-rail` (plain Floor tiles,
  not `train-track`: no ambient train).
- **No invisible walls**: every generator ends with `Kit.dress()` (`hokuriku.py`), which gives any bare
  collider a walker can touch a shrub (what `play.js lint` reports as `stray-collision`).
- **The Map** (a map of Japan, `hud-input-touch.md`) has a dot for each of the three: `config.places` has
  `Kanazawa`, `Shirakawago` (label `Shirakawa-go`, as on the HUD) and `Toyama`, each a room key, so each
  district is its own dot although all three are one stitched city — friends in Shirakawa-go light
  Shirakawa-go's dot and the gold ring follows the district the player is standing in; Kanazawa Station and
  the 7-Eleven are in Kanazawa. Debug map-click travel lands outside Kanazawa Station, on Shirakawa-go's
  west road in from Kanazawa and on Toyama's south road in from Shirakawa-go (`Places.arrival`: a town
  with no station is entered from the side nearest a station).
- **Build order**: `generate_hokuriku_art.py`, `make_prefabs.py`, `generate_kanazawa.py`,
  `generate_shirakawago.py`, `generate_toyama.py`, `generate_konbinis.py Kanazawa`, `generate_stations.py`,
  the three maps in `../devhouse.world` (as `hokuriku.AT` places them), `config cities.HokurikuCity`,
  `sync_cities.py`, `config_to_tiled.py Kanazawa Shirakawago Toyama KanazawaStation KonbiniKanazawa1`,
  `play.js lint` for those and `HokurikuCity`, `make_worldmap.py`. In `devhouse.world` the region stands
  north-west of Tokyo, north of Yukimura and west of Sapporo (its box is x -112..-2, y -100..-34 in world
  cells), east of Fukuoka's east edge - Fukuoka stays the westernmost map - and across Sendai's band of latitude.
- Blog NPCs can be sent to `Kanazawa Castle's Ishikawa gate`, `Kenrokuen garden`, `the Higashi Chaya teahouse
  row`, `the whisky bar`, `the Nagamachi samurai lane` (Kanazawa), `the suspension bridge`, `the Shirakawa-go
  viewpoint`, `the gassho farmhouses` (Shirakawago), `the Glass Art Museum`, `the tram stop`, `the black
  ramen shop` and `the port observation tower` (Toyama), each `rooms:`-scoped, besides the generic shrine /
  7-Eleven / vending / pond spots. Fourteen devhouse 2 placements were re-homed there with `--rehome`
  (see `blog-pipeline.md`).

### Hokkaido: Sapporo and Asahikawa (issue #43)

Two generated towns reachable only by train (`SapporoStation`, `AsahikawaStation` in
`tools/generate_stations.py`; both sit detached to the north in `devhouse.world`). They are devhouse 3's
two bases: the trip's base cast stands in Sapporo on 18-24 Feb 2027 and in Asahikawa from the 25th (see
Trips; the generators keep a room's NPCs), and on any other date the rooms are empty unless the blog
pipeline has placed someone there.

- **Sapporo** (`tools/generate_sapporo.py`, 56x43) is the one town on a street GRID: two east-west streets
  (rows 20-22, 31-33) and three north-south (columns 14-16, 30-32 the station avenue, 44-46), `road-plain`
  asphalt where they cross (roads are ordinary walkable Floor tiles). North of the first street: the
  high-rise row + discount store (west), the station plaza, the **Clock Tower** on its paving and the
  konbini (`KonbiniSapporo1`). Between the streets: **Odori Park**, a strip of snow trees and lanterns with a
  path down the middle, closed at the east end by the **TV Tower**. South: houses on a lane and a
  frozen-pond corner. The high-rises stand shoulder to shoulder with a hedge closing the ground behind
  them, and both landmarks collide along their silhouettes (see their prefab comments): the Clock
  Tower is solid up to its pyramid roof (only the roof tip is walk-behind) and the TV Tower up to the top
  of its lattice (only the thin mast is), so the tower's shaft closes Kita-Odori's roadway at columns
  49-50 and you pass it on the north pavement. Nobody is fully hidden behind either landmark (on the pavement at (49-50,19) the foot of the mast covers half the player).
- **Asahikawa** (`tools/generate_asahikawa.py`, 42x32) is the small day-trip town: **ramen alley** (three
  machiya under red `ramen-banner` nobori), a frozen **river** running bank to bank with one timber
  **bridge**, and on the south bank a torii, the blue shrine and cottages. The river is laid by hand
  (`ice-pond-autotile` edge-n / center / edge-s rows, solid) because `Builder.pond` is two rows tall.
- **Art**: `tools/generate_hokkaido.py` (needs Pillow) draws the Clock Tower, TV Tower, bridge, banner and
  `road-plain` - at half size, pixel-doubled, in the GuttyKreum palette with a 1px ink outline, so they sit
  at the 2x scale of the building crops. They are not line-art placeholders. The LimeZu `Tileset_53_MV`
  clock tower was rejected (16px art - pixels twice the size - and more saturated). `--preview out.png`
  writes a contact sheet. It also derives the `dirt-snow-autotile` family (9 roles) from
  `dirt-outside-autotile` by swapping the green grass fringe for a snow bank - use it for dirt paths on
  snow ground (Asahikawa and Yukimura's shrine path do, #105) - and `gravel-snow-autotile` from
  `gravel-autotile` the same way (`SNOW_FAMILIES`), which the rail corridors of Yukimura, Sapporo and
  Asahikawa use (#125). `test_game.js` fails a snow-ground room that lays either grass-fringed family.
- **Flat sprites over water**: `Over Floor` and `Water` share one fixed depth, so a multi-cell sprite on
  `Over Floor` is drawn UNDER water tiles. The bridge therefore sits on `Non-Collidables` with
  `spriteMetadata.depthBias: -200` (written by `generate_hokkaido.py`'s `FLAT` table): above every ground
  layer, below everything Y-sorted, so the player walks on it. Its cells are simply left out of the
  river's colliders.
- **Konbini interiors per host**: `tools/generate_konbinis.py [Host ...]` - with host names it (re)builds
  only those hosts' stores (`generate_konbinis.py Sapporo`), leaving every other konbini room untouched.
  `generate_sapporo.py` re-seals the konbini door, so run it after every Sapporo regeneration. (The
  discount store's door is wired by `generate_sapporo.py` itself and survives a regeneration; its
  interior is `generate_discount_stores.py Sapporo`.)
- **Build order**: `generate_hokkaido.py`, `make_prefabs.py`, `generate_sapporo.py`,
  `generate_asahikawa.py`, `generate_konbinis.py Sapporo`, `generate_discount_stores.py Sapporo`,
  `generate_stations.py` (the towns fence and seal themselves - `b.finish()`), then
  `config_to_tiled.py Sapporo Asahikawa SapporoStation AsahikawaStation KonbiniSapporo1 DonTakoteSapporo`
  (it takes any number of rooms and fails, writing nothing, on a name that is not a room - #102) and
  `node tools/play.js lint <Room>` (lint reads the Tiled map).
- Blog NPCs can be sent to `the Sapporo Clock Tower`, `the Sapporo TV Tower`, `the bridge over the frozen
  river`, `ramen alley` and `the frozen pond` (`LANDMARKS` in `tools/blog_to_npc.py`), besides the generic
  shrine / torii / 7-Eleven / vending spots.
- Asahikawa's three cottages were the first houses you could walk into (`HouseAsahikawa1..3`, see House
  interiors below); the three machiya of ramen alley are shops and stay sealed.
- A room missing from `assets/map/world-map.json` is fine: `TrainTravel.dirTo` treats it as x=0. Re-run
  `tools/make_worldmap.py` to add new rooms (the studio lays the world out from it).
- **A new town needs its dot on the Map**: add `"<Room>": { "geo": [lon, lat], "label": "..." }` to
  config `places` (the Map is a map of Japan since #211, see `hud-input-touch.md`). `japan-map.test.js`
  fails for a station town with no entry, and for a geo that falls in the sea of the drawn outline.

### Fukuoka (issue #67)

A generated town reachable only by train (`FukuokaStation`, labelled **Hakata**, a main-line city stop listed
after the existing stations in `tools/generate_stations.py`); it sits detached, far south-west of Osaka, in
`devhouse.world`. It is where devhouse 2 ended (8-12 Nov 2025) and holds that week's eight posts.

- **Fukuoka** (`tools/generate_fukuoka.py`, 62x62). The west edge is the **sea** (columns 0-4, solid
  `pond-autotile_center`) with a waterline (`beach-shore-*`) and three columns of `sand-autotile` beach. A paved
  pedestrian **avenue** (columns 29-32) is the spine, north to south: the station house and its forecourt ->
  a signalled zebra crossing over the **downtown street** (rows 20-22, asphalt; high-rises and **Fukuoka Tower**
  on its plaza by the beach to the west, the station plaza with the 7-Eleven `KonbiniFukuoka1` to the east)
  -> between **Canal City** with its fountain (west) and **Kushida shrine** - a `shrine-red` hall with a
  Yamakasa float beside it - the machiya and a pagoda (east) -> **the ramen river street** -> the bridge ->
  Ohori Park's pond (south-west) and **Dazaifu Tenmangu** (south-east) -> the south lane.
- **The ramen river street**: ten **yatai** (rows 34-36: `yatai-ramen|yakitori|oden`, 3x3, solid all over)
  face a two-row promenade and the bank; a hedge runs behind the row and behind every gap in it, so the stalls
  are only ever seen from the front. Between them stand `yatai-lanterns` posts: the key holds `-lanterns`, so
  `DayNight` lights them at night with the lanterns and lamp posts (no code change).
- **The Naka river** (rows 40-42, from the first column east of the waterline to the east edge of the map) is
  the room's one `waterways` entry, built exactly like Osaka's canal (`pond-autotile` edge-n / center / edge-s,
  parapet and shade tiles on the four-cell deck, `under` columns 29-32), so it carries the ambient boats and
  can be fished from the bank. Its west end, the river mouth, is a closed end (a boat fades in there): the run
  is measured on its first rimmed cross-section, and the open sea beside it has no rim to measure.
- **Dazaifu Tenmangu** is inside the town, not a room of its own, and is laid out the way a shrine is walked:
  from the south lane through a `torii-red`, over the arched `dazaifu-bridge` (flat, `Non-Collidables` +
  `depthBias: -200`, the `asahikawa-bridge` recipe; the two pond cells under it are left out of the colliders),
  to the `dazaifu-hall` - the temporary hall of 2025 with a grove on its roof, as post 740 found it - between
  `plum-tree`s. All buildings face south, so a shrine approached from the north would show its back.
- **Art**: `tools/generate_fukuoka_art.py` (needs Pillow; `--preview out.png` writes a contact sheet) draws all
  of the above in `generate_hokkaido.py`'s way (half size, pixel-doubled, GuttyKreum palette, 1px ink
  outline; it imports that tool's palette and helpers), derives `sand-autotile` (9 roles) from
  `dirt-outside-autotile`, and adds `fukuoka-tower` to config `game.lookUp.sprites`.
- **Build order**: `generate_fukuoka_art.py`, `make_prefabs.py`, `generate_fukuoka.py`,
  `generate_konbinis.py Fukuoka`, `generate_stations.py`, then
  `config_to_tiled.py Fukuoka FukuokaStation KonbiniFukuoka1`, `play.js lint` for the three, `make_worldmap.py`.
- Blog NPCs can be sent to `Fukuoka Tower`, `the yatai stalls`, `Kushida shrine`, `Canal City`,
  `Dazaifu Tenmangu` and `Hakata Station` (`LANDMARKS`, all `rooms: ('Fukuoka',)`, as Sendai's are - each
  label names one place; `Hakata Station` is the forecourt, anchored on the station house's doorway sprite,
  which every station house has), besides the generic shrine / torii / pond / pagoda / 7-Eleven / vending spots.

### House interiors: a generic home for every house (issue #208)

`tools/generate_houses.py <Town> [<Town> ...]` is the konbini recipe for homes: it finds a town's houses in
the town's map data, builds one `House<Town><n>` room per house (display name `House · Asahikawa 2`, formed
like a konbini's; the HUD writes the dot as a pipe, and where the bar is short it reads `Asahikawa house`,
`hudBrief`), opens the house's door (collider off, a hidden
transporter on the door cell, replaced in place) and puts the way out on the cell in front of it. With no
arguments it rebuilds every town that already has houses, and a re-run on an unchanged world is a no-op.
A town is given its houses by `.agent-queue/items/houses_apply.sh <Town> ...`, which runs the art tools,
the generator, `config_to_tiled` and lint for the rooms touched, then the five checks.

**Which towns have them** (24 houses; asserted by `houses.test.js`, "the roll-out"):

| Town | Houses | Stay sealed |
|---|---|---|
| Asahikawa | `HouseAsahikawa1..3` (cottages) | ramen alley's three machiya (shops) |
| Fukuoka | `HouseFukuoka1..4` (two townhouses by the avenue, two machiya) | - |
| Market (a Tokyo district) | `HouseMarket1..3` (the shopfront townhouses on the south street) | the Izakaya's house keeps its own door |
| Osaka | `HouseOsaka1..3` | - |
| Sapporo | `HouseSapporo1..7` (one north-east, six on the south lane) | - |
| Sendai | `HouseSendai2..5` (the machiya row, one townhouse on the south lane) | 1: the courtyard house behind its earthen wall; 6..10: the row behind the south wall - nobody can stand at their doors, so the numbers are kept and unused |

Machi, Inaka and Yukimura have none on purpose (those towns are going away); Palace, Park and Tokyo have no
houses. A door in a district of the stitched city is like a konbini's there: the transporter and the way
back are in the district's own cells (`RoomManager.resolve`), with stitching on or `?stitch=0`.
A machiya's doorway is the one cell of its footprint you can step onto (`sendai.test.js` allows exactly
that cell, for a machiya that is a house).

- **What is a house** (`roomgen.HOUSE_DOORS`): the three townhouse prefabs `house-blue` / `-red` / `-black`,
  found by their ground floor (`building-entrance-1/2/3`, door in the middle), and the machiya
  (`machiya-black` / `-red` / `-blue`, door in the middle of the front). **Not** a house: one whose door
  already leads somewhere (the station houses, the Izakaya in Market), and one with a shop sign at its
  front (`SHOP_SIGNS`: the ramen nobori - Asahikawa's ramen alley is three shops). 7-Elevens, the discount
  store, high-rises and apartment blocks, shrine halls, pagodas, temple halls, landmark buildings and
  stations are never houses: each wants an interior of its own.
- **A house is skipped, and stays sealed, rather than anything being moved**: when the cell in front of its
  door cannot be stood on or walked to, when an NPC's base or dated position (any content date) is on the
  door or on that cell, or when a blog landmark's stand cell (`blog_to_npc.find_spots`) is. The run prints
  each one and why. A skipped house keeps its number, so the others are not renumbered, and it is opened
  again by the next run once the reason is gone.
- **The interior** is one lit room in the void, like a konbini's (20x15, `interior: true`,
  `shopEnabled: false`, `house: {host, door, layout}`): a two-row back wall (plaster, shoji, fusuma, a
  window, the tokonoma with its scroll), nine by six cells of floor, and the **genkan** below it - three
  cells of stone a step down, shoes on one side and the shoe cupboard on the other - with the mat you leave
  by under its middle cell. You arrive in the genkan. Four layouts (`LAYOUTS`, drawn as text in the
  generator): `kotatsu` (everyone under one quilt facing the television), `futon` (beds by the closet, tea
  at the low table), `flat` (a bed on bare boards, a tatami corner) and `hearth` (boards round the sunken
  irori, a tatami room beside it). Each has tatami, a low table or hearth with cushions, a futon or bed, the
  tokonoma, a shoji or fusuma, a kitchen corner and a television or bookshelf. Furniture that stands
  against the wall (`AT_WALL`) is a 1x2 sprite whose top half is drawn over the wall's lower half.
- **Variety, and why a re-run is stable**: everything comes from the house's position. The layout is the
  house's own favourite (md5 of town and door) unless a house within twelve cells already has it - then
  the next one the neighbours lack, preferring the layout the town has used least (`pick_layouts`), so
  neighbours never match and a small town shows as many layouts as it has houses. The same hash mirrors the
  room or not and picks one of two tatami (green / sun-aged), two plasters (sand / moss), two sets of cloth
  (kotatsu quilt, futon, cushions) and the shoes in the genkan.
- **Nobody lives there yet**, and nothing is sold. One flavour interaction: bumping the kotatsu, the
  hearth, the stove, the television or the bookshelf says one line as a toast (the `flavour` rules in
  `src/utils/Interactions.js`, each with its `say`; `GameScene.checkNPCInteraction` shows it and does not
  restart it while it is up). `interior` keeps the blog pipeline out: a post is never placed in someone's
  house unless a landmark opts in.
- **A town generator needs no edit.** It rebuilds its room from scratch with every house sealed, so
  `roomgen.save_config` puts back the house doors the room had on load (`keep_house_doors`: a transporter
  into a `House...` room that still exists, where the house still stands and the rebuild put no other door),
  in the order they were in. The same function keeps every kind of interior listed in `roomgen.OWNED_DOORS`
  (a tower's lobby and a shrine's worship hall are the other two). A house the generator moved or removed stays sealed until `generate_houses.py`
  is run for the town, which also deletes the rooms no house claims any more.
- **Art**: no pack in `../Assets` has a home interior (the GuttyKreum packs are exteriors and a train car;
  there is no `Modern_Interiors`). `tools/extract_house_interior.py` takes what fits - floorboards from the
  Train Interiors car floor (`home-wood-floor`), a potted plant from the Japanese City pack (`home-plant`) -
  and `tools/generate_house_art.py` draws the other 34 `home-*` sprites in the `generate_hokkaido.py` style
  (half size, pixel-doubled, GuttyKreum palette, 1px ink outline; `--preview out.png` on both). The wall
  pieces share one beam / rail / skirting (`wall_frame`) so they join side by side; shoji, fusuma and the
  tokonoma show no plaster, so they sit in a wall of either colour.
- **Lint** (`play.js lint`, and so `play.js check`): a home with floor its furniture has sealed off is
  `house-sealed-floor`, and a flavour object with no reachable side is `flavour-no-front`; the shop rules
  (`shop-no-front`, `shop-sealed-floor`) do not apply to a house. The generator asserts the same before it
  writes a room.
- **Build order**: `extract_house_interior.py`, `generate_house_art.py`, `generate_houses.py <Town>`,
  `config_to_tiled.py <House rooms> <Town>`, `play.js lint` for each. Nothing outdoors changes to the eye,
  so the world map is not rebuilt. To see a layout that no town has yet: `generate_houses.py --variants`
  prints all four, plain and mirrored, as JSON (what `tools/tests/houses.test.js` checks).

### Tower lobbies: a door into every high-rise (issue #216)

The same generator opens a second kind of building: `tools/generate_houses.py --lobbies <Town> [<Town> ...]`
gives every high-rise, office tower and block of flats a `Lobby<Town><n>` room (`Lobby · Osaka 2`). It is
the house code with another row in its `KINDS` table, so everything above holds - found in the town's map
data, numbered in door order, skipped and sealed by the same rules, a no-op on a re-run, kept through a
town rebuild by `roomgen.save_config`. **Applied to Osaka only** (the office block, the flats, the glass
tower); the rollout is `.agent-queue/items/lobbies_apply.sh <Town> ...`.

- **What is a tower** (`roomgen.TOWER_DOORS`): the five generic building sprites `highrise-yellow`,
  `-blue`, `-glass`, `-apartment` and `midrise-apartment`, with the door cells of their prefabs. Landmark
  towers (Tokyo Tower, the Sapporo TV Tower, Fukuoka Tower, Tsutenkaku, castles) are landmarks and stay
  sealed; the discount store has its own shop floor.
- **A pair of doors** (the glass tower's): each door that passes the skip rules opens into the same lobby
  and the way out is the cell in front of the first; one that does not stays shut, and the tower is skipped
  only when neither passes. The lobby records them (`lobby: {host, door, doors}`).
- **Which run touches what**: a town named without `--lobbies` has only its houses (re)built, with
  `--lobbies` only its towers; with no town, every town that already has houses or lobbies is rebuilt, each
  kind for the towns that have it (what `check_generators.py` runs). `--dry-run` prints what a run would
  build and skip and writes nothing.
- **The lobby** is one design, identical everywhere for now (`LOBBY`, drawn as text in the generator;
  20x15, `interior: true`, `shopEnabled: false`): a stone-panelled back wall with two lifts and the
  building directory, eleven by six cells of chequered polished floor, the reception desk, a sofa either
  side of a glass table, a palm in each corner, and the entrance mat one cell below the middle of the
  floor. You arrive just above the mat. Nobody works there yet. A bump on the directory or on a lift says
  one line (two more `flavour` rules in `Interactions.js`); the lifts go nowhere.
- **Art**: the eleven `lobby-*` sprites are drawn by `tools/generate_house_art.py`, in the same style.
- **Lint**: a lobby is held to a home's two rules under the same names (`house-sealed-floor`,
  `flavour-no-front`). Tests: `tools/tests/lobbies.test.js`.
- **Dry run of the other towns** (26 Nov): Sapporo 2 of 3 and Fukuoka 3 of 4 (a lamp post stands in front
  of the flats' door in each), Sendai 1 of 2 (the flats' door opens onto a sealed verge), Market 1,
  Palace 2; Asahikawa, Tokyo and Park have no towers.

### Shrine worship halls (issue #212)

A shrine hall is enterable: its top step (the `shrine` / `shrine-red` prefab's door cell, building cell
`(1, 4)`) carries a hidden transporter into a worship hall of its own, `Shrine<Host><n>` (HUD: `Shrine | Tokyo`).
Applied so far to **Tokyo, Market and Park**; Asahikawa, Kushida and Dazaifu Tenmangu (Fukuoka) come with
the roll-out, Machi is being deleted.

- **`tools/generate_shrines.py [Host ...]`** owns the interior and the door it opens in the host, like
  `generate_konbinis.py`: the room is rebuilt from scratch (its NPCs kept), the door cell is unsealed and its
  transporter replaced in place, and the two exit mats lead to the cell in front of the door. With no host it
  rebuilds the halls already wired (what `check_generators.py` runs); a host is named the first time.
  `.agent-queue/items/shrines_apply.sh <Host> ...` is the whole roll-out for a town (art, generator,
  `config_to_tiled`, lint, the five gates).
- **A town generator keeps the door.** A generated town rebuilds its room and stamps the hall sealed;
  `roomgen.save_config` then puts the door back exactly as it does a house's (`keep_house_doors`, see House
  interiors): the hall's room carries `shrine: {host, door, look, size}`, and `'Shrine'` is a row of
  `roomgen.OWNED_DOORS` (room-key prefix -> that marker and the door sprites, `SHRINE_DOORS`), so a door
  the room had on load is restored where the hall still stands (cell unsealed, transporter back in its
  place in the list) and dropped where the hall moved or its room is gone. No town generator needs an edit
  for its shrine to stay open; `shrines.test.js` proves it on a scratch Asahikawa, and
  `check_generators.py` for every wired town. Another kind of interior is one more row in `OWNED_DOORS`.
- **What is inside** (20x16; the floor is 18x10): the inner sanctuary (`honden`, 6x3) on a raised floor
  at the back, its doors open on the mirror, offerings and paper wands in front of it; a see-through railing
  one row in front (drawn over the sanctuary: its feet are a row lower) with a standing lamp at each end; the
  thick straw rope (`shimenawa`, Tops) across the sanctuary's lintel; the offering box (`saisen`, 2x2, solid)
  with the bell and its braided rope over it (`bell`, Tops); a cloth runner from the door to the box;
  pillars 1x3 with only the foot solid, so the shaft is walked behind (Occlusion fades it); a garland of rope
  and paper (the pack's own, `shrine-in-rope`) between the front pair's heads; hanging paper lanterns; a
  tatami room with a taiko and cushions; the miko's counter (she is part of the sprite, not an NPC); a rack
  of wishing plaques (`ema`); the fortune stand (`omikuji`) and its rail of tied fortunes; daylight through
  the door (`doorlight`, a flat sprite: Non-Collidables with a negative `depthBias`).
- **Three variants.** The look follows the roof: under `shrine-top` (blue) the hall is bare cypress, white
  plaster and indigo on a cool dark floor, the counter on the west side and standing lamps either side of
  the box; under `red-shrine-top` it is vermilion and gilt on a warm dark floor, the mirror image, with a
  second pair of pillars level with the box. `LARGE` in the generator (Kushida, Dazaifu Tenmangu) builds a
  26x18 hall with a third pair of pillars, plaques on both sides and more lanterns. `HALLS` maps a hall's
  tile to its door cell, `NAMES` gives a hall its own name.
- **Lantern light.** The room is `interior` (never offered to the blog pipeline, no day/night grade) and
  `lanternLight`: at night only, `DayNight.gradeFor` dims it warm (`LANTERN_NIGHT`) and every `*-lanterns*`
  tile gets its halo. `shopEnabled: false`: nothing in it is a konbini fixture.
- **Something to do** (`src/ShrineVisit.js`, two `shrine` rules in `Interactions.js`; proposed, not yet
  confirmed by the owner - the file's header says how to take it out): bump the offering box and ¥5 goes in,
  the bell rings (a toast: there are no sound effects) and a blessing is said; bump the fortune stand and
  ¥100 draws the day's omikuji, great blessing to great curse. One a game day, kept in the shop's save blob,
  read back free until the date changes. No overlay, no key: a bump, so touch works as it stands. A held key
  makes one visit per 1.5 s.
- **Art**: `tools/generate_shrine_art.py` (needs Pillow; `--preview out.png`) draws every piece as shaded
  pixel art in the two looks (`shrine-in-<piece>-red|blue`, shared pieces `shrine-in-<piece>`); the temple
  packs are exteriors only, and `tools/extract_shrine.py` cuts the one interior piece they have, the garland.
  Both are in `check_generators.py`.
- **Doors and blog NPCs**: the door-front cell stays clear (`NPCManager.atDoorway`; `shrines.test.js` holds
  it for every dated position). `the shrine` LANDMARK stands its visitor at building cell `(1, 6)`, the foot
  of the two steps: two cells below the door, not in front of it, and walked round by the side of the
  bottom step.
