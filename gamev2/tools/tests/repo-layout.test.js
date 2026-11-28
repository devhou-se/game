// Issue #229: the Godot project left the repository. What gamev2 still needs from outside its own folder is
// the source art in ../art-source (the sheets tools/extract_*.py cut sprites from), and nothing in the game,
// its tools or the docs may point at what was removed.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const ROOT = path.join(GV2, '..');
    const GK = path.join(ROOT, 'art-source', 'GuttyKreum');
    // every sheet an extract tool reads, relative to art-source/GuttyKreum (a new one is added here too)
    const SHEETS = [
        'DotonboriCity_v3/RPGMakerVXAce/GK_DB_B.png',
        'DotonboriCity_v3/RPGMakerVXAce/GK_DB_F.png',
        'JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_B_2.png',
        'JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_C_2.png',
        'Osaka_V5/RPGMakerVXAce/GK_Osaka_C_2.png',
        'TemplesShrines_v2/Non-RPGMaker_Tilemap/Main_Tilemap.png',
        'TemplesandShrinesv2/MainTileMap/MainTileMap.png',
        'TemplesandShrinesv2/RPGMakerVXAce/GK_TS_A5.png',
        'TrainInteriors_v1/RPGMakerVXAce/GK_TI_A5.png',
        'TrainInteriors_v1/preview1.png',
        'TrainInteriors_v1/preview2.png',
        'TrainInteriors_v1/preview3.png',
        'Train_Stationv8/Tilemaps/Non-RPGMaker/Maintilemap.png',
        'UrbanAccessoriesv2/Tilemap.png',
    ];
    // files under dir (recursively) that `keep` accepts, as /-separated paths relative to dir
    const walk = (dir, keep, rel = '') => fs.readdirSync(path.join(dir, rel), { withFileTypes: true }).flatMap((e) => {
        const at = rel ? `${rel}/${e.name}` : e.name;
        if (e.isDirectory()) return e.name === 'node_modules' ? [] : walk(dir, keep, at);
        return keep(e.name) ? [at] : [];
    });

    test('the source art the extract tools name is in art-source (#229)', () => {
        assert.deepStrictEqual(walk(GK, (n) => n.endsWith('.png')).sort(), SHEETS.slice().sort(),
            'art-source/GuttyKreum holds exactly the sheets the extract tools read');
        const tools = fs.readdirSync(path.join(GV2, 'tools')).filter((n) => /^extract_.*\.py$/.test(n));
        assert.ok(tools.length >= 8, `found only ${tools.length} extract tools`);
        const sources = tools.map((n) => fs.readFileSync(path.join(GV2, 'tools', n), 'utf8'));
        tools.forEach((tool, i) => {
            // a quoted path to a sheet: not a sprite the tool writes, not an f-string template
            const named = Array.from(sources[i].matchAll(/'([^'\n]*\.png)'|"([^"\n]*\.png)"/g), (m) => m[1] || m[2])
                .filter((s) => s.includes('/') && !s.startsWith('assets/') && !s.includes('{'));
            for (const s of named) {
                assert.ok(SHEETS.includes(s.replace(/^\.\.\/art-source\/GuttyKreum\//, '')), `${tool} names ${s}, which is not a sheet in art-source`);
            }
        });
        for (const sheet of SHEETS) {
            assert.ok(sources.some((src) => src.includes(path.basename(sheet))), `no extract tool reads ${sheet}`);
        }
        // check_generators.py runs the tools in a scratch copy and must put the art beside it
        assert.ok(fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8').includes("'art-source'"),
            'check_generators.py links art-source beside its scratch project');
    });

    test('nothing points at the removed Godot project (#229)', () => {
        for (const gone of ['project.godot', 'game.sln', '.github/workflows/firebase-hosting-merge.yml']) {
            assert.ok(!fs.existsSync(path.join(ROOT, gone)), `${gone} is back`);
        }
        assert.ok(fs.existsSync(path.join(ROOT, 'AGENTS.md')), 'CLAUDE.md names AGENTS.md, so it exists');
        // paths and tools that left with it (art-source/README.md and docs/workshop/ quote them on purpose).
        // Its Assets folder is matched as a path: `Assets` alone is the game's loader helper (src/utils/Assets.js, #244)
        const GODOT = /\bAssets\/|\.\.\/Assets\b|Scenes\/|\.tscn|\.tres|doport|render_godot|render_rect|parse_godot|PORT_SCENE|project\.godot|some-assets|TeamFolders/;
        const dir = (rel, keep) => (fs.existsSync(path.join(ROOT, rel)) ? walk(path.join(ROOT, rel), keep).map((f) => `${rel}/${f}`) : []);
        const files = [
            ...dir('gamev2', (n) => /\.(py|js|md|html)$/.test(n)).filter((f) => f !== 'gamev2/tools/tests/repo-layout.test.js'),
            'CLAUDE.md', 'AGENTS.md', 'README.md', 'firebase.json',
            ...dir('.claude/skills', (n) => n === 'SKILL.md'),
            ...dir('.github/workflows', (n) => n.endsWith('.yml')),
        ];
        assert.ok(files.length > 200, `only ${files.length} files were read`);
        for (const f of files) {
            const hit = fs.readFileSync(path.join(ROOT, f), 'utf8').split('\n').findIndex((line) => GODOT.test(line));
            assert.ok(hit < 0, `${f}:${hit + 1} still points at the Godot project`);
        }
        // the deploy publishes the game and nothing else: the build of gamev2/ that tools/build_dist.js writes (#244)
        const hosting = JSON.parse(fs.readFileSync(path.join(ROOT, 'firebase.json'), 'utf8')).hosting;
        assert.deepStrictEqual(hosting.map((h) => [h.site, h.public]), [['devhouse-game-canvas', 'dist']]);
    });

    test('the skills name no room the world has lost (#266)', () => {
        // Machi, Inaka and Yukimura were deleted (#68) and the skills went on sending agents to them
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const known = new Set([...Object.keys(config.rooms), ...Object.keys(config.cities)]);
        const skills = walk(path.join(ROOT, '.claude', 'skills'), (n) => n === 'SKILL.md');
        assert.ok(skills.length >= 3, `found only ${skills.length} skills`);
        let named = 0;
        for (const f of skills) {
            fs.readFileSync(path.join(ROOT, '.claude', 'skills', f), 'utf8').split('\n').forEach((line, i) => {
                assert.ok(!/\b(Machi|Inaka|Yukimura)\b/.test(line), `${f}:${i + 1} names a town that was deleted`);
                // a room handed to a play.js command in an example (`<Room>` is a placeholder, not a name)
                for (const [, room] of line.matchAll(/\b(?:warp|goto|lint|render|reach|transporters) ([A-Z]\w*)/g)) {
                    assert.ok(known.has(room), `${f}:${i + 1} names ${room}, which is not a room or a city in config.json`);
                    named++;
                }
            });
        }
        assert.ok(named >= 5, `only ${named} rooms were read from the skills' examples`);
    });

    test('the deploy builds the game, publishes the build and caches the packs for ever (#244)', () => {
        const [hosting] = JSON.parse(fs.readFileSync(path.join(ROOT, 'firebase.json'), 'utf8')).hosting;
        // a pack's name is the hash of its bytes, so it never changes under a name; the page that names the
        // packs is checked with the server on every visit. Everything else keeps Firebase's default.
        const cache = (value) => [{ key: 'Cache-Control', value }];
        // (the pages, fonts and PNGs are revalidated too: hosting.test.js and the #241 test hold those rules)
        const packRules = hosting.headers.filter((h) => h.source === '/pack/**');
        assert.deepStrictEqual(packRules, [{ source: '/pack/**', headers: cache('public, max-age=31536000, immutable') }]);
        assert.ok(hosting.headers.some((h) => h.source === '/index.html' || h.source === '**/*.@(html|ttf)'), 'the page is revalidated');
        // the build writes where firebase.json publishes from, and that folder is not committed
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'build_dist.js'), 'utf8');
        assert.ok(tool.includes("path.join(ROOT, 'dist')"), 'build_dist.js writes ../dist by default');
        assert.strictEqual(hosting.public, 'dist');
        assert.ok(fs.readFileSync(path.join(ROOT, '.gitignore'), 'utf8').split('\n').includes('dist/'));

        // the workflow builds before it deploys, and "is the live site this commit" compares the built page
        const flow = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'firebase-hosting-gamev2.yml'), 'utf8');
        const at = (text) => { const i = flow.indexOf(text); assert.ok(i >= 0, `the deploy workflow has no ${text}`); return i; };
        assert.ok(at('actions/checkout@') < at('node tools/build_dist.js --commit "$GITHUB_SHA"'));
        assert.ok(at('node tools/build_dist.js --commit "$GITHUB_SHA"') < at('FirebaseExtended/action-hosting-deploy@'));
        assert.ok(!flow.includes('gamev2/index.html'), 'nothing compares the live site with the unbuilt page');
        assert.strictEqual(flow.split('/tmp/live.html dist/index.html').length - 1, 2, 'both verify steps compare dist/index.html');
        assert.ok(flow.includes('immutable'), 'the deploy checks the cache header of a pack');
    });

    test('a redrawn sprite is not drawn from the browser cache: the deploy has every PNG re-checked (#241)', () => {
        // the sprites are asked for with no cache-buster, and Firebase Hosting's default is max-age=3600: the ferris
        // wheel without its stray piece was live while a browser that had the old sprite drew that for an hour more
        const sprites = fs.readFileSync(path.join(GV2, 'src', 'systems', 'SpriteSystem.js'), 'utf8');
        assert.ok(sprites.includes('`assets/sprites/${spriteKey}.png`'), 'SpriteSystem loads assets/sprites/<key>.png as it is');
        const [site] = JSON.parse(fs.readFileSync(path.join(ROOT, 'firebase.json'), 'utf8')).hosting;
        const rules = (site.headers || []).filter((h) => h.source === '**/*.png');
        assert.strictEqual(rules.length, 1, 'firebase.json has one headers rule for **/*.png');
        assert.deepStrictEqual(rules[0].headers, [{ key: 'Cache-Control', value: 'no-cache' }]);
    });
};
