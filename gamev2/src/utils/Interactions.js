const Interactions = {
    RULES: [
        { kind: 'vending', group: 'shop', pattern: /vending-machine/, footprint: true },
        { kind: 'counter', group: 'shop', pattern: /^(blue-shrine-platform-base|office-counter)/, footprint: true, room: 'konbini' },
        // the 7-Eleven kiosk inside a station (tools/generate_stations.py): the whole
        // booth is the till, in any room - a station is not an `interior`
        { kind: 'counter', group: 'shop', pattern: /^station-kiosk/, footprint: true },
        // an airport (tools/generate_airports.py, issue #218): the pub's bar is a till like the
        // kiosk, and the gate or the board beside it opens the flights (GameScene, StationPicker)
        { kind: 'pub', group: 'shop', pattern: /^airport-bar/, footprint: true },
        { kind: 'flights', group: 'flights', pattern: /^airport-(gate|board)/, footprint: true },
        { kind: 'drinks', group: 'shop', pattern: /^office-(shelf-drinks|shelf-glass|fridge|freezer)/, footprint: true, room: 'konbini' },
        { kind: 'snacks', group: 'shop', pattern: /^office-shelf-snacks/, footprint: true, room: 'konbini' },
        { kind: 'venue', group: 'shop', pattern: /^office-counter2/, footprint: true, room: 'venue' },
        { kind: 'water', group: 'water', pattern: /^office-watercooler/, footprint: true, room: 'konbini' },
        { kind: 'pond', group: 'pond', pattern: /^pond-autotile/ },
        { kind: 'clock', group: 'clock', pattern: /^(office-clock|office-poster-menu)/ },
        // a home's furniture (issue #208, tools/generate_houses.py): a bump says one line
        // (`say`, shown as a toast by GameScene) and nothing else happens
        { kind: 'kotatsu', group: 'flavour', pattern: /^home-kotatsu/, footprint: true, say: 'the kotatsu is warm. you could stay under it all winter' },
        { kind: 'hearth', group: 'flavour', pattern: /^home-irori/, footprint: true, say: 'the kettle over the hearth is just starting to sing' },
        { kind: 'stove', group: 'flavour', pattern: /^home-stove/, footprint: true, say: 'the stove ticks. the kettle on it is nearly boiling' },
        { kind: 'television', group: 'flavour', pattern: /^home-tv/, footprint: true, say: 'the weather: snow in the north, and more tomorrow' },
        { kind: 'bookshelf', group: 'flavour', pattern: /^home-bookshelf/, footprint: true, say: 'paperbacks, a road atlas, and manga read to pieces' },
        // the home city (issue #218)
        { kind: 'clocks', group: 'flavour', pattern: /^sfb-clocks-station/, footprint: true, say: 'everybody meets under the clocks. nobody has ever caught a train here' },
        { kind: 'sea-lions', group: 'flavour', pattern: /^sfb-sea-lions/, footprint: true, say: 'the sea lions bark at you. one of them is eating somebody\'s chips' },
    ],

    match(key, roomConfig, venues) {
        const interior = !!roomConfig.interior;
        const konbini = interior && roomConfig.shopEnabled !== false;
        const venue = interior && venues && venues[roomConfig.shopMenu] ? roomConfig.shopMenu : null;
        for (const rule of Interactions.RULES) {
            if (rule.room === 'konbini' && !konbini) continue;
            if (rule.room === 'venue' && !venue) continue;
            if (!rule.pattern.test(key)) continue;
            const hit = { kind: rule.room === 'venue' ? venue : rule.kind, group: rule.group, footprint: !!rule.footprint };
            if (rule.say) hit.say = rule.say;
            return hit;
        }
        return null;
    },

    all(room, roomConfig, opts) {
        const { sizeOf, venues, group } = opts || {};
        const found = [];
        const dg = roomConfig.drinkingGame;
        if (dg && (!group || group === 'drinking-game')) {
            for (const [x, y] of (dg.triggerCells || [])) {
                found.push({ kind: 'drinking-game', group: 'drinking-game', x, y, w: 1, h: 1 });
            }
        }
        // a room uses a few hundred sprite keys for its thousands of tiles:
        // each key is matched against the rules once
        const hits = new Map();
        for (const layer of (room.layers || [])) {
            for (const xy in (layer.tiles || {})) {
                const key = layer.tiles[xy];
                let hit = hits.get(key);
                if (hit === undefined) hits.set(key, hit = Interactions.match(key, roomConfig, venues));
                if (!hit || (group && hit.group !== group)) continue;
                const [x, y] = xy.split(',').map(Number);
                const [w, h] = hit.footprint && sizeOf ? sizeOf(key) : [1, 1];
                const one = { kind: hit.kind, group: hit.group, key, x, y, w, h };
                if (hit.say) one.say = hit.say;
                found.push(one);
            }
        }
        return found;
    },

    find(room, roomConfig, gridX, gridY, opts) {
        return Interactions.all(room, roomConfig, opts).find(i =>
            gridX >= i.x && gridX < i.x + i.w && gridY >= i.y && gridY < i.y + i.h) || null;
    },

    /**
     * Every interactive cell of a room: Map "x,y" -> the interactions covering
     * that cell (footprints expanded), in all() order. Built once per room
     * load (RoomManager.interactionAt) so a bump is one lookup, not a scan of
     * every tile in the room (issue #145).
     */
    index(room, roomConfig, opts) {
        const cells = new Map();
        for (const i of Interactions.all(room, roomConfig, opts)) {
            for (let y = i.y; y < i.y + i.h; y++) {
                for (let x = i.x; x < i.x + i.w; x++) {
                    const list = cells.get(x + ',' + y);
                    if (list) list.push(i); else cells.set(x + ',' + y, [i]);
                }
            }
        }
        return cells;
    },

    /** find() against an index(): the first interaction on the cell (of `group`, when given), or null. */
    lookup(index, gridX, gridY, group) {
        const list = index.get(gridX + ',' + gridY);
        if (!list) return null;
        return (group ? list.find(i => i.group === group) : list[0]) || null;
    },
};

if (typeof window !== 'undefined') window.Interactions = Interactions;
