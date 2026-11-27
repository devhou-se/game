// Issue #244: the game loads its images and JSON through src/utils/Assets.js, which hands back the file
// itself (working on the game: no build) or its copy in a pack (the deployed game, tools/build_dist.js);
// the photos load after the boot, and the loading bar of the deployed game follows the images pack.
module.exports = ({ test, assert, fs, path, vm, GV2 }) => {
    const source = (f) => fs.readFileSync(path.join(GV2, 'src', f), 'utf8');

    // src/utils/Assets.js in a context of its own, with a Blob and a URL that take notes
    const assetsWith = () => {
        const made = [], revoked = [];
        class Blob {
            constructor(parts, type) { this.bytes = Buffer.concat(parts.map((p) => Buffer.from(p))); this.type = type || ''; }
            slice(from, to, type) { return new Blob([this.bytes.subarray(from, to)], type); }
        }
        const URL = {
            createObjectURL: (blob) => { made.push(blob); return `blob:${made.length}`; },
            revokeObjectURL: (url) => revoked.push(url),
        };
        const c = vm.createContext({ Blob, URL, window: {} });
        vm.runInContext(source('utils/Assets.js'), c, { filename: 'utils/Assets.js' });
        return { Assets: vm.runInContext('Assets', c), made, revoked, window: c.window };
    };

    test('unbuilt, Assets hands back the file itself, cache-busted where an edit must show (#244)', () => {
        const { Assets, made, window } = assetsWith();
        assert.strictEqual(window.Assets, Assets);
        assert.strictEqual(Assets.url('assets/sprites/tree.png'), 'assets/sprites/tree.png');
        assert.ok(/^assets\/map\/japan\.png\?t=\d+$/.test(Assets.url('assets/map/japan.png', true)));
        assert.ok(/^config\.json\?t=\d+$/.test(Assets.json('config.json')));
        assert.strictEqual(made.length, 0);
        // nothing to let go of, and nothing breaks
        Assets.release();
        Assets.installPhotos(Buffer.from('x'));
        assert.strictEqual(Assets.photos, null);
        // something that is not a data pack is not installed (a 200 with the wrong body)
        for (const bad of [null, [], 'x', {}, { json: {}, images: {} }, { json: {}, images: [], photos: {} }]) {
            assert.strictEqual(Assets.install(bad, Buffer.from('x')), false, JSON.stringify(bad));
        }
        assert.strictEqual(Assets.install({ json: {}, images: {}, photos: {} }, null), false);
        assert.strictEqual(Assets.files, null);
        assert.strictEqual(Assets.url('assets/sprites/tree.png'), 'assets/sprites/tree.png');
    });

    test('built, Assets hands back the parsed JSON and a blob URL of the image\'s bytes, and release() revokes them (#244)', () => {
        const { Assets, made, revoked } = assetsWith();
        const data = {
            json: { 'config.json': { rooms: {} } },
            images: { 'a.png': [0, 3], 'b.png': [3, 2] },
            photos: { 'assets/photos/1.png': [0, 4], 'assets/photos/2.png': [4, 1] },
        };
        assert.strictEqual(Assets.install(data, Buffer.from('AAABB')), true);
        assert.strictEqual(Assets.json('config.json'), data.json['config.json']);
        assert.ok(/^other\.json\?t=\d+$/.test(Assets.json('other.json')), 'a file the pack does not have is fetched');
        assert.strictEqual(Assets.url('a.png'), 'blob:1');
        assert.strictEqual(Assets.url('b.png', true), 'blob:2', 'a packed file needs no cache-buster');
        assert.strictEqual(Assets.url('a.png'), 'blob:3', 'a URL per call');
        assert.deepStrictEqual(made.map((b) => [b.bytes.toString(), b.type]), [['AAA', 'image/png'], ['BB', 'image/png'], ['AAA', 'image/png']]);
        assert.strictEqual(Assets.url('c.png'), 'c.png');
        assert.ok(/^c\.png\?t=\d+$/.test(Assets.url('c.png', true)));
        // the photos pack has not arrived: a photo is still its file
        assert.strictEqual(Assets.url('assets/photos/1.png'), 'assets/photos/1.png');

        // the boot is over: the URLs are revoked, the packs dropped, the photos index kept
        Assets.release();
        assert.deepStrictEqual(revoked, ['blob:1', 'blob:2', 'blob:3']);
        assert.strictEqual(Assets.files, null);
        assert.strictEqual(Assets.images, null);
        assert.strictEqual(Assets.url('a.png'), 'a.png');
        assert.ok(/^config\.json\?t=\d+$/.test(Assets.json('config.json')));
        assert.strictEqual(Assets.photos.index, data.photos);
        assert.strictEqual(Assets.photos.blob, null);

        Assets.installPhotos(Buffer.from('PPPPQ'));
        assert.strictEqual(Assets.url('assets/photos/2.png'), 'blob:4');
        assert.strictEqual(Assets.url('assets/photos/1.png'), 'blob:5');
        assert.deepStrictEqual(made.slice(3).map((b) => b.bytes.toString()), ['Q', 'PPPP']);
        Assets.release();
        assert.deepStrictEqual(revoked.slice(3), ['blob:4', 'blob:5']);
        assert.strictEqual(Assets.photos, null);
        assert.strictEqual(Assets.urls.length, 0);
        Assets.release();
        assert.strictEqual(revoked.length, 5, 'nothing is revoked twice');

        // the photos pack could not be had: the photos are the loose files
        assert.strictEqual(Assets.install(data, Buffer.from('AAABB')), true);
        Assets.release();
        Assets.installPhotos(null);
        assert.strictEqual(Assets.photos, null);
        assert.strictEqual(Assets.url('assets/photos/1.png'), 'assets/photos/1.png');
    });

    test('the loading bar of the built game is the images pack, then the files made from it (#244)', () => {
        const c = vm.createContext({ console, URLSearchParams, location: { search: '' }, window: {}, Phaser: { Scene: class {} } });
        vm.runInContext(source('GameScene.js'), c, { filename: 'GameScene.js' });
        const bar = vm.runInContext('GameScene.bootProgress', c);
        const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} is not ${b}`);
        // unbuilt (or the packs failed): the loader's own progress
        for (const v of [0, 0.25, 1]) assert.strictEqual(bar(v, null), v);
        // built: the download is 70% of the bar, and the loader's count joins once the game's files are queued
        near(bar(0, { images: 0, queued: false }), 0);
        near(bar(0.9, { images: 0.5, queued: false }), 0.35);
        near(bar(0.99, { images: 1, queued: false }), 0.7);
        near(bar(0, { images: 1, queued: true }), 0.7);
        near(bar(0.5, { images: 1, queued: true }), 0.85);
        near(bar(1, { images: 1, queued: true }), 1);
        // the game's Phaser settings for the loader
        const game = source('game.js');
        assert.ok(/loader: \{[^}]*maxParallelDownloads: 32,[^}]*imageLoadType: 'HTMLImageElement'[^}]*\}/.test(game));
        // the photos are fetched once the loading screen is gone, by the scene's own loader
        const scene = source('GameScene.js');
        assert.ok(/window\.hideLoader\(\);\s*\/\/[^\n]*\n\s*this\.loadPhotos\(\);/.test(scene), 'loadPhotos() follows hideLoader()');
    });
};
