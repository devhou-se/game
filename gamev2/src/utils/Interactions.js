const Interactions = {
    RULES: [
        { kind: 'vending', group: 'shop', pattern: /vending-machine/, footprint: true },
        { kind: 'counter', group: 'shop', pattern: /^(blue-shrine-platform-base|office-counter)/, footprint: true, room: 'konbini' },
        { kind: 'drinks', group: 'shop', pattern: /^office-(shelf-drinks|shelf-glass|fridge|freezer)/, footprint: true, room: 'konbini' },
        { kind: 'snacks', group: 'shop', pattern: /^office-shelf-snacks/, footprint: true, room: 'konbini' },
        { kind: 'venue', group: 'shop', pattern: /^office-counter2/, footprint: true, room: 'venue' },
        { kind: 'pond', group: 'pond', pattern: /^pond-autotile/ },
        { kind: 'clock', group: 'clock', pattern: /^(office-clock|office-poster-menu)/ },
    ],

    match(key, roomConfig, venues) {
        const interior = !!roomConfig.interior;
        const konbini = interior && roomConfig.shopEnabled !== false;
        const venue = interior && venues && venues[roomConfig.shopMenu] ? roomConfig.shopMenu : null;
        for (const rule of Interactions.RULES) {
            if (rule.room === 'konbini' && !konbini) continue;
            if (rule.room === 'venue' && !venue) continue;
            if (!rule.pattern.test(key)) continue;
            return { kind: rule.room === 'venue' ? venue : rule.kind, group: rule.group, footprint: !!rule.footprint };
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
        for (const layer of (room.layers || [])) {
            for (const xy in (layer.tiles || {})) {
                const key = layer.tiles[xy];
                const hit = Interactions.match(key, roomConfig, venues);
                if (!hit || (group && hit.group !== group)) continue;
                const [x, y] = xy.split(',').map(Number);
                const [w, h] = hit.footprint && sizeOf ? sizeOf(key) : [1, 1];
                found.push({ kind: hit.kind, group: hit.group, key, x, y, w, h });
            }
        }
        return found;
    },

    find(room, roomConfig, gridX, gridY, opts) {
        return Interactions.all(room, roomConfig, opts).find(i =>
            gridX >= i.x && gridX < i.x + i.w && gridY >= i.y && gridY < i.y + i.h) || null;
    },
};

if (typeof window !== 'undefined') window.Interactions = Interactions;
