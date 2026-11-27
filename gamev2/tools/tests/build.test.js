// Issue #244: the deployed game is built by tools/build_dist.js — one script bundle and three packs with
// content-hashed names, named by the built index.html — and the game loads its files through
// src/utils/Assets.js, which hands back the file itself (unbuilt) or its copy in a pack (built).
// The build decides what to pack by running GameScene's own loading code, so these tests are also what
// keeps the built and the unbuilt game loading the same things.
module.exports = ({ test, assert, fs, path, vm, GV2, require }) => {
    const os = require('os');
    const crypto = require('crypto');
    const { build, scriptList, recordLoads } = require('./build_dist');
    const hashOf = (buffer) => crypto.createHash('sha256').update(buffer).digest('hex').slice(0, 12);
    const source = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');

    // one build (packs and index.html only) shared by the tests below, read into memory and removed
    let made = null;
    const built = () => {
        if (made) return made;
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-build-'));
        try {
            const out = path.join(tmp, 'dist');
            const result = build({ out, commit: 'abc123', copy: false });
            const pack = {};
            for (const name of fs.readdirSync(path.join(out, 'pack'))) pack[`pack/${name}`] = fs.readFileSync(path.join(out, 'pack', name));
            made = { result, pack, index: fs.readFileSync(path.join(out, 'index.html'), 'utf8'), top: fs.readdirSync(out).sort() };
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
        return made;
    };

    test('the page marks what the build replaces, and the script list is between the marks (#244)', () => {
        const html = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
        for (const mark of ['<!-- build:head -->', '<!-- build:scripts -->', '<!-- /build:scripts -->']) {
            assert.strictEqual(html.split(mark).length, 2, `exactly one ${mark}`);
        }
        const head = html.indexOf('<head>'), mark = html.indexOf('<!-- build:head -->');
        assert.strictEqual(html.slice(head + '<head>'.length, mark).trim(), '', 'build:head is the first thing in <head>');
        const files = scriptList(html);
        // every src/*.js the page names is in the list, and is a file
        const named = Array.from(html.matchAll(/'(src\/[\w./-]+\.js)'/g), (m) => m[1]);
        assert.deepStrictEqual(files, named, 'no script is listed outside the marks');
        assert.ok(files.length > 40, `only ${files.length} scripts`);
        for (const f of files) assert.ok(fs.existsSync(path.join(GV2, f)), `${f} is listed and missing`);
        // Assets is defined before the two files that call it while loading, and game.js starts the game last
        assert.ok(files.indexOf('src/utils/Assets.js') >= 0, 'Assets.js is listed');
        assert.ok(files.indexOf('src/utils/Assets.js') < files.indexOf('src/systems/SpriteSystem.js'));
        assert.ok(files.indexOf('src/utils/Assets.js') < files.indexOf('src/GameScene.js'));
        assert.strictEqual(files[files.length - 1], 'src/game.js');
        // the page still boots unbuilt: no GAME_BUILD in the source
        assert.ok(!html.includes('GAME_BUILD'));
    });

    test('the built page loads the bundle and names exactly the files in pack/ (#244)', () => {
        const { result, pack, index, top } = built();
        assert.deepStrictEqual(top, ['index.html', 'pack'], 'copy: false writes only the page and the packs');
        assert.ok(!/<script[^>]*\ssrc="src\/|'src\//.test(index), 'no src/ script is left in the built page');
        assert.ok(!index.includes('Date.now'), 'no cache-buster is left in the built page');
        assert.ok(!index.includes('build:'), 'the marks are gone');
        const named = Array.from(index.matchAll(/pack\/[\w.]+/g), (m) => m[0]);
        assert.deepStrictEqual(Array.from(new Set(named)).sort(), Object.keys(pack).sort());
        assert.deepStrictEqual(Object.keys(pack).sort(), Object.values(result.files).sort());
        // each name carries the hash of its bytes
        for (const [kind, ext] of [['game', 'js'], ['data', 'json'], ['images', 'bin'], ['photos', 'bin']]) {
            const file = result.files[kind];
            assert.strictEqual(file, `pack/${kind}.${hashOf(pack[file])}.${ext}`);
        }
        // GAME_BUILD names the three packs and the commit; the bundle is the one script after it
        const m = index.match(/<script>window\.GAME_BUILD = (\{[^<]*\});<\/script>\s*<script src="([^"]+)"><\/script>/);
        assert.ok(m, 'GAME_BUILD is set right before the bundle');
        assert.deepStrictEqual(JSON.parse(m[1]), { commit: 'abc123', data: result.files.data, images: result.files.images, photos: result.files.photos });
        assert.strictEqual(m[2], result.files.game);
        assert.ok(index.indexOf('phaser') < index.indexOf(m[0]), 'Phaser is loaded before the bundle');
        // the two packs the boot waits for are hinted, the photos (fetched after it) are not
        const hints = Array.from(index.matchAll(/<link rel="preload" as="fetch" crossorigin href="([^"]+)">/g), (h) => h[1]);
        assert.deepStrictEqual(hints, [result.files.data, result.files.images]);
        // browsers look for the charset in the first 1024 bytes
        assert.ok(Buffer.byteLength(index.slice(0, index.indexOf('<meta charset'))) < 900, 'the hints do not push the charset down');
        // the rest of the page is the source page
        const html = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
        assert.strictEqual(index.slice(index.indexOf(m[0]) + m[0].length), html.slice(html.indexOf('<!-- /build:scripts -->') + '<!-- /build:scripts -->'.length));
    });

    test('the bundle is every listed script once, in the page\'s order, and compiles (#244)', () => {
        const { result, pack } = built();
        const bundle = pack[result.files.game].toString('utf8');
        const files = scriptList(fs.readFileSync(path.join(GV2, 'index.html'), 'utf8'));
        assert.deepStrictEqual(result.scripts, files);
        let at = 0;
        for (const f of files) {
            const text = `// ${f}\n${fs.readFileSync(path.join(GV2, f), 'utf8')}`;
            assert.strictEqual(bundle.indexOf(text, at), at, `${f} is next in the bundle, whole`);
            at += text.length;
            if (f !== files[files.length - 1]) {
                assert.strictEqual(bundle.slice(at, at + 3), '\n;\n', `${f} is closed off from the next file`);
                at += 3;
            }
        }
        assert.strictEqual(at, bundle.length, 'and nothing else');
        assert.doesNotThrow(() => new vm.Script(bundle, { filename: result.files.game }));
        // one script now: a file that declared strict mode would change the files after it
        for (const f of files) assert.ok(!/^\s*['"]use strict['"]/m.test(fs.readFileSync(path.join(GV2, f), 'utf8')), `${f} is strict`);
    });

    test('the packs hold what the game loads, byte for byte (#244)', () => {
        const { result, pack } = built();
        const data = JSON.parse(pack[result.files.data].toString('utf8'));
        assert.deepStrictEqual(Object.keys(data), ['json', 'images', 'photos']);
        const { loads } = result;
        assert.deepStrictEqual(Object.keys(data.json).sort(), loads.json);
        assert.deepStrictEqual(Object.keys(data.images), loads.images, 'images are packed in sorted order');
        assert.deepStrictEqual(Object.keys(data.photos), loads.photos);
        for (const file of loads.json) {
            assert.deepStrictEqual(data.json[file], JSON.parse(fs.readFileSync(path.join(GV2, file), 'utf8')), file);
        }
        for (const [index, file] of [[data.images, result.files.images], [data.photos, result.files.photos]]) {
            let end = 0;
            for (const [name, [offset, length]] of Object.entries(index)) {
                assert.strictEqual(offset, end, `${name} follows the file before it`);
                assert.ok(pack[file].subarray(offset, offset + length).equals(fs.readFileSync(path.join(GV2, name))), `${name} is not its file`);
                end = offset + length;
            }
            assert.strictEqual(end, pack[file].length, `${file} holds nothing else`);
        }
        // what the game is known to load is there
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        for (const file of ['config.json', 'assets/map/world-map.json', 'assets/map/japan.json', 'assets/ads/manifest.json',
            'assets/items/manifest.json', 'assets/portraits/manifest.json']) assert.ok(file in data.json, file);
        for (const room of Object.keys(config.rooms)) {
            const tmj = `tiled/${room.toLowerCase()}.tmj`;
            assert.strictEqual(tmj in data.json, fs.existsSync(path.join(GV2, tmj)), tmj);
        }
        for (const file of ['assets/single-tile.png', 'assets/map/japan.png', 'assets/sprites/james_front_frame_0.png']) assert.ok(file in data.images, file);
        // files a manifest names, and the frames of an animated sprite (the item and portrait manifests are empty today)
        assert.ok(loads.images.some((f) => f.startsWith('assets/ads/')) && loads.images.some((f) => /_frame_\d+\.png$/.test(f)));
        assert.ok(loads.images.length > 1000 && loads.json.length > 100, `${loads.images.length} images, ${loads.json.length} JSON files`);
    });

    test('the photos are a pack of their own, and every photo an NPC shows is in it (#244)', () => {
        const { result, pack } = built();
        const data = JSON.parse(pack[result.files.data].toString('utf8'));
        const config = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        const ids = new Set();
        for (const room of Object.values(config.rooms)) {
            for (const npc of room.npcs || []) {
                if (npc.photo) ids.add(npc.photo);
                for (const st of Object.values(npc.states || {})) if (st.photo) ids.add(st.photo);
            }
        }
        assert.ok(ids.size > 10, `only ${ids.size} photos in the config`);
        assert.deepStrictEqual(Object.keys(data.photos), Array.from(ids, (id) => `assets/photos/${id}.png`).sort());
        assert.ok(!Object.keys(data.images).some((f) => f.startsWith('assets/photos/')), 'no photo is in the pack the boot waits for');
        assert.ok(!Object.keys(data.photos).some((f) => f in data.images));
    });

    test('the build learns what to pack from the game\'s own loading code, and refuses a load that goes round Assets (#244)', () => {
        const loads = recordLoads();
        // the fonts are the only loads that are not packed: load.font takes the file itself
        assert.deepStrictEqual(loads.fonts.slice().sort(), ['fonts/PixelOperatorMono-Bold.ttf', 'fonts/PixelOperatorMono.ttf', 'fonts/PressStart2P-Regular.ttf']);
        assert.deepStrictEqual(loads.stray, []);
        assert.deepStrictEqual(loads, built().result.loads);
        // a load written the old way is a stray, whichever kind it is
        const edited = (from, to) => (f) => {
            const text = source(f);
            if (f !== 'GameScene.js') return text;
            assert.ok(text.includes(from), `GameScene.js no longer has ${from}`);
            return text.replace(from, to);
        };
        assert.deepStrictEqual(recordLoads(edited('Assets.url("assets/single-tile.png")', '"assets/single-tile.png"')).stray, ['image "assets/single-tile.png"']);
        assert.deepStrictEqual(recordLoads(edited("Assets.json('assets/map/japan.json')", "'assets/map/japan.json?t=1'")).stray, ['json "assets/map/japan.json?t=1"']);
        assert.deepStrictEqual(recordLoads(edited('Assets.url(`assets/photos/${id}.png`)', '`assets/photos/${id}.png`')).stray.length, built().result.loads.photos.length);
        // and a loader call the recorder does not know stops the build rather than going unrecorded
        assert.throws(() => recordLoads(edited('this.load.json("config", Assets.json("config.json"));',
            'this.load.json("config", Assets.json("config.json")); this.load.audio("x", "x.mp3");')), /load\.audio\(\)/);
        // both files that queue loads call nothing but Assets for an image or a JSON file
        for (const f of ['GameScene.js', 'systems/SpriteSystem.js']) {
            const calls = Array.from(source(f).matchAll(/\.load\.(image|spritesheet|json)\(([^\n]*)/g), (m) => m[2]);
            assert.ok(calls.length, `${f} queues loads`);
            for (const call of calls) assert.ok(/Assets\.(url|json)\(|Path\b|build\.data/.test(call), `${f}: load(${call} does not go through Assets`);
        }
    });

    test('two builds of the same sources and commit are the same bytes, and the commit is in the page (#244)', () => {
        const { result, pack, index } = built();
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-build-'));
        try {
            const out = path.join(tmp, 'dist');
            const again = build({ out, commit: 'abc123', copy: false });
            assert.deepStrictEqual(again.files, result.files);
            for (const file of Object.keys(pack)) assert.ok(fs.readFileSync(path.join(out, file)).equals(pack[file]), file);
            assert.strictEqual(fs.readFileSync(path.join(out, 'index.html'), 'utf8'), index);
            // building over an earlier build is allowed, and another commit changes only the page
            const next = build({ out, commit: 'def456', copy: false });
            assert.deepStrictEqual(next.files, result.files);
            assert.deepStrictEqual(fs.readdirSync(path.join(out, 'pack')).map((n) => `pack/${n}`).sort(), Object.keys(pack).sort());
            assert.strictEqual(fs.readFileSync(path.join(out, 'index.html'), 'utf8'), index.replace('"commit":"abc123"', '"commit":"def456"'));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });

    test('the build will not write into the game, over the repository, or over a folder that is not a build (#244)', () => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-build-'));
        try {
            const refused = (out, why) => assert.throws(() => build({ out, commit: 'abc123', copy: false }), why, out);
            refused(GV2, /gamev2\/ or inside it/);
            refused(path.join(GV2, 'dist'), /gamev2\/ or inside it/);
            refused(path.join(GV2, 'assets', 'sprites'), /gamev2\/ or inside it/);
            refused(path.join(GV2, '..'), /holds the repository/);
            refused(path.join(GV2, '..', '..'), /holds the repository/);
            const other = path.join(tmp, 'notes');
            fs.mkdirSync(other);
            fs.writeFileSync(path.join(other, 'keep.txt'), 'mine');
            refused(other, /not an earlier build/);
            refused(path.join(other, 'keep.txt'), /not a folder/);
            assert.strictEqual(fs.readFileSync(path.join(other, 'keep.txt'), 'utf8'), 'mine');
            assert.throws(() => build({ out: path.join(tmp, 'dist'), commit: 'a b"c', copy: false }), /not a commit id/);
            assert.throws(() => build({ commit: 'abc123' }), /output folder/);
            assert.ok(!fs.existsSync(path.join(tmp, 'dist')), 'a refused build writes nothing');
            // an empty folder is fine
            fs.mkdirSync(path.join(tmp, 'empty'));
            assert.doesNotThrow(() => build({ out: path.join(tmp, 'empty'), commit: 'abc123', copy: false }));
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
        // and the default output is not committed
        assert.ok(fs.readFileSync(path.join(GV2, '..', '.gitignore'), 'utf8').split('\n').includes('dist/'), '.gitignore has dist/');
    });

    test('a full build is the game\'s files plus the packs, without dotfiles or installed modules (#244)', () => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gamev2-build-'));
        try {
            const out = path.join(tmp, 'dist');
            const result = build({ out, commit: 'abc123' });
            const skipped = (n) => n.startsWith('.') || n === 'node_modules' || n === '__pycache__';
            assert.deepStrictEqual(fs.readdirSync(out).sort(), fs.readdirSync(GV2).filter((n) => !skipped(n)).concat('pack').sort());
            // the loose files are still there: the game falls back to them, and /studio/ and /editor/ read them
            for (const f of ['config.json', 'src/GameScene.js', 'assets/sprites/james_front_frame_0.png', 'tiled/tokyo.tmj', 'studio/index.html', 'editor/index.html']) {
                assert.ok(fs.readFileSync(path.join(out, f)).equals(fs.readFileSync(path.join(GV2, f))), f);
            }
            assert.strictEqual(fs.readFileSync(path.join(out, 'index.html'), 'utf8'), built().index);
            assert.deepStrictEqual(result.files, built().result.files);
            const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? [e.name, ...walk(path.join(dir, e.name))] : [e.name]));
            assert.deepStrictEqual(walk(out).filter(skipped), []);
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });
};
