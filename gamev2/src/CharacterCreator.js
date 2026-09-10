/**
 * CharacterCreator — make your own character (name + look).
 *
 * The cast sprites (james/bailey/damian/dylan/julia) are flat-palette pixel
 * art drawn on one shared 64×64 template: every body has the same shoulder
 * line, waist line and feet rows per animation frame. That makes real
 * mix-and-match possible without new art:
 *
 *   HAIR  — the head band of any cast member (their hairstyle + face)
 *   TOP   — the torso band of any cast member (their shirt, arms included)
 *   LEGS  — the lower band of any cast member (trousers/shorts + shoes)
 *   BEARD — the facial-hair pixels of a bearded cast member (bailey/damian),
 *           overlaid on any face (all faces share the same geometry)
 *
 * Each part recolours independently by palette-swapping that donor's colour
 * slots; two-tone slots keep their light/dark offset from the slot's anchor
 * so shading survives any recolour. Long hair that hangs past the shoulder
 * line is carried by pixel class (hair colours), not by row, so it overlays
 * whatever top is worn.
 *
 * The composed frames become the `custom_front/back/side` sprite set, which
 * flows through SpriteSystem/Character/CharacterSelect exactly like a cast
 * character. The creation persists in localStorage and is rebuilt from the
 * base sprites on boot. Shown automatically on first ever play; afterwards
 * via Menu → Create Character (or the custom row in Menu → Character).
 */
class CharacterCreator {
    // Per-donor palette slots, measured from the actual sprite frames. The
    // first colour in each slot is the anchor; the rest keep their lightness
    // offset from it when recoloured. `legs` lists the colours of the lower
    // garment where the sprite draws one (otherwise the legs reuse `top`
    // colours and are recoloured via the LEGS choice anyway, band-scoped).
    static DONORS = {
        james:  { skin: ['#f6c39a', '#fdcba2'], hair: ['#3c2e20'],            top: ['#a53137', '#ea757b'], legs: [] },
        bailey: { skin: ['#f4bc8e'],            hair: ['#58371b'],            top: ['#327345', '#63c64d'], legs: ['#afbfd2'] },
        damian: { skin: ['#f9cba4', '#f4bc8e'], hair: ['#e6af3a', '#ffd962'], top: ['#fa7c00'],            legs: ['#327345', '#63c64d'] },
        dylan:  { skin: ['#fdcba2'],            hair: ['#1c150e'],            top: ['#193d3f'],            legs: [] },
        julia:  { skin: ['#f2ab70'],            hair: ['#150b06'],            top: ['#032e48', '#011a29'], legs: ['#d9d9d9'] },
    };

    /** Cast members with facial hair to lend. */
    static BEARDS = ['bailey', 'damian'];

    // Template cut rows per direction, indexed by frame (walk frames shift
    // the template by 2px — measured across all 50 frames, identical for
    // every body). topStart = first torso row, bottomStart = first legs row.
    static CUTS = {
        front: { top: [38, 40, 38, 40], bottom: [46, 48, 46, 48] },
        back:  { top: [36, 34, 36, 34], bottom: [44, 42, 44, 42] },
        side:  { top: [36, 36],         bottom: [44, 46] },
    };

    /** Is (x,y) inside the facial-hair box for this direction/frame? */
    static inBeardBox(dir, frame, x, y) {
        if (dir === 'back') return false;
        if (dir === 'front') {
            const off = (frame % 2) * 2; // walk frames sit 2px lower
            return y >= 28 + off && y < 36 + off;
        }
        // side: chin/jaw of a right-facing profile; s1 sits 2px higher
        const off = frame === 1 ? -2 : 0;
        return y >= 26 + off && y < 34 + off && x >= 22;
    }

    static SKIN_TONES = ['#ffe3c9', '#fdcba2', '#f6c39a', '#f2ab70', '#c98a52', '#96613a', '#6b4226'];
    static HAIR_COLORS = ['#1a1208', '#3c2e20', '#58371b', '#8a5a2b', '#e6af3a', '#b0491f', '#e53b44', '#ff7eb6', '#7e4fc9', '#3a6fd8', '#2ea44f', '#d9d9d9'];
    static OUTFIT_COLORS = ['#a53137', '#e53b44', '#fa7c00', '#e6af3a', '#63c64d', '#327345', '#3a6fd8', '#032e48', '#7e4fc9', '#ff7eb6', '#8a5a2b', '#2b2b33', '#d9d9d9'];

    static STORAGE_KEY = 'gamev2_custom_character';
    static SEEN_KEY = 'gamev2_creator_seen';

    // ---------------------------------------------------------------- state

    /** The saved creation (migrated to the parts format), or null. */
    static load() {
        try {
            const data = JSON.parse(localStorage.getItem(CharacterCreator.STORAGE_KEY));
            if (!data) return null;
            // v1 creations had a single `body`; split it into parts
            if (!data.parts && data.body && CharacterCreator.DONORS[data.body]) {
                data.parts = { hair: data.body, top: data.body, legs: data.body, beard: null };
            }
            const p = data.parts;
            if (!p || !CharacterCreator.DONORS[p.hair] || !CharacterCreator.DONORS[p.top] ||
                !CharacterCreator.DONORS[p.legs]) return null;
            if (p.beard && !CharacterCreator.BEARDS.includes(p.beard)) p.beard = null;
            data.colors = data.colors || {};
            return data;
        } catch (e) { return null; }
    }

    static save(data) {
        try {
            localStorage.setItem(CharacterCreator.STORAGE_KEY, JSON.stringify(data));
            localStorage.setItem('gamev2_character', 'custom');
            localStorage.setItem(CharacterCreator.SEEN_KEY, '1');
        } catch (e) { /* play on without persistence */ }
    }

    /** First ever visit: no character chosen and the creator never dismissed. */
    static shouldAutoShow() {
        try {
            return !localStorage.getItem('gamev2_character') && !localStorage.getItem(CharacterCreator.SEEN_KEY);
        } catch (e) { return false; }
    }

    // ------------------------------------------------------------ boot hooks

    /**
     * Patch config so a saved custom character is the player from frame one.
     * Call right after CharacterSelect.applySaved (before SpriteSystem boots).
     */
    static applySaved(config) {
        const data = CharacterCreator.load();
        let mode = null;
        try { mode = localStorage.getItem('gamev2_character'); } catch (e) { /* no storage */ }
        if (!data || mode !== 'custom' || !config.spriteMetadata[`${data.parts.hair}_front`]) return;

        CharacterCreator.injectMetadata(config.spriteMetadata, data.parts.hair);
        config.player.sprite = 'custom_front';
        config.player.directionalSprites = {
            down: 'custom_front', up: 'custom_back', right: 'custom_side', left: '',
        };
        config.player.autoFlip = { horizontal: true, vertical: false };
        if (data.name) config.player.name = data.name;
    }

    /**
     * Build the custom textures at boot. Call after spriteSystem.initialize()
     * (the base frames are loaded) and BEFORE createAnimations() (so the
     * custom walk cycles are created from the fresh textures).
     */
    static buildSavedTextures(scene) {
        const data = CharacterCreator.load();
        let mode = null;
        try { mode = localStorage.getItem('gamev2_character'); } catch (e) { /* no storage */ }
        if (data && mode === 'custom') CharacterCreator.buildTextures(scene, data);
    }

    /** Clone a base body's sprite metadata as the custom_* sprite set. */
    static injectMetadata(spriteMetadata, body) {
        for (const dir of ['front', 'back', 'side']) {
            const base = spriteMetadata[`${body}_${dir}`];
            if (base) spriteMetadata[`custom_${dir}`] = JSON.parse(JSON.stringify(base));
        }
    }

    /** Rebuild metadata + textures + walk animations for a (new) creation. */
    static rebuild(scene, data) {
        for (const dir of ['front', 'back', 'side']) {
            const animKey = `custom_${dir}_anim`;
            if (scene.anims.exists(animKey)) scene.anims.remove(animKey);
        }
        CharacterCreator.injectMetadata(scene.spriteSystem.spriteMetadata, data.parts.hair);
        CharacterCreator.buildTextures(scene, data);
        scene.spriteSystem.createAnimations();
    }

    /** Make sure the custom textures exist (e.g. for CharacterSelect's preview). */
    static ensureTextures(scene) {
        const data = CharacterCreator.load();
        if (!data) return false;
        if (!scene.textures.exists('custom_front_frame_0')) CharacterCreator.rebuild(scene, data);
        return true;
    }

    /** Become the custom character: rebuild textures and swap the live player. */
    static applyToPlayer(scene, data) {
        if (!data || !data.parts) return;
        const p = scene.player;

        // detach the player from the custom textures before they're rebuilt
        if (p.sprite.texture && String(p.sprite.texture.key).startsWith('custom_')) {
            if (p.sprite.anims) p.sprite.anims.stop();
            p.sprite.setTexture(`${data.parts.hair}_front_frame_0`);
        }
        CharacterCreator.rebuild(scene, data);

        const meta = scene.spriteSystem.spriteMetadata.custom_front;
        meta.isDirectional = true;
        meta.directions = { down: 'custom_front', up: 'custom_back', right: 'custom_side', left: '' };
        meta.autoFlip = { horizontal: true, vertical: false };

        scene.config.player.name = data.name || 'Player';
        p.name = scene.config.player.name;
        p.baseSpriteKey = 'custom_front';
        p.isDirectional = true;
        p.currentDirection = 'none';        // force the texture swap below
        p.updateDirectionSprite(0, 1);      // face the camera as the new you

        scene.syncNpcPresence();            // playing custom: the whole cast exists
        if (scene.syncPlayerNameLabel) scene.syncPlayerNameLabel();
    }

    // -------------------------------------------------------- colour maths

    static hexToRgb(hex) {
        const n = parseInt(hex.slice(1), 16);
        return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }

    static rgbToHsl(r, g, b) {
        r /= 255; g /= 255; b /= 255;
        const max = Math.max(r, g, b), min = Math.min(r, g, b);
        const l = (max + min) / 2;
        if (max === min) return { h: 0, s: 0, l };
        const d = max - min;
        const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        let h;
        if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        else if (max === g) h = ((b - r) / d + 2) / 6;
        else h = ((r - g) / d + 4) / 6;
        return { h, s, l };
    }

    static hslToRgb(h, s, l) {
        if (s === 0) { const v = Math.round(l * 255); return [v, v, v]; }
        const hue = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1 / 6) return p + (q - p) * 6 * t;
            if (t < 1 / 2) return q;
            if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
            return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        return [hue(p, q, h + 1 / 3), hue(p, q, h), hue(p, q, h - 1 / 3)].map(v => Math.round(v * 255));
    }

    static rgbInt(hex) {
        const [r, g, b] = CharacterCreator.hexToRgb(hex);
        return (r << 16) | (g << 8) | b;
    }

    /** Shade-preserving recolour of a slot: {srcRgbInt: [r,g,b]}, merged into map. */
    static addSlot(map, srcs, chosenHex) {
        if (!srcs || !srcs.length || !chosenHex) return;
        const anchor = CharacterCreator.rgbToHsl(...CharacterCreator.hexToRgb(srcs[0]));
        const chosen = CharacterCreator.rgbToHsl(...CharacterCreator.hexToRgb(chosenHex));
        for (const src of srcs) {
            const s = CharacterCreator.rgbToHsl(...CharacterCreator.hexToRgb(src));
            const l = Math.min(0.97, Math.max(0.04, chosen.l + (s.l - anchor.l)));
            map[CharacterCreator.rgbInt(src)] = CharacterCreator.hslToRgb(chosen.h, chosen.s, l);
        }
    }

    // ------------------------------------------------------- frame compose

    /** rgbInt → 'skin'|'hair'|'top'|'legs' classifier for one donor. */
    static classifier(donor) {
        const def = CharacterCreator.DONORS[donor];
        const cls = {};
        for (const slot of ['skin', 'hair', 'top', 'legs']) {
            for (const hex of def[slot]) cls[CharacterCreator.rgbInt(hex)] = slot;
        }
        return cls;
    }

    /** ImageData of one loaded base frame (or null). */
    static frameData(scene, key) {
        if (!scene.textures.exists(key)) return null;
        const tex = scene.textures.get(key);
        const img = tex.getSourceImage ? tex.getSourceImage() : tex.source[0].image;
        if (!img) return null;
        const c = document.createElement('canvas');
        c.width = img.width;
        c.height = img.height;
        const ctx = c.getContext('2d', { willReadFrequently: true });
        ctx.drawImage(img, 0, 0);
        return ctx.getImageData(0, 0, c.width, c.height);
    }

    /**
     * Compose one frame of the creation onto a fresh canvas:
     * legs band → torso band → head (+ trailing hair) → beard overlay.
     * Each part recoloured with its own donor-scoped palette map.
     */
    static composeFrame(scene, data, dir, frame) {
        const { parts, colors } = data;
        const cuts = CharacterCreator.CUTS[dir];
        const topStart = cuts.top[frame];
        const bottomStart = cuts.bottom[frame];

        const src = {};
        for (const part of ['hair', 'top', 'legs']) {
            src[part] = CharacterCreator.frameData(scene, `${parts[part]}_${dir}_frame_${frame}`);
            if (!src[part]) return null;
        }
        if (parts.beard) {
            src.beard = CharacterCreator.frameData(scene, `${parts.beard}_${dir}_frame_${frame}`);
        }
        const W = src.hair.width, H = src.hair.height;

        // per-part recolour maps (skin applies everywhere so donors match)
        const D = CharacterCreator.DONORS;
        const maps = { hair: {}, top: {}, legs: {}, beard: {} };
        CharacterCreator.addSlot(maps.hair, D[parts.hair].skin, colors.skin);
        CharacterCreator.addSlot(maps.hair, D[parts.hair].hair, colors.hair);
        CharacterCreator.addSlot(maps.top, D[parts.top].skin, colors.skin);
        CharacterCreator.addSlot(maps.top, D[parts.top].top, colors.top);
        CharacterCreator.addSlot(maps.legs, D[parts.legs].skin, colors.skin);
        // the lower band recolours as one garment: donors with their own legs
        // colours anchor there; james/dylan draw legs in their top colours
        const legDef = D[parts.legs];
        const legSrcs = legDef.legs.length ? legDef.legs.concat(legDef.top) : legDef.top;
        CharacterCreator.addSlot(maps.legs, legSrcs, colors.legs);
        if (parts.beard) {
            CharacterCreator.addSlot(maps.beard, D[parts.beard].hair, colors.beard);
        }

        const cls = {
            hair: CharacterCreator.classifier(parts.hair),
            top: CharacterCreator.classifier(parts.top),
            legs: CharacterCreator.classifier(parts.legs),
            beard: parts.beard ? CharacterCreator.classifier(parts.beard) : null,
        };

        const out = new ImageData(W, H);
        const put = (x, y, d, i, map) => {
            const int = (d[i] << 16) | (d[i + 1] << 8) | d[i + 2];
            const t = map[int];
            const o = (y * W + x) * 4;
            out.data[o] = t ? t[0] : d[i];
            out.data[o + 1] = t ? t[1] : d[i + 1];
            out.data[o + 2] = t ? t[2] : d[i + 2];
            out.data[o + 3] = d[i + 3];
        };
        const each = (part, fn) => {
            const d = src[part].data;
            const c = cls[part];
            for (let y = 0; y < H; y++) {
                for (let x = 0; x < W; x++) {
                    const i = (y * W + x) * 4;
                    if (d[i + 3] === 0) continue;
                    fn(x, y, d, i, c[(d[i] << 16) | (d[i + 1] << 8) | d[i + 2]]);
                }
            }
        };

        // LEGS: everything from the waist down, plus this donor's legs-slot
        // pixels that poke above it (damian's high shoe tops)
        each('legs', (x, y, d, i, c) => {
            if (c === 'hair') return;
            if (y >= bottomStart || (c === 'legs' && y >= topStart)) put(x, y, d, i, maps.legs);
        });
        // TOP: the torso band (arms included — skin recolours globally), plus
        // this donor's top-slot pixels above the shoulder line (high sleeves)
        each('top', (x, y, d, i, c) => {
            if (c === 'hair' || c === 'legs') return;
            if ((y >= topStart && y < bottomStart) || (c === 'top' && y < topStart)) put(x, y, d, i, maps.top);
        });
        // HEAD: everything above the shoulder line except this donor's own
        // clothing, plus hair pixels at ANY row (long hair over the shirt)
        each('hair', (x, y, d, i, c) => {
            if (c === 'top' || c === 'legs') return;
            if (y < topStart || c === 'hair') put(x, y, d, i, maps.hair);
        });
        // BEARD: the donor's facial-hair pixels, on top of the new face
        if (parts.beard && src.beard) {
            each('beard', (x, y, d, i, c) => {
                if (c === 'hair' && CharacterCreator.inBeardBox(dir, frame, x, y)) put(x, y, d, i, maps.beard);
            });
        }

        const canvas = document.createElement('canvas');
        canvas.width = W;
        canvas.height = H;
        canvas.getContext('2d').putImageData(out, 0, 0);
        return canvas;
    }

    /** Compose one frame and register it as a texture. Returns success. */
    static buildFrame(scene, data, dir, frame, destKey) {
        const canvas = CharacterCreator.composeFrame(scene, data, dir, frame);
        if (!canvas) return false;
        if (scene.textures.exists(destKey)) scene.textures.remove(destKey);
        scene.textures.addCanvas(destKey, canvas);
        return true;
    }

    /** Build the full custom_front/back/side frame set for a creation. */
    static buildTextures(scene, data) {
        const fallback = { front: 4, back: 4, side: 2 };
        const sm = (scene.spriteSystem && scene.spriteSystem.spriteMetadata) ||
            (scene.config && scene.config.spriteMetadata) || {};
        for (const dir of ['front', 'back', 'side']) {
            const meta = sm[`${data.parts.hair}_${dir}`];
            const count = (meta && meta.frameCount) || fallback[dir];
            for (let i = 0; i < count; i++) {
                CharacterCreator.buildFrame(scene, data, dir, i, `custom_${dir}_frame_${i}`);
            }
        }
    }

    // ---------------------------------------------------------------- UI

    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.objs = [];
        this.nameInput = null;
        this.previewCounter = 0;
        this.previewKey = null;
        this.onResize = () => this.positionNameInput();
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({
            up: K.UP, down: K.DOWN, left: K.LEFT, right: K.RIGHT,
            w: K.W, s: K.S, a: K.A, d: K.D,
            enter: K.ENTER, space: K.SPACE, esc: K.ESC, r: K.R,
        });
        this.donors = Object.keys(CharacterCreator.DONORS)
            .filter(b => (scene.config.spriteMetadata || {})[`${b}_front`]);
        this.views = ['front', 'side', 'back'];
    }

    isVisible() { return this.visible; }

    show(opts = {}) {
        if (this.visible || !this.donors.length) return;
        this.firstRun = !!opts.firstRun;
        const saved = CharacterCreator.load();
        this.data = saved ? JSON.parse(JSON.stringify(saved)) : {
            name: '',
            parts: { hair: this.donors[0], top: this.donors[0], legs: this.donors[0], beard: null },
            colors: { skin: null, hair: null, top: null, legs: null, beard: null },
        };
        this.data.colors = this.data.colors || {};
        this.view = 0;
        this.selectedRow = 0;
        const JD = Phaser.Input.Keyboard.JustDown;
        Object.values(this.keys).forEach(k => JD(k)); // swallow stale presses
        this.visible = true;
        this.render();
    }

    hide() {
        if (!this.visible) return;
        this.visible = false;
        try { localStorage.setItem(CharacterCreator.SEEN_KEY, '1'); } catch (e) { /* fine */ }
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.swatchRows = [];
        this.rowDefs = [];
        if (this.nameInput) {
            this.nameInput.remove();
            this.nameInput = null;
            window.removeEventListener('resize', this.onResize);
        }
        if (this.previewKey && this.scene.textures.exists(this.previewKey)) {
            this.scene.textures.remove(this.previewKey);
            this.previewKey = null;
        }
    }

    confirm() {
        const data = this.data;
        data.name = (data.name || '').trim().slice(0, 12);
        CharacterCreator.save(data);
        CharacterCreator.applyToPlayer(this.scene, data);
        this.hide();
    }

    randomise() {
        const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
        this.data.parts = {
            hair: pick(this.donors),
            top: pick(this.donors),
            legs: pick(this.donors),
            beard: Math.random() < 0.35 ? pick(CharacterCreator.BEARDS) : null,
        };
        this.data.colors = {
            skin: pick(CharacterCreator.SKIN_TONES),
            hair: pick(CharacterCreator.HAIR_COLORS),
            top: pick(CharacterCreator.OUTFIT_COLORS),
            legs: pick(CharacterCreator.OUTFIT_COLORS),
            beard: pick(CharacterCreator.HAIR_COLORS),
        };
        this.paint();
    }

    // ------------------------------------------------------------- input

    handleInput() {
        // while typing a name, the DOM input owns the keyboard
        if (this.nameInput && document.activeElement === this.nameInput) return;
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        if (JD(k.enter) || JD(k.space)) return this.confirm();
        if (JD(k.r)) return this.randomise();
        const n = this.rowDefs.length;
        if (!n) return;
        if (JD(k.up) || JD(k.w)) { this.selectedRow = (this.selectedRow - 1 + n) % n; this.paint(); }
        if (JD(k.down) || JD(k.s)) { this.selectedRow = (this.selectedRow + 1) % n; this.paint(); }
        if (JD(k.left) || JD(k.a)) this.cycle(-1);
        if (JD(k.right) || JD(k.d)) this.cycle(1);
    }

    /** Left/right on the selected row: previous/next donor or swatch. */
    cycle(step) {
        const row = this.rowDefs[this.selectedRow];
        if (!row) return;
        if (row.kind === 'donor') {
            const options = row.optional ? [null, ...row.donors] : row.donors;
            const i = options.indexOf(this.data.parts[row.part]);
            this.data.parts[row.part] = options[(Math.max(i, 0) + step + options.length) % options.length];
            this.paint();
        } else if (row.kind === 'color') {
            const options = [null, ...row.palette];
            const cur = options.indexOf(this.data.colors[row.slot] || null);
            this.data.colors[row.slot] = options[(Math.max(cur, 0) + step + options.length) % options.length];
            this.paint();
        }
    }

    // ---------------------------------------------------------- rendering

    /** Layout constants shared by render() and the DOM name input. */
    layout() {
        const cam = this.scene.cameras.main;
        const pw = 720, ph = 660;
        return {
            W: cam.width, H: cam.height, pw, ph,
            px: (cam.width - pw) / 2, py: (cam.height - ph) / 2,
        };
    }

    render() {
        const scene = this.scene;
        const { W, H, pw, ph, px, py } = this.layout();
        const objs = this.objs;

        const overlay = scene.add.graphics();
        overlay.fillStyle(0x000000, 0.8);
        overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0);
        overlay.setDepth(2000);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        objs.push(overlay);

        const panel = scene.add.graphics();
        panel.fillStyle(0x1a1a1a, 1);
        panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x666666, 1);
        panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0);
        panel.setDepth(2001);
        objs.push(panel);

        const text = (x, y, t, size, opts = {}) => {
            const o = scene.add.text(x, y, t, {
                fontSize: size, fill: opts.color || '#ffffff',
                fontFamily: opts.bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono',
            });
            o.setOrigin(opts.originX !== undefined ? opts.originX : 0.5, 0.5);
            o.setResolution(1);
            o.setScrollFactor(0);
            o.setDepth(2002);
            objs.push(o);
            return o;
        };

        text(W / 2, py + 34, 'CREATE YOUR CHARACTER', '28px', { bold: true });

        // ✕ close (the touch-screen ESC)
        const close = text(px + pw - 24, py + 26, '✕', '24px', { color: '#888888' });
        close.setInteractive({ useHandCursor: true });
        close.on('pointerdown', () => this.hide());

        // live preview + view rotation
        this.preview = scene.add.image(px + 130, py + 240, 'tile');
        this.preview.setScale(2);
        this.preview.setScrollFactor(0);
        this.preview.setDepth(2002);
        objs.push(this.preview);
        const mkViewArrow = (x, step) => {
            const a = text(x, py + 340, step < 0 ? '‹' : '›', '32px', { bold: true, color: '#aaaaaa' });
            a.setInteractive({ useHandCursor: true });
            a.on('pointerdown', () => {
                this.view = (this.view + step + this.views.length) % this.views.length;
                this.paint();
            });
        };
        mkViewArrow(px + 60, -1);
        mkViewArrow(px + 200, 1);
        this.viewLabel = text(px + 130, py + 340, 'FRONT', '16px', { color: '#888888' });

        // name (a real DOM input so typing works on desktop AND mobile)
        text(px + 250, py + 88, 'NAME', '20px', { bold: true, originX: 0 });
        this.createNameInput();

        // sections: one donor row + one colour row per part, plus skin
        this.rowDefs = [
            { kind: 'donor', part: 'hair', label: 'HAIR', donors: this.donors },
            { kind: 'color', slot: 'hair', palette: CharacterCreator.HAIR_COLORS, of: 'hair' },
            { kind: 'donor', part: 'beard', label: 'BEARD', donors: CharacterCreator.BEARDS, optional: true },
            { kind: 'color', slot: 'beard', palette: CharacterCreator.HAIR_COLORS, of: 'beard' },
            { kind: 'color', slot: 'skin', label: 'SKIN', palette: CharacterCreator.SKIN_TONES },
            { kind: 'donor', part: 'top', label: 'TOP', donors: this.donors },
            { kind: 'color', slot: 'top', palette: CharacterCreator.OUTFIT_COLORS, of: 'top' },
            { kind: 'donor', part: 'legs', label: 'LEGS', donors: this.donors },
            { kind: 'color', slot: 'legs', palette: CharacterCreator.OUTFIT_COLORS, of: 'legs' },
        ];

        this.rowLabels = [];
        this.donorValues = {};
        this.swatchRows = [];
        let y = py + 136;
        this.rowDefs.forEach((row, rowIndex) => {
            if (row.kind === 'donor') {
                this.rowLabels.push(text(px + 250, y, row.label, '20px', { bold: true, originX: 0 }));
                const mk = (x, step) => {
                    const a = text(x, y, step < 0 ? '‹' : '›', '26px', { bold: true, color: '#aaaaaa' });
                    a.setInteractive({ useHandCursor: true });
                    a.on('pointerdown', () => { this.selectedRow = rowIndex; this.cycle(step); });
                };
                mk(px + 440, -1);
                mk(px + 662, 1);
                this.donorValues[row.part] = text(px + 551, y, '', '20px', { bold: true });
                y += 34;
            } else {
                if (row.label) {
                    this.rowLabels.push(text(px + 250, y, row.label, '20px', { bold: true, originX: 0 }));
                    y += 30;
                } else {
                    // colour strip belonging to the donor row above it
                    this.rowLabels.push(this.rowLabels[this.rowLabels.length - 1]);
                }
                const swatches = [];
                const options = [null, ...row.palette];
                options.forEach((hex, i) => {
                    const sx = px + 262 + i * 31;
                    const r = scene.add.rectangle(sx, y, 22, 22, 0x000000);
                    r.setScrollFactor(0);
                    r.setDepth(2002);
                    r.setInteractive({ useHandCursor: true });
                    r.on('pointerdown', () => {
                        this.selectedRow = rowIndex;
                        this.data.colors[row.slot] = hex;
                        this.paint();
                    });
                    objs.push(r);
                    swatches.push({ rect: r, hex });
                });
                this.swatchRows[rowIndex] = swatches;
                y += row.label ? 40 : 46;
            }
        });

        // buttons
        const btn = (x, label, cb) => {
            const b = scene.add.rectangle(x, py + ph - 66, 190, 44, 0x2b2b2b);
            b.setStrokeStyle(2, 0x666666);
            b.setScrollFactor(0);
            b.setDepth(2002);
            b.setInteractive({ useHandCursor: true });
            b.on('pointerdown', cb);
            objs.push(b);
            text(x, py + ph - 66, label, '20px', { bold: true });
        };
        btn(px + 360, 'RANDOM (R)', () => this.randomise());
        btn(px + 570, 'START ▶', () => this.confirm());

        text(W / 2, py + ph - 24, '↑/↓ pick a row · ←/→ change it · ENTER: play · ESC: cancel', '14px', { color: '#888888' });

        this.paint();
    }

    /** Update everything that changes without a full re-render. */
    paint() {
        if (!this.visible) return;
        const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
        if (this.viewLabel) this.viewLabel.setText(this.views[this.view].toUpperCase());

        for (const part of ['hair', 'top', 'legs', 'beard']) {
            const v = this.donorValues[part];
            if (v) v.setText(this.data.parts[part] ? cap(this.data.parts[part]) : 'None');
        }

        // donor + colour rows of one section share a label object — highlight
        // the label when EITHER of its rows is selected
        const selectedLabel = this.rowLabels[this.selectedRow];
        this.rowLabels.forEach(l => l.setFill(l === selectedLabel ? '#ffff00' : '#ffffff'));

        this.rowDefs.forEach((row, i) => {
            if (row.kind !== 'color') return;
            const chosen = this.data.colors[row.slot] || null;
            // the leading "original" swatch previews the relevant donor's colour
            const donorOf = row.of === 'beard' ? (this.data.parts.beard || CharacterCreator.BEARDS[0])
                : row.of ? this.data.parts[row.of] : null;
            const def = donorOf ? CharacterCreator.DONORS[donorOf] : null;
            const original = row.slot === 'skin' ? '#f6c39a'
                : def ? (row.slot === 'legs'
                    ? (def.legs[0] || def.top[0])
                    : def[row.slot === 'beard' ? 'hair' : row.slot][0])
                : '#f6c39a';
            this.swatchRows[i].forEach((s, j) => {
                s.rect.setFillStyle(parseInt((s.hex || original).slice(1), 16));
                const selected = s.hex === chosen;
                s.rect.setStrokeStyle(selected ? 3 : 1, selected ? 0xffff00 : 0x666666);
            });
        });
        this.paintPreview();
    }

    /** Rebuild the preview texture for the current selection + view. */
    paintPreview() {
        const scene = this.scene;
        const view = this.views[this.view];
        // side sheets idle on frame 1 (feet together); front/back on frame 0
        const frame = view === 'side' ? 1 : 0;
        const canvas = CharacterCreator.composeFrame(scene, this.data, view, frame);
        if (!canvas) return;
        const key = `__creator_preview_${this.previewCounter++}`;
        scene.textures.addCanvas(key, canvas);
        this.preview.setTexture(key);
        if (this.previewKey && scene.textures.exists(this.previewKey)) {
            scene.textures.remove(this.previewKey);
        }
        this.previewKey = key;
    }

    // ------------------------------------------------------- DOM name input

    createNameInput() {
        const el = document.createElement('input');
        el.type = 'text';
        el.maxLength = 12;
        el.placeholder = 'your name…';
        el.value = this.data.name || '';
        el.autocomplete = 'off';
        el.style.cssText = [
            'position:fixed', 'z-index:1000', 'box-sizing:border-box',
            'background:#000', 'color:#fff', 'border:2px solid #666',
            'text-align:center', "font-family:'PixelOperatorMono',monospace",
            'outline:none',
        ].join(';');
        el.addEventListener('input', () => { this.data.name = el.value; });
        // keep typed keys (arrows, R, space, enter…) away from Phaser
        el.addEventListener('keydown', (e) => {
            e.stopPropagation();
            if (e.key === 'Enter' || e.key === 'Escape') el.blur();
        });
        el.addEventListener('focus', () => {
            const kb = this.scene.input.keyboard;
            if (kb.disableGlobalCapture) kb.disableGlobalCapture();
        });
        el.addEventListener('blur', () => {
            const kb = this.scene.input.keyboard;
            if (kb.enableGlobalCapture) kb.enableGlobalCapture();
        });
        document.body.appendChild(el);
        this.nameInput = el;
        window.addEventListener('resize', this.onResize);
        this.positionNameInput();
    }

    /** Map panel game-coords onto the (scaled, centered) canvas. */
    positionNameInput() {
        if (!this.nameInput) return;
        const canvas = this.scene.game.canvas;
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const sx = rect.width / this.scene.game.config.width;
        const sy = rect.height / this.scene.game.config.height;
        const { px, py } = this.layout();
        const gx = px + 340, gy = py + 68, gw = 330, gh = 40;
        const st = this.nameInput.style;
        st.left = (rect.left + gx * sx) + 'px';
        st.top = (rect.top + gy * sy) + 'px';
        st.width = (gw * sx) + 'px';
        st.height = (gh * sy) + 'px';
        st.fontSize = (20 * sy) + 'px';
    }
}

if (typeof window !== 'undefined') window.CharacterCreator = CharacterCreator;
