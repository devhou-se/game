/**
 * Places - the towns of the game as real places in Japan (issue #211).
 *
 * The Map overlay is a map of Japan with one dot per town. Which towns, and
 * where, is data — `config.json` top-level `places`:
 *
 *   "places": { "TokyoCity": { "geo": [139.77, 35.68], "label": "Tokyo" },
 *               "Osaka":     { "geo": [135.50, 34.69], "label": "Osaka" }, ... }
 *
 * A key is a `cities` key (the whole stitched city is ONE dot: Tokyo's
 * districts are "Tokyo") or a room key; `geo` is [longitude, latitude].
 * An entry whose key is neither is skipped, so a town's geo can be written
 * before its room lands. A town with no entry has no dot: the made-up ones
 * (Inaka, Yukimura) are not on the map of Japan, and are reached as ever by
 * train from Tokyo Station.
 *
 * A place that is not in Japan is `"overseas": true` (issue #218: the home
 * city, reached by air). It is still one marker with a label, a presence dot
 * and the player's ring, but it is drawn as a plane out in the sea at the
 * map's edge: its `geo` says where on the picture, not where in the world.
 * An airport room belongs to the place of the room it serves (config
 * `airports.<key>.serves`): Haneda is in Tokyo's dot.
 *
 * Pure functions of the config (and the map's metadata, assets/map/japan.json,
 * written by tools/make_japan_map.py): tools/tests/japan-map.test.js runs the
 * same code. GameScene.showMap draws what these decide.
 */
class Places {
    /** Every place that has a dot: [{ key, label, lon, lat, rooms, overseas }], in config order. */
    static list(config) {
        const out = [];
        const rooms = (config && config.rooms) || {}, cities = (config && config.cities) || {};
        for (const [key, p] of Object.entries((config && config.places) || {})) {
            const geo = p && p.geo;
            if (!Array.isArray(geo) || geo.length !== 2 || !geo.every(Number.isFinite)) continue;
            const city = cities[key];
            if (!city && !rooms[key]) continue;          // its room has not been built yet
            out.push({
                key, lon: geo[0], lat: geo[1],
                label: p.label || (city ? city.name : rooms[key].name) || key,
                rooms: city ? (city.rooms || []).map(m => m.room) : [key],
                overseas: !!p.overseas,
            });
        }
        return out;
    }

    /**
     * The place a room belongs to, or null: the room itself, the city it is
     * a district of, the town its station serves, the town its airport
     * serves, or — for an interior — wherever its doors lead (a konbini is
     * in its town). A room that is its
     * own place wins over the city it is stitched into, so the districts of
     * a region can be separate dots.
     */
    static of(config, room) {
        const list = Places.list(config);
        const direct = (r) => {
            const own = list.find(p => p.key === r);
            if (own) return own.key;
            const within = list.find(p => p.rooms.includes(r));
            return within ? within.key : null;
        };
        const seen = new Set();
        let front = [room];
        for (let hop = 0; hop < 4 && front.length; hop++) {
            const next = [];
            for (const r of front) {
                if (seen.has(r) || !config.rooms || !config.rooms[r]) continue;
                seen.add(r);
                const key = direct(r);
                if (key) return key;
                const station = (config.stations || {})[r];
                if (station && station.town) next.push(station.town);
                const airport = (config.airports || {})[r];
                if (airport && airport.serves) next.push(airport.serves);
                for (const t of config.rooms[r].transporters || []) next.push(t.targetRoom);
            }
            front = next;
        }
        return null;
    }

    /**
     * The places with somebody in them on `date`, as a Set of keys: the
     * trip's members, wherever Trips.membersByRoom has them standing (the
     * intro's "where the friends are"), never `opts.played`. Who and how
     * many is not said: the player goes and finds out.
     */
    static present(config, date, opts) {
        const out = new Set();
        for (const group of Trips.membersByRoom(config, date, opts)) {
            const key = Places.of(config, group.room);
            if (key) out.add(key);
        }
        return out;
    }

    /**
     * Where a traveller sets foot in a place — { room, x, y } in district
     * cells, or null: outside its station's door (the first station on the
     * line that serves it), else outside its airport's door, else any door
     * into it.
     */
    static arrival(config, key) {
        const place = Places.list(config).find(p => p.key === key);
        if (!place) return null;
        const stations = Object.entries(config.stations || {})
            .filter(([, st]) => place.rooms.includes(st.town))
            .sort((a, b) => (a[1].order || 0) - (b[1].order || 0));
        for (const [stationRoom] of stations) {
            const door = ((config.rooms[stationRoom] || {}).transporters || []).find(t => place.rooms.includes(t.targetRoom));
            if (door) return { room: door.targetRoom, x: door.targetX, y: door.targetY };
        }
        for (const [airportRoom, airport] of Object.entries(config.airports || {})) {
            if (!place.rooms.includes(airport.serves)) continue;
            const door = ((config.rooms[airportRoom] || {}).transporters || []).find(t => place.rooms.includes(t.targetRoom));
            if (door) return { room: door.targetRoom, x: door.targetX, y: door.targetY };
        }
        for (const room of place.rooms) {
            const cell = Trips.arrivals(config, room)[0];
            if (cell) return { room, x: cell[0], y: cell[1] };
        }
        return null;
    }

    /**
     * "you are here: ..." for a room: its display name, with the town when
     * the name does not already say it, or that it is off this map.
     */
    static whereText(config, room) {
        const name = ((config.rooms || {})[room] || {}).name || room;
        const town = Places.list(config).find(p => p.key === Places.of(config, room));
        if (!town) return `${name} (not on this map)`;
        const far = town.overseas ? ', overseas' : '';
        return name.includes(town.label) ? `${name}${far && ` (${far.slice(2)})`}` : `${name} (in ${town.label}${far})`;
    }

    /** Canvas px (before text growth) a town's marker reaches from its centre: nothing else may come nearer. */
    static reach(here, present) {
        return here ? Places.DOT_YOU * Places.YOU_PULSE + 2 : present ? Places.DOT_HALO : Places.DOT;
    }

    /** [x, y] on the map image (its own px) of a longitude / latitude. */
    static project(meta, lon, lat) {
        return [(lon - meta.lon0) * meta.pxPerLon, (meta.lat0 - lat) * meta.pxPerLat];
    }

    /** The place whose dot is nearest an image point, within `reach` image px; or null. */
    static nearest(meta, places, ix, iy, reach) {
        let best = null, bestD = reach;
        for (const p of places) {
            const [x, y] = Places.project(meta, p.lon, p.lat);
            const d = Math.hypot(x - ix, y - iy);
            if (d <= bestD) { best = p; bestD = d; }
        }
        return best;
    }

    /**
     * Where each dot's label goes. `dots` are [{ key, x, y, r, w, h }]: the
     * dot's centre and radius and its label's size, in the px of `bounds`
     * ({ x, y, w, h }, the map on screen). Returns { key: { x, y, leader } }
     * — the label's centre, and whether it stands off far enough to want a
     * line back to its dot.
     *
     * A label never covers another label or anybody's dot and never leaves
     * the map. Each tries beside its dot first (right, left, above, below,
     * then the diagonals) and then the same eight further out; the most
     * hemmed-in dots choose first. `fits` is false on a label for which no
     * such spot exists (it is then put beside its dot regardless).
     */
    static layout(dots, bounds) {
        const hit = (a, b) => a.x1 > b.x0 && a.x0 < b.x1 && a.y1 > b.y0 && a.y0 < b.y1;
        const dotBox = (d) => ({ x0: d.x - d.r - 1, y0: d.y - d.r - 1, x1: d.x + d.r + 1, y1: d.y + d.r + 1 });
        const crowd = (d) => Math.min(...dots.filter(o => o !== d).map(o => Math.hypot(o.x - d.x, o.y - d.y)), Infinity);
        const order = dots.slice().sort((a, b) => crowd(a) - crowd(b) || (a.key < b.key ? -1 : 1));
        const taken = [], out = {};
        for (const d of order) {
            const others = dots.filter(o => o !== d).map(dotBox);
            let chosen = null;
            for (let ring = 0; ring < Places.RINGS && !chosen; ring++) {
                const gap = d.r + Places.LABEL_GAP + ring * Places.RING_STEP;
                const dx = gap + d.w / 2, dy = gap + d.h / 2;
                // a diagonal label sits on the dot's corner, not out past both edges
                const sx = d.r * 0.5 + ring * Places.RING_STEP + d.w / 2;
                for (const [ox, oy] of [[dx, 0], [-dx, 0], [0, -dy], [0, dy], [sx, -dy], [sx, dy], [-sx, -dy], [-sx, dy]]) {
                    const cx = d.x + ox, cy = d.y + oy;
                    const box = { x0: cx - d.w / 2, y0: cy - d.h / 2, x1: cx + d.w / 2, y1: cy + d.h / 2 };
                    if (box.x0 < bounds.x || box.y0 < bounds.y || box.x1 > bounds.x + bounds.w || box.y1 > bounds.y + bounds.h) continue;
                    if (others.some(o => hit(box, o)) || taken.some(t => hit(box, t))) continue;
                    chosen = { x: cx, y: cy, leader: ring > 0, fits: true, box };
                    break;
                }
            }
            if (!chosen) {
                const cx = d.x + d.r + Places.LABEL_GAP + d.w / 2;
                chosen = { x: cx, y: d.y, leader: false, fits: false,
                    box: { x0: cx - d.w / 2, y0: d.y - d.h / 2, x1: cx + d.w / 2, y1: d.y + d.h / 2 } };
            }
            taken.push(chosen.box);
            out[d.key] = chosen;
        }
        return out;
    }
}

/** Canvas px between a dot and its label; how much further each ring of tries stands off; how many rings. */
Places.LABEL_GAP = 4;
Places.RING_STEP = 14;
Places.RINGS = 10;
/** Dot radii on the Map overlay, canvas px before UIScale's text growth: a town, a town with people in it and its halo, the ring round the player's. */
Places.DOT = 5;
Places.DOT_PRESENT = 7;
Places.DOT_HALO = 11;
Places.DOT_YOU = 12;
/** How far the player's ring swells as it pulses. */
Places.YOU_PULSE = 1.2;
/** The Map's legend line (worded through Hints.text). */
Places.LEGEND = 'red dot: friends in town   ·   gold ring: you';
/** Half the wingspan of an overseas place's plane marker, canvas px before text growth. */
Places.PLANE = 9;

if (typeof window !== 'undefined') window.Places = Places;
