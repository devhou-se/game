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
        this.roomPanel = new RoomPanel($('#room-panel'), this.config, k => this.setRoom(k));
        this.layerPanel = new LayerPanel($('#layer-panel'), this.config, this.canvas, () => {});
        this.inspector = new InspectorPanel($('#inspector-panel'), this.config, this.textures);

        // Tool registry: { id, label, onCell(cell,type,button) }. Phase 1 = inspect.
        this.tools = [];
        this.registerTool({
            id: 'inspect', label: 'Inspect',
            onCell: (cell, type) => {
                if (type === 'down') { this.canvas.setSelection(cell); this.inspector.show(this.activeRoom, cell); }
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

    setRoom(key) {
        this.activeRoom = key;
        this.canvas.setSelection(null);
        this.canvas.setQA([]);
        this.canvas.setRoom(key);
        this.roomPanel.render(key);
        this.layerPanel.render(key);
        this.inspector.clear();
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
