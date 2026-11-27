// The ESC menu's cursor, moved with real keys at any frame rate (#252):
//
//   const menu = require('./menu');
//   const row = await menu.step(page, 'ArrowDown');     // one press; the row the cursor is on afterwards
//   const { at, rows } = await menu.moveTo(page, 7);    // onto row 7, the short way round
//
// The game reads its keys once a frame and moves the cursor when one goes down. A key let go and pressed
// again between two frames was never up as far as the game saw, so the second press moves nothing; on a slow
// machine a frame is longer than any fixed gap between two presses. So a press here is over when the game has
// run frames with the key up (frames()), and where the cursor is gets read again after every press: it is
// never taken from the number of presses sent.
//
// No dependencies: it is handed the playwright page, so the unit tests run it against a page of their own
// (tools/tests/browser-regress.test.js). `__t` is regress.js' in-page helper (install()).
const CURSOR = '__t.s.menuManager.selectedIndex';
const ROWS = '__t.s.menuManager.options.length';
const DOWN = 's', UP = 'ArrowUp';

/** Until the game has run `n` more frames: whatever went down or up before this has been read by its once-a-frame input. */
async function frames(page, n = 2) {
    const from = await page.evaluate('__t.frames');
    try { await page.waitForFunction(`__t.frames >= ${from + n}`, null, { timeout: 5000 }); }
    catch (e) { throw new Error(`the game ran fewer than ${n} frames in 5s`); }
}

/**
 * One press of a menu key: down until the cursor has left its row (at most `ms`), then up until the game has
 * seen it up. Returns the row the cursor is on afterwards, which the caller compares: a press that moved
 * nothing returns the row it started on.
 */
async function step(page, key, ms = 1500) {
    const from = await page.evaluate(CURSOR);
    await page.keyboard.down(key);
    try { await page.waitForFunction(`${CURSOR} !== ${from}`, null, { timeout: ms }); } catch (e) { /* the row is read below */ }
    await page.keyboard.up(key);
    await frames(page);
    return page.evaluate(CURSOR);
}

/** The short way round a list of `n` rows that wraps, from row `from` to row `to`: { dir: 1 (down) or -1 (up), steps }. */
function route(from, to, n) {
    const down = (((to - from) % n) + n) % n;
    return down <= n - down ? { dir: 1, steps: down } : { dir: -1, steps: n - down };
}

/**
 * Put the open menu's cursor on row `to`: one press at a time, the way chosen again from where the cursor
 * really is after each, so a press that moved nothing is sent again and one that went too far is walked back.
 * At most one press per row of the menu. Returns { at, rows }: the row it ended on (the caller compares it
 * with `to`) and every row the cursor was on, the starting one first.
 */
async function moveTo(page, to) {
    const n = await page.evaluate(ROWS);
    const rows = [await page.evaluate(CURSOR)];
    for (let presses = 0; rows[rows.length - 1] !== to && presses < n; presses++) {
        rows.push(await step(page, route(rows[rows.length - 1], to, n).dir > 0 ? DOWN : UP));
    }
    return { at: rows[rows.length - 1], rows };
}

module.exports = { frames, step, route, moveTo };
