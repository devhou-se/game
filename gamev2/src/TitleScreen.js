/**
 * TitleScreen — the game's title / splash screen (issue #9).
 *
 * Shown on every page load once the loader has gone and the world is ready,
 * BEFORE the first-run character creator: the game title over the cast lined
 * up large (their front sprites at 5x, or hand-drawn portraits for anyone
 * listed in assets/portraits/manifest.json), a little hop travelling along
 * the line, and a blinking start prompt.
 *
 * SPACE / ENTER / ESC (so the touch A and B buttons too) or a tap/click
 * anywhere dismisses it and runs the `onStart` callback — GameScene uses that
 * to continue the boot flow. While it is up it owns all input (InputHandler
 * priority 0), so nothing moves or opens underneath.
 *
 * `?notitle=1` skips it (tests / development), and so does the reload of an
 * in-game date change (Time Travel) — see shouldShow().
 */
class TitleScreen {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.objs = [];
        this.timers = [];
        this.onStart = null;
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ enter: K.ENTER, space: K.SPACE, esc: K.ESC });
    }

    /** One-shot sessionStorage flag: skip the title on the next load only. */
    static SKIP_KEY = 'gamev2_skip_title';

    /**
     * False when the page was opened with ?notitle=1, or when this load is an
     * in-game reload (setGameDate / Time Travel sets SKIP_KEY just before it
     * navigates). Consumes the flag, so call it once per boot.
     */
    static shouldShow() {
        let skip = false;
        try {
            skip = sessionStorage.getItem(TitleScreen.SKIP_KEY) === '1';
            sessionStorage.removeItem(TitleScreen.SKIP_KEY);
        } catch (e) { /* storage blocked: just show the title */ }
        if (skip) return false;
        return new URLSearchParams(location.search).get('notitle') !== '1';
    }

    isVisible() { return this.visible; }

    /** Characters in the line-up: the devhouse members (config.members) that have a sprite set. */
    cast() {
        return CharacterSelect.lineup(this.scene.config);
    }

    show(onStart) {
        if (this.visible) return;
        this.onStart = onStart || null;
        const JD = Phaser.Input.Keyboard.JustDown;
        Object.values(this.keys).forEach(k => JD(k)); // swallow stale presses
        this.visible = true;
        this.render();
    }

    /** Take the screen down and hand over to the game. */
    start() {
        if (!this.visible) return;
        this.visible = false;
        this.timers.forEach(t => t.remove());
        this.timers = [];
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        const onStart = this.onStart;
        this.onStart = null;
        if (onStart) onStart();
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        // evaluate all three so none is left "just down" for the next overlay
        const pressed = [JD(k.space), JD(k.enter), JD(k.esc)].some(Boolean);
        if (pressed) this.start();
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const objs = this.objs;
        const DEPTH = 9000; // above the HUD, every overlay and the debug menu
        const add = (o, depth) => { o.setScrollFactor(0); o.setDepth(DEPTH + depth); objs.push(o); return o; };
        const text = (x, y, t, size, family, color) => {
            const o = scene.add.text(x, y, t, { fontSize: size, fill: color, fontFamily: family });
            o.setOrigin(0.5, 0.5); o.setResolution(1);
            return o;
        };

        // backdrop: the loader's colour, so the hand-over from it is seamless.
        // It is the tap target, and swallows clicks meant for the world/HUD.
        const bg = add(scene.add.graphics(), 0);
        bg.fillStyle(0x0a0a12, 1); bg.fillRect(0, 0, W, H);
        bg.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        bg.on('pointerdown', () => this.start());

        // title, with a hard pixel drop shadow
        const title = (scene.config.game && scene.config.game.title) || 'game.devhou.se';
        const size = Math.min(56, Math.floor((W - 160) / title.length));
        add(text(W / 2 + 6, 196, title, `${size}px`, 'PressStart2P', '#1f7a3d'), 1);
        add(text(W / 2, 190, title, `${size}px`, 'PressStart2P', '#ffffff'), 2);

        // the cast, standing on a shared baseline
        const cast = this.cast();
        const n = Math.max(1, cast.length);
        const spacing = Math.min(240, Math.floor((W - 80) / n));
        const scale = Math.max(1, Math.min(5, Math.floor((spacing - 12) / 42))); // body is 42px wide
        const baseY = 650;
        const shadows = add(scene.add.graphics(), 1);
        const figures = cast.map((name, i) => {
            const cx = Math.round(W / 2 + (i - (n - 1) / 2) * spacing);

            // blocky oval shadow under the feet
            shadows.fillStyle(0x000000, 0.55);
            shadows.fillRect(cx - 16 * scale, baseY - scale, 32 * scale, 3 * scale);
            shadows.fillRect(cx - 13 * scale, baseY - 2 * scale, 26 * scale, 5 * scale);

            const portraitKey = `portrait-${name}`;
            let img;
            if (scene.textures.exists(portraitKey)) {
                // hand-drawn art: fitted into a slot the size of the dialogue
                // portrait window (240x200 at the usual 5x), so a portrait
                // shows at the same scale in both places
                img = scene.add.image(cx, baseY, portraitKey);
                const b = DialogueManager.BUST;
                let s = Math.min((b.w * scale) / img.width, (b.h * scale) / img.height);
                if (s > 1) s = Math.floor(s);
                img.setOrigin(0.5, 1);
                img.setScale(s);
            } else {
                const key = `${name}_front`;
                img = scene.add.image(cx, baseY, scene.textures.exists(`${key}_frame_0`) ? `${key}_frame_0` : key);
                // feet are on row 54 of the 64px frame, body centred on column 31
                img.setOrigin(31 / 64, 54 / 64);
                img.setScale(scale);
            }
            img.texture.setFilter(Phaser.Textures.FilterMode.NEAREST);
            add(img, 2);

            add(text(cx, baseY + 40, name.charAt(0).toUpperCase() + name.slice(1),
                '24px', 'PixelOperatorMonoBold', '#bbbbbb'), 2);
            return img;
        });

        // idle: a one-sprite-pixel hop travelling along the line, then a beat
        let tick = 0;
        this.timers.push(scene.time.addEvent({
            delay: 260, loop: true,
            callback: () => {
                const hopper = tick % (figures.length + 3);
                figures.forEach((img, i) => { img.y = baseY - (i === hopper ? scale : 0); });
                tick++;
            },
        }));

        // start prompt, blinking
        const prompt = add(text(W / 2, 800, Hints.touch(scene) ? 'TAP TO START' : 'PRESS SPACE / TAP TO START',
            '28px', 'PixelOperatorMonoBold', '#ffff00'), 2);
        let blink = 0;
        this.timers.push(scene.time.addEvent({
            delay: 275, loop: true,
            callback: () => prompt.setVisible(++blink % 4 !== 0), // 3 beats on, 1 off
        }));
    }
}

if (typeof window !== 'undefined') window.TitleScreen = TitleScreen;
