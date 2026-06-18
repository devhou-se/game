/**
 * RoomPanel.js — room selector + size readout. (Add/delete/props land in Phase 3.)
 */
class RoomPanel {
    constructor(el, config, onSelect) {
        this.el = el; this.config = config; this.onSelect = onSelect;
    }
    render(activeRoom) {
        const keys = this.config.roomKeys();
        const opts = keys.map(k => `<option value="${k}" ${k === activeRoom ? 'selected' : ''}>${k}</option>`).join('');
        const s = this.config.roomCells(activeRoom);
        this.el.innerHTML = `
            <h3>Room</h3>
            <select id="rp-select" class="ctl">${opts}</select>
            <div class="muted" id="rp-size">${s.w} × ${s.h} cells</div>`;
        this.el.querySelector('#rp-select').onchange = e => this.onSelect(e.target.value);
    }
}
