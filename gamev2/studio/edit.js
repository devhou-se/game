const Edit = (() => {
    const GS = 64;
    const FLIP = 0x1FFFFFFF;
    const LAYER_Z = { 'Floor': 0, 'Over Floor': 1, 'Water': 1, 'Non-Collidables': 4, 'Collidables': 5, 'Other': 6, 'Tops': 7, 'Colliders': 5 };
    const floats = new WeakMap();
    const markFloat = (o, ...keys) => {
        let set = floats.get(o);
        if (!set) floats.set(o, set = new Set());
        for (const k of keys) set.add(String(k));
        return o;
    };

    function parse(text) {
        return JSON.parse(text, function (key, value, ctx) {
            if (typeof value === 'number' && ctx && /[.eE]/.test(ctx.source)) markFloat(this, key);
            return value;
        });
    }

    const str = (s) => JSON.stringify(s).replace(/[\u007f-￿]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));

    function stringify(value, indent) {
        const pad = (n) => '\n' + ' '.repeat(indent * n);
        const go = (v, depth, holder, key) => {
            if (v === null) return 'null';
            if (typeof v === 'number') {
                const float = holder && floats.has(holder) && floats.get(holder).has(String(key));
                return float && Number.isInteger(v) ? v + '.0' : String(v);
            }
            if (typeof v === 'boolean') return String(v);
            if (typeof v === 'string') return str(v);
            if (Array.isArray(v)) {
                if (!v.length) return '[]';
                return '[' + v.map((x, i) => pad(depth + 1) + go(x, depth + 1, v, i)).join(',') + pad(depth) + ']';
            }
            const keys = Object.keys(v);
            if (!keys.length) return '{}';
            return '{' + keys.map(k => pad(depth + 1) + str(k) + ': ' + go(v[k], depth + 1, v, k)).join(',') + pad(depth) + '}';
        };
        return go(value, 0, null, '');
    }

    const sortKeys = (o) => {
        const entries = Object.entries(o).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0);
        for (const [k] of entries) delete o[k];
        for (const [k, v] of entries) o[k] = v;
        return o;
    };

    const prop = (o, n, d) => {
        const p = (o.properties || []).find(p => p.name === n);
        return p ? p.value : d;
    };
    const props = (d) => Object.entries(d).map(([name, value]) => (
        { name, type: typeof value === 'boolean' ? 'bool' : typeof value === 'number' ? 'int' : 'string', value }));
    const setProp = (o, name, value) => {
        const p = (o.properties || (o.properties = [])).find(p => p.name === name);
        if (p) p.value = value;
        else o.properties.push(props({ [name]: value })[0]);
    };

    const spriteKey = (image) => {
        const key = image.split('/').pop().replace(/\.png$/, '');
        return key === 'collider-marker' ? 'gk_blank' : key;
    };
    const keyOf = (doc, gid) => {
        const ts = doc.tilesets[0];
        const t = ts.tiles.find(t => t.id === (gid & FLIP) - ts.firstgid);
        return t ? spriteKey(t.image) : null;
    };
    function gidOf(doc, key, ctx) {
        const ts = doc.tilesets[0];
        let t = ts.tiles.find(t => spriteKey(t.image) === key);
        if (!t) {
            const dir = ts.tiles.length ? ts.tiles[0].image.replace(/[^/]*$/, '') : '../assets/sprites/';
            const file = key === 'gk_blank' ? 'collider-marker' : key;
            const [w, h] = key === 'gk_blank' ? [GS, GS] : ctx.pixels(key);
            t = { id: ts.tiles.reduce((m, t) => Math.max(m, t.id), -1) + 1, image: `${dir}${file}.png`, imagewidth: w, imageheight: h };
            ts.tiles.push(t);
            ts.tilecount = ts.tiles.length;
        }
        return ts.firstgid + t.id;
    }

    const isMeta = (L) => L.type === 'objectgroup' && prop(L, 'gv2meta', false);
    const layerName = (L) => prop(L, 'gv2layer', L.name.replace(' ·obj', ''));
    const findLayer = (doc, name, type) => doc.layers.find(L => L.type === type && !isMeta(L) && layerName(L) === name);
    function ensureLayer(doc, name, type) {
        const found = findLayer(doc, name, type);
        if (found) return found;
        const twin = doc.layers.find(L => !isMeta(L) && layerName(L) === name);
        const spec = { gv2layer: name, z: twin ? prop(twin, 'z', 0) : (LAYER_Z[name] || 0), collision: twin ? prop(twin, 'collision', false) : name === 'Colliders' };
        const L = type === 'tilelayer'
            ? { type, id: doc.nextlayerid++, name, width: doc.width, height: doc.height, x: 0, y: 0, opacity: 1, visible: true, data: new Array(doc.width * doc.height).fill(0), properties: props(spec) }
            : { type, id: doc.nextlayerid++, name: name + ' ·obj', x: 0, y: 0, opacity: 1, visible: true, draworder: 'index', objects: [], properties: props(spec) };
        const at = twin ? doc.layers.indexOf(twin) + 1 : doc.layers.findIndex(isMeta);
        doc.layers.splice(at < 0 ? doc.layers.length : at, 0, L);
        return L;
    }
    function meta(doc) {
        let L = doc.layers.find(isMeta);
        if (!L) {
            L = { type: 'objectgroup', id: doc.nextlayerid++, name: 'Meta', x: 0, y: 0, opacity: 1, visible: true, draworder: 'index', objects: [], properties: props({ gv2meta: true }) };
            doc.layers.push(L);
        }
        return L;
    }

    function sprites(doc) {
        const out = [];
        for (const L of doc.layers) {
            if (isMeta(L)) continue;
            const base = { L, layer: layerName(L), z: prop(L, 'z', 0), collision: !!prop(L, 'collision', false) };
            if (L.type === 'tilelayer') {
                for (let i = 0; i < L.data.length; i++) {
                    if (L.data[i]) out.push({ ...base, kind: 'tile', i, key: keyOf(doc, L.data[i]), x: i % doc.width, y: (i / doc.width) | 0 });
                }
            } else if (L.type === 'objectgroup') {
                for (const o of L.objects) {
                    if (o.gid) out.push({ ...base, kind: 'object', o, key: keyOf(doc, o.gid), x: Math.round(o.x / GS), y: Math.round(o.y / GS) });
                }
            }
        }
        return out;
    }
    const size = (s, ctx) => s.collision ? [1, 1] : ctx.sizeOf(s.key);
    const covers = (s, x, y, ctx) => {
        const [w, h] = size(s, ctx);
        return x >= s.x && x < s.x + w && y >= s.y && y < s.y + h;
    };
    const standing = (s) => !s.collision && s.z >= 2;
    const same = (a, b) => a.L === b.L && a.kind === b.kind && (a.kind === 'tile' ? a.i === b.i : a.o === b.o);

    function thingsAt(doc, x, y, ctx) {
        return sprites(doc).filter(s => !s.collision && covers(s, x, y, ctx))
            .sort((a, b) => b.z - a.z || (b.kind === 'object') - (a.kind === 'object'));
    }

    function setSolid(doc, x, y, on) {
        if (x < 0 || y < 0 || x >= doc.width || y >= doc.height) return;
        const i = y * doc.width + x;
        if (on) {
            ensureLayer(doc, 'Colliders', 'tilelayer').data[i] = gidOf(doc, 'gk_blank');
            return;
        }
        for (const L of doc.layers) {
            if (isMeta(L) || !prop(L, 'collision', false)) continue;
            if (L.type === 'tilelayer') L.data[i] = 0;
            else L.objects = L.objects.filter(o => !(Math.round(o.x / GS) === x && Math.round(o.y / GS) === y));
        }
    }
    const solidCells = (doc) => new Set(sprites(doc).filter(s => s.collision).map(s => s.x + ',' + s.y));

    function ownedColliders(doc, thing, ctx) {
        if (!standing(thing)) return [];
        const all = sprites(doc);
        const solid = new Set(all.filter(s => s.collision).map(s => s.x + ',' + s.y));
        const others = all.filter(s => standing(s) && !same(s, thing));
        const [w, h] = size(thing, ctx);
        const cells = [];
        for (let dy = 0; dy < h; dy++) for (let dx = 0; dx < w; dx++) {
            const x = thing.x + dx, y = thing.y + dy;
            if (solid.has(x + ',' + y) && !others.some(o => covers(o, x, y, ctx))) cells.push([dx, dy]);
        }
        return cells;
    }

    function removeSprite(doc, thing, ctx) {
        for (const [dx, dy] of ownedColliders(doc, thing, ctx)) setSolid(doc, thing.x + dx, thing.y + dy, false);
        if (thing.kind === 'tile') thing.L.data[thing.i] = 0;
        else thing.L.objects.splice(thing.L.objects.indexOf(thing.o), 1);
    }

    function moveSprite(doc, thing, nx, ny, ctx) {
        const [w, h] = size(thing, ctx);
        if (nx < 0 || ny < 0 || nx + w > doc.width || ny + h > doc.height) throw new Error('That is outside the room');
        const clash = sprites(doc).find(s => !same(s, thing) && s.layer === thing.layer && s.x === nx && s.y === ny);
        if (clash) throw new Error(`${clash.key} is already on that cell`);
        const owned = ownedColliders(doc, thing, ctx);
        for (const [dx, dy] of owned) setSolid(doc, thing.x + dx, thing.y + dy, false);
        if (thing.kind === 'tile') {
            const gid = thing.L.data[thing.i];
            thing.L.data[thing.i] = 0;
            thing.L.data[ny * doc.width + nx] = gid;
        } else {
            thing.o.x = nx * GS;
            thing.o.y = ny * GS;
        }
        for (const [dx, dy] of owned) setSolid(doc, nx + dx, ny + dy, true);
    }

    function prefab(name, doc) {
        const pf = { name, w: doc.width, h: doc.height, sprites: [], colliders: [], doors: [] };
        for (const L of doc.layers) {
            if (isMeta(L)) {
                for (const o of L.objects) if (prop(o, 'kind') === 'door') pf.doors.push([Math.floor(o.x / GS), Math.floor(o.y / GS)]);
            } else if (L.type === 'objectgroup') {
                for (const o of L.objects) if (o.gid) pf.sprites.push({ layer: layerName(L), x: Math.round(o.x / GS), y: Math.round(o.y / GS), key: keyOf(doc, o.gid) });
            } else if (L.type === 'tilelayer') {
                L.data.forEach((gid, i) => {
                    if (!gid) return;
                    const key = keyOf(doc, gid), x = i % L.width, y = (i / L.width) | 0;
                    if (layerName(L) === 'Colliders' || key === 'gk_blank') pf.colliders.push([x, y]);
                    else pf.sprites.push({ layer: layerName(L), x, y, key });
                });
            }
        }
        for (const d of pf.doors) if (!pf.colliders.some(c => c[0] === d[0] && c[1] === d[1])) pf.colliders.push(d);
        return pf;
    }

    function checkStamp(doc, pf, x, y, ctx) {
        const all = sprites(doc);
        for (const s of pf.sprites) {
            const [w, h] = ctx.sizeOf(s.key);
            const sx = x + s.x, sy = y + s.y;
            if (sx < 0 || sy < 0 || sx + w > doc.width || sy + h > doc.height) return 'Outside the room';
            const anchored = all.find(o => !o.collision && o.layer === s.layer && o.x === sx && o.y === sy);
            if (anchored) return `${anchored.key} is already on ${sx}, ${sy}`;
            if (s.layer !== 'Collidables') continue;
            const hit = all.find(o => o.layer === 'Collidables' && o.x < sx + w && sx < o.x + size(o, ctx)[0] && o.y < sy + h && sy < o.y + size(o, ctx)[1]);
            if (hit) return `Overlaps ${hit.key}`;
        }
        const doors = transporters(doc);
        for (const [dx, dy] of pf.colliders) {
            const cx = x + dx, cy = y + dy;
            if (cx < 0 || cy < 0 || cx >= doc.width || cy >= doc.height) return 'Outside the room';
            if (doors.some(t => t.x === cx && t.y === cy)) return `Covers the door at ${cx}, ${cy}`;
            const who = (ctx.people || []).find(p => p.x === cx && p.y === cy);
            if (who) return `Covers ${who.name} on ${who.date}`;
        }
        return null;
    }

    function stamp(doc, pf, x, y, ctx) {
        const refused = checkStamp(doc, pf, x, y, ctx);
        if (refused) throw new Error(refused);
        for (const s of pf.sprites) {
            const [w, h] = ctx.sizeOf(s.key);
            const [pw, ph] = ctx.pixels(s.key);
            const gid = gidOf(doc, s.key, ctx);
            if (w === 1 && h === 1) ensureLayer(doc, s.layer, 'tilelayer').data[(y + s.y) * doc.width + x + s.x] = gid;
            else ensureLayer(doc, s.layer, 'objectgroup').objects.push({ id: doc.nextobjectid++, gid, name: s.key, x: (x + s.x) * GS, y: (y + s.y) * GS, width: pw, height: ph, visible: true });
        }
        for (const [dx, dy] of pf.colliders) setSolid(doc, x + dx, y + dy, true);
    }

    function transporters(doc) {
        const L = doc.layers.find(isMeta);
        if (!L) return [];
        return L.objects.filter(o => prop(o, 'kind', '') === 'transporter').map(o => ({
            o, x: Math.floor(o.x / GS), y: Math.floor(o.y / GS),
            targetRoom: prop(o, 'targetRoom', ''), targetX: prop(o, 'targetX', 0), targetY: prop(o, 'targetY', 0), hidden: !!prop(o, 'hidden', false),
        }));
    }
    function addTransporter(doc, x, y, targetRoom, targetX, targetY, hidden) {
        const o = markFloat({
            id: doc.nextobjectid++, name: 'transporter', point: true, x: x * GS + GS / 2, y: y * GS + GS / 2, width: 0, height: 0, visible: true,
            properties: props({ kind: 'transporter', targetRoom, targetX, targetY, hidden: !!hidden }),
        }, 'x', 'y');
        meta(doc).objects.push(o);
        return o;
    }
    function removeTransporter(doc, t) {
        const L = meta(doc);
        L.objects.splice(L.objects.indexOf(t.o), 1);
    }
    function moveTransporter(t, x, y) {
        markFloat(t.o, 'x', 'y');
        t.o.x = x * GS + GS / 2;
        t.o.y = y * GS + GS / 2;
    }
    function retarget(t, room, x, y) {
        setProp(t.o, 'targetRoom', room);
        setProp(t.o, 'targetX', x);
        setProp(t.o, 'targetY', y);
    }

    function arrival(doc, x, y, open) {
        const doors = new Set(transporters(doc).map(t => t.x + ',' + t.y));
        const options = [[0, 1], [0, -1], [1, 0], [-1, 0]].filter(([dx, dy]) => open(x + dx, y + dy) && !doors.has((x + dx) + ',' + (y + dy)));
        const facing = options.find(([dx, dy]) => !open(x - dx, y - dy));
        const pick = facing || options[0];
        return pick ? [x + pick[0], y + pick[1]] : null;
    }

    function link(a, b) {
        for (const end of [a, b]) {
            if (transporters(end.doc).some(t => t.x === end.x && t.y === end.y)) throw new Error(`${end.room} ${end.x}, ${end.y} is already a door`);
        }
        const landA = arrival(a.doc, a.x, a.y, a.open), landB = arrival(b.doc, b.x, b.y, b.open);
        if (!landA) throw new Error(`No open cell beside ${a.room} ${a.x}, ${a.y}`);
        if (!landB) throw new Error(`No open cell beside ${b.room} ${b.x}, ${b.y}`);
        setSolid(a.doc, a.x, a.y, false);
        setSolid(b.doc, b.x, b.y, false);
        addTransporter(a.doc, a.x, a.y, b.room, landB[0], landB[1], true);
        addTransporter(b.doc, b.x, b.y, a.room, landA[0], landA[1], true);
        return { landA, landB };
    }

    function moveNpc(config, room, name, date, x, y) {
        const npc = (config.rooms[room].npcs || []).find(n => n.name === name);
        if (!npc) throw new Error(`${name} is not in ${room}`);
        if (!npc.states || !Object.keys(npc.states).length) {
            npc.gridX = x;
            npc.gridY = y;
            return false;
        }
        const state = npc.states[date] || (npc.states[date] = {});
        state.gridX = x;
        state.gridY = y;
        sortKeys(state);
        sortKeys(npc.states);
        return true;
    }

    return {
        GS, parse, stringify, prop, keyOf, sprites, thingsAt, size, solidCells, setSolid, removeSprite, moveSprite,
        prefab, checkStamp, stamp, transporters, addTransporter, removeTransporter, moveTransporter, retarget, setProp, link, moveNpc,
    };
})();

if (typeof window !== 'undefined') window.Edit = Edit;
if (typeof module !== 'undefined') module.exports = Edit;
