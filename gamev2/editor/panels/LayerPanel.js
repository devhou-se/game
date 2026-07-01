/**
 * LayerPanel.js — per-layer visibility + active-layer selection, plus the
 * collision-overlay and grid toggles. Active layer is where Paint/Erase act.
 */
class LayerPanel {
    constructor(el, config, canvas, onActiveLayer) {
        this.el = el; this.config = config; this.canvas = canvas;
        this.onActiveLayer = onActiveLayer;
        this.activeLayer = null;
    }
    render(roomKey) {
        const layers = this.config.room(roomKey).layers;
        if (!this.activeLayer || !layers.find(L => L.name === this.activeLayer)) {
            const firstPaintable = layers.find(L => !L.collision);
            this.activeLayer = firstPaintable ? firstPaintable.name : layers[0].name;
        }
        const rows = layers.map(L => {
            const vis = this.canvas.layerVisible[L.name] !== false;
            const isColl = L.collision;
            return `<div class="layer-row ${L.name === this.activeLayer ? 'active' : ''}" data-layer="${L.name}">
                <input type="checkbox" class="lp-vis" data-layer="${L.name}" ${vis ? 'checked' : ''} title="visible">
                <span class="lp-name">${L.name}</span>
                <span class="lp-z">z${L.z}${isColl ? ' ⛔' : ''}</span>
            </div>`;
        }).join('');
        this.el.innerHTML = `
            <h3>Layers</h3>
            <div class="layer-list">${rows}</div>
            <label class="chk"><input type="checkbox" id="lp-coll" ${this.canvas.showCollision ? 'checked' : ''}> Collision overlay</label>
            <label class="chk"><input type="checkbox" id="lp-grid" ${this.canvas.showGrid ? 'checked' : ''}> Grid</label>`;

        this.el.querySelectorAll('.lp-vis').forEach(cb => cb.onchange = e => {
            e.stopPropagation();
            this.canvas.setLayerVisible(e.target.dataset.layer, e.target.checked);
        });
        this.el.querySelectorAll('.layer-row').forEach(row => row.onclick = () => {
            this.activeLayer = row.dataset.layer;
            this.render(roomKey);
            if (this.onActiveLayer) this.onActiveLayer(this.activeLayer);
        });
        this.el.querySelector('#lp-coll').onchange = e => this.canvas.setShowCollision(e.target.checked);
        this.el.querySelector('#lp-grid').onchange = e => this.canvas.setShowGrid(e.target.checked);
    }
}
