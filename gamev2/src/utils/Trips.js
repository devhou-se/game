/**
 * Trips — the devhouse trips, as data (issues #118, #131, #130, #96, #59).
 *
 * config.json carries a top-level `trips` list:
 *
 *   "trips": [{
 *     "id": "devhouse3", "name": "devhouse 3", "where": "Hokkaido",
 *     "start": "2027-02-18", "end": "2027-02-28",
 *     "members": ["bailey", ...],                       // sprite base names
 *     "home": { "room": "Sapporo", "x": 33, "y": 12 },  // where a player starts
 *     "stays": [                                        // optional: where the group is based
 *       { "from": "2027-02-18", "room": "Sapporo",   "x": 33, "y": 12 },
 *       { "from": "2027-02-25", "room": "Asahikawa", "x": 31, "y": 12 }
 *     ]
 *   }]
 *
 * The trip a GAME DATE belongs to (forDate: the latest trip that has opened
 * by then — so the days after a trip still belong to it — or the first trip
 * for a date before them all) decides everything that used to be hard-wired
 * to one Tokyo trip. A trip OPENS a little before it starts (`"lead"` days,
 * default Trips.LEAD): a post from the travel days on the way there is that
 * trip's, not the last word of the one before. On those lead-in days only
 * people who have posted are anywhere — the trip's base NPCs stand at the
 * base from its first day.
 *
 *   - which NPCs exist and which dated states apply (windowFor, used by
 *     resolveNpc in NpcStates.js): a base NPC marked `"trip": "<id>"` is
 *     only there on that trip's dates (and, with `"stay": "<room>"`, only
 *     while the group is based in that room), and states from before the
 *     date's trip — or before its current stay — are history, not applied.
 *     A dated state inside the window still places anybody anywhere, so a
 *     blog post moves its author as usual.
 *   - the day a visitor opens on (defaultDate): today while a trip is on,
 *     otherwise a day of the most recent trip that has posts.
 *   - where a player starts (startFor), who the intro names and where it
 *     says they are (memberNames, membersByRoom, whereText), the HUD date
 *     (dateLabel) and the Time Travel picker (jump).
 *
 * Everything here is a pure function of the config and a date, so
 * tools/test_game.js, tools/play.js and the studio run the same rules the
 * game does. A config with no `trips` behaves as it did before trips existed.
 */
class Trips {
    static ISO = /^\d{4}-\d{2}-\d{2}$/;

    /** config.trips, validated and sorted by start date. Bad entries are dropped. */
    static of(config) {
        const list = (config && Array.isArray(config.trips)) ? config.trips : [];
        return list
            .filter(t => t && t.id && Trips.ISO.test(t.start || '') && Trips.ISO.test(t.end || '') && t.start <= t.end)
            .map(t => Object.assign({}, t, {
                name: t.name || t.id,
                opens: Trips.addDays(t.start, -(Number.isInteger(t.lead) && t.lead >= 0 ? t.lead : Trips.LEAD)),
                members: Array.isArray(t.members) ? t.members.map(m => String(m).toLowerCase()) : [],
                stays: (Array.isArray(t.stays) ? t.stays : [])
                    .filter(s => s && s.room && Trips.ISO.test(s.from || ''))
                    .sort((a, b) => (a.from < b.from ? -1 : a.from > b.from ? 1 : 0)),
            }))
            .sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
    }

    /** How many days before its start a trip opens (its lead-in), unless it says `lead`. */
    static LEAD = 14;

    /** The trip that is on right now: `today` is between its start and end. */
    static live(trips, today) {
        return trips.find(t => today >= t.start && today <= t.end) || null;
    }

    /**
     * The trip a date belongs to: the latest one that has opened by then
     * (its lead-in days before the start included), or the first trip for a
     * date before any of them. null with no trips.
     */
    static forDate(trips, date) {
        if (!trips.length) return null;
        let found = trips[0];
        for (const t of trips) if ((t.opens || t.start) <= date) found = t;
        return found;
    }

    /** Is `date` one of the trip's own days (start to end)? */
    static during(trip, date) {
        return !!trip && date >= trip.start && date <= trip.end;
    }

    /** Where the group is based on `date`: the latest stay begun by then (else the first). */
    static stayFor(trip, date) {
        const stays = (trip && trip.stays) || [];
        if (!stays.length) return null;
        let found = stays[0];
        for (const s of stays) if (s.from <= date) found = s;
        return found;
    }

    /**
     * What a date can see: its trip, the stay the group is on, and `from` —
     * the first day whose dated states still count (the start of the stay,
     * or of the trip when it has no stays). null with no trips.
     *
     * `early` marks a lead-in day of a later trip: the trip has opened but
     * not started, so `from` is the day it opened and its base NPCs are not
     * standing anywhere yet. (Days before the FIRST trip are not early: they
     * show that trip's base cast, as they did before trips were data.)
     */
    static windowFor(trips, date) {
        const trip = Trips.forDate(trips, date);
        if (!trip) return null;
        const stay = Trips.stayFor(trip, date);
        if (date < trip.start && trip !== trips[0]) return { trip, stay, early: true, from: trip.opens || trip.start };
        return { trip, stay, early: false, from: stay && stay.from > trip.start ? stay.from : trip.start };
    }

    /**
     * Does an NPC's BASE definition exist in this window? An unmarked NPC
     * always does. One marked with `trip` only on that trip's dates (not on
     * its lead-in days), and with `stay` only while the group is based in
     * that room. (Dated states are applied on top either way — see
     * resolveNpc.)
     */
    static baseOn(npc, window) {
        if (!npc.trip || !window) return true;
        if (npc.trip !== window.trip.id || window.early) return false;
        return !npc.stay || !!(window.stay && window.stay.room === npc.stay);
    }

    /** The content days that belong to a trip, sorted (every dated day belongs to exactly one). */
    static daysOf(trips, trip, dates) {
        return dates.filter(d => Trips.forDate(trips, d).id === trip.id).sort();
    }

    /** Whole days since the epoch; UTC so daylight saving never skews a count. */
    static dayNumber(iso) {
        const [y, m, d] = iso.split('-').map(Number);
        return Math.round(Date.UTC(y, m - 1, d) / 86400000);
    }

    /** `iso` moved by `n` days. */
    static addDays(iso, n) {
        return new Date((Trips.dayNumber(iso) + n) * 86400000).toISOString().slice(0, 10);
    }

    /**
     * Map `today` onto one of `days` (sorted): count the days since the last
     * of them and wrap, so the day after the last day is the first again and
     * tomorrow shows the next one.
     */
    static cycle(today, days) {
        const n = days.length;
        return days[(((Trips.dayNumber(today) - Trips.dayNumber(days[n - 1]) - 1) % n) + n) % n];
    }

    /**
     * The game date when the URL names none.
     *
     * While a trip is on, that is today — post or no post, the trip's base
     * NPCs are standing where the group is staying. Otherwise today is
     * cycled over the content days of the most recent trip that has any
     * (falling back to the first trip with posts when none has opened yet),
     * so the two trips are never read as one fifteen-month span. With no
     * dated content at all, today.
     */
    static defaultDate(today, dates, trips) {
        if (Trips.live(trips, today)) return today;
        const posted = trips.map(t => Trips.daysOf(trips, t, dates)).filter(days => days.length);
        if (!posted.length) return today;
        let days = posted[0];
        for (const list of posted) {
            const t = Trips.forDate(trips, list[0]);
            if ((t.opens || t.start) <= today) days = list;
        }
        return Trips.cycle(today, days);
    }

    /** "bailey" -> "Bailey". */
    static displayName(base) {
        const s = String(base || '');
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    /** A trip's members as display names, alphabetical. */
    static memberNames(trip) {
        return ((trip && trip.members) || []).map(Trips.displayName).sort((a, b) => a.localeCompare(b));
    }

    /** ["A", "B", "C"] -> "A, B and C". */
    static list(words) {
        return words.length > 1 ? `${words.slice(0, -1).join(', ')} and ${words[words.length - 1]}` : words.join('');
    }

    static baseOf(spriteKey) {
        return String(spriteKey || '').replace(/_(front|back|side)$/, '');
    }

    /**
     * Where the trip's members are standing on `date`: one entry per room
     * that has any, in config order — { room, name, members: [{ name, x, y }] }.
     * Only the travelling cast counts (a fixture like the izakaya's opponent
     * does not), and never `opts.played`, the member the player is playing as.
     */
    static membersByRoom(config, date, opts) {
        const trips = Trips.of(config);
        const trip = Trips.forDate(trips, date);
        const members = new Set((trip && trip.members) || []);
        const played = (opts && opts.played) || null;
        const game = (config && config.game) || {};
        const cx = Math.floor((game.worldWidth || 0) / (game.gridSize || 64) / 2);
        const cy = Math.floor((game.worldHeight || 0) / (game.gridSize || 64) / 2);
        const out = [];
        for (const [room, def] of Object.entries((config && config.rooms) || {})) {
            const here = [];
            for (const raw of def.npcs || []) {
                const npc = resolveNpc(raw, date, trips);
                if (!npc || npc.drinkingGameOpponent) continue;
                const base = Trips.baseOf(npc.sprite);
                if (!members.has(base) || base === played) continue;
                here.push({
                    name: npc.name,
                    x: npc.gridX != null ? npc.gridX : cx + (npc.gridOffsetX || 0),
                    y: npc.gridY != null ? npc.gridY : cy + (npc.gridOffsetY || 0),
                });
            }
            if (here.length) out.push({ room, name: def.name || room, members: here });
        }
        return out;
    }

    /**
     * The intro's "where is everybody" sentence. `groups` is membersByRoom,
     * `here` the room the player is standing in. People in the player's own
     * room are named; other rooms are listed (three at most — a few places
     * to head for, not an itinerary).
     */
    static whereText(groups, here) {
        if (!groups.length) return 'They are out and about.';
        const names = (g) => g.members.map(m => m.name).sort((a, b) => a.localeCompare(b));
        const mine = groups.find(g => g.room === here);
        const others = groups.filter(g => g.room !== here);
        const places = Trips.list(others.slice(0, 3).map(g => g.name));
        if (!mine) return `Today they are in ${places}.`;
        const who = names(mine);
        const be = (n) => (n === 1 ? 'is' : 'are');
        if (!others.length) {
            return who.length > 2
                ? `Today everyone is here in ${mine.name}.`
                : `Today ${Trips.list(who)} ${be(who.length)} here in ${mine.name}.`;
        }
        const away = others.reduce((n, g) => n + g.members.length, 0);
        const rest = others.length === 1 && away <= 2
            ? `${Trips.list(names(others[0]))} ${be(away)} in ${places}`
            : `the others are in ${places}`;
        return `Today ${Trips.list(who)} ${be(who.length)} here in ${mine.name}, and ${rest}.`;
    }

    /** A { room, x, y } that names a room the config has, or null. */
    static cell(config, spot) {
        if (!spot || !spot.room || !config.rooms || !config.rooms[spot.room]) return null;
        if (!Number.isInteger(spot.x) || !Number.isInteger(spot.y)) return null;
        return { room: spot.room, x: spot.x, y: spot.y };
    }

    /**
     * Where a returning player starts on `date`: where the group is staying
     * (the stay's cell), else the trip's home, else config.player's start.
     */
    static homeFor(config, date) {
        const trip = Trips.forDate(Trips.of(config), date);
        const p = (config && config.player) || {};
        return Trips.cell(config, Trips.stayFor(trip, date)) || Trips.cell(config, trip && trip.home) ||
            { room: p.startRoom, x: p.startX, y: p.startY };
    }

    /** How close (in cells, either axis) a start cell must be to count as "next to" someone. */
    static NEAR = 6;

    /**
     * Where the player starts on `date` — { room, x, y }, the same terms a
     * door target is written in.
     *
     * A returning player (`opts.newPlayer` false) always starts at the
     * trip's home for that date, wherever the cast is: nothing about their
     * game moves because the cast did.
     *
     * A NEW player starts where they can meet someone (issues #96, #59): the
     * room with the most members on that date — a tie goes to the room
     * fewest doors and train rides from home (so the home room itself
     * first), then config order — and never counting `opts.played`, the
     * member they are playing as. In the home room they stand on the home
     * cell when somebody is within NEAR cells of it; otherwise on the
     * walkable cell closest to the group that can be walked to from the
     * room's arrivals (see standNear). Nobody anywhere, or no such cell:
     * the home.
     */
    static startFor(config, date, opts) {
        const home = Trips.homeFor(config, date);
        if (!opts || !opts.newPlayer) return home;
        const groups = Trips.membersByRoom(config, date, { played: opts.played });
        if (!groups.length) return home;
        const hops = Trips.hopsFrom(config, home.room);
        const far = (g) => (g.room in hops ? hops[g.room] : Infinity);
        let best = null;
        for (const g of groups) {
            const better = !best || g.members.length > best.members.length ||
                (g.members.length === best.members.length && far(g) < far(best));
            if (better) best = g;
        }
        const gap = (m, x, y) => Math.max(Math.abs(m.x - x), Math.abs(m.y - y));
        if (best.room === home.room && best.members.some(m => gap(m, home.x, home.y) <= Trips.NEAR)) return home;
        const spot = Trips.standNear(config, best.room, best.members, best.room === home.room ? home : null);
        return spot ? { room: best.room, x: spot[0], y: spot[1] } : home;
    }

    /**
     * Is a trip member (other than `played`) within NEAR cells of (x, y) in
     * `room` on `date`? What a start cell is for.
     */
    static hasCompany(config, date, room, x, y, played) {
        const group = Trips.membersByRoom(config, date, { played }).find(g => g.room === room);
        return !!group && group.members.some(m => Math.max(Math.abs(m.x - x), Math.abs(m.y - y)) <= Trips.NEAR);
    }

    /**
     * How many room changes each room is from `from`: a door is one, and so
     * is a train ride between any two stations. Rooms that cannot be reached
     * are left out.
     */
    static hopsFrom(config, from) {
        const stations = Object.keys(config.stations || {});
        const next = (room) => {
            const out = ((config.rooms[room] || {}).transporters || []).map(t => t.targetRoom);
            return stations.includes(room) ? out.concat(stations) : out;
        };
        const hops = { [from]: 0 }, queue = [from];
        for (let i = 0; i < queue.length; i++) {
            for (const room of next(queue[i])) {
                if (room in hops || !config.rooms[room]) continue;
                hops[room] = hops[queue[i]] + 1;
                queue.push(room);
            }
        }
        return hops;
    }

    /**
     * Every cell a walker can arrive on in a room: door targets from every
     * room's transporters, and the platform cell of a station room.
     */
    static arrivals(config, room) {
        const cells = [];
        for (const def of Object.values(config.rooms || {})) {
            for (const t of def.transporters || []) {
                if (t.targetRoom === room) cells.push([t.targetX, t.targetY]);
            }
        }
        const station = (config.stations || {})[room];
        if (station && Array.isArray(station.arrive)) cells.push([station.arrive[0], station.arrive[1]]);
        return cells;
    }

    /**
     * The cell to stand on to be next to `people` ([{ x, y }]) in a room, or
     * null: flood the room's walkable cells from its arrivals (and `extra`,
     * a known-good cell), then take the one nearest to anybody that is at
     * least two cells from everybody — close enough to see them, not in
     * their way. Of several as near, the one the shortest walk from an
     * arrival: on the way from the door to the people.
     *
     * Walkable means what it means to the collision system: a Floor tile, no
     * tile on a collision layer, inside the room and its boundary, and not a
     * door (which would send the player straight out again) or an NPC.
     */
    static standNear(config, room, people, extra) {
        const def = config.rooms[room];
        const grid = (config.game && config.game.gridSize) || 64;
        const W = Math.round((def.worldWidth || config.game.worldWidth) / grid);
        const H = Math.round((def.worldHeight || config.game.worldHeight) / grid);
        const K = (x, y) => x + ',' + y;
        const floor = new Set(), solid = new Set();
        for (const layer of def.layers || []) {
            const into = layer.collision ? solid : (layer.name === 'Floor' ? floor : null);
            if (into) for (const xy of Object.keys(layer.tiles || {})) into.add(xy);
        }
        for (const t of def.transporters || []) solid.add(K(t.gridX, t.gridY));
        for (const p of people) solid.add(K(p.x, p.y));
        const poly = def.boundary && def.boundary.length >= 3 ? def.boundary : null;
        const inside = (x, y) => {
            if (!poly) return true;
            let hit = false;
            for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
                const [xi, yi] = poly[i], [xj, yj] = poly[j];
                if ((yi > y + 0.5) !== (yj > y + 0.5) &&
                    x + 0.5 < (xj - xi) * (y + 0.5 - yi) / (yj - yi) + xi) hit = !hit;
            }
            return hit;
        };
        const ok = (x, y) => x >= 0 && y >= 0 && x < W && y < H &&
            floor.has(K(x, y)) && !solid.has(K(x, y)) && inside(x, y);

        const seeds = Trips.arrivals(config, room);
        if (extra) seeds.push([extra.x, extra.y]);
        const seen = new Set(), queue = [];
        for (const [x, y] of seeds) {
            if (ok(x, y) && !seen.has(K(x, y))) { seen.add(K(x, y)); queue.push([x, y]); }
        }
        let best = null;
        for (let i = 0; i < queue.length; i++) {
            const [x, y] = queue[i];
            const d = Math.min(...people.map(p => Math.max(Math.abs(p.x - x), Math.abs(p.y - y))));
            // the flood runs in walking order, so the first cell found at a distance wins it
            if (d >= 2 && (!best || d < best.d)) best = { x, y, d };
            for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                if (!ok(nx, ny) || seen.has(K(nx, ny))) continue;
                seen.add(K(nx, ny));
                queue.push([nx, ny]);
            }
        }
        return best ? [best.x, best.y] : null;
    }

    /**
     * The HUD's date: "devhouse 3 · February 20 2027" on one of a trip's own
     * days, the bare date on any other. `format` is formatGameDate.
     *
     * `fits(label)`, when given, says whether a label has room in the HUD:
     * the trip's name is dropped when it does not (a long room name such as
     * "Don Takote · Sapporo" leaves no room for it before the menu button),
     * so the wallet after the date is never pushed under the button.
     */
    static dateLabel(trips, iso, format, fits) {
        const trip = Trips.forDate(trips, iso);
        const bare = format(iso);
        if (!Trips.during(trip, iso)) return bare;
        const full = `${trip.name} · ${bare}`;
        return !fits || fits(full) ? full : bare;
    }

    /**
     * The day Time Travel lands on when it jumps to a trip: its first day
     * with posts, or its first day when it has none yet.
     */
    static landing(trips, trip, dates) {
        return Trips.daysOf(trips, trip, dates).find(d => Trips.during(trip, d)) || trip.start;
    }

    /**
     * Time Travel's trip jump: from `iso`, the landing day of the next
     * (`dir` > 0) or previous trip, or null when there is none that way.
     * From a day between two trips, "previous" is the trip just ended.
     */
    static jump(trips, iso, dir, dates) {
        const target = dir > 0
            ? trips.find(t => t.start > iso)
            : [...trips].reverse().find(t => t.end < iso);
        return target ? Trips.landing(trips, target, dates) : null;
    }
}

if (typeof window !== 'undefined') window.Trips = Trips;
