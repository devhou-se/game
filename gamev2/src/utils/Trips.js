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
 * base from its first day. Nobody has arrived, and the game says so (issue
 * #164, leadIn): the HUD counts the days down ("devhouse 3 in 8 days", or
 * "in 8d" where the line is tight), the
 * intro says when and where the trip starts, and a player with nobody to
 * stand next to starts at the trip's first base, where they will arrive.
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
 *   - where a player starts (startFor: beside the group, new player or
 *     returning — issue #166), who the intro names and where it says they
 *     are (memberNames, membersByRoom, whereText), the HUD date (dateLabel)
 *     and the Time Travel picker (jump).
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

    /**
     * The lead-in a date is in (issue #164): { trip, days, stay } — the trip
     * that has opened but not started, how many days until it does, and its
     * first base — or null on any other day. The same days windowFor calls
     * `early`: nobody is standing at the base yet.
     */
    static leadIn(trips, date) {
        const w = Trips.windowFor(trips, date);
        if (!w || !w.early) return null;
        return { trip: w.trip, days: Trips.dayNumber(w.trip.start) - Trips.dayNumber(date), stay: Trips.stayFor(w.trip, w.trip.start) };
    }

    /** The trip `today` is in the lead-in of — opened, not started — or null. */
    static upcoming(trips, today) {
        const lead = Trips.leadIn(trips, today);
        return lead ? lead.trip : null;
    }

    /** "February 18": a day without its year, for a sentence. */
    static dayText(iso) {
        return formatGameDate(iso).replace(/ \d+$/, '');
    }

    /** 1 -> "tomorrow", 8 -> "in 8 days". */
    static inDays(n) {
        return n === 1 ? 'tomorrow' : `in ${n} days`;
    }

    /**
     * The intro's sentence for a lead-in day — "devhouse 3 starts here in
     * Sapporo on February 18." — or '' on any other day. The place is the
     * trip's first base by its display name (else where the trip goes), and
     * "here" when that is the room the player is standing in.
     */
    static arrivalText(config, date, here) {
        const lead = Trips.leadIn(Trips.of(config), date);
        if (!lead) return '';
        const room = lead.stay && lead.stay.room, def = room && config.rooms && config.rooms[room];
        const place = def ? (def.name || room) : lead.trip.where;
        const where = place ? ` ${def && room === here ? 'here ' : ''}in ${place}` : '';
        return `${lead.trip.name} starts${where} on ${Trips.dayText(lead.trip.start)}.`;
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
     * so the two trips are never read as one fifteen-month span. Once that
     * trip is over only its own days (start to end) are cycled, when it
     * has any: not a post from the road in the days before it. With no
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
        // a trip that is over is shown by its own days: a post from the road
        // in its lead-in ("devhouse 3 in 6 days") is not a day to open on
        const trip = Trips.forDate(trips, days[0]);
        const own = trip && today > trip.end ? days.filter(d => Trips.during(trip, d)) : [];
        return Trips.cycle(today, own.length ? own : days);
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
     *
     * `arrival` is arrivalText's sentence on a lead-in day (issue #164): with
     * nobody anywhere it is the answer — they have not arrived yet — and
     * with somebody who has posted from the road it follows where they are.
     */
    static whereText(groups, here, arrival) {
        const text = Trips.placesText(groups, here);
        if (!arrival) return text || 'They are out and about.';
        return text ? `${text} ${arrival}` : `They have not arrived yet: ${arrival}`;
    }

    /** whereText's sentence about the people who are somewhere; '' with nobody. */
    static placesText(groups, here) {
        if (!groups.length) return '';
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
     * The trip's own cell on `date`: where the group is staying (the stay's
     * cell — the first stay on a lead-in day), else the trip's home, else
     * config.player's start. Where a player starts when there is nobody to
     * stand next to (startFor).
     */
    static homeFor(config, date) {
        const trip = Trips.forDate(Trips.of(config), date);
        const p = (config && config.player) || {};
        return Trips.cell(config, Trips.stayFor(trip, date)) || Trips.cell(config, trip && trip.home) ||
            { room: p.startRoom, x: p.startX, y: p.startY };
    }

    /**
     * Move the start cell (the editor's Spawn tool, issue #169): config.player's
     * start, and with it every trip `home` and `stays` cell that stood on the
     * old one — those are what decide where the game opens (homeFor), and
     * player.start* is only their fallback. Returns the names of the trips
     * that moved; a trip that starts somewhere else is left where it is.
     */
    static moveStart(config, room, x, y) {
        const p = config.player || (config.player = {});
        const was = (s) => !!s && s.room === p.startRoom && s.x === p.startX && s.y === p.startY;
        const moved = [];
        for (const trip of (Array.isArray(config.trips) ? config.trips : [])) {
            if (!trip) continue;
            const spots = [trip.home, ...(Array.isArray(trip.stays) ? trip.stays : [])].filter(was);
            for (const s of spots) { s.room = room; s.x = x; s.y = y; }
            if (spots.length) moved.push(trip.name || trip.id);
        }
        p.startRoom = room; p.startX = x; p.startY = y;
        return moved;
    }

    /** How close (in cells, either axis) a start cell must be to count as "next to" someone. */
    static NEAR = 6;

    /**
     * Where the player starts on `date` — { room, x, y }, the same terms a
     * door target is written in.
     *
     * Every player — new (issues #96, #59) or returning, after a reload or
     * a Time Travel hop (issue #166: there is no saved position to restore,
     * and the trip's home has nobody near it on most days) — starts where
     * they can meet someone: the
     * room with the most members on that date — a tie goes to the room
     * fewest doors and train rides from home (so the home room itself
     * first), then config order — and never counting `opts.played`, the
     * member they are playing as. In the home room they stand on the home
     * cell when somebody is within NEAR cells of it; otherwise on the
     * walkable cell closest to the group that can be walked to from the
     * room's arrivals (see standNear). Nobody anywhere (a lead-in day
     * nobody has posted on: the home is the base they will arrive at), or
     * no such cell: the home.
     */
    static startFor(config, date, opts) {
        const home = Trips.homeFor(config, date);
        const groups = Trips.membersByRoom(config, date, { played: opts && opts.played });
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
     * "Anybody" is the biggest cluster of them (crowd): with two on the bay
     * promenade and one alone on a flight of steps, the cell is beside the
     * two. And it is ordinary ground where there is any (plain): not a stair
     * tile, and not a deck over water (a bridge, a pier) — a player who
     * opens the game half way up a staircase reads as a bug.
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
        const floor = new Set(), solid = new Set(), odd = new Set();
        for (const layer of def.layers || []) {
            const into = layer.collision ? solid : (layer.name === 'Floor' ? floor : null);
            if (into) for (const xy of Object.keys(layer.tiles || {})) into.add(xy);
            if (layer.collision) continue;
            for (const [xy, tile] of Object.entries(layer.tiles || {})) {
                if (!Trips.plain(layer.name, tile)) odd.add(xy);
            }
        }
        for (const t of def.transporters || []) solid.add(K(t.gridX, t.gridY));
        for (const p of people) solid.add(K(p.x, p.y));
        const near = Trips.crowd(people);
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
        let best = null, any = null;
        for (let i = 0; i < queue.length; i++) {
            const [x, y] = queue[i];
            const gap = (p) => Math.max(Math.abs(p.x - x), Math.abs(p.y - y));
            const d = Math.min(...near.map(gap));
            // the flood runs in walking order, so the first cell found at a distance wins it;
            // two cells from EVERYBODY, also the ones outside the crowd
            if (d >= 2 && people.every(p => gap(p) >= 2)) {
                if (!any || d < any.d) any = { x, y, d };
                if (!odd.has(K(x, y)) && (!best || d < best.d)) best = { x, y, d };
            }
            for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
                if (!ok(nx, ny) || seen.has(K(nx, ny))) continue;
                seen.add(K(nx, ny));
                queue.push([nx, ny]);
            }
        }
        // ordinary ground unless the only cells in sight of them (NEAR) are steps or a deck
        if (!best || (best.d > Trips.NEAR && any.d <= Trips.NEAR)) best = any;
        return best ? [best.x, best.y] : null;
    }

    /**
     * The people ([{ x, y }]) to stand next to: the biggest cluster of them,
     * a cluster being people within NEAR cells of one another, in a chain.
     * Clusters as big as each other are all kept (standNear then takes the
     * one nearest the door).
     */
    static crowd(people) {
        const left = [...people], clusters = [];
        while (left.length) {
            const cluster = [left.shift()];
            for (let i = 0; i < cluster.length; i++) {
                for (let j = left.length - 1; j >= 0; j--) {
                    const a = cluster[i], b = left[j];
                    if (Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y)) <= Trips.NEAR) cluster.push(...left.splice(j, 1));
                }
            }
            clusters.push(cluster);
        }
        const most = Math.max(0, ...clusters.map(c => c.length));
        return clusters.filter(c => c.length === most).flat();
    }

    /**
     * Is a tile (its key, on a layer that is not a collision layer) ordinary
     * ground to start a player on? Not a stair tile ("castle-stairs_0_1")
     * and not anything on the Water layer: a walkable cell with water under
     * it is the deck of a bridge or a pier.
     */
    static plain(layer, tile) {
        return layer !== 'Water' && !/stairs/.test(String(tile));
    }

    /**
     * The HUD's date: the bare date ("February 20 2027"), on a trip's own
     * days too — the HUD never names the trip an ordinary day belongs to
     * (issue #163: it used to lead the date where the row had room, so it
     * came and went from room to room). The one exception is a lead-in day,
     * "devhouse 3 in 8 days | February 10 2027" (issue #164: the reason the
     * base is empty — "devhouse 3 in 8d | …", then "devhouse 3 soon | …",
     * where the count does not fit; the bar's separator is " | " throughout,
     * issue #207). `format` is formatGameDate.
     *
     * `fits(label)`, when given, says whether a label has room in the HUD:
     * the countdown is shortened and then dropped when it does not, so the
     * wallet after the date is never pushed under the menu button.
     */
    static dateLabel(trips, iso, format, fits) {
        const bare = format(iso);
        // the countdown is this line: `const lead = null;` and the HUD is the bare date every day
        const lead = Trips.leadIn(trips, iso);
        if (!lead) return bare;
        // the count, then shorter ways to say it, then nothing
        return Trips.countdowns(lead)
            .map(count => `${count} | ${bare}`)
            .find(label => !fits || fits(label)) || bare;
    }

    /** A lead-in's countdown, longest first: "devhouse 3 in 8 days", "devhouse 3 in 8d", "devhouse 3 soon". */
    static countdowns(lead) {
        return [Trips.inDays(lead.days), `in ${lead.days}d`, 'soon'].map(when => `${lead.trip.name} ${when}`);
    }

    /**
     * A lead-in day's countdown on its own, with no date after it —
     * "devhouse 3 in 8d" — or null on any other day. It stands IN PLACE of
     * the date on a landscape phone's one-row bar, which has no room for
     * both (GameScene.layoutHUD): the countdown is the reason the base is
     * empty, and the date is one tap away in Time Travel, which that
     * segment opens. The longest form `fits(label)` allows, or null when
     * none does.
     */
    static countdown(trips, iso, fits) {
        const lead = Trips.leadIn(trips, iso);
        return (lead && Trips.countdowns(lead).find(label => !fits || fits(label))) || null;
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
