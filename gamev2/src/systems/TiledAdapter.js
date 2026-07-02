/**
 * TiledAdapter - reads a Tiled .tmj (JSON) map into the exact room shape that
 * RoomManager already renders: { layers:[{name,z,collision,tiles:{"x,y":key}}],
 * transporters, worldWidth, worldHeight, boundary }.
 *
 * This is the PoC bridge for authoring levels in Tiled instead of the bespoke
 * config.json. Because the output matches config's room shape, the ENTIRE
 * existing renderer (per-sprite placement + feet-based Y-sort + collision) is
 * reused untouched -- Tiled just becomes the data source.
 *
 * Conventions (produced by tools/config_to_tiled.py):
 *  - one image-collection tileset; each tile's `image` basename IS the sprite key
 *  - tile layers carry 1x1 ground; object layers carry multi-cell tile-objects
 *  - both kinds carry `gv2layer` (name) + `z` + `collision` custom properties;
 *    a tile layer and its `· obj` companion merge back into one gamev2 layer
 *  - tileset objectalignment=topleft, so a tile-object's (x,y) is its cell's
 *    top-left -> cell = round(x/GS), round(y/GS)
 *  - a `Meta` object layer holds transporter points + a boundary polygon
 */
const TiledAdapter = {
    toRoom(tmj) {
        const GS = tmj.tilewidth || 64;
        const W = tmj.width;
        const FLIP = 0x1FFFFFFF; // strip Tiled's flip flags from the high bits of a gid

        // gid -> sprite key, via the tileset's per-tile image filename.
        // The visible collider-marker tile (used so collision is paintable in
        // Tiled) maps back to the game's invisible gk_blank collider.
        const ts = tmj.tilesets[0];
        const idToKey = {};
        for (const t of ts.tiles) {
            let key = t.image.split('/').pop().replace(/\.png$/, '');
            if (key === 'collider-marker') key = 'gk_blank';
            idToKey[t.id] = key;
        }
        const keyOf = (gid) => idToKey[(gid & FLIP) - ts.firstgid];

        const prop = (o, n, d) => {
            const p = (o.properties || []).find(p => p.name === n);
            return p ? p.value : d;
        };

        // merge a tile layer + its "· obj" companion (same gv2layer) into one layer
        const byName = {};
        let order = 0;
        const layerFor = (name, z, coll) =>
            byName[name] || (byName[name] = { name, z, collision: coll, tiles: {}, _o: order++ });

        let transporters = [];
        let boundary = null;
        const worldWidth = prop(tmj, 'gv2worldWidth', W * GS);
        const worldHeight = prop(tmj, 'gv2worldHeight', tmj.height * GS);

        for (const L of tmj.layers) {
            if (L.type === 'tilelayer') {
                const lay = layerFor(prop(L, 'gv2layer', L.name), prop(L, 'z', 0), prop(L, 'collision', false));
                for (let i = 0; i < L.data.length; i++) {
                    const gid = L.data[i];
                    if (!gid) continue;
                    lay.tiles[`${i % W},${(i / W) | 0}`] = keyOf(gid);
                }
            } else if (L.type === 'objectgroup' && prop(L, 'gv2meta', false)) {
                for (const o of L.objects) {
                    if (prop(o, 'kind', '') === 'transporter') {
                        transporters.push({
                            gridX: Math.floor(o.x / GS), gridY: Math.floor(o.y / GS),
                            targetRoom: prop(o, 'targetRoom', ''),
                            targetX: prop(o, 'targetX', 0), targetY: prop(o, 'targetY', 0),
                            hidden: prop(o, 'hidden', false),
                        });
                    } else if (prop(o, 'kind', '') === 'boundary' && o.polygon) {
                        boundary = o.polygon.map(p => [Math.round((o.x + p.x) / GS), Math.round((o.y + p.y) / GS)]);
                    }
                }
            } else if (L.type === 'objectgroup') {
                const lay = layerFor(prop(L, 'gv2layer', L.name), prop(L, 'z', 0), prop(L, 'collision', false));
                for (const o of L.objects) {
                    if (!o.gid) continue;
                    lay.tiles[`${Math.round(o.x / GS)},${Math.round(o.y / GS)}`] = keyOf(o.gid);
                }
            }
        }

        const layers = Object.values(byName).sort((a, b) => a._o - b._o)
            .map(({ name, z, collision, tiles }) => ({ name, z, collision, tiles }));
        return { layers, transporters, worldWidth, worldHeight, boundary };
    },
};

if (typeof window !== 'undefined') window.TiledAdapter = TiledAdapter;
