const ART = 32;
const COLOR = { torii: '#e0421f', moat: '#2f5fd0', moss: '#2f8f5b', sun: '#f2b01e', ink: '#1b1f3b', paper: '#f4efe4' };
const GROUP_COLOR = { shop: COLOR.sun, pond: COLOR.moat, clock: '#9b4fd0', 'drinking-game': '#d04f9b' };
const LAYERS = [
    ['art', 'Art', true], ['collision', 'Collision', false], ['unreachable', 'Unreachable', true],
    ['teleports', 'Teleports', true], ['trains', 'Train lines', false], ['interactions', 'Interactions', true], ['people', 'People', true],
];

const $ = (id) => document.getElementById(id);
const canvas = $('view');
const ctx = canvas.getContext('2d');
const stage = $('stage');

const S = {
    model: null, images: {}, rooms: {}, order: [], dates: [], dateIndex: 0,
    show: Object.fromEntries(LAYERS.map(([k, , on]) => [k, on])),
    view: { x: 0, y: 0, z: 6 }, selected: null, survey: { problems: [], reach: {} },
    source: null, files: {}, prefabs: [], people: {}, stale: new Set(), worldMap: null,
    edit: null, tool: 'select', arm: null, hover: null, linkFrom: null, retarget: null, active: 0,
    paint: null, moving: null, changes: [], note: '', noteBad: false,
};
const TOOLS = [['select', 'Select'], ['solid', 'Solid'], ['link', 'Link']];
// The game stitches the districts of config `cities` into one room, and the studio draws that
// room. ?stitch=0 (as in the game) shows them as the separate rooms joined by seam teleports.
let STITCH = new URLSearchParams(location.search).get('stitch') !== '0';

const bust = Date.now();
const web = {
    text: (p) => fetch(`../${p}?t=${bust}`).then(r => r.ok ? r.text() : null).catch(() => null),
    image: async (key) => `../assets/sprites/${key}.png`,
};
function folder(dir) {
    const file = async (p) => {
        const parts = p.split('/');
        let d = dir;
        for (const part of parts.slice(0, -1)) d = await d.getDirectoryHandle(part);
        return d.getFileHandle(parts[parts.length - 1]);
    };
    return {
        text: (p) => file(p).then(h => h.getFile()).then(f => f.text()).catch(() => null),
        image: (key) => file(`assets/sprites/${key}.png`).then(h => h.getFile()).then(f => URL.createObjectURL(f)).catch(() => `../assets/sprites/${key}.png`),
        write: async (p, text) => {
            const w = await (await file(p)).createWritable();
            await w.write(text);
            await w.close();
        },
        list: async (p) => {
            let d = dir;
            for (const part of p.split('/')) d = await d.getDirectoryHandle(part);
            const names = [];
            for await (const name of d.keys()) names.push(name);
            return names.sort();
        },
    };
}
const loadImage = async (key) => {
    if (S.images[key]) return;
    const src = await S.source.image(key);
    await new Promise((resolve) => {
        const im = new Image();
        im.onload = () => { S.images[key] = im; resolve(); };
        im.onerror = () => resolve();
        im.src = src;
    });
};
const tmjPath = (k) => `tiled/${k.toLowerCase()}.tmj`;
const env = {
    exists: (key) => !!S.images[key],
    sizeOf: (key) => {
        const im = S.images[key];
        return im ? [Math.max(1, Math.round(im.width / 64)), Math.max(1, Math.round(im.height / 64))] : [1, 1];
    },
    pixels: (key) => [S.images[key].width, S.images[key].height],
};
const el = (tag, props, ...kids) => {
    const node = Object.assign(document.createElement(tag), props || {});
    for (const kid of kids) node.append(kid);
    return node;
};

function world() {
    const config = decodeConfig(structuredClone(S.files['config.json'].doc));
    WorldModel.applyTiled(config, (k) => S.files[tmjPath(k)] && S.files[tmjPath(k)].doc);
    return config;
}

async function load(source) {
    S.source = source;
    S.files = {};
    S.images = {};
    const open = async (p, indent) => {
        const text = await source.text(p);
        if (text !== null) S.files[p] = { doc: Edit.parse(text), indent };
    };
    await open('config.json', 2);
    if (!S.files['config.json']) throw new Error('config.json is missing');
    const keys = Object.keys(S.files['config.json'].doc.rooms);
    await Promise.all(keys.map(k => open(tmjPath(k), 1)));
    S.worldMap = JSON.parse(await source.text('assets/map/world-map.json') || '{"rooms":{}}');

    S.prefabs = [];
    if (source.list) {
        for (const name of await source.list('tiled/prefabs')) {
            if (!name.endsWith('.tmj')) continue;
            S.prefabs.push(Edit.prefab(name.slice(0, -4), Edit.parse(await source.text('tiled/prefabs/' + name))));
        }
    }

    const config = world();
    const sprites = new Set(['gk_blank']);
    const draft = new WorldModel(config, env, null, { stitch: STITCH, worldMap: S.worldMap });
    for (const room of Object.values(draft.roomManager.rooms)) {
        for (const layer of room.layers || []) for (const key of Object.values(layer.tiles || {})) sprites.add(key);
    }
    for (const room of Object.values(config.rooms)) {
        for (const npc of room.npcs || []) sprites.add(npc.sprite + '_frame_0');
    }
    for (const pf of S.prefabs) for (const sp of pf.sprites) sprites.add(sp.key);
    await Promise.all([...sprites].map(loadImage));

    const days = new Set(contentChangeDates(config));
    for (const trip of Trips.of(config)) {
        days.add(trip.start);
        for (const stay of trip.stays) days.add(stay.from);
    }
    S.dates = [...days].sort();
    S.changes = [];
    S.selected = null;
    S.model = null;
    build(true);

    const today = S.model.date;
    if (!S.dates.includes(today)) S.dates.push(today);
    S.dates.sort();
    S.dateIndex = S.dates.indexOf(today);
    $('scrub').max = S.dates.length - 1;

    const cast = new Set([baseOf(config.player.sprite)]);
    for (const room of Object.values(config.rooms)) for (const npc of room.npcs || []) cast.add(baseOf(npc.sprite));
    $('as').replaceChildren(...[...cast].map(name => el('option', { value: name, textContent: 'as ' + name })));
    $('as').value = S.model.as;

    const cities = config.cities && Object.keys(config.cities).length;
    $('stitch').hidden = !cities || !!source.write;
    $('stitch').setAttribute('aria-pressed', STITCH);
}

function build(first) {
    const prev = S.model;
    S.model = new WorldModel(world(), env, prev ? { date: prev.date, as: prev.as } : null, { stitch: STITCH, worldMap: S.worldMap });
    const m = S.model;
    const shown = m.runtimeRooms();
    if (first) layout(shown);
    for (const k of shown) {
        const r = m.roomManager.rooms[k];
        const room = S.rooms[k];
        room.w = r.worldWidth / 64;
        room.h = r.worldHeight / 64;
        m.enter(k, 0, 0);
        Object.assign(room, { blocked: m.blocked, interactions: m.interactions(), npcs: room.npcs || [] });
        if (first || S.stale.has(k)) room.art = renderArt(k);
        // the woodland between a city's districts is scenery, not unreachable floor
        room.outside = new Set();
        if (room.members) {
            for (let y = 0; y < room.h; y++) for (let x = 0; x < room.w; x++) if (!m.roomManager.checkBoundary(x, y)) room.outside.add(x + ',' + y);
        }
    }
    S.stale.clear();
    S.people = {};
}

async function boot() {
    await load(web);
    $('stitch').onclick = () => { location.search = STITCH ? '?stitch=0' : ''; };
    for (const [key, label] of LAYERS) {
        const b = el('button', { textContent: label });
        b.setAttribute('aria-pressed', S.show[key]);
        b.onclick = () => {
            S.show[key] = !S.show[key];
            b.setAttribute('aria-pressed', S.show[key]);
            if (key === 'teleports' || key === 'trains') { layout(S.model.runtimeRooms()); fit(); }
            draw();
        };
        $('layers').append(b);
    }
    for (const [key, label] of TOOLS) {
        const b = el('button', { textContent: label });
        b.dataset.tool = key;
        b.onclick = () => setTool(key);
        $('tools').append(b);
    }
    $('edit').hidden = !window.showDirectoryPicker;
    bind();
    resize();
    fit();
    refresh();
    $('loading').hidden = true;
}

async function startEdit() {
    let picked;
    try { picked = await window.showDirectoryPicker({ mode: 'readwrite' }); } catch (e) { return; }
    let root = picked, repo = null;
    try { root = await picked.getDirectoryHandle('gamev2'); repo = picked; } catch (e) { root = picked; }
    try {
        await root.getFileHandle('config.json');
        await root.getDirectoryHandle('tiled');
    } catch (e) {
        $('source').textContent = `No gamev2/config.json in "${picked.name}"`;
        $('source').className = 'badge bad';
        $('source').hidden = false;
        return;
    }
    let branch = '';
    try {
        const head = await (await (await (await repo.getDirectoryHandle('.git')).getFileHandle('HEAD')).getFile()).text();
        const ref = /ref: refs\/heads\/(.+)/.exec(head);
        branch = ref ? ref[1].trim() : head.slice(0, 7);
    } catch (e) { branch = ''; }
    $('loading').hidden = false;
    STITCH = false;
    try {
        await load(folder(root));
    } catch (e) {
        $('loading').textContent = 'failed to load: ' + e.message;
        throw e;
    }
    S.edit = { name: picked.name, branch };
    $('where').textContent = picked.name + (branch ? ` (${branch})` : '');
    $('source').hidden = true;
    $('edit').hidden = true;
    $('rail').hidden = false;
    $('changes').hidden = false;
    setTool('select');
    resize();
    fit();
    refresh();
    $('loading').hidden = true;
}

function setTool(tool) {
    S.tool = tool;
    S.arm = S.linkFrom = S.retarget = null;
    for (const b of $('tools').children) b.setAttribute('aria-pressed', b.dataset.tool === tool);
    library();
    cursor();
    draw();
}

function cursor() {
    stage.style.cursor = S.moving ? 'move' : S.edit && (S.arm || S.retarget || S.tool !== 'select') ? 'crosshair' : '';
}

const docOf = (k) => S.files[tmjPath(k)] && S.files[tmjPath(k)].doc;
function peopleOf(k) {
    if (S.people[k]) return S.people[k];
    const m = S.model, out = [];
    for (const date of S.dates) {
        for (const raw of S.files['config.json'].doc.rooms[k].npcs || []) {
            const r = resolveNpc(raw, date, m.trips);
            if (r) out.push({ name: r.name, date, x: r.gridX !== null ? r.gridX : m.cx + r.gridOffsetX, y: r.gridY !== null ? r.gridY : m.cy + r.gridOffsetY });
        }
    }
    return (S.people[k] = out);
}
const ctxOf = (k) => ({ sizeOf: env.sizeOf, pixels: env.pixels, people: peopleOf(k) });
const cellName = (k, x, y) => `${k} (${x}, ${y})`;

function say(text, bad) {
    S.note = text;
    S.noteBad = !!bad;
    changes();
}

function restore(before) {
    for (const [p, text] of Object.entries(before)) S.files[p].doc = Edit.parse(text);
}

function change(rooms, fn, config) {
    const paths = rooms.map(tmjPath).concat(config ? ['config.json'] : []);
    const missing = paths.find(p => !S.files[p]);
    if (missing) return say(`${missing} is missing`, true);
    const before = Object.fromEntries(paths.map(p => [p, Edit.stringify(S.files[p].doc, S.files[p].indent)]));
    try {
        S.changes.push({ text: fn(), before, rooms });
    } catch (e) {
        restore(before);
        return say(e.message, true);
    }
    S.note = '';
    for (const k of rooms) S.stale.add(k);
    build(false);
    refresh();
    return true;
}

function undo() {
    const last = S.changes.pop();
    if (!last) return;
    restore(last.before);
    for (const k of last.rooms) S.stale.add(k);
    S.note = '';
    build(false);
    refresh();
}

async function save() {
    const paths = [...new Set(S.changes.flatMap(c => Object.keys(c.before)))];
    if (!paths.length) return;
    try {
        for (const p of paths) await S.source.write(p, Edit.stringify(S.files[p].doc, S.files[p].indent));
    } catch (e) {
        return say('Could not save: ' + e.message, true);
    }
    S.changes = [];
    say(`Saved ${paths.length} ${paths.length === 1 ? 'file' : 'files'}: ${paths.join(', ')}`);
}

function changes() {
    if (!S.edit) return;
    const n = S.changes.length;
    const rows = S.changes.map((c, i) => el('div', { className: 'change' }, el('span', { className: 'dim', textContent: i + 1 }), el('span', { textContent: c.text })));
    const undoButton = el('button', { textContent: 'Undo', disabled: !n });
    const saveButton = el('button', { className: 'go', textContent: 'Save', disabled: !n });
    undoButton.onclick = undo;
    saveButton.onclick = save;
    $('changes').replaceChildren(
        el('h2', {}, el('span', { textContent: 'Changes' }), el('span', { className: 'badge', textContent: n })),
        ...rows,
        ...(S.note ? [el('div', { className: S.noteBad ? 'note bad' : 'note', textContent: S.note })] : []),
        el('div', { className: 'actions' }, undoButton, saveButton));
}

function library() {
    if (!S.edit) return;
    const q = $('search').value.trim().toLowerCase();
    $('library').replaceChildren(...S.prefabs.filter(pf => pf.name.includes(q)).map(pf => {
        const main = pf.sprites.slice().sort((a, b) => env.sizeOf(b.key)[0] * env.sizeOf(b.key)[1] - env.sizeOf(a.key)[0] * env.sizeOf(a.key)[1])[0];
        const im = main && S.images[main.key];
        const b = el('button', { className: 'asset' },
            im ? el('img', { src: im.src, alt: '' }) : el('span', {}),
            el('span', {}, el('span', { textContent: pf.name }), el('span', { className: 'dim', textContent: `${pf.w}x${pf.h}` + (pf.doors.length ? ', door' : '') })));
        b.setAttribute('aria-pressed', S.arm === pf);
        b.onclick = () => {
            const next = S.arm === pf ? null : pf;
            setTool('select');
            S.arm = next;
            library();
            cursor();
            draw();
        };
        return b;
    }));
}

function thingsAt(sel) {
    const doc = docOf(sel.room);
    const list = [];
    for (const n of S.rooms[sel.room].npcs) if (n.gridX === sel.x && n.gridY === sel.y) list.push({ type: 'npc', name: n.name, x: n.gridX, y: n.gridY, w: 1, h: 1, label: n.name, kind: 'person' });
    if (!doc) return list;
    const t = Edit.transporters(doc).find(t => t.x === sel.x && t.y === sel.y);
    if (t) list.push({ type: 'door', t, x: t.x, y: t.y, w: 1, h: 1, label: `door to ${t.targetRoom}`, kind: t.hidden ? 'hidden door' : 'door' });
    for (const s of Edit.thingsAt(doc, sel.x, sel.y, ctxOf(sel.room))) {
        const [w, h] = env.sizeOf(s.key);
        list.push({ type: 'sprite', s, x: s.x, y: s.y, w, h, label: s.key, kind: s.layer });
    }
    return list;
}
const activeThing = () => {
    if (!S.edit || !S.selected) return null;
    const list = thingsAt(S.selected);
    return list[Math.min(S.active, list.length - 1)] || null;
};

function removeActive() {
    const thing = activeThing(), sel = S.selected;
    if (!thing || thing.type === 'npc') return;
    change([sel.room], () => {
        if (thing.type === 'door') {
            Edit.removeTransporter(docOf(sel.room), thing.t);
            return `Removed the door at ${cellName(sel.room, thing.x, thing.y)}`;
        }
        Edit.removeSprite(docOf(sel.room), thing.s, ctxOf(sel.room));
        return `Removed ${thing.label} from ${cellName(sel.room, thing.x, thing.y)}`;
    });
}

function moveActive(thing, room, x, y) {
    if (thing.type === 'npc') {
        const date = S.model.date;
        return change([], () => {
            const dated = Edit.moveNpc(S.files['config.json'].doc, room, thing.name, date, x, y);
            return `Moved ${thing.name} to ${cellName(room, x, y)}` + (dated ? ` from ${formatGameDate(date)}` : '');
        }, true);
    }
    return change([room], () => {
        if (thing.type === 'door') Edit.moveTransporter(thing.t, x, y);
        else Edit.moveSprite(docOf(room), thing.s, x, y, ctxOf(room));
        return `Moved ${thing.label}, ${cellName(room, thing.x, thing.y)} to (${x}, ${y})`;
    });
}

function place(pf, c) {
    const x = c.x - Math.floor(pf.w / 2), y = c.y - pf.h + 1;
    change([c.room], () => {
        Edit.stamp(docOf(c.room), pf, x, y, ctxOf(c.room));
        return `Placed ${pf.name} at ${cellName(c.room, x, y)}`;
    });
}

function paintSolid(paint) {
    const cells = [...paint.cells].map(c => c.split(',').map(Number));
    change([paint.room], () => {
        for (const [x, y] of cells) Edit.setSolid(docOf(paint.room), x, y, paint.on);
        const where = cells.length === 1 ? cellName(paint.room, cells[0][0], cells[0][1]) : `${cells.length} cells in ${paint.room}`;
        return paint.on ? `Made ${where} solid` : `Opened ${where}`;
    });
}

function linkCells(a, b) {
    const rooms = a.room === b.room ? [a.room] : [a.room, b.room];
    change(rooms, () => {
        const end = (c) => {
            const r = S.rooms[c.room], reach = S.survey.reach[c.room] || new Set();
            const open = (x, y) => reach.size ? reach.has(x + ',' + y) : x >= 0 && y >= 0 && x < r.w && y < r.h && !r.blocked.has(x + ',' + y);
            return { ...c, doc: docOf(c.room), open };
        };
        Edit.link(end(a), end(b));
        return `Linked ${cellName(a.room, a.x, a.y)} \u21c4 ${cellName(b.room, b.x, b.y)}`;
    });
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
    if (S.show.teleports) for (const k of keys) {
        for (const t of m.roomManager.rooms[k].transporters) {
            const at = m.roomManager.resolve(t.targetRoom, t.targetX, t.targetY);
            if (!rooms[at.room]) continue;
            links.push({ a: k, ax: t.gridX + 0.5, ay: t.gridY + 0.5, b: at.room, bx: at.x + 0.5, by: at.y + 0.5, w: 1 });
        }
    }
    const stations = S.show.trains ? Object.entries(m.config.stations || {}).filter(([k]) => rooms[k]) : [];
    for (let i = 0; i < stations.length; i++) for (let j = i + 1; j < stations.length; j++) {
        const [a, sa] = stations[i], [b, sb] = stations[j];
        links.push({ a, ax: sa.board[0][0] + 0.5, ay: sa.board[0][1] + 0.5, b, bx: sb.board[0][0] + 0.5, by: sb.board[0][1] + 0.5, w: 0.15 });
    }
    const placed = placeRooms(rooms, links);
    for (const k of keys) S.rooms[k] = Object.assign(S.rooms[k] || {}, placed[k]);
    // cities first: a city's woodland fills its whole bounding box, so anything else is drawn over it.
    // Districts shown side by side (?stitch=0) keep the stitched city's stacking order
    const stacked = WorldModel.stackOrder(m.config, keys);
    S.order = stacked.filter(k => S.rooms[k].members).concat(stacked.filter(k => !S.rooms[k].members));
}

const THROUGH = 4;
const CROSS = 8;
const GAP = 4;
function placeRooms(rooms, links) {
    const keys = Object.keys(rooms);
    const byRoom = Object.fromEntries(keys.map(k => [k, []]));
    const weight = Object.fromEntries(keys.map(k => [k, 0]));
    const pairKey = (l) => [l.a, l.b].sort().join('\u0000');
    const bundle = {};
    for (const l of links) bundle[pairKey(l)] = (bundle[pairKey(l)] || 0) + 1;
    links.forEach((l, i) => {
        l.i = i;
        l.n = bundle[pairKey(l)];
        byRoom[l.a].push(l);
        if (l.b !== l.a) byRoom[l.b].push(l);
        weight[l.a] += l.w;
        weight[l.b] += l.w;
    });
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
    const live = (l) => placed.has(l.a) && placed.has(l.b);
    const ends = (l) => [rooms[l.a].x + l.ax, rooms[l.a].y + l.ay, rooms[l.b].x + l.bx, rooms[l.b].y + l.by];
    const crossCost = (touched) => {
        const E = links.map(l => live(l) ? ends(l) : null);
        let c = 0;
        for (const l of touched) {
            if (!E[l.i]) continue;
            for (const o of links) {
                if (o === l || !E[o.i] || (touched.has(o) && o.i < l.i)) continue;
                if ((o.a === l.a && o.b === l.b) || (o.a === l.b && o.b === l.a)) continue;
                if (crosses(E[l.i], E[o.i])) c += CROSS * Math.min(l.w, o.w) / (l.n * o.n);
            }
        }
        return c;
    };
    const roomCost = (k, placed) => byRoom[k].reduce((c, l) => c + (live(l) ? linkCost(l, placed) : 0), 0);
    const movedCost = (moved) => {
        const touched = new Set();
        for (const k of moved) for (const l of byRoom[k]) touched.add(l);
        let c = crossCost(touched);
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
        const sibling = () => {
            const near = byRoom[k].length ? pick(byRoom[k]) : null;
            const o = near ? (near.a === k ? near.b : near.a) : null;
            const l = o ? pick(byRoom[o]) : null;
            return l ? (l.a === o ? l.b : l.a) : pick(keys);
        };
        const swap = move >= 0.85 ? (move < 0.93 ? sibling() : pick(keys)) : null;
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
            if (o === k) continue;
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

function crosses([ax, ay, bx, by], [cx, cy, dx, dy]) {
    const same = (x1, y1, x2, y2) => x1 === x2 && y1 === y2;
    if (same(ax, ay, cx, cy) || same(ax, ay, dx, dy) || same(bx, by, cx, cy) || same(bx, by, dx, dy)) return false;
    const turn = (px, py, qx, qy, rx, ry) => Math.sign((qx - px) * (ry - py) - (qy - py) * (rx - px));
    return turn(ax, ay, bx, by, cx, cy) * turn(ax, ay, bx, by, dx, dy) < 0 && turn(cx, cy, dx, dy, ax, ay) * turn(cx, cy, dx, dy, bx, by) < 0;
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
    changes();
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

        if (S.show.collision || (S.edit && S.tool === 'solid')) {
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
    }

    if (S.show.trains) {
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
    if (S.edit) overlay();
}

function overlay() {
    const z = S.view.z;
    const box = (k, x, y, w, h, color, dash) => {
        const r = S.rooms[k];
        ctx.setLineDash(dash || []);
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(sx(r.x + x), sy(r.y + y), w * z, h * z);
        ctx.setLineDash([]);
    };
    const label = (k, x, y, text, color) => {
        const r = S.rooms[k];
        ctx.font = 'bold 14px Pixel, monospace';
        const w = ctx.measureText(text).width;
        ctx.fillStyle = color;
        ctx.fillRect(sx(r.x + x), sy(r.y + y) - 20, w + 10, 18);
        ctx.fillStyle = COLOR.paper;
        ctx.fillText(text, sx(r.x + x) + 5, sy(r.y + y) - 6);
    };

    const thing = !S.moving && !S.arm && activeThing();
    if (thing) box(S.selected.room, thing.x, thing.y, thing.w, thing.h, COLOR.ink, [6, 4]);

    if (S.paint) {
        const r = S.rooms[S.paint.room];
        ctx.fillStyle = S.paint.on ? 'rgba(224, 66, 31, 0.75)' : 'rgba(47, 143, 91, 0.75)';
        for (const key of S.paint.cells) {
            const [cx, cy] = key.split(',').map(Number);
            ctx.fillRect(sx(r.x + cx), sy(r.y + cy), z, z);
        }
    }
    if (S.moving) {
        const m = S.moving;
        box(m.room, m.x, m.y, m.thing.w, m.thing.h, COLOR.sun);
        label(m.room, m.x, m.y, `${m.x}, ${m.y}`, COLOR.ink);
    }
    if (S.arm && S.hover) {
        const pf = S.arm, c = S.hover, r = S.rooms[c.room];
        const x = c.x - Math.floor(pf.w / 2), y = c.y - pf.h + 1;
        const doc = docOf(c.room);
        const refused = doc ? Edit.checkStamp(doc, pf, x, y, ctxOf(c.room)) : 'No map file for this room';
        ctx.globalAlpha = 0.75;
        for (const sp of pf.sprites) {
            const im = S.images[sp.key];
            if (im) ctx.drawImage(im, sx(r.x + x + sp.x), sy(r.y + y + sp.y), im.width * z / 64, im.height * z / 64);
        }
        ctx.globalAlpha = 1;
        ctx.fillStyle = 'rgba(224, 66, 31, 0.45)';
        for (const [dx, dy] of pf.colliders) ctx.fillRect(sx(r.x + x + dx), sy(r.y + y + dy), z, z);
        box(c.room, x, y, pf.w, pf.h, refused ? COLOR.torii : COLOR.moss);
        label(c.room, x, y, refused || `${pf.name} ${x}, ${y}`, refused ? COLOR.torii : COLOR.ink);
    }
    const from = S.linkFrom || (S.retarget && S.selected);
    if (from) {
        const r = S.rooms[from.room];
        box(from.room, from.x, from.y, 1, 1, COLOR.sun);
        if (S.hover) {
            const to = S.rooms[S.hover.room];
            arrow(sx(r.x + from.x + 0.5), sy(r.y + from.y + 0.5), sx(to.x + S.hover.x + 0.5), sy(to.y + S.hover.y + 0.5), COLOR.sun, 3);
        }
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

    if (S.edit) {
        const list = thingsAt(sel);
        S.active = Math.max(0, Math.min(S.active, list.length - 1));
        list.forEach((thing, i) => {
            const row = el('button', { className: 'row' }, el('span', { textContent: thing.label }), el('span', { className: 'dim', textContent: thing.kind }));
            row.setAttribute('aria-pressed', i === S.active);
            row.onclick = () => { S.active = i; inspect(); draw(); };
            parts.push(row);
        });
        const thing = list[S.active];
        if (thing && thing.type !== 'npc') {
            const actions = el('div', { className: 'actions' });
            if (thing.type === 'door') {
                const lead = el('button', { textContent: 'Leads to' });
                lead.setAttribute('aria-pressed', !!S.retarget);
                lead.onclick = () => { S.retarget = S.retarget ? null : thing; cursor(); inspect(); draw(); };
                const hide = el('button', { textContent: 'Hidden' });
                hide.setAttribute('aria-pressed', thing.t.hidden);
                hide.onclick = () => change([sel.room], () => {
                    Edit.setProp(thing.t.o, 'hidden', !thing.t.hidden);
                    return `${thing.t.hidden ? 'Showed' : 'Hid'} the door at ${cellName(sel.room, thing.x, thing.y)}`;
                });
                actions.append(lead, hide);
            }
            const remove = el('button', { textContent: 'Remove' });
            remove.onclick = removeActive;
            actions.append(remove);
            parts.push(actions);
        }
    }

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
    S.active = 0;
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

    $('edit').onclick = startEdit;
    $('search').oninput = library;
    window.addEventListener('beforeunload', (e) => { if (S.changes.length) e.preventDefault(); });
    window.addEventListener('keydown', (e) => {
        if (!S.edit || /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
        const mod = e.metaKey || e.ctrlKey;
        if (e.key === 'Escape') { S.arm = S.linkFrom = S.retarget = null; library(); cursor(); inspect(); draw(); }
        else if (e.key === 'Delete' || e.key === 'Backspace') removeActive();
        else if (mod && e.key === 'z') { e.preventDefault(); undo(); }
        else if (mod && e.key === 's') { e.preventDefault(); save(); }
    });

    const at = (e, cycle) => {
        const box = stage.getBoundingClientRect();
        const cx = S.view.x + (e.clientX - box.left) / S.view.z, cy = S.view.y + (e.clientY - box.top) / S.view.z;
        const cell = (k) => ({ room: k, x: Math.floor(cx - S.rooms[k].x), y: Math.floor(cy - S.rooms[k].y) });
        const under = S.order.filter(k => { const r = S.rooms[k]; return cx >= r.x && cx < r.x + r.w && cy >= r.y && cy < r.y + r.h; }).map(cell);
        return WorldModel.stackPick(under, cycle ? S.selected : null);
    };

    let drag = null;
    stage.addEventListener('pointerdown', (e) => {
        stage.setPointerCapture(e.pointerId);
        const c = at(e);
        const plain = S.edit && e.button === 0 && !e.shiftKey && !S.arm && !S.retarget;
        if (plain && c && S.tool === 'solid') {
            S.paint = { room: c.room, on: !S.rooms[c.room].blocked.has(c.x + ',' + c.y), cells: new Set([c.x + ',' + c.y]) };
            draw();
            return;
        }
        if (plain && c && S.tool === 'select' && S.selected && S.selected.room === c.room && S.selected.x === c.x && S.selected.y === c.y) {
            const thing = activeThing();
            if (thing) {
                S.moving = { thing, room: c.room, ox: c.x - thing.x, oy: c.y - thing.y, x: thing.x, y: thing.y };
                cursor();
                return;
            }
        }
        drag = { x: e.clientX, y: e.clientY, vx: S.view.x, vy: S.view.y, moved: false };
    });
    stage.addEventListener('pointermove', (e) => {
        const c = at(e);
        S.hover = c;
        if (S.paint) {
            if (c && c.room === S.paint.room) S.paint.cells.add(c.x + ',' + c.y);
            draw();
            return;
        }
        if (S.moving) {
            if (c && c.room === S.moving.room) { S.moving.x = c.x - S.moving.ox; S.moving.y = c.y - S.moving.oy; }
            draw();
            return;
        }
        if (!drag) {
            if (S.arm || S.linkFrom || S.retarget) draw();
            return;
        }
        if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 4) drag.moved = true;
        if (!drag.moved) return;
        stage.classList.add('dragging');
        S.view.x = drag.vx - (e.clientX - drag.x) / S.view.z;
        S.view.y = drag.vy - (e.clientY - drag.y) / S.view.z;
        draw();
    });
    stage.addEventListener('pointerup', (e) => {
        stage.classList.remove('dragging');
        if (S.paint) {
            const paint = S.paint;
            S.paint = null;
            return paintSolid(paint);
        }
        if (S.moving) {
            const m = S.moving;
            S.moving = null;
            cursor();
            if (m.x === m.thing.x && m.y === m.thing.y) return draw();
            if (moveActive(m.thing, m.room, m.x, m.y)) select(m.room, m.x + m.ox, m.y + m.oy, false);
            return;
        }
        const was = drag;
        drag = null;
        if (!was || was.moved) return;
        const c = at(e, !S.edit);
        if (S.arm) {
            if (c) place(S.arm, c);
        } else if (S.retarget) {
            const thing = S.retarget, from = S.selected;
            S.retarget = null;
            cursor();
            if (c) change([from.room], () => {
                Edit.retarget(thing.t, c.room, c.x, c.y);
                return `Door at ${cellName(from.room, thing.x, thing.y)} now leads to ${cellName(c.room, c.x, c.y)}`;
            });
            else { inspect(); draw(); }
        } else if (S.edit && S.tool === 'link') {
            if (!c) S.linkFrom = null;
            else if (!S.linkFrom) S.linkFrom = c;
            else { const from = S.linkFrom; S.linkFrom = null; linkCells(from, c); }
            draw();
        } else if (c) select(c.room, c.x, c.y, false);
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

boot().catch((e) => { $('loading').hidden = false; $('loading').textContent = 'failed to load: ' + e.message; throw e; });
