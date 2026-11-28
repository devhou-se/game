# 367: ramen you sit down for, order and eat at the counter

Commit the implementation as `gamev2: ... (#367)`. Paths below are under `gamev2/`.

## Context

The owner: "there are no real ramen shops! they exist but i can't sit and buy ramen. i want to buy and
eat ramen (on the spot)".

What is there today:

| Place | Today |
|---|---|
| Susukino's ramen alley, Sapporo: `susukino-ramen-stall-a` at (18,42) and (24,42), `-b` at (21,42), 3x3 | a bump opens RAMEN ALLEY (`Shop.VENUES.ramen`): Karaage, Edamame, Nama Beer. No ramen. The stools are paint: the whole stall is a wall. (`/work/media/367-design-ramen-alley-list-today.png`) |
| `ShopAsahikawa4` ("Ramen · Asahikawa", behind `ramen-shoyu-front`) | the one generic shop floor: an office counter with a till, four drinks shelves, two plants, the same `ramen` list. Nowhere to sit. (`367-design-asahikawa-ramen-shop-today.png`) |
| Fukuoka's four `yatai-ramen` (10 / 22 / 38 / 50, 34), 3x3, a ラーメン noren and three stools | nothing: no rule in `Interactions.js` |

There is no bowl in the catalogue (`Shop.DEFAULT_ITEMS`) and no bowl icon (`ItemIcons.SHAPES`).

What already works and is reused: the venue list and "buy & use now" (`Shop.buy(true)` -> `Shop.use`),
and sitting (`src/utils/Seats.js`): in the Izakaya you step onto an `izakaya-stool`, press towards the
bar again and the list opens while you sit. Checked in a browser.

#376 (CoCo Ichibanya) and #377 (MOS Burger) wait for this ticket and are told to build on its
"sit-and-eat-on-the-spot mechanic" and not add a second one. So the mechanic below is two small general
pieces, not ramen code.

## Approach

1. **Three bowls**, one per town, in the catalogue with one new `bowl` icon shape.
2. **Eat-in items** (`eatIn: true` on a catalogue item): served where they are sold. Buying one eats it
   there and then through the existing `use()` path; it is never carried, so quantity is 1 and it never
   shows in Items. This is a property of the item, so any venue that lists one serves it.
3. **A stool at every ramen counter**, with the existing seat step: walk into the stool and you are on
   it, press towards the counter and the list opens.
   - `ShopAsahikawa4` gets a second shop-floor layout: a counter the width of the room with a row of
     `izakaya-stool` in front of it (already a seat). The counter can only be reached from a stool.
   - The street stalls have their stools painted on. `Seats` gets one optional field, `at`, that limits
     a rule to some cells of the sprite's footprint; the **middle stool** of each Susukino stall and each
     Fukuoka ramen yatai becomes a seat. Only the middle one: the outer stools are 20 to 25 px off their
     cell's centre, so the player would sit on the post or the wheel
     (`/work/media/367-design-prototype-stall-seats.png`: the three columns of each, prototyped in the
     running game; the middle column is the design). No art changes.
4. **Fukuoka's ramen yatai sell**: one `Interactions` rule and one venue.

Sitting is not required to order. The layouts put a stool between the player and the counter; a bump on
a stall's outer columns still opens the list standing, as now. A hard "sit first" rule was the
alternative; it would refuse a sale for no gain and tie #377 (order at a counter, sit at a table) to it.

No new art, no new input, no save change. Out of scope: `toyama-ramen` (a building with no door), the
mall's `mall-in-front-ramen` (a flavour line about a ramen floor that does not exist), the two sealed
Asahikawa fronts, Fukuoka's yakitori and oden yatai. Opening those is new interiors (#363's family).

## Changes

### `src/Shop.js`

- **Catalogue**: a new first section of `Shop.DEFAULT_ITEMS`, before the drinks, so a bowl is the first
  row of its list:

  | `id` | `name` | `price` | `where` | `effect` | `desc` |
  |---|---|---|---|---|---|
  | `miso-ramen` | Miso Ramen | 950 | `ramen` | `{ speed: 1.2, secs: 300 }` | `butter and corn on top. speed +20% for 5 min, on top of any drink.` |
  | `shoyu-ramen` | Shoyu Ramen | 900 | `ramenya` | `{ speed: 1.15, focus: 8, secs: 300 }` | `a film of lard keeps it hot to the last sip: speed +15% and 8s more on the work clock, for 5 min.` |
  | `tonkotsu-ramen` | Tonkotsu Ramen | 850 | `yatai` | `{ steady: true, prizeBonus: 1.5, secs: 300 }` | `lines the stomach: drinks cannot make you wobble and nomikai showdown winnings +50%, for 5 min.` |

  All three: `category: 'food'`, `energy: 100` (a full meter), `eatIn: true`,
  `icon: { shape: 'bowl', colors }` (colours under `ItemIcons.js`). Only existing effect kinds are used.
- **Venues** (`Shop.VENUES`; titles are capitals and spaces only, a test reads them by regex):
  - `ramen`: `sells: i => i.where === 'ramen' || ['karaage', 'edamame', 'nama-beer'].includes(i.id)`
  - new `ramenya: { title: 'RAMEN SHOP', sells: i => i.where === 'ramenya' || ['karaage', 'nama-beer'].includes(i.id) }`
  - new `yatai: { title: 'YATAI', sells: i => i.where === 'yatai' || ['edamame', 'nama-beer'].includes(i.id) }`
- **Eat-in**:
  - `static eatsIn(item) { return !!(item && item.eatIn); }`
  - `maxQty`: 1 for an eat-in item (beside `permanent`).
  - `buy(useNow)`: for an eat-in item `qty` is 1 and it is always used: the condition becomes
    `(useNow || Shop.eatsIn(item)) && !item.permanent`. The rest of the path is unchanged (money, the
    stamp, `use()`'s toast, energy, effect, achievements, the gulp).
  - `static buyLabels(item)` -> `{ buy, useNow, hint }`, the words for the selected row, used by
    `paint()`:
    permanent `{ '[ buy ]', '', H }`; eat-in `{ '', '[ order & eat ]', 'ENTER order & eat' }`; anything
    else `{ '[ buy ]', '[ buy & use now ]', H }`, with `H = 'ENTER buy · SHIFT+ENTER buy & use now'`.
    `render()` keeps the `[ buy ]` button and the last hint line as `this.buyText` / `this.hintText`
    (cleared with the other text refs); `paint()` sets them per row (the hint through `Hints.text`), and
    shows `×1` and the single price for an eat-in row as it does for a permanent one. The sell list is
    untouched.

### `src/ItemIcons.js`

A `bowl` map in `ItemIcons.SHAPES` (16 rows of 16): a bowl seen from the front and a little above. `a`
broth, `c` noodles in it, `d` a topping, `b` the bowl's body with `e` on its lit rim, `o` outline; two
chopsticks resting on the rim. More than 40 pixels drawn. Colours (tune by eye; the three must stay
different pixels):

| | `a` broth | `b` bowl | `c` noodles | `d` topping |
|---|---|---|---|---|
| miso | `#c98a3c` | `#b23a2e` | `#f3dc8a` | `#ffe14a` (butter) |
| shoyu | `#7a4a22` | `#2f4a8a` | `#f0d9a0` | `#e8a0a0` (chashu) |
| tonkotsu | `#efe3c8` | `#1f1f2a` | `#fff6da` | `#d8423a` (beni shoga) |

### `src/utils/Seats.js`

- A rule may carry `at: [[col, row], ...]`: the cells of the sprite's footprint that are the seat. In
  `index()`, inside the cell loop: `if (rule.at && !rule.at.some(([c, r]) => c === cx - x && r === row)) continue;`.
  Document it in the header comment beside `open`.
- One row, first in the table:
  `{ kind: 'stool', pattern: /^(susukino-ramen-stall-[ab]|yatai-ramen)_/, at: [[1, 2]], pose: { face: 'up', dy: -6 } }`
  (`dy` -6 is what the prototype used; tune by screenshot so the head sits at the counter's edge.)

The rest of the stall stays a wall for everything, and a bump on it still opens the list.

### `src/utils/Interactions.js`

After the `ramen` rule:
`{ kind: 'yatai', group: 'shop', pattern: /^yatai-ramen/, footprint: true }` with a one-line comment.

### `tools/generate_houses.py` and the room `ShopAsahikawa4`

- A second layout beside `SHOP`, and which venue uses it:

  ```python
  RAMEN = dict(wall='wpwwwpw',
               floor=['SSSSSSS',     # the back shelves, wall to wall
                      'BbBbCcP',     # the counter: three lengths, the till on the last, closed by a plant
                      'TTTTTT.',     # a stool at every place
                      '.......',
                      'P.....P'],
               door=3)
  SHOP_LAYOUTS = {'ramenya': RAMEN}      # Shop.VENUES id -> layout; every other shop floor is SHOP
  ```
- `SHOP_TYPES['ramen-shoyu-front']` becomes `('Ramen', 'ramenya', 'office-shelf-drinks_0_0')`.
- `build_shop` takes `SHOP_LAYOUTS.get(menu, SHOP)`. New characters: `B` an `office-counter2_0_0`
  without a till, `T` an `izakaya-stool_0_0` (`it.prop`, so it is on `Collidables` with a collider: a
  seat needs one). `C` is as now.
- `check_interior`: a counter's cell in front may be a stool, if the cell in front of the stool is
  reached. Nothing else is relaxed.
- Update the module docstring ("one layout") and regenerate:
  `python3 tools/generate_houses.py --shops Asahikawa`, then `python3 tools/config_to_tiled.py` on the
  rooms it rewrote, `node tools/play.js lint ShopAsahikawa4`, and look at
  `node tools/play.js render ShopAsahikawa4 out.png`. Only `ShopAsahikawa4` may differ in `git diff`
  (config and `tiled/ShopAsahikawa4.tmj`): shelves (6..12, 5), counters at (6,6) (8,6) (10,6) with the
  till on (11,6), a plant (12,6), stools (6..11, 7), plants (6,9) (12,9), `shopMenu` and `shop.type`
  `ramenya`. Door, mat, name and size are unchanged. Rebuild the world map only if
  `check_generators.py` asks for it.

### Docs

- `docs/shop-and-economy.md`: the bump table (the `ramen` row; new `ramenya` and `yatai` rows), the
  catalogue section (`eatIn`, the three bowls, the `bowl` shape), buying ("order & eat"), the energy
  table, and that Taste Tester now counts 15.
- `docs/architecture.md`, "Sitting on furniture": `at`, and the stalls' middle stool.
- `docs/landmarks-and-towns.md`: Susukino's ramen alley, Asahikawa's ramen alley, Fukuoka's yatai row,
  and Shop floors (the second layout).

## Data and interfaces

- Catalogue item: new optional `eatIn: true` (a `config.json` `shop.items` catalogue may use it too).
- `Seats` rule: new optional `at`.
- `Shop.VENUES`: `ramenya`, `yatai`; `ramen` sells one more thing.
- `config.json`: `ShopAsahikawa4` layers, `shopMenu: "ramenya"`, `shop.type: "ramenya"`. No palette
  change (`izakaya-stool_0_0`, `office-counter2_0_0` are in it).
- Save blob `gamev2_shop`: unchanged (v4). A bowl is counted in `used` like any food and never rests in
  `items`.
- For #376 / #377: an `eatIn` item, a venue row that lists it, and seats in front of whatever opens the
  venue (a `Seats` row, or a `SHOP_LAYOUTS` entry for a generated shop floor).

## Tests

Unit (`tools/tests/`, run `node tools/test_game.js`):

- `shop.test.js`: the three bowls are food, `eatIn`, energy 100, and each is sold by exactly one venue
  (`ramen`, `ramenya`, `yatai`) and by no other row of `Shop.VENUES`, first in its list. With
  `shopWith` (and the stubs `energy.test.js` adds for `use()`): buying a bowl at energy 0 with quantity
  set to 3 takes one price, leaves `items` without it, sets `used['miso-ramen']` to 1, energy to 100 and
  the food effect; with too little money nothing changes. `Shop.buyLabels` for a bowl, a drink and the
  rod. `maxQty` is 1. The existing "every item has an icon, no two alike" test covers the bowls.
- `seats.test.js`: `at` keeps only the listed cells (a made-up room, as the overlap case); in shipped
  Sapporo `seatAt(19,44)`, `(22,44)`, `(25,44)` are `stool` seats with `face: 'up'` and every other cell
  of the three stalls is none; the same for the four yatai at `(x+1, 36)`; `canSit` from the cell below,
  `canStep` still false. In the pose-fits test: every `at` cell is inside the sprite.
- `sapporo.test.js` (the ramen-alley case, about line 612): the list has `miso-ramen`.
- `fukuoka.test.js`: `yatai-ramen_0_0` matches `{ kind: 'yatai', group: 'shop', footprint: true }`;
  `yatai-yakitori` and `yatai-oden` match nothing.
- `asahikawa.test.js` line 66: `ShopAsahikawa4` is `'ramenya'`. Add: its six stools are seats, each with
  a counter cell above and floor below; no counter cell has open floor in front.

Checks, from `gamev2/`, all must pass: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`,
`node tools/play.js check`, `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`.

Browser (`tools/browser/README.md`): add a `ramen` check to `tools/browser/regress.js` and run the
regression. Sapporo: from (19,45) press up -> on (19,44), lifted, facing up; up again -> list `ramen`,
first row Miso Ramen, `[ order & eat ]` shown and `[ buy ]` empty; ENTER -> money down 950, energy 100,
no `miso-ramen` in `shop.items`, a food effect running. `ShopAsahikawa4`: from (9,8) up -> on the stool
(9,7); up -> list `ramenya`. Then play it by hand on desktop and at a phone size with touch
(`?touch=1`): the three places, by day and night, and look at the screenshots: the player on each
middle stool, the bowl icons in the list, the new shop floor.

## Risks and open questions

- **#366 redraws the Susukino stalls in place** (design stage). The seat needs the middle stool to stay
  on the stall's middle column, bottom row. Whichever lands second looks at a screenshot of the player
  seated. The same holds for any later yatai redraw.
- **Map data**: this rebuilds `ShopAsahikawa4` and edits `generate_houses.py`, which #370 to #373 (new
  shop floors) also edit. Expect a small merge in `SHOP_TYPES`.
- **Taste Tester** goes from 12 to 15 things and now needs Sapporo, Asahikawa and Fukuoka. It is read
  live from `used`, so a player who had it sees 12/15 until they eat the bowls.
- One seat per street stall, and the shio stall (`-b`) serves the alley's miso bowl. A bowl per stall,
  or three seats per stall (the stools redrawn on cell centres), are follow-ups if the owner wants them.
- Damian and Bailey are placed at Fukuoka (11,37), in front of the first yatai's stool, on some dates;
  its list still opens from the outer columns and the other three yatai are free.
- The Asahikawa shop keeps the konbini's furniture: it is a ramen counter by layout, not by new art.
- Owner's call, not blocking: whether ordering should require being seated (chosen: no), and whether
  Toyama's ramen shop and the mall's ramen front should open (not in this ticket).
