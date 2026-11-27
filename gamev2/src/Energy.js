/**
 * Energy and the konbini stamp card (issue #209) — the rules only, as pure
 * static functions. The state (energy, stamps, hints) lives in the Shop's
 * save blob and the Shop draws the meter; nothing here touches Phaser.
 *
 * ENERGY is a 0..MAX meter. Every cell walked costs STEP (a sprint covers
 * twice the cells, so it drains twice as fast by the clock); eating and
 * drinking puts it back (`valueOf`). It never blocks anything but the sprint:
 *   0             peckish — SHIFT does nothing until you eat or drink
 *   1..WELL_FED   normal — sprint is the usual x2
 *   >= WELL_FED   well fed — sprint is x WELL_FED_SPRINT
 * Walking speed is the same at every level.
 *
 * The STAMP CARD has one stamp per place bought from: a store (a konbini or
 * a discount store, by room key) or the vending machines of an area
 * (`vending:<room>`). Stamps only add up, so a milestone's reward is paid
 * the moment the count reaches it and needs no "claimed" record.
 *
 * A stamp is never taken back, even when its place leaves the world (issue
 * #68 deleted Machi's 7-Eleven and the made-up towns' machines): it was
 * bought and its reward was paid, and dropping it would pay the same
 * milestone twice on the way back up. Such a stamp still counts on the card,
 * which says how many are from places that have closed (`Stamps.closed`);
 * Konbini Pilgrim only ever asks for the stores that exist.
 */
const Energy = {
    MAX: 100,
    /** Cells of walking a full meter lasts: 1800 cells = 6 min at 5 cells/s (3 min of pure sprint). */
    CELLS: 1800,
    /** At or under this the meter is "low" (red, and the one-time hint). */
    LOW: 25,
    /** At or over this you are well fed. */
    WELL_FED: 70,
    /** Sprint multipliers: the usual one, and the well-fed one. */
    SPRINT: 2,
    WELL_FED_SPRINT: 2.25,
    /** Segments in the HUD meter. */
    SEGMENTS: 5,
    /** The free cup from a konbini's water cooler: this much, and never past WATER_CAP. */
    WATER: 20,
    WATER_CAP: 40,
    /** What an item restores when it says nothing itself (a config catalogue), by category. */
    DEFAULTS: { food: 40, fish: 50, drink: 15 },
    /** Debug "fast hunger": the drain is multiplied by this. */
    DEBUG_FACTOR: 30,

    /** Any saved value as a valid level; anything missing or junk is a full meter (old saves, new players). */
    clamp(v) {
        return typeof v === 'number' && isFinite(v) ? Math.max(0, Math.min(Energy.MAX, v)) : Energy.MAX;
    },

    /** What one cell of walking costs (`factor`: the debug multiplier). */
    stepCost(factor) { return Energy.MAX / Energy.CELLS * (factor || 1); },

    /** The level after walking one cell. */
    afterStep(energy, factor) { return Math.max(0, energy - Energy.stepCost(factor)); },

    /** 'peckish' | 'low' | 'ok' | 'fed' */
    level(energy) {
        if (energy <= 0) return 'peckish';
        if (energy <= Energy.LOW) return 'low';
        return energy >= Energy.WELL_FED ? 'fed' : 'ok';
    },

    /** What holding sprint multiplies the step speed by: 1 when peckish. */
    sprintMultiplier(energy) {
        if (energy <= 0) return 1;
        return energy >= Energy.WELL_FED ? Energy.WELL_FED_SPRINT : Energy.SPRINT;
    },

    /** What eating or drinking one of an item restores (gear restores nothing). */
    valueOf(item) {
        if (!item || item.permanent) return 0;
        if (typeof item.energy === 'number') return Math.max(0, item.energy);
        const cat = item.category || (item.effect ? 'drink' : 'food');
        return Energy.DEFAULTS[cat] || 0;
    },

    /** The level after eating or drinking `item`. */
    afterEating(energy, item) { return Math.min(Energy.MAX, energy + Energy.valueOf(item)); },

    /** The level after a free cup of water: it takes the edge off, it never makes you well fed. */
    afterWater(energy) {
        return energy >= Energy.WATER_CAP ? energy : Math.min(Energy.WATER_CAP, energy + Energy.WATER);
    },

    /** How many of the meter's segments are lit: any energy at all lights one. */
    segments(energy) {
        return energy <= 0 ? 0 : Math.max(1, Math.round(energy / Energy.MAX * Energy.SEGMENTS));
    },

    /** The meter's colour at a level. */
    color(energy) {
        return { peckish: 0x666666, low: 0xff5544, ok: 0xffcc66, fed: 0x66ff88 }[Energy.level(energy)];
    },

    /**
     * What to say when a step takes the meter from `before` to `after`, or
     * null: the one-time hint the first time it runs low (`hinted` says it
     * has been said), and a line every time it runs out.
     */
    notice(before, after, hinted) {
        if (before > 0 && after <= 0) return { kind: 'peckish', text: Energy.PECKISH };
        if (!hinted && before > Energy.LOW && after <= Energy.LOW) return { kind: 'low', text: Energy.HINT };
        return null;
    },

    /**
     * Sprint held on an empty meter: is it time to say the peckish line again?
     * (`last`: when it was last said this way, ms; at most once per REMIND_MS.)
     */
    remind(energy, now, last) {
        return energy <= 0 && (last == null || now - last >= Energy.REMIND_MS);
    },
    REMIND_MS: 10000,

    HINT: 'getting peckish: food and drink from a konbini or a vending machine fills the meter',
    PECKISH: 'peckish: no sprint until you eat or drink something',
};

const Stamps = {
    /**
     * The card's rewards, by stamp count: yen back, or a free item.
     * (2 is two shops, the first evening; 12 is most of the stores there are.)
     */
    MILESTONES: [
        { at: 2, yen: 200 },
        { at: 5, item: 'onigiri' },
        { at: 8, yen: 500 },
        { at: 12, yen: 1000, item: 'nikuman' },
    ],
    ACHIEVEMENT: 'Konbini Pilgrim',

    /** Is this room a store with a till (a konbini or a discount store)? Same test as Interactions' konbini. */
    isStore(roomConfig) { return !!roomConfig && !!roomConfig.interior && roomConfig.shopEnabled !== false; },

    /** Every store in the world, from config: [{ id: room key, name }], in config order. */
    stores(config) {
        const rooms = (config && config.rooms) || {};
        return Object.keys(rooms).filter(k => Stamps.isStore(rooms[k])).map(k => ({ id: k, name: rooms[k].name || k }));
    },

    /**
     * The stamp a purchase earns: the store's room key inside a store, the
     * area's vending machines for a machine on the street (`room` is the
     * district underfoot in a stitched city), nothing anywhere else (the
     * izakaya bar).
     */
    placeFor(kind, room, roomConfig) {
        if (Stamps.isStore(roomConfig)) return room;
        return kind === 'vending' && room ? 'vending:' + room : null;
    },

    /** A saved stamps object as a clean { id: 1 } map. */
    clean(saved) {
        const out = {};
        if (saved && typeof saved === 'object') for (const id in saved) if (saved[id]) out[id] = 1;
        return out;
    },

    count(stamps) { return Object.keys(stamps || {}).length; },

    /**
     * The stamps whose place is no longer in the world: a store that is not a
     * store room of this config, the machines of a room that is gone.
     */
    closed(config, stamps) {
        const rooms = (config && config.rooms) || {};
        return Object.keys(stamps || {}).filter(id =>
            (id.startsWith('vending:') ? !rooms[id.slice(8)] : !Stamps.isStore(rooms[id])));
    },

    /** The milestones reached by going from `before` stamps to `after`. */
    rewards(before, after) { return Stamps.MILESTONES.filter(m => m.at > before && m.at <= after); },

    /** The next milestone after `count` stamps, or null when the card is done. */
    next(count) { return Stamps.MILESTONES.find(m => m.at > count) || null; },

    /** "¥200 back" / "a free Onigiri" — `nameOf(id)` names an item, `fmt(n)` writes yen. */
    describe(m, nameOf, fmt) {
        const parts = [];
        if (m.yen) parts.push(`${fmt(m.yen)} back`);
        if (m.item) parts.push(`a free ${nameOf(m.item)}`);
        return parts.join(' and ');
    },

    /** The achievement: a stamp from every store that exists. */
    progress(config, stamps) {
        const all = Stamps.stores(config), have = all.filter(s => (stamps || {})[s.id]).length;
        return { name: Stamps.ACHIEVEMENT, desc: 'Buy something at every konbini and discount store',
                 value: have, total: all.length, complete: all.length > 0 && have >= all.length };
    },
};

if (typeof window !== 'undefined') { window.Energy = Energy; window.Stamps = Stamps; }
