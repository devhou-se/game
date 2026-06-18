/**
 * app.js — editor bootstrap. Loads config + textures, wires the canvas + panels,
 * and routes cell events to the active tool. Tools are registered in this.tools
 * so later phases (collision, transporters, QA, painting) just add entries.
 */
const $ = sel => document.querySelector(sel);

class EditorApp {
    async init() {
        this.config = new Config();
        await this.config.load();
        this.textures = new Textures();
        await this.textures.loadForConfig(this.config);
        if (this.textures.missing.length) {
            console.warn('Missing tile PNGs:', this.textures.missing.slice(0, 10),
                this.textures.missing.length > 10 ? `(+${this.textures.missing.length - 10})` : '');
        }

        this.canvas = new RoomCanvas($('#canvas'), this.config, this.textures);
        this.roomPanel = new RoomPanel($('#room-panel'), this.config, {
            onSelect: k => this.setRoom(k),
            onResize: (w, h) => this._resizeRoom(w, h),
        });
        this.layerPanel = new LayerPanel($('#layer-panel'), this.config, this.canvas, () => {});
        this.inspector = new InspectorPanel($('#inspector-panel'), this.config, this.textures);
        this.props = new PropertiesPanel($('#properties-panel'), this.config, {
            onChange: () => { this.config.markDirty(); this.canvas.render(); this._status(); },
            onDelete: idx => this._deleteTransporter(idx),
        });

        // Tool registry: { id, label, onCell(cell,type,button) }. Phase 1 = inspect.
        this.tools = [];
        this.registerTool({
            id: 'inspect', label: 'Inspect',
            onCell: (cell, type) => {
                if (type === 'down') { this.canvas.setSelection(cell); this.inspector.show(this.activeRoom, cell); }
            },
        });
        // Collision: paint gk_blank on the Colliders layer (left = solid, right = erase).
        this.registerTool({
            id: 'collision', label: 'Collision', paints: true,
            onSelect: () => { this.canvas.setShowCollision(true); this.layerPanel.render(this.activeRoom); },
            onCell: (cell, type, btn) => {
                if (type !== 'down' && type !== 'drag') return;
                const col = this._ensureColliders();
                const k = `${cell.x},${cell.y}`;
                if (btn === 2) delete col.tiles[k]; else col.tiles[k] = 'gk_blank';
                this.config.markDirty();
                this.canvas.render();
                this.inspector.show(this.activeRoom, cell);
                this._status(cell);
            },
        });
        // Transporter: click to place (targets the first other room); click an existing one to edit.
        this.registerTool({
            id: 'transporter', label: 'Transporter',
            onCell: (cell, type) => {
                if (type !== 'down') return;
                const trs = this.config.room(this.activeRoom).transporters;
                let idx = trs.findIndex(t => t.gridX === cell.x && t.gridY === cell.y);
                if (idx < 0) {
                    const other = this.config.roomKeys().find(r => r !== this.activeRoom) || this.activeRoom;
                    const tc = this.config.roomCells(other);
                    trs.push({ gridX: cell.x, gridY: cell.y, targetRoom: other,
                               targetX: Math.floor(tc.w / 2), targetY: Math.floor(tc.h / 2), hidden: false });
                    idx = trs.length - 1; this.config.markDirty();
                }
                this.canvas.setSelection(cell); this.canvas.render();
                this.props.showTransporter(this.activeRoom, idx);
                this._status(cell);
            },
        });
        // Spawn: set the player start (and start room) to the clicked cell.
        this.registerTool({
            id: 'spawn', label: 'Spawn',
            onCell: (cell, type) => {
                if (type !== 'down') return;
                const p = this.config.data.player;
                p.startRoom = this.activeRoom; p.startX = cell.x; p.startY = cell.y;
                this.config.markDirty(); this.canvas.setSelection(cell); this.canvas.render();
                this.inspector.show(this.activeRoom, cell); this._status(cell);
            },
        });
        this.tool = 'inspect';

        this.canvas.onCell = (cell, type, btn) => this._onCell(cell, type, btn);
        this._wireChrome();
        this.canvas.resize();

        this.activeRoom = this.config.data.player.startRoom || this.config.roomKeys()[0];
        this.setRoom(this.activeRoom);
        this.inspector.clear();
        this._renderToolbar();
        this._status();
    }

    registerTool(t) { this.tools.push(t); }
    currentTool() { return this.tools.find(t => t.id === this.tool); }
    /** Paint tools claim left-drag to paint; everything else left-drags to pan. */
    _applyDragMode() { this.canvas.dragMode = (this.currentTool() && this.currentTool().paints) ? 'paint' : 'pan'; }

    /** The room's dedicated collision layer, created if missing. */
    _ensureColliders() {
        let c = this.config.colliders(this.activeRoom);
        if (!c) { c = { name: 'Colliders', z: 5, collision: true, tiles: {} };
                  this.config.room(this.activeRoom).layers.push(c); }
        return c;
    }

    _resizeRoom(wCells, hCells) {
        const GS = this.config.gridSize, r = this.config.room(this.activeRoom);
        r.worldWidth = wCells * GS; r.worldHeight = hCells * GS;
        r.boundary = [[0, 0], [wCells, 0], [wCells, hCells], [0, hCells]];
        this.config.markDirty();
        this.canvas.fitView();
        this.roomPanel.render(this.activeRoom);
        this._status();
    }

    _deleteTransporter(idx) {
        this.config.room(this.activeRoom).transporters.splice(idx, 1);
        this.config.markDirty();
        this.canvas.setSelection(null); this.canvas.render();
        this.props.clear(); this._status();
    }

    setRoom(key) {
        this.activeRoom = key;
        this.canvas.setSelection(null);
        this.canvas.setQA([]);
        this.canvas.setRoom(key);
        this.roomPanel.render(key);
        this.layerPanel.render(key);
        this.inspector.clear();
        if (this.props) this.props.clear();
        this._status();
    }

    _onCell(cell, type, btn) {
        if (type === 'move') { this._status(cell); return; }
        const t = this.currentTool();
        if (t && t.onCell) t.onCell(cell, type, btn);
    }

    _wireChrome() {
        $('#btn-save').onclick = () => this.config.save();
        $('#btn-reload').onclick = () => location.reload();
        $('#btn-fit').onclick = () => this.canvas.fitView();
    }

    _renderToolbar() {
        const bar = $('#toolbar-tools');
        bar.innerHTML = this.tools.map(t =>
            `<button class="tool-btn ${t.id === this.tool ? 'active' : ''}" data-tool="${t.id}">${t.label}</button>`).join('');
        bar.querySelectorAll('.tool-btn').forEach(b => b.onclick = () => {
            this.tool = b.dataset.tool;
            const t = this.currentTool();
            if (t && t.onSelect) t.onSelect();
            this._applyDragMode();
            this._renderToolbar();
        });
    }

    _status(cell) {
        $('#status').textContent =
            `${this.activeRoom}   |   ${cell ? `cell ${cell.x},${cell.y}` : '—'}   |   zoom ${Math.round(this.canvas.cam.zoom * 100)}%` +
            (this.config.dirty ? '   |   ● unsaved' : '');
    }
}

window.addEventListener('DOMContentLoaded', () => {
    window.editor = new EditorApp();
    window.editor.init().catch(e => {
        console.error(e);
        document.body.insertAdjacentHTML('beforeend',
            `<div style="position:fixed;inset:0;display:flex;align-items:center;justify-content:center;color:#f55;font:14px monospace;background:#111">Editor failed to load: ${e.message}<br>(serve via http, open /editor/)</div>`);
    });
});
