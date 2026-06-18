/**
 * PropertiesPanel.js — context editor for the selected thing. Phase 3: transporters
 * (target room/cell, hidden flag, delete). Lives in the right sidebar under Inspect.
 */
class PropertiesPanel {
    constructor(el, config, callbacks) {
        this.el = el; this.config = config; this.cb = callbacks; // {onChange, onDelete}
    }
    clear() {
        this.el.innerHTML = `<h3>Properties</h3><div class="muted">Transporter tool: click to place; click an existing one to edit.</div>`;
    }
    showTransporter(roomKey, idx) {
        const t = this.config.room(roomKey).transporters[idx];
        if (!t) return this.clear();
        const opts = this.config.roomKeys()
            .map(r => `<option value="${r}" ${r === t.targetRoom ? 'selected' : ''}>${r}</option>`).join('');
        this.el.innerHTML = `
            <h3>Transporter</h3>
            <div class="muted">at ${t.gridX}, ${t.gridY}</div>
            <label class="lbl">Target room</label>
            <select class="ctl" id="pp-room">${opts}</select>
            <div class="row2">
              <div><label class="lbl">Target X</label><input class="ctl" id="pp-tx" type="number" value="${t.targetX}"></div>
              <div><label class="lbl">Target Y</label><input class="ctl" id="pp-ty" type="number" value="${t.targetY}"></div>
            </div>
            <label class="chk"><input type="checkbox" id="pp-hidden" ${t.hidden ? 'checked' : ''}> Hidden (no tile / label)</label>
            <button class="btn btn-danger" id="pp-del">Delete transporter</button>`;
        const upd = () => {
            t.targetRoom = this.el.querySelector('#pp-room').value;
            t.targetX = +this.el.querySelector('#pp-tx').value;
            t.targetY = +this.el.querySelector('#pp-ty').value;
            t.hidden = this.el.querySelector('#pp-hidden').checked;
            this.cb.onChange();
        };
        this.el.querySelector('#pp-room').onchange = upd;
        this.el.querySelector('#pp-tx').oninput = upd;
        this.el.querySelector('#pp-ty').oninput = upd;
        this.el.querySelector('#pp-hidden').onchange = upd;
        this.el.querySelector('#pp-del').onclick = () => this.cb.onDelete(idx);
    }
}
