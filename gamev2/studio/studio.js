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

    const sprites = new Set();
    for (const room of Object.values(config.rooms)) {
        for (const layer of room.layers || []) for (const key of Object.values(layer.tiles || {})) sprites.add(key);
        for (const npc of room.npcs || []) sprites.add(npc.sprite + '_frame_0');
    }
    await Promise.all([...sprites].map(loadImage));

    S.model = new WorldModel(config, {
        exists: (key) => !!S.images[key],
        sizeOf: (key) => {
            const im = S.images[key];
            return im ? [Math.max(1, Math.round(im.width / 64)), Math.max(1, Math.round(im.height / 64))] : [1, 1];
        },
    });
    const m = S.model;

    layout(keys, worldMap);
    for (const k of keys) {
        m.enter(k, 0, 0);
        Object.assign(S.rooms[k], { blocked: m.blocked, interactions: m.interactions(), art: renderArt(k), npcs: [] });
    }

    S.dates = [...contentChangeDates(config)].sort();
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

function layout(keys, worldMap) {
    const m = S.model;
    const size = (k) => [m.roomManager.rooms[k].worldWidth / 64, m.roomManager.rooms[k].worldHeight / 64];
    let right = 0, bottom = 0;
    for (const k of keys) {
        const rect = worldMap.rooms[k];
        if (!rect) continue;
        const [w, h] = size(k);
        const scale = rect.w / rect.cells[0];
        S.rooms[k] = { x: Math.round(rect.x / scale), y: Math.round(rect.y / scale), w, h };
        right = Math.max(right, S.rooms[k].x + w);
        bottom = Math.max(bottom, S.rooms[k].y + h);
    }
    let x = 0, y = bottom + 8, rowH = 0;
    for (const k of keys) {
        if (S.rooms[k]) continue;
        const [w, h] = size(k);
        if (x + w > Math.max(right, 120)) { x = 0; y += rowH + 6; rowH = 0; }
        S.rooms[k] = { x, y, w, h };
        x += w + 4;
        rowH = Math.max(rowH, h);
    }
    S.order = keys;
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
                if (!r.blocked.has(key) && !reach.has(key)) ctx.fillRect(x0 + cx * z, y0 + cy * z, z, z);
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
    }

    if (S.show.teleports) {
        for (const k of S.order) {
            const r = S.rooms[k];
            for (const t of S.model.roomManager.rooms[k].transporters) {
                const to = S.rooms[t.targetRoom];
                if (!to) continue;
                const lit = S.selected && ((S.selected.room === k && S.selected.x === t.gridX && S.selected.y === t.gridY) ||
                    (S.selected.room === t.targetRoom && S.selected.x === t.targetX && S.selected.y === t.targetY));
                const near = S.selected && (S.selected.room === k || S.selected.room === t.targetRoom);
                ctx.globalAlpha = lit || near || !S.selected ? (lit ? 1 : near ? 0.9 : 0.45) : 0.12;
                arrow(sx(r.x + t.gridX + 0.5), sy(r.y + t.gridY + 0.5), sx(to.x + t.targetX + 0.5), sy(to.y + t.targetY + 0.5),
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
    for (const k of S.order) {
        const r = S.rooms[k];
        const w = ctx.measureText(k).width, h = parseInt(ctx.font.slice(5), 10) + 6;
        ctx.fillStyle = COLOR.ink;
        ctx.fillRect(sx(r.x), sy(r.y), w + 12, h);
        ctx.fillStyle = COLOR.paper;
        ctx.fillText(k, sx(r.x) + 6, sy(r.y) + h - 6);
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
            el('span', { className: 'dim', textContent: p.room + (p.x === undefined ? '' : ` ${p.x},${p.y}`) }));
        b.onclick = () => p.x === undefined ? focusRoom(p.room) : select(p.room, p.x, p.y, true);
        return b;
    }));
    $('rooms').replaceChildren(...S.order.map(k => {
        const r = S.rooms[k];
        const b = el('button', { className: 'row' },
            el('span', { textContent: k }),
            el('span', { className: 'dim', textContent: `${r.w}x${r.h}` + (r.npcs.length ? ` (${r.npcs.map(n => n.name).join(', ')})` : '') }));
        b.onclick = () => focusRoom(k);
        return b;
    }));
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
    const parts = [el('h2', {}, el('span', { textContent: `${sel.room} ${sel.x},${sel.y}` }), el('span', { className: 'badge ' + state[1], textContent: state[0] }))];

    const t = m.room.transporters.find(t => t.gridX === sel.x && t.gridY === sel.y);
    if (t) {
        const go = el('button', { className: 'row' }, el('span', { textContent: `→ ${t.targetRoom} ${t.targetX},${t.targetY}` }), el('span', { className: 'dim', textContent: t.hidden ? 'hidden door' : 'transporter' }));
        go.onclick = () => select(t.targetRoom, t.targetX, t.targetY, true);
        parts.push(go);
    }
    for (const [k, room] of Object.entries(m.roomManager.rooms)) {
        for (const from of room.transporters) {
            if (from.targetRoom !== sel.room || from.targetX !== sel.x || from.targetY !== sel.y) continue;
            const back = el('button', { className: 'row' }, el('span', { textContent: `← ${k} ${from.gridX},${from.gridY}` }), el('span', { className: 'dim', textContent: 'arrives here' }));
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

    const cmd = `node tools/play.js warp ${sel.room} ${sel.x} ${sel.y}`;
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
    S.view.z = Math.min(stage.clientWidth / (r.w + 4), stage.clientHeight / (r.h + 6));
    S.view.x = r.x + r.w / 2 - stage.clientWidth / 2 / S.view.z;
    S.view.y = r.y + r.h / 2 - stage.clientHeight / 2 / S.view.z;
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
        const k = S.order.find(k => { const r = S.rooms[k]; return cx >= r.x && cx < r.x + r.w && cy >= r.y && cy < r.y + r.h; });
        if (k) select(k, Math.floor(cx - S.rooms[k].x), Math.floor(cy - S.rooms[k].y), false);
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
