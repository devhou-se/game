const ART = 32;
const COLOR = { torii: '#e0421f', moat: '#2f5fd0', moss: '#2f8f5b', sun: '#f2b01e', ink: '#1b1f3b', paper: '#f4efe4' };
const GROUP_COLOR = { shop: COLOR.sun, pond: COLOR.moat, clock: '#9b4fd0', 'drinking-game': '#d04f9b' };
const LAYERS = [
    ['art', 'Art', true], ['collision', 'Collision', false], ['unreachable', 'Unreachable', true],
    ['teleports', 'Teleports', true], ['interactions', 'Interactions', true], ['people', 'People', true],
];

const $ = (id) => document.getElementById(id);
const canvas = $('view');
const ctx = canvas.getContext('2d');
const stage = $('stage');

const S = {
    model: null, images: {}, rooms: {}, order: [], dates: [], dateIndex: 0,
    show: Object.fromEntries(LAYERS.map(([k, , on]) => [k, on])),
    view: { x: 0, y: 0, z: 6 }, selected: null, survey: { problems: [], reach: {} },
};
// The game stitches the districts of config `cities` into one room, and the studio draws that
// room. ?stitch=0 (as in the game) shows them as the separate rooms joined by seam teleports.
const STITCH = new URLSearchParams(location.search).get('stitch') !== '0';

const bust = Date.now();
const getJSON = (url) => fetch(`${url}?t=${bust}`).then(r => r.ok ? r.json() : null).catch(() => null);
const loadImage = (key) => new Promise((resolve) => {
    const im = new Image();
    im.onload = () => { S.images[key] = im; resolve(); };
    im.onerror = () => resolve();
    im.src = `../assets/sprites/${key}.png`;
});
const el = (tag, props, ...kids) => {
    const node = Object.assign(document.createElement(tag), props || {});
    for (const kid of kids) node.append(kid);
    return node;
};

async function boot() {
    const config = decodeConfig(await getJSON('../config.json'));
    const keys = Object.keys(config.rooms);
    const tmj = Object.fromEntries(await Promise.all(keys.map(async k => [k, await getJSON(`../tiled/${k.toLowerCase()}.tmj`)])));
    WorldModel.applyTiled(config, (k) => tmj[k]);
    const worldMap = await getJSON('../assets/map/world-map.json') || { rooms: {} };

    // the model first (it stitches the cities), then the art of every room it holds - a stitched
    // city's woodland tiles are in its merged layers, not in any config room
    S.model = new WorldModel(config, {
        exists: (key) => !!S.images[key],
        sizeOf: (key) => {
            const im = S.images[key];
            return im ? [Math.max(1, Math.round(im.width / 64)), Math.max(1, Math.round(im.height / 64))] : [1, 1];
        },
    }, null, { stitch: STITCH, worldMap });
    const sprites = new Set();
    for (const room of Object.values(S.model.roomManager.rooms)) {
        for (const layer of room.layers || []) for (const key of Object.values(layer.tiles || {})) sprites.add(key);
    }
    for (const room of Object.values(config.rooms)) {
        for (const npc of room.npcs || []) sprites.add(npc.sprite + '_frame_0');
    }
    await Promise.all([...sprites].map(loadImage));
    const m = S.model;

    // the rooms that are drawn: a stitched city stands in for its districts
    const shown = m.runtimeRooms();
    layout(shown);
    for (const k of shown) {
        m.enter(k, 0, 0);
        const r = S.rooms[k];
        Object.assign(r, { blocked: m.blocked, interactions: m.interactions(), art: renderArt(k), npcs: [] });
        // the woodland between a city's districts is scenery, not unreachable floor
        r.outside = new Set();
        if (r.members) {
            for (let y = 0; y < r.h; y++) for (let x = 0; x < r.w; x++) if (!m.roomManager.checkBoundary(x, y)) r.outside.add(x + ',' + y);
        }
    }
    if (config.cities && Object.keys(config.cities).length) {
        const b = $('stitch');
        b.hidden = false;
        b.setAttribute('aria-pressed', STITCH);
        b.onclick = () => { location.search = STITCH ? '?stitch=0' : ''; };
    }

    // the days with posts, plus the first day of every trip and stay (the trip's base cast)
    const days = new Set(contentChangeDates(config));
    for (const trip of Trips.of(config)) {
        days.add(trip.start);
        for (const stay of trip.stays) days.add(stay.from);
    }
    S.dates = [...days].sort();
    const today = m.date;
    if (!S.dates.includes(today)) S.dates.push(today);
    S.dates.sort();
    S.dateIndex = S.dates.indexOf(today);
    $('scrub').max = S.dates.length - 1;

    const cast = new Set([baseOf(config.player.sprite)]);
    for (const room of Object.values(config.rooms)) for (const npc of room.npcs || []) cast.add(baseOf(npc.sprite));
    for (const name of cast) $('as').append(el('option', { value: name, textContent: 'as ' + name }));
    $('as').value = m.as;

    for (const [key, label] of LAYERS) {
        const b = el('button', { textContent: label });
        b.setAttribute('aria-pressed', S.show[key]);
        b.onclick = () => { S.show[key] = !S.show[key]; b.setAttribute('aria-pressed', S.show[key]); draw(); };
        $('layers').append(b);
    }

    bind();
    resize();
    fit();
    refresh();
    $('loading').remove();
}

function layout(keys) {
    const m = S.model;
    const rooms = {};
    for (const k of keys) {
        const r = m.roomManager.rooms[k];
        const city = m.roomManager.cities[k];
        rooms[k] = { x: 0, y: 0, w: r.worldWidth / 64, h: r.worldHeight / 64, members: city ? city.members : null };
    }
    const links = [];
    for (const k of keys) {
        for (const t of m.roomManager.rooms[k].transporters) {
            if (!rooms[t.targetRoom]) continue;
            links.push({ a: k, ax: t.gridX + 0.5, ay: t.gridY + 0.5, b: t.targetRoom, bx: t.targetX + 0.5, by: t.targetY + 0.5, w: 1 });
        }
    }
    const stations = Object.entries(m.config.stations || {}).filter(([k]) => rooms[k]);
    for (let i = 0; i < stations.length; i++) for (let j = i + 1; j < stations.length; j++) {
        const [a, sa] = stations[i], [b, sb] = stations[j];
        links.push({ a, ax: sa.board[0][0] + 0.5, ay: sa.board[0][1] + 0.5, b, bx: sb.board[0][0] + 0.5, by: sb.board[0][1] + 0.5, w: 0.15 });
    }
    S.rooms = placeRooms(rooms, links);
    // cities first: a city's woodland fills its whole bounding box, so anything else is drawn over it.
    // Districts shown side by side (?stitch=0) keep the stitched city's stacking order
    const stacked = WorldModel.stackOrder(m.config, keys);
    S.order = stacked.filter(k => S.rooms[k].members).concat(stacked.filter(k => !S.rooms[k].members));
}

const THROUGH = 4;
const GAP = 4;
function placeRooms(rooms, links) {
    const keys = Object.keys(rooms);
    const byRoom = Object.fromEntries(keys.map(k => [k, []]));
    const weight = Object.fromEntries(keys.map(k => [k, 0]));
    for (const l of links) {
        byRoom[l.a].push(l);
        if (l.b !== l.a) byRoom[l.b].push(l);
        weight[l.a] += l.w;
        weight[l.b] += l.w;
    }
    const area = (k) => rooms[k].w * rooms[k].h;
    const overlaps = (k, x, y, placed) => {
        const r = rooms[k];
        for (const o of placed) {
            if (o === k) continue;
            const p = rooms[o];
            if (x < p.x + p.w + GAP && x + r.w + GAP > p.x && y < p.y + p.h + GAP && y + r.h + GAP > p.y) return true;
        }
        return false;
    };
    const linkCost = (l, placed) => {
        const a = rooms[l.a], b = rooms[l.b];
        const x1 = a.x + l.ax, y1 = a.y + l.ay, x2 = b.x + l.bx, y2 = b.y + l.by;
        const len = Math.hypot(x2 - x1, y2 - y1);
        let through = 0;
        for (const o of placed) through += clipLength(x1, y1, x2, y2, rooms[o]);
        return l.w * (len + THROUGH * through);
    };
    const roomCost = (k, placed) => byRoom[k].reduce((c, l) => c + (placed.has(l.a) && placed.has(l.b) ? linkCost(l, placed) : 0), 0);
    const movedCost = (moved) => {
        const touched = new Set();
        for (const k of moved) for (const l of byRoom[k]) touched.add(l);
        let c = 0;
        for (const l of touched) c += linkCost(l, placed);
        for (const l of links) {
            if (touched.has(l)) continue;
            const a = rooms[l.a], b = rooms[l.b];
            for (const k of moved) c += l.w * THROUGH * clipLength(a.x + l.ax, a.y + l.ay, b.x + l.bx, b.y + l.by, rooms[k]);
        }
        return c;
    };

    const placed = new Set();
    const spots = (k, others) => {
        const r = rooms[k], out = [];
        for (const o of others) {
            if (o === k) continue;
            const p = rooms[o];
            for (let y = p.y - r.h + 1; y < p.y + p.h; y += 2) out.push([p.x + p.w + GAP, y], [p.x - r.w - GAP, y]);
            for (let x = p.x - r.w + 1; x < p.x + p.w; x += 2) out.push([x, p.y + p.h + GAP], [x, p.y - r.h - GAP]);
        }
        return out;
    };
    const seed = keys.slice().sort((a, b) => weight[b] - weight[a] || area(b) - area(a))[0];
    placed.add(seed);
    while (placed.size < keys.length) {
        const pull = Object.fromEntries(keys.map(k => [k, 0]));
        for (const l of links) {
            if (placed.has(l.a) && !placed.has(l.b)) pull[l.b] += l.w;
            if (placed.has(l.b) && !placed.has(l.a)) pull[l.a] += l.w;
        }
        const k = keys.filter(k => !placed.has(k)).sort((a, b) => pull[b] - pull[a] || area(b) - area(a))[0];
        placed.add(k);
        let best = Infinity, bx = 0, by = 0;
        for (const [x, y] of spots(k, placed)) {
            if (overlaps(k, x, y, placed)) continue;
            rooms[k].x = x; rooms[k].y = y;
            const c = roomCost(k, placed) + (Math.abs(x) + Math.abs(y)) * 1e-3;
            if (c < best) { best = c; bx = x; by = y; }
        }
        rooms[k].x = bx; rooms[k].y = by;
    }

    let rand = 1234567;
    const random = () => (rand = (rand * 1103515245 + 12345) & 0x7fffffff) / 0x80000000;
    const pick = (list) => list[Math.floor(random() * list.length)];
    const steps = 12000;
    for (let i = 0; i < steps; i++) {
        const t = 1 - i / steps;
        const temp = 12 * t * t + 0.05;
        const k = pick(keys);
        const r = rooms[k];
        const move = random();
        const swap = move >= 0.85 ? pick(keys) : null;
        if (swap === k) continue;
        const s = swap ? rooms[swap] : null;
        const moved = swap ? [k, swap] : [k];
        const was = [r.x, r.y, s && s.x, s && s.y];
        const before = movedCost(moved);
        if (swap) {
            [r.x, r.y, s.x, s.y] = [s.x, s.y, r.x, r.y];
        } else if (move < 0.5) {
            const reach = Math.max(1, Math.round(8 * t));
            r.x += Math.round((random() * 2 - 1) * reach);
            r.y += Math.round((random() * 2 - 1) * reach);
        } else {
            const near = byRoom[k].length ? pick(byRoom[k]) : null;
            const o = near ? (near.a === k ? near.b : near.a) : pick(keys);
            [r.x, r.y] = pick(spots(k, [o]));
        }
        const ok = !overlaps(k, r.x, r.y, placed) && (!swap || !overlaps(swap, s.x, s.y, placed));
        const delta = ok ? movedCost(moved) - before : Infinity;
        if (delta > 0 && random() >= Math.exp(-delta / temp)) {
            [r.x, r.y] = was;
            if (swap) [s.x, s.y] = [was[2], was[3]];
        }
    }

    const minX = Math.min(...keys.map(k => rooms[k].x)), minY = Math.min(...keys.map(k => rooms[k].y));
    for (const k of keys) { rooms[k].x -= minX; rooms[k].y -= minY; }
    return rooms;
}

function clipLength(x1, y1, x2, y2, r) {
    const dx = x2 - x1, dy = y2 - y1;
    let t0 = 0, t1 = 1;
    for (const [p, q] of [[-dx, x1 - r.x], [dx, r.x + r.w - x1], [-dy, y1 - r.y], [dy, r.y + r.h - y1]]) {
        if (p === 0) { if (q < 0) return 0; continue; }
        const t = q / p;
        if (p < 0) { if (t > t1) return 0; if (t > t0) t0 = t; }
        else { if (t < t0) return 0; if (t < t1) t1 = t; }
    }
    return (t1 - t0) * Math.hypot(dx, dy);
}

function renderArt(k) {
    const r = S.rooms[k];
    const c = el('canvas', { width: r.w * ART, height: r.h * ART });
    const g = c.getContext('2d');
    g.imageSmoothingEnabled = false;
    g.fillStyle = '#000';
    g.fillRect(0, 0, c.width, c.height);
    for (const t of S.model.drawOrder(k)) {
        const im = S.images[t.key];
        g.drawImage(im, t.x * ART, t.y * ART, im.width * ART / 64, im.height * ART / 64);
    }
    return c;
}

function refresh() {
    const m = S.model;
    m.date = S.dates[S.dateIndex];
    $('date').textContent = formatGameDate(m.date);
    $('scrub').value = S.dateIndex;
    S.survey = m.survey();
    for (const k of S.order) S.rooms[k].npcs = m.npcsIn(k);
    panels();
    inspect();
    draw();
}

const sx = (cx) => (cx - S.view.x) * S.view.z;
const sy = (cy) => (cy - S.view.y) * S.view.z;

function draw() {
    const z = S.view.z;
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = COLOR.paper;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.textBaseline = 'alphabetic';

    for (const k of S.order) {
        const r = S.rooms[k];
        const x0 = sx(r.x), y0 = sy(r.y);
        if (S.show.art) ctx.drawImage(r.art, x0, y0, r.w * z, r.h * z);
        else { ctx.fillStyle = '#fff'; ctx.fillRect(x0, y0, r.w * z, r.h * z); }
        const cell = (key, fn) => { const [cx, cy] = key.split(',').map(Number); fn(x0 + cx * z, y0 + cy * z); };

        if (S.show.collision) {
            ctx.fillStyle = 'rgba(224, 66, 31, 0.5)';
            for (const key of r.blocked) cell(key, (px, py) => ctx.fillRect(px, py, z, z));
        }
        if (S.show.unreachable) {
            const reach = S.survey.reach[k] || new Set();
            ctx.fillStyle = 'rgba(27, 31, 59, 0.62)';
            for (let cy = 0; cy < r.h; cy++) for (let cx = 0; cx < r.w; cx++) {
                const key = cx + ',' + cy;
                if (!r.blocked.has(key) && !reach.has(key) && !r.outside.has(key)) ctx.fillRect(x0 + cx * z, y0 + cy * z, z, z);
            }
        }
        if (S.show.interactions) {
            ctx.lineWidth = Math.max(1.5, z / 8);
            for (const i of r.interactions) {
                ctx.strokeStyle = GROUP_COLOR[i.group];
                ctx.strokeRect(x0 + i.x * z + 1, y0 + i.y * z + 1, i.w * z - 2, i.h * z - 2);
            }
        }
        ctx.strokeStyle = COLOR.ink;
        ctx.lineWidth = 2;
        ctx.strokeRect(x0, y0, r.w * z, r.h * z);
        // the districts of a stitched city: where one map ends and the next begins
        ctx.setLineDash([6, 4]);
        ctx.lineWidth = 1;
        for (const mem of r.members || []) ctx.strokeRect(x0 + mem.x * z, y0 + mem.y * z, mem.w * z, mem.h * z);
        ctx.setLineDash([]);
    }

    if (S.show.teleports) {
        for (const k of S.order) {
            const r = S.rooms[k];
            for (const t of S.model.roomManager.rooms[k].transporters) {
                // a door's target is authored as (district, cell): where that is in the drawn room
                const at = S.model.roomManager.resolve(t.targetRoom, t.targetX, t.targetY);
                const to = S.rooms[at.room];
                if (!to) continue;
                const lit = S.selected && ((S.selected.room === k && S.selected.x === t.gridX && S.selected.y === t.gridY) ||
                    (S.selected.room === at.room && S.selected.x === at.x && S.selected.y === at.y));
                const near = S.selected && (S.selected.room === k || S.selected.room === at.room);
                ctx.globalAlpha = lit || near || !S.selected ? (lit ? 1 : near ? 0.9 : 0.45) : 0.12;
                arrow(sx(r.x + t.gridX + 0.5), sy(r.y + t.gridY + 0.5), sx(to.x + at.x + 0.5), sy(to.y + at.y + 0.5),
                    lit ? COLOR.torii : COLOR.moss, lit ? 3 : 1.5);
                ctx.globalAlpha = 1;
                ctx.fillStyle = COLOR.moss;
                ctx.fillRect(sx(r.x + t.gridX), sy(r.y + t.gridY), z, z);
            }
        }
        const stations = Object.entries(S.model.config.stations || {}).filter(([k]) => S.rooms[k]);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = COLOR.moat;
        ctx.lineWidth = 1.5;
        for (let i = 0; i < stations.length; i++) for (let j = i + 1; j < stations.length; j++) {
            const [a, sa] = stations[i], [b, sb] = stations[j];
            ctx.beginPath();
            ctx.moveTo(sx(S.rooms[a].x + sa.board[0][0] + 0.5), sy(S.rooms[a].y + sa.board[0][1] + 0.5));
            ctx.lineTo(sx(S.rooms[b].x + sb.board[0][0] + 0.5), sy(S.rooms[b].y + sb.board[0][1] + 0.5));
            ctx.stroke();
        }
        ctx.setLineDash([]);
        ctx.fillStyle = COLOR.moat;
        for (const [k, st] of stations) for (const [bx, by] of st.board) ctx.fillRect(sx(S.rooms[k].x + bx), sy(S.rooms[k].y + by), z, z);
    }

    if (S.show.people) {
        for (const k of S.order) {
            const r = S.rooms[k];
            for (const n of r.npcs) {
                const px = sx(r.x + n.gridX), py = sy(r.y + n.gridY);
                const size = Math.max(z, 22);
                const im = S.images[n.name.toLowerCase() + '_front_frame_0'];
                ctx.fillStyle = COLOR.sun;
                ctx.fillRect(px + z / 2 - size / 2 - 2, py + z - size - 2, size + 4, size + 4);
                if (im) ctx.drawImage(im, px + z / 2 - size / 2, py + z - size, size, size);
                ctx.font = 'bold 14px Pixel, monospace';
                const w = ctx.measureText(n.name).width;
                ctx.fillStyle = COLOR.ink;
                ctx.fillRect(px + z / 2 - w / 2 - 4, py + z + 3, w + 8, 16);
                ctx.fillStyle = COLOR.paper;
                ctx.fillText(n.name, px + z / 2 - w / 2, py + z + 15);
            }
        }
    }

    ctx.font = `bold ${Math.max(13, Math.min(20, z * 2.2))}px Pixel, monospace`;
    const tag = (name, cx, cy) => {
        const w = ctx.measureText(name).width, h = parseInt(ctx.font.slice(5), 10) + 6;
        ctx.fillStyle = COLOR.ink;
        ctx.fillRect(sx(cx), sy(cy), w + 12, h);
        ctx.fillStyle = COLOR.paper;
        ctx.fillText(name, sx(cx) + 6, sy(cy) + h - 6);
    };
    for (const k of S.order) {
        const r = S.rooms[k];
        // a city is named by its districts, each at its own corner
        if (r.members) for (const mem of r.members) tag(mem.key, r.x + mem.x, r.y + mem.y);
        else tag(k, r.x, r.y);
    }

    ctx.strokeStyle = COLOR.torii;
    ctx.lineWidth = 3;
    for (const p of S.survey.problems) {
        if (p.x === undefined) continue;
        const r = S.rooms[p.room];
        ctx.beginPath();
        ctx.arc(sx(r.x + p.x + 0.5), sy(r.y + p.y + 0.5), Math.max(z, 9), 0, Math.PI * 2);
        ctx.stroke();
    }

    if (S.selected) {
        const r = S.rooms[S.selected.room];
        ctx.strokeStyle = COLOR.torii;
        ctx.lineWidth = 3;
        ctx.strokeRect(sx(r.x + S.selected.x) - 1, sy(r.y + S.selected.y) - 1, z + 2, z + 2);
    }
}

function arrow(x1, y1, x2, y2, color, width) {
    const a = Math.atan2(y2 - y1, x2 - x1), h = 8 + width * 2;
    ctx.strokeStyle = ctx.fillStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - h * Math.cos(a - 0.4), y2 - h * Math.sin(a - 0.4));
    ctx.lineTo(x2 - h * Math.cos(a + 0.4), y2 - h * Math.sin(a + 0.4));
    ctx.fill();
}

function panels() {
    const { problems } = S.survey;
    const count = $('problem-count');
    count.textContent = problems.length;
    count.className = 'badge ' + (problems.length ? 'bad' : 'good');
    $('problems').replaceChildren(...problems.map(p => {
        const b = el('button', { className: 'row' },
            el('span', { textContent: p.text }),
            el('span', { className: 'dim', textContent: p.where || p.room }));
        b.onclick = () => p.x === undefined ? focusRoom(p.room) : select(p.room, p.x, p.y, true);
        return b;
    }));
    // one row per room as authored: a city lists its districts (and, last, itself)
    const rows = [];
    const row = (name, w, h, npcs, go) => {
        const b = el('button', { className: 'row' },
            el('span', { textContent: name }),
            el('span', { className: 'dim', textContent: `${w}x${h}` + (npcs.length ? ` (${npcs.map(n => n.name).join(', ')})` : '') }));
        b.onclick = go;
        rows.push(b);
    };
    // listed in config order, whatever the stacking order is
    for (const k of S.model.runtimeRooms()) {
        const r = S.rooms[k];
        for (const mem of r.members || []) {
            row(mem.key, mem.w, mem.h, r.npcs.filter(n => n.homeRoom === mem.key),
                () => focusRect(r.x + mem.x, r.y + mem.y, mem.w, mem.h));
        }
        row(r.members ? `${k} (stitched)` : k, r.w, r.h, r.members ? [] : r.npcs, () => focusRoom(k));
    }
    $('rooms').replaceChildren(...rows);
}

function inspect() {
    const box = $('inspector');
    const sel = S.selected;
    box.hidden = !sel;
    if (!sel) return;
    const m = S.model;
    m.enter(sel.room, sel.x, sel.y);
    const key = sel.x + ',' + sel.y;
    const inside = m.roomManager.checkBoundary(sel.x, sel.y);
    const reach = (S.survey.reach[sel.room] || new Set()).has(key);
    const person = S.rooms[sel.room].npcs.some(n => n.gridX === sel.x && n.gridY === sel.y);
    const state = !inside ? ['outside the boundary', 'bad'] : m.blocked.has(key) ? ['blocked', 'bad']
        : person ? ['occupied', ''] : reach ? ['walkable', 'good'] : ['unreachable', 'bad'];
    // named the way config and the maps name it: the district's own cell inside a stitched city
    const local = m.roomManager.districtsAt(sel.x, sel.y, sel.room)[0] || sel;
    const parts = [el('h2', {}, el('span', { textContent: `${local.room} ${local.x},${local.y}` }), el('span', { className: 'badge ' + state[1], textContent: state[0] }))];
    if (local.room !== sel.room) parts.push(el('div', { className: 'row' }, el('span', { textContent: `${sel.room} ${sel.x},${sel.y}` }), el('span', { className: 'dim', textContent: 'stitched city cell' })));

    const t = m.room.transporters.find(t => t.gridX === sel.x && t.gridY === sel.y);
    if (t) {
        const go = el('button', { className: 'row' }, el('span', { textContent: `→ ${t.targetRoom} ${t.targetX},${t.targetY}` }), el('span', { className: 'dim', textContent: t.hidden ? 'hidden door' : 'transporter' }));
        const dest = m.roomManager.resolve(t.targetRoom, t.targetX, t.targetY);
        go.onclick = () => select(dest.room, dest.x, dest.y, true);
        parts.push(go);
    }
    for (const k of S.order) {
        for (const from of m.roomManager.rooms[k].transporters) {
            const dest = m.roomManager.resolve(from.targetRoom, from.targetX, from.targetY);
            if (dest.room !== sel.room || dest.x !== sel.x || dest.y !== sel.y) continue;
            const back = el('button', { className: 'row' }, el('span', { textContent: `← ${m.spot(k, from.gridX, from.gridY)}` }), el('span', { className: 'dim', textContent: 'arrives here' }));
            back.onclick = () => select(k, from.gridX, from.gridY, true);
            parts.push(back);
        }
    }
    if (m.onBoardCell()) parts.push(el('div', { className: 'row' }, el('span', { textContent: 'train boarding' }), el('span', { className: 'dim', textContent: 'any other station' })));

    const i = m.interactionAt(sel.x, sel.y);
    if (i && i.kind === 'npc') {
        parts.push(el('h2', {}, el('span', { textContent: i.npc.name })));
        if (i.npc.photo) parts.push(el('img', { className: 'photo', src: `../assets/photos/${i.npc.photo}.png` }));
        for (const line of i.npc.dialogue) parts.push(el('blockquote', { textContent: line }));
    } else if (i) {
        parts.push(el('dl', { className: 'kv' }, el('dt', { textContent: 'bump' }), el('dd', { textContent: m.describe(i) })));
    }

    const tiles = m.tilesAt(sel.x, sel.y);
    parts.push(el('ul', { className: 'tiles' }, ...tiles.map(tile => el('li', { className: tile.collision ? 'solid' : '' },
        `${tile.layer} z${tile.z}: ${tile.key}` + (tile.at[0] !== sel.x || tile.at[1] !== sel.y ? ` (from ${tile.at.join(',')})` : '')))));

    const cmd = `node tools/play.js warp ${local.room} ${local.x} ${local.y}`;
    const code = el('code', { textContent: cmd });
    code.onclick = () => navigator.clipboard && navigator.clipboard.writeText(cmd);
    parts.push(code);
    box.replaceChildren(...parts);
}

function select(room, x, y, pan) {
    S.selected = { room, x, y };
    if (pan) {
        const r = S.rooms[room];
        S.view.z = Math.max(S.view.z, 14);
        S.view.x = r.x + x + 0.5 - stage.clientWidth / 2 / S.view.z;
        S.view.y = r.y + y + 0.5 - stage.clientHeight / 2 / S.view.z;
    }
    inspect();
    draw();
}

function focusRoom(k) {
    const r = S.rooms[k];
    focusRect(r.x, r.y, r.w, r.h);
}

function focusRect(x, y, w, h) {
    S.view.z = Math.min(stage.clientWidth / (w + 4), stage.clientHeight / (h + 6));
    S.view.x = x + w / 2 - stage.clientWidth / 2 / S.view.z;
    S.view.y = y + h / 2 - stage.clientHeight / 2 / S.view.z;
    draw();
}

function fit() {
    const all = Object.values(S.rooms);
    const w = Math.max(...all.map(r => r.x + r.w)), h = Math.max(...all.map(r => r.y + r.h));
    S.view.z = Math.min(stage.clientWidth / (w + 6), stage.clientHeight / (h + 8));
    S.view.x = w / 2 - stage.clientWidth / 2 / S.view.z;
    S.view.y = h / 2 - 2 - stage.clientHeight / 2 / S.view.z;
}

function resize() {
    canvas.width = stage.clientWidth * devicePixelRatio;
    canvas.height = stage.clientHeight * devicePixelRatio;
    canvas.style.width = stage.clientWidth + 'px';
    canvas.style.height = stage.clientHeight + 'px';
    draw();
}

function bind() {
    const step = (d) => { S.dateIndex = Math.max(0, Math.min(S.dates.length - 1, S.dateIndex + d)); refresh(); };
    $('prev').onclick = () => step(-1);
    $('next').onclick = () => step(1);
    $('scrub').oninput = (e) => { S.dateIndex = Number(e.target.value); refresh(); };
    $('as').onchange = (e) => { S.model.as = e.target.value; refresh(); };
    window.addEventListener('resize', resize);

    let drag = null;
    stage.addEventListener('pointerdown', (e) => {
        drag = { x: e.clientX, y: e.clientY, vx: S.view.x, vy: S.view.y, moved: false };
        stage.setPointerCapture(e.pointerId);
    });
    stage.addEventListener('pointermove', (e) => {
        if (!drag) return;
        if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 4) drag.moved = true;
        if (!drag.moved) return;
        stage.classList.add('dragging');
        S.view.x = drag.vx - (e.clientX - drag.x) / S.view.z;
        S.view.y = drag.vy - (e.clientY - drag.y) / S.view.z;
        draw();
    });
    stage.addEventListener('pointerup', (e) => {
        stage.classList.remove('dragging');
        const was = drag;
        drag = null;
        if (!was || was.moved) return;
        const box = stage.getBoundingClientRect();
        const cx = S.view.x + (e.clientX - box.left) / S.view.z, cy = S.view.y + (e.clientY - box.top) / S.view.z;
        const cell = (k) => ({ room: k, x: Math.floor(cx - S.rooms[k].x), y: Math.floor(cy - S.rooms[k].y) });
        const under = S.order.filter(k => { const r = S.rooms[k]; return cx >= r.x && cx < r.x + r.w && cy >= r.y && cy < r.y + r.h; }).map(cell);
        // the room drawn on top takes the click (a later district over an earlier one, a town over
        // a city's box); clicking the selected cell again picks the room underneath
        const hit = WorldModel.stackPick(under, S.selected);
        if (hit) select(hit.room, hit.x, hit.y, false);
        else { S.selected = null; inspect(); draw(); }
    });
    stage.addEventListener('wheel', (e) => {
        e.preventDefault();
        const box = stage.getBoundingClientRect();
        const mx = e.clientX - box.left, my = e.clientY - box.top;
        const wx = S.view.x + mx / S.view.z, wy = S.view.y + my / S.view.z;
        S.view.z = Math.max(1.5, Math.min(64, S.view.z * Math.exp(-e.deltaY * 0.0015)));
        S.view.x = wx - mx / S.view.z;
        S.view.y = wy - my / S.view.z;
        draw();
    }, { passive: false });
}

boot().catch((e) => { $('loading').textContent = 'failed to load: ' + e.message; throw e; });
