/**
 * RoomPanel.js — room selector + editable size (in cells). Add/delete room and
 * boundary-polygon editing are deferred (ported rooms already have correct rects).
 */
class RoomPanel {
    constructor(el, config, cb) {
        this.el = el; this.config = config; this.cb = cb; // {onSelect, onResize}
    }
    render(activeRoom) {
        const keys = this.config.roomKeys();
        const opts = keys.map(k => `<option value="${k}" ${k === activeRoom ? 'selected' : ''}>${k}</option>`).join('');
        const s = this.config.roomCells(activeRoom);
        this.el.innerHTML = `
            <h3>Room</h3>
            <select id="rp-select" class="ctl">${opts}</select>
            <div class="row2" style="margin-top:8px">
              <div><label class="lbl">Width (cells)</label><input class="ctl" id="rp-w" type="number" min="1" value="${s.w}"></div>
              <div><label class="lbl">Height (cells)</label><input class="ctl" id="rp-h" type="number" min="1" value="${s.h}"></div>
            </div>`;
        this.el.querySelector('#rp-select').onchange = e => this.cb.onSelect(e.target.value);
        const resize = () => this.cb.onResize(
            Math.max(1, +this.el.querySelector('#rp-w').value),
            Math.max(1, +this.el.querySelector('#rp-h').value));
        this.el.querySelector('#rp-w').onchange = resize;
        this.el.querySelector('#rp-h').onchange = resize;
    }
}
