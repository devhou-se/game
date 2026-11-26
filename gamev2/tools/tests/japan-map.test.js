// The Map overlay is a map of Japan with a dot per town (issue #211): config `places` (a town's real
// longitude / latitude and label), src/utils/Places.js (which towns, who is in them, where the labels
// go) and the picture and projection tools/make_japan_map.py writes to assets/map/japan.{png,json}.
module.exports = ({ test, assert, fs, path, GV2, game, load, realConfig }) => {
    load('utils/Places.js');
    const P = game('Places');
    // values made in the game's vm context, as this realm's own (deepStrictEqual compares prototypes)
    const plain = (v) => JSON.parse(JSON.stringify(v));
    const meta = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'japan.json'), 'utf8'));
    const xy = (key, config = realConfig()) => {
        const p = P.list(config).find(q => q.key === key);
        assert.ok(p, `no place ${key}`);
        return P.project(meta, p.lon, p.lat);
    };
    // the towns another lane is building: their geo is already in config, their rooms are not
    const COMING = ['Kanazawa', 'Toyama', 'Shirakawago'];
    // the world with those rooms in it, each a town of its own
    const withComing = () => {
        const c = realConfig();
        const rooms = Object.assign({}, c.rooms);
        for (const k of COMING) if (!rooms[k]) rooms[k] = { name: k, layers: [], npcs: [] };
        return Object.assign({}, c, { rooms });
    };
    const inside = (pts, lon, lat) => {
        let hit = false;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
            const [xi, yi] = pts[i], [xj, yj] = pts[j];
            if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) hit = !hit;
        }
        return hit;
    };

    test('the map of Japan: the picture, its projection and the four main islands (#211)', () => {
        const png = fs.readFileSync(path.join(GV2, meta.image));
        assert.deepStrictEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [meta.width, meta.height]);
        for (const island of ['Hokkaido', 'Honshu', 'Shikoku', 'Kyushu']) {
            assert.ok(meta.islands[island].length >= 15, `${island} is an outline, not a blob`);
            for (const [lon, lat] of meta.islands[island]) {
                const [x, y] = P.project(meta, lon, lat);
                assert.ok(x > 0 && y > 0 && x < meta.width && y < meta.height, `${island} runs off the picture at ${lon},${lat}`);
            }
        }
        // north is up, east is right, and the country keeps its shape (a degree of longitude is shorter)
        assert.ok(meta.pxPerLon < meta.pxPerLat && meta.pxPerLon > meta.pxPerLat * 0.7);
        assert.deepStrictEqual(plain(P.project(meta, meta.lon0, meta.lat0)), [0, 0]);
        // it is in check_generators, and what it writes is compared
        const check = fs.readFileSync(path.join(GV2, 'tools', 'check_generators.py'), 'utf8');
        assert.ok(/ART_TOOLS = \[[^\]]*'make_japan_map'/.test(check) && /OUTPUTS = \[[^\]]*'assets\/map'/.test(check));
    });

    test('towns sit where they are in Japan: Sapporo north of Tokyo north of Osaka, Fukuoka far south-west (#211)', () => {
        const [sx, sy] = xy('Sapporo'), [tx, ty] = xy('TokyoCity'), [ox, oy] = xy('Osaka');
        const [fx, fy] = xy('Fukuoka'), [ax, ay] = xy('Asahikawa'), [ex, ey] = xy('Sendai');
        assert.ok(sy < ey && ey < ty && ty < oy && oy < fy, 'north to south: Sapporo, Sendai, Tokyo, Osaka, Fukuoka');
        assert.ok(fx < ox && ox < tx && tx < ex, 'west to east: Fukuoka, Osaka, Tokyo, Sendai');
        assert.ok(ax > sx && ay < sy, 'Asahikawa is north-east of Sapporo');
        // far: further from Osaka than Osaka is from Tokyo
        assert.ok(Math.hypot(fx - ox, fy - oy) > Math.hypot(ox - tx, oy - ty));
        // every dot is on land, on the right island, and well inside the picture
        const island = { Sapporo: 'Hokkaido', Asahikawa: 'Hokkaido', Fukuoka: 'Kyushu' };
        for (const p of P.list(withComing())) {
            assert.ok(inside(meta.islands[island[p.key] || 'Honshu'], p.lon, p.lat), `${p.key} is in the sea`);
            const [x, y] = P.project(meta, p.lon, p.lat);
            assert.ok(x > 8 && y > 8 && x < meta.width - 8 && y < meta.height - 8, `${p.key} is at the edge`);
        }
    });

    test('every town that is a real place has a dot, one per city, and it comes from config (#211)', () => {
        const config = realConfig();
        const list = P.list(config);
        assert.deepStrictEqual(plain(list.map(p => p.label)).sort(), ['Asahikawa', 'Fukuoka', 'Osaka', 'Sapporo', 'Sendai', 'Tokyo']);
        // the stitched city is ONE dot, named after the city
        const tokyo = list.find(p => p.key === 'TokyoCity');
        assert.deepStrictEqual(plain(tokyo.rooms), plain(config.cities.TokyoCity.rooms).map(m => m.room));
        // every town a train goes to is on the map, but for the made-up ones (not in Japan: no dot,
        // still a train ride from Tokyo Station)
        const madeUp = ['Inaka', 'Yukimura'];
        for (const [room, st] of Object.entries(config.stations)) {
            const key = P.of(config, st.town);
            assert.strictEqual(P.of(config, room), key, `${room} is in its town`);
            if (madeUp.includes(st.town)) assert.strictEqual(key, null, `${st.town} has a dot`);
            else assert.ok(key, `${st.town} has no geo in config.places`);
        }
        // every other room is somewhere too: an interior is in the town its door leads to
        for (const room of Object.keys(config.rooms)) {
            if (!madeUp.some(m => room.startsWith(m))) assert.ok(P.of(config, room), `${room} is in no place`);
        }
        assert.strictEqual(P.of(config, 'KonbiniSapporo1'), 'Sapporo');
        assert.strictEqual(P.of(config, 'Izakaya'), 'TokyoCity');
        assert.strictEqual(P.of(config, 'Machi'), 'TokyoCity');
        assert.strictEqual(P.of(config, 'FukuokaStation'), 'Fukuoka');
        assert.strictEqual(P.whereText(config, 'Market'), 'Market (in Tokyo)');
        assert.strictEqual(P.whereText(config, 'TokyoStation'), 'Tokyo Station');
        assert.strictEqual(P.whereText(config, 'Inaka'), 'Inaka (not on this map)');

        // a geo whose room is not built yet is skipped, and shows the day the room lands
        for (const k of COMING) {
            if (config.rooms[k]) continue;
            assert.ok(config.places[k], `${k} has its geo ready`);
            assert.ok(!list.some(p => p.key === k));
        }
        const later = P.list(withComing());
        assert.strictEqual(later.length, list.length + COMING.filter(k => !config.rooms[k]).length);
        assert.strictEqual(later.find(p => p.key === 'Shirakawago').label, 'Shirakawa-go');
        // the districts of a stitched region can be dots of their own
        const region = Object.assign({}, withComing());
        region.cities = Object.assign({}, region.cities, { Hokuriku: { name: 'Hokuriku', rooms: COMING.map(room => ({ room, x: 0, y: 0 })) } });
        assert.strictEqual(P.of(region, 'Toyama'), 'Toyama');
        // a bad entry is no dot, not a crash
        const odd = Object.assign({}, config, { places: { Osaka: { geo: [135.5] }, Sendai: {}, Nowhere: { geo: [1, 2] }, Sapporo: { geo: [141.35, 43.06] } } });
        assert.deepStrictEqual(plain(P.list(odd)).map(p => [p.key, p.label]), [['Sapporo', 'Sapporo']]);
        assert.deepStrictEqual(plain(P.list({})), []);
    });

    test('a town with friends in it on the game date has the other dot: devhouse 2 and devhouse 3 days (#211)', () => {
        const config = realConfig();
        const on = (date, opts) => Array.from(P.present(config, date, opts)).sort();
        // devhouse 2: three in Sendai and one at Tokyo Station; then Fukuoka, with one in Machi (Tokyo)
        // and one in Inaka, which is not on the map
        assert.deepStrictEqual(on('2025-10-27'), ['Sendai', 'TokyoCity']);
        assert.deepStrictEqual(on('2025-11-10'), ['Fukuoka', 'TokyoCity']);
        assert.deepStrictEqual(on('2025-10-05'), ['TokyoCity']);
        // devhouse 3: everyone in Sapporo, then Asahikawa; nobody anywhere on a lead-in day
        assert.deepStrictEqual(on('2027-02-20'), ['Sapporo']);
        assert.deepStrictEqual(on('2027-02-26'), ['Asahikawa']);
        assert.deepStrictEqual(on('2027-02-10'), []);
        // the same people the intro's "where the friends are" counts — never the one being played
        const groups = game('Trips.membersByRoom')(config, '2025-10-27');
        const alone = groups.find(g => g.room === 'TokyoStation').members[0].name.toLowerCase();
        assert.deepStrictEqual(on('2025-10-27', { played: alone }), ['Sendai']);
        // the overlay says where, never who or how many
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        const body = src.slice(src.indexOf('    showMap() {'), src.indexOf('     * Show credits overlay'));
        assert.ok(/Places\.present\(config, gameDate\(\), \{ played \}\)/.test(body));
        assert.ok(!/npc\.name|npcsIn|members\.length|'world-map'/.test(body), 'no names, no NPC dots, no counts, not the old picture');
        assert.ok(body.includes('Hints.text(this, Places.LEGEND)'));
    });

    test('labels never cover each other or a dot and never leave the map: desktop, landscape and portrait phone (#211)', () => {
        const fit = game('UIScale.mapFit'), MAX = game('UIScale.MAP_MAX_SCALE');
        const hit = (a, b) => a.x1 > b.x0 && a.x0 < b.x1 && a.y1 > b.y0 && a.y0 < b.y1;
        // [name, canvas width in view, cropped, text growth, the picture's scale]
        const views = [['desktop 1280x960', 1280, false, 1, 3], ['landscape phone 844x390', 1280, false, 1.6, 3],
            ['portrait phone, narrowest view', game('Viewport.MIN_VISIBLE'), true, 1.6, 2], ['portrait phone 390x844', 612, true, 1.3, 2.5]];
        for (const [name, W, cropped, k, scale] of views) {
            const s = fit(W, 960, meta.width, meta.height, cropped, MAX);
            assert.strictEqual(s, scale, `${name}: the picture is drawn in half steps`);
            const bounds = { x: (W - meta.width * s) / 2, y: (960 - meta.height * s) / 2 + 4, w: meta.width * s, h: meta.height * s };
            assert.ok(bounds.x >= 12 && bounds.y >= 60 && bounds.y + bounds.h <= 960 - 70, `${name}: room for the title and the two footer lines`);
            for (const config of [realConfig(), withComing()]) {
                const places = P.list(config);
                // wherever the player is, and whoever is where: nobody, everybody, each town alone
                for (const here of [null].concat(places.map(p => p.key))) {
                    for (const present of [[], places.map(p => p.key)].concat(places.map(p => [p.key]))) {
                        const font = Math.round(16 * k);
                        const dots = places.map(p => {
                            const [x, y] = P.project(meta, p.lon, p.lat);
                            // the bold pixel face is 0.5 em a glyph; allow more, and the label's padding
                            return { key: p.key, x: Math.round(bounds.x + x * s), y: Math.round(bounds.y + y * s),
                                r: P.reach(p.key === here, present.includes(p.key)) * k,
                                w: Math.ceil(p.label.length * font * 0.62) + 6, h: Math.ceil(font * 1.2) + 2 };
                        });
                        const spots = P.layout(dots, bounds);
                        const why = `${name}, at ${here}, friends in ${present}`;
                        for (const d of dots) {
                            const at = spots[d.key];
                            assert.ok(at.fits, `${why}: no room for ${d.key}'s label`);
                            assert.ok(at.box.x0 >= bounds.x && at.box.y0 >= bounds.y && at.box.x1 <= bounds.x + bounds.w &&
                                at.box.y1 <= bounds.y + bounds.h, `${why}: ${d.key}'s label leaves the map`);
                            assert.ok(Math.abs(at.box.x1 - at.box.x0 - d.w) < 1e-6 && Math.abs(at.box.y1 - at.box.y0 - d.h) < 1e-6);
                            for (const o of dots) {
                                if (o === d) continue;
                                assert.ok(!hit(at.box, spots[o.key].box), `${why}: ${d.key} and ${o.key} labels overlap`);
                                assert.ok(!hit(at.box, { x0: o.x - o.r, y0: o.y - o.r, x1: o.x + o.r, y1: o.y + o.r }),
                                    `${why}: ${d.key}'s label covers ${o.key}'s dot`);
                            }
                            // its own dot is clear of it, and a label that had to stand off gets a leader line
                            assert.ok(!hit(at.box, { x0: d.x - d.r, y0: d.y - d.r, x1: d.x + d.r, y1: d.y + d.r }), `${why}: ${d.key}'s label is on its dot`);
                            const gap = Math.max(at.box.x0 - d.x, d.x - at.box.x1, at.box.y0 - d.y, d.y - at.box.y1);
                            assert.strictEqual(at.leader, gap > d.r + P.LABEL_GAP + 1, `${why}: ${d.key} leader`);
                        }
                        // the dots themselves are told apart: today's towns stand clear of each other, and the
                        // three Hokuriku towns to come (35 km apart) may touch but never hide one another
                        for (const a of dots) for (const b of dots) {
                            if (a.key >= b.key) continue;
                            const near = COMING.includes(a.key) && COMING.includes(b.key);
                            assert.ok(Math.hypot(a.x - b.x, a.y - b.y) >= (near ? 1 : 2) * P.DOT * k + (near ? 0 : 2), `${why}: ${a.key} and ${b.key} dots merge`);
                        }
                    }
                }
            }
        }
        // phones: a label is at least 10 CSS px (16px grown 1.6x on a 960-high canvas shown 390 high)
        assert.ok(Math.round(16 * game('UIScale.MAX_TEXT_GROWTH')) * 390 / 960 >= game('UIScale.MIN_TEXT'));
        // a label with nowhere to go says so
        const tight = P.layout([{ key: 'a', x: 10, y: 10, r: 5, w: 80, h: 20 }], { x: 0, y: 0, w: 40, h: 20 });
        assert.strictEqual(tight.a.fits, false);
    });

    test('debug map-click travel: the dot nearest the click, and the cell outside that town\'s station (#211)', () => {
        const config = realConfig();
        const places = P.list(config);
        const [sx, sy] = xy('Sapporo'), [ax, ay] = xy('Asahikawa');
        assert.strictEqual(P.nearest(meta, places, sx + 2, sy - 1, 9).key, 'Sapporo');
        // between the two Hokkaido towns the nearer one wins; out at sea is nobody
        assert.strictEqual(P.nearest(meta, places, sx * 0.4 + ax * 0.6, sy * 0.4 + ay * 0.6, 20).key, 'Asahikawa');
        assert.strictEqual(P.nearest(meta, places, 20, 20, 9), null);
        for (const p of places) {
            const to = P.arrival(config, p.key);
            assert.ok(to && p.rooms.includes(to.room), `${p.key} has no arrival cell`);
            const station = Object.keys(config.stations).find(k => (config.rooms[k].transporters || [])
                .some(t => t.targetRoom === to.room && t.targetX === to.x && t.targetY === to.y));
            assert.ok(station, `${p.key}: ${JSON.stringify(to)} is not outside a station door`);
        }
        assert.deepStrictEqual(plain(P.arrival(config, 'Sendai')), { room: 'Sendai', x: 35, y: 10 });
        assert.deepStrictEqual(plain(P.arrival(config, 'TokyoCity')), { room: 'Palace', x: 27, y: 10 });
        assert.strictEqual(P.arrival(config, 'Nowhere'), null);
        // a town with no station is entered by any door into it
        const noTrains = Object.assign({}, config, { stations: {} });
        assert.ok(P.arrival(noTrains, 'Sapporo').room === 'Sapporo');
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(/Places\.nearest\(meta, places, ix, iy, UIScale\.MAP_CLICK_REACH \/ s\)/.test(src));
        assert.ok(/this\.roomManager\.switchRoom\(to\.room, cell\[0\], cell\[1\]\)/.test(src));
    });
};
