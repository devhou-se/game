# Browser regression (tools/browser)

`regress.js` drives the real game in a headless Chrome: boot as a returning and a first-time player, walking and
walls, a district seam (stitched and `?stitch=0`), a konbini in and out with its shop, a Devhouse in by its street
door and up its stair with the key held down (desktop and a landscape phone), NPC dialogue, the menu, Map and Time
Travel, a shift at the job in a tower lobby, a train ride, a trip day and a lead-in day, a landscape and a portrait
phone, night, and scenery fading over the player. It prints `ok` / `FAIL <name> <evidence>` per check and ends `N/N checks passed`
(exit 1 on any failure; any console or page error is a failure). About 25 seconds.

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
effect; a fixed short tap can be dropped when the frame rate dips. The one place a key is held for a fixed time is
`devhouseStair`: a room change does not let go of a held key, and `hold()` lets go the moment its condition is true,
which is the one moment a stair that bounces you between two floors cannot show.
