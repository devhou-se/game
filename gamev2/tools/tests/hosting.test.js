// Issue #250: Firebase Hosting caches a file for an hour unless firebase.json says otherwise. Each page holds
// the list of scripts it loads (with a cache-buster), so a cached page would run an old list against the
// newest scripts; the fonts are fetched by a fixed URL. Both are served `Cache-Control: no-cache`: the browser
// keeps its copy and asks the server whether it is still current before every use. The PNGs carry the same
// header since issue #241 (repo-layout.test.js holds that rule).
module.exports = ({ test, assert, fs, path, GV2 }) => {
    // files under gamev2 that are published (firebase.json ignores dot files and node_modules), as URL paths
    const walk = (rel = '') => fs.readdirSync(path.join(GV2, rel), { withFileTypes: true }).flatMap((e) => {
        if (e.name.startsWith('.') || e.name === 'node_modules') return [];
        return e.isDirectory() ? walk(`${rel}/${e.name}`) : [`${rel}/${e.name}`];
    });
    // a `source` glob as Firebase reads it, for the forms firebase.json uses: a literal path, **, * and @(a|b)
    const matcher = (source) => {
        const re = source.split(/(\*\*\/|\*\*|\*|@\([^)]*\))/).map((part) => {
            if (part === '**/') return '(?:.*/)?';
            if (part === '**') return '.*';
            if (part === '*') return '[^/]*';
            if (part.startsWith('@(')) return `(?:${part.slice(2, -1).split('|').map((s) => s.replace(/[.+?^${}()[\]\\]/g, '\\$&')).join('|')})`;
            assert.ok(!/[*?!+@()[\]{}|]/.test(part), `${source}: a glob form this test does not read`);
            return part.replace(/[.^$\\]/g, '\\$&');
        }).join('');
        return new RegExp(`^${re}$`);
    };
    // the Cache-Control value a URL path is served with (the last rule that sets it wins), or undefined
    const cacheControl = (rules, url) => {
        let value;
        for (const rule of rules) {
            if (!rule.matches.test(url)) continue;
            for (const h of rule.headers) if (h.key.toLowerCase() === 'cache-control') value = h.value;
        }
        return value;
    };

    test('hosting: every page and every font is revalidated on each load, so a deploy reaches a returning browser (#250)', () => {
        const hosting = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'firebase.json'), 'utf8')).hosting[0];
        const rules = hosting.headers.map((rule) => ({ matches: matcher(rule.source), headers: rule.headers }));
        const files = walk();
        const pages = files.filter((f) => f.endsWith('.html'));
        assert.ok(pages.includes('/index.html') && pages.length >= 3, `found only ${pages}`);
        for (const page of pages) {
            assert.strictEqual(cacheControl(rules, page), 'no-cache', `${page} is cached`);
            // the address a player types: the folder, which Firebase answers with its index.html
            if (path.posix.basename(page) === 'index.html') {
                const dir = page.slice(0, -'index.html'.length);
                assert.strictEqual(cacheControl(rules, dir), 'no-cache', `${dir} is cached`);
            }
        }
        const fonts = files.filter((f) => f.endsWith('.ttf'));
        assert.ok(fonts.length >= 4, `found only ${fonts}`);
        for (const font of fonts) assert.strictEqual(cacheControl(rules, font), 'no-cache', `${font} is cached`);
        // the art keeps the rule it has (#241) beside the new ones
        assert.ok(files.includes('/assets/map/japan.png'), '/assets/map/japan.png is gone');
        assert.strictEqual(cacheControl(rules, '/assets/map/japan.png'), 'no-cache', '/assets/map/japan.png is cached');
        // nothing else is touched: scripts and data carry their own cache-buster
        for (const other of ['/src/game.js', '/config.json', '/tiled/tokyo.tmj', '/fonts/README.md']) {
            assert.ok(files.includes(other), `${other} is gone`);
            assert.strictEqual(cacheControl(rules, other), undefined, `${other} has a Cache-Control rule`);
        }
    });
};
