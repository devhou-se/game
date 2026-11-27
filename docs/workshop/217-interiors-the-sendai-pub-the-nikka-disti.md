# Design: interiors for the Sendai pub, the Nikka distillery and Canal City (#217)

All paths are under `gamev2/` unless they start with `docs/workshop/`. Read `gamev2/CLAUDE.md`,
`docs/landmarks-and-towns.md` ("The palace's audience hall", "The temple's main hall") and
`docs/generators-and-checks.md` first: this ticket is three more rooms of that kind.

This design was reviewed against the code (see Review at the end). The body below is the revised design.

## Context

Three buildings that blog posts are told beside are sealed boxes:

| Building (sprite) | Host | Door cell(s) today | Cell in front |
|---|---|---|---|
| the pub (`sendai-pub_0_0`, 5x5) | `Sendai` | (28,20) | (28,21) |
| the Nikka kiln house (`sendai-kiln_0_0`, 5x6) | `Sendai` | (5,33) | (5,34) |
| Canal City (`canal-city_0_0`, 8x6) | `Fukuoka` | (15,29), (16,29) | (15,30), (16,30) |

(Checked: the sprites stand at Sendai (26,16) and (3,28) and Fukuoka (12,24) on `Collidables`, each door
is drawn in those columns of the art, every door cell has a collider and every front cell is open ground,
on this branch and on `origin/master`.)

The owner wants each to open into an interior:

- **Pub**: a proper pub: a bar with taps, stools, tables, a TV showing the baseball.
- **Distillery**: a small tasting bar with one copper pot still. Nothing major.
- **Canal City**: a simple, bright, multi-level atrium: the canal and fountain through the middle,
  decorative shopfronts, benches and planters. Not a full mall.
- Ordering a drink uses the existing shop list (`Shop.VENUES`). No new items.

## Before you start (do these first, in this order)

1. **Bring the branch up to date with `origin/master`.** When this was reviewed the branch was four commits
   behind: master had gained the konbini redesign (#221: 13 `Konbini*` rooms rebuilt, `tilePalette` grown
   from 769 to 795, new rows in `Interactions.RULES`) and the shrine roll-out (Fukuoka now has doors into
   `ShrineFukuoka1` and `ShrineFukuoka2`). Check with `git merge-base --is-ancestor origin/master HEAD`; if
   it fails, `git merge origin/master` (the branch holds only this design, so it is conflict-free). Never
   generate on the stale base: palette indices are positional, and a room built on 769.. cannot be merged
   with master's 769..794.
2. **Install Pillow**: `pip install --break-system-packages Pillow` (the container has none; without it
   `check_generators.py` lists every art tool as `skip`, which is not a pass, and no art tool runs).
3. **`export PYTHONDONTWRITEBYTECODE=1`** for the whole session. Master tracks
   `gamev2/tools/__pycache__/*.pyc`; running any tool rewrites them and they would be committed as noise.
   If `git status` ever shows them modified, `git checkout -- gamev2/tools/__pycache__`.
4. **Record the baseline of the generator check**, before changing anything:
   `python3 tools/check_generators.py > /tmp/gen-before.log; grep -E '^(DRIFT|skip)' /tmp/gen-before.log`.
   Measured in this container on untouched master with Pillow 13.0.0: every room generator and
   `config_to_tiled` is `ok`, `generate_konbini_art.py` is `ok`, **25 older art tools report `DRIFT`** (their
   committed PNGs were encoded by another Pillow; the pixels are not the point) and 2 are skipped for want
   of a Japanese font. That drift is not yours and **must not be "fixed"**: never commit a re-run of an
   existing art tool. The gate for this ticket is in Tests.

## Approach

Three bespoke interiors on the palace (#215) / temple (#213) pattern, **one commit per room**, in this
order: pub, distillery, Canal City. Each commit is complete on its own (generator, art, door, rules,
tests, docs, the gate in Tests met). **Commit each room as soon as it is green**; do not hold the three
for one push at the end, so a run that is cut short leaves finished rooms behind.

Per room: a generator `tools/generate_<x>.py` rebuilds the room from scratch (keeping its NPCs), finds the
building in its host **by sprite**, removes the collider on the door cell(s) and wires a hidden
transporter there, replaced in place so a re-run is byte-identical. An art tool
`tools/generate_<x>_art.py` draws the kit. A row in `roomgen.OWNED_DOORS` makes `generate_sendai.py` /
`generate_fukuoka.py` keep the door through a town rebuild, so **neither town generator is edited**.
(Verified in review: with the three doors opened onto stand-in rooms and the three `OWNED_DOORS` rows
added on a scratch copy of master, `check_generators.py` reproduces the world, so the town generators do
keep the doors.)

Decisions taken here (none needs the owner):

- **Drinks**: two new venues over the existing catalogue, opened by bumping the bar sprite (a rule per
  sprite, as the airport pub and the arcade's stand bar do). No stamp, no fish bought, no new save data,
  no new JS file, no `GameScene.js` change.
- **Light**: the pub and the distillery are `lanternLight` (dim and warm at night, lamps and the TV glow).
  The atrium is plain `interior`: never graded (`DayNight.gradeFor`), so it is bright at any hour.
- **The canal is drawn art** (`mall-in-canal-*`), not `pond-autotile`: no fishing indoors (the `pond` rule
  matches `/^pond-autotile/` only).
- **Julia's post 727 stays outside**, at Fukuoka (14,30) beside the doors. Interiors offer the blog
  pipeline nothing (`find_spots`: "`interior` rooms offer nothing"), every other landmark with an interior
  keeps its post outside, and she is 2 cells from the nearest door, which is what `NPCManager.atDoorway`
  and the pipeline's `area_cell` ask for. The fountain's line nods to her "water performance" instead.
  Post 505 (Bailey, the baseball) stays at the castle ruins and post 501 (Julia) beside the pub door; the
  TV's line is post 505's own ("some guy next to us went full gold-chain Eagles superfan and we clapped
  along").
- **TV and fountain are static sprites** (the game has no tile animation); the TV gets a slow glow at
  night.

### What each room must have, and what may be cut

Art is the bulk of the work. If the budget runs short, cut from the "may be cut" column, never from the
first; a cut piece also loses its rule, its test line and its doc line.

| Room | Must have (the ticket) | May be cut |
|---|---|---|
| Pub | bar with taps, back bar, stools, tables and chairs, the TV with the baseball, hung lamps | darts, chalkboard, booths |
| Distillery | tasting counter and shelf, stools, the one copper pot still, hung lamps | racked casks on the wall, floor casks, the window |
| Canal City | the two gallery levels on the back wall, the canal, the fountain, both bridges, shopfronts, benches, planters | palms; the five shopfronts may be three designs repeated |

## Changes

### Shared (lands with the pub commit)

`tools/roomgen.py`

- Constants beside `TEMPLE_*`, and three rows in `OWNED_DOORS`:

  ```python
  PUB_DOORS = {'sendai-pub_0_0': [(2, 4)]}
  PUB_PREFIX = 'Pub'                    # rooms.Pub<Host><n>
  DISTILLERY_DOORS = {'sendai-kiln_0_0': [(2, 5)]}
  DISTILLERY_PREFIX = 'Distillery'      # rooms.Distillery<Host><n>
  MALL_DOORS = {'canal-city_0_0': [(3, 5), (4, 5)]}
  MALL_PREFIX = 'Mall'                  # rooms.Mall<Host><n>
  # OWNED_DOORS: PUB_PREFIX: ('pub', PUB_DOORS), DISTILLERY_PREFIX: ('distillery', DISTILLERY_DOORS),
  #              MALL_PREFIX: ('mall', MALL_DOORS)
  ```

  Add each row in the commit of its room. `owned_door` matches by `startswith`: no room key on master
  starts with `Pub`, `Distillery` or `Mall`.
- Two helpers, used by the three new generators only (palace and temple keep their own copies):
  - `sprite_doors(cfg, host, table)` -> sorted `[(door cell, cell in front)]` for every sprite of `table`
    found on `DOOR_LAYERS` of `host` (the loop in `generate_palace.py` `towers()`).
  - `open_doors(cfg, host, key, doors, arrive)`: for each door, pop its `Colliders` tile and put
    `transporter(dx, dy, key, *cell, hidden=True)` in place, or append (the tail of `generate_palace.py`).

Every generator below: `rg.cli(__doc__, sys.argv[1:])`, `HOST`, `KEY = f'{rg.<X>_PREFIX}{HOST}1'`,
`NAME` (11 characters or fewer), the palace's frame (`OX, OY = 1, 4`; `W, H = FW + 2, FH + 7`; row 0 dark,
a 3-row solid back wall on `Collidables`, side walls / front wall / thresholds on `Floor`, `doorlight` on
`Non-Collidables`, `b.fill('office-void-autotile')`), the `put` / `solid` / `stand` closures copied from
`generate_palace.py`, a `boundary` polygon of the floor plus the doorway cells, the marker
`room[<marker>] = {'host': HOST, 'doors': [...]}`, `interior = True`, `shopEnabled = False`, an assert
that **exactly one** building of that sprite was found in the host, and an assert that every floor cell
that is not solid is reachable from the door (as `generate_chikagai.py` does). That assert is the only
guard the atrium has: `play.js lint`'s `shop-sealed-floor` runs only in a room with a shop fixture, so it
covers the pub and the distillery and is silent in the mall. Exits lead to the cell in front of the
outside door; you arrive one row inside, never on an exit cell. Coordinates below are floor cells (`fx`,
`fy`); a piece may move a cell if lint or the art needs it, as long as the invariants in Tests hold.
`Builder` refuses a room smaller than 20x15; all three are at or above it.

Every art tool: Pillow, the manner and header of `generate_palace_art.py` (32 px a cell, pixel-doubled,
ink outline, seeded, no text except in the game's own fonts, `--preview out.png`), registers
`<prefix>-in-<piece>_0_0` in `spriteMetadata` + `tileNames` and **appends to `tilePalette` at its current
end** (795 on master when reviewed; read the length, never hard-code it, never reorder). To keep three
tools from tripling the work:

- The frame pieces (floor a/b, side walls, front wall, thresholds, doorlight) are one set of functions
  that take a palette. Write them in `generate_pub_art.py`; the other two tools may import them, the way
  `generate_fukuoka_town_art.py` imports from `generate_sendai_town_art.py`. An art tool must do nothing
  on import (`if __name__ == '__main__':`), or importing it rewrites its PNGs.
- The mall's shopfronts are one function driven by a table (name, colours, what is in the window), as
  `generate_chikagai_art.py` draws its fronts.

### 1. The pub: `PubSendai1`, name `The Pub`, 20x17 (`FW, FH = 18, 10`)

Add `tools/generate_pub.py`, `tools/generate_pub_art.py` (sprites `pub-in-*`), `tools/tests/pub.test.js`,
`tiled/pubsendai1.tmj`. `lanternLight = True`. Marker `pub`. Doorway: `fx` 8..9 on row `FH`, both cells
exit to Sendai (28,21); arrive at `fx` 8, `fy` 9.

| Piece (`pub-in-…`) | Size | Where | Notes |
|---|---|---|---|
| `floor-a` / `floor-b` | 1x1 | whole floor | dark boards |
| `side-w` / `side-e`, `wall-front`, `threshold-w` / `-e`, `doorlight` (2x3) | | frame | wood panelling |
| `wall-backbar` | 7x3 | back wall, `fx` 0..6 | bottle shelves, mirror, optics |
| `wall-tv` | 4x3 | back wall, `fx` 10..13 | a big screen: the diamond, a batter, a score bug |
| `wall-darts` | 2x3 | back wall, `fx` 15..16 | dartboard and chalk scores |
| `wall-panel` | 1x3 | the other back-wall columns (`fx` 7..9, 14, 17) | wainscot, framed prints |
| `bar` | 7x2 | `fx` 0..6, `fy` 0..1, **all solid**, flush to the west wall | back row is the staff aisle, front row the counter with three beer taps and a till |
| `stool` | 1x1 solid | `fy` 2 at `fx` 1, 3, 5 | leaves 0, 2, 4, 6 free to reach the bar |
| `table` | 2x1 solid | (3,5), (3,8), (12,4) | pints on them |
| `chair` | 1x1 solid | one each side of each table | |
| `booth` | 2x3, **all solid** | east wall, `fx` 16..17, `fy` 3..5 and `fy` 6..8, back to back | high-backed bench and table |
| `chalkboard` | 1x2, foot solid | (0,8) | the specials |
| `lamp-hang` | 1x2 on `Tops` | over the bar (above `fx` 1, 3, 5) and each table | |

The bar is flush to the side wall so there is no one-cell pocket at its end where the player could stand
on the staff's side. The booths are solid in every row: with only the foot row solid the player could
stand inside the table.

### 2. The distillery: `DistillerySendai1`, name `Distillery`, 20x15 (`FW, FH = 18, 8`)

Add `tools/generate_distillery.py`, `tools/generate_distillery_art.py` (sprites `distillery-in-*`),
`tools/tests/distillery.test.js`, `tiled/distillerysendai1.tmj`. `lanternLight = True`. Marker
`distillery`. Doorway `fx` 8..9, both exit to Sendai (5,34); arrive at `fx` 8, `fy` 7.

| Piece (`distillery-in-…`) | Size | Where | Notes |
|---|---|---|---|
| `floor-a` / `floor-b` | 1x1 | whole floor | stone flags |
| frame pieces as the pub | | | red brick |
| `wall-brick` | 1x3 | back wall filler (`fx` 4..6, 9..12) | |
| `wall-window` | 2x3 | back wall, `fx` 7..8 | arched window |
| `wall-casks` | 4x3 | back wall, `fx` 0..3 | casks racked three high |
| `wall-shelf` | 5x3 | back wall, `fx` 13..17 | bottles behind the counter |
| `still` | 3x4 | `fx` 4..6, `fy` 0..3; rows `fy` 2..3 solid | one copper pot still: pot, swan neck, lyne arm; the neck is walked behind |
| `counter` | 5x2 | `fx` 13..17, `fy` 0..1, **all solid**, flush to the east wall | tasting counter, glasses poured, staff aisle behind |
| `stool` | 1x1 solid | (14,2), (16,2) | leaves 13, 15, 17 free |
| `cask` | 1x1 solid | (0,4), (1,4), (0,6) | on end |
| `lamp-hang` | 1x2 on `Tops` | over the counter and the still | |

### 3. Canal City: `MallFukuoka1`, name `Canal City`, 28x23 (`FW, FH = 26, 14`)

Add `tools/generate_mall.py`, `tools/generate_mall_art.py` (sprites `mall-in-*`),
`tools/tests/mall.test.js`, `tiled/mallfukuoka1.tmj`. No `lanternLight`. Marker `mall`. The frame differs
in one way: the back wall is **5 rows** (`OY = 6`, `H = FH + 9`): the top two rows of every back-wall
piece are two gallery levels (curved terracotta balconies, railings, small lit fronts), the bottom three
the ground floor. Doorway `fx` 12..13: the west cell exits to Fukuoka (15,30), the east to (16,30); the
west outside leaf arrives at `fx` 12, the east at `fx` 13, `fy` 13.

| Piece (`mall-in-…`) | Size | Where | Notes |
|---|---|---|---|
| `floor-a` / `floor-b` | 1x1 | whole floor | pale stone, a terracotta band beside the canal |
| `side-w` / `side-e`, `wall-front`, `threshold-w` / `-e`, `doorlight` | | frame | side walls show the gallery ends |
| `wall-pier` | 1x5 | back wall, `fx` 0, 5, 10, 15, 20, 25 | |
| `front-fashion`, `front-toys`, `front-okonomiyaki`, `front-cafe`, `front-ramen` | 4x5 | back wall, `fx` 1, 6, 11, 16, 21 | decorative shopfronts under the galleries; one function, a table |
| `canal-n-a/-b`, `canal-a/-b`, `canal-s-a/-b` | 1x1 on `Floor` | `fy` 5, 6, 7, every `fx` not under the fountain; **solid except in the bridges' columns** | water with stone edges; the water runs on under the bridges |
| `bridge` | 2x3 on `Non-Collidables`, walkable, `depthBias: -200` | `fx` 4..5 and 20..21, `fy` 5..7 | lies flat under whoever crosses, exactly as `dazaifu-bridge_0_0` and `matsushima-pier_0_0` do (the art tool writes `depthBias`, as `generate_fukuoka_art.py`'s `FLAT` does) |
| `fountain` | 4x3 solid on `Collidables` | `fx` 11..14, `fy` 5..7 | basin and jets, in the canal |
| `palm` | 1x2, foot solid | (2,3), (23,3), (8,9), (17,9) | planter palm |
| reused `station-bench_0_0` / `station-bench-back_0_0`, `station-planter-a_0_0` / `-b_0_0` | 2x2 each, solid | benches along the south bank (foot row `fy` 9) facing the canal, planters at the row's ends and by the doors | no new art; they are 2x2, so lay the row out for that and keep palms clear of them |

The canal should look like the canal the #219 rebuild will lay outside: `assets/sprites/fukuoka-canal_0_0.png`,
`fukuoka-canal-jets_0_0.png` and `fukuoka-canal-bridge_0_0.png` are already on disk (drawn by
`generate_fukuoka_town_art.py`, not yet registered). Look at them and match the quays and the water. Do
not register or place those sprites here: they belong to that tool and to #219.

### Files touched in every commit

- `config.json`, `tiled/<room>.tmj`, `tiled/sendai.tmj` or `tiled/fukuoka.tmj`
  (`python3 tools/config_to_tiled.py <Room> <Host>`), `assets/sprites/*.png` (**only** new `pub-in-*`,
  `distillery-in-*`, `mall-in-*` files).
- `tools/check_generators.py`: the generator in `GENERATORS` (after `generate_temple`, so after the town
  generators and before `districts`), the art tool in `ART_TOOLS`.
- `src/utils/Interactions.js`, `src/Shop.js`, `src/utils/Glows.js`: see Data and interfaces.
- `tools/tests/sendai.test.js` (pub and distillery commits): in "Sendai: every landmark is there and can
  be walked to from the station door (#66)", `doorway()` also accepts a cell that carries a hidden
  transporter into a room whose `pub` or `distillery` marker has host `Sendai` and lists that cell.
- `tools/tests/fukuoka.test.js` (mall commit): the "only ways out of town" list (in "Fukuoka: Hakata
  station is a main-line stop…") becomes, on master,
  `['FukuokaStation', 'KonbiniFukuoka1', 'MallFukuoka1', 'MallFukuoka1', 'ShrineFukuoka1', 'ShrineFukuoka2']`
  (it is sorted; add the two `MallFukuoka1` to whatever the list is after the merge) and its comment says
  so.
- Docs: `docs/landmarks-and-towns.md` gets one section per room in the format of "The temple's main hall"
  and the three landmark-table rows say the building opens. The pub's section also says why these three
  did not wait for the rebuild although "Senso-ji only, for now" says temples do: their doors are found
  by sprite, and what the rebuild owes them (see Risks). `docs/shop-and-economy.md` gets the two venue
  rows; `tools/generate_izakaya.py`'s header note is untouched.
- Not touched: `generate_sendai.py`, `generate_fukuoka.py`, `blog_to_npc.py`, `test_blog_to_npc.py`,
  `devhouse.world`, `index.html`, `GameScene.js`, `world-model.js` (the palace and temple commits edited
  it only to add a new interaction group; these rooms use `shop` and `flavour`), `assets/map`, any NPC
  placement, any existing PNG, `tools/__pycache__`.

Verified in review on a scratch copy of master with the three doors opened: the two tests named above are
the only ones in `node tools/test_game.js` that fail; `test_blog_to_npc.py`, `play.js check` and
`sync_cities.py --check` pass unchanged.

## Data and interfaces

`config.json` rooms (new): `PubSendai1`, `DistillerySendai1`, `MallFukuoka1`, each with `interior: true`,
`shopEnabled: false`, a `boundary`, and its marker (`pub` / `distillery` / `mall`:
`{host, doors: [[x, y], …]}`). Hosts gain hidden transporters: Sendai (28,20) -> `PubSendai1`, Sendai
(5,33) -> `DistillerySendai1`, Fukuoka (15,29) and (16,29) -> `MallFukuoka1`. `spriteMetadata` for
`mall-in-bridge_0_0` carries `depthBias: -200`. No save-format change.

`src/Shop.js` `Shop.VENUES`:

```js
// the pub in Sendai and the distillery's tasting bar (issue #217): over the bar; no stamp, no fish bought.
// (`pub` above is the airport's bar; this one is `taproom` so each keeps its own title.)
taproom: { title: 'THE PUB',     sells: i => i.where === 'izakaya' },
tasting: { title: 'TASTING BAR', sells: i => i.id === 'highball' },
```

`src/utils/Interactions.js` `RULES` (shop rows beside `standbar`, flavour rows beside the temple's; all
`footprint: true`; the first matching rule wins and none of these patterns is matched by an earlier row):

| kind | group | pattern | say |
|---|---|---|---|
| `taproom` | shop | `/^pub-in-bar/` | |
| `tasting` | shop | `/^distillery-in-counter/` | |
| `baseball` | flavour | `/^pub-in-wall-tv/` | the baseball is on. a man in a gold chain claps for the Eagles and the bar claps with him |
| `darts` | flavour | `/^pub-in-wall-darts/` | three darts in the wall, none in the board. nobody is owning up |
| `specials` | flavour | `/^pub-in-chalkboard/` | today's special is fish and chips. it has been today's special for some years |
| `pot-still` | flavour | `/^distillery-in-still/` | a copper pot still, warm to the hand. whatever is in it will be ready in about twelve years |
| `casks` | flavour | `/^distillery-in-(wall-casks\|cask)/` | the casks are asleep. the chalk on the nearest one says not before 2037 |
| `mall-fountain` | flavour | `/^mall-in-fountain/` | the jets rest between shows. the next water performance starts just after you leave |
| `mall-fashion` | flavour | `/^mall-in-front-fashion/` | winter coats in the window, in sizes for somebody smaller |
| `mall-toys` | flavour | `/^mall-in-front-toys/` | a wall of capsule toys and plushies. the big one is not for sale |
| `mall-okonomiyaki` | flavour | `/^mall-in-front-okonomiyaki/` | okonomiyaki, made in front of you. the queue says it is good. opinions differ |
| `mall-cafe` | flavour | `/^mall-in-front-cafe/` | the cafe has a queue for the queue |
| `mall-ramen` | flavour | `/^mall-in-front-ramen/` | the ramen stadium is five floors up. the escalator is part of the wall |

A bump fires only on a blocked step (`Character.js`), so walking behind the still's neck or the
chalkboard's head says nothing; the line comes from pushing into a solid cell of the piece.

`src/utils/Glows.js` `Glows.SPRITES` rows (pub and distillery only): `pub-in-lamp-hang_0_0` and
`distillery-in-lamp-hang_0_0` (warm, as `palace-in-lamp-hang`), `pub-in-wall-backbar_0_0` (`WARM`, wide and
low), `pub-in-wall-tv_0_0` (`COOL`, `pulse: { period: 2600, depth: 0.25 }`: a slow swell in the range the
table already uses, not a strobe), `distillery-in-wall-window_0_0` (`COOL`, faint).

## Tests

New `tools/tests/pub.test.js`, `distillery.test.js`, `mall.test.js`, each modelled on
`tools/tests/temple.test.js` (unique test names). **No test hard-codes a host coordinate**: every door,
front cell and post cell is derived from where the building's sprite stands, so the #219 rebuild can move
the building without editing these files.

- The host door cell(s) are found by sprite, walkable, carry a hidden transporter into the room; arrival is
  free floor and not an exit; every exit leads to the cell in front of its outside door; walking in and
  straight back out returns you there.
- On every trip date no NPC stands on a door or its front cell and no wanderer can reach them. The posts
  beside the doors stay on their landmark's stand cell, sprite origin plus `LANDMARKS`' offset: pub
  (3,5), kiln (3,6), Canal City (2,6) (today Sendai (29,21) and (6,34), Fukuoka (14,30) for post 727).
- Every non-solid floor cell is reachable from the door (the test does its own flood fill: lint does not
  check this in the mall); the bar / counter, every flavour piece, both canal banks and both bridges have
  a reachable side; `node tools/play.js lint <Room> <Host>` is clean.
- `Interactions.match`: the bar opens `taproom` / `tasting`; each flavour sprite says its line (100
  characters or fewer); the mall has no `shop` and no `pond` interaction.
- `Shop.VENUES.taproom` sells exactly Highball, Nama Beer, Edamame, Karaage; `tasting` exactly Highball;
  neither `buys`; `Stamps.placeFor(kind, KEY, room) === null`.
- Flags: pub and distillery `lanternLight`, mall not; `shopEnabled === false`; `name.length <= 11`,
  `hudBrief(NAME) === NAME`, `Places.whereText` gives `The Pub (in Sendai)`, `Distillery (in Sendai)`,
  `Canal City (in Fukuoka)`; `spriteMetadata['mall-in-bridge_0_0'].depthBias === -200`.
- Generator plumbing: listed in `check_generators.py`; the `OWNED_DOORS` row is in `roomgen.py` (a text
  match, as `chikagai.test.js` does); the marker equals the host's transporters; palette entries appended;
  every sprite on disk, whole cells, placed; and, on a scratch copy as `temple.test.js`'s last test does,
  a re-run of the room's own generator is byte-identical and rebuilding the interior from a re-sealed host
  gives the same world. That a re-run of `generate_sendai.py` / `generate_fukuoka.py` keeps the door is
  what `check_generators.py` proves; the JS tests do not spawn the town generators again.

Run from `gamev2/` before each commit:

```bash
export PYTHONDONTWRITEBYTECODE=1
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py > /tmp/gen-after.log; grep -E '^(DRIFT|skip)' /tmp/gen-after.log
python3 tools/sync_cities.py --check
node tools/play.js lint PubSendai1 Sendai        # and the other rooms / hosts
node tools/play.js render PubSendai1 /work/media/pub.png
python3 -m http.server 8000 &                    # then, per tools/browser/README.md:
PORT=8000 node tools/browser/regress.js
git status --short                               # nothing under tools/__pycache__, no existing PNG modified
```

**The generator gate**, since the container's Pillow makes older art tools drift: the `DRIFT` / `skip`
lines after the change are exactly the baseline's (step 4 of "Before you start"), every room generator
and `config_to_tiled` is `ok`, and each new art tool (`generate_pub_art`, `generate_distillery_art`,
`generate_mall_art`) is `ok`. A new `DRIFT` line, or a baseline one that vanished because its PNGs were
re-encoded, is a failure. Say in the result that the three new art tools were encoded by the container's
Pillow and may show as `DRIFT` on the owner's machine, as #221's did.

Then play each room in a browser at desktop size and at 667x375 with `?touch=1`, by day and with
`?tod=night`: walk in from the street, buy a drink at each bar, bump every flavour piece, cross both
bridges, leave by each door. The trip is in Sendai on `?date=2025-10-29` (Julia stands by the pub door,
Damian by the kiln's) and in Fukuoka on `?date=2025-11-10` (Julia by Canal City's). Save screenshots to
`/work/media/`.

## Risks and open questions

- **The #219 rebuild of Sendai and Fukuoka** will move buildings, which is why "Senso-ji only, for now"
  in `docs/landmarks-and-towns.md` makes other temples wait. These three do not need to wait: the doors
  are found by sprite, and the rebuild's art tools keep `sendai-pub_0_0`, `sendai-kiln_0_0` and
  `canal-city_0_0` ("not redrawn" in the headers of `generate_sendai_town_art.py` and
  `generate_fukuoka_town_art.py`). What actually happens on a move: `keep_house_doors` puts a door back
  only where its sprite still stands, so a moved building comes out of the town generator sealed and
  `check_generators.py` fails until `generate_pub.py` / `generate_distillery.py` / `generate_mall.py` and
  `config_to_tiled` are run again; they re-find the building and re-wire the door. That is the whole of
  what the rebuild owes these rooms, and the docs section must say it. If the tasting bar should later
  sit behind the new `sendai-distillery-warehouse` door instead of the kiln's, that is one row in
  `DISTILLERY_DOORS`.
- **Map data is serial per town, and this stage cannot read the other agents' claims.** The pub and
  distillery both write `Sendai`; land them one after the other. If `origin/master` has moved Sendai,
  Fukuoka or the palette by the time the work is merged, do not hand-merge `config.json`: merge master,
  then re-run the art tool, the generator and `config_to_tiled`.
- **Art volume** is the bulk of the work (about 20 sprites a room). Ship rooms in the order given; each
  commit stands alone; cut only from the "may be cut" column.
- **Art encoded in the container** will drift on the owner's machine (see the gate). Known, and the same
  as #221.
- **A one-item shop list** (the tasting bar) has no precedent; check the panel in the browser. If it looks
  wrong, sell Highball and Nama Beer.
- **Names**: the room is `The Pub` because the sprite's fascia says PUB; the blog and the landmark table
  call it the HUB pub. Renaming is the `NAME` constant and the venue title.
- **Open for the owner, not blocking**: move post 727 inside Canal City. It would need the blog pipeline
  to allow an `interior` room for one landmark; this design leaves her outside.

## Review

Design adversary, 27 Nov. Method: read the generators, `roomgen.py`, the rules, lint and the tests the
design names; looked at the three building sprites; then, on a scratch worktree of `origin/master`,
opened the three doors onto stand-in rooms, added the three `OWNED_DOORS` rows and ran every check; then
installed Pillow there and ran `check_generators.py` again. The scratch tree was deleted; nothing but this
file changed.

What held up: the door cells and offsets, the `OWNED_DOORS` approach (the town generators do keep the
doors), the list of existing tests to change (exactly those two fail), leaving posts 501 / 509 / 515 / 727
where they are (the blog tests and `play.js check` pass, each is 2 cells from its door), `world-model.js`
untouched, the TV line (it is post 505's own words), interiors offering the pipeline nothing, the atrium
never being graded, and the rebuild keeping the three sprites.

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | **The design was written against a stale base.** `origin/master` is four commits ahead of the branch: #221 rebuilt 13 konbini rooms and grew `tilePalette` from 769 to 795, and the shrine roll-out added two doors to Fukuoka. "769 onwards" and the `fukuoka.test.js` list were both wrong, and rooms generated on the old palette could not be merged. | "Before you start" step 1 (merge master first); palette appended at its current end, never a hard-coded index; the Fukuoka list now includes the two shrines. | Yes |
| 2 | **"All checks green" cannot be met for `check_generators.py` in the container.** There is no Pillow (art tools are silently `skip`), and with Pillow 13.0.0 installed 25 existing art tools report `DRIFT` on untouched master. An implementer told "never leave it failing" could re-run them and commit hundreds of re-encoded PNGs. | Install step, a recorded baseline, and a gate defined as "same DRIFT list as the baseline, new tools `ok`"; never commit an existing PNG. | Yes |
| 3 | **Tracked `.pyc` files.** Master tracks `tools/__pycache__/*.pyc`; any tool run dirties them and everything left in the repo is committed. | `PYTHONDONTWRITEBYTECODE=1`, and a `git status` line in the checks. | Yes |
| 4 | **Wrong claim about lint.** `shop-sealed-floor` runs only where a room has a shop fixture (or is a house or lobby): it guards the pub and distillery, not the atrium. | Wording corrected; the generator's assert and `mall.test.js`'s own flood fill are named as the atrium's guards. | Yes |
| 5 | **Pockets behind the bars.** The pub bar on `fx` 1..7 and the tasting counter on `fx` 12..16 each left a one-cell-wide, two-deep pocket at the wall end, where the player stands on the staff's side. | Both run flush to the side wall (`fx` 0..6, `fx` 13..17); back bar, shelf, stools and lamps moved with them. | Yes |
| 6 | **Booths you can stand inside.** With only the foot row solid the player walks into the table and bench. The two booths also left a two-cell dead end between them. | Booths solid in all three rows, set back to back on `fy` 3..8. | Yes |
| 7 | **The bridge's layer contradicted its own precedent.** "On `Floor`, `depthBias` as `dazaifu-bridge`": that bridge is on `Non-Collidables` with `depthBias: -200`, and no interior lays a multi-cell sprite on `Floor`. It also left no water under the bridge. | Bridge on `Non-Collidables` with `depthBias: -200` written by the art tool; canal tiles run under it, not solid in its columns; a test asserts the bias. | Yes |
| 8 | **The TV's glow was a strobe.** `period: 900, depth: 0.35` is three times faster than any row in `Glows.SPRITES` (2300 to 3400 ms), in a dimmed room, on a phone. | `period: 2600, depth: 0.25`. | Yes |
| 9 | **A redundant, slow test.** Spawning `generate_sendai.py` / `generate_fukuoka.py` from three JS test files repeats what `check_generators.py` already proves. | The JS tests match the `OWNED_DOORS` row as text and spawn only the room's own generator; the town re-run is left to `check_generators.py`. | Yes |
| 10 | **Tests hard-coded host coordinates** ((29,21), (6,34), (14,30)), so the #219 rebuild would have to edit three more files, which is the cost "Senso-ji only" was avoiding. | Every cell is derived from the sprite's position plus the `LANDMARKS` offset. | Yes |
| 11 | **The rebuild risk was understated.** "The rebuild needs no change here" is not true if a building moves: the door is dropped and `check_generators.py` fails until the three generators are re-run. The design also contradicted the docs' "wait for the rebuild" note without saying why. | Risks spells out what happens and what the rebuild owes; the docs section must say it. | Yes |
| 12 | **Art volume against one implementation run.** Three art tools the size of the palace's (about 1,200 lines each) with no shared code and no cut order; a run that stops early could leave nothing. | Shared frame functions, table-driven shopfronts, a must-have / may-be-cut table per room, commit each room when green. | Yes |
| 13 | **The indoor canal ignored the outdoor one.** The rebuild's canal, jets and footbridge are already drawn (`fukuoka-canal*_0_0.png`); an unrelated look inside would clash once #219 lands. | Match those pieces; do not register or place them (they are #219's). | Yes |
| 14 | **Benches and planters are 2x2**, not the one-cell props the layout implied; palms at (8,9) and (17,9) would collide with a bench row on `fy` 9. | Sizes stated; the row is laid out for 2x2 and palms keep clear. | Yes |
| 15 | **Browser check was not actionable**: no way given to reach the rooms. | The trip dates that put the player in each town are named. | Yes |
| 16 | **A third copy of the izakaya list.** `taproom` sells what `pub` (the airport's) and `standbar` already sell; the pub could reuse `pub` with a room-level title. | Not changed: `Shop.titleFor` renames only `counter`, so reuse means changing its meaning and its tests for one row saved. A comment now says which bar `pub` is. | No |
| 17 | **Nine new tool and test files.** One table-driven generator for all three rooms (as `chikagai.py`) would be fewer files. | Not changed: the rooms share a frame and nothing else, the ticket wants them shippable one at a time, and one generator per interior is the pattern `check_generators.py` and the docs describe. The shared parts go in `roomgen.py` and the pub's art tool instead. | No |
| 18 | **The pub scrolls** (20x17 in a 20x15 view), so the top of the TV is off screen as you arrive; 20x15 would show the whole room. | Not changed: the palace and temple scroll too, and ten rows are what make room for tables and booths. Check the arrival framing in the browser screenshots. | No |

Nothing here needs the owner's decision.
