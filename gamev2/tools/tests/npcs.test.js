module.exports = ({ test, assert, fs, path, GV2, ctx, game, realConfig, castOn }) => {
    test('a dated state that marks an NPC absent carries no placement', () => {
        // tools/blog_to_npc.py PLACEMENT_KEYS: a leftover photo is still preloaded, leftover dialogue reads as a post
        const placementKeys = ['gridX', 'gridY', 'dialogue', 'photo', 'voice', 'drunk', 'posts'];
        const rooms = JSON.parse(fs.readFileSync(path.join(GV2, 'config.json'), 'utf8')).rooms;
        const stale = [];
        for (const [key, room] of Object.entries(rooms)) {
            for (const npc of room.npcs || []) {
                for (const [date, st] of Object.entries(npc.states || {})) {
                    if (st.present !== false) continue;
                    const left = placementKeys.filter((k) => k in st);
                    if (left.length) stale.push(`${key} ${npc.name} ${date}: ${left.join(', ')}`);
                }
            }
        }
        assert.deepStrictEqual(stale, []);
    });

    test('a wandering NPC keeps off a doorway: a transporter and the cells beside it', () => {
        const mgr = game('Object.create(NPCManager.prototype)');
        const steps = [];
        const npc = { gridX: 4, gridY: 6, isMoving: false, startMovement: (dx, dy) => steps.push(`${dx},${dy}`) };
        const room = { npcs: [npc], transporters: [{ gridX: 5, gridY: 5 }] };   // a door at 5,5: 5,6 is in front of it
        mgr.scene = { dialogueManager: { isVisible: () => false },
            roomManager: { currentRoom: 'Market', rooms: { Market: room } } };
        assert.deepStrictEqual([[5, 5], [5, 6], [4, 5], [6, 5], [5, 4], [4, 6], [6, 6], [5, 7]].map(c => mgr.atDoorway(...c)),
            [true, true, true, true, true, false, false, false]);
        const roll = (direction) => { ctx.Phaser = { Math: { Between: () => direction } }; mgr.handleWander(); };
        try {
            roll(2);   // right, onto 5,6
            assert.deepStrictEqual(steps, [], 'stepped in front of the door');
            [1, 3, 4].forEach(roll);   // left, up (4,5 is beside the door), down
            assert.deepStrictEqual(steps, ['-1,0', '0,1']);
            room.transporters = [];
            roll(2);
            assert.deepStrictEqual(steps, ['-1,0', '0,1', '1,0'], 'no door, no restriction');
        } finally {
            delete ctx.Phaser;
        }
    });

    test('base NPCs are trip-scoped: devhouse 3 stands in Sapporo then Asahikawa, and nowhere in 2025 (#131)', () => {
        const config = realConfig();
        const seven = ['Bailey', 'Damian', 'Dylan', 'Julia', 'Khoi', 'Sam', 'Xander'];
        for (const d of ['2027-02-18', '2027-02-20', '2027-02-24']) {
            assert.deepStrictEqual(castOn(config, d), seven.map(n => `Sapporo/${n}`), d);
        }
        for (const d of ['2027-02-25', '2027-02-26', '2027-02-28', '2027-03-15']) {
            assert.deepStrictEqual(castOn(config, d), seven.map(n => `Asahikawa/${n}`), d);
        }
        const days = [...game('contentChangeDates')(config)].filter(d => d < '2027').sort();
        assert.ok(days.length > 20);
        for (const d of days.concat('2025-09-01', '2026-11-25', '2027-02-03')) {
            const cast = castOn(config, d);
            assert.ok(!cast.some(c => /\/(Khoi|Sam|Xander)$/.test(c)), `${d}: ${cast}`);
            assert.ok(cast.some(c => /\/(Bailey|Damian|Dylan|Julia)$/.test(c)), `${d}: devhouse 2 is there`);
        }
        // the fortnight before devhouse 3 is its lead-in: devhouse 2 is history and nobody stands at the base yet
        for (const d of ['2027-02-04', '2027-02-10', '2027-02-17']) assert.deepStrictEqual(castOn(config, d), [], d);
        // the base lines are neutral: nobody is still waiting for a trip they are on
        const resolveNpc = game('resolveNpc'), trips = game('Trips.of')(config);
        for (const room of ['Sapporo', 'Asahikawa']) {
            for (const raw of config.rooms[room].npcs) {
                const npc = resolveNpc(raw, room === 'Sapporo' ? '2027-02-20' : '2027-02-26', trips);
                assert.ok(npc && npc.dialogue.length >= 2, `${room}/${raw.name} has lines`);
                assert.ok(!/can't wait|looking forward to devhouse/i.test(npc.dialogue.join(' ')), `${room}/${raw.name}: ${npc.dialogue}`);
            }
        }
        // James is the default player sprite, never a member; the credits are left alone
        for (const t of trips) assert.ok(!t.members.includes('james'), t.id);
        assert.ok(config.credits.includes('Audio: Gloria') && config.credits.includes('Slacker: Yashuk'));
    });

    test('a post inside a trip still moves its author, and history from another trip or stay does not apply', () => {
        const resolveNpc = game('resolveNpc');
        const trips = game('Trips.of')({ trips: [
            { id: 'a', start: '2030-01-01', end: '2030-01-10', members: ['kim'] },
            { id: 'b', start: '2031-01-01', end: '2031-01-10', members: ['kim'],
                stays: [{ from: '2031-01-01', room: 'North' }, { from: '2031-01-06', room: 'South' }] },
        ] });
        const north = { name: 'Kim', sprite: 'kim_front', gridX: 1, gridY: 1, dialogue: ['base north'], trip: 'b', stay: 'North',
            states: { '2031-01-03': { present: true, gridX: 5, gridY: 5, dialogue: ['posted'] } } };
        const south = { name: 'Kim', sprite: 'kim_front', gridX: 2, gridY: 2, dialogue: ['base south'], trip: 'b', stay: 'South',
            states: { '2031-01-03': { present: false } } };
        const old = { name: 'Kim', sprite: 'kim_front', gridX: 9, gridY: 9, dialogue: ['base a'], trip: 'a',
            states: { '2030-01-04': { gridX: 8, dialogue: ['a post'] }, '2031-01-08': { present: true, gridX: 7, dialogue: ['back at a'] } } };
        const hidden = { name: 'Kim', sprite: 'kim_front', gridX: 3, gridY: 3, dialogue: [], present: false,
            states: { '2030-01-05': { present: true, dialogue: ['a hop'] } } };
        const at = (npc, d) => { const r = resolveNpc(npc, d, trips); return r && `${r.gridX},${r.gridY} ${r.dialogue[0]}`; };
        // trip a, and the gap after it: its own base and posts
        assert.strictEqual(at(old, '2030-01-02'), '9,9 base a');
        assert.strictEqual(at(old, '2030-06-01'), '8,9 a post');
        assert.strictEqual(at(hidden, '2030-01-06'), '3,3 a hop');
        assert.strictEqual(at(north, '2030-01-06'), null);
        // trip b before the post: base in the north, nothing of trip a
        assert.strictEqual(at(north, '2031-01-02'), '1,1 base north');
        assert.strictEqual(at(south, '2031-01-02'), null);
        assert.strictEqual(at(old, '2031-01-02'), null);
        assert.strictEqual(at(hidden, '2031-01-02'), null);
        // the post moves them, until the group moves base
        assert.strictEqual(at(north, '2031-01-04'), '5,5 posted');
        assert.strictEqual(at(north, '2031-01-06'), null);
        assert.strictEqual(at(south, '2031-01-06'), '2,2 base south');
        // a post from somewhere else entirely — even another trip's room — still places them
        assert.strictEqual(at(old, '2031-01-08'), '7,9 back at a');
        // with no trips configured nothing is scoped
        assert.strictEqual(resolveNpc(old, '2031-01-02', []).gridX, 8);
        assert.strictEqual(resolveNpc(north, '2030-01-06', []).gridX, 1);
    });
};
