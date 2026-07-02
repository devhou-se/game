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

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];

/** "2026-07-02" -> "July 2 2026" (the HUD display format). */
function formatGameDate(iso) {
    const [y, m, d] = iso.split('-').map(Number);
    return `${MONTHS[m - 1]} ${d} ${y}`;
}

/** Navigate to the given game date (today -> clean URL, no param). */
function setGameDate(iso) {
    const params = new URLSearchParams(location.search);
    const d = new Date();
    const todayIso = d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
    if (!iso || iso === todayIso) params.delete('date'); else params.set('date', iso);
    const qs = params.toString();
    location.href = location.pathname + (qs ? '?' + qs : '');
}

/** Open a native date picker seeded with the current game date; picking a
 *  date reloads the game at that date (NPC states re-resolve). */
function pickGameDate() {
    let input = document.getElementById('gv2-date-picker');
    if (!input) {
        input = document.createElement('input');
        input.type = 'date';
        input.id = 'gv2-date-picker';
        // keep it focusable/clickable but visually out of the way (top-left,
        // under the HUD) — showPicker() anchors the browser UI to it
        input.style.cssText = 'position:fixed;top:4px;left:4px;width:1px;height:1px;opacity:0.01;border:0;padding:0;';
        input.addEventListener('change', () => setGameDate(input.value));
        document.body.appendChild(input);
    }
    input.value = gameDate();
    try { input.showPicker(); } catch (e) { input.focus(); input.click(); }
}

if (typeof window !== 'undefined') {
    window.gameDate = gameDate;
    window.resolveNpc = resolveNpc;
    window.formatGameDate = formatGameDate;
    window.setGameDate = setGameDate;
    window.pickGameDate = pickGameDate;
}
