/**
 * TouchControls - a full on-screen gamepad for touch / mobile.
 *
 * Layout: d-pad bottom-left; bottom-right a cluster of A, the sprint pill
 * under it where the thumb rests (it is the one button that is HELD, and
 * held most of the time you walk), and a small B above it (issue #225).
 * Every button synthesizes REAL keyboard events (keydown on press, keyup
 * on release), so the entire game is playable without a keyboard and
 * without tapping the world:
 *
 *   d-pad  -> WASD         (walk, and navigate every menu/overlay)
 *   A      -> SPACE        (talk/advance, select, buy, strike a fish, board)
 *   B      -> ESC          (close any overlay; opens the menu in the world)
 *   sprint -> SHIFT        (hold to run)
 *
 * Because they're indistinguishable from key presses, every current and
 * future overlay works with no touch-specific code. The `state` object is
 * still maintained for InputHandler's movement fold-in.
 *
 * Shown while touch is the input in USE, not merely available (issue #116):
 *
 *   - a device whose main pointer is a finger (phone, tablet) starts with
 *     them; a touchscreen laptop (main pointer a mouse / trackpad) does not
 *   - the first real touch anywhere shows them; a real press of a game key
 *     hides them again. Hint wording follows (see Hints), live
 *   - `?touch=1` forces them on, whatever is pressed (desktop testing)
 *
 * `enabled` is "the controls are on screen now"; listen for the scene event
 * `'inputmodechange'` to hear it change. The overlay container is
 * pointer-events:none so stray taps still reach the canvas.
 *
 * The controls cost the canvas nothing: Viewport (src/systems/Viewport.js)
 * puts them in the black bars beside or under the canvas when there are
 * any, and otherwise translucent over the canvas's bottom corners, and sets
 * `--tc-scale`, which shrinks the d-pad and the button cluster to fit.
 *
 * A touch on a control belongs to that control alone. Phaser listens for
 * touches on the whole window, not just the canvas, so without `swallowTouch` a tap
 * on A would ALSO reach whatever overlay is under it as a pointer-down (and
 * advance a dialogue twice — issue #49).
 */
class TouchControls {
    constructor(scene) {
        this.scene = scene;
        this.state = { left: false, right: false, up: false, down: false, sprint: false };
        this.forced = /[?&]touch=1/.test(location.search);
        this.enabled = false;
        this.releases = [];   // let go of whatever each control is holding
        this._watch();
        this.setEnabled(this.forced || TouchControls.touchFirst());
    }

    /** Is a finger this device's main pointer (a phone or tablet, not a touchscreen laptop)? */
    static touchFirst() {
        if (!(('ontouchstart' in window) || (navigator.maxTouchPoints > 0))) return false;
        return typeof window.matchMedia !== 'function' || window.matchMedia('(pointer: coarse)').matches;
    }

    /**
     * Follow the input actually in use: a real touch brings the controls up,
     * a real game key takes them away. The controls' own synthetic key
     * events are not trusted, and typing a name (the on-screen keyboard in
     * the character creator's input) is not playing with a keyboard.
     */
    _watch() {
        window.addEventListener('touchstart', () => this.setEnabled(true), { capture: true, passive: true });
        window.addEventListener('keydown', (e) => {
            if (!e.isTrusted || this.forced || !TouchControls.GAME_KEYS.test(e.code || '')) return;
            const t = e.target;
            if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName || ''))) return;
            this.setEnabled(false);
        }, true);
    }

    /** Show or hide the controls; canvas layout and every hint on screen follow. */
    setEnabled(on) {
        on = !!on;
        if (on === this.enabled) return;
        this.enabled = on;
        if (on && !this.root) this._build();
        if (!on) this.releases.forEach(release => release());
        if (this.root) this.root.style.display = on ? '' : 'none';
        // controls beside / under / over the canvas, or the window to itself
        Viewport.apply(this.scene.game);
        Hints.refresh(this.scene);
        // the intro draws its controls page for one input or the other
        const intro = this.scene.intro;
        if (intro && intro.isVisible()) intro.render();
        this.scene.events.emit('inputmodechange', on);
    }

    /**
     * Wire a button: pressed-state styling, optional `state` flag, and a
     * synthetic keyboard key. Release also fires on cancel and on the finger
     * sliding off, so nothing ever sticks held-down.
     */
    _bind(btn, stateKey, keyDef) {
        const fire = (type) => window.dispatchEvent(new KeyboardEvent(type, {
            key: keyDef.key, code: keyDef.code,
            keyCode: keyDef.keyCode, which: keyDef.keyCode, bubbles: true,
        }));
        // a razor-quick tap can land keydown+keyup inside one frame, which
        // isDown-polling consumers (menu toggle, dialogue) would never see —
        // so the synthetic key is held for at least ~90ms (several frames)
        let downAt = 0;
        const set = (v) => (e) => {
            e.preventDefault();
            if (stateKey) this.state[stateKey] = v;
            btn.classList.toggle('tc-pressed', v);
            if (v) {
                downAt = performance.now();
                fire('keydown');
            } else {
                const wait = Math.max(0, 90 - (performance.now() - downAt));
                wait ? setTimeout(() => fire('keyup'), wait) : fire('keyup');
            }
        };
        let held = false;
        const press = set(true), lift = set(false);
        const down = (e) => { held = true; press(e); };
        const up = (e) => { if (held) { held = false; lift(e); } };
        if (this.releases) this.releases.push(() => up({ preventDefault() {} }));
        TouchControls.swallowTouch(btn);
        btn.addEventListener('pointerdown', down);
        btn.addEventListener('pointerup', up);
        btn.addEventListener('pointercancel', up);
        btn.addEventListener('pointerleave', up);
    }

    /**
     * A touch on a control must not also reach the game as a tap. Phaser
     * listens for touchstart on the window and treats one outside the canvas
     * as a pointer-down unless it is defaultPrevented; cancelling pointerdown
     * (as the handlers here do) suppresses the follow-up mouse events but
     * not the touch ones. Without this, A during dialogue advanced a line by
     * key and another by the overlay's tap handler.
     */
    static swallowTouch(el) {
        const swallow = (e) => { if (e.cancelable !== false) e.preventDefault(); };
        for (const type of ['touchstart', 'touchmove', 'touchend', 'touchcancel']) {
            el.addEventListener(type, swallow, { passive: false });
        }
    }

    _btn(label, cls, extra) {
        const b = document.createElement('button');
        b.textContent = label;
        b.className = 'tc-btn ' + cls;
        if (extra) b.style.cssText += extra;
        return b;
    }

    /**
     * The d-pad surface: track one pointer from down through move to up,
     * mapping its position around the pad centre to a held direction set
     * (8 sectors — the four diagonals hold two WASD keys at once). Each
     * change fires the matching synthetic keydown/keyup immediately;
     * movement is isDown-polled so no minimum hold is needed.
     */
    _bindPad(pad, arrows) {
        const KEYDEFS = {
            up: { key: 'w', code: 'KeyW', keyCode: 87 },
            down: { key: 's', code: 'KeyS', keyCode: 83 },
            left: { key: 'a', code: 'KeyA', keyCode: 65 },
            right: { key: 'd', code: 'KeyD', keyCode: 68 },
        };
        const fire = (type, d) => window.dispatchEvent(new KeyboardEvent(type, {
            key: KEYDEFS[d].key, code: KEYDEFS[d].code,
            keyCode: KEYDEFS[d].keyCode, which: KEYDEFS[d].keyCode, bubbles: true,
        }));

        let active = new Set();
        let pointerId = null;

        const apply = (next) => {
            for (const d of ['up', 'down', 'left', 'right']) {
                const was = active.has(d), is = next.has(d);
                if (is === was) continue;
                this.state[d] = is;
                arrows[d].classList.toggle('tc-pressed', is);
                fire(is ? 'keydown' : 'keyup', d);
            }
            active = next;
        };

        const dirsAt = (e) => {
            const r = pad.getBoundingClientRect();
            const dx = e.clientX - (r.left + r.width / 2);
            const dy = e.clientY - (r.top + r.height / 2);
            if (Math.hypot(dx, dy) < r.width * 0.09) return new Set();   // centre dead zone (16px at full size)
            const a = Math.atan2(dy, dx) * 180 / Math.PI;    // 0° = east
            const s = new Set();
            if (a > -67.5 && a < 67.5) s.add('right');
            if (a > 112.5 || a < -112.5) s.add('left');
            if (a > 22.5 && a < 157.5) s.add('down');
            if (a < -22.5 && a > -157.5) s.add('up');
            return s;
        };

        TouchControls.swallowTouch(pad);
        pad.addEventListener('pointerdown', (e) => {
            e.preventDefault();
            if (pointerId !== null) return;
            pointerId = e.pointerId;
            try { pad.setPointerCapture(e.pointerId); } catch (err) { /* synthetic pointers */ }
            apply(dirsAt(e));
        });
        pad.addEventListener('pointermove', (e) => {
            if (e.pointerId !== pointerId) return;
            apply(dirsAt(e));
        });
        const end = (e) => {
            if (e.pointerId !== pointerId) return;
            pointerId = null;
            apply(new Set());
        };
        pad.addEventListener('pointerup', end);
        pad.addEventListener('pointercancel', end);
        this.releases.push(() => { pointerId = null; apply(new Set()); });
    }

    _build() {
        const style = document.createElement('style');
        style.textContent = `
            #touch-controls { position:fixed; inset:0; z-index:10; pointer-events:none;
                touch-action:none; -webkit-user-select:none; user-select:none; }
            #touch-controls .tc-btn { position:absolute; pointer-events:auto;
                display:flex; align-items:center; justify-content:center;
                color:rgba(255,255,255,0.92);
                background:rgba(12,12,18,0.48);
                border:1.5px solid rgba(255,255,255,0.22);
                box-shadow:0 2px 8px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.10);
                font-family:monospace; touch-action:none;
                -webkit-user-select:none; user-select:none;
                -webkit-tap-highlight-color:transparent;
                transition:transform 70ms ease, background 70ms ease; }
            #touch-controls .tc-pressed { background:rgba(120,124,150,0.85);
                transform:scale(0.92); }
            #touch-controls .tc-pad { width:58px; height:58px; font-size:24px;
                border-radius:12px; }
            #touch-controls .tc-padzone { position:absolute; width:174px; height:174px;
                pointer-events:auto; touch-action:none; border-radius:24px;
                background:rgba(12,12,18,0.22);
                transform:scale(var(--tc-scale,1)); transform-origin:left bottom;
                -webkit-tap-highlight-color:transparent; }
            #touch-controls .tc-cluster { position:absolute;
                width:${Viewport.CONTROLS.clusterW}px; height:${Viewport.CONTROLS.clusterH}px;
                transform:scale(var(--tc-scale,1)); transform-origin:right bottom; }
            #touch-controls .tc-a { border-radius:50%;
                font-size:30px; font-weight:bold;
                border-color:rgba(255,215,0,0.55); color:#ffd700; }
            #touch-controls .tc-b { border-radius:50%;
                font-size:20px; font-weight:bold;
                border-color:rgba(255,120,120,0.5); color:#ff9c9c; }
            #touch-controls .tc-sprint { border-radius:${TouchControls.CLUSTER.sprint.h / 2}px;
                font-size:44px; line-height:1; padding:0 0 4px; }
            /* no energy, no sprint (Shop.updateEffectChip sets it on the root) */
            #touch-controls.tc-nosprint .tc-sprint { opacity:0.35; border-style:dashed; }
        `;
        document.head.appendChild(style);

        const root = document.createElement('div');
        root.id = 'touch-controls';

        // D-pad, bottom-left: ONE touch surface, not four buttons. The thumb
        // is tracked continuously (pointer capture), so direction changes
        // without lifting, and the corners between two arrows hold both keys
        // — a diagonal. The arrows are just visuals that light up.
        const pad = document.createElement('div');
        pad.className = 'tc-padzone';
        pad.style.cssText =
            'left:max(16px,env(safe-area-inset-left));' +
            'bottom:max(16px,env(safe-area-inset-bottom));';
        const arrows = {
            up: this._btn('▲', 'tc-pad', 'left:58px;top:0;'),
            left: this._btn('◀', 'tc-pad', 'left:0;top:58px;'),
            right: this._btn('▶', 'tc-pad', 'left:116px;top:58px;'),
            down: this._btn('▼', 'tc-pad', 'left:58px;top:116px;'),
        };
        Object.values(arrows).forEach(b => { b.style.pointerEvents = 'none'; pad.appendChild(b); });
        this._bindPad(pad, arrows);

        // A / sprint / B cluster, bottom-right: A above-right and the sprint
        // pill below-left of it (hold to run), the two a thumb in the corner
        // reaches without stretching; B small, above A. One box, so the three
        // scale together about the corner they sit in.
        const cluster = document.createElement('div');
        cluster.className = 'tc-cluster';
        cluster.style.cssText =
            'right:max(20px,env(safe-area-inset-right));' +
            'bottom:max(16px,env(safe-area-inset-bottom));';
        const at = (k) => `width:${k.w}px;height:${k.h}px;right:${k.right}px;bottom:${k.bottom}px;`;
        const a = this._btn('A', 'tc-a', at(TouchControls.CLUSTER.a));
        const b = this._btn('B', 'tc-b', at(TouchControls.CLUSTER.b));
        this._bind(a, null, { key: ' ', code: 'Space', keyCode: 32 });
        this._bind(b, null, { key: 'Escape', code: 'Escape', keyCode: 27 });
        const sprint = this._btn('»', 'tc-sprint', at(TouchControls.CLUSTER.sprint));
        this._bind(sprint, 'sprint', { key: 'Shift', code: 'ShiftLeft', keyCode: 16 });
        cluster.append(a, b, sprint);

        root.append(pad, cluster);
        document.body.appendChild(root);
        this.root = root;
    }
}

/**
 * Where the three buttons sit in their cluster at scale 1: size, and distance
 * from the cluster box's right and bottom edges, in CSS px. The box itself is
 * Viewport.CONTROLS (clusterW x clusterH), which the canvas is laid out around.
 * Sprint is held, so it is the big one on the bottom row; B is tapped now and
 * then, so it is the small one furthest from the corner (issue #225).
 */
TouchControls.CLUSTER = {
    a: { w: 76, h: 76, right: 0, bottom: 70 },
    sprint: { w: 90, h: 60, right: 60, bottom: 0 },
    b: { w: 52, h: 52, right: 12, bottom: 158 },
};

/** Trusted presses of these mean a keyboard is in use (KeyboardEvent.code). */
TouchControls.GAME_KEYS = /^(Key[WASD]|Arrow(Up|Down|Left|Right)|Space|Enter|NumpadEnter|Escape|Shift(Left|Right))$/;

if (typeof window !== 'undefined') window.TouchControls = TouchControls;
