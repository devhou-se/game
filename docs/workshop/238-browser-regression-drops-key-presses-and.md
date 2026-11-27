# Design: a browser regression that does not drop presses or overrun its deadline on a slow machine (#238)

## Context

`gamev2/tools/browser/regress.js` (24 checks) runs the desktop walk-through beside the first-time and phone
profiles: two pages on the one shared Chrome. In a slow container (software GL) `menu-entries`, `menu-map` and
`phone-landscape-touch` ("a tap on B did not clock off") fail now and then, `phone-landscape-devhouse` fails
after it as a follow-on, and a clean run takes 75-90 s against `DEADLINE_MS = 80000`. It happens on unmodified
`origin/master`; a ~4 s wait put before `menu-entries` makes it fail every time.

The cause, from reading the code and Phaser 4.2.0 (**not reproduced: the design stage has no browser**):

- **A key release that no game frame sees.** `InputHandler` reads the keys once a frame and finds a menu or
  ESC press as an edge against `lastKeyState` (`held(key) && !lastKeyState.down`, then
  `lastKeyState.down = sKey.isDown || cursors.down.isDown`). `hold()` in `browser.js` lets a key go for a
  fixed 120 ms. When one frame takes longer than that, the key goes up and the next one comes down between
  two frames: the game never sees the gap, the second press is not an edge, and nothing moves. `menu-entries`
  (ArrowDown and `s` in turn, both feeding `lastKeyState.down`) and `menuTo()` in `menu-map` (`s` or ArrowUp
  repeated, ESC twice) are the checks that press one logical key twice in a row. The phone's B-then-B taps
  have the same weakness with their fixed 150 ms.
- **The other page.** Frames get that long when the second page boots or loads a room on the shared GPU
  process; `menu-map` boots the desktop page twice. The clock-off failure is not the lost-edge kind (`Career`
  reads keys with Phaser's `JustDown`, which is latched): the likeliest reading is the phone page standing
  still for longer than the 1.5 s the assertion allows while the desktop page boots. A 4 s shift lines those
  up, which fits the ticket's recipe.
- **Follow-on.** The two `phone-landscape` checks share a page with no clean-up between them, so a failed
  touch check leaves the Career overlay up for the Devhouse check.
- **Deadline.** 80 s was sized for a ~25 s run on a fast machine.

Intended outcome: the suite gives the same answer at any frame rate, a failure in one check does not fail the
next, and a slow machine finishes inside the deadline. No assertion is loosened, and the game is not changed.

## Approach

Everything is in `gamev2/tools/browser/`.

1. **One page at a time.** Run `desktop`, `firstTime`, `phones`, `trips` one after another. No page then
   competes with another for the GPU process, and a check's timing no longer depends on what a different
   profile happens to be doing. Cost: a longer run on a fast machine (estimated ~25 s to ~35 s, to be measured).
2. **A press is over when the game has seen the key up.** A new `frames(page, n = 2)` in `browser.js` waits
   until the game loop has run `n` more frames. `hold()` waits for it together with its 120 ms, so the release
   lasts 120 ms or two frames, whichever is longer: nothing changes on a fast machine. The phone taps get a
   `tap()` helper that waits for the tap's effect, then for every key to be up, then two frames, in place of
   the fixed 150 ms.
3. **Clean up between the two phone-landscape checks** with the `cleanly` wrapper the desktop profile has.
4. **Deadline 300 s, settable** with a `DEADLINE_MS` environment variable. The 25 s per-check limit stays, so
   a stuck check is still reported in 25 s; the deadline is only the cap on a browser that has died.

Not chosen: **retrying a press or tap** (the ticket's other option). A retry passes when the game drops a
real press (the kind of bug #195 was) and can apply a press twice: that loosens every assertion behind
it. Waiting for the release to be seen makes one press enough. Scaling the deadline from a measured
boot time was the close alternative to a fixed one; a single number that can be overridden is simpler to
reason about in a merge queue.

## Changes

### `gamev2/tools/browser/browser.js`

- Add and export `frames`:

  ```js
  // until the game has run `n` more frames: whatever went down or up before this has been read by the
  // game's once-a-frame input, at any frame rate
  async function frames(page, n = 2) {
      const from = await page.evaluate('window.game.loop.frame');
      try { await page.waitForFunction(`window.game.loop.frame >= ${from + n}`, null, { timeout: 5000 }); }
      catch (e) { throw new Error(`the game ran fewer than ${n} frames in 5s`); }
  }
  ```

  (`loop.frame` is Phaser's `TimeStep.frame`, incremented after each step's update; the game sets no fps
  limit, so one count is one update.)
- `hold()`: the last line becomes `await Promise.all([page.waitForTimeout(120), frames(page)]);`. Reword its
  comment: the key is held until `done()`, then let go until the game has run two frames with it up, because
  a release shorter than a frame is never seen and the next press of that key is then not a press.
- Top-of-file usage comment and `module.exports`: add `frames`.

### `gamev2/tools/browser/regress.js`

- **Run block** (end of file): replace the `side` promise with
  `await desktop(shared); await firstTime(); await phones(); await trips(shared);` and the comment with
  "one page at a time: a second page booting on the shared Chrome stalls the first one's frames (#238)".
- **`DEADLINE_MS`**: `const DEADLINE_MS = Number(process.env.DEADLINE_MS) || 300000;`, its comment and
  header line 6 reworded with the measured run times (fast machine, software GL). The failure message already
  prints the value.
- **`install()`**: add
  `keysUp: () => { const i = s.inputHandler, c = i.cursors; return [c.up, c.down, c.left, c.right, i.wKey, i.aKey, i.sKey, i.dKey, i.escKey, i.enterKey, i.spaceKey, i.shiftKey].every(k => !k.isDown); }`.
- **`tap()`**, beside `press()`, with the same shape:

  ```js
  /** A real tap on a touch button: over when the game has seen its key go up again. Returns whether `expr` became true. */
  async function tap(page, at, expr, ms = 1500) {
      await page.touchscreen.tap(at.x, at.y);
      const ok = await until(page, expr, ms);
      // the button holds its key 90ms and lets go on a timer: wait for that, not for a fixed time
      need(await until(page, '__t.keysUp()', 5000), 'a touch control never let go of its key');
      await frames(page);
      return ok;
  }
  ```

- **`phone-landscape-touch`**: the five `page.touchscreen.tap` calls and the `until` after each become
  `need(await tap(page, b, '<same expression>'), '<same message>')` (B opens the menu, B closes it, A starts
  the shift, B clocks off, B leaves), with the same 1500 ms bound. Delete the three `waitForTimeout(150)`.
  The last of them stood before the "no overlay, back at the desk" read so that a menu wrongly opened by that
  B had time to show; `tap()` has by then seen the key up and two frames run, which is at least as long. The
  `off` read stays between the two B taps where it is. The d-pad and sprint touches (CDP, waiting on
  `lifted()` / state) do not change.
- **`cleanly`**: move the wrapper out of `desktop()` to module level as
  `const cleaner = (page, errors) => async (name, fn) => { …same body… }`; `desktop()` gets
  `const cleanly = cleaner(page, errors);`. In `phones()`, the `phone-landscape` profile does the same and
  runs `phone-landscape-touch` and `phone-landscape-devhouse` through it. Keep both checks' own
  `need(errors.length === 0, { errors })` lines: they are stricter than the wrapper's.
- **`devhouseStair`**: after its `finally { await page.keyboard.up(key); }` add `await frames(page);` (the
  one key-up outside `hold()`).
- **Header rules**: the real-keys rule ends "held until the game has seen them, and let go until it has seen
  that too (`hold()`, `tap()`)"; add "never a fixed gap between two presses or taps".
- `frames` joins the `require('./browser')` line.

No other wait changes: the negative `hold(page, key, 'false', 200 / 450)` checks, the 3 s held key in
`devhouseStair` and the three-`requestAnimationFrame` idiom stay.

### `gamev2/tools/browser/README.md`

- "About 25 seconds" becomes the measured figures, and says the profiles run one page at a time and why.
- The `hold()` paragraph: also lets the key go until the game has run two frames; `frames(page)` is exported
  for a script that sends its own key-up; a phone tap goes through `tap()` in `regress.js`.
- `DEADLINE_MS` (default 300 s) beside `SHOTS`.

### `gamev2/tools/tests/browser-harness.test.js` (new)

The browser regression does not run in the Checks workflow, so two text pins keep the rule there
(`repo-layout.test.js` is the model for reading a file):

- `test('the browser regression never taps a touch button with a fixed wait after it (#238)', …)`:
  `regress.js` contains `page.touchscreen.tap(` exactly once (inside `tap()`).
- `test('hold() lets a key go until the game has run frames with it up (#238)', …)`: the body of `hold` in
  `browser.js` calls `frames(page)`.

The runner is synchronous and `browser.js` needs `playwright-core` to load, so the helpers themselves are
exercised only by the regression.

## Data and interfaces

- `browser.js` exports `frames(page, n = 2)`; `hold()` keeps its signature.
- `regress.js` reads a new optional environment variable `DEADLINE_MS` (milliseconds; default 300000).
- No game source, `config.json`, map or art change. No room is touched.

## Tests

Needs a browser: the ticket should carry the `workshop/needs:browser` label for Implementation. Start Chrome
with `chromium.launchServer({ port: 9333, host: '127.0.0.1', wsPath: 'pw' })`, serve `gamev2/`, then
`NODE_PATH=<dir holding playwright-core> PORT=<port> node tools/browser/regress.js`.

1. **Before any change**, on this branch: run it five times and once with the ticket's recipe (a temporary
   `await page.waitForTimeout(4000)` before `menu-entries`); keep the failures and run times as the baseline.
   If the container is too fast to fail, slow the page instead (temporary, never committed): in `open()`,
   `(await context.newCDPSession(page)).send('Emulation.setCPUThrottlingRate', { rate: 6 })`.
2. **After the change**: ten runs in a row print `24/24 checks passed`, with no assertion edited, plus three
   with whatever made step 1 fail (the 4 s wait, the throttle). Record the slowest and fastest run time; they
   go in the README and the deadline comment. If a throttled run trips the 25 s per-check limit, lower the
   rate: that is the throttle, not a finding.
3. `DEADLINE_MS=1000 node tools/browser/regress.js` exits 1 with the "did not finish within 1s" lines.
4. If the slowest clean run is over 150 s, say so in the summary rather than raising the deadline again.
5. From `gamev2/`: `node tools/test_game.js` (the two new tests), `python3 tools/test_blog_to_npc.py`,
   `node tools/play.js check`, `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`.

Nothing a player sees changes, so there is no play-through or screenshot to make beyond the regression's own.

## Risks and open questions

- **The cause is derived, not observed.** If step 1 shows presses lost with frames well under 120 ms, or
  step 2 still fails, stop and report what was seen (log the largest gap between two `postupdate`s around the
  failing press) instead of adding retries or widening a bound.
- **The clock-off failure is the least certain part.** Running one page at a time removes the stall this
  design blames; if it still fails alone on the browser, it is a different fault and belongs in the summary.
- **A slower run on a fast machine.** If the owner would rather keep two pages there, that is a switch to add
  later; it is left out because a mode nobody runs stops working.
- **A dead browser now holds the queue for up to 300 s** instead of 80 s (each stuck check still fails in
  25 s). `DEADLINE_MS` lowers it where that matters.
- `frames()` needs a booted game on the page and throws if a press itself reloads the page; no `hold()` or
  `tap()` does today (Time Travel is closed with ESC, and a date is set by `boot()`).
- The 120 ms in `hold()` is kept so that no check's timing changes on a fast machine. Dropping it would
  shorten the run; not in this change.
- Left alone, and worth knowing: a check that times out keeps running against its page; the negative
  `hold(…, 'false', 200)` checks prove little at a very low frame rate; and the game itself drops a press that
  follows a release of the same logical key inside one frame (ArrowDown then `s` in a menu during a long
  frame). That last one is game behaviour, outside this ticket.
