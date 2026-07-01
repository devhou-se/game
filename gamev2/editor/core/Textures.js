/**
 * Textures.js — load the tile PNGs referenced by the rooms (the sliced GuttyKreum
 * tiles in ../assets/sprites/). Exposes get(key) -> {img, w, h}.
 */
class Textures {
    constructor(basePath = '../assets/sprites/') {
        this.basePath = basePath;
        this.map = {};       // key -> {img, w, h}
        this.missing = [];   // keys whose PNG failed to load
    }

    /** Collect every tile key used across all room layers, then load them. */
    async loadForConfig(config) {
        const keys = new Set();
        for (const rk of config.roomKeys()) {
            for (const L of config.room(rk).layers) {
                for (const key of Object.values(L.tiles || {})) keys.add(key);
            }
        }
        await this.loadKeys([...keys]);
        return this;
    }

    loadKeys(keys) {
        return Promise.all(keys.map(key => new Promise(resolve => {
            const img = new Image();
            img.onload = () => { this.map[key] = { img, w: img.naturalWidth, h: img.naturalHeight }; resolve(); };
            img.onerror = () => { this.missing.push(key); resolve(); };
            img.src = this.basePath + key + '.png';
        })));
    }

    get(key) { return this.map[key]; }
    has(key) { return !!this.map[key]; }
}
