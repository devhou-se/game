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
        // paths and tools that left with it (art-source/README.md and docs/workshop/ quote them on purpose)
        const GODOT = /\bAssets\b|Scenes\/|\.tscn|\.tres|doport|render_godot|render_rect|parse_godot|PORT_SCENE|project\.godot|some-assets|TeamFolders/;
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
        // the deploy publishes the game and nothing else
        const hosting = JSON.parse(fs.readFileSync(path.join(ROOT, 'firebase.json'), 'utf8')).hosting;
        assert.deepStrictEqual(hosting.map((h) => [h.site, h.public]), [['devhouse-game-canvas', 'gamev2']]);
    });
};
