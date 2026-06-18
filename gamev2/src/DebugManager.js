/**
 * DebugManager - in-game debug overlay.
 *
 * Toggle with the backtick key ( ` ). When on:
 *  - a stats panel shows FPS, player cell + depth, camera and current room
 *  - collidable cells are tinted red (the actual collision map)
 *  - clicking any cell lists every tile there (key / layer z / depth / collision)
 */
class DebugManager {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.info = '(click a tile to inspect)';

        // World-space collision overlay (scrolls with the camera)
        this.overlay = scene.add.graphics();
        this.overlay.setDepth(4000);

        // Screen-space stats panel (fixed to camera)
        this.text = scene.add.text(8, 48, '', {
            fontSize: '14px',
            fill: '#00ff66',
            fontFamily: 'monospace',
            backgroundColor: 'rgba(0,0,0,0.7)',
            padding: { x: 6, y: 6 }
        });
        this.text.setScrollFactor(0);
        this.text.setDepth(4001);
        this.text.setResolution(1);
        this.text.setVisible(false);

        scene.input.keyboard.on('keydown-BACKTICK', () => this.toggle());
        scene.input.on('pointerdown', (pointer) => {
            if (this.visible) this.inspect(pointer);
        });
    }

    toggle() {
        this.visible = !this.visible;
        this.text.setVisible(this.visible);
        if (!this.visible) this.overlay.clear();
    }

    /** List every tile occupying the clicked cell. */
    inspect(pointer) {
        const GS = this.scene.GRID_SIZE;
        const gx = Math.floor(pointer.worldX / GS);
        const gy = Math.floor(pointer.worldY / GS);
        const names = (this.scene.config && this.scene.config.tileNames) || {};
        const hits = [];
        this.scene.roomManager.floorSprites.forEach(t => {
            const tx = t.getData('gridX'), ty = t.getData('gridY');
            const fw = Math.max(1, Math.round(t.width / GS));
            const fh = Math.max(1, Math.round(t.height / GS));
            if (gx >= tx && gx < tx + fw && gy >= ty && gy < ty + fh) {
                const label = names[t.texture.key] || t.texture.key;
                const anchor = (tx === gx && ty === gy) ? '' : ` (@${tx},${ty})`;
                hits.push(`${label}  z${t.getData('layerZ')} d${Math.round(t.depth)}${t.getData('layerCollision') ? ' [COLL]' : ''}${anchor}`);
            }
        });
        this.info = `cell (${gx},${gy})\n` + (hits.length ? hits.join('\n') : '(empty)');
        console.log('[debug] cell', gx, gy, hits);
    }

    update() {
        if (!this.visible) return;
        const s = this.scene, GS = s.GRID_SIZE, cam = s.cameras.main, p = s.player;
        this.text.setText([
            'DEBUG  ( ` toggle | click = inspect )',
            `fps    ${Math.round(s.game.loop.actualFps)}`,
            `player ${p.gridX},${p.gridY}  depth ${Math.round(p.sprite.depth)}`,
            `cam    ${Math.round(cam.scrollX)},${Math.round(cam.scrollY)}`,
            `room   ${s.roomManager.currentRoom}`,
            '',
            this.info
        ].join('\n'));

        // Redraw collidable cells visible on screen.
        this.overlay.clear();
        this.overlay.fillStyle(0xff0000, 0.3);
        this.overlay.lineStyle(1, 0xff0000, 0.5);
        const x0 = cam.scrollX, y0 = cam.scrollY, x1 = x0 + cam.width, y1 = y0 + cam.height;
        s.roomManager.floorSprites.forEach(t => {
            if (!t.getData('layerCollision')) return;
            const px = t.getData('gridX') * GS, py = t.getData('gridY') * GS;
            if (px < x1 && px + GS > x0 && py < y1 && py + GS > y0) {
                this.overlay.fillRect(px, py, GS, GS);
                this.overlay.strokeRect(px, py, GS, GS);
            }
        });
    }
}
