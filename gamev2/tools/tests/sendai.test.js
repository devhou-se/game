module.exports = ({ test, assert, fs, path, GV2 }) => {
    const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
    const name = (t) => (typeof t === 'number' ? cfg.tilePalette[t] : t) || '';
    const room = cfg.rooms.Sendai;
    const layer = (n, r = room) => ((r.layers || []).find((l) => l.name === n) || {}).tiles || {};
    const W = room.worldWidth / 64, H = room.worldHeight / 64;
    const colliders = layer('Colliders');
    const sprites = {};                                   // sprite key -> its top-left cells
    for (const l of room.layers) {
        for (const [xy, t] of Object.entries(l.tiles || {})) (sprites[name(t)] = sprites[name(t)] || []).push(xy.split(',').map(Number));
    }
    const at = (key) => { assert.ok(sprites[key], `Sendai has no ${key}`); return sprites[key][0]; };
    const open = (x, y) => x >= 0 && y >= 0 && x < W && y < H && !(`${x},${y}` in colliders);
    const reach = (from) => {                             // every cell walkable from `from`
        const seen = new Set([from.join()]), todo = [from];
        while (todo.length) {
            const [x, y] = todo.pop();
            for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                if (open(nx, ny) && !seen.has(`${nx},${ny}`)) { seen.add(`${nx},${ny}`); todo.push([nx, ny]); }
            }
        }
        return seen;
    };

    test('Sendai: the station is a city stop on the line, and its doors lead in and back out (#66)', () => {
        const st = cfg.stations.SendaiStation;
        assert.deepStrictEqual([st.label, st.town, st.train, st.parent], ['Sendai', 'Sendai', 'train-orange', undefined]);
        assert.ok(st.order > cfg.stations.TokyoStation.order && st.order < cfg.stations.SapporoStation.order, 'between Tokyo and Hokkaido on the board');
        assert.strictEqual(cfg.rooms.SendaiStation.name, 'Sendai Station');
        const into = room.transporters.find((t) => t.targetRoom === 'SendaiStation');
        const back = cfg.rooms.SendaiStation.transporters.filter((t) => t.targetRoom === 'Sendai');
        assert.ok(into && back.length === 2, 'station house door and the two door mats');
        for (const t of back) {
            assert.deepStrictEqual([t.targetX, t.targetY], [into.gridX, into.gridY + 1], 'you step out in front of the station house door');
        }
        assert.ok(open(into.gridX, into.gridY) && open(into.gridX, into.gridY + 1));
    });

    test('Sendai: the 7-Eleven has its own interior, wired both ways (#66)', () => {
        const [kx, ky] = at('seven-eleven_0_0');
        const door = room.transporters.find((t) => t.targetRoom === 'KonbiniSendai1');
        assert.ok(door, 'the konbini door is not wired: run generate_konbinis.py Sendai');
        assert.deepStrictEqual([door.gridX, door.gridY], [kx + 1, ky + 3]);
        const shop = cfg.rooms.KonbiniSendai1;
        assert.strictEqual(shop.name, '7-Eleven · Sendai');
        assert.strictEqual(shop.interior, true);
        for (const t of shop.transporters) {
            assert.deepStrictEqual([t.targetRoom, t.targetX, t.targetY], ['Sendai', kx + 1, ky + 4], 'you step out in front of the shop door');
        }
    });

    test('Sendai: every landmark is there and can be walked to from the station door (#66)', () => {
        const start = room.transporters.find((t) => t.targetRoom === 'SendaiStation');
        const seen = reach([start.gridX, start.gridY + 1]);
        // sprite -> the cell its visitor stands on, relative to the sprite's top-left (LANDMARKS in tools/blog_to_npc.py)
        const stand = {
            'sendai-masamune_0_0': [3, 4], 'sendai-zuihoden_0_0': [2, 6], 'sendai-pub_0_0': [3, 5],
            'sendai-kiln_0_0': [3, 6], 'matsushima-ferry_0_0': [-2, -1], 'seven-eleven_0_0': [0, 4],
        };
        for (const [key, [dx, dy]] of Object.entries(stand)) {
            const [x, y] = at(key);
            assert.ok(seen.has(`${x + dx},${y + dy}`), `${key}: nobody can walk to (${x + dx},${y + dy})`);
            assert.ok(key in cfg.spriteMetadata, `${key} is not in spriteMetadata (not loaded at boot)`);
        }
        // the statue stands up a flight of steps, on a terrace above a stone wall; Zuihoden up its own steps
        const stairs = Object.keys(layer('Over Floor')).filter((xy) => name(layer('Over Floor')[xy]).startsWith('castle-stairs'))
            .map((xy) => xy.split(',').map(Number));
        const [mx, my] = at('sendai-masamune_0_0'), [zx, zy] = at('sendai-zuihoden_0_0');
        const flight = (x0, x1) => stairs.filter(([x]) => x >= x0 && x <= x1).map(([, y]) => y);
        assert.ok(new Set(flight(mx, mx + 2)).size >= 5 && Math.min(...flight(mx, mx + 2)) > my + 3, 'a flight of steps below the statue');
        assert.ok(new Set(flight(zx, zx + 6)).size >= 5 && Math.min(...flight(zx, zx + 6)) > zy + 4, 'a flight of steps below Zuihoden');
        assert.ok((sprites['castle-wall-siding_0_0'] || []).length >= 30, 'the terrace stands on a stone wall');
        // a samurai town: earthen walls, gates you walk through, pines, machiya
        assert.ok(sprites['sendai-earthen-wall_0_0'].length >= 60, 'earthen walls');
        assert.ok(sprites['sendai-pine_0_0'].length >= 15, 'pines');
        assert.strictEqual(Object.keys(sprites).filter((k) => k.startsWith('machiya-')).length, 3, 'the machiya row');
        for (const [gx, gy] of sprites['sendai-gate_0_0']) {
            for (const [x, y] of [[gx + 1, gy + 1], [gx + 2, gy + 2]]) assert.ok(seen.has(`${x},${y}`), `gateway cell ${x},${y} is shut`);
            assert.ok(seen.has(`${gx + 1},${gy + 3}`) && seen.has(`${gx + 1},${gy}`), 'a gate leads somewhere on both sides');
        }
        // nobody stands under a roof: every building's roof rows are solid. The one cell of a building you
        // can step onto is the doorway of a machiya that is a house (#208): the middle of its front row,
        // a hidden door into a House room of this town, with the street in front of it
        // ...and the door of the pub and of the distillery's kiln (#217): a hidden door into a room whose
        // `pub` / `distillery` marker names this town and lists that very cell
        const interior = (cx, cy) => room.transporters.some((t) => t.hidden && t.gridX === cx && t.gridY === cy &&
            ['pub', 'distillery'].some((mark) => { const m = (cfg.rooms[t.targetRoom] || {})[mark];
                return m && m.host === 'Sendai' && m.doors.some(([dx, dy]) => dx === cx && dy === cy); }));
        const doorway = (key, x, y, w, h, cx, cy) => seen.has(`${cx},${cy + 1}`) && (/^sendai-(pub|kiln)/.test(key) ? interior(cx, cy) :
            /^machiya/.test(key) && cx === x + (w - 1) / 2 && cy === y + h - 1 &&
            room.transporters.some((t) => t.hidden && t.gridX === cx && t.gridY === cy &&
                ((cfg.rooms[t.targetRoom] || {}).house || {}).host === 'Sendai'));
        // ...and the door of a tower that has a lobby (#216): on its ground-floor row, a hidden door into a Lobby
        // room of this town, with the street in front of it - the yellow high-rise's (23,20). The flats over the
        // 7-Eleven have none: the store is their ground floor
        const lobbyDoor = (key, y, h, cx, cy) => /^highrise/.test(key) && cy === y + h - 1 &&
            seen.has(`${cx},${cy + 1}`) && room.transporters.some((t) => t.hidden && t.gridX === cx && t.gridY === cy &&
                ((cfg.rooms[t.targetRoom] || {}).lobby || {}).host === 'Sendai');
        const size = (key) => { const m = cfg.spriteMetadata[key]; return [Math.round(0.5 / m.anchorX), Math.round(0.5 / m.anchorY)]; };
        const opened = [];
        for (const key of Object.keys(sprites).filter((k) => /^(highrise|machiya|sendai-pub|sendai-kiln|sendai-zuihoden)/.test(k))) {
            const [w, h] = size(key);
            for (const [x, y] of sprites[key]) {
                for (let cx = x; cx < x + w; cx++) for (let cy = y; cy < y + h; cy++) {
                    if (doorway(key, x, y, w, h, cx, cy)) continue;
                    if (lobbyDoor(key, y, h, cx, cy)) { opened.push(`${key} ${cx},${cy}`); continue; }
                    assert.ok(!seen.has(`${cx},${cy}`), `${key}: (${cx},${cy}) can be walked onto, behind the building`);
                }
            }
        }
        assert.deepStrictEqual(opened, ['highrise-yellow_0_0 23,20'], 'the one tower door that opens');
    });

    test('Sendai: Matsushima bay is the east edge - a shore, a pier you walk on, a boat lane clear of the islets (#66)', () => {
        const water = layer('Water');
        const [fx, fy] = at('matsushima-ferry_0_0'), [px, py] = at('matsushima-pier_0_0');
        assert.strictEqual(cfg.spriteMetadata['matsushima-pier_0_0'].depthBias, -200, 'the pier lies flat, under whoever is on it');
        assert.strictEqual(py, fy + 2, 'the boat is moored along the pier');
        for (let y = py; y < H; y++) {
            for (let x = px; x < W; x++) {
                const xy = `${x},${y}`, onPier = y === py && x < px + 5;
                assert.ok(name(water[xy]).startsWith('pond-autotile_'), `${xy} is not water`);
                assert.strictEqual(xy in colliders, !onPier, onPier ? `pier cell ${xy} is not walkable` : `water cell ${xy} is walkable`);
            }
        }
        assert.strictEqual(name(water[`${px},${py + 3}`]), 'pond-autotile_edge-w', 'the bank runs down the west side of the bay');
        assert.ok(fs.existsSync(path.join(GV2, 'assets', 'sprites', 'pond-autotile_edge-w.png')) && 'pond-autotile_edge-w' in cfg.spriteMetadata);
        // you can fish it: the bank and the water beside the pier are pond tiles the Interactions table knows
        const rules = fs.readFileSync(path.join(GV2, 'src', 'utils', 'Interactions.js'), 'utf8');
        assert.ok(/kind: 'pond'[^}]*pattern: \/\^pond-autotile\//.test(rules), 'the bay can be fished: any pond-autotile tile is a pond');

        assert.strictEqual(room.waterways.length, 1);
        const w = room.waterways[0];
        assert.deepStrictEqual([w.axis, w.to], ['v', H - 1], 'the channel runs off the south edge: boats sail in and out there');
        assert.ok(w.from > 0 && w.cols >= 2 && w.col + w.cols <= W);
        const islets = Object.keys(sprites).filter((k) => k.startsWith('matsushima-') && !k.includes('pier'));
        assert.ok(islets.includes('matsushima-ball-rock_0_0') && sprites['matsushima-islet_0_0'].length >= 2, 'pine islets, and the rock with a ball on top');
        for (const key of islets) {
            const m = cfg.spriteMetadata[key], wide = Math.round(0.5 / m.anchorX);
            for (const [x] of sprites[key]) assert.ok(x + wide - 1 < w.col, `${key} at column ${x} stands in the boats' lane`);
        }
        for (let y = w.from; y <= w.to; y++) {
            for (let x = w.col; x < w.col + w.cols; x++) {
                assert.strictEqual(name(water[`${x},${y}`]), 'pond-autotile_center', `channel cell ${x},${y} is not open water`);
            }
        }
    });

    test('Sendai stands clear of the stitched city and of every other town in devhouse.world (#66)', () => {
        const world = JSON.parse(fs.readFileSync(path.join(GV2, '..', 'devhouse.world'), 'utf8')).maps;
        const key = (m) => path.basename(m.fileName, '.tmj');
        const sendai = world.find((m) => key(m) === 'sendai');
        assert.ok(sendai, 'sendai.tmj is not in devhouse.world');
        assert.deepStrictEqual([sendai.width, sendai.height], [room.worldWidth, room.worldHeight]);
        const apart = (a, b) => a.x + a.width <= b.x || b.x + b.width <= a.x || a.y + a.height <= b.y || b.y + b.height <= a.y;
        for (const m of world) if (m !== sendai) assert.ok(apart(sendai, m), `Sendai overlaps ${key(m)}`);
        const districts = new Set(cfg.cities.TokyoCity.rooms.map((r) => r.room.toLowerCase()));
        const city = world.filter((m) => districts.has(key(m)));
        const box = { x: Math.min(...city.map((m) => m.x)), y: Math.min(...city.map((m) => m.y)) };
        box.width = Math.max(...city.map((m) => m.x + m.width)) - box.x;
        box.height = Math.max(...city.map((m) => m.y + m.height)) - box.y;
        assert.ok(apart(sendai, box), 'Sendai is inside the stitched city\'s box');
        const tokyo = world.find((m) => key(m) === 'tokyo');
        assert.ok(sendai.y + sendai.height / 2 < tokyo.y + tokyo.height / 2 && sendai.x + sendai.width / 2 > tokyo.x + tokyo.width / 2,
            'Sendai is north-east of Tokyo');
        const map = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'world-map.json'), 'utf8'));
        assert.deepStrictEqual(map.rooms.Sendai.cells, [W, H], 'world-map.json has no Sendai: run make_worldmap.py');
    });

    test('the Sendai-stay posts stand in Sendai, at the spot each is about (#66)', () => {
        const where = {};                                 // 'Name date' -> 'Room x,y'
        for (const [key, r] of Object.entries(cfg.rooms)) {
            for (const npc of r.npcs || []) {
                for (const [date, s] of Object.entries(npc.states || {})) {
                    if (s.present !== false && 'gridX' in s && date >= '2025-10-27' && date <= '2025-10-30') {
                        where[`${npc.name} ${date}`] = `${key} ${s.gridX},${s.gridY}`;
                    }
                }
            }
        }
        const near = (who, sprite, reachN = 4) => {
            const [room_, cell] = (where[who] || '').split(' ');
            assert.strictEqual(room_, 'Sendai', `${who} is in ${room_ || 'no room'}`);
            const [x, y] = cell.split(',').map(Number), [sx, sy] = at(sprite);
            const m = cfg.spriteMetadata[sprite], w = Math.round(0.5 / m.anchorX), h = Math.round(0.5 / m.anchorY);
            const dx = Math.max(sx - x, 0, x - (sx + w - 1)), dy = Math.max(sy - y, 0, y - (sy + h - 1));
            assert.ok(dx + dy <= reachN, `${who} at ${cell} is not at ${sprite} (${sx},${sy})`);
            assert.ok(open(x, y), `${who} stands on a solid cell`);
        };
        near('Damian 2025-10-27', 'sendai-zuihoden_0_0');         // 484
        near('Dylan 2025-10-27', 'matsushima-ferry_0_0', 6);      // 485 (on the promenade, beside the moored boat)
        near('Bailey 2025-10-27', 'matsushima-ferry_0_0', 6);     // 487
        near('Julia 2025-10-28', 'seven-eleven_0_0');             // 491 ("two minute walk here for coffee")
        near('Damian 2025-10-28', 'sendai-masamune_0_0');         // 496
        near('Julia 2025-10-29', 'sendai-pub_0_0');               // 501
        near('Bailey 2025-10-29', 'sendai-masamune_0_0');         // 505
        near('Damian 2025-10-29', 'sendai-kiln_0_0');             // 509
        near('Julia 2025-10-30', 'sendai-kiln_0_0');              // 515
        near('Bailey 2025-10-30', 'seven-eleven_0_0');            // 520 ("this 7-Eleven")
        // 480 is about leaving Tokyo ("straight here to catch a three hour train to Sendai"): it stays on Tokyo's platform
        assert.ok(where['Julia 2025-10-27'].startsWith('TokyoStation '), where['Julia 2025-10-27']);
    });

    test('Sendai art: a rerun of generate_sendai_town_art.py leaves the committed PNGs byte for byte (#394)', () => {
        // Into a copy of the committed sprites: every file whose pixels are unchanged is left as it is, even when
        // Pillow would encode it differently; a missing file is written and a file with other pixels rewritten,
        // both with the committed pixels (not bytes: the committed files came from another encoder).
        const snippet = [
            'import contextlib, io, json, os, shutil, sys, tempfile',
            'try:',
            '    from PIL import Image',
            'except ImportError:',
            '    print(json.dumps({"pillow": False})); sys.exit(0)',
            'import generate_sendai_town_art as s',
            'keys = sorted(s.build())',
            'tmp = tempfile.mkdtemp()',
            'try:',
            '    for key in keys:',
            '        shutil.copy("assets/sprites/%s.png" % key, tmp)',
            '    p = lambda key: os.path.join(tmp, key + ".png")',
            '    gone, other, reenc = keys[0], keys[1], keys[-1]',
            '    os.remove(p(gone))',
            '    Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(p(other))',
            '    Image.open(p(reenc)).convert("RGBA").save(p(reenc), compress_level=0)',
            '    stamp = open(p(reenc), "rb").read()',
            '    s.SPR, sys.argv = tmp, ["generate_sendai_town_art.py"]',
            '    with contextlib.redirect_stdout(io.StringIO()):',
            '        s.main()',
            '    rewritten = [key for key in keys if key not in (gone, other, reenc) and open(p(key), "rb").read() != open("assets/sprites/%s.png" % key, "rb").read()]',
            '    px = lambda f: Image.open(f).convert("RGBA").tobytes()',
            '    redrawn = [key for key in (gone, other) if px(p(key)) != px("assets/sprites/%s.png" % key)]',
            '    print(json.dumps({"pillow": True, "count": len(keys), "rewritten": rewritten, "redrawn": redrawn, "reenc_kept": open(p(reenc), "rb").read() == stamp}))',
            'finally:',
            '    shutil.rmtree(tmp)',
        ].join('\n');
        const { spawnSync } = require('child_process');
        const run = spawnSync('python3', ['-c', snippet], { cwd: GV2, encoding: 'utf8',
            timeout: 120000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.ok(!run.error, `python3 did not finish: ${run.error}`);
        assert.strictEqual(run.status, 0, run.stderr);
        const out = JSON.parse(run.stdout.trim().split('\n').pop());
        if (!out.pillow) return;
        assert.ok(out.count > 3, `the tool draws only ${out.count} sprites`);
        assert.ok(out.reenc_kept, 'a file with the same pixels in another encoding was rewritten');
        assert.deepStrictEqual(out.rewritten, [], 'files differ from the committed ones after a run');
        assert.deepStrictEqual(out.redrawn, [], 'a missing file or one with other pixels is not drawn back as committed');
    });
};
