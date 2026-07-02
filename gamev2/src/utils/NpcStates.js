/**
 * NpcStates — dated NPC state snapshots.
 *
 * An NPC in config.json may carry a `states` object keyed by ISO date:
 *
 *   "states": {
 *     "2026-06-30": { "dialogue": ["..."] },
 *     "2026-07-02": { "dialogue": ["..."], "gridX": 26, "gridY": 34 }
 *   }
 *
 * At load, the states dated on-or-before the game date are applied to the
 * base NPC in chronological order — each one is an UPDATE overlaying only the
 * fields it names (so a later dialogue change keeps an earlier position
 * change, and anything never named falls back to the base definition).
 * Viewing "2026-07-01" above shows the 06-30 dialogue at the base position.
 *
 * The game date defaults to today (device local time) and can be overridden
 * with ?date=YYYY-MM-DD for time travel. A state of {"present": false}
 * removes the NPC from that date until a later state sets it back.
 */
function gameDate() {
    const p = new URLSearchParams(location.search).get('date');
    if (p && /^\d{4}-\d{2}-\d{2}$/.test(p)) return p;
    const d = new Date();
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

function resolveNpc(npcConfig, date) {
    if (!npcConfig.states) return npcConfig;
    const merged = Object.assign({}, npcConfig);
    delete merged.states;
    // ISO dates compare correctly as strings
    for (const d of Object.keys(npcConfig.states).sort()) {
        if (d <= date) Object.assign(merged, npcConfig.states[d]);
    }
    if (merged.present === false) return null;
    return merged;
}

if (typeof window !== 'undefined') {
    window.gameDate = gameDate;
    window.resolveNpc = resolveNpc;
}
