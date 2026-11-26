# Landmarks and the train-only towns (Osaka, Sendai, Sapporo, Asahikawa)

Named landmark sprites, adding one, and the generated towns of Osaka and Hokkaido (snow, konbini per host, build order).

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
- A room missing from `assets/map/world-map.json` is fine: the Map overlay still opens (no dot, "you are
  here: <room>") and `TrainTravel.dirTo` treats it as x=0. Re-run `tools/make_worldmap.py` to add new rooms.
