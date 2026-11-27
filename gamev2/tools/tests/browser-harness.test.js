// Issue #238: the browser regression (tools/browser) lost key presses and taps on a slow machine. The game
// reads its keys once a frame, so a key must stay up until the game has run frames with it up, and a tap is
// over when its button has let go of its key: never after a fixed time. The regression itself is not in the
// Checks workflow (it needs a Chrome), so the rule is pinned in the text of the harness here.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const read = (name) => fs.readFileSync(path.join(GV2, 'tools', 'browser', name), 'utf8');
    // the source of `async function <name>(...) { ... }` at the top level of a file
    const body = (src, name) => {
        const from = src.indexOf(`\nasync function ${name}(`);
        assert.ok(from >= 0, `no async function ${name}`);
        return src.slice(from, src.indexOf('\n}\n', from));
    };

    test('the browser regression never taps a touch button with a fixed wait after it (#238)', () => {
        const src = read('regress.js');
        // the other direct tap is on the lift ride's picture (a skip, no button), not a touch button
        assert.strictEqual(src.split('page.touchscreen.tap(').length - 1, 2, 'every touch button tap goes through tap()');
        const tap = body(src, 'tap');
        assert.ok(tap.includes('page.touchscreen.tap('), 'tap() is the one place a touch button is tapped');
        assert.ok(tap.includes('__t.keysUp()') && tap.includes('await frames(page)'),
            'tap() waits for the button to let go of its key, then for the game to have seen that');
        assert.ok(!tap.includes('waitForTimeout'), 'tap() waits on the game, not for a fixed time');
        // what it waits on is there: the in-page helper, and frames() from browser.js
        assert.ok(/\bkeysUp: \(\) =>/.test(src), 'install() defines __t.keysUp');
        assert.ok(/const \{[^}]*\bframes\b[^}]*\} = require\('\.\/browser'\)/.test(src), 'regress.js takes frames from browser.js');
    });

    test('hold() lets a key go until the game has run frames with it up (#238)', () => {
        const src = read('browser.js');
        const hold = body(src, 'hold');
        const up = hold.indexOf('page.keyboard.up(key)');
        assert.ok(up >= 0 && hold.indexOf('frames(page)', up) > up, 'hold() waits frames(page) after the key-up');
        // frames() counts the game loop's own frames, and says so when there are none
        const frames = body(src, 'frames');
        assert.ok(frames.includes('window.game.loop.frame') && frames.includes('throw new Error('), 'frames() counts game frames');
        assert.ok(/module\.exports = \{[^}]*\bframes\b[^}]*\}/.test(src), 'browser.js exports frames');
    });

    test('the browser regression runs one page at a time (#238)', () => {
        const src = read('regress.js');
        const run = src.slice(src.lastIndexOf('(async () => {'));
        const order = ['await desktop(shared);', 'await firstTime();', 'await phones();', 'await trips(shared);'].map((c) => run.indexOf(c));
        assert.ok(order.every((at, i) => at >= 0 && (i === 0 || at > order[i - 1])), 'the profiles are awaited in turn');
        assert.ok(!/=\s*\(?(async\b|desktop\(|firstTime\(|phones\(|trips\()/.test(run.replace('(async () => {', '')),
            'no profile is started and awaited later');
    });
};
