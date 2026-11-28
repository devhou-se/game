const Interactions = {
    RULES: [
        { kind: 'vending', group: 'shop', pattern: /vending-machine/, footprint: true },
        { kind: 'counter', group: 'shop', pattern: /^(blue-shrine-platform-base|office-counter|konbini-counter)/, footprint: true, room: 'konbini' },
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
        // the pub in Sendai (tools/generate_pub.py, issue #217): the bar is the till
        { kind: 'taproom', group: 'shop', pattern: /^pub-in-bar/, footprint: true },
        // the distillery's tasting bar in Sendai (tools/generate_distillery.py, issue #217): the counter is the till
        { kind: 'tasting', group: 'shop', pattern: /^distillery-in-counter/, footprint: true },
        // Susukino's ramen alley (issue #219, stage 4): a counter under a noren, eaten at as a yatai is
        { kind: 'ramen', group: 'shop', pattern: /^susukino-ramen-stall/, footprint: true },
        { kind: 'drinks', group: 'shop', pattern: /^(office-(shelf-drinks|shelf-glass|fridge|freezer)|konbini-coffee)/, footprint: true, room: 'konbini' },
        { kind: 'snacks', group: 'shop', pattern: /^(office-shelf-snacks|konbini-(chiller|gondola-(snacks|noodles|bread)))/, footprint: true, room: 'konbini' },
        { kind: 'venue', group: 'shop', pattern: /^office-counter2/, footprint: true, room: 'venue' },
        { kind: 'water', group: 'water', pattern: /^(office-watercooler|konbini-water)/, footprint: true, room: 'konbini' },
        // inside a shrine's worship hall (tools/generate_shrines.py; src/ShrineVisit.js)
        { kind: 'offering', group: 'shrine', pattern: /^shrine-in-saisen/, footprint: true },
        { kind: 'omikuji', group: 'shrine', pattern: /^shrine-in-omikuji_/, footprint: true },
        // inside the palace's audience hall (tools/generate_palace.py; src/PalaceVisit.js)
        { kind: 'audience', group: 'palace', pattern: /^palace-in-dais/, footprint: true },
        { kind: 'guestbook', group: 'palace', pattern: /^palace-in-guestbook/, footprint: true },
        // inside a temple's main hall (tools/generate_temple.py; src/TempleVisit.js)
        { kind: 'incense', group: 'temple', pattern: /^temple-in-jokoro/, footprint: true },
        // (a pagoda's ground floor has the same box: tools/generate_pagodas.py, issue #214)
        { kind: 'offering', group: 'temple', pattern: /^(temple|pagoda)-in-saisen/, footprint: true },
        { kind: 'drawers', group: 'temple', pattern: /^temple-in-omikuji/, footprint: true },
        { kind: 'pond', group: 'pond', pattern: /^pond-autotile/ },
        { kind: 'clock', group: 'clock', pattern: /^(office-clock|office-poster-menu)/ },
        // a 7-Eleven's clock is part of its back wall (tools/generate_konbinis.py, issue #221): the
        // sprite sits on the wall's upper cell and the bump lands on the lower one
        { kind: 'clock', group: 'clock', pattern: /^konbini-wall-clock/, footprint: true },
        // a home's furniture (issue #208, tools/generate_houses.py): a bump says one line
        // (`say`, shown as a toast by GameScene) and nothing else happens
        { kind: 'kotatsu', group: 'flavour', pattern: /^home-kotatsu/, footprint: true, say: 'the kotatsu is warm. you could stay under it all winter' },
        { kind: 'hearth', group: 'flavour', pattern: /^home-irori/, footprint: true, say: 'the kettle over the hearth is just starting to sing' },
        { kind: 'stove', group: 'flavour', pattern: /^home-stove/, footprint: true, say: 'the stove ticks. the kettle on it is nearly boiling' },
        { kind: 'television', group: 'flavour', pattern: /^home-tv/, footprint: true, say: 'the weather: snow in the north, and more tomorrow' },
        { kind: 'bookshelf', group: 'flavour', pattern: /^home-bookshelf/, footprint: true, say: 'paperbacks, a road atlas, and manga read to pieces' },
        // a tower's lobby (issue #216, the same generator): the directory board says a line...
        { kind: 'directory', group: 'flavour', pattern: /^lobby-directory/, footprint: true, say: 'engineering is hiring, the directory says. ask at the desk' },
        // ...and the reception desk and the lifts are the job (issue #226; src/Career.js): the desk
        // signs you on, a lift takes you up to a shift
        { kind: 'desk', group: 'career', pattern: /^lobby-desk/, footprint: true },
        { kind: 'lift', group: 'career', pattern: /^lobby-lift/, footprint: true },
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
        // the pub in Sendai (issue #217): the baseball on the big screen (post 505's own words), the darts, the specials
        { kind: 'baseball', group: 'flavour', pattern: /^pub-in-wall-tv/, footprint: true, say: 'the baseball is on. a man in a gold chain claps for the Eagles and the bar claps with him' },
        { kind: 'darts', group: 'flavour', pattern: /^pub-in-wall-darts/, footprint: true, say: 'three darts in the wall, none in the board. nobody is owning up' },
        { kind: 'specials', group: 'flavour', pattern: /^pub-in-chalkboard/, footprint: true, say: 'today\'s special is fish and chips. it has been today\'s special for some years' },
        // the distillery in Sendai (issue #217): the one pot still, and the casks on the wall and on the floor
        { kind: 'pot-still', group: 'flavour', pattern: /^distillery-in-still/, footprint: true, say: 'a copper pot still, warm to the hand. whatever is in it will be ready in about twelve years' },
        { kind: 'casks', group: 'flavour', pattern: /^distillery-in-(wall-casks|cask)/, footprint: true, say: 'the casks are asleep. the chalk on the nearest one says not before 2037' },
        // Canal City's atrium in Fukuoka (issue #217): the fountain in the canal, and the five shopfronts. Nothing is sold
        { kind: 'mall-fountain', group: 'flavour', pattern: /^mall-in-fountain/, footprint: true, say: 'the jets rest between shows. the next water performance starts just after you leave' },
        { kind: 'mall-fashion', group: 'flavour', pattern: /^mall-in-front-fashion/, footprint: true, say: 'winter coats in the window, in sizes for somebody smaller' },
        { kind: 'mall-toys', group: 'flavour', pattern: /^mall-in-front-toys/, footprint: true, say: 'a wall of capsule toys and plushies. the big one is not for sale' },
        { kind: 'mall-okonomiyaki', group: 'flavour', pattern: /^mall-in-front-okonomiyaki/, footprint: true, say: 'okonomiyaki, made in front of you. the queue says it is good. opinions differ' },
        { kind: 'mall-cafe', group: 'flavour', pattern: /^mall-in-front-cafe/, footprint: true, say: 'the cafe has a queue for the queue' },
        { kind: 'mall-ramen', group: 'flavour', pattern: /^mall-in-front-ramen/, footprint: true, say: 'the ramen stadium is five floors up. the escalator is part of the wall' },
        // the station with the clocks in San Franbourne (issue #246, tools/generate_flinders.py): the clocks on the
        // gate line are a clock (Time Travel), the departures board and the ticket machines say a line
        { kind: 'clock', group: 'clock', pattern: /^flinders-in-clocks/, footprint: true },
        { kind: 'replacement-buses', group: 'flavour', pattern: /^flinders-in-board/, footprint: true, say: 'every line on the board says the same thing: buses replace trains' },
        { kind: 'ticket-machine', group: 'flavour', pattern: /^flinders-in-tickets/, footprint: true, say: 'the machine wants a card you do not have. the card is sold by the machine' },
        // Fukuoka Tower's observation deck (issue #242): the glass, the coin binoculars, the brass map, the padlocks, the sign by the lift
        { kind: 'deck-window', group: 'flavour', pattern: /^deck-in-window/, footprint: true, say: 'the bay, 123 metres down. the glass is very clean and you are very careful not to lean on it' },
        { kind: 'binoculars', group: 'flavour', pattern: /^deck-in-binoculars/, footprint: true, say: 'a hundred yen for two minutes. somebody else\'s two minutes are still running: a ferry, very large' },
        { kind: 'compass', group: 'flavour', pattern: /^deck-in-compass/, footprint: true, say: 'a brass map of the bay with an arrow for north. you are the dot in the middle' },
        { kind: 'padlocks', group: 'flavour', pattern: /^deck-in-locks/, footprint: true, say: 'padlocks in the shape of a heart, each with two names on it. nobody has come back for a key' },
        { kind: 'lift-sign', group: 'flavour', pattern: /^deck-in-lift-sign/, footprint: true, say: 'you are 123 metres up a tower of 234. the other 111 are aerial' },
        // the gondola at the foot of Osaka's ferris wheel (issue #242): one turn of the wheel and the view (src/ViewRide.js)
        { kind: 'wheel', group: 'ride', pattern: /^wheel-boarding/, footprint: true },
        // inside a pagoda (issue #214): the heart pillar, the Buddhas at its foot, the sutra chests, the thousand Buddhas, the window
        { kind: 'heart-pillar', group: 'flavour', pattern: /^pagoda-in-pillar/, footprint: true, say: 'the heart pillar runs from the ground to the spire and touches no floor. it sways in quakes' },
        { kind: 'four-buddhas', group: 'flavour', pattern: /^pagoda-in-shumidan/, footprint: true, say: 'four small Buddhas sit round the foot of the pillar, one facing each wind' },
        { kind: 'sutra-chests', group: 'flavour', pattern: /^pagoda-in-kyozo/, footprint: true, say: 'chests of sutras tied with cord, labelled in a hand nobody writes any more' },
        { kind: 'thousand-buddhas', group: 'flavour', pattern: /^pagoda-in-senbutsu/, footprint: true, say: 'a wall of tiny gilt Buddhas, a thousand of them. you count eleven and give up' },
        { kind: 'pagoda-window', group: 'flavour', pattern: /^pagoda-in-window/, footprint: true, say: 'through the slats: tiled roofs, then more roofs. the wind is louder up here' },
        // the home city (issue #218)
        { kind: 'clocks', group: 'flavour', pattern: /^sfb-clocks-station/, footprint: true, say: 'everybody meets under the clocks. nobody has ever caught a train here' },
        { kind: 'sea-lions', group: 'flavour', pattern: /^sfb-sea-lions/, footprint: true, say: 'the sea lions bark at you. one of them is eating somebody\'s chips' },
        // the fingerpost inside Karuizawa's gate, out of Tokyo's west gate (issue #260)
        { kind: 'fingerpost', group: 'flavour', pattern: /^karuizawa-fingerpost/, footprint: true, say: 'east, through the gate: Tokyo. west, up the road through the larches: Karuizawa' },
        // ...and at the head of its road (issue #262): Shiraito Falls (its rock arms, either side of the pool, which fishes) and the corn stall
        { kind: 'waterfall', group: 'flavour', pattern: /^karuizawa-falls/, footprint: true, say: 'hundreds of white threads slip out of the rock itself. no river above: the mountain just leaks' },
        { kind: 'corn-stall', group: 'flavour', pattern: /^karuizawa-corn-stall/, footprint: true, say: 'corn off the charcoal, brushed with soy sauce. next bus in forty minutes, which is about right' },
        // Odori Park in the snow festival (issue #219): the corn tent, the sculptures, the frozen fountain
        { kind: 'corn', group: 'flavour', pattern: /^snowfest-stall-corn/, footprint: true, say: 'grilled corn, butter and soy sauce. the queue starts somewhere behind you' },
        { kind: 'snow-castle', group: 'flavour', pattern: /^snow-sculpture-castle/, footprint: true, say: 'a castle keep carved out of packed snow. the board says please do not climb it' },
        { kind: 'snow-tanuki', group: 'flavour', pattern: /^snow-sculpture-tanuki/, footprint: true, say: 'a snow tanuki in a straw hat. his sake flask has frozen solid' },
        { kind: 'snow-bear', group: 'flavour', pattern: /^snow-sculpture-bear/, footprint: true, say: 'a snow bear with a salmon. he will not finish it before april' },
        { kind: 'fountain', group: 'flavour', pattern: /^odori-fountain/, footprint: true, say: 'the fountain is off for the winter. the lights under the ice are not' },
        // Kansai (issue #255): the fingerposts either side of the seam where Osaka's avenue walks on to Himeji
        { kind: 'fingerpost', group: 'flavour', pattern: /^kansai-fingerpost/, footprint: true, say: 'west: himeji castle and koko-en. east: osaka, dotonbori' },
        // ...the ones either side of the seam where it walks on from Himeji to Okayama (issue #267), and what stands in Okayama
        { kind: 'fingerpost', group: 'flavour', pattern: /^okayama-fingerpost/, footprint: true, say: 'west: okayama, the black castle and korakuen. east: himeji castle, then osaka' },
        { kind: 'momotaro', group: 'flavour', pattern: /^okayama-momotaro/, footprint: true, say: 'momotaro the peach boy, with his dog, monkey and pheasant. the ogres never stood a chance' },
        { kind: 'bizen-stall', group: 'flavour', pattern: /^okayama-bizen-stall/, footprint: true, say: 'bizen ware: no glaze, two weeks in the kiln, no two alike. beer tastes better from it, they say' },
        { kind: 'crane', group: 'flavour', pattern: /^okayama-crane/, footprint: true, say: 'a red-crowned crane. it looks at you, then at the pond, and chooses the pond' },
        // ...the ones either side of the seam where Osaka's avenue walks on to Nara (issue #268), and what stands in Nara
        { kind: 'fingerpost', group: 'flavour', pattern: /^nara-fingerpost/, footprint: true, say: 'west: osaka, dotonbori. east: nara, the great buddha and the deer' },
        { kind: 'deer', group: 'flavour', pattern: /^nara-deer-(doe|stag)/, footprint: true, say: 'a deer, resting. it has seen ten thousand visitors today and you are not the interesting one' },
        { kind: 'deer-bow', group: 'flavour', pattern: /^nara-deer-bow/, footprint: true, say: 'the deer bows. it wants a cracker. it bows again, lower, and stands on your foot' },
        { kind: 'senbei-stall', group: 'flavour', pattern: /^nara-senbei-stall/, footprint: true, say: 'deer crackers, 200 yen a stack. every deer in the park knows the sound of the paper band' },
        { kind: 'stone-lantern', group: 'flavour', pattern: /^nara-stone-lantern/, footprint: true, say: 'a stone lantern, furred with moss. there are two thousand along this path, each one given by somebody' },
        { kind: 'nandaimon', group: 'flavour', pattern: /^nara-nandaimon/, footprint: true, say: 'the great south gate. two wooden guardians, eight metres tall, glare out of the dark either side' },
        { kind: 'great-buddha-hall', group: 'flavour', pattern: /^nara-daibutsuden/, footprint: true, say: 'the great buddha hall. fifteen metres of bronze sit inside, and a pillar with a hole the size of his nostril' },
        { kind: 'torii', group: 'flavour', pattern: /^nara-kasuga-torii/, footprint: true, say: 'the vermilion gate of kasuga taisha. the deer walk through without bowing' },
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
        // a 7-Eleven's fixtures that sell nothing (issue #221)
        { kind: 'atm', group: 'flavour', pattern: /^konbini-atm/, footprint: true, say: 'the cash machine speaks four languages. your card speaks none of them' },
        { kind: 'copier', group: 'flavour', pattern: /^konbini-copier/, footprint: true, say: 'the copier also sells concert tickets. none for tonight' },
        { kind: 'magazines', group: 'flavour', pattern: /^konbini-magazines/, footprint: true, say: 'this week\'s manga, thick as a brick and taped shut' },
        { kind: 'ice-cream', group: 'flavour', pattern: /^konbini-freezer/, footprint: true, say: 'ice cream, whatever the season. the lid is cold enough to stick to' },
        { kind: 'sundries', group: 'flavour', pattern: /^konbini-gondola-daily/, footprint: true, say: 'umbrellas, socks, phone chargers. everything you forgot to pack' },
        // the Devhouses (issue #69). Not the tables or the chairs: you walk round them all day
        { kind: 'locked-door', group: 'flavour', pattern: /^devhouse-door/, footprint: true, say: 'locked. whoever lives behind it is not one of us' },
        { kind: 'bath', group: 'flavour', pattern: /^devhouse-bath/, footprint: true, say: 'the bath is full and hot. somebody has called it for after dinner' },
        { kind: 'washer', group: 'flavour', pattern: /^devhouse-washer/, footprint: true, say: 'forty minutes left on the wash. it has said so for an hour' },
        { kind: 'goldfish', group: 'flavour', pattern: /^devhouse-water-bowl/, footprint: true, say: 'two goldfish in a stone bowl. they have seen every stand-up this trip and have no notes' },
        { kind: 'bunk', group: 'flavour', pattern: /^devhouse-bunk/, footprint: true, say: 'the top bunk was claimed on day one. the bottom one was what was left' },
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
