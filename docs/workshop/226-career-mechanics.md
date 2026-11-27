# Design: career mechanics — a job in the office towers (#226)

All paths are under `gamev2/` unless they start with `docs/workshop/`.

Revised after the design review; the criticisms and what was done about each are in **Review** at the end.

## Context

Money comes from the ¥5,000 you start with, fishing (needs the ¥1,200 rod, then a walk to a shop to sell)
and staked nomikai rounds. The ticket asks for another way to earn, "software engineer or design or tech
related … mini games or maybe a game progression … up to u".

The towers already have the place for it: every tower lobby (`LobbyOsaka1..3`, `LobbySapporo1..2`, #216) has
two lifts that say "the lift wants a pass", an unmanned reception desk with a monitor, and docs that say
"Nobody works there yet". Screenshots of today: `226-design-lobby-today.png`, `226-design-lift-today.png`.

Outcome: you can take a job as a software engineer in any tower, play a short mini-game for pay, and be
promoted up a six-step ladder that makes the game harder and the pay better. It is saved, shown in the menu,
counted in the achievements, and works on the keyboard and on a phone's touch pad.

## Approach

**Code only.** No change to `config.json`, `tiled/`, generators, art or `devhouse.world` (map data is serial;
this can land beside any town rebuild). The lobby's existing sprites get new meanings through the
`Interactions` table.

**The word is "shift".** One go at the mini-game is a **shift**, on screen, in the docs, in identifiers and
in test names. "Sprint" is taken: it is what SHIFT and the touch pill do, and `Hints` rewrites `SHIFT` to
`sprint`. Nothing in this change is called a sprint.

**The loop**

1. Bump the **reception desk**: you are signed on (toast), which creates the saved `career`. Later bumps read
   your status back. Toast only, like `PalaceVisit`.
2. Bump a **lift**: without a pass, a toast pointing at the desk; with one, the **shift** overlay opens.
3. A **shift** is 5 tickets against a clock. Each ticket is a commit-style name and a row of arrows; press
   them in order (arrows / WASD / the d-pad). A wrong press restarts that ticket's row ("BUILD FAILED"),
   costing time only. All 5 merged before the clock = a clean shift, and the shift ends there.
4. Pay = tickets merged × the level's pay, plus the level's bonus if clean. It goes into the wallet once, when
   the shift ends.
5. Lifetime tickets merged decide the **title**; a higher title means longer rows and more pay.

Why this game: it uses only the allowed keys, is unlike the two existing ones (fishing is one timed press, the
nomikai is mashing), reads as "typing", and is playable with a thumb. One career works in every tower.

**The ladder** (`Career.LEVELS`; level = last row whose `at` ≤ lifetime `merged`)

| title | at | row length | clock | pay / ticket | clean bonus | clean shift |
|---|---|---|---|---|---|---|
| Intern | 0 | 3 | 20 s | ¥10 | ¥30 | ¥80 |
| Junior Engineer | 10 | 4 | 20 s | ¥20 | ¥50 | ¥150 |
| Engineer | 25 | 5 | 25 s | ¥35 | ¥75 | ¥250 |
| Senior Engineer | 50 | 6 | 30 s | ¥55 | ¥100 | ¥375 |
| Staff Engineer | 90 | 7 | 35 s | ¥80 | ¥125 | ¥525 |
| Principal Engineer | 150 | 8 | 40 s | ¥110 | ¥200 | ¥750 |

Pay per key press rises with every step (with and without the bonus), so a promotion is never a pay cut. The
level is locked in when a shift starts; a promotion is announced on the result screen and applies from the
next shift.

**The clock is one second an arrow, never under 20 s** (`Career.clockMs`: `max(MIN_CLOCK_MS, TICKETS × len ×
ARROW_MS)`). The clock column above is derived, not a table column. Every level then asks for the same pace
(about one press a second with no mistakes), and what gets harder is the row: a miss costs more of it. A flat
30 s would ask an Intern for 0.5 presses a second and a Principal for 1.33, which a thumb on a d-pad cannot
hold through a restarted row.

**Balance, with the arithmetic.** A clean shift ends when the fifth ticket merges, so it lasts as long as the
typing, not as long as the clock. The model: `5 × len` presses at 3 a second on a keyboard or 1.5 a second
with a thumb, plus 2 s for the result and ready screens.

| title | clean shift | keyboard | thumb |
|---|---|---|---|
| Intern | ¥80 in 7 s / 12 s | ≈ ¥700 / min | ≈ ¥400 / min |
| Junior Engineer | ¥150 in 9 s / 15 s | ≈ ¥1,050 | ≈ ¥600 |
| Engineer | ¥250 in 10 s / 19 s | ≈ ¥1,450 | ≈ ¥800 |
| Senior Engineer | ¥375 in 12 s / 22 s | ≈ ¥1,900 | ≈ ¥1,000 |
| Staff Engineer | ¥525 in 14 s / 25 s | ≈ ¥2,300 | ≈ ¥1,250 |
| Principal Engineer | ¥750 in 15 s / 29 s | ≈ ¥2,900 | ≈ ¥1,550 |

For comparison: a won FRIENDLY round is ¥100 in about 20 s (≈ ¥300 / min); fishing is ≈ ¥205 a cast and about
5 s a cast (≈ ¥2,500 / min, before the walk to sell and after the ¥1,200 rod); a won BIG TAB is ¥2,000 in a
15 s round. So an Intern earns a little more than FRIENDLY rounds, a Principal on a keyboard about what
fishing does, and nothing here beats a BIG TAB. The whole ladder is 150 tickets: 30 clean shifts, about
6 minutes of typing on a keyboard or 11 with a thumb, paying ¥11,160 on the way up.

No daily cap (fishing has none) and no energy cost (the documented rule: mini-games cost nothing).

**Coffee helps.** A new additive effect kind `focus` (seconds added to the shift clock, locked in at the
start as the nomikai's buffs are); Canned Coffee gains `focus: 5`.

**Judging a press.** Directions, not keys: an arrow and its WASD key are the same direction. Each frame,
`dirs` is the set of directions that went down this frame and `held` the set that was already down.

1. `dirs` empty: nothing.
2. `dirs` has more than two directions, or two opposite ones: **miss**. (Slapping every key at once is not an
   answer. A perpendicular pair is what the d-pad sends for a touch that lands on a diagonal.)
3. `dirs` contains the expected direction: **advance** one arrow.
4. The arrow just typed is still held (`at > 0` and `held` contains `seq[at - 1]`) and every direction in
   `dirs` is perpendicular to it: **nothing**. This is a thumb rolling off the arrow it pressed into the
   neighbouring diagonal, or a finger sliding round the pad's rim to the next arrow; the d-pad sends a
   keydown for it and it was never a press.
5. Otherwise: **miss**.

Each frame advances at most one arrow. Rule 4 forgives only under the key that just scored, so rolling the
fingers round all four keys still collects misses.

**Not in this change:** a second department (design), an NPC colleague, new art, a HUD element. The ladder and
the rules tables are written so another job can be a second table later.

## Changes

### New: `src/Career.js`

Class `Career(scene)`, header comment in the house style (what it is, the rules, "To take it out: …").
Modelled on `DrinkingGame` (overlay) plus `PalaceVisit` (bump de-dupe).

- State `idle | ready | playing | result`; `isActive()` is `state !== 'idle'`.
- Own keys via `scene.input.keyboard.addKeys`: W A S D, the four arrows, SPACE, ENTER, ESC.
- **One reader for the keys**: `read()` is `Career.read(this.keys, this.justDown)` (static, below; nothing
  in the game sets `this.justDown`, so Phaser's `JustDown` is used, and the unit tests set a fake, as
  `InputHandler.swallow` lets them). It reads `JustDown` of all eleven keys on every call. There is no Phaser
  in the unit runner, so nothing else in the class may call `Phaser.Input.Keyboard.JustDown`.
- **No press outlives its frame** (#220). Phaser keeps `JustDown` raised until it is read. `handleInput`
  reads every key on every frame in every state, so an arrow tapped on the ready screen or a SPACE tapped
  while typing is used up there and then; and the overlay swallows what was pending as it opens and as it
  closes (a `read()` whose result is dropped), so the key held to bump the lift is not a press in it.
- `hold(heading)`: `if (this.bump) this.bump = ShrineVisit.carried(this.bump, now, heading)`.
- `check(gridX, gridY)`: false when `isActive()`, `roomManager.isTransitioning`, the dialogue or the shop
  panel is up (the guards `DrinkingGame.checkStart` and the other visits' callers have).
  `hit = roomManager.interactionAt(x, y, 'career')`; false if none or no shop. Record the bump and stop if not
  `ShrineVisit.fresh` (exactly `PalaceVisit.check`). Then:
  - `desk`: `out = Career.signOn(shop.career)`; if `out.fresh` set `shop.career = out.career`, `shop.save()`;
    `shop.toast(out.line)`.
  - `lift`, no `shop.career`: `shop.toast('the lift wants a pass. the reception desk hands them out')`.
  - `lift`, hired: swallow (`this.read()`), `state = 'ready'`, `render()`.
- `render()`: dimmer (0x000000, 0.82, depth 2000), a 760x490 panel (fill 0x10161c, border 0x5fd38d, depth
  2001), texts at depth 2002 (`PixelOperatorMono` / `PixelOperatorMonoBold`, `setResolution(1)`,
  `setScrollFactor(0)`), one Graphics for the arrow row. Everything pushed to `this.objs`, destroyed in `leave()`.
  Sizes follow the overlay rules (single lines ≥ 16px, paragraphs ≥ 22px; nothing tweened).
  - **ready**: `ENGINEERING`, the title, "5 tickets · {secs}s · ¥{pay} a ticket · +¥{bonus} for a clean
    shift", a rules line ("press the arrows in order. a wrong one fails the build and the ticket starts
    again"), the focus line when `shop.buff('focus') > 0` ("coffee: +5s on the clock"), hint
    `Hints.text(scene, 'SPACE to start    ESC to leave')`.
  - **playing**: `TICKET n/5`, the ticket name, the arrow row, the clock (one decimal, 100 ms
    `scene.time.addEvent`, as the nomikai's), a status line (`BUILD FAILED` for 600 ms after a miss, `MERGED`
    after a ticket), hint `Hints.text(scene, 'arrows to type    ESC to clock off')`. **Lower-case `arrows`**:
    the `Hints` rule that turns it into `d-pad` is case-sensitive, and `ARROWS` would be left on a phone.
  - **result**: `SHIFT COMPLETE` (clean) / `TIME'S UP` / `CLOCKED OFF`, "{n}/5 merged", "+¥{pay}" and
    "clean shift +¥{bonus}" when earned, `PROMOTED: {title}` when it happened, else "{k} more to {next title}"
    (nothing at the top), hint `Hints.text(scene, 'SPACE for another shift    ESC to leave')`.
  - Each hint is its own Text object.
- The arrow row: `Graphics.fillTriangle` per arrow in a 56px cell, centred in the panel (8 arrows = 448px);
  done 0x5fd38d, current 0xffffff with a 2px box round its cell, pending 0x4a5560. Redrawn (`clear()`) on
  every change. No font glyphs for arrows.
- `begin()`: `level = Career.levelOf(shop.career.merged)`,
  `clock = Career.clockMs(level.len, shop.buff('focus'))`, `merged = 0`, `names = Career.names(Math.random)`,
  first `seq = Career.sequence(level.len, Math.random)`, `at = 0`, start the 100 ms ticker and a
  `delayedCall(clock, () => this.finish(false))`.
- `handleInput()` (called from `InputHandler.routeInput`) is `this.act(this.read())`; `act(input)` takes
  `{ dirs, held, confirm, esc }` and is what the unit tests drive:
  - ready: `confirm` → `begin()`; `esc` → `leave()`.
  - playing: `esc` → `finish(false)`. Else `out = Career.press(seq, at, dirs, held)`: `'step'` → `at++`;
    `'merged'` → `merged++`, then `finish(true)` if it was the fifth, else next name and sequence, `at = 0`;
    `'miss'` → `at = 0`, show `BUILD FAILED`.
  - result: `confirm` → `state = 'ready'`, redraw; `esc` → `leave()`.
- `finish(clean)`: returns at once unless `state === 'playing'` (the timer and the fifth merge, or ESC, can
  land on one frame; it pays once). Stop the timers; note which `careerProgress()` rows are complete;
  `out = Career.settle(shop.career, level, merged, clean)`; `shop.career = out.career`;
  `adjustWallet(out.pay + out.bonus)` (copy `DrinkingGame.adjustWallet`: money, `shop.save()`,
  `scene.updateHUD()`); `state = 'result'`; if a `careerProgress()` row has become complete,
  `shop.toast('★ achievement: ' + names.join(' + '))` (the wording `Fishing` uses; the toast is a `uiFloat`
  and sits clear of the panel by itself).
- `leave()`: destroy `objs`, `state = 'idle'`, swallow, and `if (this.bump) this.bump.at = now` so a
  direction still held against the lift does not reopen the overlay.

Statics (pure; these are what the unit tests call):

| static | returns |
|---|---|
| `Career.LEVELS` | the ladder: `{ title, at, len, pay, bonus }` |
| `Career.TICKETS = 5`, `Career.ARROW_MS = 1000`, `Career.MIN_CLOCK_MS = 20000` | |
| `Career.TICKET_NAMES` | ≥ 16 short lower-case commit lines, ≤ 40 characters, ASCII (e.g. `fix: the login button does nothing`, `chore: bump left-pad`, `revert: "fix: the login button"`); no real names |
| `Career.DIRS = ['up', 'down', 'left', 'right']` | |
| `Career.levelOf(merged)` | the `LEVELS` row |
| `Career.next(merged)` | `{ title, left }` for the next row, or `null` at the top |
| `Career.clockMs(len, focus)` | `Math.max(MIN_CLOCK_MS, TICKETS * len * ARROW_MS) + 1000 * (focus \|\| 0)` |
| `Career.sequence(len, rand)` | `len` of `DIRS`, never three the same in a row |
| `Career.names(rand)` | `TICKETS` distinct `TICKET_NAMES` |
| `Career.read(keys, justDown = Phaser.Input.Keyboard.JustDown)` | `{ dirs, held, confirm, esc }`: `dirs` the directions with a key that went down since the last read, `held` the directions with a key down that did not, `confirm` SPACE or ENTER just down, `esc` ESC just down. Calls `justDown` on **every** key, every call (no short-circuit: W + ↑ pressed together are one `up` now and nothing on the next read) |
| `Career.press(seq, at, dirs, held)` | `null` / `'step'` / `'merged'` (the step that completes `seq`) / `'miss'`, by the five rules under "Judging a press"; `held` may be omitted (no forgiveness) |
| `Career.signOn(career)` | not hired: `{ fresh: true, career: { merged: 0, shifts: 0, earned: 0 }, line: 'You fill in a form. Staff pass: Intern. The lifts go up to engineering now.' }`; hired: `{ fresh: false, line: Career.status(career) }` |
| `Career.status(career)` | `"{title} · {merged} tickets merged · {left} more to {next}"`; at the top `"Principal Engineer · {merged} tickets merged · nowhere left to go but meetings"` |
| `Career.settle(career, level, merged, clean)` | `{ career: { merged: +merged, shifts: +1, earned: +pay+bonus }, pay: merged * level.pay, bonus: clean ? level.bonus : 0, promoted: new title or null }`; does not mutate its input |
| `Career.where(config)` | `[{ room, name }]` for every room with a `lobby`, `name` = the display name of `lobby.host` (as the HUD shows it), sorted; the Career card's "who is hiring" |

### Modified

- **`index.html`**: add `'src/Career.js'` to the script list after `'src/PalaceVisit.js'` (it uses `ShrineVisit`).
- **`src/utils/Interactions.js`**:
  - lift: `{ kind: 'lift', group: 'career', pattern: /^lobby-lift/, footprint: true }` (no `say`).
  - new: `{ kind: 'desk', group: 'career', pattern: /^lobby-desk/, footprint: true }`.
  - directory stays `flavour`; `say: 'engineering is hiring, the directory says. ask at the desk'`
    (58 characters: `lobbies.test.js` holds a lobby's lines to 60).
  - Add `career` to the file's list of groups / header comment.
- **`src/GameScene.js`**: construct `this.career = new Career(this)` beside `shrineVisit` / `palaceVisit`;
  in `checkNPCInteraction` call `this.career.check(x, y)` beside the palace line, inside the same
  `!dialogueManager.isVisible() && !shop.isVisible()` test its neighbours have (the lift is no longer
  `flavour`, so nothing after it answers for that cell); in `update` add
  `this.career.hold(this.inputHandler.heading())`; new `showCareer()` (below).
- **`src/systems/InputHandler.js`**: add
  `this.scene.career && this.scene.career.isActive() && this.scene.career` to `routeInput()`'s overlay list,
  after the drinking game.
- **`src/Shop.js`**:
  - `load()`: `this.career = Shop.careerOf(raw.career)`; `save()`: `if (this.career) blob.career = this.career`
    (the `omikuji` / `guestbook` idiom; `v` stays 4).
  - `Shop.careerOf(raw)`: `null` unless `raw` is an object whose `merged` is a finite number ≥ 0; then
    `{ merged, shifts, earned }`, each floored, with `shifts` and `earned` falling back to 0 when they are
    missing or not finite numbers ≥ 0. `merged` is the title; a blob with a damaged counter beside it must
    not cost the player the ladder.
  - `Shop.EFFECT_KINDS.focus = { describe: v => \`work clock +${v}s\`, additive: true }` (the shape of the
    `headStart` row). Canned Coffee's summary then reads "speed +30%, work clock +5s for 1:30".
  - Canned Coffee: `effect: { speed: 1.3, secs: 90, focus: 5 }`,
    `desc: 'the long haul: speed +30% and 5s more on the work clock, for 90s.'` (65 characters; the longest
    `desc` today is 66).
- **`src/MenuManager.js`**: a `Career` row after `Stamp Card`, calling `scene.showCareer()` exactly as the
  Stamp Card row calls `showStampCard()` (11 rows; the panel height formula already follows the count: 660px).
- **`src/GameScene.js` `showCareer()`**: a copy of `showStampCard()`'s shell (dimmer, 640-wide panel
  0x1a1a1a / 0x666666, `achievementsVisible` + `achievementsCloseCallback`, click or ESC closes, hint
  `Hints.text(this, '(click or ESC to close)')`). Content: `CAREER`; hired: the title, "tickets merged",
  "shifts", "earned ¥…" (`shop.fmt`), the next promotion (`Career.next`), then the six `LEVELS` rows
  (title · row length · pay per ticket; yours highlighted gold, later ones grey). Not hired: "no job yet",
  "the office towers are hiring:", one line per `Career.where(config)` name (de-duplicated), "ask at the
  reception desk".
- **`src/AchievementManager.js`**: `careerProgress()` returning two rows in the existing
  `{ name, desc, value, total, complete }` shape from `scene.shop.career` (zeros when null), `[]` when
  `typeof Career === 'undefined'` (the guard `fishingProgress()` has), appended in `itemProgress()`:
  - `First Paycheck` — "Merge a ticket at work" — `min(merged, 1)` / 1.
  - `Principal Engineer` — "Reach the top of the ladder" — level index / `LEVELS.length - 1`.
  The achievements panel grows by itself (6 rows → 658px of 960).
- **`tools/world-model.js`**: add `'career'` before `'flavour'` in `interactionAt`'s group order; `describe`:
  desk → `'the reception desk: signs you on for a job in the tower (free); afterwards reads your title back'`,
  lift → `'the lift up to work: a shift of tickets for pay (needs the staff pass from the reception desk)'`;
  the `flavour-no-front` lint is computed over `career` interactions as well as `flavour` ones (same error name).
- **`tools/play.js`**: `GLYPH.career = 'J'` and `J job` in the legend line of `help`; a `career` bump prints
  `describe()` (no terminal mini-game).
- **`tools/test_game.js`**: add `'Career.js'` to the runner's source list beside `'DrinkingGame.js'`, and
  nothing else. `AchievementManager.itemProgress()` reads `Career`, and `shop.test.js` calls `itemProgress()`,
  so whether `Career` is loaded must not depend on which test file ran first. `Career.js` only needs
  `ShrineVisit` when `check` / `hold` run, so `ShrineVisit.js` stays out of the list and is loaded by
  `career.test.js` with the guard the shrine, palace and temple tests use
  (`if (!game('typeof ShrineVisit !== "undefined"')) vm.runInContext(src('ShrineVisit.js'), …)`). The
  `shiftWith(career, focus)` helper (a `Career` on `Object.create`, stub `scene.time`, stub texts / graphics,
  keys as `{ isDown, _justDown }` objects and a `justDown` that reads and clears `_justDown`, a shop
  `{ money, career, save, fmt, buff, toast }`) lives in `career.test.js`: only that file uses it.
- **`tools/browser/regress.js`**: `if (s.career.isActive()) o.push('career')` in `__t.overlays()`;
  `if (s.career.isActive()) s.career.leave()` in `__t.reset()`; the new checks under Tests; any assertion
  that pins the menu's rows or labels updated strictly.
- **Docs**: `docs/shop-and-economy.md` — a "Career" section (loop, ladder table, the clock rule, the five
  judging rules, the balance table with its model, how to add a job), `focus` in the effect kinds, `career`
  in the save blob, Canned Coffee's line; `docs/landmarks-and-towns.md` Tower lobbies — the desk and lifts now
  do something, the directory's new line; `docs/architecture.md` File Structure — `Career.js`, and `Career`
  among the readers of `Interactions`; `docs/hud-input-touch.md` Input Handling — the shift's keys beside the
  nomikai's; `docs/tools-play-test-studio.md` if it lists glyphs or bump descriptions.

## Data and interfaces

- **Save** (`localStorage.gamev2_shop`, still `v: 4`): optional `career: { merged, shifts, earned }`. Absent
  until you sign on; hired = present. Old blobs load and save unchanged; a value without a usable `merged`
  loads as not hired; the wallet is never changed by loading. Nothing is written during a shift: closing the
  tab mid-shift loses that shift's tickets and nothing else.
- **Interactions**: new group `career` with kinds `desk` and `lift`; `lift` leaves `flavour`.
- **Effects**: new kind `focus` (additive seconds); an item gets it by adding `focus: n` to its `effect`.
- **Scene**: `scene.career` (`check`, `hold`, `isActive`, `handleInput`, `leave`), `scene.showCareer()`.
- No new keys, no new localStorage key, no config or asset changes.

## Tests

Unit — new `tools/tests/career.test.js` (unique test names, `(#226)` suffix):

- `levelOf` / `next` at 0, 9, 10, 149, 150, 9999; `LEVELS` is ascending in `at`, `len`, `pay`, in pay per
  key press without the bonus (`pay / len`) and with it (`(5·pay + bonus) / (5·len)`).
- The balance model is pinned, so a retune has to be made on purpose: `(5·pay + bonus) / (5·len / 3 + 2) × 60`
  is under ¥800 for the Intern and under ¥3,000 for the Principal.
- `clockMs(3, 0)` = 20000, `clockMs(5, 0)` = 25000, `clockMs(8, 0)` = 40000, `clockMs(8, 5)` = 45000.
- `sequence`: right length, only `DIRS`, never three in a row, deterministic for a seeded `rand`; `names`: 5
  distinct.
- `press`, one case per rule: empty → `null`; expected alone → `step`; last one → `merged`; wrong → `miss`;
  a perpendicular pair holding the expected direction → `step`; a pair without it → `miss`; two opposite
  directions → `miss` even when one is expected; three or four directions → `miss`; a wrong perpendicular
  direction while the arrow just typed is held → `null`; the same with nothing held, at `at = 0`, or under a
  held key that is not the arrow just typed → `miss`; the expected direction under a held key → `step`.
- `settle`: totals, bonus only when clean, `promoted` exactly when a threshold is crossed, input not mutated,
  0 merged pays ¥0 and still counts a shift.
- `signOn`: hires once; a second call changes nothing and reads the status; `status` at the top.
- Save (`shopWith`): a blob without `career` loads `null` and saves no `career` key; a valid one round-trips;
  garbage (`'x'`, `-1`, `{}`, `{ merged: 'x' }`) loads `null`; `{ merged: 40 }` and
  `{ merged: 40, shifts: null, earned: -3 }` load as `{ merged: 40, shifts: 0, earned: 0 }`; money untouched
  in every case.
- `focus`: Canned Coffee's summary is `speed +30%, work clock +5s for 1:30`; `shop.buff('focus')` is 5 while
  it is active, 0 after.
- `read`: a key down since the last read is in `dirs` once and in `held` on the next read while it stays
  down; W and ↑ down together are one `up` and nothing on the next read; SPACE or ENTER is `confirm`.
- `shiftWith`: a full clean shift driven through `handleInput` (the stub keys) adds `5·pay + bonus` to the wallet once and
  1 to `shifts`; ESC mid-shift settles what is merged with no bonus; the timer's `finish(false)` after a
  clean finish does not pay twice; a player at 9 merged is promoted on the result; an arrow pressed on the
  ready screen is not the first press of the shift; SPACE pressed while playing does not skip the result;
  the first merged ticket toasts
  `★ achievement: First Paycheck` once.
- Hints: `Hints.word` of each of the three hint lines has no `ARROWS`, `SPACE` or `ESC` left in it, and the
  playing line reads `d-pad to type    B to clock off`.
- `Career.where(realConfig)` lists exactly the rooms that have a `lobby`.
- `careerProgress` rows for null, 1 merged and 150 merged.
- World (`worldWith`): in every lobby the desk and both lifts answer in group `career` and the directory in
  `flavour`; `play.js lint` is clean for all five lobbies.

Updated strictly:

- `tools/tests/lobbies.test.js`, the bump test: the directory's hit is `flavour`, the desk's and the lifts'
  `career`; kinds bumped are `['desk', 'directory', 'lift']`. The lines test: the directory alone is `flavour`
  with a `say` of 11..60 characters; `lobby-lift_0_0` and `lobby-desk_0_0` match in group `career` with
  `footprint` and no `say`; `lobby-desk_0_0` leaves the list of sprites that match `null`; the walled lobby's
  `flavour-no-front` names the directory, a lift and the desk. Both tests are renamed to say what they now hold.
- `tools/tests/shop.test.js`: the `itemProgress()` names become
  `['Taste Tester', 'Regular Customer', 'Big Catch', 'Konbini Pilgrim', 'First Paycheck', 'Principal Engineer']`.
- Any test that pins the menu rows, Canned Coffee's `desc` or the list of effect kinds.

Browser — `tools/browser/regress.js` (`tools/browser/README.md`):

- `career-shift` (desktop): the profile's save is shared by every check, so the check starts by setting
  `__t.s.shop.career = null` and saving, and puts it back to `null` when it ends. Stand in `LobbyOsaka1`;
  real keys: bump a lift → the pass toast, no overlay; bump the desk → hired; bump the lift → overlay
  `career`, `ready`; SPACE; press what `__t.s.career.seq` asks for, one wrong key in the middle (asserting
  `at` returns to 0); after five tickets the wallet is up by exactly ¥80 and `gamev2_shop` holds
  `career.merged === 5`; ESC leaves, the player has not moved, no overlay is left.
- `menu-entries`: the `Career` row exists and opens / closes the card.
- `phone-landscape-touch` (touches sent as the check already sends them, `Input.dispatchTouchEvent`): with
  the pass, the overlay opens from a d-pad bump, A starts, d-pad touches type one ticket, and one of those
  touches is moved from the arrow it typed into the neighbouring diagonal before it is lifted (`at` does not
  go back to 0 and no `BUILD FAILED`); the hint on screen reads `d-pad to type`; B clocks off and B leaves.

Run, from `gamev2/`:

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py
python3 tools/sync_cities.py --check
node tools/browser/regress.js      # with the server and the shared Chrome, per tools/browser/README.md
```

Then play it with real keys and touches at 1280x960, 844x390 (touch), 667x375 and 390x844, and look at
screenshots of the ready, playing (mid-row, after a miss) and result screens, the Career card (hired and
not), the 11-row menu and the achievements panel.

## Risks and open questions

- **The pace is modelled, not measured.** Nothing in this pipeline presses keys at a person's speed: the
  regression's presses are instant, so it proves the rules and says nothing about how the clock feels. The
  balance table rests on 3 presses a second on a keyboard and 1.5 with a thumb. The implementer may change
  `ARROW_MS` and `MIN_CLOCK_MS` only, and must update the docs and tests to match. The ladder's pay is pinned
  by a test and stays as tabled unless the owner says otherwise.
- **A keyboard player will rarely see the clock run out** (they need about a third of it). For them the game
  is accuracy, and the clock is there for the thumb. Tightening it for keyboards would shut phones out.
- **The ladder is short**: about 6 minutes of clean shifts on a keyboard, 11 with a thumb. Longer is one
  column (`at`) of one table.
- **Only Osaka and Sapporo have towers today**, so a player who starts in Tokyo or Fukuoka takes a train to
  work. The Career card says where; every town whose lobbies are rolled out later gets the job with no code.
- **Thumb accuracy** on the d-pad at phone scale decides whether the miss rule feels fair. Rules 2 to 4 of
  the judging and the proportional clock are the mitigation; one case is left, a touch that lands on a
  diagonal and is then rocked across the boundary and back, which reads as a second press.
- **Money is already farmable** (BIG TAB), so the job is tuned as a steady earner, not the best one. A daily
  cap was left out on purpose.
- **Review weight.** It changes the save blob, the Interactions table and more than six source files: it needs
  the independent review `docs/working-on-issues.md` asks for.
- **Open (not blocking):** the owner may prefer a design job as well, or a named colleague at the desk; both
  fit as follow-ups (a second ladder table; an NPC needs map data).

## Review

The design was read against the code it names. Each criticism, the fix, and whether the body above took it.

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | **The balance claim was wrong by 2 to 4 times.** It priced a shift at the full 30 s, but a clean shift ends at the fifth merge. At 3 presses a second the old table paid an Intern ≈ ¥1,700 / min (not "about FRIENDLY", ≈ ¥300) and a Principal ≈ ¥4,700 / min (not "about fishing", ≈ ¥2,500), with no rod and no walk: fishing would have been pointless from the first minute, and the ladder paid ¥20,350 on the way up. | State the time model and price the ladder from it: clean shifts of ¥80 to ¥750. The comparison table is in the body and a unit test pins the two ends. | Yes |
| 2 | **A flat 30 s clock means nothing on a keyboard and too much on a phone.** It asks for 0.5 presses a second from an Intern and 1.33 from a Principal; at 1.5 taps a second a Principal's 40 presses take 27 s with no mistake at all. | One second an arrow, never under 20 s (`clockMs(len, focus)`), so every level asks the same pace. Tunables are `ARROW_MS` and `MIN_CLOCK_MS`. | Yes |
| 3 | **"Sprint" already means something.** SHIFT sprints, the touch pill is the sprint button, and `Hints` rewrites `SHIFT` to `sprint`; "A for another sprint" beside that pill, and "sprint clock" in an item's summary, read as running. The save field was already `shifts`. | Call it a shift everywhere: screens, docs, identifiers, test names. | Yes |
| 4 | **The judging rule could be mashed.** "The set contains the expected direction" passes all four keys slapped at once, every frame. | More than two directions, or two opposite ones, is a miss. | Yes |
| 5 | **The d-pad sends keydowns that are not presses.** It is one surface with eight sectors: a thumb that rolls from an arrow into the next diagonal, or slides round the rim, fires a keydown for the neighbour while the first is held. The design counted that as a miss and restarted the row, and offered only "raise `CLOCK_MS`". | Rule 4: a wrong perpendicular direction under the arrow just typed is ignored. `press` takes `held`; unit cases for each side of the rule, and a moved touch in the phone check. | Yes; one case left open in Risks |
| 6 | **The playing hint would not be reworded on a phone.** `Hints`' rule for `arrows` is case-sensitive, so `'ARROWS to type'` stays as written beside "B to clock off". | Lower-case `arrows`, and a unit test of the touch wording of all three hints. | Yes |
| 7 | **Stale presses.** Nothing read the arrows on the ready and result screens or SPACE while playing, so `JustDown` stayed raised (#220): an arrow tapped before SPACE was the first press of the shift, SPACE tapped mid-shift skipped the result. Reading a direction's two keys with a short-circuit leaves W + ↑ scoring twice. `leave()` dereferenced `this.bump` unguarded. | One static, `Career.read`, reads every key on every frame in every state (and takes its `justDown` as a parameter, since the unit runner has no Phaser: `handleInput` as designed could not have been driven there); its result is dropped as the overlay opens and closes; the bump is guarded. Unit cases for each. | Yes |
| 8 | **The directory's new line breaks an existing test.** It was 66 characters; `lobbies.test.js` holds a lobby's lines to 60. | A 58-character line. | Yes |
| 9 | **`lobbies.test.js` pins more than the design listed**: `lobby-desk_0_0` must match `null`, both lines must be `flavour` with a `say`, and the walled-lobby lint is only asserted for the directory. | The exact edits are listed under Tests, and the lint assertion now covers a lift and the desk. | Yes |
| 10 | **`shop.test.js` pins `itemProgress()` to four names**, and `itemProgress()` would have read `Career` only when some earlier test file happened to have loaded it. "Add `ShrineVisit.js` to the list if not yet loaded" was not an instruction. | `Career.js` goes in the runner's list (it needs nothing at load time), `ShrineVisit.js` is loaded by `career.test.js` with the existing guard, `careerProgress()` gets `fishingProgress()`'s `typeof` guard, the pinned list is updated, and the helper lives in the test file. | Yes |
| 11 | **`Shop.careerOf` was all or nothing**: one bad counter and the player is an unhired Intern again. | Hired when `merged` is usable; `shifts` and `earned` fall back to 0. | Yes |
| 12 | **The two achievements were never announced.** Fishing toasts `★ achievement:` when a row completes; the design only added rows to the panel. | `finish()` compares `careerProgress()` before and after and toasts. | Yes |
| 13 | **The coffee's summary misread**: "speed +30%, +5s on the sprint clock at work for 1:30". | `work clock +5s`, and a `desc` no longer than the longest today. | Yes |
| 14 | **The regression would leak state.** One save is shared by every check, `__t.reset()` did not know the overlay, and "a fresh save" was not something the check could have. | `career` in `reset()`; the check clears and restores `shop.career`. | Yes |
| 15 | **`check()` had no guards** and the scene line was written as an early `return` unlike its neighbours. | The guards `DrinkingGame.checkStart` has, and the call sits inside its neighbours' test. | Yes |
| 16 | **The ladder is over in 6 to 11 minutes**, short for "a game progression". | Stretch `at`. | No: how long it should last is taste, the thresholds are one column, and the number is now in Risks for the owner. |
| 17 | **Two presses on one frame**: the second is dropped. | Queue them. | No: it costs one press on a frame hitch and nothing else; a queue is more code than the fault. |
| 18 | **Simpler: drop the desk** (the first lift bump hires you), **the `focus` kind, or the Career card.** | — | No: the desk is what reads your title back, the coffee is the one tie to the shop, and the card is how a player in Tokyo learns the job exists and where. Each is small. |
| 19 | **`play.js` draws `undefined` for every glyph-less group** (the directory today, in any `map` of a lobby). | A fallback glyph. | No: it is there before this change and is not this ticket's; `GLYPH.career` keeps the new group out of it. |
| 20 | **How it feels cannot be tested here.** Playwright does not have thumbs or a typing speed. | Said so in Risks, with what stands in: the pinned model, the rule cases, the moved touch. | Yes |
