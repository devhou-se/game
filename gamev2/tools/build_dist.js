#!/usr/bin/env node
// The deploy build: `node tools/build_dist.js [--out <dir>] [--commit <sha>]` (from gamev2/).
//
// Working on the game needs no build: gamev2/index.html runs as it is. This writes what is PUBLISHED
// (firebase.json's `public`): a copy of gamev2/ in <dir> (default ../dist, not committed) with
//
//   pack/game.<hash>.js     the scripts index.html lists, in its order, as one file
//   pack/data.<hash>.json   { json: { path: parsed JSON }, images: { path: [offset, length] }, photos: {...} }
//   pack/images.<hash>.bin  every image the boot loads, end to end (the index is in the data pack)
//   pack/photos.<hash>.bin  the NPC photos, which the game fetches once it is up
//   index.html              the script list replaced by the bundle and `window.GAME_BUILD`, which names the packs
//
// <hash> is the first 12 hex digits of the file's SHA-256, so a pack can be cached for ever (firebase.json)
// and index.html, which is revalidated on every visit, is the only thing that says which packs are current.
//
// What goes in the packs is not listed anywhere: the build runs the game's own GameScene.preload() and
// queuePhotos() against a recording loader. Every load there goes through Assets.json / Assets.url
// (src/utils/Assets.js); one that does not, or a file the game asks for that is not there, fails the build.
// The same sources and commit give the same bytes. `require('./build_dist').build({ out, commit, copy })`
// is the same thing for the tests (`copy: false` writes only pack/ and index.html).
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { execFileSync } = require('child_process');

const GV2 = path.dirname(__dirname);
const ROOT = path.dirname(GV2);
const MARK = { head: '<!-- build:head -->', scripts: '<!-- build:scripts -->', end: '<!-- /build:scripts -->' };

const fail = (message) => { throw new Error('build_dist: ' + message); };
const hashOf = (buffer) => crypto.createHash('sha256').update(buffer).digest('hex').slice(0, 12);
const once = (text, mark) => {
    const at = text.indexOf(mark);
    if (at < 0 || text.indexOf(mark, at + 1) >= 0) fail(`index.html needs exactly one ${mark}`);
    return at;
};

// A file the game names, as bytes. The name is the game's own ('assets/sprites/x.png'): relative, inside gamev2/.
const read = (file, askedBy) => {
    const plain = typeof file === 'string' && file !== '' && !path.isAbsolute(file) && !/[?#\\]/.test(file) &&
        path.posix.normalize(file) === file && !file.startsWith('../');
    if (!plain) fail(`${askedBy} asks for ${JSON.stringify(file)}, which is not a plain path inside gamev2/`);
    const full = path.join(GV2, file);
    if (!fs.existsSync(full) || !fs.statSync(full).isFile()) fail(`${askedBy} asks for ${file}, which is not in gamev2/`);
    return fs.readFileSync(full);
};

/** The script files index.html loads, in order: the 'src/....js' entries between the build:scripts markers. */
function scriptList(html) {
    const block = html.slice(once(html, MARK.scripts), once(html, MARK.end));
    const files = Array.from(block.matchAll(/'(src\/[\w./-]+\.js)'/g), (m) => m[1]);
    if (!files.length) fail('no script list between the build:scripts markers of index.html');
    if (new Set(files).size !== files.length) fail('index.html lists a script twice');
    return files;
}

/**
 * What the game loads, found by running its own preload() and queuePhotos() against a loader that only takes notes:
 * { json, images, photos } (sorted paths that came through Assets), fonts (the URLs given to load.font)
 * and stray (loads whose URL did not come through Assets — the build refuses those). `source(file)` is the
 * text of a file under src/ (the tests hand in an edited one).
 */
function recordLoads(source = (file) => fs.readFileSync(path.join(GV2, 'src', file), 'utf8')) {
    const asked = new Set(), json = new Set(), images = new Set(), photos = new Set();
    const fonts = [], stray = [], handlers = new Map(), pending = [], parsed = {};
    let into = images;
    const note = (kind, url) => { if (!asked.has(url)) stray.push(`${kind} ${JSON.stringify(url)}`); };
    const listen = (keep) => (event, fn) => {
        if (!handlers.has(event)) handlers.set(event, []);
        handlers.get(event).push({ fn, keep });
        return load;
    };
    const load = new Proxy({
        on: listen(true),
        once: listen(false),
        off: () => load,
        font: (key, url) => { fonts.push(url); },
        image: (key, url) => note('image', url),
        spritesheet: (key, url) => note('spritesheet', url),
        json: (key, url) => { note('json', url); if (asked.has(url)) pending.push([key, url]); },
    }, {
        get(target, name) {
            if (!(name in target)) fail(`the game called load.${String(name)}(), which the build does not record`);
            return target[name];
        },
    });
    const ctx = vm.createContext({
        console, URLSearchParams, location: { search: '' },
        window: {},   // no GAME_BUILD: preload() queues everything itself
        Phaser: { Scene: class {} },
        Assets: {
            json: (file) => { asked.add(file); json.add(file); return file; },
            url: (file) => { asked.add(file); into.add(file); return file; },
        },
    });
    for (const f of ['systems/SpriteSystem.js', 'GameScene.js']) {
        vm.runInContext(source(f), ctx, { filename: f });
    }
    const scene = new (vm.runInContext('GameScene', ctx))();
    scene.load = load;
    scene.textures = { exists: () => false };

    scene.preload();
    // a JSON file "arrives" after the code that asked for it has returned, as it does in the loader, and
    // whatever its handlers queue arrives after that
    while (pending.length) {
        const [key, file] = pending.shift();
        const data = JSON.parse(read(file, 'the game').toString('utf8'));
        parsed[key] = data;
        const event = `filecomplete-json-${key}`, list = handlers.get(event) || [];
        handlers.set(event, list.filter((h) => h.keep));
        for (const h of list) h.fn(key, 'json', data);
    }
    if (!parsed.config) fail('preload() did not load config.json under the key "config"');
    into = photos;
    scene.queuePhotos(parsed.config);

    const sorted = (set) => Array.from(set).sort();
    return { json: sorted(json), images: sorted(images), photos: sorted(photos), fonts, stray };
}

/** The files end to end, and where each one is: { buffer, index: { path: [offset, length] } }. */
function packFiles(files, what) {
    const index = {}, parts = [];
    let offset = 0;
    for (const file of files) {
        const bytes = read(file, what);
        index[file] = [offset, bytes.length];
        parts.push(bytes);
        offset += bytes.length;
    }
    return { buffer: Buffer.concat(parts), index };
}

/**
 * The folder the build may write: not gamev2/, not inside it, and not a folder that holds it (the
 * repository root, or anything above). It is emptied first, so one that already has something in it
 * must be an earlier build.
 */
function checkOut(out) {
    const real = (dir) => (fs.existsSync(dir) ? fs.realpathSync(dir) : dir);
    const within = (dir, parent) => {
        const rel = path.relative(real(parent), real(dir));
        return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
    };
    if (within(out, GV2)) fail(`--out ${out} is gamev2/ or inside it: the build copies gamev2/, and would publish itself`);
    if (within(GV2, out)) fail(`--out ${out} holds the repository: the build empties its output folder`);
    if (!fs.existsSync(out)) return;
    if (!fs.statSync(out).isDirectory()) fail(`--out ${out} is not a folder`);
    const names = fs.readdirSync(out);
    if (names.length && !(names.includes('index.html') && names.includes('pack'))) {
        fail(`--out ${out} has files in it and is not an earlier build (no index.html and pack/): not emptying it`);
    }
}

/**
 * Build the published site into `out`. `commit` is recorded in window.GAME_BUILD (so the built index.html
 * differs for every commit, which the deploy's "is the live site this commit" check relies on).
 * Returns { out, commit, files: { game, data, images, photos } (names relative to out), scripts, loads }.
 */
function build({ out, commit = 'dev', copy = true } = {}) {
    if (!out) fail('build() needs an output folder');
    out = path.resolve(out);
    if (!/^[\w.-]+$/.test(commit)) fail(`--commit ${JSON.stringify(commit)} is not a commit id`);
    checkOut(out);

    // everything is worked out before the output folder is touched
    const html = fs.readFileSync(path.join(GV2, 'index.html'), 'utf8');
    once(html, MARK.head);
    const scripts = scriptList(html);
    const bundle = Buffer.from(scripts.map((f) => `// ${f}\n${read(f, 'index.html').toString('utf8')}`).join('\n;\n'), 'utf8');

    const loads = recordLoads();
    if (loads.stray.length) {
        fail('every load in GameScene goes through Assets.json / Assets.url (src/utils/Assets.js); these did not:\n  ' +
            loads.stray.join('\n  '));
    }
    for (const font of loads.fonts) read(font, 'the game');   // not packed: load.font fetches the file itself
    const both = loads.photos.filter((f) => loads.images.includes(f));
    if (both.length) fail(`in the boot's images and in the photos: ${both.join(', ')}`);
    const json = {};
    for (const file of loads.json) {
        json[file] = JSON.parse(read(file, 'the game').toString('utf8'));
        // Phaser takes an object in place of a URL only when it is a plain object
        if (!json[file] || typeof json[file] !== 'object' || Array.isArray(json[file])) fail(`${file} is not a JSON object`);
    }
    const images = packFiles(loads.images, 'the game'), photos = packFiles(loads.photos, 'the game');
    const data = Buffer.from(JSON.stringify({ json, images: images.index, photos: photos.index }), 'utf8');

    const files = {
        game: `pack/game.${hashOf(bundle)}.js`,
        data: `pack/data.${hashOf(data)}.json`,
        images: `pack/images.${hashOf(images.buffer)}.bin`,
        photos: `pack/photos.${hashOf(photos.buffer)}.bin`,
    };
    const hint = (file) => `<link rel="preload" as="fetch" crossorigin href="${file}">`;
    const game = { commit, data: files.data, images: files.images, photos: files.photos };
    const start = once(html, MARK.scripts), end = once(html, MARK.end) + MARK.end.length;
    const index = (html.slice(0, start) +
        `<script>window.GAME_BUILD = ${JSON.stringify(game)};</script>\n    <script src="${files.game}"></script>` +
        html.slice(end))
        .replace(MARK.head, `${hint(files.data)}\n    ${hint(files.images)}`);

    fs.rmSync(out, { recursive: true, force: true });
    fs.mkdirSync(out, { recursive: true });
    if (copy) {
        const skip = (name) => name.startsWith('.') || name === 'node_modules' || name === '__pycache__';
        fs.cpSync(GV2, out, { recursive: true, filter: (from) => from === GV2 || !skip(path.basename(from)) });
    }
    fs.mkdirSync(path.join(out, 'pack'), { recursive: true });
    fs.writeFileSync(path.join(out, files.game), bundle);
    fs.writeFileSync(path.join(out, files.data), data);
    fs.writeFileSync(path.join(out, files.images), images.buffer);
    fs.writeFileSync(path.join(out, files.photos), photos.buffer);
    fs.writeFileSync(path.join(out, 'index.html'), index);
    return { out, commit, files, scripts, loads };
}

module.exports = { build, scriptList, recordLoads, GV2, ROOT };

if (require.main === module) {
    const args = process.argv.slice(2), opts = {};
    while (args.length) {
        const flag = args.shift();
        if ((flag !== '--out' && flag !== '--commit') || !args.length) {
            console.error('usage: node tools/build_dist.js [--out <dir>] [--commit <sha>]');
            process.exit(2);
        }
        opts[flag.slice(2)] = args.shift();
    }
    if (!opts.commit) {
        try { opts.commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: GV2, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); }
        catch (e) { opts.commit = 'dev'; }
    }
    try {
        const built = build({ out: opts.out || path.join(ROOT, 'dist'), commit: opts.commit });
        const kb = (file) => `${Math.round(fs.statSync(path.join(built.out, file)).size / 1024)} KB`;
        console.log(`built ${built.out} at ${built.commit}`);
        console.log(`  ${built.files.game}  ${kb(built.files.game)}  (${built.scripts.length} scripts)`);
        console.log(`  ${built.files.data}  ${kb(built.files.data)}  (${built.loads.json.length} JSON files)`);
        console.log(`  ${built.files.images}  ${kb(built.files.images)}  (${built.loads.images.length} images)`);
        console.log(`  ${built.files.photos}  ${kb(built.files.photos)}  (${built.loads.photos.length} photos)`);
    } catch (e) {
        console.error(e.message);
        process.exit(1);
    }
}
