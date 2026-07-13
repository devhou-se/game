/**
 * TouchControls - a full on-screen gamepad for touch / mobile.
 *
 * Layout: d-pad bottom-left; A / B buttons bottom-right with a sprint pill
 * above them. Every button synthesizes REAL keyboard events (keydown on
 * press, keyup on release), so the entire game is playable without a
 * keyboard and without tapping the world:
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
 * Shown only on touch devices, or with `?touch=1` for desktop testing. The
 * overlay container is pointer-events:none so stray taps still reach the
 * canvas.
 */
class TouchControls {
    constructor(scene) {
        this.scene = scene;
        this.state = { left: false, right: false, up: false, down: false, sprint: false };
        this.enabled = this._isTouch() || /[?&]touch=1/.test(location.search);
        if (this.enabled) this._build();
    }

    _isTouch() {
        return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
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
        btn.addEventListener('pointerdown', set(true));
        btn.addEventListener('pointerup', set(false));
        btn.addEventListener('pointercancel', set(false));
        btn.addEventListener('pointerleave', set(false));
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
            if (Math.hypot(dx, dy) < 16) return new Set();   // centre dead zone
            const a = Math.atan2(dy, dx) * 180 / Math.PI;    // 0° = east
            const s = new Set();
            if (a > -67.5 && a < 67.5) s.add('right');
            if (a > 112.5 || a < -112.5) s.add('left');
            if (a > 22.5 && a < 157.5) s.add('down');
            if (a < -22.5 && a > -157.5) s.add('up');
            return s;
        };

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
                -webkit-tap-highlight-color:transparent; }
            #touch-controls .tc-a { width:76px; height:76px; border-radius:50%;
                font-size:30px; font-weight:bold;
                border-color:rgba(255,215,0,0.55); color:#ffd700; }
            #touch-controls .tc-b { width:62px; height:62px; border-radius:50%;
                font-size:24px; font-weight:bold;
                border-color:rgba(255,120,120,0.5); color:#ff9c9c; }
            #touch-controls .tc-sprint { width:64px; height:42px;
                border-radius:21px; font-size:20px; }
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

        // A / B cluster, bottom-right (A above-right, B below-left, GB-style)
        const a = this._btn('A', 'tc-a',
            'right:max(20px,env(safe-area-inset-right));bottom:calc(max(16px,env(safe-area-inset-bottom)) + 74px);');
        const b = this._btn('B', 'tc-b',
            'right:calc(max(20px,env(safe-area-inset-right)) + 88px);bottom:max(16px,env(safe-area-inset-bottom));');
        this._bind(a, null, { key: ' ', code: 'Space', keyCode: 32 });
        this._bind(b, null, { key: 'Escape', code: 'Escape', keyCode: 27 });

        // sprint pill above the cluster (hold to run)
        const sprint = this._btn('»', 'tc-sprint',
            'right:max(20px,env(safe-area-inset-right));bottom:calc(max(16px,env(safe-area-inset-bottom)) + 168px);');
        this._bind(sprint, 'sprint', { key: 'Shift', code: 'ShiftLeft', keyCode: 16 });

        root.append(pad, a, b, sprint);
        document.body.appendChild(root);
        this.root = root;
    }
}

if (typeof window !== 'undefined') window.TouchControls = TouchControls;
