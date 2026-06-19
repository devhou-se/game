/**
 * ConfigCodec - decodes the v2 game-data format back to the runtime shape.
 *
 * On disk (config format v2) each layer's `tiles` maps "x,y" -> an INTEGER index
 * into the top-level `tilePalette` array, instead of repeating the tile key
 * string for all ~13k placements. This keeps re-port diffs small and the file
 * compact. At load we expand it back to "x,y" -> "<tile key>" so every runtime
 * consumer (RoomManager.loadLayer, etc.) is unchanged.
 *
 * Version-gated and idempotent: v1 configs (no version / no palette) pass
 * through untouched, and a second call is a no-op.
 */
function decodeConfig(config) {
    if (!config || (config.version || 1) < 2 || !Array.isArray(config.tilePalette)) {
        return config; // v1 format already stores tile-key strings
    }
    const palette = config.tilePalette;
    for (const roomKey in (config.rooms || {})) {
        for (const layer of (config.rooms[roomKey].layers || [])) {
            if (layer._decoded || !layer.tiles) continue;
            const expanded = {};
            for (const xy in layer.tiles) {
                const idx = layer.tiles[xy];
                expanded[xy] = (typeof idx === 'number') ? palette[idx] : idx;
            }
            layer.tiles = expanded;
            layer._decoded = true;
        }
    }
    return config;
}

if (typeof window !== 'undefined') window.decodeConfig = decodeConfig;
