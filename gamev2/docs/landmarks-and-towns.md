# Landmarks and the train-only towns (Osaka, Sendai, Sapporo, Asahikawa)

Named landmark sprites, adding one, the generated towns of Osaka and Hokkaido (snow, konbini per host, build order), and house interiors.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Featured locations / landmarks (issue #17)

Named landmarks are ordinary multi-cell sprites on a room's `Collidables` layer (Y-sorted by their feet:
solid at the base, walk-behind above), each wrapped in a prefab so generators can `b.stamp()` them:

| Landmark | Room | Sprite key | Art |
|---|---|---|---|
| Tokyo Tower | Palace (feet continue into Park) | `tokyo-tower_0_0` (`tokyo-tower-feet`: its bottom three rows, Park's copy) | the team's line drawing (`art-source/line-art/`) painted by `tools/generate_tokyo_art.py`; the team's art is still wanted (#70) |
| Tokyo Station | Palace | `tokyo-station_0_0` | the team's line drawing (`art-source/line-art/`) painted by `tools/generate_tokyo_art.py`; the team's art is still wanted (#70) |
| Tsutenkaku Tower | Osaka | `tsutenkaku_0_0` | the line drawing (`art-source/line-art/`) painted by `tools/generate_tsutenkaku.py`; the team's art is still wanted (#70) |
| Dotonbori entrance arch | Osaka | `dotonbori-arch_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |
| Dotonbori ferris wheel | Osaka | `dotonbori-wheel_0_0` | GuttyKreum Dotonbori pack via `tools/extract_dotonbori.py` |
| The gondola you board at the wheel's foot | Osaka | `wheel-boarding_0_0` | one of the wheel's own gondolas, cut from its sprite with the door open, by `tools/generate_wheel_art.py` (see "A turn on the Dotonbori wheel") |
| Sapporo Clock Tower | Sapporo | `sapporo-clock-tower_0_0` | shaded pixel art drawn by `tools/generate_hokkaido.py` |
| Sapporo TV Tower | Sapporo | `sapporo-tv-tower_0_0` | shaded pixel art drawn by `tools/generate_hokkaido.py` |
| Sapporo Station front (the star clock), the red-brick government hall (Akarenga) | Sapporo | `sapporo-station-front_0_0`, `sapporo-akarenga_0_0` | shaded pixel art drawn by `tools/generate_sapporo_art.py` |
| Asahikawa Station's glass hall, Asahibashi (the green arch bridge), the ramen alley gate, the Asahiyama Zoo gate | Asahikawa | `asahikawa-station-front_0_0`, `asahibashi-deck_0_0` (with `-arch-w`, `-arch-e`, `-brace`), `asahikawa-ramen-gate_0_0`, `zoo-gate_0_0` | shaded pixel art drawn by `tools/generate_asahikawa_art.py` |
| Date Masamune statue (Aoba Castle ruins) | Sendai | `sendai-masamune_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Zuihoden | Sendai | `sendai-zuihoden_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| The pub (HUB) | Sendai | `sendai-pub_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py`; its door opens into `PubSendai1` (see "The Sendai pub") |
| Nikka distillery kiln house | Sendai | `sendai-kiln_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py`; its door opens into `DistillerySendai1` (see "The Nikka distillery's tasting bar") |
| Matsushima sightseeing boat, pier, islets | Sendai | `matsushima-*_0_0` | shaded pixel art drawn by `tools/generate_sendai_art.py` |
| Fukuoka Tower | Fukuoka | `fukuoka-tower_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py`; the two door leaves in its foot are a lift up to `DeckFukuoka1` (see "Fukuoka Tower's deck") |
| Yatai stalls (ramen, yakitori, oden) and their lantern posts | Fukuoka | `yatai-ramen_0_0`, `yatai-yakitori_0_0`, `yatai-oden_0_0`, `yatai-lanterns_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Canal City and its fountain | Fukuoka | `canal-city_0_0`, `canal-fountain_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py`; the mall's two door leaves open into `MallFukuoka1` (see "Canal City's atrium") |
| Kushida shrine's Yamakasa float | Fukuoka | `hakata-yamakasa_0_0` (beside a `shrine-red` hall) | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Dazaifu Tenmangu: hall, arched bridge, plum trees | Fukuoka | `dazaifu-hall_0_0`, `dazaifu-bridge_0_0`, `plum-tree_0_0` | shaded pixel art drawn by `tools/generate_fukuoka_art.py` |
| Kanazawa Castle's Ishikawa gate | Kanazawa | `kanazawa-ishikawa-gate_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Kenrokuen's Kotoji lantern | Kanazawa | `kanazawa-kotoji_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Higashi Chaya teahouses, the whisky bar | Kanazawa | `kanazawa-chaya-a/-b_0_0`, `kanazawa-whisky-bar_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Gassho farmhouses, the suspension bridge, the viewpoint, the peaks | Shirakawago | `shirakawa-*_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Glass Art Museum, tram and stop, black-ramen shop, port observation tower | Toyama | `toyama-*_0_0` | shaded pixel art drawn by `tools/generate_hokuriku_art.py` |
| Himeji Castle: the keep, a corner turret, the gatehouse, the white wall, the moat bridge | Himeji | `himeji-keep_0_0`, `himeji-turret_0_0`, `himeji-gate_0_0`, `himeji-wall_0_0`, `himeji-bridge_0_0` | shaded pixel art drawn by `tools/generate_kansai_art.py` (see "Kansai") |
| Koko-en's roofed gate | Himeji | `himeji-kokoen-gate_0_0` | shaded pixel art drawn by `tools/generate_kansai_art.py` |
| Okayama Castle: the black "crow" keep | Okayama | `okayama-keep_0_0` | shaded pixel art drawn by `tools/generate_kansai_art.py` (see "Kansai") |
| Korakuen: the Tsukimi bridge, the red-crowned cranes, the stones at the island's corners | Okayama | `okayama-bridge_0_0`, `okayama-crane_0_0`, `okayama-bank-rock_0_0` | shaded pixel art drawn by `tools/generate_kansai_art.py` |
| The Momotaro statue, the Bizen-ware stall | Okayama | `okayama-momotaro_0_0`, `okayama-bizen-stall_0_0` | shaded pixel art drawn by `tools/generate_kansai_art.py` |
| Todaiji: the Great Buddha Hall, the Nandaimon gate | Nara | `nara-daibutsuden_0_0`, `nara-nandaimon_0_0` | shaded pixel art drawn by `tools/generate_kansai_art.py` (see "Kansai") |
| Kasuga Taisha: the torii, the stone lanterns (the hall is the stock `shrine-red`) | Nara | `nara-kasuga-torii_0_0`, `nara-stone-lantern_0_0` | shaded pixel art drawn by `tools/generate_kansai_art.py` |
| The deer of Nara Park, the deer cracker stall | Nara | `nara-deer-doe_0_0`, `nara-deer-stag_0_0` (cut from the UrbanAccessoriesv2 sheet by `tools/extract_street.py`), `nara-deer-bow_0_0`, `nara-senbei-stall_0_0` | the bowing deer and the stall drawn by `tools/generate_kansai_art.py` |

The three placeholders are line drawings with colour laid on (#271): the drawing is kept in
`../art-source/line-art/`, `tools/line_art.py` paints it by rule (regions of the drawing take a material, small
ones on a wall become window panes, the lines take a shade of what they cross; its docstring has the rules) and
the two tools only say which part is which material. The outline and every line are the drawing's own, and the
test below fails if a sprite's alpha differs from its drawing's by a pixel: to change a shape, change the drawing.

The three placeholders (and the team's art, when it replaces them: a PNG of the same size needs no map or code
change) have to fit a map that is not theirs to move, and `tools/tests/landmark-placeholders.test.js` holds them
to it: Tokyo Station's picture is clear over its forecourt (the cells (16..18, 7) and (22..24, 7) of its bottom
row; the small towers either side of the centre block come down to the foot of the row above), where Palace's
shrub gardens, lamp posts and a vending machine stand inside its
footprint, its pavilions' feet are as wide as the cells Palace keeps solid under them (see "Tokyo Station's
footprint" below), and it is clear in its top two rows outside the turrets, the domes and the centre gable, where
Palace's passing train runs behind the roof; the cells you walk through between Tokyo Tower's feet and under
Tsutenkaku's archway stay see-through. (The towers themselves are solid, as their drawings are: the game fades
them over the player, see `occlusion.md`.)

- **Tokyo Station's footprint** (issue #259): the sprite is 41x8 cells at Palace (7,2), but only its two
  pavilions (columns 10..14 and 40..44) and the entrance (26..28) come down into its bottom row, row 9; the
  wings end in row 8. So Palace's `Colliders` are solid over rows 2..8 and, in row 9, only under those and
  under the forecourt (the gardens, lamps and vending machine at columns 23..31, which show where the sprite
  is clear); the door is (27,9). The rest of row 9 is paving the player walks on, drawn in front of the
  sprite (a character in its bottom row sorts past its feet). The whole rectangle used to be solid, and a
  player walking north stopped a cell and a half short of a wing with nothing in the way. Row 8 stays solid
  though the foot of it is paving: someone standing there would be drawn under the wall. A redrawn station keeps
  this ground line (#70) or moves the colliders with it: `map-data.test.js` fails on a solid bottom-row cell
  with nothing standing on it and on an open cell under the art.
- **Osaka** (`tools/generate_osaka.py`, 50x46) is a generated town reached by train, and the town of the
  stitched city `KansaiCity` (see "Kansai": Himeji is walked to from its west edge, Okayama from Himeji's, and
  Nara from its east edge):
  station house -> arch over the main street -> the canal bridge -> Canal-side Avenue -> Tsutenkaku on its
  plaza, with the ferris wheel on the north bank (a gondola at its foot is boarded for one turn and the view:
  see "A turn on the Dotonbori wheel", issue #242). The Dotonbori canal (rows 20-22) runs the whole width of
  the map under the bridge and carries the ambient boats (issue #61, see Ambient Traffic); the main street
  and the avenue are its asphalt roads (issues #106 / #151, see Street accessories) and the discount store by the arch opens into `DonTakoteOsaka` (issue #91, see Shop). The tower stands on the street's axis, so a shrub garden fills the ground behind
  it and the street forks round at the avenue (otherwise the player walks hidden behind the sprite for ten cells); the
  platform-edge fence and the continuous border hedges keep the player off the ballast and out from behind
  the fences. `OsakaStation` is registered in `tools/generate_stations.py`
  (`STATIONS` / `TOWN_DOORS`) and so in config `stations`; in `devhouse.world` Osaka sits where
  `tools/kansai.py` puts it, with Himeji against its west edge and Nara against its east edge (see "Kansai").
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
  `districts`; the HUD names the ROOM (`hudRoomName`), which for Tokyo's five rooms is the district.
- **Names are the redesign plan's, bounds are today's map.** A district the plan names that is not built yet
  has NO entry: Ueno and Shibuya (Park is one district, "Park", whose description says it stands in for both),
  Shirakawa-go's ryokan, Osaka's station front (a
  threshold, not a district). Add it in the change that builds it. San Franbourne (#218) was not on master when this landed: give it districts when it is.

| Room (key) | Districts today |
|---|---|
| Tokyo | Imperial Palace |
| Market | Asakusa |
| Palace | Marunouchi |
| Park | Park |
| Shinjuku | Shinjuku |
| Sapporo | Sapporo Station front, Clock Tower block, Odori Park, Tanukikoji |
| Asahikawa | Station front and Heiwa-dori, Ramen alley, Asahibashi and the riverbank |
| Osaka | Dotonbori, Shinsekai |
| Himeji | Himeji Castle, Koko-en garden |
| Okayama | Okayama Castle, Momotaro Avenue, Korakuen garden |
| Nara | Todaiji, Nara Park, Kasuga Taisha |
| Sendai | Sendai Station front, Aoba Castle ruins, Downtown, Zuihoden, Nikka distillery, Samurai quarter, Matsushima bay |
| Fukuoka | Hakata Station, Momochi, Canal City, Old Hakata, Nakasu, Dazaifu |
| Kanazawa | Station front, Higashi Chaya and the temple hill, Katamachi, Castle, Kenrokuen, Nagamachi |
| Shirakawago | Far bank and bridge, Village, Viewpoint |
| Toyama | Iwase port, Tram street |

- **Tokyo's display names**: the room keys are unchanged; see `name` in `maps-and-rooms.md`.
- **Shinjuku** is a room and a district of one name: "Shinjuku, Tokyo's street of high-rises" below.
- **Is a city its own?** `tools/check_distinct.py` (`generators-and-checks.md`) measures how much art each
  city shares with the others; a rebuild must not make a city worse.

### Shinjuku, Tokyo's street of high-rises (issue #94)

Market and Palace are ported maps with no free street front, so two towers were all either could take. The
street of high-rises is a district of its own, `Shinjuku` (34x36), in what was wood west of the west road of
Palace and Park, and the fifth district of the stitched Tokyo ("Shinjuku is the fifth district" in
`stitched-city.md`: where it sits, its seam with Palace, `?stitch=0`). It is generated:
`tools/generate_shinjuku.py` (on `hokuriku.Kit`, in `check_generators.py`), then
`tools/generate_houses.py --lobbies Shinjuku`. No art of its own and no palette entry: every sprite is the
city kit's. Tokyo, Market, Palace and Park lose no tile to it.

- **The avenue** is rows 14-16, the road between Palace and Park carried on west over the west road (the
  T-junction there is a crossroads now). It runs from column 4 to the west road, a pavement two cells deep either side,
  a zebra crossing on columns 22-23 under two signals (`traffic-light` stamped at `(21,11)`, its foot on the
  north pavement, and at `(24,15)`, its foot on the south one; `TrafficLights` runs them like any other), and it ends at column 4 in a
  capped turning box with a bus bay (`bus-stop` at `(4,17)`): a road that leaves a junction leads
  somewhere (#240).
- **Nine towers, every one with a lobby** (see Tower lobbies). Five stand on row 11 along the north
  pavement: flats `(4,4)`, the glass tower `(10,2)`, the blue office block `(15,1)`, the ochre one
  `(21,4)`, the lower flats `(26,6)`. Four stand on row 29 in the south block, facing a promenade (rows
  30-32) that the pavement reaches down both sides of the block: the blue block `(5,19)`, the glass tower
  `(12,20)`, flats `(18,22)`, the ochre block `(25,22)`. Two vending machines (`(9,10)`, `(14,10)`) and a
  utility pole stand between the northern towers; the rest is wood. No rubbish bins.
- **The district** (`districts.py`) is "Shinjuku", bounds `(2,2)-(32,32)`, standing cell `(16,13)`; its one
  named spot is "the vending machines". The blog pipeline may place a Tokyo post there like in any district.
- **Is Tokyo still its own?** The towers are the kit's, which Osaka and Fukuoka also use, so Tokyo's numbers
  in `check_distinct.py` moved (buildings 0.16 to 0.19, own art 55% to 53%; it still passes all three
  targets) and its baseline entry records that (`generators-and-checks.md`).
- **Checks**: `tools/tests/shinjuku.test.js` (the district in the city, the kerb column, the crossing, the
  seam both ways, every tower's door and lobby, the walk in from the Palace/Park road, stitched and
  `--stitch=0`); `shinjuku-avenue` and `phone-landscape-avenue` in the browser regression.

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
  **pier** is flat (`Non-Collidables` + `depthBias: -200`, the `asahibashi-deck` recipe) and its five cells
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
  the **Glass Art Museum**, the **tram stop** and `toyama-tram-rail` (plain Floor tiles, not `train-track`: no
  ambient train). The **tram** is not a tile: it runs the rails end to end, stops under the shelter and can be
  ridden (the room's `tramways` entry, issue #245; see "Shuttles" in `ambient-traffic.md`).
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

### Kansai: Osaka, with Himeji, Okayama and Nara on foot (issues #255, #267, #268; #68, runs 2, 4 and 5)

Osaka, **Himeji**, **Okayama** and **Nara** are four generated rooms the game stitches into ONE walkable
room, **`KansaiCity`** - the third stitched city, built as Hokuriku is (above; `stitched-city.md`). Osaka is
the town and has the region's one station. Himeji, Okayama and Nara are small places with NO station: you
walk to Himeji from Osaka, west along Canal-side Avenue, and on along the same avenue to Okayama, where it
ends; and east along it the other way to Nara, where it ends below the Nandaimon. Devhouse 2's Damian was in
Okayama on 12 November 2025 (post 745), in Himeji on the 13th (post 754) and in Nara on the 14th (post 764).
All four are to be rebuilt to one plan: see "Kansai: one plan for Osaka, Himeji and Okayama" below.

- **Layout** (`tools/kansai.py`, the one place the generators agree on it; city cells, the union's top-left
  is 0,0). Kansai is planned as FIVE districts, one ticket each, and `AT` / `SIZE` hold all five so that a
  later ticket moves nothing: **Okayama** 44x40 at (0,36), **Himeji** 44x40 at (44,36), **Osaka** 50x46 at
  (88,30), Nara 52x40 at (138,36), LakeBiwa 46x36 at (152,0). **`BUILT`** names the ones that exist
  (`('Himeji', 'Nara', 'Okayama', 'Osaka')` today); config `cities.KansaiCity.rooms` is exactly those. A
  join (`JOINS`, four rows today) is open only when both its districts are built: a generator asks
  `ks.is_open(district, side)` and closes its edge otherwise, so Himeji's west edge opened when Okayama was
  built (`generate_himeji.py` keeps the closed branch), Osaka's west and east rail caps and seam pieces are
  there only because Himeji and Nara are, and **Nara's north edge is wood until Lake Biwa is built** (its row
  `('Nara', 'n', …, 'LakeBiwa', …)` is already in `JOINS`, inert until then; issue #269 opens it).
  **Okayama's own west edge has no join**, nor Nara's east and south ones: nothing is planned beyond them.
  The city today is 190x46 (`depthScale` 1): Himeji's, Okayama's and Nara's top row is six rows below
  Osaka's, and that gap is the stitcher's woodland (`cities.KansaiCity.backdrop`, a copy of Hokuriku's),
  which also carries Osaka's railway on west and east to the city's edges - the track runs two rows above
  Himeji's keep's roof, and above Nara on the bare strip the backdrop keeps clear of trees
  (`extendClear`), in view from the end of the towpath.
- **The seam**: Osaka's west edge meets Himeji's east edge. **Canal-side Avenue** (Osaka rows 24-28: a
  pavement, three rows of road, a pavement) is Himeji rows 18-22, and **Osaka's canal** (rows 20-22) runs on
  as the **castle moat** (Himeji rows 14-16): the same Floor and Water tiles either side of the edge, with
  `edge-n` / `edge-s` pavement pieces at the seam instead of the autotile's rounded corner. The five avenue
  cells each carry a hidden transporter landing three cells inside the neighbour (`kansai.seams`), which is
  what `?stitch=0` plays; they are the only open cells on the shared edge. A **fingerpost**
  (`kansai-fingerpost`, 1x2) stands beside the pavement on each side of the seam, and a bump reads it (one
  `flavour` row in `Interactions.js`).
- **The second seam** (issue #267): Himeji's west edge meets Okayama's east edge, and the avenue carries
  on, on the same rows either side (18-22), with the same seam pieces and five more hidden transporters each
  way (Himeji's ten are its east five, then its west five). Nothing else crosses it: the verges either side
  of the avenue are shrubs and wood. Its fingerposts are a second sprite key, **`okayama-fingerpost`** (the
  same drawing): a `flavour` rule is matched by sprite key alone, so one key cannot say two lines, and a
  key beginning `kansai-fingerpost` would be caught by the first rule. Himeji has one of each, by the seam
  it is for.
- **The third seam** (issue #268): Osaka's east edge meets Nara's west edge. The avenue carries on (Nara
  rows 18-22) and the canal runs on as Nara's **river** (rows 14-16), with the same seam pieces and five
  hidden transporters each way. Osaka's ten are its west five, then its east five: the row order of
  `JOINS`, which `generate_osaka.py` writes as it is (it does not call `kept_order`), so keep Osaka's west
  row first there. Its fingerposts are a third key, **`nara-fingerpost`**: Osaka (47,28), Nara (3,22).
- **Osaka** changed only at its two edges: no bushes cap the rail corridor on (0, 3..5) or (49, 3..5) - the
  line carries on west and east - the pavement's seam pieces on (0,24), (0,28), (49,24) and (49,28), the
  fingerposts at (2,28) and (47,28), and the ten seam transporters. A later Osaka must keep the avenue on
  rows 24-28 and the canal on rows 20-22 at both edges.
- **Himeji** (`tools/generate_himeji.py`): north, **Himeji Castle** on its hill - the white **keep**
  (`himeji-keep`, 10x8 at (8,0), on the district's top row, so its art is exactly its footprint: nothing may
  overhang into the row above, which is not Himeji's; `game.lookUp.sprites` has it, so the camera looks up
  from the terrace in front of it), a corner **turret**, and a gravel terrace with pines and stone lanterns.
  Two wall tiers hold the hill up (rows 10-13: the castle's own white plaster wall, `himeji-wall`, over a
  stone base) and the only way up is the **gatehouse** (`himeji-gate`, 6x4 at (30,10); the gateway is its
  columns 2-3): over the timber **bridge** across the moat (`himeji-bridge`, 2x4, flat with
  `depthBias: -200`), through the gateway, up the steps. The **moat** ends at a bank at column 6 and is
  Himeji's `waterways` entry, declared from column 7 (see "Boats" in `ambient-traffic.md`), so the canal's
  boats sail it; it is `pond-autotile`, so it can be fished. The avenue runs on out of the west edge to
  Okayama (it ended at the woods at column 5 until #267). South
  of it, **Koko-en**: a garden behind an earthen wall (Sendai's wall and pine sprites), entered through its
  roofed gate (`himeji-kokoen-gate`, 4x3 at (20,23); the gateway is its columns 1-2) - a gravel loop round a
  pond, crossed by the same timber bridge, with lanterns, pines and maples. There is no building with a
  door: the keep and the turret are solid over their whole footprint, and the keep is looked at, not entered.
- **Okayama** (`tools/generate_okayama.py`, issue #267) is laid out on one north-south axis, columns
  21-22: the keep, the steps down the stone wall, across the avenue, the bridge, the island. North,
  **Okayama Castle**, the black "crow castle" (`okayama-keep`, 8x7 at (18,2): black boarded walls with a
  white band under each eave, gold shachi on the ridge, a low stone base; solid over its whole
  footprint, roof rows too; `game.lookUp.sprites` has it), on a gravel terrace with pines and stone lanterns
  above a **stone wall** (rows 13-14) whose only way up is the steps on the axis. The avenue (rows 18-22)
  ends west in a paved **plaza** with the bronze **Momotaro** and his dog, monkey and pheasant
  (`okayama-momotaro`, 2x3 at (8,17)); a **stall of Bizen ware** (`okayama-bizen-stall`, 3x3 at (15,15))
  stands beside the pavement. South, **Korakuen** is an island (7..38, 27..35) in a **river**: a ring of
  solid `pond-autotile` (5..40, 24..37; it can be fished), crossed only by the steel **Tsukimi bridge**
  (`okayama-bridge`, 2x4 at (21,24), flat with `depthBias: -200`). The pond set has no inner-corner piece,
  so a heap of the rim's own stones (`okayama-bank-rock`, 2x2, flat) lies over each corner of the island,
  under a pine. On the island: a gravel loop round the lawns, a pond, maples and pines, lanterns and two
  red-crowned **cranes** (`okayama-crane`, 1x2). The statue, the stall and a crane each answer a bump
  (`flavour` rows). The river is NOT a `waterways` run: no arm of the ring leads anywhere, so a boat would
  fade in and out in full view. There is no building with a door and no ordinary sealed building: the keep
  is looked at, not entered, and the stall is an open counter. The west, north and south edges are wood.
- **Nara** (`tools/generate_nara.py`, issue #268, 52x40). **Todaiji** stands on one north-south axis,
  columns 36-37: the **Great Buddha Hall** (`nara-daibutsuden`, 12x8 at (31,2): two broad hipped roofs, the
  gold horns on the ridge, white plaster between dark posts, the curved gable over the middle doors; solid
  over its whole footprint, roof rows too, with wood on rows 0-1 behind it; `game.lookUp.sprites` has it, so
  the camera looks up from the court) over its gravel **court**, behind an earthen wall (rows 14-15,
  Sendai's) crossed only through the **Nandaimon** (`nara-nandaimon`, 6x4 at (34,12); the gateway is its
  columns 2-3, walked under like Koko-en's gate). The avenue in from Osaka ends below it in a paved **plaza**
  with a **deer cracker stall** (`nara-senbei-stall`, 2x2 at (41,16)). West, Osaka's canal runs on as a
  **river** (rows 14-16) that bends north up columns 20-22, with a gravel **towpath** (23-24) beside it; both
  stop at row 2 until Lake Biwa joins there (the river's closed head is `edge-n` and a `corner-ne`, with an
  `okayama-bank-rock` over its west corner and another over the inside of the bend: no `corner-nw`, which
  the blog pipeline would read as "the pond"). The river is Nara's `waterways` entry as far as the bend
  (columns 0-19), so the canal's boats sail on into it and fade out where it turns north. South, **Nara
  Park**'s lawn with maples and pines, and **deer** on the lawn, the court and the plaza: the two resting
  ones of the UrbanAccessoriesv2 sheet (`nara-deer-doe`, `nara-deer-stag`) and a drawn bowing one
  (`nara-deer-bow`), all 1x1 and solid. South-east, **Kasuga Taisha**: through a vermilion torii
  (`nara-kasuga-torii`, 4x4 at (31,24), its own art and not the kit's `torii-red`, which made Kansai worse
  than its distinctness baseline), up a gravel approach lined with **stone lanterns** (`nara-stone-lantern`,
  1x2, nineteen) round a cedar wood, to the stock `shrine-red` at (42,24), whose door (44,30) leads into its
  worship hall `ShrineNara1`, named "Kasuga Taisha" (`generate_shrines.py` `NAMES`). The nineteenth
  lantern, at the plaza's south-east corner, closes the one cell behind the shrine's roof (42,24). The
  lanterns are unlit at night, like Sendai's (`DayNight.js` halos `-lanterns`, not `-lantern`: keep the key
  singular). Every Nara sprite answers a bump (`flavour` rows). No station, no railway, no bin, no building
  with a door but the shrine. The east and south edges are wood, and the north edge until Lake Biwa.
- **The Map** has a dot each for Himeji, Okayama and Nara (`config.places.Himeji` / `.Okayama` / `.Nara`,
  `"minor": true`: a small place, whose label gives way to the towns' - `hud-input-touch.md`). Nara's geo is
  Todaiji's, so its dot touches Osaka's (`Places.order`). Debug map-click travel lands on Himeji (40,18), on
  the avenue three cells in from Osaka, on Okayama (40,18), three cells in from Himeji, and on Nara (3,18),
  three cells in from Osaka's east end (`Places.arrival`).
- **Districts and the blog pipeline**: `districts.py` has `castle` and `kokoen`; `LANDMARKS` has `Himeji
  Castle` (the visitor stands at (12,8), on the terrace in front of the keep's middle, where the camera
  looks up) and `Koko-en garden`, both `rooms:`-scoped. "the pond" is a spot of Koko-en, not of the castle:
  the moat's bank tile is the same `pond-autotile_corner-nw` the pond's label looks for, and the garden's is
  found first (`kansai.test.js` holds it there). Damian's 13 November placement was re-homed from Osaka with
  `blog_to_npc.py --rehome Damian 2025-11-13 "Himeji · Himeji Castle"` (see `blog-pipeline.md`).
  Okayama has `castle`, `momotaro` (the avenue and the plaza) and `korakuen`, and four `rooms:`-scoped
  `LANDMARKS` rows: `Okayama Castle` (the visitor stands at (20,9), in front of the keep and off the steps'
  columns), `Korakuen garden` (anchored on the first crane: (27,31), the lawn beside it), `the Momotaro
  statue` (8,20) and `the Bizen-ware stall` (16,18). "the pond" is a spot of Korakuen for the same reason
  it is Koko-en's: the label's tile is found in `"x,y"` string order, and the garden pond's `"14,31"` sorts
  before the river's corner `"5,24"` - keep the garden pond's first column between 10 and 43. Damian's 12
  November placement was re-homed from Hakata's platform with
  `blog_to_npc.py --rehome Damian 2025-11-12 "Okayama · Korakuen garden"`.
  Nara has `todaiji` (the hall, the court and the plaza), `nara-park` (the lawn, the river and the towpath)
  and `kasuga`, and five `rooms:`-scoped `LANDMARKS` rows: `the Great Buddha Hall` (35,10), in front of the
  hall and off the axis; `the Nandaimon gate` (35,16), the plaza below its west post; `the deer cracker
  stall` (41,18); `the deer of Nara Park` (anchored on the first stag in `"x,y"` order, (12,29): the lawn
  beside it, (13,29)); and `Kasuga Taisha` (45,32), the approach east of the door's column (the generic
  `the shrine` is there too). Damian's 14 November placement was re-homed from Osaka's canal bank with
  `blog_to_npc.py --rehome Damian 2025-11-14 "Nara · the Great Buddha Hall"`. No start room changed.
- **Build order** (art tools with a Pillow python): `extract_street.py` (the deer), `generate_kansai_art.py`,
  `make_prefabs.py`, `generate_okayama.py`, `generate_himeji.py`, `generate_nara.py`, `generate_osaka.py`,
  `generate_shrines.py Nara`, the maps in `../devhouse.world` (as `kansai.AT` places them: the city's (0,0)
  is world cell (-258,31), which is Okayama's corner now) and `config cities.KansaiCity`, `sync_cities.py`,
  `districts.py`, `config_to_tiled.py Osaka Himeji Okayama Nara ShrineNara1`, `play.js lint` for `Osaka`,
  `Himeji`, `Okayama`, `Nara`, `ShrineNara1` and `KansaiCity`,
  `make_worldmap.py`, `check_distinct.py` (its row is `Kansai`). A ticket that builds the next district
  adds its generator, adds the district to `BUILT` and to `cities.KansaiCity.rooms`, re-runs the neighbours'
  generators (their edge opens) and drops its stub from `japan-map.test.js`. In `devhouse.world` the five
  rectangles are x -258..-60, y 31..107 in world cells: south-west of Hokuriku, with Fukuoka moved west and
  south to (-330,90) to stay clear and stay the westernmost map. `kansai.test.js` checks that nothing else
  stands in any of the five.

### Kansai: one plan for Osaka, Himeji and Okayama (issue #273; the plan #274, built by #275, #276, #277)

**This is a plan, not what is built**: the section above describes the rooms as they are. Each of the three
tickets rebuilds one room to this plan, rewrites that room's bullet above, and deletes its part here.
**Fixed** means a ticket may not move it. A **target** is the cell the plan was drawn with: the ticket's own
design may shift it by blockout, but not change what it is or which side of what it stands on.

- **What repeats today.** Himeji and Okayama are the same room twice:
  1. *The same three bands on the same rows of a 44x40 room*: castle north (Himeji rows 0-13, Okayama
     3-14), the avenue straight through on rows 18-22, a garden south (rows 24-37).
  2. *The same castle*: a salmon `gravel-autotile` terrace as wide as the room (Himeji 6..41, Okayama
     13..40) above a retaining wall along its whole south side, with one two-column way up (the gateway on
     32-33, the steps on 21-22), four `sendai-pine` and two or three `sendai-stone-lantern` on the gravel,
     and a frontal grey-roofed keep on a stone base at the top with its visitor in front.
  3. *The same garden*: a rectangle entered on columns 21-22 in both (Koko-en's gate, the Tsukimi bridge)
     with lanterns flanking the entry, a rectangular two-cell gravel loop (8..38 x 27..35 and 9..36 x
     28..34) round a lawn with a two-row `b.pond`, three maples and some pines. Both gardens' district
     `stand` is (22,28).
  4. *The same water*: a three-row rock-rimmed `pond-autotile` band crossed north-south by one 2x4 deck.
  5. *The same edges*: the same `AUTUMN` list (`sendai-maple`, `-pine`, `-cedar`) as solid wood all round.
  6. *The same arrival*: in from the east on rows 18-22 along an empty three-lane road, a wall behind a
     verge to the north, the garden's boundary to the south, a fingerpost with its feet on (39,23).

  Osaka shares nothing with them and has little of its own: three generic towers, two generic houses and
  a house for a station on grey brick, and the same road.
- **The idea: one walk west along one road, from the city to where the road ends.** Each thing the three
  share changes role from district to district, so no two use it the same way:

  | | Osaka: the city on the canal | Himeji: the castle on its hill | Okayama: the garden in the river |
  |---|---|---|---|
  | You | browse | climb | stroll |
  | Shape | east-west strata crossed by one north-south street | a hairpin of walled courts north, a row of walled garden rooms south; everything square and enclosed | two banks of a river that bends; nothing on an axis, nothing walled |
  | The road | a city avenue: lights, a crossing, fronts and signs | a quiet road under the castle wall, passing through | stops at the river after ten cells |
  | Water | a straight canal between quays, with boats | the canal's west end as the moat, rock-rimmed under a white wall; the same boats | an open river, off the map by two edges; a garden pond |
  | Ground | paved edge to edge: grey brick, boardwalk, retro paving; no lawn | swept `sand-autotile` courts; lawn only inside Koko-en | lawn; `gravel-autotile` only as paths |
  | Skyline | towers and signs: Tsutenkaku, the wheel, sign towers | one white keep on the top row, one turret | low: trees, a mound, the black keep down at the water |
  | Trees | none but the tower's garden | pines; maples only inside Koko-en | maples and cedars; a pine only as a specimen |
  | Its own art | `osaka-*` (#219) | `himeji-*` | `okayama-*` |

- **Fixed for all three tickets.**
  - `tools/kansai.py` is not edited: `AT`, `SIZE`, the avenue and water rows, `JOINS` and `seams()` stay.
    (#268 and #269 edit it to add their districts.)
  - The seams, and the two columns inside each (x 0-1, x W-2..W-1), which hold only the avenue, water, a
    verge and wood or hedge:

    | Edge | Avenue (pavement, three road rows, pavement) | Water |
    |---|---|---|
    | Okayama x=43 = Himeji x=0 | rows 18-22 both | none |
    | Himeji x=43 = Osaka x=0 | Himeji 18-22 = Osaka 24-28 | Himeji 14-16 = Osaka 20-22, one `waterways` run |
    | Osaka x=49 (= Nara x=0, #268) | Osaka 24-28 | Osaka 20-22 |

    with `edge-n` / `edge-s` pavement pieces on the edge cells and the five hidden transporters each way.
  - The fingerposts, by the cell each is stamped at (1x2, feet one row below): Osaka (2,28); Himeji
    (39,22) and (4,22); Okayama (39,22). `Places.arrival` for Himeji and Okayama stays (40,18).
  - Himeji and Okayama have no station, no `train-track*` tile, no door and no ordinary sealed building.
    No bins. Real places only.
  - "the pond" stays a spot of the garden in both: the first `pond-autotile_corner-nw` in `"x,y"` string
    order must be the garden pond's.
  - `check_distinct.py`: no ticket leaves Kansai worse than `tools/distinct_baseline.json`. It is "most
    like Sendai" through the `sendai-*` trees, lantern and wall: no ticket adds another `sendai-*` kind.

- **Himeji (#275): a climb.** The castle is the district, and you earn the keep.
  - *Fixed*: the keep `himeji-keep` 10x8 at (8,0) and its visitor's cell (12,8); the moat on rows 14-16
    from its bank at x=6 to x=43 with its `waterways` entry from 7; the avenue on rows 18-22 across the
    whole room.
  - *North of the moat, three courts walked as a hairpin* (targets): over the bridge (columns 32-33) and
    through the gatehouse (6x4 at (30,10)) in the white wall on its stone base (rows 10-13, x 6..41) into
    **Sannomaru** (23..41, 6..9); east to steps (38-39) up an inner stone wall (rows 4-5, x 20..41); back
    west along the **upper walk** (18..41, 2..3); down the lane by the keep's east flank (18..19, 2..7)
    into **Honmaru** (6..19, 8..9), in front of the keep. The turret (3x4, solid) stands on (20,6) and
    closes Honmaru from Sannomaru, so the hairpin is the only way. About 50 cells from the bridge to the
    visitor, where it is 28 today.
  - *South of the avenue, Koko-en as three walled rooms in a row* (targets), not a loop: the earthen wall
    on row 24; the roofed gate 4x3 at (8,23), gateway columns 9-10, at the Okayama end; rooms A (7..16), B
    (19..30) and C (33..40) on rows 26-37, parted by solid tree lines two cells thick with one opening
    each, staggered (A-B on rows 28-29, B-C on rows 34-35) so the walk is a zigzag. B is the lord's garden
    with the koi pond (21..28, 30..32) under the timber bridge; A is pines and lanterns; C is maples.
    Paths are one cell of `k.paved`, not gravel.
  - *Ground and trees*: `sand-autotile` for all three courts; no `gravel-autotile` in Himeji. (The sand
    is Fukuoka's beach, from `generate_fukuoka_art.py`. If `check_distinct.py` counts that against
    Kansai, #275 recolours a court family of its own in `generate_kansai_art.py`.) Pines north of the
    avenue and in the border woods (pine and cedar); maples only in Koko-en.
  - *On arrival from Osaka* the canal becomes the moat beside the road and the white wall rises behind it;
    the bridge and gate are eight cells in, and the keep is not seen until the upper walk. *From Okayama*
    the Koko-en gate comes first, and the keep is overhead behind a wall with no way in until the far end.
- **Okayama (#276): a stroll.** The garden is the district; the keep is scenery, and the road ends.
  - *Fixed*: the avenue's cells at the seam; Momotaro, the Bizen-ware stall and two cranes stay in the
    room; Damian's post of 12 November stays in Korakuen beside the first crane (cells under "Posts").
  - *The river* (targets) is a bend of `pond-autotile`, solid: an east-west reach on rows 19-21 from the
    west edge to x=32 - the avenue's three road rows carried on as water - turning south as a reach on
    columns 29-32 to the bottom edge. It leaves by the city's own west and south edges only. The pond set
    has no inner-corner piece, so a heap of `okayama-bank-rock` covers the one inner corner, at the
    garden's north-east tip (28,22). It is not a `waterways` run.
  - *East bank* (targets): the avenue (34..43, 18..22; road from x=38, capped west) ends in the **plaza**
    (34..40, 14..23) on the outside of the bend, water ahead and to the south-west: Momotaro 2x3 at
    (35,16), the stall 3x3 at (37,14).
  - *North bank* (targets): west from the plaza along a small gravel **court** (22..33, 14..18) to the
    **keep** `okayama-keep` 8x7 at (14,12), its stone base on the bank (foot row 18) with no terrace in
    front and no wall across the room. The `Okayama Castle` visitor stands on the court beside it.
  - *The Tsukimi bridge* (`okayama-bridge`, 2x4 as drawn) at (22,19), beside the keep, is the only way
    into the garden, as it is in Okayama: plaza, court, keep, bridge, garden.
  - *Korakuen* (targets) is the inside of the bend (3..27, 22..37): open lawn to walk on, one cranked
    gravel path from the bridge's landing to the pond, the pond (6..13, 32..35), a mound (Yuishinzan, new
    art, about 5x4 at (4,25)), the cranes' feet on (14,27) and (16,28). From its north bank (row 22, x
    14..21) the keep is four cells north across the water, inside the look-up's fade (`lookUp.cells` 3,
    `fade` 3): the garden borrows the castle. #276 measures that in a browser at desktop and phone size.
  - *On arrival* the road runs through wood for a few cells and stops at a small plaza on the water: the
    statue, the stall, the river ahead, the keep low on the far side of the court, the lawn over the bend.
- **Osaka (#277): a browse.** `docs/workshop/219-city-redesign-plan-from-the-210-audit-ne.md`, "Stage E -
  Osaka", with its fixed cells, row bands for rows 0-22, interiors, labels and tests, and three amendments:
  1. **The avenue stays**: rows 24-28 from edge to edge (pavement, three road rows, pavement), open at
     x=0 and, once Nara is built, at x=49. Stage E's "the border closes the old avenue's ends" and "no
     road tile, traffic light" do not apply to it. The north-south main street (columns 23-26) does lose
     its asphalt, and meets the avenue at one crossing with the lights.
  2. **South of the canal**: row 23 is a one-row south quay of boardwalk. Stage E's south-bank row of
     fronts (rows 25-30) has no site. Shinsekai is rows 29-44 on `osaka-retro-paving-autotile`: the
     Shinsekai arch over the street south of the avenue, one row of fronts either side of the tower, the
     plaza on rows 38-43. #277's design picks which south-side sprites fit; the rest stay unplaced.
  3. **The canal** keeps rows 20-22 as water to both edges (`from 0` to `W-1`) and is `pond-autotile` on
     its edge cells, as the seam test asks.

  *On arrival* by train: out under the station's glass roof, the arch ahead down a street of fronts, the
  wheel to the north-east, then boardwalk, canal and bridge. *From Himeji*: the hedge opens onto the quay
  to the north and Shinsekai's fronts to the south, with Tsutenkaku ahead.
- **Along the seams.** *Osaka-Himeji*: the road and the water cross unchanged and everything else turns
  over within two columns - quay to rock rim, fronts to a white wall, paving to verge; the railway carries
  on west in the backdrop above Himeji, which has no track. *Himeji-Okayama*: only the road crosses, wood
  either side; west of it the road has ten cells left. *Osaka's east edge* is Nara's (#268): the avenue
  and the canal on their rows and nothing else.
- **Posts.** Every dated post keeps its room and its label. One changes cell:

  | Post | Today | After |
  |---|---|---|
  | Himeji: Damian 13 Nov (754), `Himeji Castle` | (12,8) | unchanged (fixed) |
  | Okayama: Damian 12 Nov (745), `Korakuen garden` | (27,31), beside the first crane (28,31) | **(13,27)**, beside the first crane (14,27): #276 re-runs `blog_to_npc.py --rehome Damian 2025-11-12 "Okayama · Korakuen garden"` and moves the pins in `test_blog_to_npc.py` and `kansai.test.js` |
  | Osaka: 568, 615 (Dylan) and 764 (Damian) at the wheel (39,19); 768 (Damian) at the arch (21,18); 769 (Bailey) at Tsutenkaku (26,43); 636 (Dylan) at the platform's vending machines (14,6) | | unchanged (Stage E's fixed cells) |
  | Osaka: 590 (Dylan) (17,35); 681 (Dylan) (30,17) | under a sakura; the crab house's door front | re-homed by #277 as Stage E says: `Osaka · the Dotonbori boat pier`, `Osaka · Dotonbori (area)` |

  A stand-in that #268 or #269 has moved out of Osaka by then is no longer Osaka's.
- **Build order and rooms.** One at a time, because map data is serial; each leaves the city walkable end
  to end and the checks green.
  1. **#275 Himeji** - room `Himeji` only. Okayama is still the old room beside it.
  2. **#276 Okayama**, after #275 is merged - room `Okayama` only.
  3. **#277 Osaka**, after both - room `Osaka` and its interiors (`LobbyOsaka1` kept, `LobbyOsaka2`,
     `LobbyOsaka3`, `HouseOsaka1`, `HouseOsaka2` pruned, the shop rooms Stage E adds; the doors of
     `OsakaStation`, `DonTakoteOsaka` and `DevhouseOsaka1F` keep their cells). **Not while #268 (Nara) is
     being built**: both rebuild `Osaka`. Whichever is second runs `generate_osaka.py` on the other's.

  Each ticket: its generator, `config.json` (`rooms.<Room>`, its `districts`), its `LANDMARKS` rows,
  `tiled/<Room>.tmj`, its tests in `kansai.test.js` (for Osaka, the files Stage E lists),
  `make_worldmap.py --pil`, `check_distinct.py`. Sizes and slots do not change, so `devhouse.world` and
  `cities.KansaiCity` should not: `sync_cities.py --check` says.
- **Later districts.** A castle added to the region later (Hikone, #269) says in its design how its
  ground, its approach and its water differ from Himeji's hairpin and Okayama's riverbank. The terrace
  above a full-width wall with one stair is not used again.

### Karuizawa: out of Tokyo's west gate, on foot (issues #68, #256; parts #260, #261, #262, #263)

The mountain resort devhouse 2's Damian and Julia went to on 1-2 November 2025. A small place with NO
station, walked to from its town like Shirakawa-go and Toyama: it is the **fifth district of `TokyoCity`**, a
48x40 generated room (`tools/generate_karuizawa.py`, art from `tools/generate_karuizawa_art.py`) at world cell
`(-48, 8)`, west of the `Tokyo` room, entered through Tokyo's west gate (see The west gate in
`stitched-city.md`: the same generator reopens it).

- **What is there now** (part 1: the room and the gate; part 2: the Ginza; room cells): the gate on the east edge, `(47, 34..35)`,
  on Tokyo's own brick; a two-cell packed-dirt road (`dirt-outside-autotile`) west from it along rows 34-35 to
  column 14, then north up columns 14-15 to row 10 (the bay at its head is below). The **fingerpost**
  (`karuizawa-fingerpost_0_0`, 1x2) stands on the verge inside the gate, foot at `(44, 33)`, beside the cell
  the gate lands you on with `?stitch=0`; bumping it reads which way is Tokyo and which Karuizawa
  (`Interactions.js`, kind `fingerpost`).
- **Kyu-Karuizawa Ginza** (part 2, issue #261): three shopfronts side by side on the north side of the road
  in, where it turns north, each 3x4 with its top-left on row 29 and its door in the middle of its bottom
  row. Every shopfront in the game has its door in its bottom row, so they face south onto the road in, not
  onto the leg north; the dirt is one row wider there, `(16..28, 33)`, to meet the doors. The gaps between
  them, `(20 | 24, 29..32)`, are solid. Each door leads into a shop floor (see Shop floors:
  `generate_houses.py --shops Karuizawa`, which opens the doors the town generator places sealed):

  | front (`karuizawa-shop-*_0_0`) | at | door | room | name | `shopMenu` |
  |---|---|---|---|---|---|
  | `bakery`: a half-timbered boulangerie under a steep red-brown gable | `(17, 29)` | `(18, 32)` | `ShopKaruizawa1` | `Bakery · Karuizawa` | `bakery` |
  | `jam`: the jam and souvenir shop, white clapboard under a green roof | `(21, 29)` | `(22, 32)` | `ShopKaruizawa2` | `Souvenirs · Karuizawa` | `souvenirs` |
  | `lounge`: the cocktail lounge, dark boards over a stone dado | `(25, 29)` | `(26, 32)` | `ShopKaruizawa3` | `Lounge · Karuizawa` | `lounge` |

  The lounge's list is its own row of `Shop.VENUES` (LOUNGE: Highball, Vodka Redbull, Nama Beer; see Shop).
  Each front's lit window and door are glow spots in its `spriteMetadata` (`GLOW` in the art tool), so the
  street is lit at night. Nothing else is built: no sealed ordinary building, no bin. Keep the doors and the
  cells in front of them, `(18 | 22 | 26, 32..33)`, free of NPCs and blog spots: somebody standing there
  seals that shop on the next `generate_houses.py` run (`tools/tests/karuizawa.test.js` holds it). Moving
  the Ginza is `GINZA_Y`, the three columns of `GINZA` and the widened-dirt rectangle in the generator.
- **The head of the road** (#262), what the two of them came for:
  - **Shiraito Falls**: one static 8x3 sprite, `karuizawa-falls_0_0`, at `(12..19, 3..5)`, set into the north
    wood and solid all over. The two end cells of its bottom row, `(12, 5)` and `(19, 5)`, are rock arms on
    the bank: bump one (from `(12, 6)` or `(11, 5)`) for its line (kind `waterfall`).
  - **The pool**: the shared `pond-autotile` on the Water layer, `(13..18, 5..7)`, its top row under the
    falls. It has **no north rim on purpose** (`edge-w` / `center` / `edge-e` where a rim would be): the
    rim's white rocks would show through the falling water, and with no `pond-autotile_corner-nw` tile the
    pipeline's generic `the pond` spot is not added beside `Shiraito Falls`. Bumping it fishes, as any pond
    does. No cell that is both pool and falls has an open cell beside it, so no bump both fishes and talks.
  - **The bay**: packed dirt, `(11..20, 9..10)`, where the bus turns round; the shared **bus stop**
    (`bus-stop_0_0`, the one eleven other rooms have; no line, as in every town) at `(18, 8)` above it.
  - **The corn stall**: `karuizawa-corn-stall_0_0`, 3x2 at `(19..21, 6..7)`, a prop with a line (kind
    `corn-stall`), not a shop: its counter is row 7, bumped from row 8.
  - Open ground: `(10..11, 5)`, `(10..12, 6..7)`, row 8 but for the stop, and rows 9..11 of columns 10..21.
- **The woods** are solid everywhere else, so the gate cells are the only open cells on the room's edge.
  They are `karuizawa-larch`, a November larch drawn as a 2x3 (`_0_0`) and a 2x4 (`_0_1`) sprite of one
  family (prefabs `karuizawa-larch`, `karuizawa-larch-tall`; `Kit.TALL` in `tools/hokuriku.py`), so the wood
  has a skyline. No sprite in the room is one other town's: its Collidables are `karuizawa-*`, the common
  shrub and the common bus stop (`karuizawa.test.js`).
- **No track.** The room has no `train-track*` tile and must not get one: the city's ambient train runs on
  the topmost track row of the whole stitched room, and the Palace line's cutting passes under Karuizawa
  three rows south of its last row.
- **The Map**: `places.Karuizawa` (`geo [138.63, 36.35]`, `"minor": true`) is the first small place: a dot of
  its own north-west of Tokyo's, its label laid out after the towns' (`Places.layout`). A room that is its
  own place wins over the city it is stitched into, so the gold ring moves from Tokyo's dot to Karuizawa's
  as you walk through the gate. Debug map-click travel lands inside the gate, Karuizawa `(44, 34)`
  (`Places.arrival`). In the studio the city stays at Tokyo's own dot (`WorldModel.geoOf`).
- **Blog pipeline**: one district, `larch-road` (`tools/districts.py`), and three named spots, each
  `rooms:`-scoped in `LANDMARKS` (`tools/blog_to_npc.py`): `Shiraito Falls` (`(13, 8)`, the bank at the
  pool's south-west corner), `the corn stall` (`(21, 8)`, the east end of its counter) and `the road from
  Tokyo` (beside the fingerpost).
- **The two posts told here** (part 4, issue #263; moved with `--rehome`, see Re-homing a placement in
  `blog-pipeline.md`): Damian's day at the falls (post 544, 1 November 2025) stands at `Shiraito Falls`,
  `(13, 8)`, and Julia's corn from the bus stop vendor (572, 2 November) at `the corn stall`, `(21, 8)`;
  both had been on Tokyo Station's platform, which now says absent on those days. Each is there for the
  one day (the next post puts Damian in Toyama on the 2nd and Julia there on the 3rd), so the room is empty
  on every other date. On those two days Karuizawa's dot on the Map is the friends' dot and its label is laid
  out with the towns' (not for the one being played); on a wide view it stands beside its dot, and on a
  portrait phone it can still stand off on a leader line, as any label there (`japan-map.test.js`).
  **Bailey starts 2 November here**, at `(19, 10)` in the bay two cells from Julia: the three friends are
  one to a room that day (Julia here, Dylan in Osaka, Damian in Toyama) and Karuizawa is one room from home
  (Where the player starts in `trips-and-dates.md`). `karuizawa.test.js` pins the placements, the walk
  from the gate to each and that start.
- **Build order**: `generate_karuizawa_art.py`, `make_prefabs.py` (the larches, the falls and the stall are
  stamped), `generate_karuizawa.py`,
  `generate_houses.py --shops Karuizawa`, `districts.py`,
  `config_to_tiled.py Karuizawa Tokyo ShopKaruizawa1 ShopKaruizawa2 ShopKaruizawa3`, `sync_cities.py`,
  `make_worldmap.py`, then `play.js lint Karuizawa Tokyo TokyoCity ShopKaruizawa1 ShopKaruizawa2
  ShopKaruizawa3`. Both tools are in `check_generators.py`, and so is `generate_houses.py`, which rebuilds
  the three shop floors.

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
  The gate and the shops' windows glow at night (`Glows.SPRITES`). **Susukino** (stage 4, the neon crossing,
  south of the arcade's back row; the room grew eight rows south for it, 56x43 to 56x51, and its
  `devhouse.world` slot grew northward) stands on dark wet asphalt with the neon lying in it
  (`susukino-asphalt-autotile`, its alone): one east-west tram street (rows 47-49) with the streetcar's rails
  down its middle (`tram-rail-h` on row 48, `tram-rail-cross` where the three north-south streets, which now run
  down to it, meet it). Everything stands with its feet on row 46 and faces the tram street; the strip behind
  (row 43 up to the arcade's back wall) is closed. East of the station avenue, on its corner, the **neon
  building** with the fox board (`susukino-neon-corner` at (33,40), door (35,46): a lobby, `LobbySapporo3`) and
  the **karaoke bar** (`susukino-karaoke` at (39,42), door (40,46): a shop floor, `ShopSapporo4`, whose counter
  is a bar), a pole of neon signs (`susukino-neon-lanterns`) after each. West of it the **ramen alley**: three
  counters under noren (`susukino-ramen-stall-a` / `-b` at columns 18, 21 and 24, feet on row 44) against the
  arcade's back wall, the alley itself one row (45) behind a ploughed bank with lantern posts
  (`ramen-alley-lanterns`), entered under the ramen gate (`susukino-ramen-gate` at (27,44)) from the street. A
  bump on a counter opens its list (RAMEN ALLEY, `Shop.VENUES.ramen`); nothing in Susukino is sealed. The
  **streetcar** is declared, not placed (`rooms.Sapporo.tramways`, run by `src/AmbientTrams.js`, see Ambient
  Traffic): in from off the map along row 48, a stop at column 23 outside the alley (a strip of platform, a
  bench and the stop sign on the south kerb), out the other side, and back mirrored; overhead-wire poles
  (`tram-pole`) stand along the south kerb. The two ends of the new rows (west of column 14, east of column 46)
  are snow under trees behind a bank with a way through; the south kerb (row 50) is fenced. The fox board, the
  karaoke front and the ramen gate glow at night (`Glows.SPRITES`). The two corners beside the arcade (rows
  34-42) are still snow and trees, fenced along row 42. The west row is closed by a shrub in each gap and a hedge behind it; the
  station front, the government hall and the office blocks collide up to their roof lines (nothing of the
  station is walk-behind; of an office block only its top row), and both towers collide along their
  silhouettes (see their prefab comments): the Clock
  Tower is solid up to its pyramid roof (only the roof tip is walk-behind) and the TV Tower up to the top
  of its lattice (only the thin mast is), so the tower's shaft closes Kita-Odori's roadway at columns
  49-50 and you pass it on the north pavement. Nobody is fully hidden behind either landmark (on the pavement at (49-50,19) the foot of the mast covers half the player).
- **Asahikawa** (`tools/generate_asahikawa.py`, 42x32) is the small day-trip town, rebuilt from its own art
  (issue #219, stage B; `tools/generate_asahikawa_art.py`): a small cold river city of timber and glass.
  - **The station** is `asahikawa-station-front` (10x5 at (28,5)) on the old station house's door cell: its two
    door cells (32,9) and (33,9) lead into `AsahikawaStation`, whose mats still put you on (32,10). The platform
    strip is gone; the rail corridor is fenced off (the row-6 fence runs only where no building's top row
    stands on it).
  - **Heiwa-dori** is the pedestrian street on `heiwa-paving-autotile` (rows 10-12 from the alley gate to the
    station's far end, with a leg down to the bridgehead). One row of fronts, feet on row 9: the town's
    **7-Eleven** ((12,6), door (13,9), `KonbiniAsahikawa1`), a bookshop (sealed: nothing in the catalogue is a
    book), a sake shop, a bakery and a woodcraft shop (`ShopAsahikawa1..3`, see Shop floors). Two ice
    sculptures, benches and the street's own lamps (`heiwa-lamp-post`) stand on the setts; a door front and a
    stand cell are never under one.
  - **Ramen alley** is two cells wide on `ramen-alley-autotile` (rows 14-15): `ramen-shoyu-front` (a shop
    floor, `ShopAsahikawa4`, list `ramen`), `ramen-narrow-front` and `ramen-miso-front` (sealed), feet on row
    13, behind `asahikawa-ramen-gate` (11,11) - through its middle cell (12,13) off Heiwa-dori, or round the
    alley's open east end. Somebody stood on row 15 is walked round along row 14 or along the bank (row 16), so
    **no prop's foot on row 14 stands within two columns of a bank shrub of row 16, and no single free cell is
    left between two feet**: anyone can be stood on any cell of row 15 (the old alley was one cell wide and the
    pipeline refused its stand cell). The
    yard behind the fronts is closed (the fronts are solid all over, a hedge on column 11).
  - **The frozen river** runs bank to bank (laid by hand: `ice-pond-autotile` edge-n / center / edge-s rows,
    solid, because `Builder.pond` is two rows tall) and **Asahibashi**, the green steel arch, is the only way
    over: `asahibashi-deck` (2x5 at (20,16), flat: `Non-Collidables` + `depthBias: -200`, its cells left out of
    the colliders), a rib each side (`-arch-w` / `-arch-e`, solid) and `-brace` on `Tops` over the deck's middle
    row. A fishing tent, holes and cracks are on the ice (`Non-Collidables`, over the Water layer).
  - **The south bank**: three Hokkaido houses (`hokkaido-house-red` / `-blue`, doors (5,26), (10,26), (15,26):
    `HouseAsahikawa1..3`) behind a snow fence, and the **Asahiyama Zoo gate** (`zoo-gate` at (29,22)) with its
    ticket booth, fence, penguins and seal. The drawn gate has no back: its prefab seals the row behind the
    arch, so the arch is a porch one cell deep, and the wood behind it is closed (a hedge on column 26, the
    fence, the booth). The shrine, its foxes and the torii that stood there are gone, and `ShrineAsahikawa1`
    with them (`generate_shrines.py` prunes nothing of a town it is not run for: the room, its door and its
    map were deleted by hand).
  - **The art tool registers what it draws**: `generate_asahikawa_art.py` calls `art_register.register`
    (`tools/art_register.py`: `spriteMetadata`, `tileNames`, the `glow` spots of what is lit at night,
    `depthBias: -200` for a flat sprite) and is in `check_generators.ART_TOOLS`. `tools/tests/asahikawa.test.js`
    holds the town to all of the above.
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
  `tanukikoji-end-sign`, `tanukikoji-south-row-a` / `-b`; stage 4: `susukino-neon-corner`, `susukino-karaoke`,
  `susukino-ramen-gate`, `susukino-ramen-stall-a` / `-b`, `susukino-neon-lanterns`, `ramen-alley-lanterns`,
  `tram-pole`; `tanukikoji-rib` and `sapporo-konbini` are drawn and not placed).
  `--sheet`, `--scenes` and `--manifest` write a contact sheet, mock scenes and the door / footprint table.
  Odori's pieces (the sculptures, the two tents, now ridge tents seen from above, the fountain, the lamp,
  now a dim gold `c6a663` globe, the bench) and `ramen-alley-lanterns` are in the house look: each ends in
  `odori_finish`, which shades the snow onto the pack's blues (`form()`), swaps every off-pack colour
  (`O_SWAP`) and inks with the pack's `080d16` (#302); the shared snow helpers (`snow_cap`, `drift`, the
  `SNOW*` colours) are untouched until #285, so they still draw the old whites elsewhere.
- **Flat sprites over water**: `Over Floor` and `Water` share one fixed depth, so a multi-cell sprite on
  `Over Floor` is drawn UNDER water tiles. The bridge therefore sits on `Non-Collidables` with
  `spriteMetadata.depthBias: -200` (written by `generate_hokkaido.py`'s `FLAT` table): above every ground
  layer, below everything Y-sorted, so the player walks on it. Its cells are simply left out of the
  river's colliders.
- **Konbini interiors per host**: `tools/generate_konbinis.py [Host ...]` - with host names it (re)builds
  only those hosts' stores (`generate_konbinis.py Sapporo`), leaving every other konbini room untouched.
  `generate_sapporo.py` re-seals the konbini door, so run it after every Sapporo regeneration. (The
  discount store's door is wired by `generate_sapporo.py` itself and survives a regeneration; its
  interior is `generate_discount_stores.py Sapporo`.) **Removing a store** (issue #243): take the building
  out of the host, then run the generator for that host (`generate_konbinis.py Market`,
  `generate_discount_stores.py Sapporo`). The stores are renumbered in door order, and the run deletes the
  room nothing claims any more (`removed  KonbiniMarket6 ...`), its `tiled/` map and the door that led into
  it (`roomgen.drop_stale`, `generators-and-checks.md` "Interior building blocks"); there is nothing to
  delete by hand, and `check_generators.py` fails for a map left without a room.
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
  does something, or a `Seats.RULES` row if it is something to sit on - "Sitting on furniture" in
  `architecture.md`). The room's `boundary` is the floor, the mat and the two wall rows
  (`back_wall(..., view=True)`): the wall is solid,
  and with it the outline is taller than a landscape phone's view, so the camera follows you instead of
  being held to the floor with the wall off the top of the screen. The art is the `konbini-*` kit,
  26 sprites drawn by `tools/generate_konbini_art.py [--preview out.png]` (procedural, needs Pillow, in
  `check_generators.py`): run it before `generate_konbinis.py` when the kit changes. The Tanukikoji
  shop floors and Don Takote keep the `office-*` furniture. Tests: `tools/tests/konbini.test.js`.
- **Build order**: `generate_hokkaido.py`, `generate_sapporo_art.py`, `generate_asahikawa_art.py`, `make_prefabs.py`, `generate_sapporo.py`,
  `generate_asahikawa.py` (then `generate_konbinis.py Asahikawa`, `generate_houses.py Asahikawa` and `--shops Asahikawa`), `generate_konbinis.py Sapporo`, `generate_discount_stores.py Sapporo`,
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
  interiors below); the keys are the three Hokkaido houses of the riverside row now (#219, stage B).
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
  on its plaza by the beach to the west - the door in its foot is a lift up to its observation deck,
  `DeckFukuoka1`: see "Fukuoka Tower's deck" - the station plaza with the 7-Eleven `KonbiniFukuoka1` to the east)
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
  `depthBias: -200`, the `asahibashi-deck` recipe; the two pond cells under it are left out of the colliders),
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
  zebra crossing (neither is a tile: the cable car runs the rails west of the avenue and the tram those east of
  it, and both can be ridden - the room's `tramways`, issue #245; "Shuttles" in `ambient-traffic.md`); the **painted ladies** (six terraces, each on a higher footing than the last) standing on a
  bluestone wall of **street art** with two **coffee windows** let into it, the **laneway** along its foot;
  the plaza with the **pointy pyramid** beside the **arts-centre spire** (both in `game.lookUp.sprites`), a glass
  tower, vending machines and the 7-Eleven `KonbiniSanFranbourne1`; the **brown river** (solid, rowers on it)
  under the **red suspension bridge** - the deck is the avenue, and you walk between the legs of both towers
  (only the leg cells collide); the yellow **station with the clocks** over its door (nobody catches a
  train there, a bump says so - you meet under the clocks; the two door cells under the clocks open into its
  concourse, see "Flinders Street's concourse"), townhouses and a palm garden; the boardwalk, the
  **pier** (flat, walked on to its end) with the raft of **sea lions** beside it (a bump from the pier says a
  line), and the island with the lighthouse out in the bay. Four **leaners** (`sfb-lean-{a,b,c,d}`, `LEANERS`
  in the generator) stand folded double at the waist by the tram stop, on the pavement between the two towers,
  in the laneway and beside the 7-Eleven: one solid cell each, off the avenue and every door, and a bump says
  that figure's one line (`Interactions.RULES`, kind `leaner`).
- **Art**: `tools/generate_sanfranbourne_art.py` (Pillow, in `ART_TOOLS`; `--preview out.png`) draws every
  `sfb-*` sprite, the `airport-*` furniture and the two flight pictures as shaded pixel art in the GuttyKreum
  palette - no brand marks but the 7-Eleven the game already has. The oval and the pier are flat
  (`Non-Collidables` with a `depthBias`, the `asahibashi-deck` recipe); the river is `pond-autotile`
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
| Asahikawa | `HouseAsahikawa1..3` (the riverside row of Hokkaido houses, `hokkaido-house-red` / `-blue`, door at the sprite's (1, 3)) | - (the ramen fronts and Heiwa-dori's shops are shop floors or sealed, not houses) |
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
  front (`SHOP_SIGNS`: the ramen nobori - no town has one since Asahikawa's ramen alley got fronts of its own, #219). 7-Elevens, the discount
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
  is run for the town, which also deletes the rooms no house claims any more, their `tiled/` maps and, in a
  ported town where the map still carries it, the door that led into them (issue #243: `roomgen.drop_stale`,
  the same for lobbies, shop floors, pagodas, shrine halls, 7-Elevens and discount stores; the run prints
  `removed`, `deleted` and `shut` lines, and `--dry-run` deletes nothing). The old doorway is sealed only if
  a house still stands on it: where the building is gone the cell stays as the town left it.
- **Art**: none of the GuttyKreum packs has a home interior (they are exteriors and a train car;
  there is no `Modern_Interiors`). `tools/extract_house_interior.py` takes what fits - floorboards from the
  Train Interiors car floor (`home-wood-floor`), a potted plant from the Japanese City pack (`home-plant`) -
  and `tools/generate_house_art.py` draws the other 34 `home-*` sprites in the house look (#330): half size,
  pixel-doubled, drawn with the file's own colours and repainted to GuttyKreum sheet colours by `SWAP` as each
  is saved, a 1px navy outline on what stands, the pack's dark glass in the windows, nothing lit yellow
  (`--preview out.png` on both). The colour constants and `box` / `speckle` / `wall_frame` / `plaster` are
  shared with `generate_devhouse_art.py`, so change a colour of the home kit in `SWAP`, not in the constant. The wall
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
souvenir shop, crab shop and drugstore are `ShopSapporo1..3`, and Susukino's karaoke bar is `ShopSapporo4`.
**And to Asahikawa** (stage B): Heiwa-dori's sake shop (`Sake bar · Asahikawa`, list `standbar`), bakery
(`bakery`) and woodcraft shop (`Woodcraft · Asahikawa`, list `souvenirs`) are `ShopAsahikawa1..3`, and ramen
alley's shoyu counter (`Ramen · Asahikawa`, list `ramen`) is `ShopAsahikawa4`.
**And to Karuizawa** (issue #261): Kyu-Karuizawa Ginza's bakery (`Bakery · Karuizawa`, list `bakery`), jam
shop (`Souvenirs · Karuizawa`, list `souvenirs`) and cocktail lounge (`Lounge · Karuizawa`, list `lounge`)
are `ShopKaruizawa1..3` (see Karuizawa).

- **One layout** (`SHOP`): a white back wall with two posters, two shelves either side against it, seven by five
  cells of floor, a counter with a till, a plant in each front corner, the mat below the middle. All of it is the
  konbini's furniture (`office-*`) and the lobby's mat; no new art.
- **Named by what the front sells** (`SHOP_TYPES`: sprite family -> label, list, shelves): `Souvenirs · Sapporo`,
  `Crab shop · Sapporo`, `Drugstore · Sapporo`, `Karaoke bar · Sapporo` (numbered only where a town has several
  of one type).
- **It sells**: the room is `interior`, `shopEnabled: false` (not a store: no stamp, no Konbini Pilgrim, the
  shelves are only to look at) and `shopMenu: souvenirs | crab | drugstore | bar | standbar | bakery | ramen | lounge`, so a bump on the counter opens that
  row of `Shop.VENUES` - two or three things off the existing catalogue (see Shop). The room's `shop` marker is
  `{host, door, type}`.
- A new shopfront elsewhere is a row in `roomgen.SHOP_DOORS` and one in `SHOP_TYPES` (and a `Shop.VENUES` row
  if it sells something else).

### Tower lobbies: a door into every high-rise (issue #216)

The same generator opens a second kind of building: `tools/generate_houses.py --lobbies <Town> [<Town> ...]`
gives every high-rise, office tower and block of flats a `Lobby<Town><n>` room (`Lobby · Osaka 2`). It is
the house code with another row in its `KINDS` table, so everything above holds - found in the town's map
data, numbered in door order, skipped and sealed by the same rules, a no-op on a re-run, kept through a
town rebuild by `roomgen.save_config`. **Applied to every town that has a tower**: twenty-six lobbies in nine
towns, no tower skipped. Asahikawa, Tokyo, Park, Shirakawa-go and Toyama have no towers.

| Town (display name) | Rooms | Tower and its door cell(s) in the town |
|---|---|---|
| Osaka | `LobbyOsaka1..3` "Lobby · Osaka 1..3" | the blue office block (5,17); the flats (5,37); the glass tower (43,38)+(44,38) |
| Sapporo | `LobbySapporo1..3` "Lobby · Sapporo 1..3" | its own office blocks (#219): the brick one in the Clock Tower block (51,15); the glass one west of the station plaza (12,16); Susukino's neon corner building (35,46) |
| Market (Asakusa) | `LobbyMarket1` "Lobby · Asakusa" | highrise-yellow (16,29) |
| Palace (Marunouchi) | `LobbyPalace1..2` "Lobby · Marunouchi 1..2" | highrise-yellow (49,13); midrise-apartment (42,15) |
| Shinjuku | `LobbyShinjuku1..9` "Lobby · Shinjuku 1..9" | the street of high-rises (#94). North of the avenue: highrise-apartment (6,11); -glass (11,11)+(12,11); -blue (17,11); -yellow (22,11); midrise-apartment (28,11). The south block: highrise-blue (7,29); -glass (13,29)+(14,29); -apartment (20,29); -yellow (26,29) |
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
  for a house or a shrine of a long-named town ("House 3", "Shrine"): Asahikawa's worship hall (#212; gone
  with its shrine in #219) read "Shrine", because "Asahikawa shrine" is 16 and cost the bar its year at 667x375. The whole name still shows
  wherever the bar has room for it. A town-led form can still be too long for the countdown, as a house's can: "Kanazawa
  lobby" (14) shows the date at 844x390, and every town-led lobby but Osaka's does at 667x375.

- **What is a tower** (`roomgen.TOWER_DOORS`): the five generic building sprites `highrise-yellow`,
  `-blue`, `-glass`, `-apartment` and `midrise-apartment` and Sapporo's `sapporo-office-brick` and
  `sapporo-office-glass`, with the door cells of their prefabs. Landmark
  towers (Tokyo Tower, the Sapporo TV Tower, Tsutenkaku, castles) are landmarks and stay
  sealed - but Fukuoka Tower, whose door is a lift up to its observation deck (see "Fukuoka Tower's deck");
  the discount store has its own shop floor.
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
  and its `tiled/` map and renumbers the rest.

### Shrine worship halls (issue #212)

A shrine hall is enterable: its top step (the `shrine` / `shrine-red` prefab's door cell, building cell
`(1, 4)`) carries a hidden transporter into a worship hall of its own, `Shrine<Host><n>` (HUD: `Shrine | Asakusa`, the host's display name).
Every hall in the world has one: **Tokyo** (`ShrineTokyo1`, Palace Shrine), **Market** and **Park**
(`ShrineMarket1`, `ShrinePark1`), **Kanazawa** (`ShrineKanazawa1`, blue, standard; Asahikawa's
`ShrineAsahikawa1` went when the zoo gate was built where its shrine stood, #219) and **Fukuoka**'s two, both red and large: Kushida Shrine (`ShrineFukuoka1`) and Dazaifu Tenmangu
(`ShrineFukuoka2`). Dazaifu's hall is its own sprite (`dazaifu-hall`, stamped sealed right across): its door is
building cell `(3, 4)`, the right half of its two-wide steps, in line with the bridge
(`roomgen.SHRINE_DOORS` has a row per hall tile).

- **`tools/generate_shrines.py [Host ...]`** owns the interior and the door it opens in the host, like
  `generate_konbinis.py`: the room is rebuilt from scratch (its NPCs kept), the door cell is unsealed and its
  transporter replaced in place, and the two exit mats lead to the cell in front of the door. With no host it
  rebuilds the halls already wired (what `check_generators.py` runs); a host is named the first time.
  `.agent-queue/items/shrines_apply.sh <Host> ...` is the whole roll-out for a town (art, generator,
  `config_to_tiled`, lint, the five gates).
- **Removing a hall** (issue #243): take it out of the host and re-run the generator, with the host or with
  no argument (a town named by a hall's `shrine` marker is visited even when its last door is gone). The
  halls left are renumbered in door order, and the room nothing claims any more, its `tiled/` map and the
  door into it are deleted by the run (`roomgen.drop_stale`); nothing is deleted by hand.
- **A town generator keeps the door.** A generated town rebuilds its room and stamps the hall sealed;
  `roomgen.save_config` then puts the door back exactly as it does a house's (`keep_house_doors`, see House
  interiors): the hall's room carries `shrine: {host, door, look, size}`, and `'Shrine'` is a row of
  `roomgen.OWNED_DOORS` (room-key prefix -> that marker and the door sprites, `SHRINE_DOORS`), so a door
  the room had on load is restored where the hall still stands (cell unsealed, transporter back in its
  place in the list) and dropped where the hall moved or its room is gone. No town generator needs an edit
  for its shrine to stay open; `shrines.test.js` proves it on a scratch copy (Fukuoka and Kanazawa
  rebuilt, then Kanazawa's hall sealed and rolled out again), and `check_generators.py` for every wired
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
  across the menu or any overlay opened and closed with the key still down (`ShrineVisit.held`, fed
  `InputHandler.heading()` every frame: while the direction that bumped is held it is still that bump; let go
  or turned about it is over, so a key pressed again inside the menu is a new bump). The rule asks what is
  held and never the clock: a frame of any length with the key down is the same bump (#251).
- **Art**: `tools/generate_shrine_art.py` (needs Pillow; `--preview out.png`) draws every piece as shaded
  pixel art in the two looks (`shrine-in-<piece>-red|blue`, shared pieces `shrine-in-<piece>`); the temple
  packs are exteriors only, and `tools/extract_shrine.py` cuts the one interior piece they have, the garland.
  Both are in `check_generators.py`.
- **Doors and blog NPCs**: the door-front cell stays clear (`NPCManager.atDoorway`; `shrines.test.js` holds
  it for every dated position). `the shrine` LANDMARK stands its visitor at building cell `(1, 6)`, the foot
  of the two steps: two cells below the door, not in front of it, and walked round by the side of the
  bottom step. A base NPC is config data and is moved by hand when a door opens where it stood: Xander's
  Asahikawa cell was the one in front of the hall's door (31,27) and is (33,28) now (the hall is the zoo gate since #219, and he stands in front of it).

### Underground arcades (chikagai)

Japanese cities run a shopping arcade under their main streets, reached by stairs from the pavement. A town
gets one from three files: `tools/chikagai.py` (data only: the arcade's shape, its shopfronts, its exits and
where each exit's entrance stands on the street), `tools/generate_chikagai.py [Host ...]` (the room
`Chikagai<Host>` and the doors into it) and `tools/generate_chikagai_art.py` (the `chika-*` sprites and the
street entrance, `chikagai-entrance-snow`, 2x3: solid but for the foot of its steps, a pair of door cells).
The art is drawn in the house look, in the pack's colours only, and owns its palette: it takes only the canvas
and text helpers from `generate_station_art.py`, and `pane`, `foliage` from `generate_sendai_art.py` (#316).

- **The town's own generator stamps the entrances** where the table says (`chikagai.TOWNS[town]['exits'][slug]
  ['street']`), sealed; `generate_chikagai.py` opens them and wires both door cells of each, and
  `roomgen.save_config` keeps those doors through a town rebuild (`OWNED_DOORS`, marker `chikagai` on the room,
  as a house's or a lobby's). Walking onto the steps takes you down to the foot of the matching stairs; each
  exit brings you back up onto the cell in front of its entrance.
- **The room** is a cross of corridors: an east-west hall with 3x2 shopfronts set into its north wall behind a
  stone apron, and a stem north and south. Exits in a north wall are stairs under a gold exit sign with the
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
  ends of the hall, Tanukikoji's at the foot of the south stem. Stage 4 built Susukino and left the south exit
  where it was (east of Tanukikoji, a short walk down the east street from the crossing); to move it to
  Susukino, change its `street` cell in the table and re-run both generators.
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
  `.held`).
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
  per bump by the offering box's rule (`ShrineVisit.fresh` / `.held`). A toast is one line, so every line is
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
    fronts, a glass rail, a terracotta balcony that bows out over each shop. Every piece is an entry of
    `game.lookUp.sprites` (0: the wall stands on the floor; written by the art tool's `LOOK_UP`, issue #258),
    so on the north bank the camera looks up at it ("Looking up at landmarks" in `hud-input-touch.md`). A
    landscape phone shows 7.5 rows and its ordinary camera showed a row and a half of the wall to somebody
    standing against it; now all five rows are in view from against the wall (the top one partly behind the
    bar, which is as far as the view goes with two rows kept under the player), one row fewer for each row
    you step back, and the reach has faded out by the canal. That is 844x390; a phone under 400 px tall
    (667x375) has its controls over the canvas's bottom corners, the look-up keeps that strip under the
    player clear as well, and so it only narrows the deadzone there: one row more of the wall than before,
    the galleries still off the top. A desktop window only narrows its deadzone too, which keeps the wall's
    top clear of the bar;
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
  (`mall-in-<piece>`) and marks the back wall's pieces for the camera (`LOOK_UP`); the frame is the pub art
  tool's, in cream and terracotta. It and the generator are in `check_generators.py`.
- **Doors and blog NPCs**: no dated position or district stand cell is on a door or the cell in front of one,
  and a wanderer never steps there. The `Canal City` LANDMARK stands its visitor on the plaza beside the doors
  (the sprite's cell + (2,6): Julia on 10 November 2025). Post 727 stays outside: moving it into the atrium
  would need the blog pipeline to place into an `interior` room, which it never does.
- **Build order**: `generate_mall_art.py`, `generate_mall.py`, `config_to_tiled.py MallFukuoka1 Fukuoka`,
  `play.js lint MallFukuoka1 Fukuoka`. Tests: `tools/tests/mall.test.js` (on `tools/tests/interiors.js`).
### Flinders Street's concourse (issue #246)

**What the station is on the map.** One sprite, `sfb-clocks-station_0_0` (12x7), west of the avenue in
`SanFranbourne`: the yellow station with the board of clocks over its door. It was sealed. The two door cells
under the clocks (the sprite's cell + (5,6) and + (6,6); `SanFranbourne` 18,45 and 19,45 as the town stands)
each carry a hidden transporter into `FlindersSanFranbourne1` (HUD: `Flinders St`, the Map footer
`Flinders St (in San Franbourne, overseas)`). The west door puts you on the west half of the doorway and the
east on the east, and the mat behind you puts you back on the boardwalk in front of the door above it. The
rest of the building still bumps its line from the street. Like the pub's, the doors are found by sprite
(`roomgen.FLINDERS_DOORS`); if a rebuild of the town moves the station, run `generate_flinders.py` then
`config_to_tiled.py FlindersSanFranbourne1 SanFranbourne`.

- **`tools/generate_flinders.py`** owns the interior and the two door cells, exactly as `generate_mall.py`
  does Canal City's (`interiors.Interior`, `roomgen.sprite_doors`, `roomgen.open_door`);
  `generate_sanfranbourne.py` is not edited. A re-run is a no-op, and from a sealed building it rebuilds the
  same world (`flinders.test.js`).
- **Door keeping.** The room carries `flinders: {host, doors}` and `'Flinders'` is a row of
  `roomgen.OWNED_DOORS` (`FLINDERS_DOORS`), so a re-run of `generate_sanfranbourne.py` keeps both doors.
- **What is inside** (24x18; the floor is 20x11), a station nobody catches a train from. It is not in
  `config.stations`, on no departures board, and San Franbourne is still reached only by air.
  - the back wall, three rows tall, in the building's mustard and maroon: a bay (`wall-bay`, 3x3), an arched
    window (`wall-arch`, 4x3), the name board (`wall-name`, 6x3: `FLINDERS ST`), a window, a bay;
  - **the track** under it, two rows of the station kit's rails over ballast (`station-track-n/-s`,
    `station-ballast`), solid from end to end and empty: no train is parked, and none passes;
  - **the platform**: the kit's yellow edge row, then two rows with two benches facing the track
    (`station-bench-back`);
  - **the gate line**, the last row of the platform's floor and the only way onto it: two banks of two
    ticket gates (`station-gate`, walked through, between `station-gate-end-w/-e`) either side of **the
    clocks** (`clocks`, 4x3: the nine dials from over the door outside, on two posts; only its foot row is in
    the way, and from the platform you walk behind its head), a cell of tube railing outside each bank, the
    **ticket machines** (`tickets`, 3x2) against the west wall and the **departures board** (`board`, 3x2)
    against the east one;
  - the concourse: terrazzo (`floor-a/-b`), two `station-pillar`s, two `station-bench`es,
    `station-planter-a/-b` either side of the doorway and the daylight through it (`doorlight`).
- **No lantern light.** `interior` but not `lanternLight`, and no `Glows` rows: a concourse is as bright at
  night as by day.
- **Something to do.** Bump the clocks from either side: they are a `clock` (`Interactions.js`), so Time Travel
  opens, as at every clock. Bump the board or the machines for a line (`flavour` rules `replacement-buses`,
  `ticket-machine`). Go through a gate and along the platform. No venue, no stamp, no new overlay, key or
  save field.
- **Looking up.** The room (18 rows) is taller than a phone's view (7.5 rows on a landscape phone), so
  `back_wall(view=True)` cannot hold it whole (`RoomManager.heldRows`), and from the platform the ordinary
  camera showed the track and not the wall. The wall's three pieces are in `game.lookUp.sprites` with `2`
  (the track's rows), written by the art tool as the pagoda's roof is: on the platform the camera sits as
  high as it goes with two rows kept under you, and the name board and the windows are in view. From the
  second concourse row south of the gates it is the ordinary camera.
- **Art**: `tools/generate_flinders_art.py` (needs Pillow; `--preview out.png`) draws the 14 sprites
  (`flinders-in-<piece>`) and their frame itself, in the house look (#309): GuttyKreum colours only, the
  pack's navy outline, dark glass with a slanted glare, unlit lamps in its dim gold; it imports only
  plumbing from `generate_pub_art.py`. The track, the gates, the railing, the benches, the pillars and
  the planters are the station kit's (`tools/generate_station_art.py`). It and the generator are in `check_generators.py`.
- **Doors and blog NPCs**: no dated position or district stand cell is on a door or the cell in front of one,
  and a wanderer never steps there. The blog stands nobody at the station, and never places into an
  `interior` room.
- **Build order**: `generate_flinders_art.py`, `generate_flinders.py`,
  `config_to_tiled.py FlindersSanFranbourne1 SanFranbourne`, `play.js lint FlindersSanFranbourne1 SanFranbourne`.
  Tests: `tools/tests/flinders.test.js` (on `tools/tests/interiors.js`).

### Fukuoka Tower's deck (issue #242)

**What the tower is on the map.** One sprite, `fukuoka-tower_0_0` (4x12), on its plaza by the beach in
`Fukuoka`: the `Fukuoka Tower` landmark. It was sealed. The two leaves of the door in its foot (the sprite's
cell + (1,11) and + (2,11); `Fukuoka` 11,18 and 12,18 as the town stands) each carry a hidden transporter into
`DeckFukuoka1` (HUD: `Tower Deck`), the observation deck 123 m up, and each cell of the lift's sill inside puts
you back on the plaza in front of the leaf above it. The doors are found by sprite (`roomgen.DECK_DOORS`), as
the mall's are; if the tower moves, run `generate_tower_deck.py` then `config_to_tiled.py DeckFukuoka1 Fukuoka`.

- **The door is a lift.** A transporter into a room that carries the `deck` marker, or out of one, is a lift:
  `RoomManager.liftFor(config.rooms, from, to)` answers `'up'`, `'down'` or `null`, and
  `RoomManager.checkTransporter` hands such a door to `ViewRide.lift(dir, transporter)` instead of fading the
  room. Nothing names the tower: another deck needs only the marker.
- **The ride** (`src/ViewRide.js`, 4.5 s): the screen fades, the room is swapped under a black curtain, and the
  picture plays - the inside of the glass lift (`view-lift`, 640x640, with a hole for its window), the player
  seen from behind, and outside the town dropping away as the counter on the lift's panel climbs to `123 m`
  (`ViewRide.height` eases away from the ground and into the top; `metres`). The way down is the same ride
  backwards, the counter falling to 0. The view is two tall pictures behind the window, `view-fukuoka-far`
  (the bay, the islands and the day sky; opaque) and `view-fukuoka-near` (the plaza, the beach, Marizon and the
  town; transparent above its skyline), each bottom-aligned in the window on the ground and top-aligned at the
  top (`ViewRide.pan`): `far` is the shorter, so it moves less. The tower's own beams pass the glass on the
  way (`ViewRide.beams`: none in the window at either end).
- **The hour is the game's.** Both pictures are tinted with what the street outside is multiplied by
  (`ViewRide.tint(period)`, from `DayNight.GRADES`), and when that grade has lights `view-fukuoka-lights` (the
  lit pixels of `near` and nothing else) is drawn over them untinted. So the ride by night is the same art.
- **Skipping and input.** Input is locked for the ride like a flight (`InputHandler` hands every frame to
  `ViewRide.handleInput` while `riding`; `roomManager.isTransitioning` holds the player). SPACE / ENTER / ESC
  (A / B on touch) or a tap anywhere ends it from `ViewRide.SKIP_AFTER` (0.7 s) after the picture comes up
  (`ViewRide.canSkip`): a key still held from the walk in is not a skip. The keys are read through the
  handler's keydown latch (`InputHandler.pressed`), as the flight's are, so a tap that is down and up again
  inside one frame skips too (#253). The hint under the picture is worded by
  `Hints.text` (`SPACE: skip the ride` / the tap wording). No new key, overlay or save field.
- **On a phone** the picture is magnified as the world is, but never larger than the view less the room the
  hint needs under it (`ViewRide.layout`, `hintRoom`: `UIScale` draws the hint as large on the screen as on a
  desktop and keeps its margin, so on a phone it needs more canvas px). A portrait phone's view is narrower
  than the frame: the window and the counter's panel keep to the frame's middle `ViewRide.SAFE_W` (560) columns,
  which is `Viewport.MIN_VISIBLE`. The counter is part of the picture (it is sized with it and stays on its
  panel); the picture is a cover the size of the view to `UIScale`, drawn 1:1 like the plane's cabin.
- **`tools/generate_tower_deck.py`** owns the room and the two door cells, exactly as `generate_mall.py` does
  the mall's (`interiors.Interior`, `roomgen.sprite_doors`, `roomgen.open_door`); `generate_fukuoka.py` is not
  edited. A re-run is a no-op, and from a sealed tower it rebuilds the same world (`views.test.js`).
- **Door keeping.** The room carries `deck: {host, doors}` and `'Deck'` is a row of `roomgen.OWNED_DOORS`
  (`DECK_DOORS`), so a re-run of `generate_fukuoka.py` keeps both doors.
- **What is inside** (20x15; the floor is 18x6), one long room in dark carpet and steel:
  - the back wall, five rows tall, is glass from the floor up: six panes (`window-1..6`, 3x5) of one view north
    over Hakata Bay - the same canvases the lift shows, as they stand at the top - inside the room's boundary
    (`view=True`), so a phone's camera shows all of it;
  - three coin binoculars (`binoculars`, 1x2) and the lovers' fence of padlocks (`locks`, 2x2) along the glass,
    a brass map of the bay on a plinth (`compass`, 2x1), the sign by the lift (`lift-sign`, 1x2);
  - two benches facing the glass (`bench`, 2x1). They are seats (`Seats.RULES`, see Sitting on furniture in
    `architecture.md`): walk into one and you sit with your back to the room, its front drawn over your legs;
  - four pendant lamps over the floor (`downlight`, 1x2 on `Tops`);
  - the lift in the front wall: its sill (`lift-w`, `lift-e`) is the doorway, two cells wide, with the cabin's
    light on the carpet in front of it (`doorlight`).
- **Daylight.** `interior` (never offered to the blog pipeline) and `daylight`: the room's light is the sky's,
  so `DayNight.gradeFor` grades it by the hour exactly as it does the street (a `lanternLight` room dims only
  at night; every other interior is never graded). At dusk and at night the lamps glow and so do the lights of
  the town in the panes (`Glows.SPRITES` rows for `deck-in-downlight` and `deck-in-window-1..6`, placed where
  `view-fukuoka-lights` has its lights). What you rode up to is what you step out to.
- **Something to do.** Bump a pane, the binoculars, the brass map, the padlocks or the sign for a line
  (`flavour` rules `deck-window`, `binoculars`, `compass`, `padlocks`, `lift-sign` in `Interactions.js`); sit
  on a bench and look out. Nothing is sold (`shopEnabled: false`); no venue, no stamp.
- **Art**: `tools/generate_tower_deck_art.py` (needs Pillow; `--preview out.png`) draws the 20 sprites
  (`deck-in-<piece>`, registered as tiles) and the four pictures of the ride (`view-lift`, `view-fukuoka-near`,
  `-far`, `-lights`: whole images in `spriteMetadata`, no tile name). The view is drawn once, as three canvases
  as wide as the deck's wall; the panes and the ride's pictures are cut from them. The frame is the pub art
  tool's. It and the generator are in `check_generators.py`.
- **Without a browser**: `WorldModel.step()` reports the door as `transported: { from, to, lift: 'up' | 'down' }`
  and `play.js` prints `(the lift goes up)`; the ride itself is not modelled.
- **Doors and blog NPCs**: the `Fukuoka Tower` LANDMARK stands its visitor on the plaza, not on a door or the
  cell in front of one (`views.test.js` holds every dated position and stand cell off them), and nobody is
  placed on the deck: the pipeline never places into an `interior` room.
- **Build order**: `generate_tower_deck_art.py`, `generate_tower_deck.py`,
  `config_to_tiled.py DeckFukuoka1 Fukuoka`, `play.js lint DeckFukuoka1 Fukuoka`. Tests:
  `tools/tests/views.test.js` (on `tools/tests/interiors.js`); the browser regression rides it (`tower-lift`,
  `tower-lift-skip`, `tower-deck-night`, `phone-landscape-lift`, `phone-portrait-lift`).

### A turn on the Dotonbori wheel (issue #242)

**What it is on the map.** The wheel is one sprite, `dotonbori-wheel_0_0` (12x12, `generate_osaka.py` `WHEEL`):
two legs and a ring, nothing drawn or solid between the legs (issue #241), so you walk under it. One 2x2 prop,
`wheel-boarding_0_0`, stands at its foot: a gondola down at the ground under the three that hang on the wheel's
west side, outside the legs (`BOARDING = (WHEEL[0], WHEEL[1] + 10)`; `Osaka` 33..34, 17..18 as the town
stands), its door swung open, on a step. It is placed from `WHEEL`, so it moves with the wheel. It is solid; the
gap between the legs and the walk under the wheel are as they were, and so is the canal-bank cell under the
wheel where the blog pipeline stands the wheel's visitors.

- **Bumping it is the ride.** `Interactions.RULES` has one row for it, kind `wheel`, group `ride` (on the
  gondola, not on the wheel, whose footprint is 12x12). `GameScene.checkNPCInteraction` asks
  `ViewRide.check(x, y)` after the flights board; a fresh bump runs `ViewRide.wheel()`. One ride per bump: a key
  held against the gondola boards once, and when you step off with it still down it is still that bump. Let go
  and press again for another turn. The bump is kept by what is held, asked every frame
  (`ViewRide.hold(heading)`, `ViewRide.held`), and not by the clock as the offering box's is
  (`ShrineVisit.carried`, 250 ms): a long frame as the ride's pictures are cleared must not be a second
  14 s turn. Free; no save field.
- **The ride** (`ViewRide.RIDES.wheel`, 14 s) is the lift's sequence with no room behind the curtain: the
  screen fades, the picture plays, the screen comes back and you are on the cell you boarded from, facing the
  gondola. The picture is the inside of a gondola (`view-gondola`, 640x640, a wide window 512x320, a grab rail
  across it, two seats) with the player seen from behind, and through the glass Dotonbori: the billboards and
  the canal with its bridges and a boat at the foot, the rooftops as you climb, and at the top the sky over the
  whole town with Tsutenkaku on the skyline. A ride with `turn` goes up, over and down again
  (`ViewRide.height`: `(1 - cos 2πt) / 2`, 0 at both ends and 1 half-way, slow at the bottom and over the top
  as a wheel is), and the view slides sideways as the wheel carries you across (`ViewRide.drift`: `drift` px
  out on the way up, back through the middle at the top, out the other way coming down; `far` by a third,
  `ViewRide.FAR_DRIFT`). The layers are `drift` px wider than the window on each side. A gondola has no
  counter and no beams go by: those are the lift's (a ride with `top` and `panel`).
- **The hour, the skip, the phone** are the lift's (see "Fukuoka Tower's deck"): the same tint and lights
  layer (`view-dotonbori-far`, `-near`, `-lights`: the neon is the lights), SPACE / ENTER / ESC or a tap from
  0.7 s, the picture sized by `ViewRide.layout` with the window inside the frame's middle `SAFE_W` columns.
- **Art**: `tools/generate_wheel_art.py` (needs Pillow; `--preview out.png`; in `check_generators.py`) draws
  the prop - cropped from `assets/sprites/dotonbori-wheel_0_0.png`, so it is the wheel's own gondola in the
  wheel's own colours - and the four pictures, with the sky, water, buildings and lamps of
  `generate_tower_deck_art.py`. Tsutenkaku is drawn in `near`, not `far`, so that its lights come on at night.
- **Without a browser**: a step into the gondola is a bump whose `interaction` is `{ kind: 'wheel', group:
  'ride' }`; `world.describe` and `play.js` say `rides the wheel: one turn, the view over Dotonbori, and back on
  this cell`. On the map it is drawn `*`. The ride itself is not modelled.
- **Build order**: `generate_wheel_art.py`, `generate_osaka.py`, `config_to_tiled.py Osaka`,
  `make_worldmap.py`, `play.js lint Osaka`. Tests: `tools/tests/views.test.js` (the gondola's cells and the
  cells it is bumped from, free and reachable on every surveyed date; the turn, the drift, one ride per bump;
  the pictures) and `roads-waterways.test.js` (the wheel's solid cells: its legs and the gondola); the browser
  regression rides it (`wheel-ride`).

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
  10x7 floors, centred in the room; its 1F and 2F are the stair hall of those floors, two cells wide, **on the
  same room cells**, so the stairs line up all the way down. Osaka's floors are 9x10. Tokyo's were 14x8 and
  mostly bare boards: #228 kept the furniture and halved the walking space, and `devhouse.test.js` holds a
  ceiling of 48 cells to stand on per floor, so a new piece goes on the existing footprint rather than a
  wider one. A `|` partition is drawn with `devhouse-wall-v`, its last cell with `-wall-v-end`, and where a
  `-` wall meets it with `-wall-h`.
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
  tables you walk round, and a line on each would toast again and again. The bath and the bunk are also seats
  (issue #227, `Seats.js`): you get onto them instead of bumping them, and their line is said as you settle.
  Nobody lives there and nothing is
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
