# Browser regression (tools/browser)

`regress.js` drives the real game in a headless Chrome: boot as a returning and a first-time player, walking and
walls, a district seam (stitched and `?stitch=0`), a konbini in and out with its shop, NPC dialogue, the menu, Map
and Time Travel, a shift at the job in a tower lobby, a train ride, a trip day and a lead-in day, a landscape and a portrait phone, night, and scenery
fading over the player. It prints `ok` / `FAIL <name> <evidence>` per check and ends `N/N checks passed`
(exit 1 on any failure; any console or page error is a failure). About 25 seconds.

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

`open()` options: `{ touch, mobile, width, height }` for a phone, `{ now: '2027-02-20T12:00:00' }` to stub the clock,
`{ fresh: true }` for a first-time player. `hold(page, key, doneFn)` holds a key until the game state says it took
effect; a fixed short tap can be dropped when the frame rate dips.
