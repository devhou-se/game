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
| Sapporo Station front (the star clock), the red-brick government hall (Akarenga) | Sapporo | `sapporo-station-front_0_0`, `sapporo-akarenga_0_0` | shaded pixel art drawn by `tools/generate_sapporo_art.py` |
| Date Masamune statue (Aoba Castle ruins) | Sendai | `sendai-masamune_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Zuihoden | Sendai | `sendai-zuihoden_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| The pub (HUB) | Sendai | `sendai-pub_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py`; its door opens into `PubSendai1` (see "The Sendai pub") |
| Nikka distillery kiln house | Sendai | `sendai-kiln_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py`; its door opens into `DistillerySendai1` (see "The Nikka distillery's tasting bar") |
| Matsushima sightseeing boat, pier, islets | Sendai | `matsushima-*_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Fukuoka Tower | Fukuoka | `fukuoka-tower_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Yatai stalls (ramen, yakitori, oden) and their lantern posts | Fukuoka | `yatai-ramen_0_0`, `yatai-yakitori_0_0`, `yatai-oden_0_0`, `yatai-lanterns_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Canal City and its fountain | Fukuoka | `canal-city_0_0`, `canal-fountain_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py`; the mall's two door leaves open into `MallFukuoka1` (see "Canal City's atrium") |
| Kushida shrine's Yamakasa float | Fukuoka | `hakata-yamakasa_0_0` (beside a `shrine-red` hall) | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Dazaifu Tenmangu: hall, arched bridge, plum trees | Fukuoka | `dazaifu-hall_0_0`, `dazaifu-bridge_0_0`, `plum-tree_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Kanazawa Castle's Ishikawa gate | Kanazawa | `kanazawa-ishikawa-gate_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Kenrokuen's Kotoji lantern | Kanazawa | `kanazawa-kotoji_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Higashi Chaya teahouses, the whisky bar | Kanazawa | `kanazawa-chaya-a/-b_0_0`, `kanazawa-whisky-bar_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Gassho farmhouses, the suspension bridge, the viewpoint, the peaks | Shirakawago | `shirakawa-*_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Glass Art Museum, tram and stop, black-ramen shop, port observation tower | Toyama | `toyama-*_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |

- **Osaka** (`tools/generate_osaka.py`, 50x46) is a generated town reachable only by train:
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
  - `{'rooms': ('Kanazawa',)}` — the label names one place, so only those rooms offer it. Use it whenever a
    label would be wrong in another town built from the same sprites (`the Nagamachi samurai lane` is
    Kanazawa's, though Sendai has the same gate — issue #100).
  - `{'indoors': True}` — offered inside station rooms, and only there (issue #73).

### Districts: the named areas of every town (issue #219)

Every town is made of named areas, and the data says so: config `districts`, keyed by room.

```json
"districts": { "Market": [ { "key": "asakusa", "name": "Asakusa",
    "description": "Senso-ji temple and its five-storey pagoda, the lantern gate, ...",
    "bounds": [4, 2, 53, 41], "stand": [28, 27],
    "spots": ["Senso-ji temple", "the 7-Eleven", "the izakaya", "the temple gate", "..."] } ] }
```

- **One authored list**: `DISTRICTS` in `tools/districts.py`. `python3 tools/districts.py` writes config
  `districts` from it (and works out each district's `spots`: the `LANDMARKS` labels whose standing cell is
  inside its bounds); `--report` prints every district with its spots and where seven authors would stand,
  and what is in no district. It is a generator in `check_generators.py`: re-run it after an edit to the list
  or a map change that moves a landmark. Never edit config `districts` by hand.
- **Fields**: `bounds` is `[x0, y0, x1, y1]`, inclusive, in the room's OWN cells (district-local in Tokyo,
  like everything authored); `stand` the cell a visitor to "the district" stands nearest to; `description`
  one line of what is there, written for the blog placement model. Districts of one room never overlap; a
  room need not be covered edge to edge.
- **What it is for today**: the blog pipeline (`blog-pipeline.md`, "Districts"). The game does not read
  `districts`; the HUD names the ROOM (`hudRoomName`), which for Tokyo's four ported rooms is the district.
- **Names are the redesign plan's, bounds are today's map.** A district the plan names that is not built yet
  has NO entry: Ueno and Shibuya (Park is one district, "Park", whose description says it stands in for both),
  Sapporo's Susukino, Asahikawa's zoo gate, Shirakawa-go's ryokan, Osaka's station front (a
  threshold, not a district). Add it in the change that builds it. San Franbourne (#218) was not on master when this landed: give it districts when it is.

| Room (key) | Districts today |
|---|---|
| Tokyo | Imperial Palace |
| Market | Asakusa |
| Palace | Marunouchi |
| Park | Park |
| Sapporo | Sapporo Station front, Clock Tower block, Odori Park, Tanukikoji |
| Asahikawa | Station front and Heiwa-dori, Ramen alley, Asahibashi and the riverbank |
| Osaka | Dotonbori, Shinsekai |
| Sendai | Sendai Station front, Aoba Castle ruins, Downtown, Zuihoden, Nikka distillery, Samurai quarter, Matsushima bay |
| Fukuoka | Hakata Station, Momochi, Canal City, Old Hakata, Nakasu, Dazaifu |
| Kanazawa | Station front, Higashi Chaya and the temple hill, Katamachi, Castle, Kenrokuen, Nagamachi |
| Shirakawago | Far bank and bridge, Village, Viewpoint |
| Toyama | Iwase port, Tram street |

- **Tokyo's display names**: the room keys are unchanged; see `name` in `maps-and-rooms.md`.
- **Is a city its own?** `tools/check_distinct.py` (`generators-and-checks.md`) measures how much art each
  city shares with the others; a rebuild must not make a city worse.

### Sendai, the samurai town (issue #66)

`tools/generate_sendai.py` (70x48) builds devhouse 2's first base (26-30 October 2025) from what its twelve
posts say happened. It is reachable only by train (`SendaiStation`, a city stop between Osaka and Sapporo on
the board) and sits detached, north-north-east of Tokyo, in `devhouse.world`.

- **Layout**: rail, platform and station house across the north; the main street runs south from the
  forecourt and crosses **Aoba-dori** (rows 22-24). North-west, the **Aoba Castle ruins**: a gravel terrace on
  a two-tier stone wall, up a seven-row flight of steps, with **Date Masamune** on his plinth on the steps'
  axis and the great hall's foundations laid out in paving. North, downtown: an office tower, the **pub** (its
  door opens: "The Sendai pub"), a
  7-Eleven (`KonbiniSendai1`, `generate_konbinis.py Sendai`) under an apartment block, vending machines.
  North-east, **Zuihoden** on a two-row landing at the head of six steps, in a solid cedar grove behind an
  earthen wall. South-west, the **Nikka distillery** kiln house with casks and autumn maples - one landmark
  for the Sakunami / Yamadera day trip; its door opens into the tasting bar ("The Nikka distillery's tasting
  bar"), the only room of the distillery. South, the **samurai quarter**: an earth lane (rows
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
  gate and a house in its court. South-east, a shrine in a cedar wood (Teramachi, post 707). Four of its
  houses can be walked into (`HouseKanazawa1..4`, `generate_houses.py Kanazawa`, see House interiors): the
  two machiya on Higashi Chaya's lane, the machiya downtown and the samurai's house; the town generator
  knows nothing of them (`roomgen.save_config` keeps their doors through a rebuild).
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
  `generate_shirakawago.py`, `generate_toyama.py`, `generate_konbinis.py Kanazawa`, `generate_houses.py Kanazawa`,
  `generate_stations.py`,
  the three maps in `../devhouse.world` (as `hokuriku.AT` places them), `config cities.HokurikuCity`,
  `sync_cities.py`, `config_to_tiled.py Kanazawa Shirakawago Toyama KanazawaStation KonbiniKanazawa1 HouseKanazawa1..4`,
  `play.js lint` for those and `HokurikuCity`, `make_worldmap.py`. In `devhouse.world` the region stands
  north-west of Tokyo and west of Sapporo (its box is x -112..-2, y -100..-34 in world
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
  asphalt where they cross (roads are ordinary walkable Floor tiles). It is being rebuilt district by
  district (issue #219); **stages 1 to 3, the north, Odori Park and Tanukikoji, are done**: four districts, each on
  ground of its own.
  **Sapporo Station front** (grey stone slabs, `brown-brick-autotile`; stage 1 had borrowed the arcade's red brick, which stage 3 gave back to Tanukikoji alone): the station front with the
  star clock (`sapporo-station-front`, 10x7 at (24,4), across the rail line; its pair of doors (28,10) and
  (29,10) both lead into `SapporoStation`, and you come out on (28,11)), the plaza below it, and west of
  the plaza on the same slabs the red-brick government hall (`sapporo-akarenga` at (2,11), a landmark:
  sealed), the glass KITA office block (`sapporo-office-glass`) and the discount store. **Clock Tower
  block** (dark setts, `flat-grey-brick-autotile`, east of the avenue): the **Clock Tower** where it always
  stood and the red-brick office block (`sapporo-office-brick`); the konbini moved to the arcade with stage 3. The two
  office blocks open into lobbies (`LobbySapporo1`, `LobbySapporo2`, see Tower lobbies); no generic
  townhouse and no Osaka high-rise stands north of Kita-Odori. **Odori Park** (rows 23-30 between the two
  streets, a path of packed snow - `snow-path-autotile` - on snow, rows 26-27 from block to block) is the
  snow festival, and the three blocks the streets cut it into are not alike: west the **sculpture court**
  (the snow castle `snow-sculpture-castle` at (4,23) with a court in front of its steps, the snow tanuki at
  (12,23)), in the middle **the fountain and the stalls** (the frozen `odori-fountain` at (22,25) on a plaza
  the path runs round, the corn tent at (17,23) and the hot-drinks tent at (27,23), their counters on the
  path), east the **TV Tower lawn** (the snow bear at (38,24), open snow, children's heaps), closed at the
  east end by the **TV Tower** on its own plaza, exactly where it was. Ploughed snowbanks (`snowbank-h` /
  `-v` / `-pile`, one solid cell each) close a block's edges: you come in along the path or by a gap in the
  bank from either street. `odori-lamp-post` (1x2, lit at night by the lamp rule) and `odori-bench` (2x1)
  furnish all three. The sculptures collide along their silhouettes (the castle up its keep, the tanuki and
  the bear all over), a tent all over like a yatai, the fountain's basin and stem - nobody stands inside
  one, and each has free ground along its south side. A bump on the hot-drinks tent opens a shop list (HOT
  DRINKS: Canned Coffee and Green Tea, `Shop.VENUES.stall`); the corn tent, the three sculptures and the
  fountain each say one line (`Interactions.RULES`, group `flavour`). The frozen pond in the south-west
  corner went with stage 2 (Asahikawa keeps the frozen water), and the sakura with it. **Tanukikoji**
  (stage 3, south of Minami-Odori, on red basket-weave brick, `arcade-brick-autotile`, its alone) is the covered
  shopping arcade: one east-west street (rows 38-40) in two stretches, columns 17-29 and 33-43, either side of
  the station avenue, which it crosses in the open. Its north row (rows 34-37, feet on row 37, standing on
  Minami-Odori's kerb where the south pavement was) is shopfronts under one glass roof, solid from the roof
  down: west, an upright sign (`tanukikoji-end-sign`), the souvenir shop (18,34), the **TANUKI KOJI gate**
  (`tanukikoji-gate` at (21,34): you walk through its two middle columns, 22-23, from Minami-Odori; its outer
  columns are solid; the board fades while you are under it), the crab shop (25,34), a sign; east, a sign, the
  drugstore (35,34), the town's 7-Eleven (38,34, `KonbiniSapporo1`, same key and name as before the move), a
  sign and the 7-Eleven's own. Its south row (rows 40-42, `tanukikoji-south-row-a` / `-b` alternating) is the
  backs of the next street's shops: the top row is roof only and overhangs the street's southern row (walked
  under; Occlusion fades the module), the two rows below are solid and stand where the south fence did. The
  three shops open into shop floors (`ShopSapporo1..3`, see Shop floors) - no building of the arcade is sealed.
  The six townhouses that stood here are gone and so are `HouseSapporo1..6`: Sapporo has no House interior.
  The gate and the shops' windows glow at night (`Glows.SPRITES`). Still to come (stage 4: Susukino and the
  streetcar, south of the arcade); until then the two south corners are snow and trees. The west row is closed by a shrub in each gap and a hedge behind it; the
  station front, the government hall and the office blocks collide up to their roof lines (nothing of the
  station is walk-behind; of an office block only its top row), and both towers collide along their
  silhouettes (see their prefab comments): the Clock
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
  snow ground (Asahikawa does, #105) - and `gravel-snow-autotile` from
  `gravel-autotile` the same way (`SNOW_FAMILIES`), which the rail corridors of Sapporo and
  Asahikawa use (#125). `test_game.js` fails a snow-ground room that lays either grass-fringed family.
- **Sapporo's own art**: `tools/generate_sapporo_art.py` (needs Pillow, in `check_generators` `ART_TOOLS`)
  draws everything else that is Sapporo's - the station front, the government hall, the two office blocks,
  and the pieces the later stages will place (Tanukikoji's arcade, Susukino's neon, Odori's snow sculptures
  and stalls, the streetcar, `arcade-brick-autotile` and `snow-path-autotile`) - and registers every sprite
  in `spriteMetadata` / `tileNames`. A piece gets a prefab in `make_prefabs.py` when a stage places it
  (stage 1: `sapporo-station-front`, `sapporo-akarenga`, `sapporo-office-brick`, `sapporo-office-glass`;
  stage 2: the three `snow-sculpture-*`, the two `snowfest-stall-*`, `odori-fountain`, `odori-lamp`,
  `odori-bench`, the three `snowbank-*`; stage 3: the three `tanukikoji-shop-*`, `tanukikoji-gate`,
  `tanukikoji-end-sign`, `tanukikoji-south-row-a` / `-b`; `tanukikoji-rib` and `sapporo-konbini` are drawn and not placed).
  `--sheet`, `--scenes` and `--manifest` write a contact sheet, mock scenes and the door / footprint table.
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
- **Konbini interiors** (issue #221): a store is a Pokémon Mart's plan dressed as a 7-Eleven, a lit
  floor in the void of a 20x15 room like a house's. The back wall is two rows (`konbini-wall`, with the
  clock and the tobacco rack over the till) and the floor six: the clerk's counter nook in one back
  corner (`konbini-counter-w` / `-e`, 2x3, the clerk drawn into the sprite - there is no NPC), then
  along the wall the drinks coolers (`office-fridge`), the open chillers, the coffee machine, the water
  dispenser, the copier and the cash machine; shelf blocks (`konbini-gondola-*`, 2x2) with an aisle on
  every side; the ice-cream chest; the baskets and the magazine rack in the bottom corners; the mat
  (`konbini-mat`, two cells, both of them the way out) at the bottom centre, the door landing you on the
  cell above its left half. The plans are the text grids in `LAYOUTS` (`aisles` and `freezer` 12 cells
  wide, `small` 10): one character a cell, a capital where a piece starts. `plan_of(store)` deals a
  store its plan, whether it is mirrored (the till in the east corner) and what its shelf blocks stock
  from its host and door cell, so a rebuild reproduces it. The room is built on the shared shell
  (`tools/interiors.py`, `generators-and-checks.md` "Interior building blocks"), whose `room()` fails
  the run if a plan leaves floor the door does not reach; `check_store()` fails it for a selling
  fixture with no free cell under one of its columns, or anything else you can bump with no free side.
  To add a plan, add a grid to `LAYOUTS` (a new piece
  also needs its letter in `AT_WALL` or `FURNITURE`, and a rule in `Interactions.js` if a bump on it
  does something). The room's `boundary` is the floor, the mat and the two wall rows
  (`back_wall(..., view=True)`): the wall is solid,
  and with it the outline is taller than a landscape phone's view, so the camera follows you instead of
  being held to the floor with the wall off the top of the screen. The art is the `konbini-*` kit,
  26 sprites drawn by `tools/generate_konbini_art.py [--preview out.png]` (procedural, needs Pillow, in
  `check_generators.py`): run it before `generate_konbinis.py` when the kit changes. The Tanukikoji
  shop floors and Don Takote keep the `office-*` furniture. Tests: `tools/tests/konbini.test.js`.
- **Build order**: `generate_hokkaido.py`, `generate_sapporo_art.py`, `make_prefabs.py`, `generate_sapporo.py`,
  `generate_asahikawa.py`, `generate_konbinis.py Sapporo`, `generate_discount_stores.py Sapporo`,
  `generate_stations.py` (the towns fence and seal themselves - `b.finish()`; the station's way out is
  `TOWN_DOORS` there), `generate_houses.py Sapporo` and `generate_houses.py --lobbies Sapporo`, `generate_chikagai.py Sapporo` (see Underground arcades), then
  `config_to_tiled.py Sapporo Asahikawa SapporoStation AsahikawaStation KonbiniSapporo1 DonTakoteSapporo`
  and the House / Lobby rooms
  (it takes any number of rooms and fails, writing nothing, on a name that is not a room - #102) and
  `node tools/play.js lint <Room>` (lint reads the Tiled map).
- Blog NPCs can be sent to `the Sapporo Clock Tower`, `the Sapporo TV Tower`, Odori Park's `Odori Park`
  (the plaza beside the fountain), `the snow castle`, `the snow tanuki`, `the snow bear`, `the snow festival
  stalls` and `the Odori fountain` (all scoped to Sapporo), `the bridge over the frozen river` and `ramen
  alley` (`LANDMARKS` in `tools/blog_to_npc.py`), besides the generic shrine / torii / 7-Eleven / vending
  spots. `the frozen pond` is no longer a row: Sapporo's pond went with stage 2 of its rebuild and the only other
  one was in Yukimura, a made-up town that is deleted (issue #68). A town that gets a frozen pond adds a row
  scoped to it.
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
  -> between **Canal City** with its fountain (west; the mall's doors open into its atrium, `MallFukuoka1`:
  see "Canal City's atrium") and **Kushida shrine** - a `shrine-red` hall with a
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

### San Franbourne, the home city, and its airport (issue #218)

devhouse people come from Melbourne or from San Francisco, so home is both at once: **one** city, played for
affection, not two halves. It is overseas - **reachable only by air** (see "Airports and flights" in
`trains-and-stations.md`): no station serves it, it is on no departures board, nobody is placed there by a trip
and the blog pipeline never offers it (`"blog": false` on the room, see `blog-pipeline.md`).

- **The name is written once.** `NAME` in `tools/generate_sanfranbourne.py` becomes `rooms.SanFranbourne.name`,
  and the Map label, the flights board, the flight's caption and the Map footer all read it from there (config
  `places.SanFranbourne` and `airports.SanFranbourneAirport` carry no label). The room key stays
  `SanFranbourne`. To rename the city: change `NAME` and re-run `generate_sanfranbourne.py` and
  `generate_konbinis.py SanFranbourne` (its 7-Eleven's room name, `7-Eleven · <name>`, is derived by that
  generator like every konbini's). Its airport has a name of its own, **Tullafrisco Airport**, the way Hakata
  station serves Fukuoka. `airports.test.js` fails if the bare name appears a second time in `config.json`.
- **San Franbourne** (`tools/generate_sanfranbourne.py`, 60x60), north to south down the **avenue** (columns
  28-31): the **airport terminal** and control tower (north-west; its double doors lead into
  `SanFranbourneAirport`) and the **sports ground** (north-east: a flat oval you walk on, four posts at each
  end, light towers that glow at night, banks of fog on `Tops`); the **tram street** (rows 15-17), where a
  **cable car** and a **green-and-yellow tram** share one pair of rails and the avenue crosses on a signalled
  zebra crossing; the **painted ladies** (six terraces, each on a higher footing than the last) standing on a
  bluestone wall of **street art** with two **coffee windows** let into it, the **laneway** along its foot;
  the plaza with the **pointy pyramid** beside the **arts-centre spire** (both in `game.lookUp.sprites`), a glass
  tower, vending machines and the 7-Eleven `KonbiniSanFranbourne1`; the **brown river** (solid, rowers on it)
  under the **red suspension bridge** - the deck is the avenue, and you walk between the legs of both towers
  (only the leg cells collide); the yellow **station with the clocks** over its door (sealed: nobody catches a
  train there, a bump says so - you meet under the clocks), townhouses and a palm garden; the boardwalk, the
  **pier** (flat, walked on to its end) with the raft of **sea lions** beside it (a bump from the pier says a
  line), and the island with the lighthouse out in the bay. Four **leaners** (`sfb-lean-{a,b,c,d}`, `LEANERS`
  in the generator) stand folded double at the waist by the tram stop, on the pavement between the two towers,
  in the laneway and beside the 7-Eleven: one solid cell each, off the avenue and every door, and a bump says
  that figure's one line (`Interactions.RULES`, kind `leaner`).
- **Art**: `tools/generate_sanfranbourne_art.py` (Pillow, in `ART_TOOLS`; `--preview out.png`) draws every
  `sfb-*` sprite, the `airport-*` furniture and the two flight pictures as shaded pixel art in the GuttyKreum
  palette - no brand marks but the 7-Eleven the game already has. The oval and the pier are flat
  (`Non-Collidables` with a `depthBias`, the `asahikawa-bridge` recipe); the river is `pond-autotile`
  recoloured (`sfb-river_*`, so it is not a fishing spot); the light towers are named `...lamp-post` so
  `DayNight` lights them.
- **Houses are sealed** (`generate_houses.py` has not been run for this town's houses), and there are no
  rubbish bins. The glass tower's pair of doors (47,27) and (48,27) open into `LobbySanFranbourne1` (see Tower
  lobbies; `generate_houses.py --lobbies SanFranbourne`, kept through a rebuild of the town).
- **Built by** `generate_sanfranbourne_art.py` -> `generate_airports.py` -> `generate_sanfranbourne.py` ->
  `generate_konbinis.py SanFranbourne` -> `generate_stations.py` (the Haneda stop) -> `config_to_tiled.py` ->
  `make_worldmap.py`. `devhouse.world` has it far to the south-east of every Japan map.
- **On the Map** it is the one `overseas` place: a little plane in the sea south-east of Honshu on a dashed
  course off the corner of the picture (config `places.SanFranbourne`: `overseas: true`, and a `geo` that is a
  position on the picture, not a real longitude / latitude). The ring and the red dot work there as anywhere;
  the footer reads `San Franbourne (overseas)`. `HanedaAirport` and its rail stop belong to Tokyo's dot
  (`Places.of` follows `airports.<key>.serves`).
- **Tests**: `tools/tests/airports.test.js`.

### House interiors: a generic home for every house (issue #208)

`tools/generate_houses.py <Town> [<Town> ...]` is the konbini recipe for homes: it finds a town's houses in
the town's map data, builds one `House<Town><n>` room per house (display name `House · Asahikawa 2`, formed
like a konbini's; the HUD writes the dot as a pipe, and where the bar is short it reads `Asahikawa house`,
`hudBrief`), opens the house's door (collider off, a hidden
transporter on the door cell, replaced in place) and puts the way out on the cell in front of it. With no
arguments it rebuilds every town that already has houses, and a re-run on an unchanged world is a no-op.
A town is given its houses by `.agent-queue/items/houses_apply.sh <Town> ...`, which runs the art tools,
the generator, `config_to_tiled` and lint for the rooms touched, then the five checks.

**Which towns have them** (20 houses; asserted by `houses.test.js`, "the roll-out"):

| Town | Houses | Stay sealed |
|---|---|---|
| Asahikawa | `HouseAsahikawa1..3` (cottages) | ramen alley's three machiya (shops) |
| Fukuoka | `HouseFukuoka1..4` (two townhouses by the avenue, two machiya) | - |
| Kanazawa (a district of Hokuriku) | `HouseKanazawa1..4`: the two machiya at the east end of Higashi Chaya's lane, the machiya downtown beside the whisky bar, the samurai's house in its court behind the Nagamachi gate | 5..7: the three roofs seen over Nagamachi's walls stand in compounds that are solid throughout - nobody can stand at their doors, so the numbers are kept and unused |
| Market (a Tokyo district) | `HouseMarket1..3` (the shopfront townhouses on the south street) | the Izakaya's house keeps its own door |
| Osaka | `HouseOsaka1..2` (the two townhouses in Shinsekai) | - (the black townhouse's lot on Dotonbori is the Devhouse now, see "The Devhouses") |
| Sapporo | none: its last six townhouses went when Tanukikoji was built (#219, stage 3) | - |
| Sendai | `HouseSendai2..5` (the machiya row, one townhouse on the south lane) | 1: the courtyard house behind its earthen wall; 6..10: the row behind the south wall - nobody can stand at their doors, so the numbers are kept and unused |

Palace, Park, Tokyo and Shirakawa-go have no
houses; Toyama's old street has not been given its own yet. A door in a district of a stitched city (Market
in Tokyo, Kanazawa in Hokuriku) is like a konbini's there: the transporter and the way
back are in the district's own cells (`RoomManager.resolve`), with stitching on or `?stitch=0`.
A machiya's doorway is the one cell of its footprint you can step onto (`sendai.test.js` and
`kanazawa.test.js` allow exactly that cell, for a machiya that is a house).

- **What is a house** (`roomgen.HOUSE_DOORS`): the three townhouse prefabs `house-blue` / `-red` / `-black`,
  found by their ground floor (`building-entrance-1/2/3`, door in the middle), and the machiya
  (`machiya-black` / `-red` / `-blue`, door in the middle of the front). **Not** a house: one whose door
  already leads somewhere (the station houses, the Izakaya in Market), and one with a shop sign at its
  front (`SHOP_SIGNS`: the ramen nobori - Asahikawa's ramen alley is three shops). 7-Elevens, the discount
  store, high-rises and apartment blocks, shrine halls, pagodas, temple halls, landmark buildings and
  stations are never houses: each wants an interior of its own (a pagoda has one: see "Pagodas").
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

### Shop floors: a door into a shopfront (issue #219)

A third row of the same generator's `KINDS` table: `tools/generate_houses.py --shops <Town> [<Town> ...]` gives
every shopfront in `roomgen.SHOP_DOORS` a `Shop<Town><n>` room, found, numbered (door order), skipped, sealed,
re-run and kept through a town rebuild exactly as a house or a lobby is. **Applied to Sapporo**: Tanukikoji's
souvenir shop, crab shop and drugstore are `ShopSapporo1..3`.

- **One layout** (`SHOP`): a white back wall with two posters, two shelves either side against it, seven by five
  cells of floor, a counter with a till, a plant in each front corner, the mat below the middle. All of it is the
  konbini's furniture (`office-*`) and the lobby's mat; no new art.
- **Named by what the front sells** (`SHOP_TYPES`: sprite family -> label, list, shelves): `Souvenirs · Sapporo`,
  `Crab shop · Sapporo`, `Drugstore · Sapporo` (numbered only where a town has several of one type).
- **It sells**: the room is `interior`, `shopEnabled: false` (not a store: no stamp, no Konbini Pilgrim, the
  shelves are only to look at) and `shopMenu: souvenirs | crab | drugstore`, so a bump on the counter opens that
  row of `Shop.VENUES` - two or three things off the existing catalogue (see Shop). The room's `shop` marker is
  `{host, door, type}`.
- A new shopfront elsewhere is a row in `roomgen.SHOP_DOORS` and one in `SHOP_TYPES` (and a `Shop.VENUES` row
  if it sells something else).

### Tower lobbies: a door into every high-rise (issue #216)

The same generator opens a second kind of building: `tools/generate_houses.py --lobbies <Town> [<Town> ...]`
gives every high-rise, office tower and block of flats a `Lobby<Town><n>` room (`Lobby · Osaka 2`). It is
the house code with another row in its `KINDS` table, so everything above holds - found in the town's map
data, numbered in door order, skipped and sealed by the same rules, a no-op on a re-run, kept through a
town rebuild by `roomgen.save_config`. **Applied to every town that has a tower**: sixteen lobbies in eight
towns, no tower skipped. Asahikawa, Tokyo, Park, Shirakawa-go and Toyama have no towers.

| Town (display name) | Rooms | Tower and its door cell(s) in the town |
|---|---|---|
| Osaka | `LobbyOsaka1..3` "Lobby · Osaka 1..3" | the blue office block (5,17); the flats (5,37); the glass tower (43,38)+(44,38) |
| Sapporo | `LobbySapporo1..2` "Lobby · Sapporo 1..2" | its own office blocks (#219): the brick one in the Clock Tower block (51,15); the glass one west of the station plaza (12,16) |
| Market (Asakusa) | `LobbyMarket1` "Lobby · Asakusa" | highrise-yellow (16,29) |
| Palace (Marunouchi) | `LobbyPalace1..2` "Lobby · Marunouchi 1..2" | highrise-yellow (49,13); midrise-apartment (42,15) |
| Fukuoka | `LobbyFukuoka1..4` "Lobby · Fukuoka 1..4" | highrise-glass (17,18)+(18,18); -blue (22,18); -yellow (26,18); midrise-apartment (38,18) |
| Sendai | `LobbySendai1` "Lobby · Sendai" | highrise-yellow (23,20) |
| Kanazawa | `LobbyKanazawa1..2` "Lobby · Kanazawa 1..2" | highrise-yellow (15,28); midrise-apartment (28,28) |
| SanFranbourne | `LobbySanFranbourne1` "Lobby · San Franbourne" | highrise-glass (47,27)+(48,27) |

A town's only lobby has no number. The way out of each is the cell below its (first) door.

- **The roll-out for a town** (from `gamev2/`; check first with `--dry-run`, which must list nothing as skipped):
  `python3 tools/generate_houses.py --lobbies <Town> ...`, then `python3 tools/config_to_tiled.py <Town> ... <each
  Lobby room>`, then `node tools/play.js lint` for each of those rooms and the checks. Market and Palace are
  ported maps with no generator: their tower doors live only in `config.json` and their `.tmj`.
- **No sealed towers** (owner rule): where a prop stood in front of a tower's door, the prop moved rather than
  the tower staying shut. Fukuoka's two pavement lamps at (18,19) and (38,19) - in front of the glass tower's
  right door and the flats' - stand one cell aside, at (19,19) and (37,19) (`generate_fukuoka.py`).
- **A store's block is not a tower** (`STOREFRONTS` in `generate_houses.py`): Sendai's flats
  (`highrise-apartment` at (38,9), door (40,16)) have the town's 7-Eleven standing directly across their door on
  purpose ("the 7-Eleven under an apartment block", `generate_sendai.py`), so the building is entered through
  the store. A tower with a `seven-eleven` on the row in front of its door, across the door's column, is
  reported as "not a tower ... in use" - not as skipped - gets no lobby and no number, and its door stays shut.
- **On a phone's HUD bar** a lobby's short form is its town's, "Osaka lobby", as a house's and a shrine's
  (`hudBrief`, `src/utils/NpcStates.js`). A town whose name makes that longer than 15 characters
  (`HUD_BRIEF_MAX`: what one row holds with the short date, its year and the starting wallet at 667x375) keeps
  the kind and its number instead: Marunouchi's read "Lobby 1" and "Lobby 2" ("Marunouchi lobby" is 16) and
  San Franbourne's only one "Lobby", and so count down on a lead-in day on both phones. The rule is the same
  for a house or a shrine of a long-named town ("House 3", "Shrine"): Asahikawa's worship hall (#212) reads
  "Shrine", because "Asahikawa shrine" is 16 and cost the bar its year at 667x375. The whole name still shows
  wherever the bar has room for it. A town-led form can still be too long for the countdown, as a house's can: "Kanazawa
  lobby" (14) shows the date at 844x390, and every town-led lobby but Osaka's does at 667x375.

- **What is a tower** (`roomgen.TOWER_DOORS`): the five generic building sprites `highrise-yellow`,
  `-blue`, `-glass`, `-apartment` and `midrise-apartment` and Sapporo's `sapporo-office-brick` and
  `sapporo-office-glass`, with the door cells of their prefabs. Landmark
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
  floor. You arrive just above the mat. **The lobby is where the job is** (issue #226, `src/Career.js`,
  see "Career" in `shop-and-economy.md`): a bump on the reception desk signs you on and afterwards reads
  your title back, and a bump on a lift, once you hold the pass, opens a shift (without it, a line pointing
  at the desk). Both are rules in `Interactions.js`, group `career`; the directory is still a `flavour`
  line and says engineering is hiring. Every lobby has the job, and one built later has it without an edit.
- **Art**: the eleven `lobby-*` sprites are drawn by `tools/generate_house_art.py`, in the same style.
- **Lint**: a lobby is held to a home's two rules under the same names (`house-sealed-floor`,
  `flavour-no-front`; the desk and the lifts are furniture you bump as well, and are held to the second).
  Tests: `tools/tests/lobbies.test.js`, and `tools/tests/career.test.js` for the job.
- **A town redesign** that keeps a tower keeps its lobby door (`roomgen.save_config`); one that removes a
  tower leaves a `Lobby` room behind until `generate_houses.py --lobbies <Town>` is run again, which drops it
  and renumbers the rest.

### Shrine worship halls (issue #212)

A shrine hall is enterable: its top step (the `shrine` / `shrine-red` prefab's door cell, building cell
`(1, 4)`) carries a hidden transporter into a worship hall of its own, `Shrine<Host><n>` (HUD: `Shrine | Asakusa`, the host's display name).
Every hall in the world has one: **Tokyo** (`ShrineTokyo1`, Palace Shrine), **Market** and **Park**
(`ShrineMarket1`, `ShrinePark1`), **Asahikawa** and **Kanazawa** (`ShrineAsahikawa1`, `ShrineKanazawa1`, blue,
standard) and **Fukuoka**'s two, both red and large: Kushida Shrine (`ShrineFukuoka1`) and Dazaifu Tenmangu
(`ShrineFukuoka2`). Dazaifu's hall is its own sprite (`dazaifu-hall`, stamped sealed right across): its door is
building cell `(3, 4)`, the right half of its two-wide steps, in line with the bridge
(`roomgen.SHRINE_DOORS` has a row per hall tile).

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
  for its shrine to stay open; `shrines.test.js` proves it on a scratch copy (Asahikawa, Fukuoka and Kanazawa
  rebuilt, then Asahikawa's hall sealed and rolled out again), and `check_generators.py` for every wired
  town. Another kind of interior is one more row in `OWNED_DOORS`.
- **The steps stay open.** The prefab seals the hall and leaves its door and the three cells of its bottom
  step open; a town must not plant on them. Kanazawa's wood did (a cedar's trunk across the door, the step's
  east end solid), so `hokuriku.Kit.woods` takes `clear=`: cells that stay out of the wood, planted and
  cleared again rather than skipped so the rest of the seeded scatter does not move. `generate_kanazawa.py`
  passes the hall's bottom step; `shrines.test.js` holds the step open in every town.
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
  26x18 hall with a third pair of pillars (two cells outside the nave's two, between them: in the nave's own
  columns its head would stand on the foot of the pair by the box), plaques and tied fortunes on both sides
  and twice the hanging lanterns. `HALLS` maps a hall's
  tile to its door cell, `NAMES` gives a hall its own name: Kushida, Dazaifu Tenmangu, and the hall inside the
  palace moat, "Palace Shrine" (`ShrineTokyo1`) - "Shrine · Imperial Palace" would not fit a phone's one-row
  HUD bar at 667x375 (issue #219). A name of its own does not make a hall large: `LARGE` lists those.
- **Lantern light.** The room is `interior` (never offered to the blog pipeline, no day/night grade) and
  `lanternLight`: at night only, `DayNight.gradeFor` dims it warm (`LANTERN_NIGHT`) and every `*-lanterns*`
  tile gets its halo. `shopEnabled: false`: nothing in it is a konbini fixture.
- **Something to do** (`src/ShrineVisit.js`, two `shrine` rules in `Interactions.js`; proposed, not yet
  confirmed by the owner - the file's header says how to take it out): bump the offering box and ¥5 goes in,
  the bell rings (a toast: there are no sound effects) and a blessing is said; bump the fortune stand and
  ¥100 draws the day's omikuji, great blessing to great curse. One a game day, kept in the shop's save blob,
  read back free until the date changes. No overlay, no key: a bump, so touch works as it stands. One visit
  per bump (`ShrineVisit.fresh`): a key held against the box or the stand pays once, until it is let go - also
  across the menu or any overlay opened and closed with the key still down (`ShrineVisit.carried`, fed
  `InputHandler.heading()` every frame: while the direction that bumped is held the bump's time moves with the
  clock; let go for `HELD_MS` it is over, so a key pressed again inside the menu is a new bump).
- **Art**: `tools/generate_shrine_art.py` (needs Pillow; `--preview out.png`) draws every piece as shaded
  pixel art in the two looks (`shrine-in-<piece>-red|blue`, shared pieces `shrine-in-<piece>`); the temple
  packs are exteriors only, and `tools/extract_shrine.py` cuts the one interior piece they have, the garland.
  Both are in `check_generators.py`.
- **Doors and blog NPCs**: the door-front cell stays clear (`NPCManager.atDoorway`; `shrines.test.js` holds
  it for every dated position). `the shrine` LANDMARK stands its visitor at building cell `(1, 6)`, the foot
  of the two steps: two cells below the door, not in front of it, and walked round by the side of the
  bottom step. A base NPC is config data and is moved by hand when a door opens where it stood: Xander's
  Asahikawa cell was the one in front of the hall's door (31,27) and is (33,28) now, by the east fox.

### Underground arcades (chikagai)

Japanese cities run a shopping arcade under their main streets, reached by stairs from the pavement. A town
gets one from three files: `tools/chikagai.py` (data only: the arcade's shape, its shopfronts, its exits and
where each exit's entrance stands on the street), `tools/generate_chikagai.py [Host ...]` (the room
`Chikagai<Host>` and the doors into it) and `tools/generate_chikagai_art.py` (the `chika-*` sprites and the
street entrance, `chikagai-entrance-snow`, 2x3: solid but for the foot of its steps, a pair of door cells).

- **The town's own generator stamps the entrances** where the table says (`chikagai.TOWNS[town]['exits'][slug]
  ['street']`), sealed; `generate_chikagai.py` opens them and wires both door cells of each, and
  `roomgen.save_config` keeps those doors through a town rebuild (`OWNED_DOORS`, marker `chikagai` on the room,
  as a house's or a lobby's). Walking onto the steps takes you down to the foot of the matching stairs; each
  exit brings you back up onto the cell in front of its entrance.
- **The room** is a cross of corridors: an east-west hall with 3x2 shopfronts set into its north wall behind a
  tan apron, and a stem north and south. Exits in a north wall are stairs under a yellow exit sign with the
  place's name (`chika-exit-<slug>`, drawn from the table); one in a south wall is steps in the front wall under
  a hanging sign (`chika-sign-<slug>`). Tactile paving runs from every exit to a line down the hall; pillars,
  benches and planters stand south of it (the station interior's sprites); coin lockers and a floor map at the
  foot of the north stairs; capsule machines at the hall's west end. Movement is held by the room's `boundary`
  (the floor and the stairs), so the walls need no colliders.
- **What a bump does** (`Interactions.RULES`, `Shop.VENUES`): the bakery, the coffee counter and the standing
  bar sell a short list (see Shop); the bookshop, the florist, the shuttered front, the capsule machines and the
  map say one line. The room is `interior` and `shopEnabled: false`: no day/night grade, never offered to the
  blog pipeline, no stamp.
- **Sapporo** has the first: **Aurora Town** (`ChikagaiSapporo`, 42x21). Its four entrances are beside the
  station's doors (28,13), in Odori Park's east block on the path (33,23, where a tree stood), tucked in by the
  TV Tower (52,24, reached up the plaza's east side; the two shrubs there went) and east of Tanukikoji (47,37).
  Underground the station stairs are at the head of the north stem, Odori Park's and the TV Tower's at the two
  ends of the hall, Tanukikoji's at the foot of the south stem. When stage 4 builds Susukino the south exit
  belongs there: move its `street` cell in the table and re-run both generators.
- **Another town**: add a row to `chikagai.TOWNS`, stamp `chikagai.ENTRANCE` at each exit's `street` cell in the
  town's generator, run `generate_chikagai_art.py` (exit signs), `generate_chikagai.py <Town>`, then
  `config_to_tiled.py Chikagai<Town> <Town>` and `play.js lint` for both. The entrance art has snow on its
  roof; a town without snow needs a second entrance sprite first.
- Tests: `tools/tests/chikagai.test.js`.

### The palace's audience hall (issue #215)

**What "the palace" is on the map.** Inside the moat of the Tokyo district `Tokyo` (display name "Imperial
Palace") stands one long blue-roofed building: a central hall, three `temple-hallway` pieces either side of
it and a three-storey tower (`pagoda-roof` over `pagoda-floor`) at each end. The central hall is the `shrine`
prefab and opens into its worship hall, "Palace Shrine" (`ShrineTokyo1`, see above): that door is untouched.
The towers are the palace's own doors: the foot of each (building cell `(1, 2)` of its `pagoda-floor`:
`Tokyo` 19,22 and 41,22) carries a hidden transporter into ONE interior, `PalaceHallTokyo1` (HUD: `Palace
Hall`, the Map footer `Palace Hall (in Tokyo)`). You come in at the foot of a side corridor and go out by
either door: the west mats put you on 19,23, the east mats on 41,23, so the hall is also a way through.

- **`tools/generate_palace.py`** owns the interior and the two doors, in the shrine generator's pattern: the
  room is rebuilt from scratch (its NPCs kept); in the host, which is a ported map with no generator, it
  removes the one collider on each door cell and puts the transporter on it, replaced in place, and touches
  nothing else. A re-run is a no-op, and from a sealed palace it rebuilds the same world (`palace.test.js`).
  `.agent-queue/items/palace_apply.sh` is the whole thing for a checkout whose palette has moved on (art,
  generator, `config_to_tiled`, lint, the doorway check, the five gates).
- **Door keeping.** The room carries `palace: {host, doors}` and `'PalaceHall'` is a row of
  `roomgen.OWNED_DOORS` (`PALACE_DOORS`: the `pagoda-floor` sprite, on `Over Floor`, which is why
  `roomgen.DOOR_LAYERS` names two layers). A pagoda in another town is the same sprite and is not a palace: a
  door counts only when it leads into a room with the marker.
- **What is inside** (26x22; the floor is 24x15), an Edo audience hall (ohiroma):
  - the back wall, three rows tall, under the edge of a coffered ceiling: twelve cells of gold-leaf screens
    painted as one picture (`mural`: an old pine, cranes, gold cloud, water), staggered shelves
    (`alcove-shelves`) to their left and tasselled lacquer doors (`alcove-doors`) to their right;
  - the dais (`dais`, 12x3, solid): a matted floor one step up with the lord's empty seat, his arm rest and
    sword, two candle stands, two braziers; a suit of armour west of it, a rack of swords east;
  - a tatami hall, the retainers' cushions in two rows, six gilt lamps hung over it (`lamp-hang`, Tops);
  - a side corridor (engawa) of boards two cells wide down each side, daylight through its paper screens
    lying across it (`sun-w` / `sun-e`, flat), separated from the mats by vermilion-and-black pillars;
  - a long corridor across the front between the two doors, walled off from the hall by two runs of painted
    screens (`fusuma-tiger`, `fusuma-waves`, 6x2) with a four-cell way through between them;
  - in that corridor: the visitors' book and the guard's rack of polearms by the west door; a waiting room
    at the east end, a folding screen (`byobu`), tea on a low table, cushions.
- **Depth** (see `occlusion.md`): pillars are 1x3 with only the foot solid; the painted screens are two rows
  with only the foot row solid, so from the hall you walk behind their heads and they fade; the armour, the
  swords, the lamps, the folding screen and the book stand are solid at the foot only; the hung lamps are
  `Tops` with a `depthBias`.
- **Lantern light.** `interior` (never offered to the blog pipeline) and `lanternLight`: at night only the
  hall dims warm and its lights come on. They are not `*-lanterns*` tiles: each has its spots in
  `Glows.SPRITES` with numeric colours (`palace-in-andon`, `-lamp-hang`, `-guardpost`, and on `-dais` the two
  candles, which breathe, and the braziers' embers).
- **Something to do** (`src/PalaceVisit.js`, two `palace` rules and three `flavour` rules in
  `Interactions.js`; the orchestrator's proposal, not confirmed by the owner - the file's header says how to
  take it out): bump the dais and you request an audience; one of six dry answers, in turn. Bump the armour,
  the swords or the guard's post for a line. Bump the visitors' book and you sign it: free, once a game day,
  kept as `guestbook: {date, n}` in the shop's save blob (see `shop-and-economy.md`); a second bump that day
  reads it back. No overlay, no key; one answer per bump by the offering box's rule (`ShrineVisit.fresh` /
  `.carried`).
- **Art**: `tools/generate_palace_art.py` (needs Pillow; `--preview out.png`) draws all 32 sprites
  (`palace-in-<piece>`) as shaded pixel art at the shrine kit's scale; every scatter is seeded, so a re-run
  is byte-identical. It and the generator are in `check_generators.py`.
- **Doors and blog NPCs**: no dated position, district stand cell or landmark stand cell is on a tower door
  or the cell in front of it (`palace.test.js` holds it for every date); `the Imperial Palace gate` (28,34)
  and `the palace moat` (20,33) are far from both.

### The temple's main hall (issue #213)

**What "the temple" is on the map.** At the head of the stall street in the Tokyo district `Market` (display
name "Asakusa") stands one great red-roofed hall laid from tiles (`shrine-walls` under `red-shrine-top-parts`),
twelve cells wide, its double door at the top of four `castle-stairs`: the hall the `Senso-ji temple` landmark
hangs on. It is not the district's shrine: that is the smaller `shrine-red` prefab east of it (43,11), which
keeps its own door and worship hall (`ShrineMarket1`, "Shrine · Asakusa", see "Shrine worship halls"). The
temple hall was sealed; its two door leaves (`shrine-walls_2_2` at `Market` 27,15 and 28,15) each carry a
hidden transporter into ONE interior, `TempleMarket1` (HUD: `Senso-ji`, the Map footer `Senso-ji (in Tokyo)`).
You arrive inside the leaf you walked through and leave onto the step below it (27,16 / 28,16).

**Senso-ji only, for now.** Zuihoden in Sendai (a mausoleum: black lacquer and gold) and any other temple get
their interior when their city is rebuilt (#219): the rebuild moves those buildings, so a door wired today would
be redone. `tools/generate_temple.py` is written for one hall; a second one is a second host and layout there.

- **`tools/generate_temple.py`** owns the interior and the two door cells, in the palace generator's pattern:
  the room is rebuilt from scratch (its NPCs kept); in the host, a ported map with no generator, it removes the
  one collider on each leaf and puts the transporter on it, replaced in place, and touches nothing else. It
  finds the door as the two `shrine-walls_2_2` tiles side by side with a step below each (the gate and the side
  halls are laid from the same family and have no such pair). A re-run is a no-op, and from a sealed temple it
  rebuilds the same world (`temple.test.js`). `.agent-queue/items/temple_apply.sh` is the whole thing for a
  checkout whose palette has moved on (art, generator, `config_to_tiled`, lint, the doorway check, the gates).
- **Door keeping.** The room carries `temple: {host, doors}` and `'Temple'` is a row of `roomgen.OWNED_DOORS`
  (`TEMPLE_DOORS`: the `shrine-walls_2_2` leaf, the door cell itself). The same tile elsewhere is not a temple
  door: a door counts only when it leads into a room with the marker.
- **What is inside** (26x22; the floor is 24x15), a Buddhist main hall (hondo): dim, old gold and dark red
  lacquer on worn stone - not the shrine's bright hall and not the palace's mats and boards:
  - the back wall, three rows tall, one picture cut into five pieces, under the edge of a coffered painted
    ceiling and a frieze (clouds; over the sanctum two dragons either side of a flaming pearl): the charm
    counter (`wall-charms`) at the head of the west aisle; old gold panels with a heavenly maiden each, brocade
    banners and hung lanterns (`wall-tennin-l` / `-r`); between them the cabinet (`kuden`) - the golden canopy
    (tengai) hung with jewels, the seated Kannon half-hidden behind brocade curtains; the hundred-drawer
    fortune cabinet with its shaker cylinder (`omikuji`) at the head of the east aisle;
  - the inner sanctum (`naijin`, 16x4, solid): mats, the altar and its offerings, two banks of candles, gilt
    lotus stands, the monk's seat, all behind a gilt lattice drawn as a mesh you see through, open in the
    middle over a low rail under a brocade valance;
  - down the middle, on the door's two columns: the offering box (`saisen`, 4x2), the great bronze incense
    burner with its smoke (`jokoro`, 4x3), and inside the doors the great red paper lantern (`chochin`, 4x3,
    `Tops`; its lettering is 観音, "Kannon": no sponsor's name);
  - eight columns, the great drum and the bowl bell before the lattice, a rack of votive candles on the west
    wall, the rail of tied-up bad fortunes on the east, candle stands, vases of gilt lotus and a bench either
    side of the doors, hung gilt lanterns and a little incense haze (`haze`, `Tops`, nearly transparent).
- **Depth** (see `occlusion.md`): columns are 1x3 with only the foot solid; the burner's top row (its smoke)
  is walked behind; the great lantern and the hung lanterns are `Tops` under four rows tall with a
  `depthBias`, so you walk under the great lantern and it fades over you.
- **Lantern light.** `interior` (never offered to the blog pipeline) and `lanternLight`: at night only, the
  hall dims and its lights come on, each a row of `Glows.SPRITES` with numeric colours (`temple-in-toro-hang`,
  `-shokudai` and `-candles`, which breathe, `-chochin`, the embers of `-jokoro`, and on `-naijin` and `-kuden`
  the sanctum's candles and gold).
- **Something to do** (`src/TempleVisit.js`, three `temple` rules and six `flavour` rules in `Interactions.js`;
  the orchestrator's proposal, not confirmed by the owner - the file's header says how to take it out). Bump
  the burner and you waft the smoke over yourself: free, five lines in turn. Bump the offering box: the
  shrine's ¥5 and blessings (`ShrineVisit.offer`), worded for a temple (palms together, no bell). Bump the
  fortune drawers: you shake a numbered stick out of the cylinder - it is the shrines' omikuji, decided by
  `ShrineVisit.fortune` with the same ¥100, odds and save field (`omikuji: {date, i}`), so there is ONE
  fortune a game day across every shrine and the temple; only the wording is the temple's. The charm counter
  sells nothing (the catalogue has no charm and none was invented): it, the sanctum, the drum, the bowl bell,
  the candles and the tied fortunes say a line. No overlay, no key, nothing of its own in the save; one answer
  per bump by the offering box's rule (`ShrineVisit.fresh` / `.carried`). A toast is one line, so every line is
  96 characters or fewer.
- **Art**: `tools/generate_temple_art.py` (needs Pillow; `--preview out.png`) draws all 29 sprites
  (`temple-in-<piece>`) as shaded pixel art at the shrine kit's scale; every scatter is seeded, so a re-run is
  byte-identical. It and the generator are in `check_generators.py`.
- **Doors and blog NPCs**: no dated position or district stand cell is on a door leaf or the step in front of
  it (`temple.test.js` holds it for every date). The `Senso-ji temple` LANDMARK stands its visitor one cell
  below the WEST end of the steps (26,17: Bailey on 1 November 2025), beside the way up, not on it. He
  wanders (two cells either way) but cannot close the doors: a wanderer never steps onto a transporter or a
  cell beside one (`NPCManager.atDoorway`), so the step under each leaf stays free, and wherever else he
  stands both leaves are still walked into from the street, stitched or not (`temple.test.js`).

### The Sendai pub (issue #217)

**What "the pub" is on the map.** One sprite, `sendai-pub_0_0` (5x5), downtown in `Sendai`: the building the
trip watched the baseball in (post 505), and the `the HUB pub` landmark. It was sealed. The door drawn in the
middle of its front row (the sprite's cell + (2,4); `Sendai` 28,20 as the town stands) carries a hidden
transporter into `PubSendai1` (HUD: `The Pub`, the Map footer `The Pub (in Sendai)`). You arrive just inside
the doorway and the mat behind you (two cells wide) puts you back on the pavement in front of the door.

**Why it did not wait for the town's rebuild**, though "Senso-ji only, for now" above says temples do. The
temple's door is a pair of tiles at fixed cells; this door, the distillery's and Canal City's are **found by
sprite** (`roomgen.sprite_doors`: the building's cell plus an offset from `roomgen.PUB_DOORS`), so nothing
about them is written down as a coordinate, in the generator or in its tests. What the #219 rebuild owes them:
if it moves the building, the town generator leaves it sealed (`roomgen.owned_door` keeps a door only where
the building still stands), and `generate_pub.py` then `config_to_tiled.py PubSendai1 Sendai` must be run
again: it finds the building where it now is and wires the door anew. Nothing else needs an edit.

- **`tools/generate_pub.py`** owns the interior and the door cell. The room is rebuilt from scratch (its NPCs
  kept) on the shared shell, `tools/interiors.py` (`Interior`: the void, the floor, the walls, the mat and its
  exits, the boundary, and the check that every open floor cell is reached from the door); in the host it
  removes the one collider on the door and puts the transporter on it, replaced in place (`roomgen.open_door`),
  and touches nothing else. `generate_sendai.py` is not edited. A re-run is a no-op, and from a sealed
  building it rebuilds the same world (`pub.test.js`).
- **Door keeping.** The room carries `pub: {host, doors}` and `'Pub'` is a row of `roomgen.OWNED_DOORS`
  (`PUB_DOORS`), so a re-run of `generate_sendai.py` keeps the door (`check_generators.py` proves it).
- **What is inside** (20x17; the floor is 18x10), a proper pub in dark wood, green and brass:
  - the back wall, three rows tall: the back bar (`wall-backbar`, 7 wide: mirrors, shelves of bottles,
    cupboards), green wallpaper over panelling with framed prints (`wall-panel`, `wall-print`), the big screen
    with the baseball on (`wall-tv`, 4 wide: the diamond, the fielders, the score 3-2) and the dartboard in
    its cabinet (`wall-darts`);
  - the bar (`bar`, 7x2, solid) under the back bar and flush to the west wall, so nobody gets onto the
    staff's side: three sets of taps, the till, glasses; stools along its front with a gap between each to
    order through;
  - four tables with a chair either side (`table`, `chair-w` / `-e`), two booths back to back on the east
    wall (`booth`, 2x3, solid throughout), the specials on a chalkboard by the west wall (`chalkboard`, 1x2:
    its head is walked behind), green glass lamps (`lamp-hang`, `Tops`) over the bar and every table.
- **Lantern light.** `interior` (never offered to the blog pipeline) and `lanternLight`: at night only, the
  room dims and its lamps, the back bar and the screen glow (`Glows.SPRITES`: `pub-in-lamp-hang`,
  `-wall-backbar`, and `-wall-tv`, which swells slowly).
- **Something to do.** Bump the bar and it sells the izakaya's list as `Shop.VENUES.taproom`, titled THE PUB
  (see `shop-and-economy.md`): no stamp, no fish bought. The screen, the dartboard and the chalkboard say a
  line each (`flavour` rules in `Interactions.js`; the screen's is post 505's own words). No new overlay, key
  or save field.
- **Art**: `tools/generate_pub_art.py` (needs Pillow; `--preview out.png`) draws the 21 sprites
  (`pub-in-<piece>`) at the palace kit's scale. Its frame (`wall_side`, `wall_front`, `threshold`,
  `doorlight`, each taking a palette), its helpers and `register()` are imported by the distillery's and
  Canal City's art tools. It and the generator are in `check_generators.py`.
- **Doors and blog NPCs**: no dated position or district stand cell is on the door or the cell in front of
  it, and a wanderer never steps there (`NPCManager.atDoorway`). The `the HUB pub` LANDMARK stands its
  visitor on the pavement beside the door (the sprite's cell + (3,5): Julia on 29 October 2025).
- **Build order**: `generate_pub_art.py`, `generate_pub.py`, `config_to_tiled.py PubSendai1 Sendai`,
  `play.js lint PubSendai1 Sendai`. Tests: `tools/tests/pub.test.js` (the checks the three interiors share
  are `tools/tests/interiors.js`).

### The Nikka distillery's tasting bar (issue #217)

**What "the distillery" is on the map.** One sprite, `sendai-kiln_0_0` (5x6), in the south-west of `Sendai`:
the red brick kiln house, the `the Nikka distillery` landmark of the Sakunami day out. It was sealed. The door
under its WHISKY sign (the sprite's cell + (2,5); `Sendai` 5,33 as the town stands) carries a hidden
transporter into `DistillerySendai1` (HUD: `Distillery`, the Map footer `Distillery (in Sendai)`). You arrive
just inside the doorway and the mat behind you (two cells wide) puts you back in the lane in front of the door.
Like the pub's, the door is found by sprite (`roomgen.DISTILLERY_DOORS`) and did not wait for the #219
rebuild; what the rebuild owes it is the same (see "The Sendai pub"): if the kiln moves, run
`generate_distillery.py` then `config_to_tiled.py DistillerySendai1 Sendai`. If the tasting bar should later
sit behind another building of the distillery, that is one row in `DISTILLERY_DOORS`.

- **`tools/generate_distillery.py`** owns the interior and the door cell, exactly as `generate_pub.py` does
  the pub's (`interiors.Interior`, `roomgen.sprite_doors`, `roomgen.open_door`); `generate_sendai.py` is not
  edited. A re-run is a no-op, and from a sealed kiln it rebuilds the same world (`distillery.test.js`).
- **Door keeping.** The room carries `distillery: {host, doors}` and `'Distillery'` is a row of
  `roomgen.OWNED_DOORS` (`DISTILLERY_DOORS`), so a re-run of `generate_sendai.py` keeps the door.
- **What is inside** (20x15; the floor is 18x8), a small tasting bar in brick, oak, copper and stone flags:
  - the back wall, three rows tall: casks racked three high (`wall-casks`, 4 wide), brick under a beam
    (`wall-brick`), the kiln's two arched windows (`wall-window`), and the bottles behind the counter under
    the sign (`wall-shelf`, 5 wide);
  - **one copper pot still** (`still`, 3x4) against the back wall: the pot on its brick hearth, the swan
    neck with the rope Nikka ties round it, the lyne arm down to the condenser. Its two lower rows are solid;
    the neck and the arm are walked behind;
  - the tasting counter (`counter`, 5x2, solid) under the bottles and flush to the east wall, so nobody gets
    onto the staff's side: three flights of drams poured on it; two stools along its front with a place to
    stand either side of each;
  - casks stood on end by the side walls (`cask`), copper lamps (`lamp-hang`, `Tops`) over the counter,
    either side of the still and in the middle of the floor.
- **Lantern light.** `interior` and `lanternLight`: at night only, the room dims and its lamps glow, and the
  windows faintly (`Glows.SPRITES`: `distillery-in-lamp-hang`, `-wall-window`).
- **Something to do.** Bump the counter and it pours a Highball as `Shop.VENUES.tasting`, titled TASTING BAR
  (see `shop-and-economy.md`): no stamp, no fish bought. The still says a line, and so do the casks, racked or
  on the floor (`flavour` rules `pot-still` and `casks` in `Interactions.js`). No new overlay, key or save
  field.
- **Art**: `tools/generate_distillery_art.py` (needs Pillow; `--preview out.png`) draws the 17 sprites
  (`distillery-in-<piece>`); the frame is the pub art tool's, in the kiln's own brick. It and the generator
  are in `check_generators.py`.
- **Doors and blog NPCs**: no dated position or district stand cell is on the door or the cell in front of
  it, and a wanderer never steps there. The `the Nikka distillery` LANDMARK stands its visitor in the lane
  beside the door (the sprite's cell + (3,6): Damian on 29 October 2025, Julia on the 30th).
- **Build order**: `generate_distillery_art.py`, `generate_distillery.py`,
  `config_to_tiled.py DistillerySendai1 Sendai`, `play.js lint DistillerySendai1 Sendai`. Tests:
  `tools/tests/distillery.test.js` (on `tools/tests/interiors.js`).

### Canal City's atrium (issue #217)

**What "Canal City" is on the map.** One sprite, `canal-city_0_0` (8x6), west of the avenue in `Fukuoka`: the
`Canal City` landmark of post 727. It was sealed. The two leaves of the door under its arch (the sprite's cell
+ (3,5) and + (4,5); `Fukuoka` 15,29 and 16,29 as the town stands) each carry a hidden transporter into
`MallFukuoka1` (HUD: `Canal City`, the Map footer `Canal City (in Fukuoka)`). The west leaf puts you on the
west half of the doorway and the east on the east, and the mat behind you puts you back on the plaza in front
of the leaf above it. Like the pub's, the doors are found by sprite (`roomgen.MALL_DOORS`) and did not wait
for the #219 rebuild; what the rebuild owes them is the same (see "The Sendai pub"): if the mall moves, run
`generate_mall.py` then `config_to_tiled.py MallFukuoka1 Fukuoka`. (The mall's top two rows are roof and are
walked behind, as they always were; only the two door cells opened.)

- **`tools/generate_mall.py`** owns the interior and the two door cells, exactly as `generate_pub.py` does
  the pub's (`interiors.Interior`, `roomgen.sprite_doors`, `roomgen.open_door`); `generate_fukuoka.py` is not
  edited. A re-run is a no-op, and from a sealed building it rebuilds the same world (`mall.test.js`).
- **Door keeping.** The room carries `mall: {host, doors}` and `'Mall'` is a row of `roomgen.OWNED_DOORS`
  (`MALL_DOORS`), so a re-run of `generate_fukuoka.py` keeps both doors.
- **What is inside** (28x23; the floor is 26x14), a bright atrium in cream stone and terracotta. It is not a
  mall to shop in: nothing is sold.
  - the back wall, **five** rows tall (the pub's and the distillery's are three): six piers (`wall-pier`,
    1x5) and between them five shopfronts (`front-fashion`, `-toys`, `-okonomiyaki`, `-cafe`, `-ramen`, 4x5:
    one function, the `FRONTS` table). The top two rows of every piece are two gallery levels: small lit
    fronts, a glass rail, a terracotta balcony that bows out over each shop;
  - **the canal** through the middle of the floor, three rows from wall to wall (`canal-n-a/-b`, `canal-a/-b`,
    `canal-s-a/-b`): the same teal water, cream coping with a terracotta band and brick quay as the street
    canal `generate_fukuoka_town_art.py` draws for #219 (whose `fukuoka-canal*` sprites are not registered or
    placed here). It is drawn art on the `Water` layer over the paving, **not** `pond-autotile`: there is no
    `pond` rule on it and nobody fishes indoors. Solid, except under the bridges;
  - **two footbridges** (`bridge`, 2x3, `Non-Collidables`, `depthBias: -200`: the `dazaifu-bridge` recipe,
    written by the art tool), the only ways across, either side of **the fountain** (`fountain`, 4x3, solid,
    standing in the canal; it carries its own water and quays, so no canal piece lies under it);
  - benches facing the water on both banks (the station's `station-bench` on the north bank with a promenade
    between it and the quay, `station-bench-back` along the south), `station-planter-a/-b` at the ends of the
    south row and either side of the door, palms in tubs (`palm`, 1x2). Each bench and planter is 2x2 with only
    its lower row in the way; none stands in a bridge's columns.
- **No lantern light.** `interior` but not `lanternLight`, and no `Glows` rows: an atrium is as bright at
  night as by day.
- **Something to do.** Bump the fountain or a shopfront for a line (`flavour` rules `mall-fountain`,
  `mall-fashion`, `mall-toys`, `mall-okonomiyaki`, `mall-cafe`, `mall-ramen` in `Interactions.js`); cross the
  bridges. The water itself says nothing. No venue, no stamp, no new overlay, key or save field.
- **Art**: `tools/generate_mall_art.py` (needs Pillow; `--preview out.png`) draws the 23 sprites
  (`mall-in-<piece>`); the frame is the pub art tool's, in cream and terracotta. It and the generator are in
  `check_generators.py`.
- **Doors and blog NPCs**: no dated position or district stand cell is on a door or the cell in front of one,
  and a wanderer never steps there. The `Canal City` LANDMARK stands its visitor on the plaza beside the doors
  (the sprite's cell + (2,6): Julia on 10 November 2025). Post 727 stays outside: moving it into the atrium
  would need the blog pipeline to place into an `interior` room, which it never does.
- **Build order**: `generate_mall_art.py`, `generate_mall.py`, `config_to_tiled.py MallFukuoka1 Fukuoka`,
  `play.js lint MallFukuoka1 Fukuoka`. Tests: `tools/tests/mall.test.js` (on `tools/tests/interiors.js`).
### Pagodas (issue #214)

**What a pagoda is on the map, and the count.** A pagoda is its base sprite on the `Collidables` layer:
`pagoda-floor` (the foot of the five-roofed one) or `red-pagoda-small-base` (a small red one, the `pagoda-small`
prefab). There are five, and three can be walked into:

| Town | What stands there | Door cells -> where you come back out | Interior |
|---|---|---|---|
| `Market` (Asakusa) | the five-roofed pagoda west of Senso-ji (`pagoda-floor` at 10,10) | 11,12 -> 11,13 | `PagodaMarket1`, "Pagoda · Asakusa", five storeys |
| `Park` | three small red pagodas in one column (34,7 / 34,11 / 34,15), drawn overlapping so they read as one tall tower | the two behind (doors 34,9+35,9 and 34,13+35,13) have the next one's roof across their doors: sealed, and they keep the numbers 1 and 2. The front one: 34,17 and 35,17 -> 34,18 | `PagodaPark3`, "Pagoda · Park", five storeys |
| `Fukuoka` | the small red pagoda of old Hakata (57,29) | 57,31 and 58,31 -> 57,32 | `PagodaFukuoka1`, "Pagoda · Fukuoka", three storeys |

The two `pagoda-floor` in `Tokyo` are not pagodas: they are the palace's end towers, laid flat on `Over Floor`,
and their doors are the audience hall's (see above). Fukuoka's pagoda is due to be replaced when that town is
rebuilt (#219): the door then goes with it (`keep_house_doors` keeps a door only on the sprite it was wired to)
and a `generate_pagodas.py` run deletes the room; whoever rebuilds runs it again.

- **One room per pagoda, holding every floor** (`W = 21`; `H = 7 + 8 * storeys`, so 21x47 or 21x31): the tower
  cut open and seen from the front. The storeys stand one above the other up the screen, the ground floor at the
  bottom, each narrower than the one below (`FLOORS`: 9, 9, 7, 7, 5 cells, or 9, 7, 5), the roofs' skirts
  flaring into the dark outside every floor and the top roof with its spire over the last. There is no door
  between storeys: you walk up each stair yourself and the camera climbs the tower with you. One room rather
  than one a floor, which would cost a fade per floor, ten more maps, and floor numbers a phone's bar has no
  room for.
- **A storey** is eight rows, `top(k) = 6 + 8 * (storeys - 1 - k)` for storey `k` (0 is the ground floor): two
  rows of back wall, five of boards, then the floor's cut edge (the stone base and the threshold on the ground
  floor). On it:
  - the heart pillar (`pillar`, 1x3, solid at its foot only: you walk behind it) in the middle of every floor;
    on the ground floor it rises out of a dais with four small Buddhas round it (`shumidan`, 3x3, its bottom
    row solid), the offering box (`saisen`) in front and a candle stand (`shokudai`) either side;
  - a steep stair (`stair`, 1x3, flat) on the back wall, on alternate sides (`stair_x`: column 12 from an even
    storey, 8 from an odd one), up through the floor above and out of a hatch in its boards (`hatch`), so on
    every floor you walk round the pillar to the next one;
  - on a middle storey, on the wall away from the stair, sutra chests (`kyozo`) or a wall of tiny gilt Buddhas
    (`senbutsu`) - which, in which order, comes from the pagoda's seed, so two towers are not the same; on the
    top storey a slatted window (`window`); one iron lantern (`toro-hang`, `Tops`) hung on every storey, never
    over a stair or a hatch.
- **Depth and movement.** The walls, the edges, the eaves, the roof and the stair are flat (`Floor` /
  `Over Floor`) with no colliders, so nothing is drawn over you on a stair. What holds you in is the room's
  `boundary`: the outline of the floors, the stairs and the mat. The room is built on the shared shell
  (`interiors.Interior`, "Interior building blocks" in `generators-and-checks.md`): the shell's floor is the
  ground floor's boards, the storeys above it and the stairs are added to its `walk`, and `Interior.room` draws
  the boundary round all of it. The colliders are the pillars' feet, the dais, the box, the candles and the
  fittings on the walls. Before anything is saved the shell fails on a floor, stair or hatch cell that cannot
  be reached from the mat, and the generator on anything with a line that cannot be bumped.
- **The roof and the look-up.** The top roof and the spire are ONE sprite (`pagoda-in-roof`, 9x6) and it is an
  entry of `game.lookUp.sprites` (2: the two rows of back wall under it; registered by the art tool, see
  "Looking up at landmarks" in `hud-input-touch.md`). The ordinary camera trails you by five rows, which on the
  top storey would cut the spire off; with the entry the camera looks up from the top storey's floor, stops
  against the room's top edge and shows the whole spire under the HUD bar, and is the ordinary camera again by
  the storey below. One sprite as wide as the roof, so the view does not slide sideways as you cross the floor.
  On a phone the view is too short to hold you and the spire at once: it shows as much of the roof as fits.
- **`tools/generate_pagodas.py [Host ...] [--dry-run]`** owns the rooms and their doors, in the shrine
  generator's pattern: `rooms.Pagoda<Host><n>` is rebuilt from scratch (`n` counts the town's pagodas by door,
  sealed ones too), each open door cell of the host loses its collider and carries a hidden transporter,
  replaced in place, and both doors of a pair arrive on the same cell inside; the mat puts you back in front of
  the first door. Finding pagodas and the stay-sealed rules are the houses' (`generate_houses.find_houses` with
  a kind of its own: front cell solid or unreachable, somebody standing there on any date, a blog stand cell).
  With no host it rebuilds the pagodas of the towns that have a `pagoda` marker, which is what
  `check_generators.py` runs; **to open a new town's pagodas name it** (`python3 tools/generate_pagodas.py
  Sendai`, after `--dry-run`), then `config_to_tiled.py` and `play.js lint` for the rooms it prints. Storeys
  come from the base sprite (`STOREYS`: 5 for `pagoda-floor`, 3 for the small red one); `TALLER` is the one
  exception, the Park's front pagoda, which stands for a tower of three.
- **Door keeping.** The room carries `pagoda: {host, door, doors, storeys}` and `'Pagoda'` is a row of
  `roomgen.OWNED_DOORS` (`PAGODA_DOORS`), so a rebuild of the town keeps the door (`pagodas.test.js` rebuilds
  Fukuoka on a scratch copy).
- **Lantern light.** `interior` (never offered to the blog pipeline) and `lanternLight`: at night the room dims
  and the lanterns and the candles glow, each a row of `Glows.SPRITES` (`pagoda-in-toro-hang`, `-shokudai`).
- **Something to do**: rules of `Interactions.js` only, no file, key or save field of its own. The offering box
  is the temple's rule (`/^(temple|pagoda)-in-saisen/`, `TempleVisit`): the shrine's ¥5 and blessings, palms
  together. The pillar, the four Buddhas, the chests, the niches and the window say a line each (`flavour`,
  96 characters or fewer).
- **On the bar**: `Pagoda | Asakusa`; `'Pagoda'` is one of `HUD_KINDS`, so a phone abbreviates it to `Asakusa
  pagoda`, as it does a shrine.
- **Art**: `tools/generate_pagoda_art.py` (needs Pillow; `--preview out.png`) draws the 31 sprites
  (`pagoda-in-<piece>`): dark timber, vermilion posts, old gold. Seeded, so a re-run changes nothing. It and
  the generator are in `check_generators.py`.
- **Doors and blog NPCs**: no dated position or district stand cell is on a door or the cell in front of it,
  and the visitor of the spot `the pagoda` stands where they did before the doors opened (Market 9,4, Park
  33,10, Fukuoka 56,27; `pagodas.test.js`).

### The Devhouses of Tokyo and Osaka (issue #69)

The two houses the trips stayed in, built from their real floor plans (the five images on the issue), a room
per floor. `tools/generate_devhouses.py` owns all ten rooms and the two street doors; the art is the home kit
plus `tools/generate_devhouse_art.py`.

| | Tokyo | Osaka |
|---|---|---|
| Where | Minato: the paved square under Tokyo Tower's feet, in the district `Park` | Dotonbori, beside Don Takote, on the lot the black townhouse had |
| Outside | `devhouse-tokyo` (5x8, six storeys), stamped at `Park` 10,9 | `devhouse-osaka` (3x7, four storeys), `b.stamp('devhouse-osaka', 9, 10)` in `generate_osaka.py` |
| Street door | `Park` 13,16; you leave onto 13,17 | `Osaka` 10,16; you leave onto 10,17 |
| Rooms | `DevhouseTokyo1F..6F` | `DevhouseOsaka1F..4F` |
| Floors | 1F and 2F are not ours: a locked door and the stairs. 3F the kitchen, the long table and the sofa; 4F beds and a bunk; 5F the tatami room, the bath and the "Staff Only" door; 6F two beds, the small table, the washer | 1F the kitchen and the tall table; 2F two tatami bedrooms and the armchairs; 3F bedrooms and the washer; 4F a tatami room that opens onto a zen garden on the roof |

- **`Park` is a ported map with no generator**, so the Tokyo building was stamped once
  (`tools/stamp_prefab.py Park --add devhouse-tokyo 10 9`; a second run refuses, the cells are taken) and the
  map is the source of truth for it. Osaka's is stamped, sealed, by its town generator on every rebuild. In
  both hosts `generate_devhouses.py` finds the building by its sprite (exactly one), takes the collider off
  the door cell (`roomgen.DEVHOUSE_DOORS`: the door's offset on each sprite) and wires a hidden transporter
  onto it, replaced in place: a re-run leaves `config.json` byte-identical, and from two sealed houses it
  builds the same world (`devhouse.test.js`).
- **Names.** `Devhouse 3F · Tokyo`: the floor leads, so a phone's one-row bar, which has room only for the
  part before the dot (`hudBrief`), says `Devhouse 3F` beside the countdown. `Places.of` follows doors to find
  a room's town, and Tokyo's top floor is six stairs and a street door from its district: its hop limit is 8.
- **A floor is data**: `FLOORS` in the generator is a grid of characters per floor (the legend is beside it:
  `ONE` 1x1 pieces, `BIG` footprints with `+` for the rest of their cells, `TALL` pieces walked behind, `BACK`
  the wall pieces), `ZONES` what the floor is laid with where it is not boards (tile in the wet rooms, tatami,
  gravel), and each room is an `Interior` shell (`tools/interiors.py`) in a 20-wide room. Tokyo's 3F-6F are
  14x8 floors; its 1F and 2F are the stair hall of those floors, two cells wide, **on the same room cells**,
  so the stairs line up all the way down. Osaka's floors are 9x10. A `|` partition is drawn with
  `devhouse-wall-v`, its last cell with `-wall-v-end`, and where a `-` wall meets it with `-wall-h`.
  What each floor must hold (so many beds, chairs, the bath...) is counted from `config.json` by
  `devhouse.test.js`; a grid may move a piece by a cell, the counts stay.
- **Stairs are hidden exits laid with a stair tile**, the way a door mat is (`Interior.doorway(..., n=1, fy=,
  inward=, mat='devhouse-stairs-up_0_0')`): `u` leads to the floor above, `d` to the one below. Every stair
  cell has exactly one free cell directly north or south of it, its **arrival cell**. Taking `u` on floor N
  puts you on the arrival cell of `d` on floor N+1, and that `d` puts you on the arrival cell of `u` on
  floor N. An arrival cell is never an exit.
- **The held-key rule.** A room change does not let go of a held key: after the fade the same step is taken
  again from the cell you arrived on. So for every stair and street door, and every direction it can be
  walked into from, that step repeated from the arrival cell at the other end must not land on another exit.
  (With `u` and `d` side by side on one row, holding DOWN on Tokyo's ground-floor stair took you up and
  straight back down for as long as you held it.) Tokyo's `d` is therefore inside the stair hall under a
  `devhouse-stairwell`, walked into heading north, and its `u` on the front row, walked into heading south.
  `devhouse.test.js` checks the rule from `config.json` for every exit, and `tools/browser/regress.js`
  (`devhouse-stair-held`) holds a real key down through a flight in both houses. Move a stair only with
  those two open.
- **Door keeping.** Every floor carries `devhouse: {host, floor}` and only the ground floor also `door`:
  `'Devhouse'` is a row of `roomgen.OWNED_DOORS`, so a rebuild of Osaka puts the street door back
  (`keep_house_doors`), and because `owned_door` is asked about any transporter into a `Devhouse...` room,
  a stair is not a kept door only because 2F and up have no `door` in their marker.
- **The roof garden** (`DevhouseOsaka4F`, floor rows 0-3): raked gravel with stepping stones, a rock, shrubs,
  a stone lantern, two seats, a side table and the goldfish bowl, behind a bamboo fence for a back wall. It
  is the one floor with `lanternLight`: at night it dims and the stone lantern glows (its row in
  `Glows.SPRITES`); the other nine are lit rooms.
- **Something to bump** (five `flavour` rules in `Interactions.js`, each one dry line): the locked doors,
  the bath, the washers, the goldfish bowl, the bunk. Not the chairs and not the tables: twenty chairs ring
  tables you walk round, and a line on each would toast again and again. Nobody lives there and nothing is
  sold; `interior` keeps the blog pipeline out, and the trips' `home` cells are where they were.
- **Lint**: a Devhouse floor is held to the house rules (`house-sealed-floor`, `flavour-no-front`) through
  its `devhouse` marker (`world-model.js`). The generator's shell asserts every free cell is reached from
  the exits before it writes a room.
- **Run order** (from `gamev2/`, Pillow needed; export `PYTHONDONTWRITEBYTECODE=1`, the tools' `.pyc`
  files are tracked):

  ```bash
  python3 tools/generate_devhouse_art.py && python3 tools/make_prefabs.py
  python3 tools/generate_osaka.py                 # stamps the Osaka building, sealed; keeps its door on a rebuild
  python3 tools/generate_houses.py Osaka          # only when Osaka's houses changed
  python3 tools/generate_devhouses.py
  python3 tools/config_to_tiled.py Osaka Park <the ten rooms the generator lists>
  node tools/play.js lint Park Osaka <the same>
  python3 tools/make_worldmap.py                  # when an outside moved
  ```

  Everything here can be re-run at will. The `Park` stamp is not in the list: it was a one-off edit of a
  ported room. After a rebase that lost it, stamp it again once, before `generate_devhouses.py`.
