/**
 * Seats - the furniture the player can get on (issue #227), as one table.
 *
 * Getting on is walking straight into it: the cell stays blocked for
 * everything that asks CollisionSystem.checkCollision (NPCs, the model's
 * paths and reach, lint), and only the player's own one-cell straight step is
 * let through (CollisionSystem.checkSeatStep). Nothing here needs new art:
 * the player is drawn a few pixels off the cell (`dy`), turned the way the
 * furniture faces (`face`), sorted in front of it, and - for a bed, a bath, a
 * chair seen from behind - a piece of the furniture's own sprite (`cover`) is
 * drawn again over them (src/systems/Seating.js).
 *
 * A rule is { kind, pattern, pose, open?, at? }:
 *  - `pattern` is matched against the sprite key, first rule wins;
 *  - the seat's cells are the BLOCKED cells of the sprite's footprint. With
 *    `open: true` they are its walkable cells instead (a bench drawn behind
 *    the cell you stand on): those take the pose when you stop there, and
 *    nothing about stepping, sorting or covering changes;
 *  - `at` is [[col, row], ...]: only those cells of the footprint (from its
 *    top left) are the seat, the rest are not (a stall's middle stool, painted
 *    on a sprite that is a wall everywhere else);
 *  - `pose` is { face?, dy?, cover? }, or an array of them, one per footprint
 *    row from the top. `face` is 'up' | 'down' | 'left' | 'right' (none: keep
 *    the way you came), `dy` the pixels the player is drawn below (+) or
 *    above (-) the cell, `cover` an [x, y, w, h] rectangle of the sprite, in
 *    its own pixels, drawn over the player.
 *
 * Pure (no Phaser): tools/world-model.js and the tests load it as it is.
 */
const Seats = {
    RULES: [
        // a ramen counter's middle stool (issue #367): its outer stools are drawn too far off their cells to sit on
        { kind: 'stool', pattern: /^(susukino-ramen-stall-[ab]|yatai-ramen)_/, at: [[1, 2]], pose: { face: 'up', dy: -6 } },
        { kind: 'stool', pattern: /^(izakaya-stool|devhouse-stool|devhouse-garden-seat)_/, pose: { dy: -14 } },
        // a dining chair is named for the side of the table it stands on, and faces the table
        { kind: 'chair', pattern: /^devhouse-chair-n_/, pose: { face: 'down', dy: -10 } },
        { kind: 'chair', pattern: /^devhouse-chair-s_/, pose: { face: 'up', dy: -12, cover: [0, 0, 64, 64] } },
        { kind: 'chair', pattern: /^devhouse-chair-w_/, pose: { face: 'right', dy: -10 } },
        { kind: 'chair', pattern: /^devhouse-chair-e_/, pose: { face: 'left', dy: -10 } },
        { kind: 'armchair', pattern: /^devhouse-armchair_/, pose: { face: 'down', dy: -8 } },
        { kind: 'toilet', pattern: /^devhouse-toilet_/, pose: { face: 'down', dy: -8 } },
        { kind: 'sofa', pattern: /^lobby-sofa_/, pose: { face: 'down', dy: -12 } },
        // seen from behind: its back is drawn over the player
        { kind: 'sofa', pattern: /^lobby-sofa-back_/, pose: { face: 'up', dy: -22, cover: [0, 0, 128, 64] } },
        { kind: 'sofa', pattern: /^devhouse-sofa_/, pose: { face: 'right' } },
        { kind: 'bench', pattern: /^station-bench_/, pose: { face: 'down', dy: -20 } },
        // the bench with its back to you is drawn on the cells you walk on
        { kind: 'bench', pattern: /^station-bench-back_/, open: true, pose: { face: 'up', dy: 6 } },
        { kind: 'bench', pattern: /^odori-bench_/, pose: { face: 'down', dy: -16 } },
        { kind: 'bench', pattern: /^temple-in-bench_/, pose: { dy: -22 } },
        { kind: 'seats', pattern: /^airport-seats_/, pose: { face: 'down', dy: -12 } },
        // the bench up Fukuoka Tower faces the glass (issue #242): you are seen from behind, and its front is drawn over your legs
        { kind: 'bench', pattern: /^deck-in-bench_/, pose: { face: 'up', dy: -20, cover: [0, 30, 128, 34] } },
        // lying down: the pillow row carries the pose, and the blanket is the cover
        { kind: 'bed', pattern: /^home-bed_/, pose: [{ face: 'down', dy: 14, cover: [0, 56, 64, 72] }, {}] },
        { kind: 'futon', pattern: /^home-futon-/, pose: [{ face: 'down', dy: 12, cover: [0, 46, 64, 82] }, {}] },
        { kind: 'bunk', pattern: /^devhouse-bunk_/, pose: [{ face: 'down', dy: 4, cover: [0, 40, 64, 40] }, {}] },
        { kind: 'bath', pattern: /^devhouse-bath_/, pose: [{ face: 'down', dy: 10, cover: [0, 52, 64, 76] }, { face: 'down', cover: [0, 100, 64, 28] }] },
    ],

    /** The rule for a sprite key, or null. */
    match(key) {
        if (typeof key !== 'string') return null;
        return Seats.RULES.find(r => r.pattern.test(key)) || null;
    },

    /**
     * Every seat cell of a room: Map "x,y" -> { kind, key, x, y, w, h, row,
     * pose, solid }. x, y, w, h are the furniture's footprint (`sizeOf(key)`
     * cells from the cell it is placed on), `row` this cell's row in it,
     * `pose` that row's pose ({} when it has none) and `solid` whether the
     * cell is blocked (so getting on it takes the seat step). Where two
     * pieces of furniture overlap, the first to claim a cell keeps it.
     */
    index(room, opts) {
        const { sizeOf, isBlocked } = opts || {};
        const cells = new Map();
        // each sprite key is matched against the rules once (as Interactions.all)
        const hits = new Map();
        for (const layer of (room.layers || [])) {
            for (const xy in (layer.tiles || {})) {
                const key = layer.tiles[xy];
                let rule = hits.get(key);
                if (rule === undefined) hits.set(key, rule = Seats.match(key));
                if (!rule) continue;
                const [x, y] = xy.split(',').map(Number);
                const [w, h] = sizeOf ? sizeOf(key) : [1, 1];
                for (let row = 0; row < h; row++) {
                    const pose = (Array.isArray(rule.pose) ? rule.pose[row] : rule.pose) || {};
                    for (let cx = x; cx < x + w; cx++) {
                        if (rule.at && !rule.at.some(([c, r]) => c === cx - x && r === row)) continue;
                        const at = cx + ',' + (y + row);
                        const blocked = !!(isBlocked && isBlocked(cx, y + row));
                        if (blocked === !!rule.open || cells.has(at)) continue;
                        cells.set(at, { kind: rule.kind, key, x, y, w, h, row, pose, solid: blocked });
                    }
                }
            }
        }
        return cells;
    },

    /** The seat cell at a cell of an index(), or null. */
    lookup(index, gridX, gridY) {
        return index.get(gridX + ',' + gridY) || null;
    },

    /** Whether a step from one cell to the next may end on this seat cell: a solid one, one cell away, straight. */
    canStepOn(cell, fromX, fromY, toX, toY) {
        return !!cell && cell.solid && Math.abs(toX - fromX) + Math.abs(toY - fromY) === 1;
    },

    /** The lift `t` (0..1) of the way from one cell to the next; either may be null, the floor. */
    dyAt(from, to, t) {
        const a = (from && from.pose.dy) || 0, b = (to && to.pose.dy) || 0;
        return a + (b - a) * Math.max(0, Math.min(1, t));
    },

    /**
     * The row someone on these seat cells sorts by: their own feet row, or
     * the foot of the lowest solid furniture they are on - so they are drawn
     * in front of what they sit on, not behind it.
     */
    footRow(cells, feetRow) {
        let row = feetRow;
        for (const c of cells) if (c && c.solid) row = Math.max(row, c.y + c.h);
        return row;
    },
};

if (typeof window !== 'undefined') window.Seats = Seats;
