/**
 * Depth.js — the single source of the game's render geometry + depth math.
 *
 * MUST stay in sync with the running game:
 *   - tile depth + anchor: gamev2/src/systems/RoomManager.js (loadLayer / calculateLayerDepth)
 *   - player/NPC depth:     gamev2/src/GameScene.js (updateCharacterDepths)
 *
 * The editor canvas reproduces these exactly so what you see == what the game renders
 * (feet-based Y-sort + Tops overhead bias + per-sprite depthBias + TOP_LEFT anchors).
 */
const Depth = {
    /**
     * Phaser depth for a placed tile.
     * @param {number} z          layer z-index
     * @param {number} gridY      anchor cell row
     * @param {number} heightCells sprite height in cells (round(pngH*scale / GS))
     * @param {number} depthBias  per-sprite nudge (spriteMetadata.depthBias)
     */
    tile(z, gridY, heightCells, depthBias) {
        if (z < 2) return (z - 5) * 100;                 // ground layers: fixed, below everything
        const feetRow = gridY + heightCells;             // feet = row below the bottom cell
        const overheadBias = z >= 7 ? 11 : 0;            // Tops layer draws over its own trunk
        return feetRow * 10 + overheadBias + (depthBias || 0);
    },

    /** Depth a player/NPC standing on a cell would have (for inspector ordering). */
    character(gridY) {
        return (gridY + 1) * 10 + 5;
    },

    /**
     * Pixel draw-rect for a tile, mirroring Phaser's setOrigin(anchorX, anchorY)
     * applied to a sprite positioned at the cell centre.
     * @returns {{x,y,w,h}} top-left + size in world pixels
     */
    drawRect(gridX, gridY, GS, pngW, pngH, meta) {
        const scale = (meta && meta.scale) || 1;
        const w = pngW * scale, h = pngH * scale;
        const ax = meta && meta.anchorX !== undefined ? meta.anchorX : 0.5;
        const ay = meta && meta.anchorY !== undefined ? meta.anchorY : 0.5;
        const cx = gridX * GS + GS / 2, cy = gridY * GS + GS / 2;
        return { x: cx - ax * w, y: cy - ay * h, w, h };
    },

    /** Sprite footprint in cells (width, height) from its pixel size. */
    cells(pngW, pngH, GS, meta) {
        const scale = (meta && meta.scale) || 1;
        return {
            w: Math.max(1, Math.round(pngW * scale / GS)),
            h: Math.max(1, Math.round(pngH * scale / GS)),
        };
    },
};
