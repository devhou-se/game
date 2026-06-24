/**
 * TouchControls - on-screen d-pad + sprint button for touch / mobile.
 *
 * The game's overlays (dialogue, menu, credits, achievements) and the HUD
 * "menu" button already respond to taps (pointerdown), and NPC interaction
 * happens by walking into them -- so the ONLY thing touch can't do is MOVE.
 * This fills that gap with a DOM overlay (kept out of the Phaser canvas so it's
 * always crisp and reliably hit-testable). It maintains a `state` object that
 * InputHandler folds into movement each frame, exactly like the keyboard.
 *
 * Shown only on touch devices, or when the URL has `?touch=1` (handy for
 * desktop testing). The overlay container is pointer-events:none so taps that
 * miss the buttons still reach the game canvas (dialogue/menu/world).
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

    // Wire a button's press/release (pointer events cover touch + mouse) to a
    // boolean on `state`; release also fires on cancel and on the finger
    // sliding off the button, so a held direction never gets "stuck".
    _bind(btn, key) {
        const idle = 'rgba(20,20,20,0.55)';
        const active = 'rgba(90,90,90,0.85)';
        const set = (v) => (e) => {
            e.preventDefault();
            this.state[key] = v;
            btn.style.background = v ? active : idle;
        };
        btn.addEventListener('pointerdown', set(true));
        btn.addEventListener('pointerup', set(false));
        btn.addEventListener('pointercancel', set(false));
        btn.addEventListener('pointerleave', set(false));
    }

    _btn(label, extra) {
        const b = document.createElement('button');
        b.textContent = label;
        b.style.cssText =
            'position:absolute;pointer-events:auto;border:none;color:#fff;' +
            'background:rgba(20,20,20,0.55);font-family:monospace;' +
            'touch-action:none;-webkit-user-select:none;user-select:none;' +
            '-webkit-tap-highlight-color:transparent;' + extra;
        return b;
    }

    _build() {
        const root = document.createElement('div');
        root.id = 'touch-controls';
        root.style.cssText =
            'position:fixed;inset:0;z-index:10;pointer-events:none;' +
            'touch-action:none;-webkit-user-select:none;user-select:none;';

        // D-pad, bottom-left (multi-touch two buttons for diagonals).
        const pad = document.createElement('div');
        pad.style.cssText =
            'position:absolute;width:174px;height:174px;' +
            'left:max(16px,env(safe-area-inset-left));' +
            'bottom:max(16px,env(safe-area-inset-bottom));';
        const cell = 'width:58px;height:58px;font-size:26px;border-radius:12px;';
        const up = this._btn('▲', cell + 'left:58px;top:0;');
        const left = this._btn('◀', cell + 'left:0;top:58px;');
        const right = this._btn('▶', cell + 'left:116px;top:58px;');
        const down = this._btn('▼', cell + 'left:58px;top:116px;');
        this._bind(up, 'up');
        this._bind(left, 'left');
        this._bind(right, 'right');
        this._bind(down, 'down');
        pad.append(up, left, right, down);

        // Sprint (hold), bottom-right.
        const sprint = this._btn('⏩',
            'width:76px;height:76px;font-size:30px;border-radius:50%;' +
            'right:max(20px,env(safe-area-inset-right));' +
            'bottom:max(32px,env(safe-area-inset-bottom));');
        this._bind(sprint, 'sprint');

        root.append(pad, sprint);
        document.body.appendChild(root);
        this.root = root;
    }
}

if (typeof window !== 'undefined') window.TouchControls = TouchControls;
