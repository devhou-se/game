/**
 * DebugManager - in-game debug overlay + issue flagging.
 *
 * Toggle with the backtick key ( ` ). When on:
 *  - a stats panel shows FPS, player cell + depth, camera and current room
 *  - collidable cells are tinted red (the actual collision map)
 *  - clicking any cell lists every tile there (key / layer z / depth / collision)
 *
 * Flagging issues (debug mode only):
 *  - click a cell, then press  N  to add/edit a note for it (it becomes a flag)
 *  - flagged cells are tinted yellow with their note; flags persist across reloads
 *  - press  E  to export ALL flags as a CSV (room, cell, note + full tile dump)
 *  - press  X  to clear all flags
 */
class DebugManager {
    constructor(scene) {
        this.scene = scene;
        this.visible = false;
        this.info = '(click a tile to inspect)';
        this.lastCell = null;                 // {x, y, room, tiles:[...]}
        this.flags = this.loadFlags();        // [{room, x, y, note, tiles:[...]}]

        // World-space overlay (collision tint + flag markers); scrolls with camera
        this.overlay = scene.add.graphics();
        this.overlay.setDepth(4000);

        // Per-flag note labels (world space); rebuilt when flags/room change
        this.flagLabels = [];
        this.labelsDirty = true;

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
        scene.input.keyboard.on('keydown-N', () => { if (this.visible) this.addNote(); });
        scene.input.keyboard.on('keydown-E', () => { if (this.visible) this.exportCSV(); });
        scene.input.keyboard.on('keydown-X', () => { if (this.visible) this.clearFlags(); });
        scene.input.on('pointerdown', (pointer) => {
            if (this.visible) this.inspect(pointer);
        });
    }

    toggle() {
        this.visible = !this.visible;
        this.text.setVisible(this.visible);
        this.labelsDirty = true;
        if (!this.visible) {
            this.overlay.clear();
            this.flagLabels.forEach(l => l.destroy());
            this.flagLabels = [];
        }
    }

    // ---- flag persistence (localStorage so flags survive the frequent reloads) ----
    loadFlags() {
        try { return JSON.parse(localStorage.getItem('gamev2_debug_flags') || '[]'); }
        catch (e) { return []; }
    }
    saveFlags() {
        try { localStorage.setItem('gamev2_debug_flags', JSON.stringify(this.flags)); }
        catch (e) { /* ignore quota/availability */ }
        this.labelsDirty = true;
    }
    findFlag(room, x, y) {
        return this.flags.find(f => f.room === room && f.x === x && f.y === y);
    }

    /** List every tile occupying a cell, formatted like the inspector. */
    tilesAt(gx, gy) {
        const GS = this.scene.GRID_SIZE;
        const names = (this.scene.config && this.scene.config.tileNames) || {};
        const hits = [];
        this.scene.roomManager.floorSprites.forEach(t => {
            const tx = t.getData('gridX'), ty = t.getData('gridY');
            const fw = Math.max(1, Math.round(t.width / GS));
            const fh = Math.max(1, Math.round(t.height / GS));
            if (gx >= tx && gx < tx + fw && gy >= ty && gy < ty + fh) {
                const label = names[t.texture.key] || t.texture.key;
                const anchor = (tx === gx && ty === gy) ? '' : ` (@${tx},${ty})`;
                hits.push(`${label} z${t.getData('layerZ')} d${Math.round(t.depth)}${t.getData('layerCollision') ? ' [COLL]' : ''}${anchor}`);
            }
        });
        return hits;
    }

    /** List every tile occupying the clicked cell + remember it for flagging. */
    inspect(pointer) {
        const GS = this.scene.GRID_SIZE;
        const gx = Math.floor(pointer.worldX / GS);
        const gy = Math.floor(pointer.worldY / GS);
        const room = this.scene.roomManager.currentRoom;
        const hits = this.tilesAt(gx, gy);
        this.lastCell = { x: gx, y: gy, room, tiles: hits };
        const flag = this.findFlag(room, gx, gy);
        const noteLine = flag ? `\n>> NOTE: ${flag.note || '(flagged)'}` : '';
        this.info = `cell (${gx},${gy})\n` + (hits.length ? hits.join('\n') : '(empty)') + noteLine;
        console.log('[debug] cell', gx, gy, hits);
    }

    /** Add/edit a note on the last-inspected cell (turns it into a flag). */
    addNote() {
        if (!this.lastCell) { this.info = 'click a cell first, then press N'; return; }
        const { x, y, room, tiles } = this.lastCell;
        const existing = this.findFlag(room, x, y);
        const note = window.prompt(`Note for ${room} (${x},${y}):`, existing ? existing.note : '');
        if (note === null) return;   // cancelled
        if (existing) { existing.note = note; existing.tiles = tiles; }
        else { this.flags.push({ room, x, y, note, tiles }); }
        this.saveFlags();
        this.info = `flagged (${x},${y}): ${note || '(no note)'}`;
    }

    clearFlags() {
        if (!this.flags.length) return;
        if (!window.confirm(`Clear all ${this.flags.length} flags?`)) return;
        this.flags = [];
        this.saveFlags();
        this.info = 'flags cleared';
    }

    /** Export every flag as CSV and download it. */
    exportCSV() {
        if (!this.flags.length) { this.info = 'no flags to export'; return; }
        const esc = (v) => `"${String(v).replace(/"/g, '""')}"`;
        const rows = [['room', 'x', 'y', 'note', 'tiles'].join(',')];
        this.flags.forEach(f => {
            rows.push([esc(f.room), f.x, f.y, esc(f.note || ''), esc((f.tiles || []).join(' ; '))].join(','));
        });
        const csv = rows.join('\n');
        try {
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `gamev2_debug_flags_${Date.now()}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            this.info = `exported ${this.flags.length} flags to CSV`;
        } catch (e) {
            console.log('[debug] CSV:\n' + csv);
            this.info = 'export failed; CSV dumped to console';
        }
    }

    rebuildLabels() {
        this.flagLabels.forEach(l => l.destroy());
        this.flagLabels = [];
        if (!this.visible) return;
        const GS = this.scene.GRID_SIZE, room = this.scene.roomManager.currentRoom;
        this.flags.filter(f => f.room === room).forEach(f => {
            const label = this.scene.add.text(f.x * GS + 2, f.y * GS - 2, f.note || '(flag)', {
                fontSize: '12px', fill: '#ffff00', fontFamily: 'monospace',
                backgroundColor: 'rgba(0,0,0,0.75)', padding: { x: 2, y: 1 }
            });
            label.setOrigin(0, 1);
            label.setDepth(4002);
            label.setResolution(1);
            this.flagLabels.push(label);
        });
        this.labelsDirty = false;
    }

    update() {
        if (!this.visible) return;
        const s = this.scene, GS = s.GRID_SIZE, cam = s.cameras.main, p = s.player;
        const room = s.roomManager.currentRoom;
        const roomFlags = this.flags.filter(f => f.room === room).length;
        const recent = this.flags.slice(-4).map(f => `  ${f.room} ${f.x},${f.y}: ${f.note || '(flag)'}`).join('\n');
        this.text.setText([
            'DEBUG  ( ` toggle | click = inspect )',
            'N add/edit note   E export CSV   X clear',
            `fps ${Math.round(s.game.loop.actualFps)}   room ${room}`,
            `player ${p.gridX},${p.gridY}  depth ${Math.round(p.sprite.depth)}`,
            `flags ${this.flags.length} total (${roomFlags} here)`,
            '',
            this.info,
            this.flags.length ? '\nrecent flags:\n' + recent : ''
        ].join('\n'));

        if (this.labelsDirty) this.rebuildLabels();

        // Redraw overlay: red = collidable cells, yellow = flagged cells.
        this.overlay.clear();
        const x0 = cam.scrollX, y0 = cam.scrollY, x1 = x0 + cam.width, y1 = y0 + cam.height;
        this.overlay.fillStyle(0xff0000, 0.3);
        this.overlay.lineStyle(1, 0xff0000, 0.5);
        s.roomManager.floorSprites.forEach(t => {
            if (!t.getData('layerCollision')) return;
            const px = t.getData('gridX') * GS, py = t.getData('gridY') * GS;
            if (px < x1 && px + GS > x0 && py < y1 && py + GS > y0) {
                this.overlay.fillRect(px, py, GS, GS);
                this.overlay.strokeRect(px, py, GS, GS);
            }
        });
        this.overlay.fillStyle(0xffff00, 0.35);
        this.overlay.lineStyle(2, 0xffff00, 0.9);
        this.flags.forEach(f => {
            if (f.room !== room) return;
            const px = f.x * GS, py = f.y * GS;
            if (px < x1 && px + GS > x0 && py < y1 && py + GS > y0) {
                this.overlay.fillRect(px, py, GS, GS);
                this.overlay.strokeRect(px, py, GS, GS);
            }
        });
    }
}
