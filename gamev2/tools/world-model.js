const DIRS = { n: [0, -1], s: [0, 1], e: [1, 0], w: [-1, 0] };
const baseOf = (key) => (key || '').replace(/_(front|back|side)$/, '');

const VENDING_RE = /vending-machine/;   // same test as the vending rule in src/utils/Interactions.js
// Overhead sprites whose bottom row is bare at each end: the shrine roofs' outer columns hold only the
// upturned eave tip there (a sliver above a head, #157), so standing in them is not standing under the roof.
const OPEN_EAVES = { 'shrine-top': 1, 'red-shrine-top': 1 };
const BIN_RE = /(^|[-_])(bin|dustbin|dumpster|trash|trashcan|rubbish|garbage|litter)([-_]|$)/i;

class WorldModel {
    static applyTiled(config, tmjFor) {
        for (const key of Object.keys(config.rooms)) {
            const tmj = tmjFor(key);
            if (!tmj) continue;
            const built = TiledAdapter.toRoom(tmj);
            const r = config.rooms[key];
            r.layers = built.layers;
            if (built.transporters.length) r.transporters = built.transporters;
            if (built.worldWidth) r.worldWidth = built.worldWidth;
            if (built.worldHeight) r.worldHeight = built.worldHeight;
            if (built.boundary) r.boundary = built.boundary;
        }
        return config;
    }

    // Every day worth surveying: the days with posts, and every day of every trip (the
    // trip's base cast stands somewhere on each of them, post or no post).
    static surveyDates(config) {
        const dates = new Set(contentChangeDates(config));
        for (const trip of Trips.of(config)) {
            for (let n = Trips.dayNumber(trip.start); n <= Trips.dayNumber(trip.end); n++) {
                dates.add(new Date(n * 86400000).toISOString().slice(0, 10));
            }
        }
        return [...dates].sort();
    }

    static defaultDate(config) {
        return defaultGameDate(todayIso(), [...contentChangeDates(config)].sort(), Trips.of(config));
    }

    // Where the game puts a player on `date` (Trips.startFor): next to the cast, or the
    // trip's own cell when nobody is anywhere.
    static startFor(config, date, opts) {
        return Trips.startFor(config, date, opts);
    }

    /**
     * opts.stitch (default true): merge the districts of config `cities` into
     * one room each, with the game's own CityStitcher, so the model is the
     * world the game plays. false = the separate rooms joined by seam
     * transporters that `?stitch=0` plays. Everything public still speaks
     * district coordinates where it can (state(), here(), problem.where).
     */
    constructor(config, env, state, opts) {
        this.env = env;
        this.config = config;
        this.GRID_SIZE = config.game.gridSize;
        this.WORLD_WIDTH = config.game.worldWidth;
        this.WORLD_HEIGHT = config.game.worldHeight;
        this.cx = Math.floor(this.WORLD_WIDTH / this.GRID_SIZE / 2);
        this.cy = Math.floor(this.WORLD_HEIGHT / this.GRID_SIZE / 2);

        this.roomManager = new RoomManager(this);
        this.roomManager.initializeRooms(config, this.cx, this.cy,
            this.WORLD_WIDTH / this.GRID_SIZE, this.WORLD_HEIGHT / this.GRID_SIZE);
        this.collisionSystem = new CollisionSystem(this);
        this.stitched = !(opts && opts.stitch === false) && typeof CityStitcher !== 'undefined';
        if (this.stitched) this.roomManager.stitchCities(config, (opts && opts.worldMap) || null);

        this.trips = Trips.of(config);
        const date = (state && state.date) || WorldModel.defaultDate(config);
        // a session opens on the trip's own cell — the same place every day, which is what a
        // script wants; `start` (play.js) goes where the game puts a player, beside the cast
        const s = Object.assign(Trips.homeFor(config, date), {
            date, as: baseOf(config.player.sprite),
        }, state || {});
        this.date = s.date;
        this.as = s.as;
        this.livery = s.livery || null;
        this.player = this.character('you', s.x, s.y);
        this.player.isPlayer = true;
        this.enter(s.room, s.x, s.y);
    }

    /** Saved in district coordinates, so a session reads the same stitched or not. */
    state() {
        const at = this.here();
        return { room: at.room, x: at.x, y: at.y, date: this.date, as: this.as, livery: this.livery };
    }

    /**
     * Where the player is, the way config and the maps say it: the district
     * underfoot and the cell in that district — plus, inside a stitched city,
     * `city` (its key) and `ox`/`oy`, the district's offset in the city room.
     */
    here() {
        const rm = this.roomManager, p = this.player;
        const at = rm.localize(p.gridX, p.gridY);
        const member = rm.memberOf[at.room];
        const inCity = member && member.city.key === rm.currentRoom;
        return { room: at.room, x: at.x, y: at.y, city: inCity ? rm.currentRoom : null,
                 ox: inCity ? member.member.x : 0, oy: inCity ? member.member.y : 0 };
    }

    /** "Market 5,3" for a cell of a runtime room (the owning district's own cell inside a city). */
    spot(roomKey, x, y) {
        const at = this.roomManager.districtsAt(x, y, roomKey)[0] || { room: roomKey, x, y };
        return `${at.room} ${at.x},${at.y}`;
    }

    /** The rooms that are entered at runtime: every config room, with a city in place of its districts. */
    runtimeRooms() {
        return [...new Set(Object.keys(this.config.rooms).map(k => this.roomManager.resolve(k, 0, 0).room))];
    }

    character(name, x, y, extra) {
        return Object.assign({
            name, gridX: x, gridY: y, isMoving: false,
            getTargetPosition() { return { x: this.gridX, y: this.gridY }; },
        }, extra);
    }

    exists(key) { return this.env.exists(key); }

    cells(key) { return this.env.sizeOf(key); }

    npcsIn(roomKey) {
        const city = this.roomManager.cities[roomKey];
        if (city) {
            // a city holds its districts' people, each in city cells
            return city.members.flatMap(m => this.npcsIn(m.key).map(n =>
                Object.assign(n, { gridX: n.gridX + m.x, gridY: n.gridY + m.y, homeRoom: m.key })));
        }
        const opponent = this.as === 'damian' ? 'bailey' : 'damian';
        const list = [];
        for (const raw of this.config.rooms[roomKey].npcs || []) {
            const r = resolveNpc(raw, this.date, this.trips);
            if (!r || baseOf(r.sprite) === this.as) continue;
            if (r.drinkingGameOpponent && baseOf(r.sprite) !== opponent) continue;
            list.push(this.character(r.name,
                r.gridX !== null ? r.gridX : this.cx + r.gridOffsetX,
                r.gridY !== null ? r.gridY : this.cy + r.gridOffsetY,
                { canInteract: true, dialogue: r.dialogue || [], photo: r.photo || null, posts: r.posts || null }));
        }
        return list;
    }

    enter(roomKey, x, y) {
        const rm = this.roomManager;
        if (!rm.rooms[roomKey]) throw new Error(`no room "${roomKey}" (try: rooms)`);
        // a district of a stitched city is the city room at the district's offset
        ({ room: roomKey, x, y } = rm.resolve(roomKey, x, y));
        rm.currentRoom = roomKey;
        const room = rm.rooms[roomKey];
        const st = (this.config.stations || {})[roomKey];
        this.livery = st ? TrainTravel.liveryFor(st, this.livery) : null;
        room.npcs = this.unpeopled ? [] : this.npcsIn(roomKey);
        rm.objectSprites = room.objects;
        // collision is the game's own set lookup (RoomManager.isBlocked)
        rm.blockedCells = new Set();
        for (const layer of room.layers) {
            if (!layer.collision) continue;
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (this.exists(key)) rm.blockedCells.add(xy);
            }
        }
        this.player.gridX = x;
        this.player.gridY = y;
        this.w = (room.worldWidth || this.WORLD_WIDTH) / this.GRID_SIZE;
        this.h = (room.worldHeight || this.WORLD_HEIGHT) / this.GRID_SIZE;
        this.blocked = rm.blockedCells;
        this.seats = null;      // this room's seat cells, indexed on first use (seatAt)
    }

    get room() { return this.roomManager.rooms[this.roomManager.currentRoom]; }
    get roomConfig() { return this.config.rooms[this.roomManager.currentRoom] || {}; }   // a city has no config room

    canStep(fx, fy, tx, ty) {
        if (tx < 0 || ty < 0 || tx >= this.w || ty >= this.h) return false;
        return this.collisionSystem.checkCollision(this.player, tx, ty, fx, fy);
    }

    /** The seat cell on a cell of the current room - furniture the player can get on (src/utils/Seats.js) - or null. */
    seatAt(x, y) {
        if (!this.seats) {
            this.seats = Seats.index(this.room, { sizeOf: (key) => this.cells(key), isBlocked: (cx, cy) => this.blocked.has(cx + ',' + cy) });
        }
        return Seats.lookup(this.seats, x, y);
    }

    /** The one step canStep refuses and the game allows: the player, straight onto a seat (CollisionSystem.checkSeatStep). */
    canSit(fx, fy, tx, ty) {
        if (tx < 0 || ty < 0 || tx >= this.w || ty >= this.h) return false;
        return this.collisionSystem.checkSeatStep(this.player, this.seatAt(tx, ty), tx, ty, fx, fy);
    }

    tilesAt(x, y) {
        const hits = [];
        for (const layer of this.room.layers) {
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                const [tx, ty] = xy.split(',').map(Number);
                if (tx > x || ty > y) continue;
                const [w, h] = (tx === x && ty === y) ? [1, 1] : this.cells(key);
                if (x < tx + w && y < ty + h) hits.push({ layer: layer.name, z: layer.z, collision: !!layer.collision, key, at: [tx, ty] });
            }
        }
        return hits;
    }

    interactions() {
        return Interactions.all(this.room, this.roomConfig, { sizeOf: (key) => this.cells(key), venues: Shop.VENUES });
    }

    interactionAt(x, y) {
        const covers = (i) => x >= i.x && x < i.x + i.w && y >= i.y && y < i.y + i.h;
        const all = this.interactions();
        const table = all.find(i => i.group === 'drinking-game' && covers(i));
        if (table) return table;
        const npc = this.room.npcs.find(n => n.gridX === x && n.gridY === y);
        if (npc) return { kind: 'npc', group: 'npc', npc };
        return ['flights', 'ride', 'shop', 'water', 'shrine', 'palace', 'temple', 'pond', 'clock', 'career', 'flavour'].map(g => all.find(i => i.group === g && covers(i))).find(Boolean) || null;
    }

    describe(i) {
        if (!i) return 'solid, nothing to interact with';
        if (i.kind === 'npc') {
            const n = i.npc;
            const lines = n.dialogue.length ? n.dialogue.map(l => `  "${l}"`).join('\n') : '  (nothing to say)';
            // the posts the lines came from, as the dialogue box captions them
            const from = [];
            n.dialogue.forEach((_, i) => {
                const post = postForLine(n.posts, i, n.dialogue.length);
                if (post && !from.includes(post)) from.push(post);
            });
            return `${n.name} says:\n${lines}` + (n.photo ? `\n  photo: assets/photos/${n.photo}.png` : '') +
                from.map(p => `\n  from: ${p.title}` + (postLink(p) ? ` <${p.url}>` : '')).join('');
        }
        if (i.group === 'shop') {
            const venue = Shop.VENUES[i.kind];
            const items = (this.config.items || Shop.DEFAULT_ITEMS).filter(venue.sells);
            return `opens the ${Shop.titleFor(i.kind, this.roomConfig)} shop: ` + items.map(it => `${it.name} ¥${it.price}`).join(', ') +
                (venue.buys ? `; buys caught fish${venue.grills ? ' and grills them' : ''}` : '');
        }
        if (i.group === 'flights') return 'opens the flights board: fly to ' +
            Object.keys(this.config.airports || {}).filter(k => k !== this.roomManager.currentRoom).join(', ');
        if (i.kind === 'water') return 'a free cup of water: a little energy, up to a cap (Energy.WATER_CAP)';
        if (i.kind === 'incense') return 'wafts the incense smoke over yourself (free): one of a few lines, in turn';
        if (i.kind === 'offering' && i.group === 'temple') return 'makes an offering (¥5 from the wallet): palms together and a blessing is said';
        if (i.kind === 'drawers') return 'shakes a numbered stick out of the cylinder and reads the fortune in its drawer (¥100; the shrines\' omikuji: one a game day across all of them)';
        if (i.kind === 'offering') return 'makes an offering (¥5 from the wallet): the bell rings and a blessing is said';
        if (i.kind === 'omikuji') return 'draws the day\'s fortune (¥100, one a game day; the same slip is read back until the date changes)';
        if (i.kind === 'audience') return 'requests an audience at the empty seat: one of a handful of dry answers, in turn';
        if (i.kind === 'guestbook') return 'signs the visitors\' book (free, once a game day; kept in the save)';
        if (i.kind === 'pond') return 'casts a fishing line (needs the fishing rod); a catch goes into the bag to sell';
        if (i.kind === 'clock') return 'opens the time-travel date picker';
        if (i.kind === 'desk') return 'the reception desk: signs you on for a job in the tower (free); afterwards reads your title back';
        if (i.kind === 'lift' && i.group === 'career') return 'the lift up to work: a shift of tickets for pay (needs the staff pass from the reception desk)';
        if (i.kind === 'wheel') return 'rides the wheel: one turn, the view over Dotonbori, and back on this cell';
        if (i.group === 'flavour') return `says: "${i.say}"`;
        if (i.kind === 'drinking-game') return 'starts the izakaya drinking game (free, or pick a stake)';
    }

    station() { return (this.config.stations || {})[this.roomManager.currentRoom]; }

    onBoardCell() {
        const st = this.station();
        return !!st && st.board.some(([bx, by]) => bx === this.player.gridX && by === this.player.gridY);
    }

    step(dir) {
        const [dx, dy] = DIRS[dir];
        const p = this.player;
        const tx = p.gridX + dx, ty = p.gridY + dy;
        if (!this.canStep(p.gridX, p.gridY, tx, ty)) {
            if (this.canSit(p.gridX, p.gridY, tx, ty)) {
                // onto a chair, a sofa, a bed: its line, if it has one, is said on getting on it (Seating)
                const seat = this.seatAt(tx, ty), was = this.seatAt(p.gridX, p.gridY);
                const same = was && was.key === seat.key && was.x === seat.x && was.y === seat.y;
                const i = same ? null : this.interactionAt(tx, ty);
                p.gridX = tx; p.gridY = ty;
                return { moved: true, seat, interaction: i && i.group === 'flavour' ? i : null };
            }
            return { moved: false, bumped: [tx, ty], interaction: this.interactionAt(tx, ty) };
        }
        const from = this.here().room;
        p.gridX = tx; p.gridY = ty;
        const t = this.room.transporters.find(t => t.gridX === tx && t.gridY === ty);
        if (t) {
            // a door into or out of an observation deck is a lift (the game plays the ride, ViewRide)
            const lift = RoomManager.liftFor(this.config.rooms, from, t.targetRoom);
            this.enter(t.targetRoom, t.targetX, t.targetY);
            return { moved: true, transported: lift ? { from, to: t.targetRoom, lift } : { from, to: t.targetRoom } };
        }
        // walking from one district of a stitched city into the next: no teleport, just a new name
        const to = this.here().room;
        return { moved: true, board: this.onBoardCell(), crossed: to !== from ? { from, to } : null };
    }

    path(gx, gy) {
        const p = this.player;
        const start = p.gridX + ',' + p.gridY, goal = gx + ',' + gy;
        const prev = new Map([[start, null]]);
        const queue = [[p.gridX, p.gridY]];
        const stops = new Set(this.room.transporters.map(t => t.gridX + ',' + t.gridY));
        while (queue.length) {
            const [x, y] = queue.shift();
            if (x + ',' + y === goal) break;
            if (stops.has(x + ',' + y) && x + ',' + y !== start) continue;
            for (const d of 'nsew') {
                const nx = x + DIRS[d][0], ny = y + DIRS[d][1], k = nx + ',' + ny;
                if (prev.has(k) || !this.canStep(x, y, nx, ny)) continue;
                prev.set(k, [x + ',' + y, d]);
                queue.push([nx, ny]);
            }
        }
        if (!prev.has(goal)) return null;
        const steps = [];
        for (let k = goal; prev.get(k); k = prev.get(k)[0]) steps.unshift(prev.get(k)[1]);
        return steps;
    }

    reachable() {
        const seen = new Set();
        const queue = [[this.player.gridX, this.player.gridY]];
        seen.add(queue[0].join(','));
        while (queue.length) {
            const [x, y] = queue.shift();
            for (const d of 'nsew') {
                const nx = x + DIRS[d][0], ny = y + DIRS[d][1], k = nx + ',' + ny;
                if (seen.has(k) || !this.canStep(x, y, nx, ny)) continue;
                seen.add(k);
                queue.push([nx, ny]);
            }
        }
        return seen;
    }

    // Every cell the game can put the player on in `roomKey`: the spawn, where a transporter
    // from any room drops them, and the station platform a train arrives at. Targets are
    // authored as (district, cell); for a stitched city they are handed back in city cells,
    // and for a district linted on its own map the seam transporters of its neighbours count
    // too (they are what `?stitch=0` plays).
    arrivals(roomKey) {
        const rm = this.roomManager;
        const cells = [];
        const lands = (room, x, y) => {
            if (room === roomKey) { cells.push([x, y]); return; }
            const at = rm.resolve(room, x, y);
            if (at.room === roomKey) cells.push([at.x, at.y]);
        };
        const p = this.config.player;
        lands(p.startRoom, p.startX, p.startY);
        for (const r of Object.values(rm.rooms)) {
            for (const t of r.transporters) lands(t.targetRoom, t.targetX, t.targetY);
        }
        for (const [k, st] of Object.entries(this.config.stations || {})) {
            if (st && st.arrive) lands(k, st.arrive[0], st.arrive[1]);
        }
        for (const [k, a] of Object.entries(this.config.airports || {})) {
            if (a && a.arrive) lands(k, a.arrive[0], a.arrive[1]);
        }
        return cells;
    }

    // The cells of `walkable` (a Set of "x,y") a player can walk to (issue #142): everything
    // connected to an arrival cell, or the largest connected area when no arrival is walkable
    // (a room nothing leads to yet). Seeding from one fixed cell instead lands in a sealed
    // pocket in most rooms.
    static walkedFrom(walkable, arrivals) {
        const flood = (start, seen) => {
            const queue = [start];
            seen.add(start);
            for (let i = 0; i < queue.length; i++) {
                const [x, y] = queue[i].split(',').map(Number);
                for (const nb of [(x + 1) + ',' + y, (x - 1) + ',' + y, x + ',' + (y + 1), x + ',' + (y - 1)]) {
                    if (seen.has(nb) || !walkable.has(nb)) continue;
                    seen.add(nb);
                    queue.push(nb);
                }
            }
            return queue;
        };
        const reached = new Set();
        for (const [x, y] of arrivals || []) {
            const c = x + ',' + y;
            if (walkable.has(c) && !reached.has(c)) flood(c, reached);
        }
        if (reached.size) return reached;
        const seen = new Set();
        let best = [];
        for (const c of walkable) {
            if (seen.has(c)) continue;
            const region = flood(c, seen);
            if (region.length > best.length) best = region;
        }
        return new Set(best);
    }

    // Columns of an overhead sprite's bottom row that would hide someone standing in them.
    static overheadCols(name, w) {
        const eave = OPEN_EAVES[name] || 0;
        const cols = [];
        for (let a = eave; a < w - eave; a++) cols.push(a);
        return cols;
    }

    // `keys` with each city's districts put in the city's own order, so a later one comes later
    // here too: where two districts overlap, the later one owns the cells (CityStitcher), and
    // whoever lays rooms out together (the studio) draws it on top and gives it the click.
    static stackOrder(config, keys) {
        const order = keys.slice();
        for (const city of Object.values(config.cities || {})) {
            const districts = (city.rooms || []).map((r) => r.room).filter((k) => keys.includes(k));
            const slots = districts.map((k) => keys.indexOf(k)).sort((p, q) => p - q);
            districts.forEach((k, i) => { order[slots[i]] = k; });
        }
        return order;
    }

    // Where each of `keys` (rooms or cities) is in the world, as { key: [east, south] } in degrees of
    // latitude: its town's `geo` (Places.of: a station, an airport or an interior is where its town is),
    // a city the mean of its districts' towns. A room with no town is left out. Whoever lays rooms out
    // together (the studio) pulls each toward it, so towns keep their real directions from one another.
    static geoOf(config, keys) {
        const places = Object.fromEntries(Places.list(config).map((p) => [p.key, p]));
        const out = {};
        for (const k of keys) {
            const city = (config.cities || {})[k];
            // a city is at its own dot: a district that is a place of its own (Karuizawa) does not pull it
            const towns = places[k] ? [k] : [...new Set((city ? (city.rooms || []).map((r) => r.room) : [k]).map((r) => Places.of(config, r)))].filter((t) => t);
            if (!towns.length) continue;
            const mean = (f) => towns.reduce((sum, t) => sum + f(places[t]), 0) / towns.length;
            out[k] = [mean((p) => p.lon) * Math.cos(38 * Math.PI / 180), -mean((p) => p.lat)];
        }
        return out;
    }

    // Which of the cells stacked at one spot (bottom first, as stackOrder lists their rooms) a click
    // picks: the top one, or, when the cell already selected is one of them, the next one down (wrapping
    // back to the top) - so a covered district's cells, its seam transporters among them, can be reached.
    static stackPick(cells, selected) {
        const at = selected ? cells.findIndex((c) => c.room === selected.room && c.x === selected.x && c.y === selected.y) : -1;
        return cells.length ? cells[at <= 0 ? cells.length - 1 : at - 1] : null;
    }

    /**
     * The streetcars of a runtime room: its districts' config `tramways` as src/AmbientTrams.js runs
     * them (none where that file is not loaded), in the room's cells. Each line also has `room` (the
     * district that declares it), `x` / `y` (that district's place in the room) and `car`: the cells
     * of the car where it first stands, a shuttle at its first stop as the game opens the room.
     */
    tramways(roomKey) {
        if (typeof AmbientTrams === 'undefined') return [];
        const room = this.roomManager.rooms[roomKey], GS = this.GRID_SIZE;
        const city = this.roomManager.cities[roomKey];
        const lines = [];
        for (const m of city ? city.members : [{ key: roomKey, x: 0, y: 0 }]) {
            for (const def of (this.config.rooms[m.key] || {}).tramways || []) {
                const line = AmbientTrams.line(def, room.layers, m, Math.round(room.worldWidth / GS));
                if (!line) continue;
                const key = line.sprites[0];
                let car = null;
                if (this.exists(key)) {
                    const [w, h] = this.cells(key);
                    const plan = AmbientTrams.plan(line, { GS, width: w * GS, worldWidth: room.worldWidth, dir: AmbientTrams.direction(0, line.faces) });
                    const at = AmbientTrams.at(plan, AmbientTrams.firstHalt(plan));
                    if (at.stopped) car = { key, x: at.x / GS, y: line.row - h + 1, w, h };
                }
                lines.push(Object.assign(line, { room: m.key, x: m.x, y: m.y, car }));
            }
        }
        return lines;
    }

    /** The line of the current room whose rails or standing car cover cell (x, y), else null. */
    tramwayAt(x, y) {
        const on = (t) => (y === t.row && x >= t.from && x <= t.to) ||
            (t.car && x >= t.car.x && x < t.car.x + t.car.w && y >= t.car.y && y < t.car.y + t.car.h);
        return this.tramways(this.roomManager.currentRoom).find(on) || null;
    }

    drawOrder(roomKey) {
        const room = this.roomManager.rooms[roomKey];
        const meta = this.config.spriteMetadata || {};
        const ground = [], standing = [];
        room.layers.forEach((layer, order) => {
            if (layer.collision) return;
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (!this.exists(key)) continue;
                const [x, y] = xy.split(',').map(Number);
                if (layer.z < 2) { ground.push({ key, x, y }); continue; }
                const depth = (y + this.cells(key)[1]) * 10 + (layer.z >= 7 ? 11 : 0) + ((meta[key] || {}).depthBias || 0);
                standing.push({ key, x, y, depth, order });
            }
        });
        for (const t of this.tramways(roomKey)) {
            if (t.car) standing.push({ key: t.car.key, x: t.car.x, y: t.car.y, depth: AmbientTrams.depthAt(t.row), order: room.layers.length });
        }
        standing.sort((a, b) => a.depth - b.depth || a.order - b.order || a.y - b.y || a.x - b.x);
        return ground.concat(standing);
    }

    lint(roomKey) {
        const room = this.roomManager.rooms[roomKey];
        const names = this.config.tileNames || {};
        const nm = (key) => names[key] || key;
        const K = (x, y) => x + ',' + y;
        // a stitched city: the woodland between the districts ("Backdrop ..." layers) is
        // generated scenery nobody can enter - it only has to leave no hole in the ground
        const floor = new Set(), overFloor = new Set(), colliders = new Set(), backdrop = new Set();
        const objects = [];
        let W = 0, H = 0;
        const foot = (x, y, key) => {
            const [w, h] = this.cells(key);
            const cells = [];
            for (let a = 0; a < w; a++) for (let b = 0; b < h; b++) cells.push([x + a, y + b]);
            return { cells, w, h };
        };
        for (const layer of room.layers) {
            const z = layer.z || 0;
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                const [x, y] = xy.split(',').map(Number);
                W = Math.max(W, x + 1); H = Math.max(H, y + 1);
                if (layer.name.startsWith('Backdrop')) { if (z < 2) backdrop.add(xy); continue; }
                if (layer.name === 'Floor') floor.add(xy);
                if (layer.name === 'Over Floor') for (const [cx, cy] of foot(x, y, key).cells) overFloor.add(K(cx, cy));
                if (layer.collision) { colliders.add(xy); continue; }
                if (z >= 1 && layer.name !== 'Floor') objects.push(Object.assign({ layer: layer.name, z, x, y, key }, foot(x, y, key)));
            }
        }
        const doors = new Set(room.transporters.map(t => K(t.gridX, t.gridY)));
        const inside = (x, y) => room.city ? this.roomManager.checkBoundary(x, y, roomKey) :
            !room.boundary || room.boundary.length < 3 ||
            this.roomManager.isPointInPolygon(x + 0.5, y + 0.5, room.boundary);
        const walkable = (x, y) => x >= 0 && x < W && y >= 0 && y < H && floor.has(K(x, y)) && !colliders.has(K(x, y)) && inside(x, y);

        const walkCells = new Set();
        for (const c of floor) if (walkable(...c.split(',').map(Number))) walkCells.add(c);
        const reachable = WorldModel.walkedFrom(walkCells, this.arrivals(roomKey));

        // True when (x, y) is walkable and part of a real walking area rather than a sealed
        // pocket: a flood from it finds at least 12 cells.
        const opensOut = (x, y) => {
            if (!walkable(x, y)) return false;
            const seen = new Set([K(x, y)]), queue = [[x, y]];
            while (queue.length && seen.size < 12) {
                const [cx, cy] = queue.shift();
                for (const [nx, ny] of [[cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]]) {
                    if (seen.has(K(nx, ny)) || !walkable(nx, ny)) continue;
                    seen.add(K(nx, ny));
                    queue.push([nx, ny]);
                }
            }
            return seen.size >= 12;
        };

        const errors = {}, warns = {};
        const push = (bag, kind, item) => (bag[kind] = bag[kind] || []).push(item);

        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (!floor.has(K(x, y)) && !backdrop.has(K(x, y))) push(errors, 'floor-hole', K(x, y));

        // "definitely no rubbish bins!!" (issue #19): any bin / dumpster / trash sprite on any
        // layer is an error, so one can never be placed again. Whole-word match between - and _,
        // so office-cabinet is fine.
        for (const layer of room.layers) {
            for (const [xy, key] of Object.entries(layer.tiles || {})) {
                if (BIN_RE.test(String(key))) push(errors, 'rubbish-bin', `${String(key)} @${xy} (${layer.name})`);
            }
        }
        for (const xy of colliders) {
            const [x, y] = xy.split(',').map(Number);
            if (!(x >= 0 && x < W && y >= 0 && y < H)) push(errors, 'oob-collider', xy);
        }

        // A vending machine is solid down to its foot (issue #101): the foot tile is the last
        // few pixels of the cabinet, so a walkable foot cell lets the player stand on the
        // machine. The two lowest cells of every machine column must collide (the empty top
        // cell of a tall machine is walk-behind). tools/seal_vending.py repairs a room.
        const machine = new Set();
        for (const o of objects) if (VENDING_RE.test(String(o.key))) for (const [cx, cy] of o.cells) machine.add(K(cx, cy));
        for (const c of [...machine].sort()) {
            const [x, y] = c.split(',').map(Number);
            const foot = !machine.has(K(x, y + 1));
            const cabinet = !foot && !machine.has(K(x, y + 2));
            if ((foot || cabinet) && !colliders.has(c)) push(errors, 'vending-walkable', `${c} (${foot ? 'foot' : 'cabinet'})`);
            // ...and it is used by bumping that foot from the cell in front (issue #137), so
            // the cell under the foot must be walkable and lead somewhere (a walled-in pocket
            // in front of a machine is no use either).
            if (foot && !opensOut(x, y + 1)) push(errors, 'vending-no-front', `${c} (front ${K(x, y + 1)})`);
        }

        // Shop fixtures inside a store (issue #152): a shelf or cooler is used by bumping it
        // from the cell in front, so the cell under EVERY column of its footprint must be
        // walkable and reachable from the door (a two-cell fridge with an aisle of shelves
        // touching its foot could only be bumped from the side, and the middle of a run not
        // at all). The till stands against the front wall: any reachable side will do.
        // "Reachable" here is walked from the room's doors, which is how a shopper gets in.
        const roomConfig = this.config.rooms[roomKey] || {};
        const fixtures = !roomConfig.interior ? [] :
            Interactions.all(room, roomConfig, { sizeOf: (key) => this.cells(key), venues: Shop.VENUES, group: 'shop' });
        // A home's furniture that says a line when bumped (issue #208) is held to the till's
        // rule - some side of it can be walked to - and a home (config `house`) to the store's:
        // no floor its furniture has sealed off. A tower's lobby (config `lobby`, issue #216)
        // and a floor of a Devhouse (config `devhouse`, issue #69) are held to both, under the
        // same two names; a lobby's reception desk and lifts (group `career`, issue #226) are
        // furniture you bump as well, and are held to the first.
        const flavour = !roomConfig.interior ? [] : ['flavour', 'career'].flatMap(group =>
            Interactions.all(room, roomConfig, { sizeOf: (key) => this.cells(key), venues: Shop.VENUES, group }));
        const homely = roomConfig.house || roomConfig.lobby || roomConfig.devhouse;
        const fromDoor = new Set();
        if (fixtures.length || flavour.length || homely) {
            const queue = room.transporters.map(t => [t.gridX, t.gridY]).filter(c => walkable(...c));
            for (const c of queue) fromDoor.add(K(...c));
            while (queue.length) {
                const [cx, cy] = queue.shift();
                for (const [nx, ny] of [[cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]]) {
                    if (fromDoor.has(K(nx, ny)) || !walkable(nx, ny)) continue;
                    fromDoor.add(K(nx, ny));
                    queue.push([nx, ny]);
                }
            }
        }
        for (const f of fixtures) {
            const till = f.kind !== 'drinks' && f.kind !== 'snacks';   // the konbini counter, a venue's bar
            const sides = [];
            for (let a = 0; a < f.w; a++) sides.push([f.x + a, f.y + f.h], [f.x + a, f.y - 1]);
            for (let b = 0; b < f.h; b++) sides.push([f.x - 1, f.y + b], [f.x + f.w, f.y + b]);
            if (till) {
                if (!sides.some(([sx, sy]) => fromDoor.has(K(sx, sy)))) push(errors, 'shop-no-front', `${nm(f.key)} @${K(f.x, f.y)} (no reachable side)`);
                continue;
            }
            for (let a = 0; a < f.w; a++) {
                const front = K(f.x + a, f.y + f.h);
                if (!fromDoor.has(front)) push(errors, 'shop-no-front', `${nm(f.key)} @${K(f.x + a, f.y)} (front ${front})`);
            }
        }

        // ...and a store has no floor its furniture has sealed off (issue #182): a filler
        // under the corner beside the cooler run left the corner cell a walkable pocket
        // nobody could step into, which reads as a gap in the fittings. (A cell some art
        // stands over - the head of a lantern whose foot is solid - is not bare floor.)
        for (const f of flavour) {
            const sides = [];
            for (let a = 0; a < f.w; a++) sides.push([f.x + a, f.y + f.h], [f.x + a, f.y - 1]);
            for (let b = 0; b < f.h; b++) sides.push([f.x - 1, f.y + b], [f.x + f.w, f.y + b]);
            if (!sides.some(([sx, sy]) => fromDoor.has(K(sx, sy)))) push(errors, 'flavour-no-front', `${nm(f.key)} @${K(f.x, f.y)} (no reachable side)`);
        }
        if (fixtures.length || homely) {
            const dressed = new Set();
            for (const o of objects) for (const [cx, cy] of o.cells) dressed.add(K(cx, cy));
            for (const c of [...walkCells].sort()) {
                if (!fromDoor.has(c) && !dressed.has(c)) push(errors, fixtures.length ? 'shop-sealed-floor' : 'house-sealed-floor', c);
            }
        }

        const covered = new Set();
        for (const o of objects) for (const [cx, cy] of o.cells) { covered.add(K(cx, cy)); covered.add(K(cx, cy - 1)); }
        const sortedColliders = [...colliders].map(c => c.split(',').map(Number)).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        // (a bare collider no walkable cell touches is not stray: it fills ground nobody can get
        // to - the yard behind the Tokyo shrine hall, issue #196 - so nobody is ever put there)
        const walledIn = (x, y) => ![[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]].some(([nx, ny]) => reachable.has(K(nx, ny)));
        for (const [x, y] of sortedColliders) if (!covered.has(K(x, y)) && !walledIn(x, y)) push(warns, 'stray-collision', K(x, y));

        for (const o of objects) {
            if (o.layer !== 'Collidables') continue;
            if (o.cells.some(([cx, cy]) => doors.has(K(cx, cy)))) continue;
            if (!o.cells.some(([cx, cy]) => colliders.has(K(cx, cy)))) push(errors, 'missing-collision', `${nm(o.key)} @${o.x},${o.y}`);
        }

        for (const o of objects) {
            if (o.z < 7 || o.h < 4) continue;
            let pavilion = o.cells.some(([cx, cy]) => overFloor.has(K(cx, cy)));
            for (let a = 0; a < o.w; a++) if (overFloor.has(K(o.x + a, o.y + o.h))) pavilion = true;
            if (pavilion) continue;
            let under = false;
            for (const a of WorldModel.overheadCols(nm(o.key), o.w)) {
                const c = K(o.x + a, o.y + o.h - 1);
                if (!colliders.has(c) && reachable.has(c)) under = true;
            }
            if (under) push(warns, 'under-overhead', `${nm(o.key)} @${o.x},${o.y} (${o.w}x${o.h})`);
        }

        const tops = {};
        for (const o of objects) if (o.z >= 7) (tops[o.key] = tops[o.key] || new Set()).add(K(o.x, o.y));
        for (const [key, cells] of Object.entries(tops)) {
            const seen = new Set();
            for (const c of cells) {
                if (seen.has(c)) continue;
                const comp = [], queue = [c];
                seen.add(c);
                while (queue.length) {
                    const cur = queue.shift();
                    comp.push(cur);
                    const [cx, cy] = cur.split(',').map(Number);
                    for (const nb of [K(cx + 1, cy), K(cx - 1, cy), K(cx, cy + 1), K(cx, cy - 1)]) {
                        if (cells.has(nb) && !seen.has(nb)) { seen.add(nb); queue.push(nb); }
                    }
                }
                if (comp.length > 15) push(warns, 'ground-on-tops', `${nm(key)} x${comp.length} contiguous (e.g. @${comp[0]})`);
            }
        }

        const isCanopy = (n) => (n.endsWith('-top') && (n.includes('sakura') || n.startsWith('tree-'))) || n === 'sakura-small';
        const isTrunk = (n) => n.includes('base') && (n.includes('sakura') || n.startsWith('tree-'));
        const depthOf = (z, y, h) => z < 2 ? -1000 : (y + h) * 10 + (z >= 7 ? 11 : 0);
        const canopies = objects.filter(o => o.z >= 7 && isCanopy(nm(o.key)));
        const trunks = objects.filter(o => o.layer === 'Collidables' && isTrunk(nm(o.key)));
        const cover = {};
        for (const o of canopies) for (const [cx, cy] of o.cells) (cover[K(cx, cy)] = cover[K(cx, cy)] || new Set()).add(`${nm(o.key)}@${o.x},${o.y}`);
        for (const [c, list] of Object.entries(cover)) if (list.size > 1) push(errors, 'canopy-overlap', `${c}: ${[...list].sort().join(' + ')}`);
        const trunkCells = new Set();
        for (const t of trunks) {
            const cells = new Set(t.cells.map(([cx, cy]) => K(cx, cy)));
            for (const c of cells) trunkCells.add(c);
            const td = depthOf(5, t.y, t.h);
            for (const o of canopies) {
                if (!o.cells.some(([cx, cy]) => cells.has(K(cx, cy)))) continue;
                const cd = depthOf(7, o.y, o.h);
                if (td > cd) push(errors, 'trunk-over-canopy', `${nm(t.key)}@${t.x},${t.y}(d${td}) over ${nm(o.key)}@${o.x},${o.y}(d${cd})`);
            }
        }
        for (const o of canopies) {
            if (nm(o.key) === 'sakura-small') continue;
            let trunk = false;
            for (let a = 0; a < o.w; a++) if (trunkCells.has(K(o.x + a, o.y + o.h))) trunk = true;
            if (!trunk) push(warns, 'floating-canopy', `${nm(o.key)} @${o.x},${o.y}`);
        }

        return { room: roomKey, width: W, height: H, objects: objects.length, colliders: colliders.size, floor: floor.size, errors, warns };
    }

    /**
     * Every room's lint ERRORS as `check` problems, one per room and kind (issue #178): a
     * store whose shelves are cut off from its door (`shop-no-front`) has sound transporters
     * and NPCs, so only the map lint sees it. Warnings stay with `lint`.
     *   [{ room, text: "lint shop-no-front: 3 (Shelf @5,6 (front 5,7); ...)" }]
     */
    lintProblems() {
        const problems = [];
        for (const room of Object.keys(this.roomManager.rooms)) {
            const { errors } = this.lint(room);
            for (const kind of Object.keys(errors).sort()) {
                const items = errors[kind];
                problems.push({ room, text: `lint ${kind}: ${items.length} (${items.slice(0, 3).join('; ')}${items.length > 3 ? '; ...' : ''})` });
            }
        }
        return problems;
    }

    /**
     * Walk the world the way the game plays it. Rooms are RUNTIME rooms (a
     * stitched city stands in for its districts, in city cells):
     *   problems: [{ room, x, y, where: "Market 5,3" (the district's own cell), text, date }]
     *   reach:    { runtime room: Set "x,y" } - every cell that can be walked to
     * opts.npcs === false leaves everybody out (what the map itself allows).
     */
    survey(dates, opts) {
        dates = dates || [this.date];
        const problems = [];
        const reach = {};
        const saved = this.state();
        const rm = this.roomManager, rooms = rm.rooms;
        const keys = this.runtimeRooms();
        this.unpeopled = !!(opts && opts.npcs === false);
        const problem = (room, x, y, text, date) => problems.push(x === undefined ? { room, text }
            : { room, x, y, where: this.spot(room, x, y), text, date });
        const arrivals = {};
        const arrive = (room, x, y, via) => {
            const at = rm.resolve(room, x, y);
            (arrivals[at.room] = arrivals[at.room] || []).push({ x: at.x, y: at.y, via });
        };
        arrive(this.config.player.startRoom, this.config.player.startX, this.config.player.startY, 'spawn');
        // every place the game can start a player: each trip's home and stays, and where a
        // new player is put (next to the cast) on each surveyed day
        const starts = new Set([`${this.config.player.startRoom},${this.config.player.startX},${this.config.player.startY}`]);
        const start = (spot, via) => {
            if (!spot || !spot.room) return;
            // Trips.homeFor ignores a home or stay without a cell and falls back — for a stay,
            // to the trip's home, which can be a different room from where the group is
            if (!Number.isInteger(spot.x) || !Number.isInteger(spot.y)) {
                problem(spot.room, undefined, undefined, `${via} has no cell (x, y): players start somewhere else instead`);
                return;
            }
            const id = `${spot.room},${spot.x},${spot.y}`;
            if (starts.has(id)) return;
            starts.add(id);
            if (!rooms[spot.room]) problem(spot.room, undefined, undefined, `${via} names a missing room`);
            else arrive(spot.room, spot.x, spot.y, via);
        };
        // player.start* is the fallback the first trip's home replaced: the two are one place
        // (the editor's Spawn tool moves both, Trips.moveStart), so apart they are a mistake
        const p = this.config.player, first = this.trips[0] && Trips.cell(this.config, this.trips[0].home);
        if (first && (first.room !== p.startRoom || first.x !== p.startX || first.y !== p.startY)) {
            problem(first.room, undefined, undefined, `${this.trips[0].name} home (${first.room} ${first.x},${first.y}) is not ` +
                `player.start (${p.startRoom} ${p.startX},${p.startY}): the game opens at the trip's home, keep them the same`);
        }
        for (const trip of this.trips) {
            start(trip.home, `${trip.name} home`);
            for (const stay of trip.stays) start(stay, `${trip.name} stay`);
        }
        // … as the default sprite, and as each member of the day's trip (never counted as company)
        for (const date of dates) {
            const trip = Trips.forDate(this.trips, date);
            for (const played of [undefined, ...((trip && trip.members) || [])]) {
                start(WorldModel.startFor(this.config, date, { played }), `player start (${date}${played ? `, as ${played}` : ''})`);
            }
        }
        for (const k of keys) {
            for (const t of rooms[k].transporters) {
                if (!rooms[t.targetRoom]) problem(k, t.gridX, t.gridY, `targets missing room "${t.targetRoom}"`);
                else arrive(t.targetRoom, t.targetX, t.targetY, this.spot(k, t.gridX, t.gridY));
            }
        }
        for (const [k, st] of Object.entries(this.config.stations || {})) arrive(k, st.arrive[0], st.arrive[1], 'train');
        for (const [k, a] of Object.entries(this.config.airports || {})) if (rooms[k]) arrive(k, a.arrive[0], a.arrive[1], 'flight');
        for (const k of keys) {
            reach[k] = new Set();
            if (!arrivals[k]) { problem(k, undefined, undefined, 'nothing leads here'); continue; }
            for (const a of arrivals[k]) {
                this.enter(k, a.x, a.y);
                if (this.blocked.has(a.x + ',' + a.y) || !rm.checkBoundary(a.x, a.y)) {
                    problem(k, a.x, a.y, `arrival from ${a.via} lands on a blocked cell`);
                    continue;
                }
                if (reach[k].has(a.x + ',' + a.y)) continue;   // already flooded from an earlier way in
                for (const c of this.reachable()) reach[k].add(c);
            }
            this.enter(k, arrivals[k][0].x, arrivals[k][0].y);
            for (const t of this.room.transporters) {
                if (!reach[k].has(t.gridX + ',' + t.gridY)) problem(k, t.gridX, t.gridY, `transporter to ${t.targetRoom} cannot be walked to`);
            }
            // a city is one room only if its districts really join up
            for (const m of (rooms[k].city ? rooms[k].city.members : [])) {
                let any = false;
                for (const c of reach[k]) {
                    const [x, y] = c.split(',').map(Number);
                    if (x >= m.x && x < m.x + m.w && y >= m.y && y < m.y + m.h) { any = true; break; }
                }
                if (!any) problem(k, undefined, undefined, `district ${m.key} cannot be walked into`);
            }
        }
        const seen = new Set();
        for (const date of (this.unpeopled ? [] : dates)) {
            this.date = date;
            for (const k of keys) {
                if (!arrivals[k]) continue;
                this.enter(k, arrivals[k][0].x, arrivals[k][0].y);
                for (const n of this.room.npcs) {
                    const id = `${k} ${n.gridX},${n.gridY} ${n.name}`;
                    if (seen.has(id)) continue;
                    const near = 'nsew'.split('').some(d => reach[k].has((n.gridX + DIRS[d][0]) + ',' + (n.gridY + DIRS[d][1])));
                    const bad = this.blocked.has(n.gridX + ',' + n.gridY) ? 'stands on a collider' : !near ? 'cannot be walked up to' : null;
                    if (!bad) continue;
                    seen.add(id);
                    problem(k, n.gridX, n.gridY, `${n.name} ${bad} (${date})`, date);
                }
            }
        }
        this.unpeopled = false;
        this.date = saved.date;
        this.enter(saved.room, saved.x, saved.y);
        return { problems, reach };
    }

    /**
     * survey().reach handed back per config room, in that room's own cells:
     * { Market: ["x,y", ...] } - for a district, the cells of its rectangle
     * that can be walked to in the stitched city (tools/blog_to_npc.py is
     * pinned to this by its unit test).
     */
    reachByRoom(reach) {
        const out = {};
        for (const k of Object.keys(this.config.rooms)) {
            const at = this.roomManager.resolve(k, 0, 0);
            const r = this.roomManager.rooms[k];
            const w = r.worldWidth / this.GRID_SIZE, h = r.worldHeight / this.GRID_SIZE;
            out[k] = [];
            for (const c of (reach[at.room] || [])) {
                const [x, y] = c.split(',').map(Number);
                const lx = x - at.x, ly = y - at.y;
                if (lx >= 0 && ly >= 0 && lx < w && ly < h) out[k].push(lx + ',' + ly);
            }
        }
        return out;
    }
}

if (typeof window !== 'undefined') window.WorldModel = WorldModel;
