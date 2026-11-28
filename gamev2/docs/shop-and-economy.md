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
| the till in a konbini: a 7-Eleven's `konbini-counter*` (any cell of the counter nook, the clerk drawn into it), Don Takote's `office-counter*` | `counter` — every vending + counter item |
| the 7-Eleven kiosk inside a station (`station-kiosk*`, any cell of the booth; see "The station interior") | `counter` — the same list |
| the 7-Eleven kiosk in an airport hall (the same booth and rule) | `counter` — the same list; no stamp |
| the pub's bar in an airport lounge (`airport-bar*`, issue #218) | `pub` — the izakaya's drinks and food, titled AIRPORT PUB; buys no fish, no stamp |
| the bar of the pub in Sendai (`pub-in-bar*`, any cell of it, bumped from the stools' side; `tools/generate_pub.py`, issue #217) | `taproom` — THE PUB: Highball, Nama Beer, Edamame, Karaage (the izakaya's list); buys no fish, no stamp. `pub` is the airport's bar, so each keeps its own title |
| the tasting counter of the Nikka distillery in Sendai (`distillery-in-counter*`, any cell of it, bumped from the stools' side; `tools/generate_distillery.py`, issue #217) | `tasting` — TASTING BAR: a Highball and nothing else; buys no fish, no stamp |
| the hot-drinks tent in Sapporo's Odori Park (`snowfest-stall-drinks*`, any cell of the tent, issue #219) | `stall` — Canned Coffee and Green Tea, titled HOT DRINKS; no stamp |
| the counter (`office-counter2*`) of a shop floor (`Shop<Town><n>`, `"shopMenu": "souvenirs"` / `"crab"` / `"drugstore"` / `"bar"`, issue #219) | that list — OMIYAGE: Green Tea, Ramune, Melon Pan; CRAB SHOP: Onigiri, Nikuman; DRUGSTORE: Zone Energy, Green Tea, Canned Coffee; KARAOKE BAR (Susukino's karaoke bar): Highball, Nama Beer, Edamame; no stamp, buys no fish |
| a counter of Susukino's ramen alley in Sapporo (`susukino-ramen-stall-a*` / `-b*`, any cell of the counter, bumped from the alley, issue #219) | `ramen` — RAMEN ALLEY: Karaage, Edamame, Nama Beer; no stamp, buys no fish |
| three shopfronts of an underground arcade (`chika-shop-bakery*` / `-kissa*` / `-bar*`, any cell of the front, `tools/generate_chikagai.py`) | `bakery` — BAKERY: Melon Pan, Nikuman, Canned Coffee; `kissa` — KISSATEN: Canned Coffee, Green Tea, Melon Pan; `standbar` — STAND BAR: Highball, Nama Beer, Edamame, Karaage; no stamp, buys no fish |
| a 7-Eleven's drinks coolers (`office-fridge`) and coffee machine (`konbini-coffee`); `office-shelf-drinks` / `-shelf-glass` / `office-freezer` in Don Takote | `drinks` — the drinks only |
| a 7-Eleven's open chillers (`konbini-chiller-a` / `-b`) and its snack, noodle and bread shelf blocks (`konbini-gondola-snacks` / `-noodles` / `-bread`); `office-shelf-snacks` in Don Takote | `snacks` — the food only |
| the rest of a 7-Eleven (issue #221) | the dispenser on the back wall (`konbini-water`) pours a cup of water; the wall clock (`konbini-wall-clock`, bumped from the floor under it) opens Time Travel; the cash machine, the copier, the magazine rack, the ice-cream chest and the sundries shelf block (`konbini-gondola-daily`) say a line; the baskets and the plain wall do nothing |
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
  `shop-sealed-floor` when a store has bare floor the door does not lead to (issue #182: a corner
  water dispenser once stood a row below the back wall and boxed in the cell above it; nothing in a
  7-Eleven stands off the wall like that now, and `generate_konbinis.py` refuses a plan that leaves
  floor the door does not reach: `Interior.room()` in `tools/interiors.py`, for every interior on it).
  `play.js check` reports every room's lint errors too (`WorldModel.lintProblems`, issue #178), so a
  store cut off from its door shows up there as `KonbiniMarket1: lint shop-no-front: ...`.
  `check` exits 1 when it lists any problem, like `lint` (issue #188), so a script or CI step can gate on it.
  The Tokyo city has no open cell that cannot be walked to (issue #196): the yard behind the Tokyo
  shrine hall, the floor under Market's wing roofs and the odd cell boxed in by bushes or lanterns carry
  a `gk_blank` collider, so nothing can place anyone there (unit-tested on the stitched city). Lint's
  `stray-collision` skips a bare collider that no walkable cell touches, which is what those are.
  `generate_konbinis.py` lays a 7-Eleven out like a Pokémon Mart (issue #221): everything that sells
  from its front stands against the back wall or is a shelf block with an aisle below it, the till is
  a nook in a back corner, and the bottom row is open but for the baskets and the magazines by the
  door - see "Konbini interiors" in `landmarks-and-towns.md`. Keep NPC spots and
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
  starts; Bailey mirrors the head start, so his +10 gimmick survives),
  `focus` (seconds on the work clock, read by `Career`, locked in when a shift
  starts; Canned Coffee carries 5), plus `secs`.
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
  the shrine's offering (¥5; the temple's box and a pagoda's are the same offering) and fortune (¥100): neither is a purchase, so neither feeds the energy meter
  nor stamps the Stamp Card. And `guestbook: {date, n}` once the palace's visitors' book has been signed
  (`PalaceVisit`, see "The palace's audience hall" there; `Shop.guestbookOf`): the day it was last signed and
  how many times in all. And `career: {merged, shifts, earned}` once the reception desk of a tower lobby has
  signed you on (`Career`, see "Career" below; `Shop.careerOf` keeps a whole one and drops anything else, so a
  dented field is no job, never a crash): lifetime tickets merged, shifts worked and yen earned at the job.
  All three fields are absent until used, and a blob without them loads and saves unchanged.
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

### Career: a job in the office towers (issue #226)

A way to earn that is not fishing: a software job in the tower lobbies (`src/Career.js`; the lobbies
are in "Tower lobbies" in `landmarks-and-towns.md`). Code only: the desk and the lifts were already
there, in every lobby, and a lobby built later has the job without an edit. One go at it is a
**shift**, in the code, the copy and here - never a sprint, because SHIFT sprints.

- **The loop**: bump the **reception desk** and you are signed on (a toast; the saved `career` is the
  staff pass, and from then on the desk reads your title back: `Career.signOn`, `Career.status`). Bump
  a **lift** with the pass and the overlay opens on its ready screen; without it a toast points at the
  desk. The building directory says who is hiring. All three are rules in `Interactions.RULES` (the
  desk and the lift in group `career`, kinds `desk` and `lift`; the directory is still `flavour`).
  One answer per bump: a key held against the desk is the same bump until it is let go
  (`ShrineVisit.fresh` / `.held`, the offering box's rule). The lift's bump waits while the overlay is
  open (`Career.hold`): left with the lift's direction still down, it is not opened again.
- **A shift** is `Career.TICKETS` (5) tickets against a clock. A ticket is a commit line
  (`Career.TICKET_NAMES`, five different ones a shift) and a row of arrows (`Career.sequence`: never
  three the same running); press them in order with the arrows, WASD or the d-pad. A wrong press
  flashes BUILD FAILED and the row starts again, which costs time and nothing else. Every ticket
  merged pays the level's `pay`; all five before the clock runs out is a **clean shift**, which ends
  there and pays the level's `bonus` on top. ESC clocks off and keeps what was merged; so does the
  clock running out. The money reaches the wallet once, when the shift ends (`Career.settle`, one
  `shop.save()`), and nothing is saved while it runs. It costs nothing to start and nothing to fail:
  no energy, no stake.
- **The ladder** (`Career.LEVELS`; `Career.levelOf(merged)` is the row, `Career.next` the promotion
  ahead). Lifetime tickets merged decide the title; the title is locked in as a shift starts, so a
  promotion earned mid-shift shows on the result (`PROMOTED: ...`) and pays from the next one.

  | Title | from tickets | row | clock | a ticket | clean bonus | a clean shift |
  |---|---|---|---|---|---|---|
  | Intern | 0 | 3 | 20 s | ¥10 | ¥30 | ¥80 |
  | Junior Engineer | 10 | 4 | 20 s | ¥20 | ¥50 | ¥150 |
  | Engineer | 25 | 5 | 25 s | ¥35 | ¥75 | ¥250 |
  | Senior Engineer | 50 | 6 | 30 s | ¥55 | ¥100 | ¥375 |
  | Staff Engineer | 90 | 7 | 35 s | ¥80 | ¥125 | ¥525 |
  | Principal Engineer | 150 | 8 | 40 s | ¥110 | ¥200 | ¥750 |

- **The clock** is one second an arrow, never under twenty: `Career.clockMs(len, focus)` =
  max(`MIN_CLOCK_MS`, `TICKETS` x `len` x `ARROW_MS`) + `focus` seconds. Every level asks the same
  pace; what gets harder is how much a miss throws away. **Canned Coffee** adds 5 s (the `focus`
  effect kind, beside its speed; locked in as the shift starts, and the ready screen says so).
- **Judging** is on directions, not keys, and is one pure function, `Career.press(seq, at, dirs,
  held)`, where `dirs` went down this frame and `held` were down already:
  1. no direction: nothing;
  2. more than two, or two opposite ones: a miss (slapping every key is not an answer; a
     perpendicular pair is what the d-pad sends for a touch on a diagonal);
  3. the one wanted is among them: a step, and the last step of a row merges the ticket;
  4. the arrow just typed is still held and every direction is across it: nothing (a thumb rolling
     off the arrow it pressed into the next diagonal - the d-pad sends a keydown for it and it was
     never a press);
  5. anything else: a miss.

  All the overlay's keys are read in one place, every frame it is up (`Career.read`, the only
  `JustDown` in the file), so no press outlives its screen (#220): an arrow tapped on the ready
  screen is not the first press of the shift, and the SPACE that starts one is not read again.
- **Balance**, by the model the ladder was priced from: a clean shift is `5 x len` presses, at 3 a
  second on a keyboard or 1.5 a second with a thumb on the d-pad, plus 2 s for the result and ready
  screens.

  | Title | a clean shift | keyboard | thumb | per minute, keyboard | per minute, thumb |
  |---|---|---|---|---|---|
  | Intern | ¥80 | 7 s | 12 s | about ¥700 | about ¥400 |
  | Junior Engineer | ¥150 | 9 s | 15 s | about ¥1,050 | about ¥600 |
  | Engineer | ¥250 | 10 s | 19 s | about ¥1,450 | about ¥800 |
  | Senior Engineer | ¥375 | 12 s | 22 s | about ¥1,900 | about ¥1,000 |
  | Staff Engineer | ¥525 | 14 s | 25 s | about ¥2,300 | about ¥1,250 |
  | Principal Engineer | ¥750 | 15 s | 29 s | about ¥2,900 | about ¥1,550 |

  The whole ladder is 150 tickets: 30 clean shifts, about 6 minutes on a keyboard and 11 with a
  thumb, and ¥11,160 earned on the way up. For scale: a FRIENDLY nomikai round is about ¥300 a
  minute, fishing about ¥2,500 a minute once you are at a pond with bait, and a BIG TAB win ¥2,000
  for a 15 s round with ¥2,000 at risk. So an Intern earns more than the free round and less than
  half of fishing, and only a Principal on a keyboard passes it. Pay per key press rises with
  every step, with and without the bonus, so a promotion is never a pay cut; `career.test.js` holds
  the table to that and pins its two ends and the ¥11,160.
- **Where it shows**: the menu's **Career** row (`GameScene.showCareer`, the achievements
  overlay's panel, as the Stamp Card is) - before you are hired, the towns with a tower that is
  hiring (`Career.where(config)`: every room with a `lobby`, named by its town); after, the title,
  tickets merged, shifts worked, yen earned, what is left to the next title and the whole ladder
  with your step picked out. Two achievements (`AchievementManager.careerProgress()`, listed in the
  Achievements overlay): **First Paycheck** (merge a ticket) and **Principal Engineer** (reach the
  top of the ladder), toasted once from the shift that earns them.
- **Phones**: the row is at most 8 arrows of `Career.CELL` (56) canvas px, 448 of the panel's 760;
  every hint goes through `Hints.text` (`A to start    B to leave`, `d-pad to type    B to clock
  off`).
- **To add a job** (design, say): it is a second ladder and a second set of ticket names, not a
  second game. Give `LEVELS` and `TICKET_NAMES` a key per job, keep the job's key in the saved
  `career`, and let the desk's rule (or a second desk kind in `Interactions.RULES`) say which one
  it signs you on for; `press`, `clockMs`, `settle` and the overlay do not care what the tickets
  are called. To take the job out again, the list is at the top of `src/Career.js`.
- Tests: `tools/tests/career.test.js` (the ladder and the balance model, the clock, the five
  judging rules, the key reader, whole stubbed shifts - clean, a miss, clocked off, time up,
  promoted - the save blob, the coffee, the card, the achievements, every lobby's desk and lifts in
  the world model); the browser regression's `career-shift` (a whole shift with real keys in a
  real lobby), `menu-entries` (the Career card) and `phone-landscape-touch` (a ticket typed on the
  d-pad, a thumb rolled into a diagonal, B clocks off).

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
| Low, `<= Energy.LOW` (25) | nothing changes; the meter is red. The first time ever it gets here a hint is toasted (`Energy.HINT`, remembered in the save as `hints.low`). |
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
- **A toast is one line, except where a phone cannot show that line at 10 CSS px** (#220): `Shop.toast`
  breaks a message too long for the gap between a small landscape phone's touch controls into even
  lines (`Shop.toastLines`, asked of `uiScale.floatWidth`; the toast's font, padding and height above
  the bottom edge are `Shop.TOAST`). At 667x375 that is any message of more than 81 characters: the
  energy hint, the "not that thirsty" water line, a fish's sell line, the longer shrine lines. The
  peckish line fits on one. `shop.toastText()` returns the message as it was said, without the line
  breaks. See [hud-input-touch.md](hud-input-touch.md).
- **The safety net** (a player cannot be left unable to eat): an empty meter costs only the sprint;
  a 7-Eleven's **water dispenser** (`konbini-water`, the `water` rule in `Interactions.js`; every
  7-Eleven has one on its back wall, issue #221) gives a free cup on a bump, `+Energy.WATER` (20)
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
