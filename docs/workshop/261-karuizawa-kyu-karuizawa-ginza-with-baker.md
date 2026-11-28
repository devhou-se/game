# Karuizawa part 2: Kyu-Karuizawa Ginza — a bakery, a souvenir shop and a lounge (#261)

Part 2 of #256 (plan: `docs/workshop/68-featured-locations-everywhere-else-anyon.md`, "Karuizawa"). Part 1
(#260, `docs/workshop/260-karuizawa-the-room-the-reopened-west-gat.md`) has landed. All cells are Karuizawa's
own. Everything below was prototyped on a scratch copy with stand-in art (Asahikawa's bakery under the three
new keys); the numbers are measured there.

## Context

Karuizawa is a road through woods with nothing to go into. The posts name the places: the old Karuizawa Ginza
shopping street and "a bar with cigars and whiskey" (Damian, 544), "a cocktail lounge" (Julia, 572), "apple pie
from a tiny boulangerie" (576, 583). This ticket builds that street: three shopfronts, each with a door, a shop
floor behind it and a list on its counter. No sealed building, no rubbish bin, nothing that is not a real place.

## Approach

**Where.** Every shopfront in the game faces south (door in its bottom row), so fronts cannot face onto the
north leg of the road (columns 14-15). The Ginza is therefore the west end of the road in, where it turns
north: three 3x4 fronts side by side on its north side, the dirt widened one row to meet their doors. The north
leg and the clearing stay as they are for the falls, the larches, the bus stop and the corn stall, and none of
part 1's asserted road cells moves. (The plan's "west then north as Kyu-Karuizawa Ginza" is read as "the street
at the turn"; a spur off the north leg would be a dead end and a rerouted road would churn part 1.)

```
row 29..32   . . [bakery ] s [ jam   ] s [lounge ] woods        s = one solid cell (a shrub)
row 33       R R d d d d d d d d d d d d d  grass verge ...      d = new dirt, cols 16..28
row 34..35   R R ================ the road in ================== -> gate (47, 34..35)
col          14  17 18 19    21 22 23    25 26 27
```

**How.** The existing shop-floor machinery, unchanged (`landmarks-and-towns.md`, "Shop floors"): a row per
front in `roomgen.SHOP_DOORS` and in `generate_houses.py` `SHOP_TYPES`, then
`generate_houses.py --shops Karuizawa` builds `ShopKaruizawa1..3` and opens the doors. The town generator
places the fronts sealed with `b.prop(key, x, 29, 3, 4)` (whole footprint solid, as Tanukikoji's `roof=0`
shops; no prefab, as part 1 has none); `roomgen.save_config` keeps the opened doors through a rebuild
(`keep_house_doors`: the sprite is on `Collidables`). One new `Shop.VENUES` row, `lounge`.

## Changes

**`tools/generate_karuizawa_art.py`** — three builders added to `SPRITES`, each `canvas(3, 4)` (96x128 at half
size, doubled to 192x256; anchors come out `32/192`, `32/256`), label = the key without `_0_0`:

| key | what it is |
|---|---|
| `karuizawa-shop-bakery_0_0` | the tiny boulangerie: cream plaster and dark half-timbering under a steep red-brown gable, a lit window of loaves and an apple pie, a board with a loaf on it |
| `karuizawa-shop-jam_0_0` | the jam and souvenir shop: white clapboard under a green roof, a lit window with shelves of red, purple and orange jars, a board with a jar on it |
| `karuizawa-shop-lounge_0_0` | the cocktail lounge: dark timber over a stone dado, a small amber window with bottles, a brass lantern by the door, a board with a cocktail glass |

Rules for all three: the door is drawn in the middle cell of the bottom row (half-size x 32..63, y 96..127) and
the building's foot is on the bottom edge; three different silhouettes and colours, unlike `heiwa-shop-*` and
`tanukikoji-shop-*`; autumn, no snow; lettering too small to read or a generic word, no real shop name; no bin;
nothing copied from `art-source/`. Add a `GLOW = {key: [spots]}` dict and write it as `glow` into each key's
`spriteMetadata` (the fingerpost gets none, its metadata stays exactly as tested): one or two spots per front
on the lit window and door, e.g. `{'x': 1.5, 'y': 3.0, 'r': 1.4, 'ry': 0.8, 'color': 0xf6dc8c, 'a': 0.55}`
(cells from the sprite's top-left; amber `0xffb366` for the lounge), placed by looking at the art. Docstring:
list the three sprites; drop "the three shopfronts" from what later tickets add.

**`tools/generate_karuizawa.py`**
- Constants: `GINZA_Y = 29` and
  `GINZA = [('karuizawa-shop-bakery_0_0', 17), ('karuizawa-shop-jam_0_0', 21), ('karuizawa-shop-lounge_0_0', 25)]`.
- The road's `b.autotile` cell list gains `rect(RX1 + 1, GATE[0] - 1, GINZA[-1][1] + 3, GATE[0] - 1)`
  (`(16..28, 33)`), in the same call so the pieces join.
- After the fingerpost and **before** the first `k.woods`:
  `for key, x in GINZA: b.prop(key, x, GINZA_Y, 3, 4)`. The woods skip taken cells, make the gaps `(20, 29..32)`
  and `(24, 29..32)` solid, and `k.dress()` puts a shrub where a bare collider meets the street. Nothing else
  changes; the room's `transporters` stay `rg.kept_order(prev, seams)` (save_config adds the doors back).
- Docstring: a `ginza` entry, "parts 2 and 3 line it" and the two "part 2 draws `karuizawa-larch`" notes
  corrected (the larch is a later part), and the build order below.

**`tools/roomgen.py`** — `SHOP_DOORS` gains `'karuizawa-shop-bakery_0_0': [(1, 3)]`,
`'karuizawa-shop-jam_0_0': [(1, 3)]`, `'karuizawa-shop-lounge_0_0': [(1, 3)]`; its comment names them.

**`tools/generate_houses.py`** — `SHOP_TYPES` gains (comment: Karuizawa, issue #261):

```python
'karuizawa-shop-bakery': ('Bakery', 'bakery', 'office-shelf-snacks_0_0'),
'karuizawa-shop-jam': ('Souvenirs', 'souvenirs', 'office-shelf-glass_0_0'),
'karuizawa-shop-lounge': ('Lounge', 'lounge', 'office-shelf-drinks_0_0'),
```

**`src/Shop.js`** — `Shop.VENUES` gains, after `tasting`, with a comment (Karuizawa's cocktail lounge, #261, a
`Shop<Town><n>` room's `shopMenu`; no stamp, no fish bought):

```js
lounge:  { title: 'LOUNGE',          sells: i => ['highball', 'vodka-redbull', 'nama-beer'].includes(i.id) },
```

**`tools/check_generators.py`** — no new entry is needed: `generate_houses` (already in `GENERATORS`) rebuilds
every town that has shop rooms, and `generate_karuizawa_art` is already in `ART_TOOLS`. Only that line's
comment changes ("the fingerpost and the Ginza's three shopfronts (#260, #261)").
**`tools/check_distinct.py`** — no change: `karuizawa-` is already in `LANDMARK_ART` (part 1 added it).

**Generated, committed with the change**: `config.json` (room `Karuizawa`, new rooms `ShopKaruizawa1..3`,
three `tilePalette` entries appended, `spriteMetadata`, `tileNames`), `tiled/karuizawa.tmj`,
`tiled/shopkaruizawa{1,2,3}.tmj`, three PNGs in `assets/sprites/`, `assets/map/world-map.png`.

**Build order** (from `gamev2/`, Pillow needed for the first and last):

```bash
python3 tools/generate_karuizawa_art.py --preview /tmp/karuizawa-art.png   # look at it
python3 tools/generate_karuizawa.py
python3 tools/generate_houses.py --shops Karuizawa
python3 tools/districts.py
python3 tools/config_to_tiled.py Karuizawa ShopKaruizawa1 ShopKaruizawa2 ShopKaruizawa3
python3 tools/make_worldmap.py
node tools/play.js lint Karuizawa ShopKaruizawa1 ShopKaruizawa2 ShopKaruizawa3 TokyoCity
node tools/play.js render Karuizawa /tmp/karuizawa.png                     # look at it
```

**Docs (same commit)**: `docs/landmarks-and-towns.md` — the Karuizawa section (what is there now: the Ginza,
its cells, the three rooms and lists; the shopfronts are no longer "later parts"; build order) and "Shop
floors" ("And to Karuizawa", `shopMenu` gains `lounge`); `docs/shop-and-economy.md` — the shop-floor row of the
bump table gains `"lounge"` — LOUNGE: Highball, Vodka Redbull, Nama Beer.

One commit: `gamev2: Kyu-Karuizawa Ginza — a bakery, a souvenir shop and a lounge you can go into … (#261)`.

## Data and interfaces

| room | name | door (Karuizawa) | front cell | `shopMenu` | title, list |
|---|---|---|---|---|---|
| `ShopKaruizawa1` | `Bakery · Karuizawa` | `(18, 32)` | `(18, 33)` | `bakery` | BAKERY: Melon Pan, Nikuman, Canned Coffee |
| `ShopKaruizawa2` | `Souvenirs · Karuizawa` | `(22, 32)` | `(22, 33)` | `souvenirs` | OMIYAGE: Green Tea, Ramune, Melon Pan |
| `ShopKaruizawa3` | `Lounge · Karuizawa` | `(26, 32)` | `(26, 33)` | `lounge` | LOUNGE: Vodka Redbull, Highball, Nama Beer |

Each room is what `build_shop` makes: 20x15, `interior: true`, `shopEnabled: false`,
`shop: {host: 'Karuizawa', door: [x, 32], type: <shopMenu>}`, one transporter `(9, 10)` back to the front cell;
the door lands on `(9, 9)`. `rooms.Karuizawa.transporters` becomes the two seams, then the three doors (hidden)
in that order. No new JS file, no new localStorage key, no change to districts, places or the blog pipeline.

## Tests

**`tools/tests/karuizawa.test.js`** — two assertions change on purpose (the only two unit tests the prototype
broke; baseline 446 passed):
- test 1: `room.transporters.map(t => t.targetRoom)` is
  `[HOST, HOST, 'ShopKaruizawa1', 'ShopKaruizawa2', 'ShopKaruizawa3']` ("the gate and the three shop doors").
- test 2: the seam comparison and the flood fill's start take `transporters.filter(t => t.targetRoom === HOST)`.

One new test, "Kyu-Karuizawa Ginza: a bakery, a souvenir shop and a lounge you can enter, each with its list
(#261)", modelled on `asahikawa.test.js` (its Heiwa-dori test) and `chikagai.test.js` (`game('Shop.VENUES')`):
- the fronts: `tilesOf(KEY)` filtered by `/^karuizawa-shop-/` is exactly the three keys at `17,29`, `21,29`,
  `25,29` on `Collidables`; each has `spriteMetadata` anchors of a 3x4 sprite and a non-empty `glow` list;
  no tile of `house-`, `machiya-`, `highrise-`, `midrise-`, `discount-store` or `seven-eleven` is in the room
  (no sealed ordinary building).
- per shop (table above): the door cell is open and the other eleven cells of the footprint are solid; the
  door's transporter and the room's lead to each other (`[HOST room, x, 33]`, landing one above the way out);
  the front cell is dirt and is reached by the flood fill from the gate; `name`, `interior`, `shopEnabled`,
  `shopMenu`, `shop` marker; `Interactions.match('office-counter2_0_0', r, venues)` is
  `{ kind: <menu>, group: 'shop', footprint: true }`; no NPC state of `rooms.Karuizawa` stands on a door or
  front cell.
- the lists: `Shop.DEFAULT_ITEMS.filter(venues[m].sells)` ids, sorted, are the three lists above;
  `Shop.titleFor('lounge', room) === 'LOUNGE'`; `venues.lounge` neither `buys` nor `grills`.
- walking it: with `worldWith(true)` and `worldWith(false)`, get from Tokyo `(6, 41)` into Karuizawa as test 3
  does (stitched: one walk; `?stitch=0`: through the gate cell), walk to each front cell, `step('n')` is
  `transported` into the shop at `(9, 9)`, and walking back out south lands on the front cell.
- `SHOP_DOORS` / `SHOP_TYPES` hold the three keys (regex on the two tool files, as the test already does for
  `check_generators.py`).

Run from `gamev2/` (prototype results in brackets; use a Pillow venv, `tools/requirements-art.txt`):

```bash
node tools/test_game.js                  # [444 passed, the 2 above failed before their edit]
python3 tools/test_blog_to_npc.py        # [ok]
node tools/play.js check                 # [no problems found]
python3 tools/check_generators.py        # [all ok; both generators re-run byte-identical]
python3 tools/sync_cities.py --check     # [in sync]
python3 tools/check_distinct.py          # [no city worse; Tokyo 0.14 / 0.31 / 58%] do not run --update
python3 tools/rehearse_blog.py           # [313/313]
REGRESS_TIME_SCALE=2 PORT=8000 node tools/browser/regress.js   # tools/browser/README.md; no new check in it
```

By playing (real keys, screenshots looked at; desktop and a landscape phone with `?touch=1`): from Tokyo's west
gate walk to each door, go in, bump the counter, see BAKERY / OMIYAGE / LOUNGE and its three items, ESC, walk
out onto the street; once with `?stitch=0`; the street at `?tod=night` for the glows. In the prototype, with
keys in headless Chromium, the door at `(22, 32)` led in and the counter opened its list, with no console error.

## Risks and open questions

- **The Ginza is on the road in, not on the north leg.** Forced by south-facing fronts; if the owner wants it
  elsewhere, only `GINZA_Y`, the three columns and the widened-dirt rectangle move.
- **Names and the list** are choices: `Souvenirs · Karuizawa` for the jam shop (it sells the OMIYAGE list, no
  jam is in the catalogue) and LOUNGE = Highball, Vodka Redbull, Nama Beer (three drinks already sold, a list no
  other venue has).
- **The art is the implementer's to draw**; the prototype used stand-ins, so the look, the glow spots and
  night were not judged. Look at the preview and at the street in the game before committing.
- **The woods reshuffle**: placing the fronts before the seeded scatter moves shrubs across the room, so
  `config.json` and `karuizawa.tmj` differ widely. Expected; lint was `0 errors, 0 warnings` for the room, the
  three shops and `TokyoCity`.
- **Later parts**: an NPC or blog spot standing on a door or its front cell seals that shop on the next
  `generate_houses.py` run; the re-homing ticket must keep `(18|22|26, 32..33)` free (the new test holds it).
- **Map data is serial**: this touches `Karuizawa` and adds `ShopKaruizawa1..3`; `Tokyo` is not changed.
- Not run in the prototype: the browser regression, a phone size, night.
