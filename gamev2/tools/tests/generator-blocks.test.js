// The generators' shared building blocks (issue #224): the primitives on roomgen.Builder, the host-door
// helpers in tools/roomgen.py and the interior shell in tools/interiors.py.
module.exports = ({ test, assert, fs, path, GV2 }) => {
    const { spawnSync } = require('child_process');
    const tool = (f) => fs.readFileSync(path.join(GV2, 'tools', f), 'utf8');
    // Run a Python snippet from gamev2/ with tools/ on the path, as a generator runs. It reads the config and
    // never saves it; whatever it leaves in `out` comes back. The timeout is for a block that hangs.
    const HEAD = ['import json, sys', 'import roomgen as rg', 'import interiors', 'from interiors import Interior, outline',
        'cfg = rg.load_config()', 'out = {}',
        'name = lambda b, layer: {xy: rg._pal[i] for xy, i in b.L[layer].items()}', ''].join('\n');
    const TAIL = '\nprint("\\n" + json.dumps(out))\n';
    const python = (snippet) => {
        const run = spawnSync('python3', ['-c', HEAD + snippet + TAIL], { cwd: GV2, encoding: 'utf8', maxBuffer: 1 << 26, timeout: 60000,
            env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: path.join(GV2, 'tools') } });
        assert.ok(!run.error, `python3 did not finish: ${run.error}`);
        assert.strictEqual(run.status, 0, run.stderr);
        return JSON.parse(run.stdout.trim().split('\n').pop());
    };
    const cells = (list) => list.map(([x, y]) => `${x},${y}`).sort();
    const rect = (x, y, w, h) => Array.from({ length: w * h }, (_, i) => [x + (i % w), y + Math.floor(i / w)]);

    test('Builder.solid, place, prop, stand and railing_row lay exactly their sprite and their collider cells', () => {
        const out = python([
            'b = rg.Builder(20, 15)',
            'b.solid(1, 1)',                                                    // one cell, as it always was
            'b.solid(3, 1, 2, 3)',                                              // a rect
            "b.place('Other', 6, 1, 'office-plant-a_0_0', rg.block(2, 3, 1))",  // offsets: rows 1 and 2 of a 2x3
            "b.prop('office-counter2_0_0', 9, 1, 2, 1)",
            "b.prop('office-plant-b_0_0', 12, 1, layer='Tops')",
            "b.stand('station-pillar_0_0', 14, 5)",                             // two rows tall, its foot on row 5
            "b.stand('office-shelf-glass_0_0', 16, 6, w=2, h=3, layer='Other')",
            'b.railing_row(10, {0: 1, 4: 1, 5: 1, 19: 1})',
            "out = {n: name(b, n) for n in ('Colliders', 'Collidables', 'Other', 'Tops')}",
            "out['block'] = rg.block(2, 2)",
            "out['cells'] = [rg.sprite_cells('office-counter2_0_0'), rg.png_size('office-counter2_0_0')]",
        ].join('\n'));
        const railing = rect(1, 10, 3, 1).concat(rect(6, 10, 13, 1));
        assert.deepStrictEqual(Object.keys(out.Colliders).sort(), cells([[1, 1], ...rect(3, 1, 2, 3), ...rect(6, 2, 2, 2), ...rect(9, 1, 2, 1),
            [12, 1], [14, 5], [16, 6], [17, 6], ...railing]));
        assert.ok(Object.values(out.Colliders).every((k) => k === 'gk_blank'));
        const pieces = { '1,10': 'post', '2,10': 'mid', '3,10': 'end', '18,10': 'end' };       // every run ends in an end
        for (let x = 6; x < 18; x++) pieces[`${x},10`] = x % 2 === 0 ? 'post' : 'mid';
        const want = { '9,1': 'office-counter2_0_0', '14,4': 'station-pillar_0_0' };
        for (const [xy, piece] of Object.entries(pieces)) want[xy] = `station-railing-${piece}_0_0`;
        assert.deepStrictEqual(out.Collidables, want);
        assert.deepStrictEqual(out.Other, { '6,1': 'office-plant-a_0_0', '16,4': 'office-shelf-glass_0_0' });
        assert.deepStrictEqual(out.Tops, { '12,1': 'office-plant-b_0_0' });
        assert.deepStrictEqual(out.block, [[0, 0], [0, 1], [1, 0], [1, 1]]);
        assert.deepStrictEqual(out.cells, [[2, 1], [128, 64]]);
    });

    test('rg.pin replaces on the cell in place, rg.open_door opens a door once and for all, rg.shut_door drops only its own kind', () => {
        const out = python([
            "T = lambda x, y, room: rg.transporter(x, y, room, 0, 0)",
            "ts = [T(1, 1, 'A'), T(2, 2, 'B'), T(1, 1, 'C'), T(3, 3, 'D'), T(1, 1, 'E')]",
            "new = T(1, 1, 'Z')",
            "out['same'] = rg.pin(ts, new) is new",
            "out['replaced'] = [t['targetRoom'] for t in ts]",
            "rg.pin(ts, T(9, 9, 'Y'))",
            "out['appended'] = [t['targetRoom'] for t in ts]",
            "rg.pin(ts, T(9, 9, 'Y')); rg.pin(ts, T(1, 1, 'Z'))",
            "out['again'] = [t['targetRoom'] for t in ts]",
            // a host with a sealed doorway and no transporters at all
            "host = {'layers': [{'name': 'Floor', 'tiles': {'4,4': 0}}, {'name': 'Colliders', 'tiles': {'4,4': 0, '5,4': 0}}]}",
            "door = rg.open_door(host, (4, 4), 'TeaRoomMarket1', (9, 8))",
            "out['door'] = door",
            "out['open'] = json.loads(json.dumps(host))",
            "rg.open_door(host, (4, 4), 'TeaRoomMarket1', (9, 8))",
            "out['twice'] = json.loads(json.dumps(host))",
            "rg.shut_door(host, (4, 4), 'Other')",                             // another kind's door on the cell: sealed, kept
            "out['others'] = [sorted(host['layers'][1]['tiles']), len(host['transporters'])]",
            "rg.shut_door(host, (4, 4), 'TeaRoom')",
            "out['shut'] = [sorted(host['layers'][1]['tiles']), host['transporters'], sorted(host['layers'][0]['tiles'])]",
            "out['blank'] = rg._pal[host['layers'][1]['tiles']['4,4']]",
        ].join('\n'));
        assert.strictEqual(out.same, true);
        assert.deepStrictEqual(out.replaced, ['Z', 'B', 'D'], 'in place, the later ones on the cell gone');
        assert.deepStrictEqual(out.appended, ['Z', 'B', 'D', 'Y']);
        assert.deepStrictEqual(out.again, out.appended, 'a second run changes nothing');
        assert.deepStrictEqual(out.door, { gridX: 4, gridY: 4, targetRoom: 'TeaRoomMarket1', targetX: 9, targetY: 8, hidden: true });
        assert.deepStrictEqual(out.open.layers[1].tiles, { '5,4': 0 }, 'only the doorway is unsealed');
        assert.deepStrictEqual(out.open.transporters, [out.door]);
        assert.deepStrictEqual(out.twice, out.open);
        assert.deepStrictEqual(out.others, [['4,4', '5,4'], 1]);
        assert.deepStrictEqual(out.shut, [['4,4', '5,4'], [], ['4,4']]);
        assert.strictEqual(out.blank, 'gk_blank');
    });

    test('the worked example in docs/generators-and-checks.md builds: a tea room on the Interior shell, wired to its door', () => {
        // the doc's own block, run as it is but for the save
        const doc = fs.readFileSync(path.join(GV2, 'docs', 'generators-and-checks.md'), 'utf8');
        const blocks = [...doc.matchAll(/```python\n([\s\S]*?)```/g)].map((m) => m[1]).filter((b) => b.includes('TeaRoomMarket1'));
        assert.strictEqual(blocks.length, 1, 'the worked example');
        assert.strictEqual(blocks[0].split('rg.save_config(cfg)').length, 2, 'the example ends by saving');
        const out = python(blocks[0].replace('rg.save_config(cfg)', [
            "out = {'room': cfg['rooms'][KEY], 'inside': inside, 'at': [it.ox, it.oy], 'pal': cfg['tilePalette'],",
            "       'door': [t for t in cfg['rooms'][HOST]['transporters'] if (t['gridX'], t['gridY']) == DOOR],",
            "       'sealed': f'{DOOR[0]},{DOOR[1]}' in cfg['rooms'][HOST]['layers'][-1]['tiles'], 'reached': len(it.reached)}",
        ].join('\n')));
        const room = out.room, tiles = (layer) => room.layers.find((l) => l.name === layer).tiles;
        assert.deepStrictEqual([room.name, room.worldWidth / 64, room.worldHeight / 64, out.at], ['Tea Room', 20, 15, [5, 3]]);
        // the floor and its two mat cells: eight corners, clockwise from the top-left
        assert.deepStrictEqual(room.boundary, [[5, 3], [15, 3], [15, 9], [11, 9], [11, 10], [9, 10], [9, 9], [5, 9]]);
        const exit = (x) => ({ gridX: x, gridY: 9, targetRoom: 'Market', targetX: 7, targetY: 38, hidden: true });
        assert.deepStrictEqual(room.transporters, [exit(9), exit(10)], 'two hidden exits, west to east');
        assert.deepStrictEqual(out.inside, [[9, 8], [10, 8]]);
        assert.strictEqual(room.interior, true);
        assert.strictEqual(room.shopEnabled, false);
        assert.deepStrictEqual(room.tearoom, { host: 'Market', door: [7, 37] });
        assert.deepStrictEqual([room.npcs, room.objects], [[], []]);
        assert.ok(!('lanternLight' in room) && !('shopMenu' in room), 'room() sets no flag it was not given');
        // void everywhere, the floor laid, the mat drawn; the wall and the counter solid, nothing else
        const key = (layer, xy) => out.pal[tiles(layer)[xy]];
        assert.strictEqual(Object.keys(tiles('Floor')).length, 20 * 15);
        assert.deepStrictEqual([key('Floor', '0,0'), key('Floor', '5,3'), key('Floor', '14,8'), key('Floor', '9,9'), key('Floor', '8,9')],
            ['office-void-autotile_center', 'office-warm-autotile_center', 'office-warm-autotile_center', 'office-warm-autotile_center',
                'office-void-autotile_center']);
        assert.deepStrictEqual(Object.keys(tiles('Colliders')).sort(), cells([...rect(5, 2, 10, 1), [11, 3], [12, 3]]));
        assert.strictEqual(key('Collidables', '11,3'), 'office-counter2_0_0');
        assert.strictEqual(out.reached, 10 * 6 - 2 + 2);
        // the host's door: the transporter already on the cell (the Izakaya's) is replaced where it sits
        assert.deepStrictEqual(out.door, [{ gridX: 7, gridY: 37, targetRoom: 'TeaRoomMarket1', targetX: 9, targetY: 8, hidden: true }]);
        assert.strictEqual(out.sealed, false);
    });

    test('an Interior centres a small floor, keeps its exits in doorway order, and fails on a floor cell nobody can reach', () => {
        const out = python([
            'it = Interior(4, 3)',
            "out['small'] = [it.b.W, it.b.H, it.ox, it.oy, it.cell(0, 0), it.cell(3, 2)]",
            'big = Interior(24, 15, 1, 4)',                                     // a hall as its generator places it
            "out['big'] = [big.b.W, big.b.H, big.ox, big.oy]",
            'held = Interior(8, 5, ox=6, oy=5, w=27, h=19)',
            "out['held'] = [held.b.W, held.b.H, held.cell(0, 0)]",
            // a door in the south wall, then a pair in the north wall, each cell leaving for its own
            'it = Interior(10, 6)',
            "south = it.doorway(8, 'Market', (1, 1), n=1)",
            "north = it.doorway(0, 'Park', [(2, 2), (3, 3)], fy=-1, inward=1)",
            "room = it.room('Order')",
            "out['order'] = [[t['gridX'], t['gridY'], t['targetRoom'], t['targetX'], t['targetY'], t['hidden']] for t in room['transporters']]",
            "out['inside'] = [south, north]",
            "out['boundary'] = room['boundary']",
            "out['flags'] = sorted(k for k in room if k not in ('name', 'layers', 'npcs', 'objects', 'transporters', 'boundary', 'worldWidth', 'worldHeight'))",
            // the Builder's calls, in floor coordinates
            'it = Interior(10, 6)',
            "it.put('Over Floor', 1, 1, 'office-plant-a_0_0'); it.solid(2, 2, 2, 1)",
            "it.place('Other', 4, 0, 'office-plant-a_0_0', [(0, 1)]); it.stand('station-pillar_0_0', 6, 3)",
            "it.side_walls('office-warm-autotile_center', 'office-floor-autotile_center', 2)",
            "it.front_wall('office-floor-autotile_center', (4, 5), ('office-warm-autotile_center', 'office-warm-autotile_center'))",
            "out['calls'] = {n: name(it.b, n) for n in ('Over Floor', 'Other', 'Collidables', 'Colliders')}",
            "out['walls'] = {xy: k for xy, k in name(it.b, 'Floor').items() if not k.startswith('office-void')}",
            // a floor cell boxed in by two colliders
            'def boxed(**kw):',
            '    it = Interior(10, 6)',
            '    it.solid(1, 0); it.solid(0, 1)',
            "    it.doorway(4, 'Market', (1, 1))",
            '    try:',
            "        it.room('Boxed', **kw)",
            '        return len(it.reached)',
            '    except AssertionError as e:',
            '        return str(e)',
            "out['boxed'] = [boxed(), boxed(pockets=[(0, 0)])]",
            'try:',
            "    Interior(10, 6).room('No way out')",
            "    out['doorless'] = 'built'",
            'except AssertionError as e:',
            "    out['doorless'] = str(e)",
        ].join('\n'));
        assert.deepStrictEqual(out.small, [20, 15, 8, 3, [8, 3], [11, 5]], 'never under the camera\'s 20x15, the floor in the middle');
        assert.deepStrictEqual(out.big, [26, 22, 1, 4]);
        assert.deepStrictEqual(out.held, [27, 19, [6, 5]]);
        assert.deepStrictEqual(out.order, [[13, 9, 'Market', 1, 1, true], [5, 2, 'Park', 2, 2, true], [6, 2, 'Park', 3, 3, true]],
            'the order doorway was called in, not west to east');
        assert.deepStrictEqual(out.inside, [[[13, 8]], [[5, 3], [6, 3]]], 'a south door arrives a row up, a north door a row down');
        assert.deepStrictEqual(out.boundary, [[5, 2], [7, 2], [7, 3], [15, 3], [15, 9], [14, 9], [14, 10], [13, 10], [13, 9], [5, 9]]);
        assert.deepStrictEqual(out.flags, ['interior']);
        assert.deepStrictEqual(out.calls, {
            'Over Floor': { '6,4': 'office-plant-a_0_0' },
            Other: { '9,3': 'office-plant-a_0_0' },
            Collidables: { '11,5': 'station-pillar_0_0' },
            Colliders: { '7,5': 'gk_blank', '8,5': 'gk_blank', '9,4': 'gk_blank', '11,6': 'gk_blank' },
        });
        const walls = {};
        for (let y = 1; y < 9; y++) { walls[`4,${y}`] = 'office-warm-autotile_center'; walls[`15,${y}`] = 'office-floor-autotile_center'; }
        for (let x = 5; x < 15; x++) walls[`${x},9`] = x === 9 || x === 10 ? 'office-warm-autotile_center' : 'office-floor-autotile_center';
        assert.deepStrictEqual(out.walls, walls);
        assert.ok(/Boxed: floor nobody can reach: \[\(5, 3\)\]/.test(out.boxed[0]), out.boxed[0]);
        assert.strictEqual(out.boxed[1], 10 * 6 - 3 + 2, 'a pocket is named in floor coordinates');
        assert.ok(/no doorway/.test(out.doorless), out.doorless);
    });

    test('an Interior lays its wall tops over the void, draws a mat cell by cell, and takes its back wall into the boundary when asked', () => {
        const out = python([
            'it = Interior(10, 6)',
            "it.side_walls('office-plant-a_0_0', 'office-plant-b_0_0', 2, layer='Over Floor')",
            // a mat two cells wide is one sprite: one threshold for a gap of two
            "it.front_wall('office-plant-a_0_0', (4, 5), ('office-plant-b_0_0',), layer='Over Floor')",
            "it.back_wall([(0, 'office-wall-white_0_0', 4), (4, 'office-wall-white_0_0', 6)], 2, view=True)",
            "tone = lambda fx, fy: 'office-warm-autotile_center' if (fx + fy) % 2 else 'office-floor-autotile_center'",
            "inside = it.doorway(4, 'Market', (1, 1), mat=tone)",
            "room = it.room('Framed')",
            "out['over'] = name(it.b, 'Over Floor')",
            "out['floor'] = {xy: k for xy, k in name(it.b, 'Floor').items() if not k.startswith('office-void')}",
            "out['framed'] = [room['boundary'], sorted(it.view), len(it.reached), inside]",
            // the same wall, not asked for: the boundary is the floor and the mat, as every other interior's
            'it = Interior(10, 6)',
            "it.back_wall([(fx, 'office-wall-white_0_0', 1) for fx in range(10)], 2)",
            "it.doorway(4, 'Market', (1, 1))",
            "out['plain'] = [it.room('Plain')['boundary'], len(it.view)]",
            // a cell in the view with no collider: only the boundary would have kept you off it
            'it = Interior(10, 6)',
            "it.doorway(4, 'Market', (1, 1))",
            'it.view.add(it.cell(0, -1))',
            'try:',
            "    it.room('Open')",
            "    out['open'] = 'built'",
            'except AssertionError as e:',
            "    out['open'] = str(e)",
        ].join('\n'));
        const over = { '9,9': 'office-plant-b_0_0' };
        for (let y = 1; y < 9; y++) { over[`4,${y}`] = 'office-plant-a_0_0'; over[`15,${y}`] = 'office-plant-b_0_0'; }
        for (let x = 5; x < 15; x++) if (x !== 9 && x !== 10) over[`${x},9`] = 'office-plant-a_0_0';
        assert.deepStrictEqual(out.over, over, 'the wall tops and the one threshold, on Over Floor');
        assert.deepStrictEqual(out.floor, { '9,9': 'office-floor-autotile_center', '10,9': 'office-warm-autotile_center' },
            'the void is left under the wall tops; each mat cell is what key_of says of it');
        const [boundary, view, reached, inside] = out.framed;
        assert.deepStrictEqual(boundary, [[5, 1], [15, 1], [15, 9], [11, 9], [11, 10], [9, 10], [9, 9], [5, 9]], 'the two wall rows are inside');
        assert.deepStrictEqual(cells(view), cells(rect(5, 1, 10, 2)));
        assert.strictEqual(reached, 10 * 6 + 2, 'the wall is in the boundary, not in the walk');
        assert.deepStrictEqual(inside, [[9, 8], [10, 8]]);
        assert.deepStrictEqual(out.plain, [[[5, 3], [15, 3], [15, 9], [11, 9], [11, 10], [9, 10], [9, 9], [5, 9]], 0]);
        assert.ok(/Open: in the boundary, not floor and not solid: \[\(5, 2\)\]/.test(out.open), out.open);
    });

    test('interiors.outline walks made-up floors clockwise from their first corner, and raises on one that is not one piece', () => {
        const out = python([
            'box = lambda x0, y0, w, h: [(x0 + x, y0 + y) for x in range(w) for y in range(h)]',
            'def tried(cells):',
            '    try:',
            '        return outline(cells)',
            '    except AssertionError as e:',
            '        return str(e)',
            "out['mat'] = tried(box(0, 0, 3, 2) + [(1, 2)])",                               // a floor and its mat
            "out['cross'] = tried(box(0, 2, 6, 2) + box(2, 0, 2, 2) + box(2, 4, 2, 2))",    // the arcade
            "out['two'] = tried(box(0, 0, 6, 2) + box(0, 2, 2, 1) + box(4, 2, 2, 1))",      // mats on two edges: the palace
            "out['offset'] = tried(set(box(5, 3, 2, 2)))",
            "out['hole'] = tried([c for c in box(0, 0, 3, 3) if c != (1, 1)])",
            "out['pieces'] = tried(box(0, 0, 2, 2) + box(4, 0, 2, 2))",
            "out['corner'] = [tried([(0, 0), (1, 1)]), tried([(1, 1), (0, 0)]), tried([(1, 0), (0, 1)]), tried([(0, 1), (1, 0)])]",
            "out['none'] = tried([])",
            "out['reach'] = sorted(interiors.reachable({(0, 0), (1, 0), (3, 0)}, [(0, 0)]))",
            "out['seed'] = [interiors.seed_of('Market:(7, 37)'), interiors.named(cfg, 'Tea Room', 'Sapporo'), interiors.named(cfg, 'Tea Room', 'Sapporo', 2)]",
        ].join('\n'));
        assert.deepStrictEqual(out.mat, [[0, 0], [3, 0], [3, 2], [2, 2], [2, 3], [1, 3], [1, 2], [0, 2]]);
        assert.deepStrictEqual(out.cross, [[0, 2], [2, 2], [2, 0], [4, 0], [4, 2], [6, 2], [6, 4], [4, 4], [4, 6], [2, 6], [2, 4], [0, 4]]);
        assert.deepStrictEqual(out.two, [[0, 0], [6, 0], [6, 3], [4, 3], [4, 2], [2, 2], [2, 3], [0, 3]]);
        assert.deepStrictEqual(out.offset, [[5, 3], [7, 3], [7, 5], [5, 5]]);
        // each of these used to hang, or would have drawn a boundary round part of the floor
        for (const got of [out.hole, out.pieces, ...out.corner]) assert.strictEqual(got, 'the floor is not one piece');
        assert.strictEqual(out.none, 'no floor');
        assert.deepStrictEqual(out.reach, [[0, 0], [1, 0]]);
        const md5 = require('crypto').createHash('md5').update('Market:(7, 37)').digest('hex');
        assert.deepStrictEqual(out.seed, [parseInt(md5.slice(0, 8), 16), 'Tea Room · Sapporo', 'Tea Room · Sapporo 2']);
    });

    // Every room generator check_generators.py runs is on the shared blocks: a new one is held to this by being listed there.
    test('no room generator carries its own copy of a shared block', () => {
        const checks = tool('check_generators.py');
        const listed = [...checks.matchAll(/^GENERATORS (?:\+)?= \[([^\]]*)\]/gm)].flatMap((m) => m[1].match(/'\w+'/g) || [])
            .map((q) => q.slice(1, -1));
        assert.ok(listed.length >= 20 && listed.includes('generate_temple') && listed.includes('districts'), `GENERATORS read as ${listed}`);
        // a door wired by hand, a PNG header read, a boundary drawn, a sprite stood, a void filled
        const banned = ['ts[at[0]] = ', 'def png_size', 'struct.unpack', 'def outline', 'def stand(', "fill('office-void-autotile')"];
        for (const name of [...listed, 'hokuriku', 'chikagai']) {
            const text = tool(name + '.py');
            for (const copy of banned) assert.ok(!text.includes(copy), `${name}.py has its own ${copy}`);
        }
        // the shell is no generator's: tests keep each interior's names out of the other generate_*.py files
        const shell = tool('interiors.py');
        assert.ok(!/Shrine|PALACE_|TEMPLE_|House|Lobby|temple-in-/.test(shell), 'interiors.py names a kind of interior');
        assert.ok(!/^import (?!hashlib$|roomgen as rg$)/m.test(shell), 'interiors.py imports more than roomgen');
    });
};
