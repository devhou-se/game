# Browser regression (tools/browser)

`regress.js` drives the real game in a headless Chrome: boot as a returning and a first-time player, walking and
walls, a district seam (stitched and `?stitch=0`), a konbini in and out with its shop, a Devhouse in by its street
door and up its stair with the key held down (desktop and a landscape phone), NPC dialogue, the menu, Map and Time
Travel, a shift at the job in a tower lobby, a train ride, a trip day and a lead-in day, a landscape and a portrait
phone, night, scenery fading over the player, getting into a bed and onto a chair (and, with the d-pad, a sofa), and the lift up Fukuoka
Tower with the key held down, its skip on the way down (an instant press, down and up with no hold), the deck by night and the ride's picture on both phones, and a turn on
Osaka's wheel (boarded by a bump, skipped, the key still held not boarding again). It prints `ok` / `FAIL <name> <evidence>` per check and ends `N/N checks passed`
(exit 1 on any failure; any console or page error is a failure). About 25 seconds.

The profiles (desktop, first-time, the two phones, the trip days) run one page at a time: a second page booting
on the shared Chrome stalls the first one's frames, and a press or a tap that lands in a stalled frame is lost
(#238). Two pages at a time a run took about 25 seconds on a fast machine and 75-90 seconds under software
WebGL; one page at a time is slower than that and has not been timed yet (put the figures here when it has),
so on a slow machine use `REGRESS_TIME_SCALE` (below).

A run that has not finished after 80 seconds, or a check that takes more than 25, is a failure: a stalled browser
must not hang the queue. On a slow machine (software WebGL on a loaded host, a Workshop container) see
"A slow machine" below.

It lives in the repo so that a change which deliberately alters behaviour updates the assertion in the same commit.
Update an assertion strictly; never loosen one to make it pass.

## Running it

It needs `playwright-core` and a Chrome it can connect to; neither is vendored.

- `browser.js` connects to ONE shared headless Chrome at `ws://127.0.0.1:9333/pw` (a playwright `launchServer`);
  each `open()` is its own isolated context. Launching a Chrome per script is slow and, with software WebGL, very
  heavy on the CPU.
- Serve `gamev2/` on a port (`python3 -m http.server 8000`) and run
  `NODE_PATH=<dir with playwright-core>/node_modules PORT=8000 node tools/browser/regress.js`.
- To check the game as it is deployed (one script bundle, the JSON and images in packs: "Loading and the
  deploy build" in `docs/architecture.md`), build it and serve the build instead:
  `node tools/build_dist.js`, then `python3 -m http.server 8001` from `../dist`, and `PORT=8001`. Do this for a
  change to what the game loads, to `index.html`'s script list or to the build. `window.GAME_BUILD` is set
  only in the built page.
- `smoke.js` is the smallest example: it boots the game and fails on any error.
- Screenshots go to `$SHOTS` (default: a folder in the system temp directory).

### A slow machine

`REGRESS_TIME_SCALE=<n>` multiplies the two time limits, the 80 seconds for the whole run and the 25 seconds for
one check, and nothing else: `REGRESS_TIME_SCALE=2 PORT=8000 node tools/browser/regress.js` allows 160 seconds
and 50 per check. A number from 1 to 100; unset is 1; anything else fails the run at once. The run's first line
says when the limits are stretched, so a log shows it.

- Use it when an unchanged run ends `the suite did not finish within 80s` or a check `timed out after 25s` with a
  different check in flight each time: the machine is slow, not the game. A Workshop container has needed 90 to
  130 seconds for the suite, so 2 is a fair start there.
- It does not loosen an assertion. The waits on game state inside a check (`hold()`, `until()`, `idle()`) and
  everything a check compares stay as written, so a failure with evidence other than those two messages is a
  real failure at any scale.
- The limits and the variable are read in `limits.js` (`tools/tests/browser-regress.test.js` holds them).

`open()` options: `{ touch, mobile, width, height }` for a phone, `{ now: '2027-02-20T12:00:00' }` to stub the clock,
`{ fresh: true }` for a first-time player. `hold(page, key, doneFn)` holds a key until the game state says it took
effect, then lets it go until the game has run two frames with it up. The game reads the keys once a frame: a fixed
short tap can be dropped when the frame rate dips, and a release shorter than a frame is never seen, so the next
press of that key is not a press. `frames(page)` is that wait by itself, for a script that sends its own key-up; a
tap on a touch button goes through `tap()` in `regress.js`, which waits for the button to let go of its key the
same way. Never put a fixed gap between two presses or taps. The one place a key is held for a fixed time is
`devhouseStair`: a room change does not let go of a held key, and `hold()` lets go the moment its condition is true,
which is the one moment a stair that bounces you between two floors cannot show.

### The menu's cursor

`menu.js` moves the ESC menu's cursor (#252). The game reads its keys once a frame and moves the cursor when a key
goes down, so a key let go and pressed again between two frames was never up as far as the game saw, and the second
press moves nothing. On a slow machine a frame is longer than the 120 ms `hold()` leaves after a key: the menu checks
failed with `could not move the menu cursor to 9` or `{"couldNotReach":"Career","selected":4}`, the cursor one row
short.

- `menu.step(page, key)` is one press: down until the cursor has left its row, up until the game has run two frames
  with it up, and it returns the row the cursor is on then. `menu-entries` asserts on that row, one row a press.
- `menu.moveTo(page, row)` walks to a row the short way round, choosing the way again from where the cursor is
  after every press. It returns `{ at, rows }`; a check that could not get there fails with `rows`, every row the
  cursor was on, which shows a press that moved nothing (a row twice) or one that moved two.
- `menu.frames(page)` is the wait by itself, for the same key twice in a row through `press()` (ESC to open the
  menu, ESC to close it).

Do not hold a key until the cursor is on a row you worked out from the presses sent. `menu.js` takes the page as an
argument and needs no playwright, so `tools/tests/browser-regress.test.js` runs it against a page whose game is the
real `InputHandler` at frame times from 16 ms to 2.4 s.
