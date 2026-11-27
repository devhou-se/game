// Issue #248: the browser regression's two time limits (the whole run, any one check) can be stretched on a
// slow machine with REGRESS_TIME_SCALE; unset, they are what they were. No browser is needed here: the limits
// are read by tools/browser/limits.js, and regress.js is run against a playwright-core that refuses to connect.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const os = require('os');
    const { limits } = require(path.join(GV2, 'tools', 'browser', 'limits.js'));

    // regress.js with `env` added, and no browser to connect to: { status, lines }
    const regress = (env) => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'browser-regress-'));
        try {
            const stub = path.join(tmp, 'node_modules', 'playwright-core');
            fs.mkdirSync(stub, { recursive: true });
            fs.writeFileSync(path.join(stub, 'index.js'), "module.exports = { chromium: { connect: async () => { throw new Error('stub: no browser'); } } };\n");
            const base = { ...process.env, NODE_PATH: path.join(tmp, 'node_modules'), SHOTS: path.join(tmp, 'shots') };
            delete base.REGRESS_TIME_SCALE;
            const run = spawnSync(process.execPath, [path.join(GV2, 'tools', 'browser', 'regress.js')], { cwd: GV2, encoding: 'utf8', timeout: 60000, env: { ...base, ...env } });
            assert.ok(!run.error, `regress.js did not finish: ${run.error}`);
            return { status: run.status, lines: run.stdout.trim().split('\n') };
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };

    test('browser regression: REGRESS_TIME_SCALE multiplies the run and the per-check limit, and unset they are 80s and 25s (#248)', () => {
        assert.deepStrictEqual(limits({}), { scale: 1, deadlineMs: 80000, checkMs: 25000 });
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '' }), limits({}));
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '1' }), limits({}));
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '2' }), { scale: 2, deadlineMs: 160000, checkMs: 50000 });
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '1.5' }), { scale: 1.5, deadlineMs: 120000, checkMs: 37500 });
        assert.deepStrictEqual(limits({ REGRESS_TIME_SCALE: '100' }), { scale: 100, deadlineMs: 8000000, checkMs: 2500000 });
    });

    test('browser regression: a REGRESS_TIME_SCALE that would shorten the limits, or is not a plain number, is refused (#248)', () => {
        for (const bad of ['0', '0.5', '0.99', '-2', '100.5', '101', 'abc', '2x', '2s', ' 2', '1e1', '0x10', 'Infinity', 'NaN', 'true']) {
            assert.throws(() => limits({ REGRESS_TIME_SCALE: bad }), /REGRESS_TIME_SCALE must be a number from 1 to 100/, `accepted ${JSON.stringify(bad)}`);
        }
    });

    test('browser regression: regress.js says when its limits are stretched, and fails at once on a bad REGRESS_TIME_SCALE (#248)', () => {
        const said = (lines) => lines.filter((l) => /REGRESS_TIME_SCALE/.test(l));
        // as committed: no word about a scale, and with no browser every profile fails
        const plain = regress({});
        assert.strictEqual(plain.status, 1, plain.lines.join('\n'));
        assert.deepStrictEqual(said(plain.lines), []);
        assert.ok(plain.lines.some((l) => /^FAIL desktop-profile stub: no browser/.test(l)), plain.lines.join('\n'));
        // stretched: the first line gives both limits; the run itself is the same
        const slow = regress({ REGRESS_TIME_SCALE: '3' });
        assert.strictEqual(slow.status, 1, slow.lines.join('\n'));
        assert.strictEqual(slow.lines[0], 'REGRESS_TIME_SCALE=3: the run may take 240s and a check 75s; the assertions are unchanged');
        assert.deepStrictEqual(slow.lines.slice(1).filter((l) => /^(ok|FAIL) /.test(l)).map((l) => l.replace(/\(\d+ms\)$/, '')),
            plain.lines.filter((l) => /^(ok|FAIL) /.test(l)).map((l) => l.replace(/\(\d+ms\)$/, '')));
        // refused: one harness failure, in the run's own words, and no check is started
        const bad = regress({ REGRESS_TIME_SCALE: '0.5' });
        assert.strictEqual(bad.status, 1, bad.lines.join('\n'));
        assert.deepStrictEqual(bad.lines, ['FAIL harness REGRESS_TIME_SCALE must be a number from 1 to 100 (1 is the usual limits), not "0.5"', '0/1 checks passed']);
    });
};
