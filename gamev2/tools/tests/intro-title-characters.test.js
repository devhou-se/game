module.exports = ({ test, assert, fs, path, GV2, game, realConfig, require, __dirname }) => {
    test('the title and intro line-ups show the listed devhouse members that have sprites, never james', () => {
        const lineup = game('CharacterSelect.lineup'), available = game('CharacterSelect.available');
        const cfg = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8'));
        assert.deepStrictEqual(cfg.members, ['bailey', 'damian', 'dylan', 'julia', 'khoi', 'sam', 'xander']);
        assert.deepStrictEqual(Array.from(lineup(cfg)), cfg.members.slice().sort(), 'every member has a sprite set, alphabetical');
        assert.deepStrictEqual(Array.from(available(cfg)), Array.from(available(cfg)).slice().sort(), 'Menu -> Character is alphabetical, james included');
        assert.ok(Array.from(available(cfg)).includes('james'), 'james stays playable (Menu -> Character)');
        assert.strictEqual(cfg.player.sprite, 'james_front', 'james stays the default player sprite');
        // a listed name without a sprite set is skipped; an unlisted sprite set never appears
        const set = (...names) => Object.fromEntries(names.flatMap(n => ['front', 'back', 'side'].map(d => [`${n}_${d}`, {}])));
        const fake = { members: ['sam', 'gloria', 'james_front', 'bailey'], spriteMetadata: set('james', 'bailey', 'sam', 'custom') };
        assert.deepStrictEqual(Array.from(lineup(fake)), ['bailey', 'sam'], 'alphabetical whatever the list order');
        assert.deepStrictEqual(Array.from(lineup({ spriteMetadata: set('james', 'bailey') })), [], 'no list, no line-up');
        // the intro's sentence under the row names the same people as the row
        // (Intro.cast: the line-up of the game date's trip, see the trips tests)
        const cast = game('Intro.cast');
        assert.deepStrictEqual(Array.from(cast(cfg, '2027-02-20')), ['bailey', 'damian', 'dylan', 'julia', 'khoi', 'sam', 'xander']);
        assert.deepStrictEqual(Array.from(cast(cfg, '2025-11-02')), ['bailey', 'damian', 'dylan', 'julia']);
        assert.deepStrictEqual(Array.from(cast({ ...cfg, trips: undefined }, '2025-11-02')), Array.from(lineup(cfg)), 'no trips: config.members');
        assert.ok(/friends: Bailey, Damian, Dylan and Julia\.$/.test(game('Intro.welcomeCopy')(cfg, '2025-11-02', '2026-11-25')[0]));
        for (const f of ['TitleScreen.js', 'Intro.js']) {
            const src = fs.readFileSync(path.join(GV2, 'src', f), 'utf8');
            assert.ok(src.includes('CharacterSelect.lineup('), `${f} draws CharacterSelect.lineup()`);
        }
    });

    test('creator donor sprites have no see-through holes, and every clothing colour is in their palette', () => {
        const png = require('./png');
        const donors = JSON.parse(game('JSON.stringify(CharacterCreator.DONORS)'));
        const cuts = JSON.parse(game('JSON.stringify(CharacterCreator.CUTS)'));
        const hex = (d, i) => '#' + [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
        const bad = [];
        for (const [name, def] of Object.entries(donors)) {
            for (const [dir, cut] of Object.entries(cuts)) {
                cut.top.forEach((topStart, frame) => {
                    const file = `${name}_${dir}_frame_${frame}`;
                    const { width: W, height: H, data } = png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', file + '.png')));
                    // flood the transparent background in from the border: what is left is a hole
                    const outside = new Uint8Array(W * H), stack = [];
                    for (let x = 0; x < W; x++) stack.push(x, (H - 1) * W + x);
                    for (let y = 0; y < H; y++) stack.push(y * W, y * W + W - 1);
                    while (stack.length) {
                        const p = stack.pop();
                        if (outside[p] || data[p * 4 + 3] !== 0) continue;
                        outside[p] = 1;
                        const x = p % W;
                        if (x > 0) stack.push(p - 1);
                        if (x < W - 1) stack.push(p + 1);
                        if (p >= W) stack.push(p - W);
                        if (p < W * (H - 1)) stack.push(p + W);
                    }
                    let holes = 0;
                    const stray = new Set();
                    for (let p = 0; p < W * H; p++) {
                        if (data[p * 4 + 3] === 0) { if (!outside[p]) holes++; continue; }
                        const y = (p - p % W) / W, c = hex(data, p * 4);
                        // the torso band holds only outline, skin, hair and the donor's top/legs colours
                        if (y >= topStart && y < cut.bottom[frame] && c !== '#000000'
                            && !['skin', 'hair', 'top', 'legs'].some((slot) => def[slot].includes(c))) stray.add(c);
                    }
                    if (holes) bad.push(`${file}: ${holes} transparent pixel(s) inside the sprite`);
                    if (stray.size) bad.push(`${file}: torso colour(s) ${[...stray].join(' ')} not in DONORS.${name}`);
                });
            }
        }
        assert.deepStrictEqual(bad, []);
    });

    test('the creator composes a mixed-donor character without holes, ticks or a flickering moustache (#128)', () => {
        const png = require('./png');
        const frames = { front: 4, back: 4, side: 2 };
        const load = (name, dir, f) => png.decode(fs.readFileSync(path.join(GV2, 'assets', 'sprites', `${name}_${dir}_frame_${f}.png`)));
        const compose = (look, dir, f) => {
            const src = {};
            for (const part of ['hair', 'top', 'legs', 'beard']) if (look.parts[part]) src[part] = load(look.parts[part], dir, f);
            return game('CharacterCreator.composePixels')(src, look, dir, f);
        };
        const at = (img, x, y) => Array.from(img.data.subarray((y * img.width + x) * 4, (y * img.width + x) * 4 + 4));
        // same picture: same alpha everywhere, same colour wherever something is drawn
        const same = (a, b) => {
            for (let i = 0; i < a.data.length; i += 4) {
                if (a.data[i + 3] !== b.data[i + 3]) return false;
                if (a.data[i + 3] && (a.data[i] !== b.data[i] || a.data[i + 1] !== b.data[i + 1] || a.data[i + 2] !== b.data[i + 2])) return false;
            }
            return true;
        };
        const look = (hair, top, legs, colors) => ({ parts: { hair, top, legs, beard: null },
            colors: Object.assign({ skin: '#f6c39a', hair: '#3c2e20', top: '#3a6fd8', legs: '#2b2b33', beard: null }, colors) });

        // one donor for every part, nothing recoloured: the composite IS the donor sprite (the tidy rules touch nothing)
        for (const name of game('Object.keys(CharacterCreator.DONORS)')) {
            const own = { parts: { hair: name, top: name, legs: name, beard: null }, colors: {} };
            for (const [dir, n] of Object.entries(frames)) {
                for (let f = 0; f < n; f++) {
                    assert.ok(same(compose(own, dir, f), load(name, dir, f)), `${name}_${dir}_${f} composed from itself changed`);
                }
            }
        }

        // 1. damian's top over someone else's legs: his own trouser pixels in the torso band are filled, not holes
        const cuts = JSON.parse(game('JSON.stringify(CharacterCreator.CUTS)'));
        for (const [dir, n] of Object.entries(frames)) {
            for (let f = 0; f < n; f++) {
                const out = compose(look('james', 'damian', 'bailey'), dir, f), top = load('damian', dir, f);
                for (let y = cuts[dir].top[f]; y < cuts[dir].bottom[f]; y++) {
                    for (let x = 0; x < out.width; x++) {
                        if (at(top, x, y)[3]) assert.ok(at(out, x, y)[3], `hole at ${x},${y} of ${dir} frame ${f}`);
                    }
                }
            }
        }
        // 2. james's head on another top, side frame 1: the outline of his own high sleeve is gone
        const side = compose(look('james', 'bailey', 'bailey'), 'side', 1);
        const wearsIt = load('bailey', 'side', 1);
        for (let y = 32; y < 36; y++) {
            for (let x = 16; x < 20; x++) assert.ok(!at(side, x, y)[3] || at(wearsIt, x, y)[3], `stray sleeve outline at ${x},${y}`);
        }
        // 3. dylan's head with dyed hair: the inside of his open mouth keeps its colour in every frame
        const dark = [0x1c, 0x15, 0x0e, 255];
        let mouths = 0;
        for (const [dir, f] of [['front', 1], ['front', 3], ['side', 0], ['side', 1]]) {
            const out = compose(look('dylan', 'dylan', 'dylan', { hair: '#ff7eb6' }), dir, f), own = load('dylan', dir, f);
            for (let p = 0; p < out.width * out.height; p++) {
                const x = p % out.width, y = (p - x) / out.width;
                if (at(own, x, y).join() !== '229,59,68,255') continue;      // a mouth pixel
                for (const [nx, ny] of [[x - 2, y], [x + 2, y], [x, y - 2], [x, y + 2]]) {
                    if (at(own, nx, ny).join() === dark.join()) { mouths++; assert.deepStrictEqual(at(out, nx, ny), dark, `${dir} ${f}: mouth interior at ${nx},${ny} dyed`); }
                }
            }
        }
        assert.ok(mouths > 0, 'dylan has no open-mouth pixels to check');
        // 4. the shoulder line is closed: an outline pixel the top donor draws right above its own shirt is there,
        //    however narrow the head donor's shoulders are
        const donors = JSON.parse(game('JSON.stringify(CharacterCreator.DONORS)'));
        const hex = (px) => '#' + px.slice(0, 3).map((v) => v.toString(16).padStart(2, '0')).join('');
        let closed = 0;
        for (const hair of Object.keys(donors)) {
            for (const top of Object.keys(donors).filter((t) => t !== hair)) {
                for (const [dir, n] of Object.entries(frames)) {
                    for (let f = 0; f < n; f++) {
                        const out = compose(look(hair, top, top), dir, f), t = load(top, dir, f), h = load(hair, dir, f);
                        for (let y = cuts[dir].top[f] - 2; y < cuts[dir].top[f]; y++) {
                            for (let x = 0; x < out.width; x++) {
                                if (hex(at(t, x, y)) !== '#000000' || !at(t, x, y)[3] || !donors[top].top.includes(hex(at(t, x, y + 2)))) continue;
                                assert.ok(at(out, x, y)[3], `${hair} head / ${top} top ${dir} ${f}: open shoulder line at ${x},${y}`);
                                if (hex(at(h, x, y)) !== '#000000') closed++;      // not simply the head donor's own outline
                            }
                        }
                    }
                }
            }
        }
        assert.ok(closed > 0, 'no donor pair has shoulders of different widths: the check tests nothing');
        // 5. julia's top on another head (#160): her long hair is not worn with it. Side view: the strand of outline
        //    behind the shoulder is gone. Back view: no see-through hole where the hair was, and the hair's lower
        //    outline is shirt, not a dark band — and no mixed composite at all has a hole.
        assert.strictEqual(at(compose(look('james', 'julia', 'julia'), 'side', 0), 14, 36)[3], 0, 'stray strand outline behind the shoulder (side 0)');
        assert.strictEqual(at(compose(look('dylan', 'julia', 'julia'), 'side', 1), 14, 36)[3], 0, 'stray strand outline behind the shoulder (side 1)');
        const shirt = Array.from(game('CharacterCreator.hslToRgb')(...Object.values(game('CharacterCreator.rgbToHsl')(0x3a, 0x6f, 0xd8)))).concat(255);
        const back = compose(look('james', 'julia', 'julia'), 'back', 0);
        for (let x = 22; x < 40; x++) {
            for (const y of [36, 38]) assert.deepStrictEqual(at(back, x, y), shirt, `back of julia's top at ${x},${y} is not shirt`);
        }
        const holed = [];
        for (const hair of Object.keys(donors)) {
            for (const top of Object.keys(donors)) {
                for (const [dir, n] of Object.entries(frames)) {
                    for (let f = 0; f < n; f++) {
                        const { width: W, height: H, data } = compose(look(hair, top, top), dir, f);
                        // flood the transparent background in from the border: what is left is a hole
                        const outside = new Uint8Array(W * H), stack = [];
                        for (let x = 0; x < W; x++) stack.push(x, (H - 1) * W + x);
                        for (let y = 0; y < H; y++) stack.push(y * W, y * W + W - 1);
                        while (stack.length) {
                            const p = stack.pop();
                            if (outside[p] || data[p * 4 + 3] !== 0) continue;
                            outside[p] = 1;
                            const x = p % W;
                            if (x > 0) stack.push(p - 1);
                            if (x < W - 1) stack.push(p + 1);
                            if (p >= W) stack.push(p - W);
                            if (p < W * (H - 1)) stack.push(p + W);
                        }
                        if (outside.some((o, p) => !o && data[p * 4 + 3] === 0)) holed.push(`${hair} head / ${top} top ${dir} ${f}`);
                    }
                }
            }
        }
        assert.deepStrictEqual(holed, [], 'see-through hole inside a composed character');

        // tools/generate_cast.py is a port of the same compose: the frames it baked are what the creator draws
        const py = fs.readFileSync(path.join(__dirname, 'generate_cast.py'), 'utf8');
        const looks = JSON.parse(py.match(/^LOOKS = (\{[\s\S]*?\n\})\n/m)[1].replace(/'/g, '"').replace(/\bNone\b/g, 'null').replace(/,(\s*[}\]])/g, '$1'));
        assert.ok(Object.keys(looks).length > 0);
        for (const [name, l] of Object.entries(looks)) {
            for (const [dir, n] of Object.entries(frames)) {
                for (let f = 0; f < n; f++) {
                    assert.ok(same(compose(l, dir, f), load(name, dir, f)), `${name}_${dir}_frame_${f}.png is not what the creator composes for that look`);
                }
            }
        }
    });

    test('the intro names the trip members and says where they are today (#130)', () => {
        const config = realConfig(), T = game('Trips'), trips = T.of(config);
        assert.strictEqual(T.list(T.memberNames(T.forDate(trips, '2027-02-20'))), 'Bailey, Damian, Dylan, Julia, Khoi, Sam and Xander');
        assert.strictEqual(T.list(T.memberNames(T.forDate(trips, '2025-11-02'))), 'Bailey, Damian, Dylan and Julia');
        const where = (date, here, played) => T.whereText(T.membersByRoom(config, date, { played }), here);
        assert.strictEqual(where('2027-02-20', 'Sapporo'), 'Today everyone is here in Sapporo.');
        assert.strictEqual(where('2027-02-26', 'Asahikawa', 'bailey'), 'Today everyone is here in Asahikawa.');
        assert.strictEqual(where('2027-02-26', 'Tokyo'), 'Today they are in Asahikawa.');
        const g = (room, name, ...people) => ({ room, name, members: people.map(n => ({ name: n })) });
        assert.strictEqual(T.whereText([], 'Tokyo'), 'They are out and about.');
        assert.strictEqual(T.whereText([g('Market', 'Asakusa', 'Damian', 'Bailey')], 'Market'), 'Today Bailey and Damian are here in Asakusa.');
        assert.strictEqual(T.whereText([g('Market', 'Asakusa', 'Bailey'), g('Osaka', 'Osaka', 'Dylan')], 'Market'),
            'Today Bailey is here in Asakusa, and Dylan is in Osaka.');
        assert.strictEqual(T.whereText([g('Market', 'Asakusa', 'Bailey'), g('Osaka', 'Osaka', 'Dylan'), g('TokyoStation', 'Tokyo Station', 'Julia')], 'Market'),
            'Today Bailey is here in Asakusa, and the others are in Osaka and Tokyo Station.');
        assert.strictEqual(T.whereText([g('A', 'A', 'x'), g('B', 'B', 'y'), g('C', 'C', 'z'), g('D', 'D', 'w')], 'Tokyo'), 'Today they are in A, B and C.');
        const copy = game('Intro.tripCopy');
        assert.ok(/on devhouse 3 right now, in Hokkaido/.test(copy(trips[1], true, false)[0]));
        assert.ok(/once they start writing/.test(copy(trips[1], true, false)[1]));
        assert.ok(/This is devhouse 2, their trip to Japan/.test(copy(trips[0], false, true)[0]));
        assert.ok(/come from the blog posts/.test(copy(trips[0], false, true)[1]));
        // the whole page, as the game words it
        const welcome = game('Intro.welcomeCopy');
        const live = welcome(config, '2027-02-20', '2027-02-20');
        assert.strictEqual(live[0], 'devhouse is a group of friends: Bailey, Damian, Dylan, Julia, Khoi, Sam and Xander.');
        assert.ok(/on devhouse 3 right now, in Hokkaido/.test(live[1]) && /once they start writing/.test(live[2]), live);
        assert.ok(!/James|Gloria|Yashuk/.test(live.join(' ')));
        const past = welcome(config, '2025-11-11', '2026-11-25');
        assert.strictEqual(past[0], 'devhouse is a group of friends: Bailey, Damian, Dylan and Julia.');
        assert.ok(/This is devhouse 2, their trip to Japan/.test(past[1]) && /come from the blog posts/.test(past[2]), past);
        assert.ok(/another day or another trip/.test(past[3]));
        // looking ahead at devhouse 3 from today is not "right now"
        assert.ok(/This is devhouse 3, their trip to Hokkaido/.test(welcome(config, '2027-02-20', '2026-11-25')[1]));
        // the cast row draws the same people
        const lineup = game('CharacterSelect.lineup');
        assert.deepStrictEqual(Array.from(lineup(config, trips[0].members)), ['bailey', 'damian', 'dylan', 'julia']);
        assert.strictEqual(lineup(config).length, 7);
    });
};
