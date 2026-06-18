/**
 * Config.js — load / model / save the game config (the multi-room, layered format
 * produced by doport.py). Save = download a config.json the game loads verbatim.
 */
class Config {
    constructor() {
        this.data = null;
        this.dirty = false;
    }

    /** Load ../config.json (cache-busted so the editor always sees the latest). */
    async load() {
        const res = await fetch('../config.json?t=' + Date.now());
        if (!res.ok) throw new Error('config.json fetch failed: ' + res.status);
        this.data = await res.json();
        this.dirty = false;
        return this.data;
    }

    get gridSize() { return this.data.game.gridSize; }
    roomKeys() { return Object.keys(this.data.rooms); }
    room(key) { return this.data.rooms[key]; }
    spriteMeta(key) { return this.data.spriteMetadata[key]; }
    tileName(key) { return (this.data.tileNames && this.data.tileNames[key]) || key; }

    /** A room's pixel size (per-room, falls back to global game size). */
    roomSize(key) {
        const r = this.room(key), g = this.data.game;
        return { w: r.worldWidth || g.worldWidth, h: r.worldHeight || g.worldHeight };
    }
    roomCells(key) {
        const s = this.roomSize(key), GS = this.gridSize;
        return { w: Math.round(s.w / GS), h: Math.round(s.h / GS) };
    }

    layer(roomKey, name) {
        return this.room(roomKey).layers.find(L => L.name === name);
    }
    /** The dedicated transparent collision layer (gk_blank cells). */
    colliders(roomKey) {
        let L = this.room(roomKey).layers.find(l => l.collision);
        return L;
    }

    /** Every tile occupying a cell, across all layers, with computed geometry. */
    tilesAt(roomKey, gx, gy, textures) {
        const GS = this.gridSize, out = [];
        for (const L of this.room(roomKey).layers) {
            for (const [pos, key] of Object.entries(L.tiles || {})) {
                const [tx, ty] = pos.split(',').map(Number);
                const tex = textures.get(key);
                const cells = tex ? Depth.cells(tex.w, tex.h, GS, this.spriteMeta(key))
                                  : { w: 1, h: 1 };
                if (gx >= tx && gx < tx + cells.w && gy >= ty && gy < ty + cells.h) {
                    out.push({
                        layer: L, key, tx, ty, cells,
                        name: this.tileName(key),
                        depth: Depth.tile(L.z, ty, cells.h, (this.spriteMeta(key) || {}).depthBias),
                        collision: !!L.collision,
                    });
                }
            }
        }
        out.sort((a, b) => a.depth - b.depth);
        return out;
    }

    markDirty() { this.dirty = true; }

    /** Download the current config as config.json (game-ready, 2-space indent). */
    save() {
        const blob = new Blob([JSON.stringify(this.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'config.json';
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
        this.dirty = false;
    }
}
