/**
 * RoomCanvas.js — depth-accurate canvas view of a room. Reproduces the game's
 * render (Depth.js) so it's true WYSIWYG, plus pan/zoom, grid, and overlays
 * (collision, transporters, spawn, boundary, hover, selection, QA).
 *
 * Tools receive cell events via the onCell callback; pan/zoom is handled here.
 */
class RoomCanvas {
    constructor(canvas, config, textures) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.config = config;
        this.textures = textures;
        this.GS = config.gridSize;

        this.roomKey = null;
        this.cam = { x: 0, y: 0, zoom: 1 };           // world coord at top-left + scale
        this.layerVisible = {};                        // name -> bool
        this.showCollision = true;
        this.showGrid = true;
        this.hover = null;                             // {x,y}
        this.selection = null;                         // {x,y}
        this.qa = [];                                  // [{x,y,sev}] highlights
        this._drawList = [];
        this._panning = false; this._panStart = null; this._panArm = null;
        this.dragMode = 'pan';   // 'pan' = left-drag pans; 'paint' = left-drag paints (set per tool)

        this.onCell = null;        // (cell{x,y}, type 'down'|'drag'|'up'|'move', button)
        this._down = false; this._downButton = 0;

        this._bindInput();
        window.addEventListener('resize', () => this.resize());
    }

    setRoom(key) {
        this.roomKey = key;
        // default all layers visible
        this.layerVisible = {};
        for (const L of this.config.room(key).layers) this.layerVisible[L.name] = true;
        this.rebuild();
        this.fitView();
    }
    setLayerVisible(name, on) { this.layerVisible[name] = on; this.rebuild(); this.render(); }
    setShowCollision(on) { this.showCollision = on; this.render(); }
    setShowGrid(on) { this.showGrid = on; this.render(); }
    setQA(list) { this.qa = list || []; this.render(); }
    setSelection(cell) { this.selection = cell; this.render(); }

    /** Build the depth-sorted tile draw list for the current room + visibility. */
    rebuild() {
        const GS = this.GS, list = [];
        for (const L of this.config.room(this.roomKey).layers) {
            if (L.collision) continue;                 // Colliders = transparent; shown via overlay
            if (this.layerVisible[L.name] === false) continue;
            for (const [pos, key] of Object.entries(L.tiles || {})) {
                const [gx, gy] = pos.split(',').map(Number);
                const tex = this.textures.get(key);
                const meta = this.config.spriteMeta(key) || {};
                if (tex) {
                    const cells = Depth.cells(tex.w, tex.h, GS, meta);
                    const r = Depth.drawRect(gx, gy, GS, tex.w, tex.h, meta);
                    list.push({ img: tex.img, r, depth: Depth.tile(L.z, gy, cells.h, meta.depthBias), gx, gy });
                } else {
                    // missing texture -> visible magenta placeholder at the cell
                    list.push({ img: null, r: { x: gx * GS, y: gy * GS, w: GS, h: GS },
                                depth: Depth.tile(L.z, gy, 1, meta.depthBias), gx, gy });
                }
            }
        }
        list.sort((a, b) => a.depth - b.depth || a.gy - b.gy || a.gx - b.gx);
        this._drawList = list;
    }

    // ---- view ----
    resize() {
        const dpr = window.devicePixelRatio || 1;
        const c = this.canvas, parent = c.parentElement;
        c.width = parent.clientWidth * dpr;
        c.height = parent.clientHeight * dpr;
        c.style.width = parent.clientWidth + 'px';
        c.style.height = parent.clientHeight + 'px';
        this._dpr = dpr;
        this.render();
    }
    fitView() {
        const s = this.config.roomSize(this.roomKey);
        const vw = this.canvas.clientWidth, vh = this.canvas.clientHeight;
        const zoom = Math.min(vw / s.w, vh / s.h) * 0.95;
        this.cam.zoom = zoom;
        this.cam.x = (s.w - vw / zoom) / 2;
        this.cam.y = (s.h - vh / zoom) / 2;
        this.render();
    }
    screenToWorld(sx, sy) {
        return { x: sx / this.cam.zoom + this.cam.x, y: sy / this.cam.zoom + this.cam.y };
    }
    screenToCell(sx, sy) {
        const w = this.screenToWorld(sx, sy);
        return { x: Math.floor(w.x / this.GS), y: Math.floor(w.y / this.GS) };
    }
    _evCell(e) {
        const rect = this.canvas.getBoundingClientRect();
        return this.screenToCell(e.clientX - rect.left, e.clientY - rect.top);
    }

    // ---- input ----
    _bindInput() {
        const c = this.canvas;
        c.addEventListener('contextmenu', e => e.preventDefault());
        c.addEventListener('wheel', e => {
            e.preventDefault();
            const rect = c.getBoundingClientRect();
            const mx = e.clientX - rect.left, my = e.clientY - rect.top;
            const before = this.screenToWorld(mx, my);
            const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
            this.cam.zoom = Math.max(0.05, Math.min(8, this.cam.zoom * factor));
            const after = this.screenToWorld(mx, my);
            this.cam.x += before.x - after.x;            // zoom toward cursor
            this.cam.y += before.y - after.y;
            this.render();
        }, { passive: false });

        const beginPan = e => { this._panning = true; this._panArm = null;
            this._panStart = { mx: e.clientX, my: e.clientY, cx: this.cam.x, cy: this.cam.y }; };

        c.addEventListener('mousedown', e => {
            // explicit pan: middle button, or shift+left
            if (e.button === 1 || (e.button === 0 && e.shiftKey)) { beginPan(e); e.preventDefault(); return; }
            this._down = true; this._downButton = e.button;
            // left-drag pans by default; only paint tools claim the drag to paint
            this._panArm = (e.button === 0 && this.dragMode !== 'paint')
                ? { mx: e.clientX, my: e.clientY, cx: this.cam.x, cy: this.cam.y } : null;
            if (this.onCell) this.onCell(this._evCell(e), 'down', e.button);
        });
        window.addEventListener('mousemove', e => {
            // a left-drag with a non-paint tool turns into a pan once it actually moves
            if (!this._panning && this._panArm) {
                const dx = e.clientX - this._panArm.mx, dy = e.clientY - this._panArm.my;
                if (Math.abs(dx) + Math.abs(dy) > 3) { this._panStart = this._panArm; this._panning = true; this._panArm = null; }
            }
            if (this._panning) {
                this.cam.x = this._panStart.cx - (e.clientX - this._panStart.mx) / this.cam.zoom;
                this.cam.y = this._panStart.cy - (e.clientY - this._panStart.my) / this.cam.zoom;
                this.render();
                return;
            }
            const cell = this._evCell(e);
            const changed = !this.hover || this.hover.x !== cell.x || this.hover.y !== cell.y;
            this.hover = cell;
            if (this._down && this.dragMode === 'paint' && this.onCell) this.onCell(cell, 'drag', this._downButton);
            else if (this.onCell) this.onCell(cell, 'move', -1);
            if (changed) this.render();
        });
        window.addEventListener('mouseup', e => {
            this._panArm = null;
            if (this._panning) { this._panning = false; this._down = false; return; }
            if (this._down && this.onCell) this.onCell(this._evCell(e), 'up', this._downButton);
            this._down = false;
        });
    }

    // ---- render ----
    render() {
        const ctx = this.ctx, dpr = this._dpr || 1;
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        ctx.fillStyle = '#0c0c10';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        if (!this.roomKey) return;
        ctx.scale(dpr, dpr);
        ctx.translate(-this.cam.x * this.cam.zoom, -this.cam.y * this.cam.zoom);
        ctx.scale(this.cam.zoom, this.cam.zoom);
        ctx.imageSmoothingEnabled = false;

        const GS = this.GS, s = this.config.roomSize(this.roomKey);
        // room backdrop (so out-of-bounds void is obvious)
        ctx.fillStyle = '#15151b';
        ctx.fillRect(0, 0, s.w, s.h);

        // tiles
        for (const t of this._drawList) {
            if (t.img) ctx.drawImage(t.img, t.r.x, t.r.y, t.r.w, t.r.h);
            else { ctx.fillStyle = 'rgba(255,0,255,0.6)'; ctx.fillRect(t.r.x, t.r.y, t.r.w, t.r.h); }
        }

        this._drawGrid(ctx, s, GS);
        if (this.showCollision) this._drawCollision(ctx, GS);
        this._drawBoundary(ctx, GS);
        this._drawTransporters(ctx, GS);
        this._drawSpawn(ctx, GS);
        this._drawQA(ctx, GS);
        if (this.selection) this._cellOutline(ctx, this.selection, GS, '#ffffff', 2.5);
        if (this.hover) this._cellOutline(ctx, this.hover, GS, '#39c5ff', 1.5);
    }

    _drawGrid(ctx, s, GS) {
        if (!this.showGrid || this.cam.zoom < 0.25) return;
        ctx.lineWidth = 1 / this.cam.zoom;
        ctx.strokeStyle = 'rgba(255,255,255,0.06)';
        ctx.beginPath();
        for (let x = 0; x <= s.w; x += GS) { ctx.moveTo(x, 0); ctx.lineTo(x, s.h); }
        for (let y = 0; y <= s.h; y += GS) { ctx.moveTo(0, y); ctx.lineTo(s.w, y); }
        ctx.stroke();
    }
    _drawCollision(ctx, GS) {
        const col = this.config.colliders(this.roomKey);
        if (!col) return;
        ctx.fillStyle = 'rgba(255,40,40,0.32)';
        ctx.strokeStyle = 'rgba(255,40,40,0.5)';
        ctx.lineWidth = 1 / this.cam.zoom;
        for (const pos of Object.keys(col.tiles || {})) {
            const [x, y] = pos.split(',').map(Number);
            ctx.fillRect(x * GS, y * GS, GS, GS);
            ctx.strokeRect(x * GS, y * GS, GS, GS);
        }
    }
    _drawBoundary(ctx, GS) {
        const b = this.config.room(this.roomKey).boundary;
        if (!b || b.length < 3) return;
        ctx.strokeStyle = '#48e06a'; ctx.lineWidth = 2 / this.cam.zoom;
        ctx.beginPath();
        b.forEach((p, i) => { const X = p[0] * GS, Y = p[1] * GS; i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); });
        ctx.closePath(); ctx.stroke();
    }
    _drawTransporters(ctx, GS) {
        for (const t of (this.config.room(this.roomKey).transporters || [])) {
            const x = t.gridX * GS, y = t.gridY * GS;
            ctx.fillStyle = t.hidden ? 'rgba(170,90,255,0.30)' : 'rgba(60,220,90,0.35)';
            ctx.strokeStyle = t.hidden ? '#aa5aff' : '#3cdc5a';
            ctx.lineWidth = 2 / this.cam.zoom;
            ctx.fillRect(x, y, GS, GS); ctx.strokeRect(x, y, GS, GS);
            this._tag(ctx, (t.hidden ? '◇ ' : '⇨ ') + t.targetRoom, x + GS / 2, y, GS);
        }
    }
    _drawSpawn(ctx, GS) {
        const p = this.config.data.player;
        if (p.startRoom !== this.roomKey) return;
        const x = p.startX * GS, y = p.startY * GS;
        ctx.strokeStyle = '#ffd23f'; ctx.lineWidth = 2.5 / this.cam.zoom;
        ctx.strokeRect(x + 2, y + 2, GS - 4, GS - 4);
        this._tag(ctx, '★ spawn', x + GS / 2, y, GS, '#ffd23f');
    }
    _drawQA(ctx, GS) {
        for (const h of this.qa) {
            ctx.strokeStyle = h.sev === 'err' ? '#ff3b3b' : '#ffb020';
            ctx.lineWidth = 3 / this.cam.zoom;
            ctx.strokeRect(h.x * GS + 1, h.y * GS + 1, GS - 2, GS - 2);
        }
    }
    _cellOutline(ctx, cell, GS, color, lw) {
        ctx.strokeStyle = color; ctx.lineWidth = lw / this.cam.zoom;
        ctx.strokeRect(cell.x * GS, cell.y * GS, GS, GS);
    }
    _tag(ctx, text, cx, topY, GS, color) {
        const z = this.cam.zoom; if (z < 0.5) return;
        ctx.save();
        ctx.font = `${12 / z}px monospace`; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
        const w = ctx.measureText(text).width + 6 / z, h = 15 / z, y = topY - 2 / z;
        ctx.fillStyle = 'rgba(0,0,0,0.7)'; ctx.fillRect(cx - w / 2, y - h, w, h);
        ctx.fillStyle = color || '#9effa0'; ctx.fillText(text, cx, y);
        ctx.restore();
    }
}
