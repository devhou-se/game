/**
 * InspectorPanel.js — click a cell to list every tile there, same readout as the
 * in-game DebugManager.inspect: "<name>  z<z> d<depth> [COLL] (@ax,ay)".
 */
class InspectorPanel {
    constructor(el, config, textures) {
        this.el = el; this.config = config; this.textures = textures;
    }
    show(roomKey, cell) {
        const hits = this.config.tilesAt(roomKey, cell.x, cell.y, this.textures);
        const rows = hits.length ? hits.map(h => {
            const anchor = (h.tx === cell.x && h.ty === cell.y) ? '' : ` (@${h.tx},${h.ty})`;
            return `<div class="insp-row${h.collision ? ' coll' : ''}">
                <span class="insp-name">${h.name}</span>
                <span class="insp-meta">z${h.layer.z} d${Math.round(h.depth)}${h.collision ? ' [COLL]' : ''}${anchor}</span>
            </div>`;
        }).join('') : `<div class="muted">(empty)</div>`;
        const p = this.config.data.player;
        const isSpawn = p.startRoom === roomKey && p.startX === cell.x && p.startY === cell.y;
        this.el.innerHTML = `
            <h3>Inspect</h3>
            <div class="insp-cell">cell (${cell.x}, ${cell.y})${isSpawn ? '  ★spawn' : ''}</div>
            ${rows}`;
    }
    clear() {
        this.el.innerHTML = `<h3>Inspect</h3><div class="muted">click a cell</div>`;
    }
}
