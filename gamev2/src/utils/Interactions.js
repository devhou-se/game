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
        // Odori Park's hot-drinks tent (issue #219): a stall that sells over its counter, as a machine does
        { kind: 'stall', group: 'shop', pattern: /^snowfest-stall-drinks/, footprint: true },
        // an underground arcade (tools/generate_chikagai.py): three of its shopfronts sell over the counter
        { kind: 'bakery', group: 'shop', pattern: /^chika-shop-bakery/, footprint: true },
        { kind: 'kissa', group: 'shop', pattern: /^chika-shop-kissa/, footprint: true },
        { kind: 'standbar', group: 'shop', pattern: /^chika-shop-bar/, footprint: true },
        { kind: 'drinks', group: 'shop', pattern: /^office-(shelf-drinks|shelf-glass|fridge|freezer)/, footprint: true, room: 'konbini' },
        { kind: 'snacks', group: 'shop', pattern: /^office-shelf-snacks/, footprint: true, room: 'konbini' },
        { kind: 'venue', group: 'shop', pattern: /^office-counter2/, footprint: true, room: 'venue' },
        { kind: 'water', group: 'water', pattern: /^office-watercooler/, footprint: true, room: 'konbini' },
        // inside a shrine's worship hall (tools/generate_shrines.py; src/ShrineVisit.js)
        { kind: 'offering', group: 'shrine', pattern: /^shrine-in-saisen/, footprint: true },
        { kind: 'omikuji', group: 'shrine', pattern: /^shrine-in-omikuji_/, footprint: true },
        // inside the palace's audience hall (tools/generate_palace.py; src/PalaceVisit.js)
        { kind: 'audience', group: 'palace', pattern: /^palace-in-dais/, footprint: true },
        { kind: 'guestbook', group: 'palace', pattern: /^palace-in-guestbook/, footprint: true },
        // inside a temple's main hall (tools/generate_temple.py; src/TempleVisit.js)
        { kind: 'incense', group: 'temple', pattern: /^temple-in-jokoro/, footprint: true },
        { kind: 'offering', group: 'temple', pattern: /^temple-in-saisen/, footprint: true },
        { kind: 'drawers', group: 'temple', pattern: /^temple-in-omikuji/, footprint: true },
        { kind: 'pond', group: 'pond', pattern: /^pond-autotile/ },
        { kind: 'clock', group: 'clock', pattern: /^(office-clock|office-poster-menu)/ },
        // a home's furniture (issue #208, tools/generate_houses.py): a bump says one line
        // (`say`, shown as a toast by GameScene) and nothing else happens
        { kind: 'kotatsu', group: 'flavour', pattern: /^home-kotatsu/, footprint: true, say: 'the kotatsu is warm. you could stay under it all winter' },
        { kind: 'hearth', group: 'flavour', pattern: /^home-irori/, footprint: true, say: 'the kettle over the hearth is just starting to sing' },
        { kind: 'stove', group: 'flavour', pattern: /^home-stove/, footprint: true, say: 'the stove ticks. the kettle on it is nearly boiling' },
        { kind: 'television', group: 'flavour', pattern: /^home-tv/, footprint: true, say: 'the weather: snow in the north, and more tomorrow' },
        { kind: 'bookshelf', group: 'flavour', pattern: /^home-bookshelf/, footprint: true, say: 'paperbacks, a road atlas, and manga read to pieces' },
        // a tower's lobby (issue #216, the same generator): the directory board and the lifts
        { kind: 'directory', group: 'flavour', pattern: /^lobby-directory/, footprint: true, say: 'every floor has a name on it. none of them is expecting you' },
        { kind: 'lift', group: 'flavour', pattern: /^lobby-lift/, footprint: true, say: 'the lift wants a pass. the lobby is as far as you go' },
        // the palace's audience hall (issue #215): the armour, the swords, the guard's post
        { kind: 'armour', group: 'flavour', pattern: /^palace-in-armour/, footprint: true, say: 'the armour has not been worn in two hundred years. it still looks ready before you do' },
        { kind: 'swords', group: 'flavour', pattern: /^palace-in-swords/, footprint: true, say: 'three swords on a rack, peace-knotted. the sign you cannot read says do not touch' },
        { kind: 'guard-post', group: 'flavour', pattern: /^palace-in-guardpost/, footprint: true, say: 'the guard has stepped out. his man-catcher has not' },
        // a temple's main hall (issue #213): the charm counter, the sanctum, the drum, the bowl bell, the candles, the tied fortunes
        { kind: 'charms', group: 'flavour', pattern: /^temple-in-wall-charms/, footprint: true, say: 'charms for safe travel, for exams, for a good match. nobody is at the counter to sell you one' },
        { kind: 'sanctum', group: 'flavour', pattern: /^temple-in-naijin/, footprint: true, say: 'the Kannon behind the curtain has been shown to nobody for thirteen hundred years. not to you either' },
        { kind: 'temple-drum', group: 'flavour', pattern: /^temple-in-drum/, footprint: true, say: 'the drum is taller than you are. the sticks are right there. you leave them right there' },
        { kind: 'bowl-bell', group: 'flavour', pattern: /^temple-in-keisu/, footprint: true, say: 'you flick the rim of the great bowl with a fingernail. it hums for a very long time' },
        { kind: 'votive-candles', group: 'flavour', pattern: /^temple-in-candles/, footprint: true, say: 'a rack of small candles, each one somebody\'s wish. the wax is still warm' },
        { kind: 'tied-fortunes', group: 'flavour', pattern: /^temple-in-musubi/, footprint: true, say: 'bad fortunes are tied here and left behind. there are a great many of them' },
        // the home city (issue #218)
        { kind: 'clocks', group: 'flavour', pattern: /^sfb-clocks-station/, footprint: true, say: 'everybody meets under the clocks. nobody has ever caught a train here' },
        { kind: 'sea-lions', group: 'flavour', pattern: /^sfb-sea-lions/, footprint: true, say: 'the sea lions bark at you. one of them is eating somebody\'s chips' },
        // Odori Park in the snow festival (issue #219): the corn tent, the sculptures, the frozen fountain
        { kind: 'corn', group: 'flavour', pattern: /^snowfest-stall-corn/, footprint: true, say: 'grilled corn, butter and soy sauce. the queue starts somewhere behind you' },
        { kind: 'snow-castle', group: 'flavour', pattern: /^snow-sculpture-castle/, footprint: true, say: 'a castle keep carved out of packed snow. the board says please do not climb it' },
        { kind: 'snow-tanuki', group: 'flavour', pattern: /^snow-sculpture-tanuki/, footprint: true, say: 'a snow tanuki in a straw hat. his sake flask has frozen solid' },
        { kind: 'snow-bear', group: 'flavour', pattern: /^snow-sculpture-bear/, footprint: true, say: 'a snow bear with a salmon. he will not finish it before april' },
        { kind: 'fountain', group: 'flavour', pattern: /^odori-fountain/, footprint: true, say: 'the fountain is off for the winter. the lights under the ice are not' },
        // ...and the people folded double at the waist on its pavements: one line each
        // an underground arcade's other fronts and furniture
        { kind: 'bookshop', group: 'flavour', pattern: /^chika-shop-books/, footprint: true, say: 'this week\'s manga, tied shut with string. everyone is reading them standing up anyway' },
        { kind: 'florist', group: 'flavour', pattern: /^chika-shop-flowers/, footprint: true, say: 'tulips in february. down here it is always spring' },
        { kind: 'shutter', group: 'flavour', pattern: /^chika-shop-shutter/, footprint: true, say: 'the shutter is down. the notice says tenant wanted' },
        { kind: 'gacha', group: 'flavour', pattern: /^chika-gacha/, footprint: true, say: 'capsule toys, three hundred yen a turn. the one you want is always at the bottom' },
        { kind: 'floor-map', group: 'flavour', pattern: /^chika-map/, footprint: true, say: 'you are here. so, apparently, is everything else' },
        { kind: 'leaner', group: 'flavour', pattern: /^sfb-lean-a/, footprint: true, say: 'he has been like this since tuesday' },
        { kind: 'leaner', group: 'flavour', pattern: /^sfb-lean-b/, footprint: true, say: 'still standing. technically' },
        { kind: 'leaner', group: 'flavour', pattern: /^sfb-lean-c/, footprint: true, say: 'three trams have come and gone. he was not waiting for one' },
        { kind: 'leaner', group: 'flavour', pattern: /^sfb-lean-d/, footprint: true, say: 'his slurpee melted hours ago. he has not spilled a drop' },
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
