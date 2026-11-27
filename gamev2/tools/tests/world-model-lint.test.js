module.exports = ({ test, assert, fs, path, GV2, game, worldWith, require }) => {
    test('lint reachability starts where the player arrives, not at a fixed cell', () => {
        const walkedFrom = game('WorldModel.walkedFrom');
        // A sealed 1-cell pocket at 0,0 (the old seed), a 2x3 hall, and a 2-cell closet.
        const cells = new Set(['0,0', '2,0', '3,0', '2,1', '3,1', '2,2', '3,2', '6,0', '6,1']);
        const sorted = (set) => [...set].sort().join(' ');
        const hall = '2,0 2,1 2,2 3,0 3,1 3,2';
        assert.strictEqual(sorted(walkedFrom(cells, [[3, 2]])), hall, 'floods from the arrival cell');
        assert.strictEqual(sorted(walkedFrom(cells, [[3, 2], [6, 1]])), hall + ' 6,0 6,1', 'every arrival counts');
        assert.strictEqual(sorted(walkedFrom(cells, [[5, 5]])), hall, 'a blocked arrival falls back to the largest area');
        assert.strictEqual(sorted(walkedFrom(cells, [])), hall, 'so does a room nothing leads to');
        assert.strictEqual(walkedFrom(new Set(), [[0, 0]]).size, 0);
    });

    test('lint lets the player stand at a shrine roof\'s eave tips, but not under the roof', () => {
        const overheadCols = game('WorldModel.overheadCols');
        assert.strictEqual(overheadCols('shrine-top', 5).join(), '1,2,3', 'the eave columns are not under the roof');
        assert.strictEqual(overheadCols('red-shrine-top', 5).join(), '1,2,3');
        assert.strictEqual(overheadCols('temple-hallway-top', 4).join(), '0,1,2,3', 'any other overhead sprite is checked edge to edge');
        // ...and the art agrees: those two bottom-row corner cells are all but empty
        const png = require('./png');
        for (const key of ['shrine-top_0_0', 'red-shrine-top_0_0']) {
            const { width, height, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', key + '.png')));
            assert.deepStrictEqual([width, height], [320, 384]);
            for (const col of [0, 4]) {
                let opaque = 0;
                for (let y = height - 64; y < height; y++) for (let x = col * 64; x < col * 64 + 64; x++) if (data[(y * width + x) * 4 + 3]) opaque++;
                assert.ok(opaque < 64 * 64 * 0.15, `${key} column ${col}: ${opaque}px of roof in the bottom cell`);
            }
        }
    });

    // (the shrine-seal test - every hall sealed as the `shrine` prefab seals it, except its one door
    // cell - is in shrines.test.js since the halls became enterable, #212)

    test('the headless world model is stopped by collision tiles, like the game', () => {
        const WorldModel = game('WorldModel');
        // a 4x3 room: a wall tile at 2,1 on a collision layer, a rug at 1,2 on a plain one
        const config = {
            game: { gridSize: 64, worldWidth: 256, worldHeight: 192 },
            player: { startRoom: 'Hall', startX: 1, startY: 1, sprite: 'bailey_front' },
            rooms: { Hall: { name: 'Hall', objects: [], transporters: [], npcs: [], layers: [
                { name: 'floor', z: 0, tiles: { '1,2': 'rug' } },
                { name: 'walls', z: 1, collision: true, tiles: { '2,1': 'wall' } },
            ] } },
        };
        const w = new WorldModel(config, { exists: () => true, sizeOf: () => [1, 1] }, { date: '2025-10-10' });
        assert.strictEqual(w.roomManager.isBlocked(2, 1), true, 'the room manager knows the collider');
        assert.strictEqual(w.canStep(1, 1, 2, 1), false, 'a collision tile blocks the step');
        assert.strictEqual(w.canStep(1, 1, 1, 2), true, 'a tile on a non-collision layer does not');
        assert.strictEqual(w.canStep(1, 1, 0, 1), true, 'nor does bare floor');
        assert.strictEqual(w.canStep(0, 1, -1, 1), false, 'the room edge still does');
    });

    test('the world check flags a trip stay with no cell (players would start at the trip home instead)', () => {
        const WorldModel = game('WorldModel');
        const room = (name) => ({ name, objects: [], npcs: [], layers: [], transporters: [
            { gridX: 0, gridY: 0, targetRoom: name === 'North' ? 'South' : 'North', targetX: 1, targetY: 1 }] });
        const config = (south) => ({
            game: { gridSize: 64, worldWidth: 256, worldHeight: 192 },
            player: { startRoom: 'North', startX: 1, startY: 1, sprite: 'bailey_front' },
            rooms: { North: room('North'), South: room('South') },
            trips: [{ id: 't', start: '2031-01-01', end: '2031-01-09', members: [], home: { room: 'North', x: 1, y: 1 },
                stays: [{ from: '2031-01-01', room: 'North', x: 1, y: 1 }, south] }],
        });
        const found = (south) => new WorldModel(config(south), { exists: () => true, sizeOf: () => [1, 1] }, { date: '2031-01-02' })
            .survey(['2031-01-02']).problems.filter(p => /has no cell/.test(p.text));
        assert.strictEqual(found({ from: '2031-01-06', room: 'South', x: 2, y: 1 }).length, 0, 'a stay with a cell is fine');
        const bad = found({ from: '2031-01-06', room: 'South' });
        assert.strictEqual(bad.length, 1, 'one problem for the stay without x, y');
        assert.strictEqual(bad[0].room, 'South');
        // which is what the game would do with it: fall back to the trip's home, in the other room
        assert.strictEqual(game('Trips').homeFor(config({ from: '2031-01-06', room: 'South' }), '2031-01-07').room, 'North');
    });

    test('check reports every room\'s lint errors: a store cut off from its door', () => {
        assert.strictEqual(JSON.stringify(worldWith(true).world.lintProblems()), '[]', 'the committed world is lint-clean');
        // wall off the row inside KonbiniMarket1's door: transporters and NPCs are still
        // fine, so the survey sees nothing, but no shelf can be walked up to
        const cut = worldWith(true, (config) => {
            const room = config.rooms.KonbiniMarket1, y = room.transporters[0].gridY - 2;
            for (let x = 0; x < room.worldWidth / 64; x++) room.layers.find(l => l.collision).tiles[x + ',' + y] = 'gk_blank';
        }).world;
        const problems = cut.lintProblems();
        assert.ok(problems.length && problems.every(q => q.room === 'KonbiniMarket1'), JSON.stringify(problems));
        assert.ok(problems.some(q => /^lint shop-no-front: \d+ \(/.test(q.text)), JSON.stringify(problems));
    });

    test('play.js check exits 1 when it lists problems, 0 when the world is clean (#188)', () => {
        const { spawnSync } = require('child_process');
        const os = require('os');
        const run = (gv2) => spawnSync(process.execPath, [path.join(gv2, 'tools', 'play.js'), 'check'], { encoding: 'utf8' });
        const clean = run(GV2);
        assert.strictEqual(clean.stdout.trim(), 'no problems found');
        assert.strictEqual(clean.status, 0);
        // a copy of the model (play.js reads the world next to itself) whose player.start drifted off the first trip's home
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-check-'));
        try {
            fs.cpSync(path.join(GV2, 'src'), path.join(tmp, 'src'), { recursive: true });
            fs.mkdirSync(path.join(tmp, 'tools'));
            for (const f of ['play.js', 'png.js', 'world-model.js']) fs.copyFileSync(path.join(GV2, 'tools', f), path.join(tmp, 'tools', f));
            fs.symlinkSync(path.join(GV2, 'assets'), path.join(tmp, 'assets'));
            const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
            config.player.startX += 1;
            fs.writeFileSync(path.join(tmp, 'config.json'), JSON.stringify(config));
            const broken = run(tmp);
            assert.ok(/^error: [^]*\n\d+ problems\n$/.test(broken.stdout), broken.stdout + broken.stderr);
            assert.strictEqual(broken.status, 1);
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });

    test('play.js map draws every interaction as one glyph, so the columns stay under the ruler (#236)', () => {
        const { spawnSync } = require('child_process');
        const os = require('os');
        // a room for each group that had no glyph: flavour, flights, water, shrine, temple, palace
        const ROOMS = {
            DevhouseOsaka4F: ['* 9,5 goldfish'], DevhouseTokyo4F: ['* 6,4 bunk', '* 6,5 bunk'], HanedaAirport: [/^\^ \d+,\d+ flights$/],
            KonbiniMarket1: [/^% \d+,\d+ water$/, /^\$ \d+,\d+ counter$/], ShrineTokyo1: [/^\+ \d+,\d+ offering$/, /^\+ \d+,\d+ omikuji$/],
            TempleMarket1: [/^\+ \d+,\d+ incense$/], PalaceHallTokyo1: [/^\+ \d+,\d+ audience$/],
        };
        // the session is kept in the temp directory: a scratch one, so the player's own is left alone
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-map-'));
        let run;
        try {
            run = spawnSync(process.execPath, [path.join(GV2, 'tools', 'play.js')], { encoding: 'utf8', maxBuffer: 1 << 26,
                input: Object.keys(ROOMS).map((r) => `warp ${r}\nmap\nlook 3\n`).join(''), env: { ...process.env, TMPDIR: tmp, TMP: tmp, TEMP: tmp } });
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
        assert.strictEqual(run.status, 0, run.stdout + run.stderr);
        assert.ok(!run.stdout.includes('undefined'), run.stdout);
        const maps = run.stdout.split(/^> warp /m).slice(1);
        assert.deepStrictEqual(maps.map((m) => m.split('\n')[0]), Object.keys(ROOMS));
        for (const text of maps) {
            const lines = text.split('\n'), room = lines[0];
            // the two rulers and every row of both maps: one character a cell
            for (const drawn of text.split(/^> (?:map|look 3)$/m).slice(1)) {
                const rows = drawn.split('\n').filter((l) => /^[ \d]{3} /.test(l));
                assert.ok(rows.length > 4, `${room}: ${drawn}`);
                for (const row of rows) assert.strictEqual(row.length, rows[0].length, `${room}: "${row}"`);
            }
            for (const note of ROOMS[room]) {
                assert.ok(lines.some((l) => (note instanceof RegExp ? note.test(l) : l === note)), `${room} has no note ${note}:\n${text}`);
            }
        }
        // a group with no glyph of its own still draws as one character, and the legend names every glyph
        const play = fs.readFileSync(path.join(GV2, 'tools', 'play.js'), 'utf8');
        const glyphs = new Function('return ' + /const GLYPH = (\{[^}]*\});/.exec(play)[1])();
        const other = /const OTHER = '(.)';/.exec(play)[1];
        assert.ok(play.includes('GLYPH[i.group] || OTHER'));
        const legend = /'Legend: [^\n]*'/.exec(play)[0];
        for (const g of new Set(Object.values(glyphs).concat(other))) {
            assert.strictEqual(g.length, 1);
            assert.ok(legend.includes(`  ${g} `), `the legend does not name ${g}`);
        }
        const groups = new Set(game('Interactions.RULES').map((r) => r.group).concat('drinking-game'));
        for (const g of groups) assert.ok(glyphs[g], `no glyph for the ${g} group`);
    });
};
