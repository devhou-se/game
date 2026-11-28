// The Map overlay is a map of Japan with a dot per town (issue #211): config `places` (a town's real
// longitude / latitude and label), src/utils/Places.js (which towns, who is in them, where the labels
// go) and the picture and projection tools/make_japan_map.py writes to assets/map/japan.{png,json}.
module.exports = ({ test, assert, fs, path, GV2, game, load, realConfig }) => {
    if (game('typeof Places') === 'undefined') load('utils/Places.js');   // airports.test.js loads it too
    const P = game('Places');
    // values made in the game's vm context, as this realm's own (deepStrictEqual compares prototypes)
    const plain = (v) => JSON.parse(JSON.stringify(v));
    const meta = JSON.parse(fs.readFileSync(path.join(GV2, 'assets', 'map', 'japan.json'), 'utf8'));
    const xy = (key, config = realConfig()) => {
        const p = P.list(config).find(q => q.key === key);
        assert.ok(p, `no place ${key}`);
        return P.project(meta, p.lon, p.lat);
    };
    // Hokuriku (#68): three districts of one stitched city, each a real town of its own and so a dot of its own
    const HOKURIKU = ['Kanazawa', 'Toyama', 'Shirakawago'];
    // the world as it was before those rooms were built: their geo in config, their rooms not
    const before = () => {
        const c = realConfig();
        const rooms = Object.assign({}, c.rooms);
        for (const k of HOKURIKU) delete rooms[k];
        return Object.assign({}, c, { rooms });
    };
    // the small places walked to from a town (#68) that are not built yet: the room is a stub, the geo and
    // label are the ones its ticket will put in config `places`. A ticket that builds one drops it from here
    // (Himeji is built, #255, and Karuizawa, #260: they are in config, and so in every Map below)
    const SMALL = { Okayama: [[133.92, 34.66], 'Okayama'], Nara: [[135.84, 34.69], 'Nara'],
        LakeBiwa: [[136.10, 35.30], 'Lake Biwa'] };
    const small = (keys) => {
        const c = realConfig();
        const rooms = Object.assign({}, c.rooms), places = Object.assign({}, c.places);
        for (const k of keys) {
            rooms[k] = { name: SMALL[k][1] };
            places[k] = { geo: SMALL[k][0], label: SMALL[k][1], minor: true };
        }
        return Object.assign({}, c, { rooms, places });
    };
    // the Map as the tickets land: Okayama, Nara and Lake Biwa in that order (Himeji and Karuizawa, which
    // waited on none of them, are there already)
    const KANSAI = ['Okayama', 'Nara', 'LakeBiwa'];
    const STAGES = KANSAI.map((_, i) => KANSAI.slice(0, i + 1));
    const LANDING = STAGES;
    // dots that may touch but never hide one another: the three Hokuriku towns (35 km apart), and Nara beside Osaka
    const MAY_TOUCH = [['Kanazawa', 'Toyama'], ['Kanazawa', 'Shirakawago'], ['Shirakawago', 'Toyama'], ['Nara', 'Osaka']];
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
        for (const p of P.list(realConfig())) {
            const [x, y] = P.project(meta, p.lon, p.lat);
            if (p.overseas) {
                // not in Japan (#218): out in the open sea, on no island, in the bottom-right of the picture,
                // south of every town
                for (const [name, pts] of Object.entries(meta.islands)) assert.ok(!inside(pts, p.lon, p.lat), `${p.key} is on ${name}`);
                assert.ok(x > meta.width * 0.7 && y > meta.height * 0.8, `${p.key} is not in the corner`);
                for (const q of P.list(realConfig())) {
                    if (q.overseas) continue;
                    const [qx, qy] = P.project(meta, q.lon, q.lat);
                    assert.ok(y > qy, `${p.key} is north of ${q.key}`);
                }
                assert.ok(x < meta.width - 8 && y < meta.height - 8, `${p.key} is at the edge`);
                continue;
            }
            assert.ok(inside(meta.islands[island[p.key] || 'Honshu'], p.lon, p.lat), `${p.key} is in the sea`);
            assert.ok(x > 8 && y > 8 && x < meta.width - 8 && y < meta.height - 8, `${p.key} is at the edge`);
        }
    });

    test('every town that is a real place has a dot, one per town, and it comes from config (#211)', () => {
        const config = realConfig();
        const list = P.list(config);
        // (the home city is the one place overseas, #218: its label is its room's name, written nowhere else)
        const home = config.rooms.SanFranbourne.name;
        assert.deepStrictEqual(plain(list.map(p => p.label)).sort(), ['Asahikawa', 'Fukuoka', 'Himeji', 'Kanazawa', 'Karuizawa', 'Osaka', home, 'Sapporo', 'Sendai', 'Shirakawa-go', 'Tokyo', 'Toyama'].sort());
        assert.deepStrictEqual(plain(list.filter(p => p.overseas).map(p => p.key)), ['SanFranbourne']);
        assert.ok(!('label' in config.places.SanFranbourne) && !JSON.stringify(config.airports).includes(home), 'the name is written once');
        // the stitched city is ONE dot, named after the city
        const tokyo = list.find(p => p.key === 'TokyoCity');
        assert.deepStrictEqual(plain(tokyo.rooms), plain(config.cities.TokyoCity.rooms).map(m => m.room));
        // every town a train goes to is on the map: the made-up ones, which had no dot, are deleted (#68)
        for (const [room, st] of Object.entries(config.stations)) {
            const key = P.of(config, st.town);
            assert.strictEqual(P.of(config, room), key, `${room} is in its town`);
            assert.ok(key, `${st.town} has no geo in config.places`);
        }
        // every other room is somewhere too: an interior is in the town its door leads to
        for (const room of Object.keys(config.rooms)) assert.ok(P.of(config, room), `${room} is in no place`);
        assert.strictEqual(P.of(config, 'KonbiniSapporo1'), 'Sapporo');
        assert.strictEqual(P.of(config, 'Izakaya'), 'TokyoCity');
        assert.strictEqual(P.of(config, 'FukuokaStation'), 'Fukuoka');
        // a district of Tokyo is named by its display name, and says its city (#219: the room keys are unchanged)
        assert.strictEqual(P.whereText(config, 'Market'), 'Asakusa (in Tokyo)');
        assert.strictEqual(P.whereText(config, 'Tokyo'), 'Imperial Palace (in Tokyo)');
        assert.strictEqual(P.whereText(config, 'Palace'), 'Marunouchi (in Tokyo)');
        assert.strictEqual(P.whereText(config, 'Park'), 'Park (in Tokyo)');
        assert.strictEqual(P.whereText(config, 'KonbiniMarket1'), '7-Eleven · Asakusa 1 (in Tokyo)');
        assert.strictEqual(tokyo.label, 'Tokyo', "the city's dot keeps the city's name");
        assert.strictEqual(P.whereText(config, 'TokyoStation'), 'Tokyo Station');
        // no room of the game needs it now, but a town with no geo still says so rather than naming a wrong place
        assert.strictEqual(P.whereText({ rooms: { Nowhere: { name: 'Nowhere' } } }, 'Nowhere'), 'Nowhere (not on this map)');

        // the districts of a stitched region are dots of their own where they are real places far apart:
        // Hokuriku is one stitched city and three towns (Tokyo's districts are one), and it has no dot itself
        assert.deepStrictEqual(plain(config.cities.HokurikuCity.rooms).map(m => m.room).sort(), HOKURIKU.slice().sort());
        assert.ok(!config.places.HokurikuCity && !list.some(p => p.key === 'HokurikuCity'));
        for (const k of HOKURIKU) {
            assert.deepStrictEqual(plain(list.find(p => p.key === k).rooms), [k]);
            assert.strictEqual(P.of(config, k), k, `${k} is its own town, not "Hokuriku"`);
        }
        // the label is the town's name as the HUD has it, never the room key
        assert.strictEqual(list.find(p => p.key === 'Shirakawago').label, 'Shirakawa-go');
        assert.strictEqual(config.rooms.Shirakawago.name, 'Shirakawa-go');
        assert.ok(!list.some(p => p.label === 'Shirakawago'));
        // the station and the konbini are in Kanazawa; the two villages have neither
        assert.strictEqual(P.of(config, 'KanazawaStation'), 'Kanazawa');
        assert.strictEqual(P.of(config, 'KonbiniKanazawa1'), 'Kanazawa');
        assert.strictEqual(P.whereText(config, 'Shirakawago'), 'Shirakawa-go');
        assert.strictEqual(P.whereText(config, 'KonbiniKanazawa1'), '7-Eleven · Kanazawa');
        // a geo whose room is not built yet is skipped, and shows the day the room lands
        const earlier = P.list(before());
        assert.strictEqual(earlier.length, list.length - HOKURIKU.length);
        for (const k of HOKURIKU) assert.ok(config.places[k] && !earlier.some(p => p.key === k));
        // a bad entry is no dot, not a crash
        const odd = Object.assign({}, config, { places: { Osaka: { geo: [135.5] }, Sendai: {}, Nowhere: { geo: [1, 2] }, Sapporo: { geo: [141.35, 43.06] } } });
        assert.deepStrictEqual(plain(P.list(odd)).map(p => [p.key, p.label]), [['Sapporo', 'Sapporo']]);
        assert.deepStrictEqual(plain(P.list({})), []);
    });

    test('a town with friends in it on the game date has the other dot: devhouse 2 and devhouse 3 days (#211)', () => {
        const config = realConfig();
        const on = (date, opts) => Array.from(P.present(config, date, opts)).sort();
        // devhouse 2: three in Sendai and one at Tokyo Station; then Fukuoka, with one still at Kanazawa's
        // shrine (the Hokuriku posts stand in Hokuriku, #68)
        assert.deepStrictEqual(on('2025-10-27'), ['Sendai', 'TokyoCity']);
        assert.deepStrictEqual(on('2025-11-10'), ['Fukuoka', 'Kanazawa']);
        // Hokuriku: a member in Shirakawa-go or Toyama lights THAT town's dot, not Kanazawa's or one for the region
        const rooms = (date) => game('Trips.membersByRoom')(config, date).map(g => g.room);
        assert.ok(rooms('2025-11-03').includes('Shirakawago') && rooms('2025-11-03').includes('Toyama') && !rooms('2025-11-03').includes('Kanazawa'));
        assert.deepStrictEqual(on('2025-11-03').filter(k => HOKURIKU.includes(k)), ['Shirakawago', 'Toyama']);
        assert.ok(rooms('2025-11-05').includes('KanazawaStation'), 'one is on the platform at Kanazawa Station');
        assert.deepStrictEqual(on('2025-11-05').filter(k => HOKURIKU.includes(k)), ['Kanazawa', 'Shirakawago']);
        // the Lake Biwa ride has no town of its own yet: it stands on Osaka's platform, the city it set out from (#68)
        assert.deepStrictEqual(on('2025-11-06'), ['Kanazawa', 'Osaka']);
        // the gold ring is the district the player stands in (as a Tokyo district is Tokyo), an interior its town
        for (const k of HOKURIKU) assert.strictEqual(P.of(config, k), k);
        assert.strictEqual(P.of(config, 'Park'), 'TokyoCity');
        const src0 = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src0.includes('const hereRoom = this.roomManager.currentDistrict();') && src0.includes('const here = Places.of(config, hereRoom);'));
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
        // (these four are the extremes: the widest and the narrowest view, the least and the most text growth)
        const views = [['desktop 1280x960', 1280, false, 1, 3], ['landscape phone 844x390', 1280, false, 1.6, 3],
            ['portrait phone, narrowest view', game('Viewport.MIN_VISIBLE'), true, 1.6, 2], ['portrait phone 390x844', 612, true, 1.3, 2.5]];
        // the view a portrait touch window really gets (#68): canvas width in view, text growth, the picture's
        // scale, worked out with the game's own functions as UIScale.textSize and showMap do
        const viewOf = (name, winW, winH) => {
            const l = game('Viewport').layout(winW, winH, true), U = game('UIScale');
            const W = 1280 - l.crop.left - l.crop.right, down = 1 / l.scale;
            const k = Math.round(100 * Math.min(U.MAX_TEXT_GROWTH, down > 1.02 ? Math.min(U.MAX_ZOOM, down) : 1)) / 100;
            return [name, W, W < 1280, k, fit(W, 960, meta.width, meta.height, W < 1280, MAX)];
        };
        // ...each as read from the running game at that size (the 390x844 phone grows its text 1.57, not the
        // 1.3 of the row above, and a tall phone gets the narrowest width with less growth)
        for (const [winW, winH, W, k, scale] of [[320, 780, 560, 1.6, 2], [360, 840, 560, 1.56, 2], [360, 800, 597, 1.6, 2.5],
            [390, 844, 612, 1.57, 2.5], [412, 915, 579, 1.41, 2.5]]) {
            const view = viewOf(`a ${winW}x${winH} phone`, winW, winH);
            assert.deepStrictEqual(view.slice(1), [W, true, k, scale], `${view[0]}: the view the game draws`);
            views.push(view);
        }
        const configs = [['today', realConfig()], ['before Hokuriku', before()]]
            .concat(LANDING.map(keys => [`with ${keys.join(', ')}`, small(keys)]));
        let coursesSeen = 0, coursesCut = 0;
        for (const [name, W, cropped, k, scale] of views) {
            const s = fit(W, 960, meta.width, meta.height, cropped, MAX);
            assert.strictEqual(s, scale, `${name}: the picture is drawn in half steps`);
            const bounds = { x: (W - meta.width * s) / 2, y: (960 - meta.height * s) / 2 + 4, w: meta.width * s, h: meta.height * s };
            assert.ok(bounds.x >= 12 && bounds.y >= 60 && bounds.y + bounds.h <= 960 - 70, `${name}: room for the title and the two footer lines`);
            for (const [stage, config] of configs) {
                const places = P.list(config);
                // wherever the player is, and whoever is where: nobody, everybody, each town alone
                for (const here of [null].concat(places.map(p => p.key))) {
                    for (const present of [[], places.map(p => p.key)].concat(places.map(p => [p.key]))) {
                        const font = Math.round(16 * k);
                        const dots = places.map(p => {
                            const [x, y] = P.project(meta, p.lon, p.lat);
                            // the bold pixel face is 0.5 em a glyph; allow more, and the label's padding
                            // (a small place's label gives way to the towns', unless you or friends are there: as showMap's)
                            return { key: p.key, x: Math.round(bounds.x + x * s), y: Math.round(bounds.y + y * s),
                                r: P.reach(p.key === here, present.includes(p.key)) * k,
                                minor: p.minor && p.key !== here && !present.includes(p.key),
                                w: Math.ceil(p.label.length * font * 0.62) + 6, h: Math.ceil(font * 1.2) + 2 };
                        });
                        // an overseas place with nobody in it is a plane with a dashed course to the corner
                        // of the map (GameScene.showMap draws these same boxes): labels keep off the dashes (#220)
                        const course = places.flatMap((p, i) => (p.overseas && !present.includes(p.key) ? P.course(dots[i], bounds, k) : []));
                        const spots = P.layout(dots, bounds, course);
                        const why = `${name}, ${stage}, at ${here}, friends in ${present}`;
                        // ...in every view of today's Map: where one order of the labels left some label no
                        // spot clear of them (the narrowest portrait view, in Tokyo), the stuck label is laid
                        // out first and they all keep clear (#68). The Maps that are not today's (before
                        // Hokuriku, with the small places to come) are still let off in the narrowest view,
                        // where keeping off them could leave a label no spot at all: there the dashes under a
                        // label are not drawn (the course starts clear of it), and most of the course still is
                        const strict = config === realConfig() || !cropped || W > game('Viewport.MIN_VISIBLE');
                        const drawn = P.uncovered(course, spots);
                        places.forEach((p, i) => {
                            const d = dots[i], on = course.filter((dash) => hit(spots[d.key].box, dash)).length;
                            assert.ok(!drawn.some((dash) => hit(spots[d.key].box, dash)), `${why}: a dash is drawn under ${d.key}'s label`);
                            const near = (dash) => hit(spots[d.key].box, { x0: dash.x0 - P.LABEL_GAP, y0: dash.y0 - P.LABEL_GAP, x1: dash.x1 + P.LABEL_GAP, y1: dash.y1 + P.LABEL_GAP });
                            if (strict) assert.strictEqual(course.filter(near).length, 0, `${why}: ${d.key}'s label touches the flight's course`);
                            if (strict) assert.strictEqual(on, 0, `${why}: ${d.key}'s label is on the flight's course`);
                        });
                        assert.ok(drawn.length >= course.length / 2 && (!course.length || drawn.length >= 5), `${why}: ${drawn.length} of ${course.length} dashes are left`);
                        if (course.length) coursesSeen++;
                        if (drawn.length < course.length) coursesCut++;
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
                        // the dots themselves are told apart: towns stand clear of each other, and the pairs of
                        // MAY_TOUCH may touch but never hide one another
                        for (const a of dots) for (const b of dots) {
                            if (a.key >= b.key) continue;
                            const near = MAY_TOUCH.some(([m, n]) => m === a.key && n === b.key);
                            assert.ok(Math.hypot(a.x - b.x, a.y - b.y) >= (near ? 1 : 2) * P.DOT * k + (near ? 0 : 2), `${why}: ${a.key} and ${b.key} dots merge`);
                        }
                    }
                }
            }
        }
        // phones: a label is at least 10 CSS px (16px grown 1.6x on a 960-high canvas shown 390 high)
        assert.ok(Math.round(16 * game('UIScale.MAX_TEXT_GROWTH')) * 390 / 960 >= game('UIScale.MIN_TEXT'));
        assert.ok(coursesSeen > 0, 'the home city and its course were laid out');
        assert.ok(coursesCut < coursesSeen / 20, `a label had to stand on the course in ${coursesCut} of ${coursesSeen} layouts`);
        // the course: 3px dashes every 10, from clear of the plane toward the bottom-right corner, inside the map
        const box = { x: 100, y: 50, w: 600, h: 400 };
        const dashes = plain(P.course({ x: 500, y: 300 }, box, 1));
        assert.ok(dashes.length > 10);
        const first = dashes[0], last = dashes[dashes.length - 1];
        assert.ok(Math.hypot(first.x0 + 1 - 500, first.y0 + 1 - 300) >= P.PLANE + 5, 'the first dash is clear of the plane');
        assert.ok(last.x1 <= 700 && last.y1 <= 450 && last.x0 > first.x0 && last.y0 > first.y0, 'it runs out to the corner and stops inside the map');
        for (const d of dashes) assert.deepStrictEqual([d.x1 - d.x0, d.y1 - d.y0], [P.COURSE_DASH, P.COURSE_DASH]);
        // the bug: beside its dot (the first choice) the label covers its own course; told about it, it moves
        const sfb = [{ key: 'sfb', x: 500, y: 300, r: P.DOT, w: 140, h: 22 }];
        const blind = P.layout(sfb, box).sfb, aware = P.layout(sfb, box, dashes).sfb;
        assert.ok(dashes.some((d) => hit(blind.box, d)), 'a label to the right of the plane is on the dashes');
        assert.ok(aware.fits && !dashes.some((d) => hit(aware.box, d)));
        // ...and not just off them: a label whose edge is 2px from a dash (the real label at 1280x960) moves too
        const close = [{ x0: blind.box.x0 + 4, y0: blind.box.y1 + 2, x1: blind.box.x0 + 7, y1: blind.box.y1 + 5 }];
        assert.ok(!hit(blind.box, close[0]));
        assert.notDeepStrictEqual(plain(P.layout(sfb, box, close).sfb.box), plain(blind.box));
        const src1 = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src1.includes('const spots = Places.layout(dots, mapBox, dots.flatMap(d => d.course));\n        for (const d of dots) d.course = Places.uncovered(d.course, spots);'));
        // where keeping off the dashes would leave a label no spot, the labels win and those dashes are left out
        const cramped = { x: 0, y: 0, w: 60, h: 12 }, mark = [{ x0: 20, y0: 4, x1: 23, y1: 7 }, { x0: 2, y0: 4, x1: 5, y1: 7 }];
        const only = P.layout([{ key: 'a', x: 6, y: 6, r: 4, w: 40, h: 12 }], cramped, mark);
        assert.ok(only.a.fits && hit(only.a.box, mark[0]));
        assert.deepStrictEqual(plain(P.uncovered(mark, only)), [mark[1]]);
        // a label with nowhere to go says so, and is put beside its dot regardless (no order can help it)
        const tight = P.layout([{ key: 'a', x: 10, y: 10, r: 5, w: 80, h: 20 }], { x: 0, y: 0, w: 40, h: 20 });
        assert.strictEqual(tight.a.fits, false);
        assert.deepStrictEqual(plain([tight.a.x, tight.a.y, tight.a.leader, tight.a.box]), [59, 10, false, { x0: 19, y0: 0, x1: 99, y1: 20 }]);
    });

    test('the Map\'s labels: a small place\'s label gives way to a town\'s, and a label left with no spot is laid out first (#68)', () => {
        const hit = (a, b) => a.x1 > b.x0 && a.x0 < b.x1 && a.y1 > b.y0 && a.y0 < b.y1;
        // a place is small where config says so: Himeji (#255) and Karuizawa (#260), and the stubs of the places to come
        assert.deepStrictEqual(plain(P.list(realConfig()).filter(p => p.minor).map(p => p.key)).sort(), ['Himeji', 'Karuizawa'], 'the minor places');
        const all = P.list(small(Object.keys(SMALL)));
        assert.deepStrictEqual(plain(all.filter(p => p.minor).map(p => p.key)).sort(), Object.keys(SMALL).concat('Himeji', 'Karuizawa').sort());
        assert.strictEqual(all.length, P.list(realConfig()).length + 3, 'each has a dot of its own');
        assert.deepStrictEqual(plain(LANDING.map(keys => keys.length)), [1, 2, 3], 'the three Maps the tickets still pass through');

        // two dots that want the same spot (the first choice of each, to its right): the one that is not minor
        // has it, whichever key sorts first, and the minor one stands off on a leader line and still fits
        const beside = { x0: 18, x1: 68 };
        const pair = (a, b) => [Object.assign({ key: 'a', x: 10, y: 10, r: 4, w: 50, h: 14 }, a), Object.assign({ key: 'b', x: 10, y: 22, r: 4, w: 50, h: 14 }, b)];
        for (const [dots, town, other] of [[pair({}, {}), 'a', 'b'], [pair({}, { minor: true }), 'a', 'b'], [pair({ minor: true }, {}), 'b', 'a']]) {
            const wide = P.layout(dots, { x: 0, y: 0, w: 200, h: 40 });
            assert.deepStrictEqual(plain([wide[town].box.x0, wide[town].box.x1, wide[town].leader, wide[town].fits]), [beside.x0, beside.x1, false, true], `${town} keeps the spot beside its dot`);
            assert.ok(wide[other].fits && wide[other].leader && !hit(wide[other].box, wide[town].box), `${other} takes what is left`);
            // ...and with room for one label only, it is the town's: no order gives both a spot, so the first is kept
            const narrow = P.layout(dots, { x: 0, y: 0, w: 70, h: 40 });
            assert.deepStrictEqual([narrow[town].fits, narrow[other].fits], [true, false], `room for one: ${town}'s`);
        }
        // a small place with the player or friends in it is not `minor` to the layout: its label is the one looked for
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(src.includes('minor: p.minor && !isHere && !isPresent,'));

        // the order is a guess. Three dots along the top edge: `b` and `c`, the closest pair, choose first; `b`
        // takes the spot under itself and `c` the next one down, which between them leave `a` nowhere to go.
        // `a` is then laid out first, under and to the right of its dot, and there is a spot for all three
        const three = [{ key: 'a', x: 10, y: 10, r: 4, w: 40, h: 12 }, { key: 'b', x: 60, y: 10, r: 4, w: 40, h: 12 }, { key: 'c', x: 80, y: 10, r: 4, w: 40, h: 12 }];
        const again = P.layout(three, { x: 0, y: 0, w: 100, h: 50 });
        assert.deepStrictEqual(plain(three.map(d => [again[d.key].box.x0, again[d.key].box.y0, again[d.key].leader, again[d.key].fits])),
            [[12, 18, false, true], [40, 32, true, true], [60, 18, false, true]]);
        for (const d of three) {
            for (const o of three) {
                if (o === d) continue;
                assert.ok(!hit(again[d.key].box, again[o.key].box), `${d.key} and ${o.key} labels overlap`);
                assert.ok(!hit(again[d.key].box, { x0: o.x - o.r, y0: o.y - o.r, x1: o.x + o.r, y1: o.y + o.r }), `${d.key}'s label covers ${o.key}'s dot`);
            }
        }
        // the case it is for: Himeji's dot alone, in the narrowest portrait view, standing in Tokyo with friends
        // in Fukuoka. One order leaves Fukuoka's label no room; laid out again, all twelve have a spot
        // (Himeji is built now, #255: this is today's Map)
        const config = realConfig(), places = P.list(config);
        const W = game('Viewport.MIN_VISIBLE'), k = 1.6, s = 2, font = Math.round(16 * k);
        const bounds = { x: (W - meta.width * s) / 2, y: (960 - meta.height * s) / 2 + 4, w: meta.width * s, h: meta.height * s };
        const dots = places.map(p => {
            const [x, y] = P.project(meta, p.lon, p.lat);
            return { key: p.key, x: Math.round(bounds.x + x * s), y: Math.round(bounds.y + y * s),
                r: P.reach(p.key === 'TokyoCity', p.key === 'Fukuoka') * k, minor: p.minor,
                w: Math.ceil(p.label.length * font * 0.62) + 6, h: Math.ceil(font * 1.2) + 2 };
        });
        const course = P.course(dots.find(d => d.key === 'SanFranbourne'), bounds, k);
        const spots = P.layout(dots, bounds, course);
        assert.strictEqual(dots.length, 12);
        for (const d of dots) assert.ok(spots[d.key].fits, `no room for ${d.key}'s label`);
        assert.strictEqual(P.uncovered(course, spots).length, course.length, 'and none stands on the flight\'s course');
    });

    test('debug map-click travel: the dot nearest the click, and the cell outside that town\'s station or on its road in (#211)', () => {
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
            const from = Object.keys(config.rooms).filter(k => (config.rooms[k].transporters || [])
                .some(t => t.targetRoom === to.room && t.targetX === to.x && t.targetY === to.y));
            const served = Object.values(config.stations).some(st => p.rooms.includes(st.town));
            // a town with a station: outside its door. Without one (Shirakawa-go, Toyama, Himeji, Karuizawa): no station cell.
            // The overseas place has no station either: outside its airport's door (#218)
            if (served) assert.ok(from.some(k => config.stations[k]), `${p.key}: ${JSON.stringify(to)} is not outside a station door`);
            else if (p.overseas) assert.ok(from.some(k => config.airports[k] && config.airports[k].serves === to.room), `${p.key}: ${JSON.stringify(to)} is not outside its airport's door`);
            else assert.ok(from.length && (HOKURIKU.concat('Himeji', 'Karuizawa').includes(p.key)), `${p.key}: ${JSON.stringify(to)} is not inside a door into it`);
        }
        // a town with no station is entered as a traveller from the railhead walks in: by the door or seam
        // from the room the fewest room changes from a station. Shirakawa-go by its west road from Kanazawa
        // (one change from Kanazawa Station), not from Toyama; Toyama by its only road, from Shirakawa-go
        assert.deepStrictEqual(plain(P.arrival(config, 'Kanazawa')), { room: 'Kanazawa', x: 33, y: 10 });
        assert.deepStrictEqual(plain(P.arrival(config, 'Shirakawago')), { room: 'Shirakawago', x: 3, y: 10 });
        assert.deepStrictEqual(plain(P.arrival(config, 'Toyama')), { room: 'Toyama', x: 18, y: 30 });
        // Himeji (#255) by the avenue from Osaka, three cells in from the seam, on the row the first seam cell lands
        assert.deepStrictEqual(plain(P.arrival(config, 'Himeji')), { room: 'Himeji', x: 40, y: 18 });
        // ...whatever order the rooms are written in: with Toyama first in config, Shirakawa-go is still entered from Kanazawa
        const reordered = Object.assign({}, config, { rooms: Object.assign({ Toyama: config.rooms.Toyama }, config.rooms) });
        assert.deepStrictEqual(plain(P.arrival(reordered, 'Shirakawago')), { room: 'Shirakawago', x: 3, y: 10 });
        // a door between a city's own districts is not a way into it
        const sealed = Object.assign({}, config, { stations: {}, rooms: Object.assign({}, config.rooms) });
        for (const k of Object.keys(config.stations)) delete sealed.rooms[k];
        assert.ok(!config.cities.TokyoCity.rooms.some(m => {
            const to = P.arrival(sealed, 'TokyoCity');
            return to && (config.rooms[m.room].transporters || []).some(t => t.targetRoom === to.room && t.targetX === to.x && t.targetY === to.y);
        }));
        assert.deepStrictEqual(plain(P.arrival(config, 'Sendai')), { room: 'Sendai', x: 35, y: 10 });
        assert.deepStrictEqual(plain(P.arrival(config, 'TokyoCity')), { room: 'Palace', x: 27, y: 10 });
        assert.strictEqual(P.arrival(config, 'Nowhere'), null);
        // with no trains at all, by any door into it
        const noTrains = Object.assign({}, config, { stations: {} });
        assert.ok(P.arrival(noTrains, 'Sapporo').room === 'Sapporo');
        const src = fs.readFileSync(path.join(GV2, 'src', 'GameScene.js'), 'utf8');
        assert.ok(/Places\.nearest\(meta, places, ix, iy, UIScale\.MAP_CLICK_REACH \/ s\)/.test(src));
        assert.ok(/this\.roomManager\.switchRoom\(to\.room, cell\[0\], cell\[1\]\)/.test(src));
    });
};
