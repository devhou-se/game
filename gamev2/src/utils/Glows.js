/**
 * Glows - what a placed sprite lights at night besides lamp posts and lanterns (issue #219).
 *
 * DayNight.buildGlows puts a warm halo on every cell whose tile is a lamp post
 * or a lantern. A neon board or a lit shop front is part of a building many
 * cells big, so it is described here instead: a sprite declares GLOW SPOTS and
 * every placed copy of it gets them at night (and only at night).
 *
 * A spot is `{ x, y, r, ry, color, a, pulse, flicker }`:
 *   x, y    centre, in CELLS from the sprite's top-left corner (2.5 = half way
 *           across the third cell), so it does not depend on the art's scale
 *   r       horizontal radius in cells; `ry` the vertical one (default: r)
 *   color   0xRRGGBB (default: the lamps' warm 0xffb366)
 *   a       strength, 0..1 (default 1)
 *   pulse   { period: ms, depth: 0..1 } - a slow swell down to (1 - depth) and back
 *   flicker true - a neon tube: steady, with a short dip now and then
 *
 * Where the spots come from, in order: the sprite's `glow` list in config.json
 * `spriteMetadata` (data wins), then Glows.SPRITES below. The table is here
 * only because the art landed before its sprites were registered; a row can
 * move into spriteMetadata as it is, and be deleted here.
 *
 * A sprite that is not in either has no spots, so a world that uses none of
 * these sprites is drawn exactly as before.
 */
const Glows = {
    PINK: 0xff5fa8, CYAN: 0x4fe0e8, YELLOW: 0xffd24a, GREEN: 0x5fe07a,
    WARM: 0xffc070,      // a lit shop window
    COOL: 0xbfd4ff,      // a white-lit board or clock face
    DEFAULT: 0xffb366,   // the lamps' own colour

    /** The spots of a sprite key: its metadata's `glow`, else the table's, else none. */
    spotsFor(key, metadata) {
        const own = metadata && metadata.glow;
        const spots = Array.isArray(own) ? own : Glows.SPRITES[key];
        return Array.isArray(spots) ? spots.filter(Glows.valid) : [];
    },

    /** A spot needs a place and a size; anything else has a default. */
    valid(spot) {
        return !!spot && Number.isFinite(spot.x) && Number.isFinite(spot.y) && spot.r > 0;
    },

    /**
     * The halos of one placed sprite, in world pixels. `left` / `top` is the
     * corner of its art (a tile record's), `cell` one cell of it on screen
     * (GRID_SIZE x the sprite's scale). `seed` tells two copies of a sprite
     * apart so their tubes do not flicker in step.
     */
    place(left, top, cell, spots) {
        return spots.map((s, i) => ({
            x: left + s.x * cell, y: top + s.y * cell,
            rx: s.r * cell, ry: (s.ry > 0 ? s.ry : s.r) * cell,
            color: s.color === undefined ? Glows.DEFAULT : s.color,
            alpha: s.a === undefined ? 1 : Math.max(0, Math.min(1, s.a)),
            pulse: s.pulse && s.pulse.period > 0 ? { period: s.pulse.period, depth: Math.max(0, Math.min(1, s.pulse.depth || 0)) } : null,
            flicker: !!s.flicker,
            seed: (Math.round(left) * 31 + Math.round(top) * 17 + i * 7) >>> 0,
        }));
    },

    /** True when a halo's brightness changes with time (so it needs a look every frame). */
    animated(halo) {
        return !!(halo.pulse || halo.flicker);
    },

    /**
     * How bright a halo is at `ms`, as a factor of its own alpha: 1 when it is
     * steady. A pulse swells between 1 and (1 - depth) over its period; a
     * flickering tube is at 1 except for about one FLICKER_STEP in sixteen,
     * when it sags to FLICKER_DIP. Both depend only on the time and the seed.
     */
    level(halo, ms) {
        let level = 1;
        if (halo.pulse) {
            const phase = (ms / halo.pulse.period + (halo.seed % 97) / 97) * Math.PI * 2;
            level *= 1 - halo.pulse.depth * (0.5 - 0.5 * Math.cos(phase));
        }
        if (halo.flicker) {
            const step = Math.floor(ms / Glows.FLICKER_STEP);
            let h = (step * 2654435761 + halo.seed * 40503) >>> 0;
            h = ((h ^ (h >>> 15)) * 2246822519) >>> 0;
            if (((h >>> 8) & 15) === 0) level *= Glows.FLICKER_DIP;
        }
        return level;
    },

    /**
     * The alpha a sprite's halo is drawn at: its own strength, times its level
     * now (pulse / flicker), times how far its sprite is faded - `fade` is the
     * tile record's (Occlusion: 0.4 while somebody stands behind the building,
     * undefined at full strength), so a ghosted building's neon ghosts with it
     * instead of burning at full strength over it (issue #220).
     */
    shown(alpha, level, fade) {
        const f = Number.isFinite(fade) ? Math.max(0, Math.min(1, fade)) : 1;
        return alpha * level * f;
    },

    /**
     * The one halo texture every spot is a tinted, stretched copy of: white,
     * in the same six steps as a lamp's halo. Drawn once (an Image of it is a
     * single quad; a lamp's Graphics halo is re-tessellated every frame).
     */
    texture(scene) {
        if (scene.textures.exists(Glows.TEXTURE)) return Glows.TEXTURE;
        const size = Glows.TEXTURE_SIZE, canvas = document.createElement('canvas');
        canvas.width = canvas.height = size;
        const c = canvas.getContext('2d');
        c.fillStyle = '#ffffff';
        c.globalCompositeOperation = 'lighter';   // the steps add up, as a lamp's additive circles do
        for (let i = 6; i >= 1; i--) {
            c.globalAlpha = 0.028 * (7 - i);
            c.beginPath();
            c.arc(size / 2, size / 2, (size / 2) * i / 6, 0, Math.PI * 2);
            c.fill();
        }
        scene.textures.addCanvas(Glows.TEXTURE, canvas);
        return Glows.TEXTURE;
    },
};

Glows.TEXTURE = 'glow-halo';
Glows.TEXTURE_SIZE = 96;
Glows.FLICKER_STEP = 110;   // ms a flicker step lasts
Glows.FLICKER_DIP = 0.55;   // how far a tube sags when it dips

/**
 * Sapporo's lit fronts (art: tools/generate_sapporo_art.py), read off the
 * artwork. `susukino-neon-lanterns` and `ramen-alley-lanterns` are not here:
 * they are lanterns by name and get the lamps' halo.
 */
Glows.SPRITES = {
    // 5x7: the fox board, the name board, two small boards, three hanging signs, the shop floor
    'susukino-neon-corner_0_0': [
        { x: 1.9, y: 2.15, r: 2.0, color: Glows.PINK, a: 0.9, pulse: { period: 3200, depth: 0.35 } },
        { x: 1.9, y: 3.55, r: 1.5, ry: 0.7, color: Glows.PINK, flicker: true },
        { x: 1.0, y: 4.15, r: 0.9, ry: 0.6, color: Glows.YELLOW },
        { x: 2.9, y: 4.15, r: 1.0, ry: 0.6, color: Glows.CYAN },
        { x: 4.3, y: 1.6, r: 0.6, ry: 1.0, color: Glows.PINK },
        { x: 4.3, y: 2.9, r: 0.6, ry: 1.0, color: Glows.GREEN },
        { x: 4.3, y: 4.6, r: 0.6, ry: 1.1, color: Glows.CYAN },
        { x: 1.9, y: 6.05, r: 1.9, ry: 0.9, color: Glows.WARM, a: 0.8 },
    ],
    // 4x5: the karaoke board, the BAR sign, the coloured rooms, the door and menu boards
    'susukino-karaoke_0_0': [
        { x: 1.55, y: 1.25, r: 1.7, ry: 0.8, color: Glows.PINK, flicker: true },
        { x: 3.6, y: 2.4, r: 0.6, ry: 1.0, color: Glows.YELLOW },
        { x: 1.6, y: 2.6, r: 1.6, ry: 0.9, color: Glows.CYAN, a: 0.6 },
        { x: 2.0, y: 4.3, r: 1.7, ry: 0.8, color: Glows.WARM, a: 0.8 },
    ],
    // 3x3: the yellow board and the row of paper lanterns under it
    'susukino-ramen-gate_0_0': [
        { x: 1.5, y: 0.75, r: 1.5, ry: 0.7, color: Glows.YELLOW },
        { x: 1.5, y: 1.4, r: 1.2, ry: 0.5, color: 0xff8a5a },
    ],
    // 4x4: the bulbs along the arch, and the tanuki's roundel
    'tanukikoji-gate_0_0': [
        { x: 2.0, y: 1.9, r: 1.9, ry: 0.8, color: Glows.YELLOW, a: 0.8, pulse: { period: 2400, depth: 0.25 } },
        { x: 2.0, y: 0.7, r: 0.8, color: Glows.WARM, a: 0.5 },
    ],
    // 3x4 each: the lit windows of the arcade's three shops (issue #219, stage 3) - warm for the gift
    // boxes and the lamplit crab shop, cool white for the drugstore's shelves
    'tanukikoji-shop-souvenir_0_0': [{ x: 1.5, y: 2.9, r: 1.5, ry: 0.8, color: Glows.WARM, a: 0.6 }],
    'tanukikoji-shop-crab_0_0': [{ x: 1.5, y: 2.9, r: 1.5, ry: 0.8, color: Glows.WARM, a: 0.6 }],
    'tanukikoji-shop-drug_0_0': [{ x: 1.5, y: 2.9, r: 1.5, ry: 0.8, color: Glows.COOL, a: 0.55 }],
    // 10x7: the star clock, the name board, the shop windows either side of the doors
    'sapporo-station-front_0_0': [
        { x: 5.0, y: 2.5, r: 1.3, color: Glows.COOL, a: 0.7 },
        { x: 5.4, y: 4.0, r: 1.7, ry: 0.7, color: Glows.COOL, a: 0.8 },
        { x: 2.3, y: 6.2, r: 2.3, ry: 0.9, color: Glows.WARM, a: 0.8 },
        { x: 8.0, y: 6.2, r: 2.3, ry: 0.9, color: Glows.WARM, a: 0.8 },
        { x: 5.4, y: 6.2, r: 1.2, ry: 0.9, color: Glows.COOL, a: 0.5 },
    ],
    // 4x3: the glass front
    'sapporo-konbini_0_0': [
        { x: 2.0, y: 1.9, r: 2.0, ry: 1.0, color: 0xfff0c8, a: 0.8 },
    ],
    // 3x3 each: the lamp under the awning
    'snowfest-stall-corn_0_0': [
        { x: 1.5, y: 1.6, r: 1.4, ry: 0.9, color: Glows.WARM },
    ],
    'snowfest-stall-drinks_0_0': [
        { x: 1.5, y: 1.6, r: 1.4, ry: 0.9, color: Glows.WARM },
    ],
    // the palace's audience hall (issue #215, art: tools/generate_palace_art.py; the room is
    // `lanternLight`, so these are lit at night and only then). 1x2: a standing paper lamp
    'palace-in-andon_0_0': [
        { x: 0.5, y: 0.95, r: 1.5, color: 0xffc878, a: 0.9 },
    ],
    // 1x2: a gilt lamp hung from the ceiling
    'palace-in-lamp-hang_0_0': [
        { x: 0.5, y: 1.0, r: 1.7, color: 0xffb860 },
    ],
    // 12x3: the two candles either side of the seat (they breathe), the embers of the two braziers
    'palace-in-dais_0_0': [
        { x: 4.05, y: 0.45, r: 1.3, color: 0xffd890, pulse: { period: 2600, depth: 0.3 } },
        { x: 7.95, y: 0.45, r: 1.3, color: 0xffd890, pulse: { period: 3100, depth: 0.3 } },
        { x: 2.5, y: 1.6, r: 0.7, color: 0xff7848, a: 0.6 },
        { x: 9.5, y: 1.6, r: 0.7, color: 0xff7848, a: 0.6 },
    ],
    // 3x2: the watch's lamp at the end of the rack
    'palace-in-guardpost_0_0': [
        { x: 2.55, y: 0.95, r: 1.2, color: 0xffc878, a: 0.9 },
    ],
    // a temple's main hall (issue #213, art: tools/generate_temple_art.py; `lanternLight` too).
    // 1x2: a gilt lantern hung from the ceiling
    'temple-in-toro-hang_0_0': [
        { x: 0.5, y: 1.0, r: 1.6, color: 0xffb860 },
    ],
    // 1x2: one fat candle on a tall stand (it breathes)
    'temple-in-shokudai_0_0': [
        { x: 0.5, y: 0.25, r: 1.3, color: 0xffd890, pulse: { period: 2300, depth: 0.3 } },
    ],
    // 2x2: a rack of votive candles
    'temple-in-candles_0_0': [
        { x: 1.0, y: 1.1, r: 1.5, ry: 1.1, color: 0xffc070, pulse: { period: 2900, depth: 0.25 } },
    ],
    // 4x3: the great red paper lantern, lit from inside
    'temple-in-chochin_0_0': [
        { x: 2.0, y: 1.45, r: 2.3, color: 0xff6040, a: 0.8 },
    ],
    // 4x3: the embers in the incense burner's ash
    'temple-in-jokoro_0_0': [
        { x: 2.0, y: 1.55, r: 1.2, ry: 0.7, color: 0xff7848, a: 0.7, pulse: { period: 3400, depth: 0.35 } },
    ],
    // 16x4: the sanctum behind the lattice - the two banks of candles, the altar's pair, the two standing lanterns
    'temple-in-naijin_0_0': [
        { x: 4.45, y: 0.6, r: 2.0, ry: 1.2, color: 0xffd890, pulse: { period: 2600, depth: 0.25 } },
        { x: 11.55, y: 0.6, r: 2.0, ry: 1.2, color: 0xffd890, pulse: { period: 3100, depth: 0.25 } },
        { x: 8.0, y: 0.3, r: 1.4, color: 0xffd890, a: 0.8 },
        { x: 3.0, y: 0.6, r: 1.0, color: 0xffc878, a: 0.8 },
        { x: 13.0, y: 0.6, r: 1.0, color: 0xffc878, a: 0.8 },
    ],
    // 6x3: the gold of the cabinet, lit from below
    'temple-in-kuden_0_0': [
        { x: 3.0, y: 1.8, r: 1.6, color: 0xffc060, a: 0.7 },
    ],
};

if (typeof window !== 'undefined') window.Glows = Glows;
