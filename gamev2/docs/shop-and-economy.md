# Shop, food and drink, fishing, the drinking game stake

The wallet, konbini / vending machines / Don Takote, items and effects, the energy meter and the stamp card, selling fish, the save blob (`src/Shop.js` and friends).

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Shop, Food and Drink (issues #12, #46, #82, #83, #84)

`src/Shop.js` owns the yen wallet, the inventory, the buy/items overlays and the
food & drink effects. Everything starts with a bump (`GameScene.checkNPCInteraction`
→ `Shop.checkShopInteraction`, which only fires on BLOCKED cells):

| Bump | Opens (`Shop.VENUES`) |
|------|-----------------------|
| any `vending-machine*` tile, any room (bump the machine's foot from the cell in front) | `vending` — items with `where: 'vending'` |
| `office-counter*` in a konbini | `counter` — every vending + counter item |
| the 7-Eleven kiosk inside a station (`station-kiosk*`, any cell of the booth; see "The station interior") | `counter` — the same list |
| the 7-Eleven kiosk in an airport hall (the same booth and rule) | `counter` — the same list; no stamp |
| the pub's bar in an airport lounge (`airport-bar*`, issue #218) | `pub` — the izakaya's drinks and food, titled AIRPORT PUB; buys no fish, no stamp |
| the hot-drinks tent in Sapporo's Odori Park (`snowfest-stall-drinks*`, any cell of the tent, issue #219) | `stall` — Canned Coffee and Green Tea, titled HOT DRINKS; no stamp |
| the counter (`office-counter2*`) of a Tanukikoji shop floor (`Shop<Town><n>`, `"shopMenu": "souvenirs"` / `"crab"` / `"drugstore"`, issue #219) | that list — OMIYAGE: Green Tea, Ramune, Melon Pan; CRAB SHOP: Onigiri, Nikuman; DRUGSTORE: Zone Energy, Green Tea, Canned Coffee; no stamp, buys no fish |
| `office-shelf-drinks` / `-shelf-glass` / `office-fridge` / `office-freezer` in a konbini | `drinks` — the drinks only |
| `office-shelf-snacks` in a konbini | `snacks` — the food only |
| `office-counter2*` (the bar) in a room with `"shopMenu": "izakaya"` | `izakaya` — items with `where: 'izakaya'` |

- A "konbini" is any room with `interior: true` and `shopEnabled !== false` — the
  7-Eleven interiors and the Don Takote discount stores (below). The
  Izakaya is `shopEnabled: false` + `shopMenu: "izakaya"` (set in
  `tools/generate_izakaya.py`): its shelves and tables stay furniture, only the bar
  sells, and the drinking game's `triggerCells` are checked first so they never
  open a menu.
- **Where the Izakaya is** (issue #68): in Tokyo, in Market - the red townhouse in the
  south-west corner of the temple precinct, west of the big torii (house front at Market
  `(6..8, 37)`). The door is `(7,37)`, entered from the paving at `(7,38)`, and a red
  lantern stands either side of the house (feet at `(5,37)` and `(9,37)`) - the only
  house on the row with a pair. Both exit mats (`Izakaya (9,13)` / `(10,13)`) land on
  `(7,38)`. It used to be behind the lakeside farmhouse of Inaka, a made-up town that is
  deleted (issue #68). `tools/generate_izakaya.py` owns the interior, the door it opens in Market
  (collider off, hidden transporter, replaced in place) and the two lanterns, the way
  `generate_konbinis.py` owns a 7-Eleven's door; Market is otherwise a ported map.
  The house's two ad boards are its sign: their `signage` spots carry `"ad"` — `ad-wide-03`
  (のみほうだい, all you can drink) at `(6,36)` and `ad-square-01` (酒) at `(8,36)` — and a spot
  with an `ad` always shows that one, where every other board draws a random ad of its shape
  on each visit (`RoomManager.adFor`). The generator's `SIGNS` owns the pins; the keys are the
  pool's own (`assets/ads/manifest.json`, numbered in `generate_ads.py` `SPECS` order: a unit
  test ties the two keys to those two specs).
  The opponents at the table (Damian; Bailey when you play as Damian) are fixtures
  kept from the room as it stands. Tests: `tools/tests/izakaya.test.js`.
- **Vending machines are solid down to their foot** (issue #101). A machine is a cabinet
  tile over a foot tile (`*-vending-machine-top*` over `-bottom` / `-base*`; the tall ones
  are a 1x2 cabinet sprite over a base), and the foot is only the last 14-18px of the
  cabinet - with the foot cell walkable the player stood on the machine's lower half. Both
  the foot and the cabinet cell above it collide (the empty top cell of a tall machine
  stays walk-behind); the vending rule matches both tiles, so the bump that opens the shop
  is on the foot, from the cell in front - which must be walkable and lead somewhere (issue
  #137: lint error `vending-no-front`; the roof-top row 27 in front of Market's (22,26) and
  (23,26) is a walk-behind strip for that, the roof is solid from row 28). The
  `vending-white` / `vending-red` prefabs carry both colliders; `node tools/play.js lint`
  fails a room with `vending-walkable` otherwise, and `python3 tools/seal_vending.py [Room ...] [--dry-run]` repairs room data
  (it refuses to seal a cell holding a transporter or a dated NPC). The same goes for the fixtures
  INSIDE a store (issue #152): a shelf or cooler is bumped from the cell below it, so lint fails with
  `shop-no-front` when any column of a konbini / Don Takote shelf or cooler has no walkable cell under
  it that the door leads to (the till, against the front wall, needs any reachable side), and with
  `shop-sealed-floor` when a store has bare floor the door does not lead to (issue #182: the corner
  water dispenser stood one row below the back wall and boxed in the corner cell above it, beside the
  cooler run - `generate_konbinis.py` now stands it in the back corner, and where that would leave a
  single cell between it and the coolers the run grows one unit to meet it, so the back row has no
  one-cell nook on either side of it).
  `play.js check` reports every room's lint errors too (`WorldModel.lintProblems`, issue #178), so a
  store cut off from its door shows up there as `KonbiniMarket1: lint shop-no-front: ...`.
  `check` exits 1 when it lists any problem, like `lint` (issue #188), so a script or CI step can gate on it.
  The Tokyo city has no open cell that cannot be walked to (issue #196): the yard behind the Tokyo
  shrine hall, the floor under Market's wing roofs and the odd cell boxed in by bushes or lanterns carry
  a `gk_blank` collider, so nothing can place anyone there (unit-tested on the stitched city). Lint's
  `stray-collision` skips a bare collider that no walkable cell touches, which is what those are.
  `generate_konbinis.py` lays a store out as coolers | walkway | aisle | walkway | (aisle | walkway) |
  counter row: a two-cell `office-fridge` pushes the aisles down a row, the last aisle stops two rows
  short of the counter row (one on the row above it closed the ring and sealed the back of the store
  off from the door - `KonbiniMarket1` and `KonbiniMarket3` were like that), and a five-row store gets
  the one-cell freezer instead of the fridge. Keep NPC spots and
  door arrivals off the cell in front of a machine's cabinet.
- **Don Takote** (issue #91): every `discount-store` facade has a shop floor -
  `DonTakoteMarket`, `DonTakoteOsaka`, `DonTakoteSapporo` (HUD: `Don Takote | Osaka`, name `Don Takote · Osaka`; the room's
  `shopTitle: "DON TAKOTE"` titles the till's list instead of `KONBINI` - `Shop.titleFor`), built
  by `tools/generate_discount_stores.py [Host ...]` on the konbini pattern. 27x19 room, one
  fixed floor plan (so a town generator can wire its door without running it first): the
  facade's own sign on a yellow back wall, a wall-to-wall back row (drink coolers one side,
  shelving the other), three ranks of shelves either side of a centre aisle, cartons of
  stock in the front corners, one till by the three-cell door mat. What is seeded per store
  (host + door cell) is the stock, the floor and which side the till is on. It adds no shop
  code: `interior: true` makes it a konbini to `Interactions.js`, so the counter, shelves
  and coolers sell through the rows above (the buy list is still titled KONBINI). The
  signage (`don-takote-sign` / `-wall` / `-wall-top` / `-pop-yen` / `-pop-sale`) is cut from
  the facade sprite by `tools/generate_discount_art.py` (Pillow, no font needed).
  **Doors**: `generate_osaka.py` and `generate_sapporo.py` stamp the facade with
  `seal=False` and add `don.door_transporter(host, door)` themselves, so regenerating the
  town keeps the shop open; Market is ported, so `generate_discount_stores.py` lifts the
  one door collider and adds the transporter there (and does the same, idempotently, for
  the generated hosts). The cell in front of the door must be free - the script asserts it.
  A new host: stamp the facade, add the host to `ALL_HOSTS`, run the script, then
  `config_to_tiled.py` for the store room and the host.
- **Catalogue**: `Shop.DEFAULT_ITEMS` (or `config.json` `shop.items`, which replaces
  it wholesale). Each item: `id` (a save-file key — don't rename), `name`, `price`,
  `where`, `category` (`drink` | `food` | `gear`), `desc`, `icon`, and `effect` or
  `permanent`. Keep `desc` truthful — the use toast is generated from the `effect`
  numbers by `effectSummary()`, so the two are read side by side. The fish
  (`category: 'fish'`, see below) are appended to whichever catalogue is in use.
- **Icons** (`src/ItemIcons.js`, issue #82): every item has a 16x16 pixel icon, shown
  at 2x on a small slot square in the buy / sell lists, the Items screen and the HUD
  effect chips. They are drawn in code, data-first: `icon: { shape, colors }` names
  a pixel map in `ItemIcons.SHAPES` (16 strings of 16 characters: `.` transparent,
  `o` outline, `w` white, `e` silver, `k` grey, and the item's own `a` body / `b`
  shade / `c` `d` accents) and fills in its colours. An item with no `icon` gets
  `ItemIcons.DEFAULTS[category]`. Textures are made once, keyed `item-<id>`.
  **Real art needs no code change**: drop `<id>.png` in `assets/items/` and list the
  id in `assets/items/manifest.json` — it is preloaded under the same key and
  `ItemIcons.ensure()` only draws what is missing (see `assets/items/README.md`).
  `node tools/test_game.js` checks every item has a distinct, well-formed icon; look
  at new ones in a list before shipping them — the panels are dark, which is what
  the slot square is for.
- **Effects are additive buffs only** (the energy meter below is separate, and the only
  thing it ever takes away is the sprint). The keys an `effect` may carry are listed in `Shop.EFFECT_KINDS`:
  `speed`, `scramble`, `steady` (read by `InputHandler` via `movementModifier()`),
  `fishBite`, `fishWindow`, `fishLuck` (read by `Fishing` via `shop.buff(key)`),
  `headStart`, `prizeBonus` (read by `DrinkingGame`, locked in when a round
  starts; Bailey mirrors the head start, so his +10 gimmick survives), plus `secs`.
  To add a new kind: add it to `EFFECT_KINDS` with a `describe`, then read it with
  `shop.buff('key')` where it applies.
- **Slots**: one `drink` effect and one `food` effect at a time (`Shop.SLOTS`, slot
  = the item's category). The same item refreshes its timer; a different item in
  the slot replaces it and the toast says which. Active effects show as chips
  under the right end of the HUD bar with the time left, and in the Items screen.
- **Buying**: ↑/↓ pick, ←/→ quantity (1-9, capped by the wallet), ENTER/SPACE buy,
  SHIFT+ENTER/SPACE "buy & use now" (touch: hold the sprint pill and tap A; mouse:
  the `‹ ›`, `[ buy ]` and `[ buy & use now ]` buttons). Buy-list rows do NOT select on
  hover (the stepper sits under them, so a mouse heading for it would drag the
  selection down): a click/tap picks a row, clicking the picked row buys it. Rows
  show `have ×N` and dim the price you cannot afford. Hint lines switch to A / B /
  sprint wording when touch controls are on (`Hints.text`). No extra key bindings.
- Expired effects are queued in `shop.woreOff` and toasted ("X wore off") by the
  250ms chip timer once no other toast or shop overlay is up, so the message is
  never lost. Against Bailey the showdown banner says he matches the head start.
- **Fish are items** (issue #83). `Fishing.CATCHES` is the one table: `id`, `name`,
  `odds`, `value`, plus `desc`, `icon` and `grilled` (an effect). `Shop.fishItems()`
  turns every catch worth something into a catalogue item (`category: 'fish'`,
  `sell: value`, `effect: grilled`, `effectName: 'Grilled <name>'`, sold nowhere).
  A landed fish goes into the bag through `shop.addCatch(c)` — the wallet is not
  touched — and the toast says what it was, that it is in the bag and what it sells
  for. A catch worth nothing (the old boot) is thrown back with a toast and never
  becomes an item. `shop.caught` counts landings per species and feeds the
  **Big Catch** achievement (`AchievementManager.fishingProgress()`: land a rare
  fish, `Fishing.isRare` = worth `Fishing.RARE_VALUE` or more).
- **Selling**: a venue with `buys: true` in `Shop.VENUES` (the konbini `counter`, the
  `izakaya` bar — not vending machines or the shelves) gets one more row under its
  items, `sell your catch ›`. ENTER on it flips the same panel to the SELL list (the
  fish held, their price, ←/→ quantity up to what is held, ENTER sells, the row
  `‹ back to the menu` returns); `shop.mode` is `'buy'` or `'sell'` and
  `refreshStock()` rebuilds the list for it. A venue with `grills: true` (the
  izakaya) also offers SHIFT+ENTER / `[ grill & eat ]`: one fish is eaten for its
  `grilled` effect in the FOOD slot. A raw fish cannot be used from the Items screen
  (the toast says where to take it). `Shop.sellValue(item, qty)` is the price; items
  without `sell` are worth nothing, so a shop never buys its own stock back. No new
  key bindings.
- **Save blob** `localStorage.gamev2_shop`:
  `{ v: 4, money, items: {id: count}, effects: {drink|food: {id, until}}, used: {id: count}, caught: {id: count},
  energy, stamps: {place: 1}, hints: {low: 1} }`,
  plus `omikuji: {date, i}` once a fortune has been drawn at a shrine or in the temple's fortune drawers (one field for both: `ShrineVisit`, see "Shrine worship
  halls" in `landmarks-and-towns.md`; `Shop.omikujiOf` drops anything that is not one). The wallet also pays
  the shrine's offering (¥5) and fortune (¥100): neither is a purchase, so neither feeds the energy meter
  nor stamps the Stamp Card. And `guestbook: {date, n}` once the palace's visitors' book has been signed
  (`PalaceVisit`, see "The palace's audience hall" there; `Shop.guestbookOf`): the day it was last signed and
  how many times in all. Both fields are absent until used, and a blob without them loads and saves unchanged.
  `until` is an absolute epoch-ms expiry, so buffs survive reloads and room changes
  and lapse on time; on load it is clamped to the item's own duration and effects
  for unknown items are dropped. Older blobs load as-is and are rewritten as v4 on
  the next save: the issue #12 one (`{money, items}`), v2 (no `caught`, no fish) and v3
  (no `energy`: the meter starts full, as it does for a new player; no `stamps`, no `hints`)
  — the wallet is never changed by loading.
  `used` counts consumption and feeds two achievements in
  `AchievementManager.consumptionProgress()`: **Taste Tester** (use every
  consumable) and **Regular Customer** (25 uses), both listed in the Achievements
  overlay.
- Test hook: `scene.shop.clockOffset` (ms) fast-forwards the shop's clock so a
  test can expire a buff without waiting.
- **Nomikai showdown stake** (`src/DrinkingGame.js`, issue #84). The ready screen has
  a stake row from `DrinkingGame.STAKES` — `FRIENDLY` (stake 0, wins ¥100 on the
  house), `SMALL TAB` (¥500) and `BIG TAB` (¥2,000), each `{ id, label, stake,
  winnings }` — picked with ←/→ (A/D, the touch d-pad) or a click/tap. A stake the
  wallet does not cover is greyed and cannot be picked — trying to (→ or a tap) toasts
  what it needs and what the wallet holds; the last pick is remembered
  while it is still affordable. The line under it says what is at risk and what the
  pool is. Money moves like this, and nowhere else: the stake leaves the wallet in
  `begin()`; a win pays `DrinkingGame.pool(option, prizeBonus)` = stake +
  winnings × bonus (so Karaage's +50% applies to the winnings, never the stake); a
  draw returns the stake; a loss pays nothing more, so it costs exactly the stake;
  ESC mid-round (`leave()`) forfeits the stake with a toast; ESC on the ready screen
  or the result costs nothing. The result screen leaves on ENTER / ESC, and on
  SPACE (the touch A button) once `DrinkingGame.RESULT_GRACE_MS` has passed, so the
  last mashes of a round do not dismiss it. The effect hooks are unchanged (`headStart` and
  `prizeBonus` are locked in when the round starts) and so is the Bailey rule: when
  the player is Damian, Bailey mirrors every press and the head start and wins by
  his ten bonus gulps, so any stake put up against him is lost.
- `node tools/test_game.js` covers the pure parts of all of this without a browser:
  icons, sell values, catches into the bag, save migration, stake / pool maths and a
  whole stubbed round at every stake (win, lose, draw, walk-out, vs Bailey).

### Energy and the stamp card (issue #209)

A reason to stop at a konbini or a vending machine every few minutes, that never punishes. The rules
are pure functions in `src/Energy.js` (`Energy`, `Stamps`); `Shop` holds the state in its save blob,
draws the meter and pays the rewards; tests are `tools/tests/energy.test.js`.

**Energy** is a 0-100 meter. A new player and a save from before the meter start full.

| | |
|---|---|
| Drain | `Energy.CELLS` = 1800 cells of walking empty a full meter (`Energy.stepCost()` = 100/1800 a cell). A walked cell is 200 ms, so that is **6 minutes of walking, 3 of pure sprinting** (a sprint, or a speed drink, covers more cells a second and so drains faster by the clock). Standing, talking, menus, mini-games and train rides cost nothing; a bump that does not move you costs nothing (`InputHandler.handlePlayerMovement` calls `shop.walked()` only when the step started). |
| Well fed, `>= Energy.WELL_FED` (70) | sprint is x`Energy.WELL_FED_SPRINT` (2.25) instead of x2. Meter green. |
| Normal | sprint x2. Meter amber. |
| Low, `<= Energy.LOW` (25) | nothing changes; the meter is red. The first time ever it gets here a one-line hint is toasted (`Energy.HINT`, remembered in the save as `hints.low`). |
| Peckish, 0 | **SHIFT / the sprint pill does nothing** and a toast says so (`Energy.PECKISH`, every time the meter empties, and again - at most once per `Energy.REMIND_MS`, 10 s - whenever sprint is held while walking on an empty meter: `Shop.sprintHeld`, so a save loaded at zero is told too). The touch sprint pill is dimmed with a dashed border while the meter is empty (`tc-nosprint` on the touch root, set by `Shop.updateEffectChip`; not while a shop list is open, where the pill is SHIFT). Walking speed is unchanged, speed drinks still work, and nothing else is ever blocked: you can walk, talk, shop, fish, play the drinking game and ride trains on an empty meter. |

- **Refilling**: using any food or drink adds its `energy` (`Energy.valueOf(item)`; the use toast ends
  `· energy +N`, the buy list and the Items screen show `energy +N` on the row). Food fills, a soft
  drink tops up, alcohol hardly counts:

  | Item | energy | | Item | energy |
  |---|---|---|---|---|
  | Nikuman, Karaage | 60 | | Zone Energy | 30 |
  | a grilled fish | 50 | | Canned Coffee, Ramune | 20 |
  | Onigiri | 45 | | Green Tea | 15 |
  | Melon Pan | 40 | | Vodka Redbull | 10 |
  | Edamame | 30 | | Highball, Nama Beer | 5 |

  An item in a config catalogue with no `energy` gets `Energy.DEFAULTS[category]`. Gear gives none.
  Buying does not fill the meter; eating does (so SHIFT+ENTER "buy & use now" is the quick way).
- **The meter** is on the HUD layer at the right end just under the bar, first in the stack the
  effect chips are in (`Shop.drawMeter`, `Shop.METER`): an onigiri and `Energy.SEGMENTS` (5)
  segments on a dark backdrop, as tall as a chip. It is not part of the bar, so the bar's one row
  (desktop, landscape phone) and two rows (portrait) are as they were. Tapping the onigiri opens Items.
- **Lines wait their turn**: the hint, the peckish line and a stamp earned by "buy & use now" go
  into `shop.notices` and are toasted by the same 250 ms timer as "X wore off", never over another
  toast or an open list. Eating or a cup of water drops a queued peckish line.
- **The safety net** (a player cannot be left unable to eat): an empty meter costs only the sprint;
  a konbini's **water cooler** (`office-watercooler`, the `water` rule in `Interactions.js`; eight of
  the eleven 7-Elevens have one in a back corner) gives a free cup on a bump, `+Energy.WATER` (20)
  up to `Energy.WATER_CAP` (40) - enough to sprint again, never enough to be well fed; the
  cheapest thing sold is a ¥160 Green Tea; and money comes back from the stamp card, a friendly
  nomikai round (¥100, no stake) and selling fish.
- **Debug**: the debug menu's `fast hunger` row multiplies the drain by `Energy.DEBUG_FACTOR` (30;
  `shop.energyDrain`). It is not saved.

**The stamp card** (menu -> Stamp Card, `GameScene.showStampCard`; it is the achievements overlay's
kind of panel and closes the same way). Buying anything stamps the place, once:

- a store - any konbini or Don Takote, by room key (`Stamps.isStore`, the same test as
  `Interactions`' konbini; the till and the shelves both count);
- the vending machines of an area - `vending:<room>`, the district underfoot in the stitched city
  (so Market's machines are one stamp, Park's another);
- the izakaya bar gives no stamp.

The card lists every store from config (`Stamps.stores(config)`), so a new town's konbini is on it
with no code change. Rewards are paid when the count of stamps reaches a milestone
(`Stamps.MILESTONES`; stamps only add up, so there is no "claimed" record) and the purchase toast
says so:

| Stamps | Reward |
|---|---|
| 2 | ¥200 back |
| 5 | a free Onigiri |
| 8 | ¥500 back |
| 12 | ¥1,000 back and a free Nikuman |

**Konbini Pilgrim** (`AchievementManager.stampProgress()`, listed in the Achievements overlay) is a
stamp from every store in config; vending areas do not count towards it.
