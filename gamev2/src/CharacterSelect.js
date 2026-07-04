/**
 * CharacterSelect — pick who you play as (issue #15).
 *
 * Swaps the player between the existing character sprite sets (james,
 * bailey, damian, dylan, julia — anything in spriteMetadata with _front,
 * _back and _side variants). The choice persists in localStorage, and
 * CharacterSelect.applySaved patches config.player before the sprite
 * system boots so a returning player wakes up as their character.
 *
 * Full mix-and-match customisation (hair/clothing) needs sprite sheets
 * that don't exist yet — this is the with-today's-assets version.
 */
class CharacterSelect {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.objs = [];
        this.rows = [];
        this.selected = 0;
        const K = Phaser.Input.Keyboard.KeyCodes;
        this.keys = scene.input.keyboard.addKeys({ up: K.UP, down: K.DOWN, enter: K.ENTER, esc: K.ESC });
        this.chars = CharacterSelect.available(scene.config);
    }

    /** Character base names with a full front/back/side sprite set. */
    static available(config) {
        const sm = config.spriteMetadata || {};
        return Object.keys(sm)
            .filter(k => k.endsWith('_front'))
            .map(k => k.slice(0, -'_front'.length))
            .filter(n => sm[`${n}_back`] && sm[`${n}_side`])
            .sort((a, b) => (a === 'james' ? -1 : b === 'james' ? 1 : a.localeCompare(b)));
    }

    /** Patch config.player to the saved character. Call before SpriteSystem boots. */
    static applySaved(config) {
        let name = null;
        try { name = localStorage.getItem('gamev2_character'); } catch (e) { /* no storage */ }
        if (!name || !CharacterSelect.available(config).includes(name)) return;
        config.player.sprite = `${name}_front`;
        config.player.directionalSprites = {
            down: `${name}_front`, up: `${name}_back`, right: `${name}_side`, left: '',
        };
        config.player.autoFlip = { horizontal: true, vertical: false };
    }

    isVisible() { return this.visible; }

    show() {
        if (this.visible) return;
        this.selected = Math.max(0, this.chars.indexOf(this.currentName()));
        const JD = Phaser.Input.Keyboard.JustDown;
        JD(this.keys.enter); JD(this.keys.esc);
        this.visible = true;
        this.render();
    }

    hide() {
        this.visible = false;
        this.objs.forEach(o => o.destroy());
        this.objs = [];
        this.rows = [];
    }

    currentName() {
        return this.scene.player.baseSpriteKey.replace(/_front$/, '');
    }

    /** Become the selected character: persist, and swap the live sprite. */
    confirm() {
        const name = this.chars[this.selected];
        this.hide();
        if (!name || name === this.currentName()) return;
        try { localStorage.setItem('gamev2_character', name); } catch (e) { /* play on */ }

        const scene = this.scene, key = `${name}_front`;
        // keep spriteMetadata directional for the new base key (idempotent —
        // the NPC casts of these sprites already set the same mapping)
        const meta = scene.spriteSystem.spriteMetadata[key];
        if (meta) {
            meta.isDirectional = true;
            meta.directions = { down: key, up: `${name}_back`, right: `${name}_side`, left: '' };
            meta.autoFlip = { horizontal: true, vertical: false };
        }

        const p = scene.player;
        p.baseSpriteKey = key;
        p.isDirectional = true;
        p.currentDirection = 'none';        // force the texture swap below
        p.updateDirectionSprite(0, 1);      // face the camera as the new character

        // you can't meet yourself: despawn the new character's NPC and bring
        // back the one you stopped being
        scene.syncNpcPresence();
    }

    handleInput() {
        const JD = Phaser.Input.Keyboard.JustDown, k = this.keys;
        if (JD(k.esc)) return this.hide();
        if (JD(k.enter)) return this.confirm();
        if (JD(k.up)) { this.selected = (this.selected - 1 + this.chars.length) % this.chars.length; this.paint(); }
        if (JD(k.down)) { this.selected = (this.selected + 1) % this.chars.length; this.paint(); }
    }

    paint() {
        this.rows.forEach((r, i) => r.setFill(i === this.selected ? '#ffff00' : '#ffffff'));
        if (this.preview) {
            const key = `${this.chars[this.selected]}_front`;
            const tex = this.scene.textures.exists(`${key}_frame_0`) ? `${key}_frame_0` : key;
            this.preview.setTexture(tex);
        }
    }

    render() {
        const scene = this.scene, cam = scene.cameras.main, W = cam.width, H = cam.height;
        const pw = 420, ph = 200 + this.chars.length * 40;
        const px = (W - pw) / 2, py = (H - ph) / 2;
        const objs = this.objs;

        const overlay = scene.add.graphics();
        overlay.fillStyle(0x000000, 0.75); overlay.fillRect(0, 0, W, H);
        overlay.setScrollFactor(0); overlay.setDepth(2000);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, W, H), Phaser.Geom.Rectangle.Contains);
        overlay.on('pointerdown', () => this.hide());
        objs.push(overlay);

        const panel = scene.add.graphics();
        panel.fillStyle(0x1a1a1a, 1); panel.fillRect(px, py, pw, ph);
        panel.lineStyle(2, 0x666666, 1); panel.strokeRect(px, py, pw, ph);
        panel.setScrollFactor(0); panel.setDepth(2001);
        panel.setInteractive(new Phaser.Geom.Rectangle(px, py, pw, ph), Phaser.Geom.Rectangle.Contains);
        objs.push(panel);

        const text = (x, y, t, size, bold, color) => {
            const o = scene.add.text(x, y, t, { fontSize: size, fill: color || '#ffffff',
                fontFamily: bold ? 'PixelOperatorMonoBold' : 'PixelOperatorMono' });
            o.setOrigin(0.5, 0.5); o.setResolution(1);
            o.setScrollFactor(0); o.setDepth(2002); objs.push(o); return o;
        };
        text(W / 2, py + 32, 'CHARACTER', '26px', true);

        // live preview of the selected character, front-facing at 2x
        this.preview = scene.add.image(W / 2, py + 92, 'tile');
        this.preview.setScale(2); this.preview.setScrollFactor(0); this.preview.setDepth(2002);
        objs.push(this.preview);

        this.rows = this.chars.map((name, i) => {
            const current = name === this.currentName() ? '  (you)' : '';
            const label = name.charAt(0).toUpperCase() + name.slice(1) + current;
            const row = text(W / 2, py + 160 + i * 40, label, '20px', true);
            row.setInteractive({ useHandCursor: true });
            row.on('pointerover', () => { this.selected = i; this.paint(); });
            row.on('pointerdown', () => { this.selected = i; this.confirm(); });
            return row;
        });
        this.paint();
        text(W / 2, py + ph - 24, '↑/↓ + ENTER: become · ESC: stay yourself', '12px', false, '#888888');
    }
}

if (typeof window !== 'undefined') window.CharacterSelect = CharacterSelect;
