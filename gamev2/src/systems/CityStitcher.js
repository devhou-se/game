/**
 * CityStitcher - merges a city's districts into ONE continuous room at load
 * (issues #40 / #41).
 *
 * The four Tokyo districts (Tokyo, Market, Palace, Park) stay four
 * Tiled maps and four room keys in config.json — the blog pipeline, the world
 * map, saved achievement progress and the room generators all key off them.
 * config `cities` lists which rooms belong together and where each one sits in
 * world cells (copied from devhouse.world by tools/sync_cities.py):
 *
 *   "cities": { "TokyoCity": {
 *       "name": "Tokyo",
 *       "rooms": [ {"room": "Tokyo", "x": 0, "y": 1}, ... ],   // later wins overlaps
 *       "drop": { "Park": ["tokyo-tower-feet"] },              // art a neighbour already draws
 *       "patch": { "Park": { "Floor": { "0,0": "road-..." } } }, // seam touch-ups, see build()
 *       "backdrop": { "floor", "tree": {"top", "base"}, "shrub", "edges", "extend", "extendClear", "extendStop" } } }
 *
 * plan() validates that block; build() turns a planned city into one runtime
 * room in the shape RoomManager renders, in MERGED cell coordinates (the
 * union's top-left is 0,0): every layer tile, object, signage spot and door
 * transporter translated by its district's offset, the hidden seam
 * transporters between districts dropped, overlapped cells given to exactly
 * one district, and the holes in the L-shaped union filled with woodland.
 *
 * `?stitch=0` switches the whole thing off (the districts are separate rooms
 * joined by fade transporters again, exactly as before).
 */
const CityStitcher = {
    /** Stitching is on unless the page was opened with ?stitch=0. */
    enabled() {
        return new URLSearchParams(window.location.search).get('stitch') !== '0';
    },

    /**
     * Validate config `cities` -> { cityKey: city }. A city that fails a check
     * is reported with console.error and left out, so its districts simply
     * stay separate rooms.
     *
     * city = { key, name, width, height (cells), members: [{ key, x, y, w, h }],
     *          drop, backdrop } with member x/y relative to the union's top-left.
     */
    plan(config, worldMap) {
        const cities = {};
        const GS = config.game.gridSize;
        const taken = new Set();
        for (const [key, def] of Object.entries(config.cities || {})) {
            const fail = (why) => console.error(`[stitch] city "${key}" not stitched: ${why}`);
            if (config.rooms[key]) { fail('a room has the same name'); continue; }
            const list = Array.isArray(def.rooms) ? def.rooms : [];
            if (list.length < 2) { fail('needs at least two rooms'); continue; }

            let bad = null;
            const members = list.map(m => {
                const room = config.rooms[m.room];
                if (!room) bad = bad || `"${m.room}" is not a room`;
                else if (taken.has(m.room)) bad = bad || `"${m.room}" is already in another city`;
                else if (!Number.isInteger(m.x) || !Number.isInteger(m.y)) bad = bad || `"${m.room}" has no cell offset`;
                return room ? {
                    key: m.room, x: m.x, y: m.y,
                    w: Math.round((room.worldWidth || config.game.worldWidth) / GS),
                    h: Math.round((room.worldHeight || config.game.worldHeight) / GS),
                } : null;
            });
            if (!bad) bad = this.disagreesWithMap(members, worldMap);
            if (bad) { fail(bad); continue; }

            const minX = Math.min(...members.map(m => m.x));
            const minY = Math.min(...members.map(m => m.y));
            members.forEach(m => { m.x -= minX; m.y -= minY; taken.add(m.key); });
            cities[key] = {
                key,
                name: def.name || key,
                members,
                width: Math.max(...members.map(m => m.x + m.w)),
                height: Math.max(...members.map(m => m.y + m.h)),
                drop: def.drop || {},
                patch: def.patch || {},
                backdrop: def.backdrop || null,
            };
        }
        return cities;
    },

    /**
     * The deployed copy of the world layout is assets/map/world-map.json (each
     * room's rect on the map image, written from devhouse.world by
     * tools/make_worldmap.py). Unless that art is hand-made (`custom`, not to
     * scale) the districts must sit the same number of cells apart in both, or
     * config `cities` has drifted from the world file. Returns the complaint,
     * or null when they agree / there is nothing to compare against.
     */
    disagreesWithMap(members, worldMap) {
        if (!worldMap || worldMap.custom || !worldMap.rooms) return null;
        const cell = (m) => {
            const r = worldMap.rooms[m.key];
            return r ? [r.x / (r.w / r.cells[0]), r.y / (r.h / r.cells[1])] : null;
        };
        const first = members[0], firstAt = cell(first);
        if (!firstAt) return null;
        for (const m of members) {
            const at = cell(m);
            if (!at) continue;
            const dx = Math.round(at[0] - firstAt[0]), dy = Math.round(at[1] - firstAt[1]);
            if (dx !== m.x - first.x || dy !== m.y - first.y) {
                return `"${m.key}" is (${m.x - first.x}, ${m.y - first.y}) cells from "${first.key}" in ` +
                    `config cities but (${dx}, ${dy}) on the world map — run tools/sync_cities.py`;
            }
        }
        return null;
    },

    /** The district that owns a merged cell: the LAST listed member containing it. */
    ownerOf(city, x, y) {
        for (let i = city.members.length - 1; i >= 0; i--) {
            const m = city.members[i];
            if (x >= m.x && x < m.x + m.w && y >= m.y && y < m.y + m.h) return m;
        }
        return null;
    },

    /**
     * One runtime room for a planned city, from its districts' already
     * initialised rooms (RoomManager.rooms). Seam transporters (target = a
     * sibling district) are dropped; door transporters keep their legacy
     * targets, which RoomManager.resolve() translates when they fire.
     *
     * `city.patch` = { district: { layer name: { "x,y": tile | null } } } (the
     * district's own cells) touches up the few tiles that were drawn for a
     * district seen on its own and read wrong once its neighbour is in view
     * — a road corner where the road now carries straight on — without
     * editing the district's map: the patched tile replaces (null: removes)
     * that layer's tile in the stitched room only.
     */
    build(city, rooms, gridSize) {
        const memberKeys = new Set(city.members.map(m => m.key));
        const byId = new Map();
        const layers = [];
        const transporters = [], objects = [], signage = [];

        for (const m of city.members) {
            const room = rooms[m.key];
            const drop = new Set(city.drop[m.key] || []);
            const patch = Object.assign({}, city.patch[m.key]);
            for (const L of (room.layers || [])) {
                const id = `${L.name}|${L.z}|${!!L.collision}`;
                let lay = byId.get(id);
                if (!lay) {
                    lay = { name: L.name, z: L.z, collision: !!L.collision, tiles: {} };
                    byId.set(id, lay);
                    layers.push(lay);
                }
                const tiles = patch[L.name] ? Object.assign({}, L.tiles, patch[L.name]) : (L.tiles || {});
                delete patch[L.name];
                for (const xy in tiles) {
                    const key = tiles[xy];
                    if (!key || drop.has(key)) continue;
                    const c = xy.indexOf(',');
                    const X = Number(xy.slice(0, c)) + m.x, Y = Number(xy.slice(c + 1)) + m.y;
                    // an overlapped cell belongs to one district only — the
                    // other's tiles AND colliders there are left out
                    const owner = this.ownerOf(city, X, Y);
                    if (owner && owner !== m) continue;
                    lay.tiles[`${X},${Y}`] = key;
                }
            }
            for (const name in patch) {
                console.warn(`[stitch] ${city.key}: patch names a layer "${name}" that ${m.key} does not have`);
            }
            for (const t of (room.transporters || [])) {
                if (memberKeys.has(t.targetRoom)) continue;   // a seam: now you just walk
                transporters.push(Object.assign({}, t, { gridX: t.gridX + m.x, gridY: t.gridY + m.y }));
            }
            for (const o of (room.objects || [])) {
                objects.push(Object.assign({}, o, { gridX: o.gridX + m.x, gridY: o.gridY + m.y }));
            }
            for (const s of (room.signage || [])) {
                signage.push(Object.assign({}, s, { gridX: s.gridX + m.x, gridY: s.gridY + m.y }));
            }
        }

        // districts list their layers in their own order: keep the draw-order
        // tie-break (same depth -> layer order) the same for all of them
        layers.forEach((l, i) => { l._o = i; });
        layers.sort((a, b) => (a.z - b.z) || (a._o - b._o));
        layers.forEach(l => { delete l._o; });

        return {
            name: city.name,
            city,
            stitched: true,
            boundary: null,                    // RoomManager.checkBoundary asks the districts
            worldWidth: city.width * gridSize,
            worldHeight: city.height * gridSize,
            // Y-sorted depths grow 10 per row; a map this tall would climb past
            // the name labels (900) and the HUD (1000), so they are squeezed
            depthScale: Math.min(1, 850 / (city.height * 10 + 20)),
            npcs: [],
            objects,
            transporters,
            floor: {},
            layers: layers.concat(this.buildBackdrop(city, layers)),
            signage,
        };
    },

    /**
     * The union of the districts is not a rectangle, and the camera is only
     * clamped to its bounding box — so every cell no district covers is
     * dressed as woodland nobody can enter (RoomManager.checkBoundary only
     * admits district cells): grass, unevenly spaced trees, and scattered
     * shrubs where no tree stands. Two rules keep the districts' own art
     * from stopping dead at the wood: `backdrop.edges` finishes ground a
     * district leaves half-drawn at its edge, and a tile matching
     * `backdrop.extend` (the railway) that reaches a district's edge carries
     * on across the void in a tree-free corridor `extendClear` rows tall.
     * Where that would run into another district rather than off the map,
     * the line stops `extendStop` cells short and ends under a shrub, so the
     * wood closes over it and the district sees trees, not a track that
     * stops dead at its fence.
     * Layers are named "Backdrop ..." so nothing mistakes them for walkable
     * Floor. Deterministic: the same wood grows on every load.
     */
    buildBackdrop(city, layers) {
        const spec = city.backdrop;
        if (!spec || !spec.floor) return [];
        const W = city.width, H = city.height;
        const isVoid = (x, y) => x >= 0 && x < W && y >= 0 && y < H && !this.ownerOf(city, x, y);
        const out = [];

        const floor = {};
        let any = false;
        for (let y = 0; y < H; y++) {
            for (let x = 0; x < W; x++) {
                if (isVoid(x, y)) { floor[`${x},${y}`] = spec.floor; any = true; }
            }
        }
        if (!any) return [];
        out.push({ name: 'Backdrop', z: 0, collision: false, tiles: floor });

        // finish ground art a district leaves half-drawn at its edge: a void
        // cell at (dx, dy) from a tile matching `beside` gets `tile` (the
        // road down Palace's west side has no kerb of its own — its western
        // lane used to be off-camera)
        const clear = new Set();
        const edge = {};
        for (const rule of (spec.edges || [])) {
            const re = new RegExp(rule.beside);
            for (const L of layers) {
                if (L.z >= 2) continue;
                for (const xy in L.tiles) {
                    if (!re.test(L.tiles[xy])) continue;
                    const [x, y] = xy.split(',').map(Number);
                    const ex = x + (rule.dx || 0), ey = y + (rule.dy || 0);
                    if (!isVoid(ex, ey)) continue;
                    edge[`${ex},${ey}`] = rule.tile;
                    clear.add(`${ex},${ey}`);
                }
            }
        }
        if (Object.keys(edge).length) out.push({ name: 'Backdrop Edge', z: 0, collision: false, tiles: edge });

        // carry edge tiles (the railway) on across the void
        const ends = [];
        if (spec.extend) {
            const re = new RegExp(spec.extend);
            const rows = spec.extendClear || 1;
            const stop = spec.extendStop || 0;
            for (const L of layers) {
                const ext = {};
                for (const xy in L.tiles) {
                    if (!re.test(L.tiles[xy])) continue;
                    const [x, y] = xy.split(',').map(Number);
                    for (const dir of [-1, 1]) {
                        let end = x + dir;
                        while (isVoid(end, y)) end += dir;
                        if (end === x + dir) continue;          // no void on this side
                        // ran into another district rather than off the map:
                        // the line ends in the wood, under a bush
                        const closed = end >= 0 && end < W;
                        if (closed) end -= dir * stop;
                        for (let cx = x + dir; cx !== end && (cx - end) * dir < 0; cx += dir) {
                            ext[`${cx},${y}`] = L.tiles[xy];
                            for (let r = 0; r < rows; r++) clear.add(`${cx},${y - r}`);
                        }
                        if (closed && (end - dir - x) * dir > 0) ends.push(`${end - dir},${y}`);
                    }
                }
                if (Object.keys(ext).length) {
                    out.push({ name: `Backdrop ${L.name}`, z: L.z, collision: false, tiles: ext });
                }
            }
        }

        // trees: a 2x3 footprint (canopy two rows, trunk row below), planted in
        // bands two rows apart and staggered so the canopies overlap
        const hash = (x, y) => (Math.imul(x, 73856093) ^ Math.imul(y, 19349663)) >>> 0;
        const trunks = {}, tops = {}, shrubs = {};
        const planted = new Set();
        const tree = spec.tree;
        if (tree && tree.top && tree.base) {
            const fits = (x, y) => {
                for (let dy = 0; dy < 3; dy++) {
                    for (let dx = 0; dx < 2; dx++) {
                        if (!isVoid(x + dx, y + dy) || clear.has(`${x + dx},${y + dy}`)) return false;
                    }
                }
                return true;
            };
            for (let y = 0, band = 0; y < H; y += 2, band++) {
                // uneven spacing (2-3 cells, now and then a clearing) and a
                // different start per band, so it reads as a wood, not a grid
                for (let x = hash(band, 7) % 3; x < W; x += 2 + (hash(x, y) % 3 ? 0 : 1) + (hash(y, x) % 9 ? 0 : 2)) {
                    if (!fits(x, y)) continue;
                    tops[`${x},${y}`] = tree.top;
                    trunks[`${x},${y + 2}`] = tree.base;
                    for (let dy = 0; dy < 3; dy++) {
                        planted.add(`${x},${y + dy}`);
                        planted.add(`${x + 1},${y + dy}`);
                    }
                }
            }
        }
        // strips too thin for a tree (and the gaps at the wood's edge) get shrubs
        if (spec.shrub) {
            for (const xy in floor) {
                if (planted.has(xy) || clear.has(xy)) continue;
                const [x, y] = xy.split(',').map(Number);
                if (hash(x, y) % 5 < 2) shrubs[xy] = spec.shrub;
            }
            for (const xy of ends) shrubs[xy] = spec.shrub;
        }
        out.push({ name: 'Backdrop Collidables', z: 5, collision: false, tiles: Object.assign(shrubs, trunks) });
        out.push({ name: 'Backdrop Tops', z: 7, collision: false, tiles: tops });
        return out;
    },
};

if (typeof window !== 'undefined') window.CityStitcher = CityStitcher;
