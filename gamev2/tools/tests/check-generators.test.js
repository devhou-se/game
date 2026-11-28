// Issue #235: tools/check_generators.py compares a PNG by its decoded pixels, not its bytes (which depend on
// the Pillow and zlib that packed it), and the Checks workflow installs the pinned Pillow so the art tools
// are checked there.
// Issue #270: make_worldmap.py is one of those tools, so a world map nobody rebuilt is drift.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const os = require('os');
    // A snippet run with tools/ on the path; the PNGs are packed with zlib alone, so it needs no Pillow.
    // png(path, rows, level): an 8-bit RGBA PNG of `rows` (lists of (r, g, b, a)), deflated at `level`.
    const HEAD = [
        'import json, os, struct, sys, zlib',
        'import check_generators as cg',
        'def png(path, rows, level):',
        '    os.makedirs(os.path.dirname(path), exist_ok=True)',
        '    chunk = lambda kind, data: struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))',
        '    raw = b"".join(b"\\x00" + bytes(v for px in row for v in px) for row in rows)',
        '    head = struct.pack(">IIBBBBB", len(rows[0]), len(rows), 8, 6, 0, 0, 0)',
        '    open(path, "wb").write(b"\\x89PNG\\r\\n\\x1a\\n" + chunk(b"IHDR", head) + chunk(b"IDAT", zlib.compress(raw, level)) + chunk(b"IEND", b""))',
        'root, work = sys.argv[1], sys.argv[2]',
        'at = lambda base, f: os.path.join(base, "assets", "sprites", f)',
        'rows = [[(x * 3 % 256, y * 5 % 256, (x + y) % 256, 255 if (x + y) % 3 else 0) for x in range(48)] for y in range(32)]',
        'out = {"pillow": cg.have_pillow()}', ''].join('\n');
    const python = (snippet) => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'check-generators-'));
        try {
            const run = spawnSync('python3', ['-c', HEAD + snippet + '\nprint("\\n" + json.dumps(out))\n', path.join(tmp, 'root'), path.join(tmp, 'work')],
                { cwd: GV2, encoding: 'utf8', timeout: 60000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
            assert.ok(!run.error, `python3 did not finish: ${run.error}`);
            assert.strictEqual(run.status, 0, run.stderr);
            return JSON.parse(run.stdout.trim().split('\n').pop());
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    };

    test('check_generators: a PNG packed differently is the same picture, a moved pixel is drift (#235)', () => {
        const out = python([
            // the same picture in other bytes; one pixel moved; another size; a text file with other bytes
            'for f in ("same.png", "pixel.png", "size.png"):',
            '    png(at(root, f), rows, 9)',
            'png(at(work, "same.png"), rows, 0)',
            'moved = [list(r) for r in rows]',
            'moved[4][7] = (1, 2, 3, 255)',
            'png(at(work, "pixel.png"), moved, 9)',
            'png(at(work, "size.png"), rows[:16], 9)',
            'for base, text in ((root, "a"), (work, "b")):',
            '    os.makedirs(os.path.join(base, "tiled"), exist_ok=True)',
            '    open(os.path.join(base, "tiled", "room.tmj"), "w").write(text)',
            'read = lambda base, f: open(at(base, f), "rb").read()',
            'out["packed"] = read(root, "same.png") != read(work, "same.png")',
            'out["first"] = cg.restore(root, work)',
            'out["putBack"] = all(read(root, f) == read(work, f) for f in ("same.png", "pixel.png", "size.png"))',
            'out["second"] = cg.restore(root, work)',
        ].join('\n'));
        assert.ok(out.packed, 'the two same.png files have the same bytes: the case tests nothing');
        // without Pillow a PNG cannot be decoded: other bytes are reported, never passed over
        const expected = out.pillow
            ? ['tiled/room.tmj changed', 'assets/sprites/pixel.png changed', 'assets/sprites/size.png changed']
            : ['tiled/room.tmj changed', 'assets/sprites/pixel.png changed', 'assets/sprites/same.png changed', 'assets/sprites/size.png changed'];
        assert.deepStrictEqual(out.first, expected);
        assert.ok(out.putBack, 'the scratch copy holds the committed bytes again, the repacked PNG too');
        assert.deepStrictEqual(out.second, [], 'nothing differs once the scratch copy is put back');
    });

    test('check_generators: a file that is not a picture, an added and a removed PNG are still reported (#235)', () => {
        const out = python([
            'png(at(root, "gone.png"), rows, 9)',
            'png(at(work, "new.png"), rows, 9)',
            'for base, data in ((root, b"not a picture"), (work, b"nor is this")):',
            '    open(at(base, "broken.png"), "wb").write(data)',
            'out["files"] = cg.restore(root, work)',
            'out["left"] = sorted(os.listdir(os.path.dirname(at(work, "x"))))',
        ].join('\n'));
        assert.deepStrictEqual(out.files, ['assets/sprites/broken.png changed', 'assets/sprites/gone.png REMOVED', 'assets/sprites/new.png ADDED']);
        assert.deepStrictEqual(out.left, ['broken.png', 'gone.png']);
    });

    test('check_generators: a map with no room and a room with no map are named, and the committed world has neither (#243)', () => {
        const out = python([
            'os.makedirs(os.path.join(root, "tiled", "prefabs"))',
            'json.dump({"rooms": {k: {} for k in ("Town", "HouseTown1", "ShrineTown1", "KonbiniTown1")}}, open(os.path.join(root, "config.json"), "w"))',
            // housetown2 and zoo have no room; ShrineTown1 and KonbiniTown1 no map; a prefab and the README are not maps of rooms
            'for f in ("zoo.tmj", "town.tmj", "housetown1.tmj", "housetown2.tmj", "README.md", os.path.join("prefabs", "shrine.tmj")):',
            '    open(os.path.join(root, "tiled", f), "w").write("{}")',
            'out["unmatched"] = cg.unmatched_maps(root)',
            'out["committed"] = cg.unmatched_maps(".")',
        ].join('\n'));
        assert.deepStrictEqual(out.unmatched, [
            'tiled/housetown2.tmj has no room in config.json: delete it',
            'tiled/zoo.tmj has no room in config.json: delete it',
            'room ShrineTown1 has no tiled/shrinetown1.tmj: run config_to_tiled.py ShrineTown1',
            'room KonbiniTown1 has no tiled/konbinitown1.tmj: run config_to_tiled.py KonbiniTown1',
        ]);
        assert.deepStrictEqual(out.committed, [], 'every committed map has a room and every room a map');
    });

    test('check_generators: config_to_tiled fails for a map left behind and for a room never seeded (#243)', () => {
        // a project like the committed one, but for one stray map and one map that is missing
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'check-generators-maps-'));
        try {
            const root = path.join(tmp, 'gamev2');
            fs.mkdirSync(path.join(root, 'tiled'), { recursive: true });
            for (const d of ['tools', 'src', 'fonts', 'assets']) fs.symlinkSync(path.join(GV2, d), path.join(root, d));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(root, 'config.json'));
            const maps = fs.readdirSync(path.join(GV2, 'tiled')).filter((f) => f.endsWith('.tmj')).sort();
            const key = Object.keys(JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms).find((k) => /^Konbini/.test(k));
            for (const f of maps) fs.copyFileSync(path.join(GV2, 'tiled', f), path.join(root, 'tiled', f === `${key.toLowerCase()}.tmj` ? 'housenowhere9.tmj' : f));
            const run = spawnSync('python3', ['-c', 'import json, sys, check_generators as cg; print("\\n" + json.dumps(cg.check([cg.TILED], sys.argv[1])))', root],
                { cwd: GV2, encoding: 'utf8', maxBuffer: 1 << 26, timeout: 120000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
            assert.strictEqual(run.status, 0, run.stderr);
            assert.deepStrictEqual(JSON.parse(run.stdout.trim().split('\n').pop()), { config_to_tiled: [
                'tiled/housenowhere9.tmj has no room in config.json: delete it',
                `room ${key} has no tiled/${key.toLowerCase()}.tmj: run config_to_tiled.py ${key}`,
            ] });
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });

    test('check_generators: make_worldmap is an art tool run with --pil, on a scratch copy that has what it reads (#270)', () => {
        const out = python([
            'out["last"] = cg.ART_TOOLS[-1] == cg.WORLDMAP == "make_worldmap" and cg.CHECKS[-1] == cg.WORLDMAP',
            'out["args"] = cg.ARGS',
            // play.js loads the game's code from src/ and the tool writes under assets/map
            'out["copied"] = "src" in cg.INPUTS and "tools" in cg.INPUTS and "assets/map" in cg.OUTPUTS and "assets/sprites" in cg.OUTPUTS',
            'out["noPillow"] = cg.skips([cg.WORLDMAP, "generate_osaka"], False, False)',
            'out["noFont"] = cg.skips([cg.WORLDMAP], True, False)',
        ].join('\n'));
        assert.ok(out.last, 'make_worldmap is the last of ART_TOOLS: it draws what the other tools made');
        // without --pil the tool draws with tmxrasterizer where Tiled is installed, and that is another picture
        assert.deepStrictEqual(out.args, { make_worldmap: ['--pil'] });
        assert.ok(out.copied, 'the scratch project lacks something make_worldmap reads or writes');
        assert.deepStrictEqual(out.noPillow, { make_worldmap: 'needs Pillow' });
        assert.deepStrictEqual(out.noFont, {}, 'the map sets no Japanese text');
        const tool = fs.readFileSync(path.join(GV2, 'tools', 'make_worldmap.py'), 'utf8');
        assert.ok(/'--pil' not in sys\.argv/.test(tool), 'make_worldmap.py no longer takes --pil');
        const meta = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        assert.strictEqual(meta.custom, false, 'a hand-made map ("custom": true) is not one make_worldmap rebuilds: take it out of ART_TOOLS');
    });

    test('check_generators: Fukuoka\'s town art is checked, before the world map that shows it (#362)', () => {
        const out = python('out["at"] = cg.ART_TOOLS.index("generate_fukuoka_town_art") if "generate_fukuoka_town_art" in cg.ART_TOOLS else -1\nout["map"] = cg.ART_TOOLS.index(cg.WORLDMAP)');
        assert.ok(out.at >= 0, 'generate_fukuoka_town_art is not in ART_TOOLS');
        assert.ok(out.at < out.map, 'generate_fukuoka_town_art runs after make_worldmap');
    });

    test('check_generators: a world map that is not what make_worldmap draws is drift, and only the picture is named (#270)', () => {
        // a project like the committed one (devhouse.world beside it), but for a patch painted on its map
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'check-generators-worldmap-'));
        try {
            const root = path.join(tmp, 'gamev2');
            fs.mkdirSync(path.join(root, 'assets', 'map'), { recursive: true });
            for (const d of ['tools', 'src', 'fonts', 'tiled', path.join('assets', 'sprites'), path.join('assets', 'ads')]) fs.symlinkSync(path.join(GV2, d), path.join(root, d));
            for (const f of fs.readdirSync(path.join(GV2, 'assets', 'map'))) fs.copyFileSync(path.join(GV2, 'assets', 'map', f), path.join(root, 'assets', 'map', f));
            fs.copyFileSync(path.join(GV2, 'config.json'), path.join(root, 'config.json'));
            fs.copyFileSync(path.join(GV2, '..', 'devhouse.world'), path.join(tmp, 'devhouse.world'));
            const run = spawnSync('python3', ['-c', [
                'import json, os, sys, check_generators as cg',
                'out = {"pillow": cg.have_pillow()}',
                'if out["pillow"]:',
                '    from PIL import Image',
                '    f = os.path.join(sys.argv[1], "assets", "map", "world-map.png")',
                '    im = Image.open(f).convert("RGB")',
                '    im.paste((255, 0, 255), (40, 40, 104, 104))',
                '    im.save(f)',
                '    out["stale"] = cg.check([cg.WORLDMAP], sys.argv[1])',
                'print("\\n" + json.dumps(out))'].join('\n'), root],
                { cwd: GV2, encoding: 'utf8', maxBuffer: 1 << 26, timeout: 120000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
            assert.strictEqual(run.status, 0, run.stderr);
            const out = JSON.parse(run.stdout.trim().split('\n').pop());
            // the tool draws with Pillow: without it the check lists it as skipped and there is nothing to run
            if (!out.pillow) return;
            // world-map.json is not named: the tool ran to its end and wrote the committed one, byte for byte
            assert.deepStrictEqual(out.stale, { make_worldmap: ['assets/map/world-map.png changed'] });
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });

    test('check_generators: the Checks workflow installs the pinned Pillow (#235)', () => {
        const pin = fs.readFileSync(path.join(GV2, 'tools', 'requirements-art.txt'), 'utf8').split('\n').filter((l) => l && !l.startsWith('#'));
        assert.strictEqual(pin.length, 1, 'requirements-art.txt holds one requirement');
        assert.ok(/^Pillow==\d+\.\d+\.\d+$/.test(pin[0]), `Pillow is pinned to one release, not "${pin[0]}"`);
        const workflow = fs.readFileSync(path.join(GV2, '..', '.github', 'workflows', 'checks.yml'), 'utf8');
        assert.ok(/pip install -r tools\/requirements-art\.txt/.test(workflow), 'checks.yml installs tools/requirements-art.txt');
        assert.ok(workflow.indexOf('requirements-art.txt') < workflow.indexOf('tools/check_generators.py'), 'Pillow is installed before the generators are checked');
    });

    test('check_generators: the Workshop agent image installs the pinned Pillow (#222)', () => {
        const pin = fs.readFileSync(path.join(GV2, 'tools', 'requirements-art.txt'), 'utf8').split('\n').filter((l) => l && !l.startsWith('#'))[0];
        // the image build is sent .workshop/ and nothing else, so the Dockerfile repeats the pin
        const lines = fs.readFileSync(path.join(GV2, '..', '.workshop', 'Dockerfile'), 'utf8').split('\n');
        const code = lines.filter((l) => l.trim() && !l.trim().startsWith('#'));
        const pillow = code.join('\n').match(/Pillow==[\d.]+/g);
        assert.deepStrictEqual(pillow, [pin], '.workshop/Dockerfile installs the Pillow of requirements-art.txt');
        // the build's own check and the note to later agents name the same release
        const version = pin.split('==')[1];
        assert.ok(code.some((l) => l.includes(`PIL.__version__ == '${version}'`)), 'the build checks the Pillow it installed');
        const label = code[code.length - 1];
        assert.ok(label.startsWith('LABEL workshop.environment="') && label.includes(`Pillow ${version}`), 'the label is last and names the Pillow');
        // what Workshop asks of the file: its own base image, and the agent's user at the end
        assert.deepStrictEqual(code.slice(0, 2), ['ARG WORKSHOP_BASE', 'FROM ${WORKSHOP_BASE}']);
        assert.deepStrictEqual(code.filter((l) => l.startsWith('USER ')), ['USER root', 'USER agent']);
        assert.ok(!code.some((l) => /^(ENTRYPOINT|WORKDIR|CMD)\b|CLAUDE_CONFIG_DIR/.test(l)), 'ENTRYPOINT, WORKDIR and CLAUDE_CONFIG_DIR stay the base image\'s');
        // no Japanese font: with one the font tool (extract_city) is run and reports DRIFT (check_generators.py, FONT_TOOLS)
        assert.ok(!code.some((l) => /fonts-|noto/i.test(l)), 'the image installs no font');
    });
};
